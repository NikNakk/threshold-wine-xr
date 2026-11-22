# Build and run

## Supply compatible components

The source build currently targets Apple Silicon macOS with Rosetta 2, an x86_64 Wine runtime, and a native OpenXR loader/runtime client built for x86_64. It uses Apple Clang, Python 3, zsh, ripgrep and MinGW's `x86_64-w64-mingw32-gcc` / `g++`. CMake is used for the independent source checks.

Supply these components separately:

| Variable | Required content |
| --- | --- |
| `DXMT_SOURCE_DIR` | DXMT checkout with `include/dxmt_native_interop.h`, `IDXMTNativeDevice2`, `IDXMTNativeDevice4`, and its native DirectX headers. Ordinary upstream DXMT releases may not expose these interfaces. |
| `MWXR_WINE_SDK` | Compatible Wine SDK: `bin/winebuild`, `include/wine/windows`, and `lib/wine/x86_64-windows` import libraries. |
| `MWXR_WINE_SOURCE` | Matching Wine source headers, including `include/wine/unixlib.h`. |
| `MWXR_WINE_RUNTIME` | x86_64 Wine runtime providing `lib/wine/x86_64-unix/ntdll.so` for linking. |
| `MWXR_NATIVE_LOADER` | x86_64 Khronos `libopenxr_loader.dylib`. |
| `OPENXR_SOURCE_DIR` | Khronos OpenXR-SDK checkout with `specification/registry/xr.xml` and `include/openxr`. |
| `VULKAN_HEADERS_DIR` | Directory containing `vulkan/` headers; defaults to `/opt/homebrew/include`. Needed to compile the included Vulkan adaptation even when launching D3D11 games. |

Useful source projects: [DXMT fork](https://github.com/NikNakk/dxmt), [OpenXR-SDK](https://github.com/KhronosGroup/OpenXR-SDK), [Wine](https://gitlab.winehq.org/wine/wine), [Monado fork](https://github.com/NikNakk/monado), and [xrizer fork](https://github.com/NikNakk/xrizer). Interface compatibility matters; there is no assertion that arbitrary current releases of these projects work together.

The initial extraction compiled against DXMT `8af1b577d3c5b95e63fe41081fbe647a9f5159cc` and OpenXR-SDK `f2448a8797c85814aa892efc1ab8707900fbcc78`, using an existing local Wine SDK/runtime. This is build evidence, not a fully pinned, reproducible dependency distribution.

## Build the bridge

```zsh
export DXMT_SOURCE_DIR="$HOME/src/dxmt"
export MWXR_WINE_SDK="$HOME/Applications/Wine-XR"
export MWXR_WINE_SOURCE="$HOME/src/wine"
export MWXR_WINE_RUNTIME="$MWXR_WINE_SDK"
export MWXR_NATIVE_LOADER="$HOME/Applications/OpenXR-x64/lib/libopenxr_loader.dylib"
export OPENXR_SOURCE_DIR="$HOME/src/OpenXR-SDK"
./scripts/build-in-process-gate.zsh
```

Output is `build-in-process/gate` (override with `MWXR_IN_PROCESS_BUILD`):

- `x86_64-windows/wineopenxr.dll`: Wine builtin PE module.
- `x86_64-unix/wineopenxr.so`: x86_64 native module. Keep the external loader and Wine libraries at their linked locations; this developer build is not a relocatable binary package.
- `in_process_gate.exe`, `in_process_swapchain.exe`, Vulkan probes, and the Metal readback helper: diagnostic binaries.

The supplied Wine runtime must already have a compatible DXMT installed for D3D11 rendering. Building this project does not install DXMT, Monado, Wine or Rosetta.

## Install Windows Steam

Use the two helpers in the README. Supply a local official `SteamSetup.exe`, a Wine runtime, and an absolute, dedicated `MWXR_IN_PROCESS_PREFIX`. The installer initializes that prefix if needed, then runs the normal interactive installer. Sign-in stays inside Steam. No credentials are collected by these scripts.

The initial helper expects Steam's default `C:\Program Files (x86)\Steam` installation. Start Windows Steam in that prefix and leave it running while launching games. There are no bundled Steam patches or switches that disable its sandbox.

## Launch an OpenXR application

Start/configure the native runtime using its own tooling. With Monado, the service and x86_64 client must have matching IPC/build versions. This launcher does not install, restart or replace the native service.

```zsh
export MWXR_IN_PROCESS_WINE="$HOME/Applications/Wine-XR"
export MWXR_IN_PROCESS_PREFIX="$HOME/Library/Application Support/ThresholdXR/WindowsPrefix"
export MWXR_NATIVE_RUNTIME_JSON="$HOME/Applications/Monado-x64/share/openxr/1/openxr_monado.json"
./scripts/run-in-process-openxr.zsh '/path/to/game.exe' [game arguments...]
```

The launcher copies the built bridge DLL into that prefix's `system32`, writes its Windows OpenXR runtime manifest, registers it under `HKLM\Software\Khronos\OpenXR\1`, and runs the application. The x86_64 native module remains in the build directory selected by `WINEDLLPATH`. Use a separate prefix when you need a different Windows OpenXR runtime.

## Launch an OpenVR application with xrizer

Supply an independently built Windows xrizer installation containing `bin/vrclient_x64.dll` and the Khronos Win64 `openxr_loader.dll`:

```zsh
export MWXR_XRIZER_ROOT="$HOME/Applications/xrizer-windows"
./scripts/run-openvr-game.zsh '/path/to/openvr-game.exe' [game arguments...]
```

Keep the game's original OpenVR loader. This helper sets `VR_OVERRIDE`, writes xrizer's OpenVR path registry in the dedicated prefix's user profiles, and uses the OpenXR launcher. The Windows OpenXR loader is copied into `system32`. OpenVR API coverage depends on xrizer and the game. This path does not require this project's deferred SteamVR driver.

## Optional rendering settings

`MWXR_CLIENT_COMPOSITOR=0|1` and `MWXR_VIEWPORT_SCALE_PERCENTAGE=1..200` set explicit per-launch overrides. Inherited native runtime values are otherwise preserved.

For a compatible Vulkan stack, set `MWXR_VULKAN=kosmickrisp` and `MWXR_KK_ROOT` to a directory with `lib/libvulkan.1.dylib` and `icd/kosmickrisp_x86_64.json`. Wine must expose the native Metal objects used by the Vulkan bridge; ordinary Wine builds need not do so.

Foveation is off unless requested. `MWXR_FOVEATION=fixed|gaze` (optionally `:OUTER[,CORE,EDGE[,STEP]]`) requires compatible runtime/graphics extensions and an explicitly selected `MWXR_FOVEATION_BUILD`. DXMT foveation also requires its runtime marker `share/mwxr-foveation-dxmt`; Vulkan foveation requires a compatible KosmicKrisp. These are advanced interfaces, not a promise of support for an arbitrary game. Do not enable them to establish a first baseline.

`MWXR_SWAPCHAIN_WAIT_MIN_MS` (default 5000) lengthens a shorter `xrWaitSwapchainImage` timeout to that many milliseconds; `0` passes the application's timeout through. Some games, EXD among them, ask for a fraction of a second and quit on a timeout, which a first-use shader compile during a level load can exceed. Each wait that outlasts the application's own timeout is logged.

`MWXR_LOG_FILE` appends the bridge's messages, and the native runtime client's, to a file. A relative name is placed in `$STEAM_COMPAT_DATA_PATH` when that is set, so each Steam game gets its own. Use it when the game has no terminal, as under NotProton.

## Probe builds

`./scripts/build-graphics-interop-probe.zsh` uses `DXMT_SOURCE_DIR`, `MWXR_WINE_SDK` and `MWXR_WINE_SOURCE` to build the OpenXR-independent texture/fence probe. Run it only in an isolated test prefix with the matching Wine/DXMT runtime. `in_process_swapchain.exe` verifies runtime-owned image readback and needs the built `wine_metal_probe` helper and a working native runtime. The native runtime may activate a headset when a probe connects; the source-only CMake checks do not connect to OpenXR.
