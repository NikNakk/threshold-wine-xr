// Copyright 2026, Nick Kennedy
// SPDX-License-Identifier: LGPL-2.1-or-later
#include "../../src/in_process/swapchain_wait.h"
#include <stdio.h>
#define CHECK(x) do { if (!(x)) { fprintf(stderr, "FAIL line %d: %s\n", __LINE__, #x); return 1; } } while (0)
int main()
{
    const int64_t ms = 1000000;
    CHECK(mw_swapchain_wait_floor_ns(nullptr) == 5000 * ms);
    CHECK(mw_swapchain_wait_floor_ns("") == 5000 * ms);
    CHECK(mw_swapchain_wait_floor_ns("250") == 250 * ms);
    CHECK(mw_swapchain_wait_floor_ns("0") == 0);
    // A malformed or negative setting keeps the default rather than turning the floor off.
    CHECK(mw_swapchain_wait_floor_ns("5s") == 5000 * ms);
    CHECK(mw_swapchain_wait_floor_ns("-1") == 5000 * ms);
    CHECK(mw_swapchain_wait_floor_ns("99999999999999") == 600000 * ms);

    const int64_t floor = 5000 * ms;
    CHECK(mw_swapchain_wait_timeout(100 * ms, floor) == floor);
    CHECK(mw_swapchain_wait_timeout(0, floor) == floor);
    CHECK(mw_swapchain_wait_timeout(8000 * ms, floor) == 8000 * ms);
    CHECK(mw_swapchain_wait_timeout(INT64_MAX, floor) == INT64_MAX);
    CHECK(mw_swapchain_wait_timeout(100 * ms, 0) == 100 * ms);
    puts("PASS swapchain wait floor: setting, lengthening and pass-through");
    return 0;
}
