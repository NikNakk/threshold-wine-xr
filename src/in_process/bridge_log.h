// Copyright 2026, Nick Kennedy
// SPDX-License-Identifier: LGPL-2.1-or-later
#pragma once
// The bridge's messages. The PE side hands each one to the Unix side, which writes it to
// fd 2. With MWXR_LOG_FILE set, init_openxr points fd 2 at that file (a relative name lands in
// $STEAM_COMPAT_DATA_PATH when that is set), so a game launched
// without a terminal (NotProton starts it through LaunchServices) still leaves a record,
// along with the native runtime client's own messages.
struct mw_log_params { const char *text; };
#ifdef __cplusplus
extern "C"
#endif
void mw_log(const char *format, ...) __attribute__((format(printf, 1, 2)));
