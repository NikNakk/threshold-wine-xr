#!/bin/bash
# Copyright 2026 Nick Kennedy
# SPDX-License-Identifier: LGPL-2.1-or-later
# Sourced by build.sh after pinned sources and SDK paths are resolved.
identity=$(shasum -a 256 release/inputs.json release/build-sdk.sh | shasum -a 256 | awk '{print $1}')
if [[ ! -f "$sdk/.complete" ]] || [[ $(cat "$sdk/.complete") != "$identity" ]]; then
  [[ ! -e "$sdk" ]] || { echo 'SDK cache identity mismatch; refusing reuse' >&2; exit 1; }
  mkdir -p "$RELEASE_WORK/wine-build"
  (cd "$RELEASE_WORK/wine-build"
   "$wine/configure" --prefix="$sdk" --enable-archs=x86_64 --disable-tests \
    --without-x --without-gstreamer --without-sdl --without-cups --without-sane \
    --without-usb --without-v4l2 --without-pcap --without-krb5 --without-gphoto \
    --without-capi --without-netapi --without-opencl --without-ffmpeg
   make -j3 tools/winebuild/winebuild include/all dlls/ntdll/ntdll.so \
     dlls/ntdll/x86_64-windows/libntdll.a dlls/winecrt0/x86_64-windows/libwinecrt0.a)
  # Only the compiler tool, headers, CRT/import libraries and native ntdll are
  # needed to link the bridge. Do not build an entire Wine distribution.
  mkdir -p "$sdk/bin" "$sdk/include/wine/windows" "$sdk/lib/wine/x86_64-windows" "$sdk/lib/wine/x86_64-unix"
  cp -R "$wine/include/." "$sdk/include/wine/windows/"
  cp -R "$RELEASE_WORK/wine-build/include/." "$sdk/include/wine/windows/"
  cp "$RELEASE_WORK/wine-build/tools/winebuild/winebuild" "$sdk/bin/"
  cp "$RELEASE_WORK/wine-build/dlls/ntdll/x86_64-windows/libntdll.a" "$sdk/lib/wine/x86_64-windows/"
  cp "$RELEASE_WORK/wine-build/dlls/winecrt0/x86_64-windows/libwinecrt0.a" "$sdk/lib/wine/x86_64-windows/"
  cp "$RELEASE_WORK/wine-build/dlls/ntdll/ntdll.so" "$sdk/lib/wine/x86_64-unix/"
  mkdir -p "$sdk/licenses" "$sdk/sources"
  for license in "$wine"/COPYING* "$wine"/LICENSE*; do
    [[ ! -f "$license" ]] || cp "$license" "$sdk/licenses/"
  done
  cp "$RELEASE_WORK"/source-archives/wine-*-source.tar.gz "$sdk/sources/"
  cp "$root/release/build-sdk.sh" "$root/release/inputs.json" "$sdk/sources/"
  printf '%s' "$identity" > "$sdk/.complete"
fi
