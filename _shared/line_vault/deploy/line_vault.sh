#!/bin/zsh
# APEX-LINEVAULT-2026-11-09: nightly line vault (reads saved PrizePicks lines, makes no PrizePicks calls)
# APEX-NBABOX-2026-11-09: first save full NBA box scores (ESPN public summary, finished games not yet saved)
/usr/bin/python3 /path/to/home/ApexSports/basketball/code/espn_box_full.py
# APEX-NBARECHECK-2026-11-09: re-read the last 3 days of NBA box scores, fix grades ESPN corrected (ESPN only)
/usr/bin/python3 /path/to/home/ApexSports/basketball/code/nba_recheck.py
cd /path/to/home/ApexSports/_shared/line_vault || exit 1
/usr/bin/python3 vault.py
