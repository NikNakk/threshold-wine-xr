# Validation

Checks performed for the initial public source snapshot:

- CMake configuration and build on Apple Silicon macOS.
- Fence-wait unit test passed.
- Seven fake-Wine launch tests passed: installer/prefix selection, existing-prefix handling, argument quoting, rejection before launch, ordinary Windows Steam selection, Windows OpenXR registration and xrizer/OpenVR routing.
- Native Metal texture query/event test passed with GPU access outside the sandbox (the sandboxed run skipped because it could not see a Metal device).
- The complete Win64/x86_64 in-process bridge, Vulkan diagnostic probes, Metal readback helper, runtime-owned swapchain probe and standalone graphics interop probe compiled against the local external dependencies listed in build-and-run.md.
- Shell syntax, embedded Python syntax, source privacy/exclusion checks, and licence-notice checks.

These checks do not establish that the new launch helpers can sign into Steam, that every game works, or that this extracted build renders correctly on a headset. No live Steam installation, purchase, sign-in, service restart or headset session is performed by the automated launch tests.

CI runs the independent CMake/source tests on Linux and macOS. It does not download or distribute Steam, Wine or proprietary game/runtime binaries. Full bridge compilation needs the compatible SDKs and interfaces described in build-and-run.md; it is distinct from the lightweight CMake test build.
