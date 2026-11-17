# Threshold Wine XR

Run Windows XR applications under Wine on Apple Silicon macOS against a native OpenXR runtime.

This is the Windows XR runtime component for Threshold XR. It also works from the command line. Threshold XR owns component installation and application management; this repository owns the Wine OpenXR adaptation and graphics sharing.

```text
Windows OpenXR application ──────────────────────┐
Windows OpenVR application → xrizer → OpenXR ────┤
                                               ↓
                                    Wine OpenXR bridge
                                               ↓
                                    native OpenXR runtime
                                               ↓
                                           headset
```

D3D11 applications use DXMT's native Metal texture and shared-event interfaces. Vulkan adaptation is included for compatible Wine/KosmicKrisp builds. The runtime has a Win64 DLL and an x86_64 macOS library loaded in the same Wine process. On Apple Silicon, the native runtime client must support x86_64; Monado's ARM64 service and x86_64 client must be compatible.

**Initial public source preview:** the bridge and probes compile, and automated launch tests pass. This extracted version has not yet been validated in a real Windows Steam sign-in, game, or headset session. It is not a complete downloadable Wine/runtime distribution.

## Windows Steam

The supported setup uses the ordinary Windows Steam client installed by the user into a dedicated Wine prefix. Steam handles sign-in, purchases, downloads and game services. The bridge handles XR; it does not replace Steam.

Download the Windows installer from [Valve](https://store.steampowered.com/about/), then select your separately supplied Wine runtime and prefix:

```zsh
export MWXR_IN_PROCESS_WINE="$HOME/Applications/Wine-XR"
export MWXR_IN_PROCESS_PREFIX="$HOME/Library/Application Support/ThresholdXR/WindowsPrefix"
./scripts/install-windows-steam.zsh "$HOME/Downloads/SteamSetup.exe"
./scripts/run-windows-steam.zsh
```

Install and sign into Steam normally, then install an owned game. The helpers do not supply Steam or a Wine distribution. They clear the native Steam redirect and library-injection environment variables. Wine/client compatibility depends on the supplied build.

## Build and launch

See [build and run](docs/build-and-run.md) for the bridge's external dependencies and complete commands, [architecture](docs/architecture.md) for component boundaries, and [validation](docs/validation.md) for checks and limitations.

```zsh
# Native source checks; no Wine runtime or headset is required.
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --parallel
ctest --test-dir build --output-on-failure
```

## Scope

Included: DXMT graphics sharing, the in-process OpenXR adaptation, optional Vulkan adaptation, xrizer launch support, Windows Steam setup helpers and diagnostic probes.

Deferred: macOS Steam client patching and UI integration, lsteamclient and the Steam stand-in, D3DMetal allocation interposition, the SteamVR driver, and experimental depth-layer submission. No Steam/client binaries, Steamworks SDK, Wine distribution, game content or private performance logs are included. OpenVR's separately licensed public header is used only by a diagnostic probe.

## Licence

The bridge is LGPL-2.1-or-later; files with their own notices retain them. See [LICENSE](LICENSE), [licensing and provenance](LICENSES/README.md), and [NOTICE.md](NOTICE.md). External runtimes, graphics translators and games have their own terms.
