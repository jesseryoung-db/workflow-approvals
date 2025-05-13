FROM mcr.microsoft.com/devcontainers/python:3.12

RUN curl -fsSL https://raw.githubusercontent.com/databricks/setup-cli/main/install.sh | sh

USER vscode
RUN curl -sSL https://install.python-poetry.org | python3 -

ENV PATH="/home/vscode/.local/bin:${PATH}"
ADD pyproject.toml poetry.lock /workspaces/workflow-approvals/
RUN cd /workspaces/workflow-approvals && poetry install --no-root

USER root
