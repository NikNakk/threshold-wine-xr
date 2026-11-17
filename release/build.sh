#!/bin/bash
# Copyright 2026 Nick Kennedy
# SPDX-License-Identifier: LGPL-2.1-or-later
# CI-only SDK build. Wine is a build input, never a bridge release payload.
set -euo pipefail
root=$PWD
: "${RELEASE_WORK:?}" "${VERSION:?}"
[[ $(uname -m) == x86_64 && $RELEASE_WORK == /* ]] || { echo 'Use an Intel macOS runner and an absolute RELEASE_WORK' >&2; exit 2; }
export MACOSX_DEPLOYMENT_TARGET=14.0
mkdir -p "$RELEASE_WORK/inputs" "$RELEASE_WORK/source-archives"
python3 - "$root/release/inputs.json" "$RELEASE_WORK" <<'PY2'
import json, pathlib, re, subprocess, sys
work=pathlib.Path(sys.argv[2])
for name, spec in json.loads(pathlib.Path(sys.argv[1]).read_text()).items():
    assert re.fullmatch(r'[0-9a-f]{40}',spec['revision'])
    target=work/'inputs'/name
    if not target.exists():
        subprocess.run(['git','init',str(target)],check=True)
        subprocess.run(['git','-C',str(target),'fetch','--depth=1','https://github.com/'+spec['repository']+'.git',spec['revision']],check=True)
        subprocess.run(['git','-C',str(target),'checkout','--detach','FETCH_HEAD'],check=True)
    assert subprocess.check_output(['git','-C',str(target),'rev-parse','HEAD'],text=True).strip()==spec['revision']
    subprocess.run(['git','-C',str(target),'submodule','update','--init','--recursive'],check=True)
    # Keep dependency sources and notices beside the resulting bridge artifacts.
    archive=work/'source-archives'/f"{name}-{spec['revision']}-source.tar.gz"
    if not archive.exists():
        subprocess.run(['git','-C',str(target),'archive','--format=tar.gz','--prefix='+name+'/', '-o',str(archive),'HEAD'],check=True)
PY2
wine="$RELEASE_WORK/inputs/wine"
sdk="$RELEASE_WORK/wine-sdk"
# An exact-key CI cache may hold a completed SDK; a marker binds it to these inputs.
source "$root/release/build-sdk.sh"
[[ ${1:-all} != sdk ]] || exit 0
openxr="$RELEASE_WORK/inputs/openxr"
cmake -S "$openxr" -B "$RELEASE_WORK/loader-native" -G Ninja \
 -DCMAKE_BUILD_TYPE=Release -DCMAKE_OSX_ARCHITECTURES=x86_64 -DBUILD_TESTS=OFF \
 -DBUILD_API_LAYERS=OFF -DBUILD_LOADER=ON -DDYNAMIC_LOADER=ON \
 -DBUILD_WITH_SYSTEM_JSONCPP=OFF -DCMAKE_CXX_FLAGS=-DJSONCPP_USING_SECURE_MEMORY=0
cmake --build "$RELEASE_WORK/loader-native" --target openxr_loader --parallel 3
cmake -S "$openxr" -B "$RELEASE_WORK/loader-windows" -G Ninja \
 -DCMAKE_BUILD_TYPE=Release -DCMAKE_SYSTEM_NAME=Windows \
 -DCMAKE_C_COMPILER=x86_64-w64-mingw32-gcc -DCMAKE_CXX_COMPILER=x86_64-w64-mingw32-g++ \
 -DBUILD_TESTS=OFF -DBUILD_API_LAYERS=OFF -DBUILD_LOADER=ON -DDYNAMIC_LOADER=ON \
 -DBUILD_WITH_SYSTEM_JSONCPP=OFF -DCMAKE_SHARED_LINKER_FLAGS='-static-libgcc -static-libstdc++' \
 -DCMAKE_CXX_FLAGS='-DWINAPI_PARTITION_SYSTEM=0' -DCMAKE_C_FLAGS='-DWINAPI_PARTITION_SYSTEM=0'
cmake --build "$RELEASE_WORK/loader-windows" --target openxr_loader --parallel 3
export DXMT_SOURCE_DIR="$RELEASE_WORK/inputs/dxmt" MWXR_WINE_SDK="$sdk" MWXR_WINE_RUNTIME="$sdk"
export MWXR_WINE_SOURCE="$wine" OPENXR_SOURCE_DIR="$openxr"
export VULKAN_HEADERS_DIR="$RELEASE_WORK/inputs/vulkan_headers/include"
export MWXR_NATIVE_LOADER="$RELEASE_WORK/loader-native/src/loader/libopenxr_loader.dylib"
export MWXR_IN_PROCESS_BUILD="$RELEASE_WORK/bridge"
zsh scripts/build-in-process-gate.zsh
zsh scripts/build-graphics-interop-probe.zsh
windows_loader=$(python3 - "$RELEASE_WORK/loader-windows" <<'PY2'
from pathlib import Path
import sys
paths=list(Path(sys.argv[1]).rglob('*openxr_loader.dll'))
assert len(paths)==1, 'Expected one built Windows Khronos loader'
print(paths[0])
PY2
)
python3 release/package.py --build "$RELEASE_WORK/bridge" --native-loader "$MWXR_NATIVE_LOADER" \
 --windows-loader "$windows_loader" \
 --source-archives "$RELEASE_WORK/source-archives" --version "$VERSION" \
 --commit "$GITHUB_SHA" --workflow-run "$GITHUB_SERVER_URL/$GITHUB_REPOSITORY/actions/runs/$GITHUB_RUN_ID" --output dist
