# Contoso Insurance — Fabric Workspace (Copilot instructions)

This repository is a **Microsoft Fabric** end-to-end demo built around a cohesive
**property & casualty insurance** story ("Contoso Insurance"). It is structured for
**Git integration** and **dev → test → prod** promotion with
[`fabric-cicd`](https://microsoft.github.io/fabric-cicd/).

## Act as a Fabric SME
When working in this repo, behave as a Microsoft Fabric subject-matter expert. The
full Fabric skill + agent toolkit is vendored under [.github](.github):

- `.github/agents/` — `FabricDataEngineer`, `FabricAppDev`, `FabricAdmin`, `FabricIQ`.
- `.github/skills/` — 24 Fabric skills (Spark, Warehouse, Eventhouse, Eventstream,
  Dataflows, Semantic Model, migrations, etc.). Read the relevant `SKILL.md` first.
- `.github/common/` — shared cores. **`ITEM-DEFINITIONS-CORE.md` is the authority**
  for every item's on-disk Git source format. Read it before adding/editing items.

## Repository layout
| Path | Purpose |
|---|---|
| `workspace/` | Fabric items in **Git source format** (the folder you sync to a workspace). Also holds `parameter.yml` — fabric-cicd requires it in the repository_directory root. |
| `sql/` | T-SQL DDL/ELT scripts for the Warehouse Gold star schema + SQL endpoint demos. |
| `kql/` | KQL scripts for the real-time Eventhouse. |
| `deploy/` | `fabric-cicd` deployment script (`deploy.py`) + `requirements.txt` for dev/test/prod promotion. |
| `.github/workflows/` | GitHub Actions CD pipeline. |

## Naming conventions
- Lakehouse `lh_*`, Warehouse `wh_*`, Notebook `nb_*`, Pipeline `pl_*`,
  Eventhouse `eh_*`, KQL DB `kqldb_*`, Eventstream `es_*`, KQL Queryset `kqs_*`,
  Semantic model `sm_*`, Report `rpt_*`, Variable library `vl_*`.
- Medallion schemas inside the lakehouse: `bronze`, `silver`, `gold`.

## Rules when editing items
1. Every item folder MUST contain a `.platform` file with a **unique** `logicalId`.
2. Notebooks are stored as `notebook-content.py` in **Fabric source format**
   (`# Fabric notebook source`, `# CELL ********************` separators).
3. Do NOT hardcode workspace/item GUIDs in committed code — resolve IDs at runtime
   via `notebookutils`, the Variable Library (`vl_insurance_config`), or
   `parameter.yml` find-replace.
4. Keep everything **demo-data driven** — `nb_00_generate_demo_data` synthesizes all
   data; there are no external source dependencies.
