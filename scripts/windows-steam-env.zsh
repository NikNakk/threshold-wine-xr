# Copyright 2026, Nick Kennedy
# SPDX-License-Identifier: LGPL-2.1-or-later
# Shared environment for the user-installed Windows Steam client.
: ${MWXR_IN_PROCESS_WINE:?Wine runtime directory containing bin/wine}
: ${MWXR_IN_PROCESS_PREFIX:?Dedicated Windows Steam Wine prefix (absolute path)}
[[ ${MWXR_IN_PROCESS_PREFIX} == /* ]] || { print -u2 'The Wine prefix must be an absolute path'; return 2; }
[[ -x ${MWXR_IN_PROCESS_WINE}/bin/wine ]] || { print -u2 'Wine executable is missing'; return 2; }
export WINEPREFIX=${MWXR_IN_PROCESS_PREFIX} WINEARCH=win64
export WINESERVER=${MWXR_IN_PROCESS_WINE}/bin/wineserver
export DYLD_FALLBACK_LIBRARY_PATH=${MWXR_IN_PROCESS_WINE}/lib/wine/x86_64-unix:${MWXR_IN_PROCESS_WINE}/lib
unset MWXR_LSTEAMCLIENT STEAM_COMPAT_CLIENT_INSTALL_PATH DYLD_INSERT_LIBRARIES
