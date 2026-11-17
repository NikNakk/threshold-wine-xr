# Bridge release CI

`.github/workflows/release.yml` builds the Win64 and x86_64 macOS halves together on an Intel macOS runner, using full source commits in `release/inputs.json`. Wine is built as an SDK input, never packaged in the bridge release. The baseline SDK has no native Steam redirect patches. DXMT/Vulkan headers are compile inputs; the Khronos loader is built for both operating systems.

For a build-only validation, run `gh workflow run release.yml --repo NikNakk/threshold-wine-xr -f version=ci-VERSION -F publish=false`. It uploads one Actions artifact containing both platform archives, `threshold-release.json`, checksums and corresponding source. This does not create a GitHub Release or tag.

A new `threshold-VERSION` tag, or an explicit manual run with `publish=true`, publishes a prerelease only after the paired build succeeds. Existing releases/tags are not overwritten. The publish job attests the archives and manifest. The component name is `threshold-wine-xr`; its `threshold-xr/release-1` manifest contains `macos-x86_64` and `windows-x86_64` artifacts and declares `integration: windows-steam`.

The package stage allowlists bridge modules, public helpers, the Khronos loader, notices and dependency pins. It rejects Wine ntdll/client payloads, Steam/Steamworks binaries and symlinks. Native load commands refer to the packaged Khronos loader and to ntdll supplied by the selected Wine runtime; no developer absolute rpaths are retained. The supported installed layout is `<wine>/bridge`, composed by `tools/prepare_runtime.py`.

Bridge and dependency source archives accompany the binary payload, including the source for Wine CRT objects incorporated into PE modules. Build recipes and full source commits are retained. These previews are ad-hoc signed, not notarized; compilation/source tests do not establish compatibility with a particular game or headset. Matching Wine ABI and native Monado client/service builds remain required.
