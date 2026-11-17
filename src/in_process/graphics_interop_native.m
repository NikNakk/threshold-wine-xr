// Copyright 2026, Nick Kennedy
// SPDX-License-Identifier: LGPL-2.1-or-later
// Read-only native Metal texture metadata for the DXMT bridge.
#import <Metal/Metal.h>
#import <Foundation/Foundation.h>
#include "graphics_interop_native.h"

int32_t mw_graphics_native_call(void *args)
{
    struct mw_gfx_native_params *p = args;
    p->status = -1;
    @autoreleasepool {
        if (p->op == MW_GFX_NATIVE_SIGNAL_EVENT) {
            id<MTLSharedEvent> event = (id<MTLSharedEvent>)p->object;
            if (event && [event conformsToProtocol:@protocol(MTLSharedEvent)]) {
                if (event.signaledValue < p->value) event.signaledValue = p->value;
                p->status = 0;
            }
            return 0;
        }
        if (p->op != MW_GFX_NATIVE_TEXTURE_INFO) return 0;
        id<MTLTexture> texture = (id<MTLTexture>)p->object;
        if (!texture || ![texture conformsToProtocol:@protocol(MTLTexture)]) return 0;
        p->actual.width = texture.width;
        p->actual.height = texture.height;
        p->actual.array_length = texture.arrayLength;
        p->actual.pixel_format = texture.pixelFormat;
        p->actual.usage = texture.usage;
        p->actual.storage_mode = texture.storageMode;
        p->actual.texture_type = texture.textureType;
        p->actual.mip_levels = texture.mipmapLevelCount;
        p->actual.samples = texture.sampleCount;
        p->iosurface = texture.iosurface != NULL;
        p->device = (uint64_t)texture.device;
        p->status = 0;
    }
    return 0;
}
