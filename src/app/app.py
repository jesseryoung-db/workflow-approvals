import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from databricks.sdk import WorkspaceClient
from databricks.sdk.core import Config
from databricks.sql import connect
from databricks.sql.types import Row
from flask import Flask, render_template, request

assert os.getenv("SQL_WAREHOUSE_ID"), "SQL_WAREHOUSE_ID must be set in app.yaml."
assert os.getenv(
    "APPROVALS_TABLE_NAME"
), "APPROVALS_TABLE_NAME must be set in app.yaml."


app = Flask(__name__)
databricks_config = Config()
workspace_client = WorkspaceClient()


@dataclass
class ApprovalRecord:
    approval_id: str
    status: str
    requested_at: datetime
    allowed_approvers: list[str]
    source_job_run_id: int
    target_job_id: int
    approved_at: datetime | None
    approved_by: str | None
    target_job_run_id: int | None


@app.route("/approvals/<approval_id>", methods=["GET", "POST"])
def approval(approval_id: str) -> str:

    # Approval records are added to a UC table when a approval is requested. A link is generated that sends them here with the approval id
    approval_record = get_approval_record(approval_id)

    # Databricks apps place the email for the user who is accessing the app in the X-Forwarded-Email header
    user_email = request.headers.get("X-Forwarded-Email")

    # Make sure the approval exists and the user is in the list of allowed approvers
    if approval_record == None or user_email not in approval_record.allowed_approvers:
        return render_template(
            "error.html",
            error_message="Approval record not found.",
        )

    # The approval keeps track of which job run triggered the approval and which job to run after the approval is granted
    source_job_run = workspace_client.jobs.get_run(approval_record.source_job_run_id)
    target_job = workspace_client.jobs.get(approval_record.target_job_id)

    # On POST, kick off the target job run and update the approval record
    if approval_record.status.lower() == "pending" and request.method == "POST":
        run = workspace_client.jobs.run_now(approval_record.target_job_id).response
        approval_record.target_job_run_id = run.run_id
        approval_record.status = "APPROVED"
        approval_record.approved_at = datetime.now().astimezone()
        approval_record.approved_by = user_email
        update_approval_record(approval_record)

    # Render approval pages
    if approval_record.status.lower() == "approved":

        return render_template(
            "approved.html",
            target_job_name=target_job.settings.name,
            source_job_name=source_job_run.run_name,
            target_job_run_url=f"{databricks_config.host}/jobs/{approval_record.target_job_id}/runs/{approval_record.target_job_run_id}",
            approved_at=approval_record.approved_at.strftime(
                "%b %d, %Y, %I:%M %p (%Z)"
            ),
            approved_by=approval_record.approved_by,
        )
    else:
        return render_template(
            "approval.html",
            target_job_name=target_job.settings.name,
            source_job_name=source_job_run.run_name,
            source_job_run_url=source_job_run.run_page_url,
            target_job_url=f"{databricks_config.host}/jobs/{approval_record.target_job_id}",
            requested_at=approval_record.requested_at.strftime(
                "%b %d, %Y, %I:%M %p (%Z)"
            ),
        )


def execute_query(query: str, parameters: dict[str, Any] = {}) -> list[Row]:
    # Utilize the Databricks SQL connector to execute queries against the UC table
    with connect(
        server_hostname=databricks_config.host,
        http_path=f"/sql/1.0/warehouses/{os.getenv('SQL_WAREHOUSE_ID')}",
        credentials_provider=lambda: databricks_config.authenticate,
    ) as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, parameters=parameters)
            return cursor.fetchall()


def get_approval_record(approval_id: str) -> ApprovalRecord | None:
    query_result = execute_query(
        """SELECT 
            approval_id,
            status,
            requested_at,
            allowed_approvers,
            source_job_run_id,
            target_job_id,
            approved_at,
            approved_by,
            target_job_run_id
        FROM 
        identifier(:approvals_table_name) 
        WHERE approval_id = :approval_id""",
        parameters={
            "approval_id": approval_id,
            "approvals_table_name": os.getenv("APPROVALS_TABLE_NAME"),
        },
    )
    return (
        ApprovalRecord(**query_result[0].asDict()) if len(query_result) == 1 else None
    )


def update_approval_record(approval_record: ApprovalRecord) -> None:
    execute_query(
        """UPDATE 
        identifier(:approvals_table_name) 
        SET status = :status,
            approved_at = :approved_at,
            approved_by = :approved_by,
            target_job_run_id = :target_job_run_id
        WHERE approval_id = :approval_id""",
        parameters={
            "status": approval_record.status,
            "approved_at": approval_record.approved_at,
            "approved_by": approval_record.approved_by,
            "target_job_run_id": approval_record.target_job_run_id,
            "approval_id": approval_record.approval_id,
            "approvals_table_name": os.getenv("APPROVALS_TABLE_NAME"),
        },
    )
