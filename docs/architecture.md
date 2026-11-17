# Architecture and ownership

`wineopenxr.dll` translates Windows OpenXR calls and wrapped handles. `wineopenxr.so` runs in the same x86_64 Wine process and calls the native Khronos loader. Neither component is the headset service.

D3D11 image import uses DXMT's explicit native interface to wrap runtime-owned Metal textures. Shared events order rendering against the compositor. The native graphics helper only queries Metal metadata and signals shared events; it contains no allocation interposition or proprietary-framework scanning.

OpenVR applications reach OpenXR through a separately supplied xrizer. The ordinary Windows Steam client supplies the user's game-service integration. Steam does not supply the bridge's headset presentation path.

Threshold XR is the installation/configuration UI and application launcher. It should select a versioned bridge component, Wine runtime, DXMT/xrizer paths and a compatible native OpenXR client. It should consume the same launch scripts or a future versioned CLI contract rather than duplicate bridge internals. The release workflow emits paired artifacts under the `threshold-wine-xr` component; Threshold XR consumes that component separately from the private Steam integration.

This repository is the canonical public home for the extracted bridge. Reviewed changes should land here. Private research can propose changes, but should not maintain a second release implementation. Interface identifiers and `MWXR_*` environment variables retain their existing names to avoid unnecessary ABI churn.
