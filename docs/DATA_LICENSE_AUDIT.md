# Data License Audit

**Status: UNRESOLVED for every source.** The portal terms and Ministry terms could not be
opened (network blocked), so no license, owner statement, or redistribution rule was read.

| Source | Data owner (assumed) | Terms read? | Redistribution | Derived stats / charts |
|---|---|---|---|---|
| MEF monthly arrivals | MEF (portal) / Ministry of Tourism as originator, unconfirmed | No | Unknown | Unknown |
| MEF entry points 2024, 2025 | same | No | Unknown | Unknown |
| MEF origin and purpose 2024, 2025 | same | No | Unknown | Unknown |
| MoT statistics reports | Ministry of Tourism | No | Unknown | Unknown |

Public accessibility is not permission to redistribute.

## Rules applied in this repo

- No source data is committed. `.gitignore` excludes everything in `data/raw_local/`, the
  standardized Parquet files, and the DuckDB warehouse.
- The software runs on manually supplied files and has no dependency on bundled data.
- This PR contains no derived findings, because there are none and rights are unclear.
- Nothing here claims approval or endorsement by MEF or the Ministry of Tourism.

## Open questions to settle before publishing results

1. What license or terms apply to each MEF dataset? Is there an open-data license?
2. Who owns the underlying statistics (MoT vs MEF)?
3. May charts and derived tables be published with attribution?
4. May files be mirrored in a public repository?

Software license: not yet chosen (see NEXT_STEPS). Dataset licenses are separate from it.
