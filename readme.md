# Databricks Manual Workflow Approvals

## Overview
This project provides a simple Databricks app that shows how you might add a "Manual Approval" step to Databricks workflow.

## Prerequisites
- [Visual Studio Code](https://code.visualstudio.com/) with the [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)

## Getting Started

### Setting Up the Dev Container
1. Clone the repository:
    ```bash
    git clone <repository-url>
    cd <repository-name>
    ```
2. Open the project in VS Code.
3. Reopen the folder in the dev container:
    - Press `F1` and select `Dev Containers: Reopen in Container`.

### Configuring the Databricks CLI
Follow the [Databricks documentation](https://docs.databricks.com/aws/en/dev-tools/cli/authentication) for logging into the workspace you want to deploy this to.

### Update variables for your environment
1. Update `databricks.yml` with the following:
    - Variable `approval_table_name` - This is the table that will be used to track approvals. When run, the `Approvals - Initialize` workflow will create a table at this path.
    - Variable `allowed_approvers` - A list of email addresses of the users who are allowed to approve.
    - Variable `sql_warehouse_id` - The ID of the warehouse that the App will use.
    - Workspace host - This is under the `targets` section. Replace `<your-databricks-workspace>` with the hostname of your Databricks workspace.
2. Update `./src/app/app.yaml` with the following:
    - `APPROVALS_TABLE_NAME` - Should be set to the same as `approval_table_name` in step 1. 

## Deployment
1. Deploy the [Databricks Asset Bundle](https://docs.databricks.com/aws/en/dev-tools/bundles/):
    ```bash
    databricks bundle deploy
    ```
2. Start the Databricks App
    ```bash
    databricks bundle run workflow_approvals
    ```
You should now see 3 workflows (`[dev <your username>] Approvals - Initialize`, `[dev <your username>] Approvals - Initial Workflow` and `[dev <your username>] Approvals - Post Approved Workflow`) as well as a Databricks App (`workflow-approvals`) in your workspace.

## Usage
### Create the approvals table and start 
After the app is deployed, manually run the `[dev <your username>] Approvals - Initialize` workflow to create the approvals table with the approriate schema.
