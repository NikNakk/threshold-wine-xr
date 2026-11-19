// Copyright 2026, Nick Kennedy
// SPDX-License-Identifier: LGPL-2.1-or-later
// Experimental opt-in D3D11 companion to Monado's Metal foveation transport.
#pragma once
#include <stdint.h>
#define XR_MWXR_FOVEATION_D3D11_EXTENSION_NAME "XR_MWXR_foveation_d3d11"
#define XR_MWXR_foveation_d3d11_SPEC_VERSION 1
#define XR_TYPE_FOVEATION_D3D11_STATE_MWXR ((XrStructureType)0x7fff5070)
typedef struct XrFoveationD3D11StateMWXR {
    XrStructureType type;
    void *next;
    XrBool32 foveationEnabled;
    uint32_t physicalWidth, physicalHeight, revision;
} XrFoveationD3D11StateMWXR;
// Call after waiting the current image, before recording draws. Initially:
// one outstanding image per non-array swapchain, one colour RT, no depth/MSAA.
// Acquiring both eye swapchains before querying either is supported.
typedef XrResult (XRAPI_PTR *PFN_xrApplyFoveationD3D11MWXR)(
    XrSwapchain, uint32_t viewIndex, XrFoveationD3D11StateMWXR *);

// Native Monado ABI, from XR_MNDX_foveation_metal.h (BSL-1.0, Nick Kennedy).
#define XR_MNDX_FOVEATION_METAL_EXTENSION_NAME "XR_MNDX_foveation_metal"
#define XR_TYPE_FOVEATION_METAL_STATE_MNDX ((XrStructureType)0x7fff5057)
typedef struct XrFoveationMetalStateMNDX {
    XrStructureType type;
    void *next;
    XrBool32 foveationEnabled;
    void *rasterizationRateMap;
    uint32_t physicalWidth, physicalHeight, revision;
} XrFoveationMetalStateMNDX;
typedef XrResult (XRAPI_PTR *PFN_xrGetFoveationMetalStateMNDX)(XrSwapchain, uint32_t, uint32_t,
                                                            XrFoveationMetalStateMNDX *);
// Additive Monado v4 lookup: target extents do not select final-image reconstruction.
#define XR_TYPE_FOVEATION_METAL_PACKED_STATE_MNDX ((XrStructureType)0x7fff5058)
typedef struct { uint32_t viewIndex; XrRect2Di imageRect; } XrFoveationMetalViewMNDX;
typedef struct {
    XrStructureType type; void *next;
    uint32_t viewCount; const XrFoveationMetalViewMNDX *views;
    uint32_t horizontalSampleCount, verticalSampleCount;
    float horizontalSampleRates[16], verticalSampleRates[16];
    uint32_t boundaryCount; float x[129], y[129];
} XrFoveationMetalPackedStateMNDX;
typedef XrResult (XRAPI_PTR *PFN_xrLookupFoveationMetalStateForExtentMNDX)(
    XrSwapchain, uint32_t, uint32_t, uint32_t, uint32_t, XrFoveationMetalStateMNDX *);
// MWXR_GAZE_FOVEATION: once per frame for the projection swapchain. Returns a borrowed
// MTLRasterizationRateMap over the whole packed target (0: render ordinary).
struct mw_gaze_foveation_params {
    XrSwapchain swapchain;
    uint32_t width, height;
    XrRect2Di rects[2];
    XrFovf fovs[2];
    uint64_t map;
    XrResult result;
    uint32_t view_indices[2];
};
struct mw_foveation_params {
    XrSwapchain swapchain;
    uint32_t view_index, reserved;
    XrFoveationD3D11StateMWXR *state;
    uint64_t map;
    XrResult result;
};

// Additive Monado v5 angular profile ABI (BSL-1.0, Nick Kennedy).
#define XR_TYPE_FOVEATION_METAL_ANGULAR_PROFILE_CREATE_INFO_MNDX ((XrStructureType)0x7fff505a)
#define XR_TYPE_FOVEATION_METAL_ANGULAR_LOOKUP_INFO_MNDX ((XrStructureType)0x7fff505b)
#define XR_TYPE_FOVEATION_METAL_ANGULAR_DIAGNOSTICS_MNDX ((XrStructureType)0x7fff505c)
typedef struct XrFoveationMetalAngularProfileCreateInfoMNDX {
 XrStructureType type; const void*  next;
 float peripheralRate; /* finite, .1..1 */
 float coreAngleDegrees; /* >=1 */
 float transitionAngleDegrees; /* >=core+1 */
 float gazeStepDegrees; /* .25..10 */
 XrBool32 eyeTracked;
} XrFoveationMetalAngularProfileCreateInfoMNDX;
typedef struct XrFoveationMetalAngularViewMNDX {
 XrRect2Di imageRect;
 XrFovf fov;
} XrFoveationMetalAngularViewMNDX;
typedef struct XrFoveationMetalAngularLookupInfoMNDX {
 XrStructureType type; const void*  next;
 uint32_t width, height; /* 1..16384 */
 uint32_t referenceViewIndex;
 XrFoveationMetalAngularViewMNDX views[2]; /* actual render FOVs, may overlap */
} XrFoveationMetalAngularLookupInfoMNDX;
typedef struct XrFoveationMetalAngularDiagnosticsMNDX {
 XrStructureType type; void*  next;
 XrBool32 gazeValid, hasGaze;
 float yawDegrees, pitchDegrees;
 uint32_t buildCount, cacheCount;
 float horizontalSampleRates[64], verticalSampleRates[32];
} XrFoveationMetalAngularDiagnosticsMNDX;
/* Runtime-owned native Metal object; borrowed until next successful lookup on
 * this profile or profile destruction. Retain for longer use. No compositor
 * selection or swapchain state changes. Failure preserves history and borrow.
 * state.next may point to angular diagnostics only; previous structs unchanged.
 * Normalized runtime gaze of referenceViewIndex is interpreted through views[0]
 * render FOV, matching the legacy DXMT angular policy. No raw gaze ray exposed.
 */
typedef XrResult (XRAPI_PTR *PFN_xrLookupFoveationMetalAngularStateMNDX)(
 XrFoveationProfileFB profile, const XrFoveationMetalAngularLookupInfoMNDX* info,
 XrFoveationMetalStateMNDX* state);

/* Version 6: optional shape chain on AngularProfileCreateInfoMNDX. Absent
 * means legacy smoothstep, preserving every v5 field and default. Gaussian
 * sigma is in degrees (.25..180); gaze filtering/cache/rendering are unchanged.
 * Gaussian-core uses the existing active core (20 degrees for fixed mode).
 * Missing tracked gaze uses the original 20/35 smoothstep until valid/held
 * gaze is available. Fixed-mode alternatives retain their selected shape.
 */
#define XR_TYPE_FOVEATION_METAL_ANGULAR_SHAPE_CREATE_INFO_MNDX ((XrStructureType)0x7fff505d)
typedef enum XrFoveationMetalAngularShapeMNDX {
 XR_FOVEATION_METAL_ANGULAR_SHAPE_SMOOTHSTEP_MNDX = 0,
 XR_FOVEATION_METAL_ANGULAR_SHAPE_GAUSSIAN_CLAMPED_MNDX = 1,
 XR_FOVEATION_METAL_ANGULAR_SHAPE_GAUSSIAN_FLOOR_MNDX = 2,
 XR_FOVEATION_METAL_ANGULAR_SHAPE_GAUSSIAN_CORE_MNDX = 3,
 XR_FOVEATION_METAL_ANGULAR_SHAPE_MAX_ENUM_MNDX = 0x7fffffff
} XrFoveationMetalAngularShapeMNDX;
typedef struct XrFoveationMetalAngularShapeCreateInfoMNDX {
 XrStructureType type; const void*  next;
 XrFoveationMetalAngularShapeMNDX shape;
 float sigmaDegrees;
} XrFoveationMetalAngularShapeCreateInfoMNDX;
