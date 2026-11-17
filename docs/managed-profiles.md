# Public and private Windows XR profiles

New public profiles use `windows_xr.integration: windows-steam` within the existing `threshold-xr/launch-stack-1` document. This is independent of native Linux/Quest profiles. The existing private repo retains `steam_play.integration: native-steam`; old `steam_play` records without a mode keep that meaning. A document containing both selections is rejected. Runtime and prefix locations are separate for the two profiles.

## Prepare the public profile

Install a pinned component stack through Threshold XR, then export/select its launch-stack file. It needs Monado's x86_64 client, Windows xrizer and both DXMT artifacts. Supply an independently installed, relocatable Wine base without lsteamclient. No Wine prefix, Steam login or native service is changed by preparation.

```zsh
python3 tools/prepare_runtime.py \
  --stack '/path/to/selected-launch-stack.json' \
  --wine-runtime '/path/to/plain-Wine' \
  --bridge-build '/path/to/threshold-wine-xr/macos-x86_64' \
  --windows-loader '/path/to/threshold-wine-xr/windows-x86_64/openxr_loader.dll' \
  --output "$HOME/Library/Application Support/ThresholdXR/WindowsSteam/runtime-VERSION" \
  --prefix "$HOME/Library/Application Support/ThresholdXR/WindowsSteam/prefix"
```

When the native and Windows bridge artifacts are separate, the selected stack must include `threshold-wine-xr/windows-x86_64`; preparation takes the matching PE module from that installed artifact. A combined developer input can instead contain both `x86_64-unix/` and `x86_64-windows/` plus the public `scripts/` directory. Packaged bridge inputs include their private copy of the Khronos loader; a developer input must already be linked against stable external paths.

The output contains a local Wine/DXMT/bridge/xrizer composition and `launch-stack.json`. It hashes the full file inventory, launch helpers and native runtime library. It never distributes that locally composed directory. The prefix remains persistent data outside it.

Use **Components → Select Windows XR Profile…** in Threshold XR to select this prepared file. The app verifies its inventory and preserves its integration mode. Selection does not start or stop anything.

```zsh
python3 tools/run_profile.py --stack '/path/to/prepared/launch-stack.json' \
  --action install-steam "$HOME/Downloads/SteamSetup.exe"
python3 tools/run_profile.py --stack '/path/to/prepared/launch-stack.json' --action steam
python3 tools/run_profile.py --stack '/path/to/prepared/launch-stack.json' \
  --action openxr '/path/to/game.exe' [game arguments...]
# OpenVR applications: use --action openvr instead.
```

The official installer comes from Valve. Windows Steam started through the prepared profile inherits the XR environment; games can also be launched directly through the profile. Critical hashes and the matching installed Monado client/service tag are checked before launch. Inherited native-Steam redirect/injection variables are removed. Game API coverage and Steam sign-in remain runtime-dependent.

## Keep private integration private

Develop shared bridge changes here and pin this repository in the private integration repo. Its macOS Steam launcher, stand-in, lsteamclient preparation and experimental backend changes stay there. Existing private prefixes are not migrated or overwritten. Use explicit profile selection to switch; do not point both profiles at one live prefix.

The private runner accepts `APPID --executable GAME.EXE [--openvr] [arguments]` for a prepared public profile and retains its existing native-Steam APPID path for private profiles. The public profile code is imported from the pinned public submodule, rather than copied into the private repo. Native Steam's prebuilt launcher installer refuses public profiles.
