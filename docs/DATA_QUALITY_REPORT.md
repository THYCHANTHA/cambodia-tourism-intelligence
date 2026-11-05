# Data Quality Report

**No real data was validated.** The only run of the pipeline on this repo reported:

`[warn] no_data: no source files were found; nothing was validated`

Checks implemented (tested on synthetic fixtures): duplicate months and entry rows, missing
months, blank values, negative values, unclassified entry points, total vs subtotal
reconciliation, entry vs national monthly totals, country vs region sums, partial-year flags.

Not implemented: revision tracking between releases, unit conversion checks, definition changes
between years. These need the real files.
