#!/bin/zsh
# Copyright 2026, Nick Kennedy
# SPDX-License-Identifier: LGPL-2.1-or-later
# Route the game's existing OpenVR loader through a separately supplied xrizer.
set -euo pipefail
repo=${0:A:h:h}
: ${MWXR_XRIZER_ROOT:?xrizer installation containing bin/vrclient_x64.dll and openxr_loader.dll}
[[ $# -gt 0 ]] || { print -u2 'usage: run-openvr-game.zsh game.exe [arguments...]'; exit 2; }
source "${repo}/scripts/windows-steam-env.zsh"
[[ -f ${MWXR_XRIZER_ROOT}/bin/vrclient_x64.dll && -f ${MWXR_XRIZER_ROOT}/openxr_loader.dll ]] || {
 print -u2 'Missing xrizer DLL or the Windows Khronos OpenXR loader'; exit 2
}
[[ -f ${WINEPREFIX}/system.reg ]] || { print -u2 'Initialize the dedicated prefix first'; exit 2; }
export VR_OVERRIDE=$("${MWXR_IN_PROCESS_WINE}/bin/wine" winepath -w "${MWXR_XRIZER_ROOT}")
VR_OVERRIDE=${VR_OVERRIDE//$'
'/}
# Valve's OpenVR loader also checks a path registry when VR_OVERRIDE is set.
python3 - "${WINEPREFIX}" "${VR_OVERRIDE}" <<'PY2'
import json, sys
from pathlib import Path
for profile in (Path(sys.argv[1]) / 'drive_c/users').iterdir():
    if not profile.is_dir() or profile.name == 'Public':
        continue
    folder = profile / 'AppData/Local/openvr'
    folder.mkdir(parents=True, exist_ok=True)
    (folder / 'openvrpaths.vrpath').write_text(json.dumps({
        'jsonid': 'vrpathreg', 'runtime': [sys.argv[2]], 'version': 1}) + '\n')
PY2
exec "${repo}/scripts/run-in-process-openxr.zsh" "$@"
