#!/bin/zsh
# Copyright 2026, Nick Kennedy
# SPDX-License-Identifier: LGPL-2.1-or-later
set -euo pipefail
repo=${0:A:h:h}
source "${repo}/scripts/windows-steam-env.zsh"
steam="${WINEPREFIX}/drive_c/Program Files (x86)/Steam/steam.exe"
[[ -f ${steam} ]] || { print -u2 'Install Windows Steam in this prefix first'; exit 2; }
unset WINEDLLOVERRIDES WINEDLLPATH XR_RUNTIME_JSON
exec "${MWXR_IN_PROCESS_WINE}/bin/wine" "${steam}" "$@"
