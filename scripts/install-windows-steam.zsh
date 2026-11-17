#!/bin/zsh
# Copyright 2026, Nick Kennedy
# SPDX-License-Identifier: LGPL-2.1-or-later
# Run the official installer supplied by the user in an explicitly selected prefix.
set -euo pipefail
repo=${0:A:h:h}
[[ $# -ge 1 && -f $1 ]] || { print -u2 'usage: install-windows-steam.zsh /path/to/SteamSetup.exe [installer arguments...]'; exit 2; }
installer=${1:A}
shift
source "${repo}/scripts/windows-steam-env.zsh"
unset WINEDLLOVERRIDES WINEDLLPATH XR_RUNTIME_JSON
[[ -f ${WINEPREFIX}/system.reg ]] || "${MWXR_IN_PROCESS_WINE}/bin/wine" wineboot --init
exec "${MWXR_IN_PROCESS_WINE}/bin/wine" "${installer}" "$@"
