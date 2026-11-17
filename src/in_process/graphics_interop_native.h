// Copyright 2026, Nick Kennedy
// SPDX-License-Identifier: LGPL-2.1-or-later
// Fixed-width ABI between the PE graphics interop backends and their native
// helper. Object fields carry borrowed Objective-C pointers valid only in this
// process; nothing here is a sharing handle or crosses a process boundary.
#pragma once
#include <stdint.h>

enum mw_gfx_native_op { MW_GFX_NATIVE_TEXTURE_INFO = 2, MW_GFX_NATIVE_SIGNAL_EVENT = 8 };

struct mw_gfx_native_desc {
    uint64_t width, height, array_length, pixel_format, usage, storage_mode, texture_type, mip_levels, samples;
};

struct mw_gfx_native_params {
    uint32_t op;
    int32_t status;   // 0 on success
    uint64_t object;
    uint64_t value;
    uint64_t device;  // MTLDevice that served the interposed allocation
    uint32_t kind, detail, iosurface, reserved;
    struct mw_gfx_native_desc requested, actual;
    char text[256];
};
