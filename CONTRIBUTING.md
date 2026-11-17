# Contributing

Develop the bridge in this public repository. Keep runtime/graphics dependencies in their owning projects and application-management UI in Threshold XR.

Preserve file-level copyright/licence notices. Include relevant source tests and distinguish compilation from real runtime/game/headset validation. For graphics changes, describe the backend, runtime/client compatibility, image ownership, and GPU ordering being checked.

Run the CMake/CTest checks and `zsh -n scripts/*.zsh` (one script per invocation). Use a dedicated prefix for runtime tests. Do not commit builds, Wine prefixes, client binaries, credentials, personal home-directory paths, game files or raw private logs.
