"""
deploy.py — Deploy the Contoso Insurance Fabric workspace with fabric-cicd.

Promotes the Git source-format items under ``../workspace`` to a target Fabric
workspace (dev / test / prod). Every cross-item reference and OneLake/workspace
GUID is bound at deploy time via ``workspace/parameter.yml`` — no real GUIDs are
ever committed to the repository.

Usage
-----
    python deploy.py --environment dev  --workspace-id <target-workspace-guid>
    python deploy.py --environment test --workspace-id <target-workspace-guid>
    python deploy.py --environment prod --workspace-id <target-workspace-guid>

Authentication
--------------
Uses ``AzureCliCredential`` by default — run ``az login`` locally, or rely on the
GitHub Actions ``azure/login`` (OIDC) step in CI. Pass ``--credential default`` to
use ``DefaultAzureCredential`` instead (e.g. service-principal environment vars
AZURE_CLIENT_ID / AZURE_TENANT_ID / AZURE_CLIENT_SECRET).
"""

from __future__ import annotations

import argparse
from pathlib import Path

from azure.identity import AzureCliCredential, DefaultAzureCredential
from fabric_cicd import FabricWorkspace, publish_all_items

# Every item type present in this repository. Lakehouse / Warehouse / Eventhouse /
# KQLDatabase are published first so downstream items (Notebook, DataPipeline,
# Eventstream, SemanticModel, Report) can resolve $items references against them.
ITEM_TYPES_IN_SCOPE = [
    "VariableLibrary",
    "Lakehouse",
    "Warehouse",
    "Eventhouse",
    "KQLDatabase",
    "KQLQueryset",
    "Eventstream",
    "Notebook",
    "DataPipeline",
    "SemanticModel",
    "Report",
]

REPO_ROOT = Path(__file__).resolve().parent.parent
WORKSPACE_DIR = REPO_ROOT / "workspace"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Deploy Contoso Insurance to Microsoft Fabric.")
    parser.add_argument(
        "--environment",
        required=True,
        choices=["dev", "test", "prod"],
        help="Target environment key (must match the keys used in parameter.yml).",
    )
    parser.add_argument(
        "--workspace-id",
        required=True,
        help="GUID of the target Fabric workspace.",
    )
    parser.add_argument(
        "--credential",
        default="cli",
        choices=["cli", "default"],
        help="Token credential source: 'cli' (AzureCliCredential) or 'default' "
        "(DefaultAzureCredential / service-principal env vars).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    credential = (
        AzureCliCredential() if args.credential == "cli" else DefaultAzureCredential()
    )

    workspace = FabricWorkspace(
        workspace_id=args.workspace_id,
        environment=args.environment,
        repository_directory=str(WORKSPACE_DIR),
        item_type_in_scope=ITEM_TYPES_IN_SCOPE,
        token_credential=credential,
    )

    publish_all_items(workspace)
    print(
        f"Published Contoso Insurance to '{args.environment}' "
        f"workspace {args.workspace_id}."
    )


if __name__ == "__main__":
    main()
