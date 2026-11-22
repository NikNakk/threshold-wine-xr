// Copyright 2026, Nick Kennedy
// SPDX-License-Identifier: LGPL-2.1-or-later
#pragma once
#include <stdint.h>
#include <stdlib.h>

// Some games ask xrWaitSwapchainImage for a fraction of a second and treat a timeout as
// fatal; EXD does. Under Wine a first-use shader compile while a level loads can hold the
// runtime's image longer than that, so shorter waits are lengthened to a floor.
// MWXR_SWAPCHAIN_WAIT_MIN_MS sets it in milliseconds; 0 passes the game's timeout through.
static const int64_t MW_SWAPCHAIN_WAIT_FLOOR_DEFAULT_MS = 5000;
static const int64_t MW_SWAPCHAIN_WAIT_FLOOR_MAX_MS = 600000;

inline int64_t mw_swapchain_wait_floor_ns(const char *setting)
{
    int64_t ms = MW_SWAPCHAIN_WAIT_FLOOR_DEFAULT_MS;
    if (setting && *setting) {
        char *end = nullptr;
        long long value = strtoll(setting, &end, 10);
        if (!*end && value >= 0) ms = value < MW_SWAPCHAIN_WAIT_FLOOR_MAX_MS ? value : MW_SWAPCHAIN_WAIT_FLOOR_MAX_MS;
    }
    return ms * 1000000;
}

// The timeout to ask the runtime for. XR_INFINITE_DURATION is INT64_MAX, so it passes.
inline int64_t mw_swapchain_wait_timeout(int64_t requested, int64_t floor_ns)
{
    return requested < floor_ns ? floor_ns : requested;
}
