// Copyright 2026, Nick Kennedy
// SPDX-License-Identifier: LGPL-2.1-or-later
#import <Metal/Metal.h>
#import <Foundation/Foundation.h>
#include "graphics_interop_native.h"
int32_t mw_graphics_native_call(void *args);
int main(void) { @autoreleasepool {
    struct mw_gfx_native_params p = {MW_GFX_NATIVE_TEXTURE_INFO};
    mw_graphics_native_call(&p);
    if (p.status != -1) return 1;
    p.op = 999; mw_graphics_native_call(&p);
    if (p.status != -1) return 2;
    id<MTLDevice> device = MTLCreateSystemDefaultDevice();
    if (!device) return 77;
    MTLTextureDescriptor *desc = [MTLTextureDescriptor texture2DDescriptorWithPixelFormat:MTLPixelFormatRGBA8Unorm width:16 height:8 mipmapped:NO];
    desc.textureType = MTLTextureType2DArray; desc.arrayLength = 2;
    id<MTLTexture> texture = [device newTextureWithDescriptor:desc];
    if (!texture) return 3;
    p.op = MW_GFX_NATIVE_TEXTURE_INFO; p.object = (uint64_t)texture;
    mw_graphics_native_call(&p);
    int result = p.status || p.actual.width != 16 || p.actual.height != 8 ||
        p.actual.array_length != 2 || p.actual.samples != 1 || p.device != (uint64_t)device;
    id<MTLSharedEvent> event = [device newSharedEvent];
    if (!event) return 4;
    p.op = MW_GFX_NATIVE_SIGNAL_EVENT; p.object = (uint64_t)event; p.value = 3;
    mw_graphics_native_call(&p);
    result |= p.status || event.signaledValue != 3;
    p.value = 1; mw_graphics_native_call(&p);
    result |= p.status || event.signaledValue != 3;
    [event release]; [texture release]; [device release];
    return result;
} }
