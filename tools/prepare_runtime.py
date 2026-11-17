#!/usr/bin/env python3
# Copyright 2026 Nick Kennedy
# SPDX-License-Identifier: LGPL-2.1-or-later
"""Prepare a new local Windows Steam runtime; never alter an existing prefix."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from managed_profiles import PUBLIC_KEYS, public_environment, read_stack, required_files

def clone(source,target):
    if sys.platform=='darwin':subprocess.run(['/bin/cp','-cR',str(source),str(target)],check=True)
    else:shutil.copytree(source,target,symlinks=True)

def prepare(stack_path,wine,bridge,windows_loader,output,prefix):
    stack=read_stack(stack_path)
    wine,bridge,windows_loader,output,prefix=map(lambda p:Path(p).expanduser().resolve(),(wine,bridge,windows_loader,output,prefix))
    if output.exists() or output.is_relative_to(wine) or output.is_relative_to(bridge):
        raise ValueError('Choose a new output outside the input components')
    if prefix==output or prefix.is_relative_to(output):raise ValueError('Persistent prefix must be outside the versioned runtime')
    for name in ('lsteamclient.dll','lsteamclient.so','mwxr-steam.exe'):
        if any(wine.rglob(name)):raise ValueError('Use a Windows Steam Wine base without native Steam integration')
    artifacts=stack.get('artifacts',{})
    required=['monado/macos-x86_64','xrizer/windows-x86_64','dxmt/macos-x86_64','dxmt/windows-x86_64']
    if any(key not in artifacts for key in required):raise ValueError('Stack needs Monado x86_64, Windows xrizer and both DXMT halves')
    monado=Path(artifacts['monado/macos-x86_64'])/'share/openxr/1/openxr_monado.json'
    xrizer=Path(artifacts['xrizer/windows-x86_64'])
    windows_bridge = bridge if (bridge/'x86_64-windows/wineopenxr.dll').is_file() else Path(artifacts.get('threshold-wine-xr/windows-x86_64', str(bridge)))
    for path in [wine/'bin/wine',wine/'bin/wineserver',wine/'lib/wine/x86_64-unix/ntdll.so',
        wine/'lib/wine/x86_64-windows/ntdll.dll',bridge/'x86_64-unix/wineopenxr.so',
        windows_bridge/'x86_64-windows/wineopenxr.dll',windows_loader,monado,xrizer/'bin/vrclient_x64.dll']:
        if not path.is_file():raise ValueError('Missing supplied component: '+str(path))
    scripts=bridge/'scripts'
    if not scripts.is_dir():raise ValueError('Bridge input must include its public scripts/ directory')
    output.parent.mkdir(parents=True,exist_ok=True)
    stage=Path(tempfile.mkdtemp(prefix='.windows-steam-',dir=output.parent))
    try:
        runtime=stage/'wine';clone(wine,runtime)
        clone(bridge,runtime/'bridge')
        if windows_bridge != bridge:
            for relative in ('x86_64-windows/wineopenxr.dll','offscreen_unity_window.exe'):
                source=windows_bridge/relative
                if source.is_file():
                    target=runtime/'bridge'/relative;target.parent.mkdir(parents=True,exist_ok=True)
                    shutil.copy2(source,target)
        clone(xrizer,runtime/'openvr')
        for source,relative in [(Path(artifacts['dxmt/macos-x86_64'])/'x86_64-unix/winemetal.so','lib/wine/x86_64-unix/winemetal.so'),
            *[(Path(artifacts['dxmt/windows-x86_64'])/'x86_64-windows'/name,'lib/wine/x86_64-windows/'+name)
              for name in ('d3d10core.dll','d3d11.dll','dxgi.dll','winemetal.dll')]]:
            target=runtime/relative
            if target.is_symlink():target.unlink()
            shutil.copy2(source,target)
        for target in [runtime/'openvr/openxr_loader.dll',runtime/'lib/wine/x86_64-windows/openxr_loader.dll']:
            shutil.copy2(windows_loader,target)
        # A complete installed Unix module also supports games spawned by Windows Steam.
        shutil.copy2(runtime/'bridge/x86_64-unix/wineopenxr.so',runtime/'lib/wine/x86_64-unix/wineopenxr.so')
        if (runtime/'bridge/lib/libopenxr_loader.dylib').is_file():
            # The packaged module uses this path when installed beside ntdll as well.
            (runtime/'lib/wine/lib').mkdir(exist_ok=True)
            shutil.copy2(runtime/'bridge/lib/libopenxr_loader.dylib',runtime/'lib/wine/lib/libopenxr_loader.dylib')
        final=output/'wine'
        env={'MWXR_IN_PROCESS_WINE':str(final),'MWXR_IN_PROCESS_BUILD':str(final/'bridge'),
            'MWXR_XRIZER_ROOT':str(final/'openvr'),'MWXR_NATIVE_RUNTIME_JSON':str(monado.resolve()),
            'MWXR_WINDOWS_OPENXR_LOADER':str(final/'openvr/openxr_loader.dll'),
            'MWXR_IN_PROCESS_PREFIX':str(prefix),'MWXR_PUBLIC_BRIDGE_ROOT':str(final/'bridge')}
        assert set(env)==PUBLIC_KEYS
        stack.pop('_path',None);stack.pop('steam_play',None)
        hashes={str(final/path.relative_to(runtime)):hashlib.sha256(path.read_bytes()).hexdigest()
                for path in runtime.rglob('*') if path.is_file()}
        hashes[str(monado.resolve())]=hashlib.sha256(monado.read_bytes()).hexdigest()
        library=(monado.parent/json.loads(monado.read_text())['runtime']['library_path']).resolve()
        hashes[str(library)]=hashlib.sha256(library.read_bytes()).hexdigest()
        stack['windows_xr']={'integration':'windows-steam','environment':env,'file_hashes':hashes,
            'distribution':'local-composition','build_attestation_verified':False}
        (stage/'launch-stack.json').write_text(json.dumps(stack,indent=2)+'\n')
        # Validate against the temporary staging location before publishing final paths.
        probe=json.loads(json.dumps(stack));probe['windows_xr']['environment']={k:v.replace(str(final),str(runtime),1) for k,v in env.items()}
        probe['windows_xr']['file_hashes']={k.replace(str(final),str(runtime),1):v for k,v in hashes.items()}
        public_environment(probe)
        stage.rename(output)
    finally:
        if stage.exists():shutil.rmtree(stage)
    return output/'launch-stack.json'

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('stack','wine-runtime','bridge-build','windows-loader','output','prefix'):parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args()
    try:print(prepare(args.stack,args.wine_runtime,args.bridge_build,args.windows_loader,args.output,args.prefix))
    except (ValueError,OSError,subprocess.CalledProcessError) as error:sys.exit(str(error))
