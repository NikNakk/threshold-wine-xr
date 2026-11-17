# Licensing and provenance

The bridge is LGPL-2.1-or-later. See the root LICENSE and LGPL-2.1.txt. Files with an explicit BSL-1.0 notice (including the fence-wait helper/test) retain that licence; BSL-1.0.txt is provided. Existing source notices remain in force.

Copied unchanged from ValveSoftware/Proton commit `5b89db940e0ebe3a137a6009a3589232fe084c09`, wineopenxr/:

- `src/in_process/proton/make_openxr`: LGPL-2.1-or-later with its original notices.
- `src/in_process/proton/openxr_private.h` and `loader_structs.h`: Proton's LICENSE.proton, supplied as Proton-BSD-3-Clause.txt, with the Valve notice retained.

`third_party/openvr/openvr.h` is the public OpenVR SDK header under its included BSD-3-Clause licence. It is used to build a diagnostic probe; it is not the Steamworks SDK.

Generated files carry the Khronos xr.xml Apache-2.0 OR MIT notice emitted by the upstream generator. Generated implementation also incorporates generator code; the combined runtime is LGPL-2.1-or-later rather than being licensed solely by the generated header notice.

Wine headers/import libraries, the Khronos registry/loader, DXMT, xrizer, Monado and Vulkan implementations are separately supplied dependencies with their own licences. They are not relicensed here. If distributing binaries later, include the applicable notices and corresponding LGPL source/build material for the actual bundled components. This initial repository publishes source only.

Release PE binaries statically link the MinGW/GCC runtime rather than requiring separate compiler DLLs. MinGW-COPYING.txt, Winpthreads.txt (mingw-w64 v14.0.0, mingw-w64-libraries/winpthreads/COPYING), GCC-COPYING.txt and GCC-Runtime-Exception.txt retain their notices and GCC Runtime Library Exception. These notices do not change the bridge source licence.
