# Database Migrations

## Numbering Gap (002-006)

Migrations 002 through 006 were created during early development and have since
been consolidated into the initial schema (001) and the latest migration (007).
The gap in numbering is intentional.

This does not affect functionality. The migration system tracks applied
migrations by filename, not by sequential number, so gaps in the numbering
are safe and expected.

Do not create new migrations to fill this gap. New migrations should continue
from 008 onward.
