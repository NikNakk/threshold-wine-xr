# Notices and source provenance

Copyright 2026 Nick Kennedy and the respective third-party contributors identified in file notices.

This initial public source snapshot was extracted from macos-wine-xr commit `1e4292fbb2770d2d1f2ef068db23d2c12f073374` with a fresh Git history. It retains the in-process OpenXR bridge and selected diagnostic sources. The public extraction removes the D3DMetal backend/interposer, supplies a smaller Metal metadata helper, restricts D3D11 backend selection to DXMT, and adds Windows Steam/xrizer launch helpers, standalone checks and documentation.

The Proton generator and support headers retain their original upstream notices and the licences identified in LICENSES/README.md. The public OpenVR header and its licence are under third_party/openvr. Generated OpenXR files are produced locally from the separately supplied Khronos registry and retain the generator's emitted notices.

Steam is a trademark of Valve Corporation. Windows and macOS are trademarks of their respective owners. This project is independent and does not claim endorsement by Valve, Microsoft, Apple, CodeWeavers or Khronos.
