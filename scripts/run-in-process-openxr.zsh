#!/bin/zsh
# Copyright 2026, Nick Kennedy
# SPDX-License-Identifier: LGPL-2.1-or-later
set -euo pipefail
repo=${0:A:h:h}
: ${MWXR_NATIVE_RUNTIME_JSON:?x86_64 native OpenXR runtime manifest}
: ${MWXR_IN_PROCESS_PREFIX:?Dedicated Wine prefix (absolute path)}
[[ ${MWXR_IN_PROCESS_PREFIX} == /* ]] || { print -u2 'The Wine prefix must be an absolute path'; exit 2; }
[[ $# -gt 0 ]] || { print -u2 'usage: run-in-process-openxr.zsh executable [args...]'; exit 1; }
source "${repo}/scripts/openxr-launch-settings.zsh"
root=${MWXR_IN_PROCESS_BUILD:-${repo}/build-in-process/gate}
: ${MWXR_IN_PROCESS_WINE:?Wine runtime with DXMT}
wine_root=${MWXR_IN_PROCESS_WINE}
# Use a dedicated prefix, separate from other Wine installations.
export WINEPREFIX=${MWXR_IN_PROCESS_PREFIX}
export WINEARCH=win64
export WINEDEBUG=${WINEDEBUG:--all}
export WINEDLLPATH=${root}
export WINESERVER=${wine_root}/bin/wineserver
# Wine loads GnuTLS, FreeType and friends by name from the runtime's lib.
export DYLD_FALLBACK_LIBRARY_PATH=${wine_root}/lib/wine/x86_64-unix:${wine_root}/lib
export MWXR_NATIVE_RUNTIME_JSON
unset MWXR_LSTEAMCLIENT STEAM_COMPAT_CLIENT_INSTALL_PATH DYLD_INSERT_LIBRARIES
unset XR_RUNTIME_JSON WINEDLLOVERRIDES
# Select KK for native Vulkan applications without installing Zink's GL DLLs.
if [[ ${MWXR_VULKAN:-} == kosmickrisp ]]; then
 : ${MWXR_KK_ROOT:?KosmicKrisp loader and ICD directory}
 kk_root=${MWXR_KK_ROOT}
 [[ -f ${kk_root}/lib/libvulkan.1.dylib && -f ${kk_root}/icd/kosmickrisp_x86_64.json ]] || {
  print -u2 "MWXR_VULKAN=kosmickrisp: missing loader or ICD in ${kk_root}"; exit 1
 }
 export DYLD_FALLBACK_LIBRARY_PATH=${kk_root}/lib:${DYLD_FALLBACK_LIBRARY_PATH}
 export VK_DRIVER_FILES=${kk_root}/icd/kosmickrisp_x86_64.json
 print -u2 "Vulkan: KosmicKrisp from ${kk_root}"
elif [[ -n ${MWXR_VULKAN:-} ]]; then
 print -u2 'MWXR_VULKAN must be kosmickrisp (or unset)'; exit 2
fi
[[ -x ${wine_root}/bin/wine && -f ${root}/x86_64-unix/wineopenxr.so ]] || {
 print -u2 'Build the in-process runtime and select a compatible Wine runtime (MWXR_IN_PROCESS_WINE)'; exit 1
}
# Wine updates a prefix itself when its runtime's wine.inf changes. An explicit
# "wineboot -u" on every launch left a temporary copy of each DLL a running process
# had open (dll*.tmp, pending until the prefix restarts): 12.9 GB in the rig prefix.
[[ -f ${WINEPREFIX}/system.reg ]] || WINEDLLOVERRIDES="mscoree=;mshtml=" "${wine_root}/bin/wine" wineboot --init
mkdir -p "${WINEPREFIX}/drive_c/openxr"
cp "${root}/x86_64-windows/wineopenxr.dll" "${WINEPREFIX}/drive_c/windows/system32/"
# xrizer loads openxr_loader.dll by name. Keeping it next to vrclient_x64.dll
# does not put it on the Windows process DLL search path. Provision the
# Khronos Win64 loader into this prefix, not the host's arm64 dylib directory.
windows_loader=${MWXR_WINDOWS_OPENXR_LOADER:-${MWXR_XRIZER_ROOT:-}/openxr_loader.dll}
if [[ -n ${MWXR_WINDOWS_OPENXR_LOADER:-} || -n ${MWXR_XRIZER_ROOT:-} ]]; then
 [[ -f ${windows_loader} ]] || {
  print -u2 "Windows OpenXR loader is missing: ${windows_loader}"; exit 1
 }
 cp "${windows_loader}" "${WINEPREFIX}/drive_c/windows/system32/openxr_loader.dll"
fi
cat > "${WINEPREFIX}/drive_c/openxr/wineopenxr64.json" <<'JSON'
{"file_format_version":"1.0.0","runtime":{"library_path":"C:\\windows\\system32\\wineopenxr.dll"}}
JSON
"${wine_root}/bin/wine" reg add 'HKLM\Software\Khronos\OpenXR\1' /v ActiveRuntime /t REG_SZ \
 /d 'C:\openxr\wineopenxr64.json' /f
case ${MWXR_DESKTOP_MIRROR:-window} in
 window)
  # Apply explicit DLL overrides to the application and its children.
  [[ -n ${MWXR_WINEDLLOVERRIDES:-} ]] && export WINEDLLOVERRIDES=${MWXR_WINEDLLOVERRIDES}
  exec "${wine_root}/bin/wine" "$@" ;;
 offscreen)
  [[ -f ${root}/offscreen_unity_window.exe ]] || {
   print -u2 'Rebuild scripts/build-in-process-gate.zsh for the off-screen Unity launcher'; exit 1
  }
  game=$("${wine_root}/bin/wine" winepath -w "$1")
  game=${game//$'\r'/}
  shift
  exec "${wine_root}/bin/wine" "${root}/offscreen_unity_window.exe" "$game" -screen-fullscreen 0 "$@"
  ;;
 *) print -u2 'MWXR_DESKTOP_MIRROR must be window or offscreen'; exit 2 ;;
esac
