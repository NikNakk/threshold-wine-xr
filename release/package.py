#!/usr/bin/env python3
# Copyright 2026 Nick Kennedy
# SPDX-License-Identifier: LGPL-2.1-or-later
"""Package only the reviewed bridge payload; never walk or bundle a Wine runtime."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tarfile
import tempfile

COMPONENT='threshold-wine-xr'
REPOSITORY='NikNakk/threshold-wine-xr'
TOKEN=re.compile(r'[A-Za-z0-9][A-Za-z0-9._-]{0,159}\Z')
PLATFORMS={'macos-x86_64':'wine-unix','windows-x86_64':'wine-dlls'}
DENIED={'steam.exe','steam_osx','steamclient.dll','steamclient64.dll','steamclient.dylib',
        'lsteamclient.dll','lsteamclient.so','steam_api.dll','steam_api64.dll','libsteam_api.dylib','ntdll.so','ntdll.dll'}

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def validate_tree(root):
    for path in Path(root).rglob('*'):
        parts=path.relative_to(root).parts
        if path.is_symlink() or not (path.is_file() or path.is_dir()):
            raise ValueError('Release payload must contain only regular files/directories')
        if any(any(ord(c)<32 or c=='\\' for c in part) for part in parts):
            raise ValueError('Unsafe archive path')
        if path.name.lower() in DENIED or any(p.lower() in ('steamworks_sdk','steam.app','crossover.app','d3dmetal.framework') for p in parts):
            raise ValueError('Excluded release payload: '+str(path.relative_to(root)))

def copy_file(source,target):
    source=Path(source)
    if source.is_symlink() or not source.is_file():
        raise ValueError('Missing or symlinked release input: '+source.name)
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(source,target)

def relocate_native(root):
    binary=root/'x86_64-unix/wineopenxr.so'
    loader=root/'lib/libopenxr_loader.dylib'
    for path in (binary,loader):
        if subprocess.check_output(['lipo','-archs',str(path)],text=True).strip()!='x86_64':
            raise ValueError('Native artifact must be x86_64')
        dependencies=subprocess.check_output(['otool','-L',str(path)],text=True).splitlines()[1:]
        identity=subprocess.check_output(['otool','-D',str(path)],text=True).splitlines()[1:]
        for row in dependencies:
            dependency=row.strip().split(' (compatibility')[0]
            if dependency in identity or dependency.startswith(('/usr/lib/','/System/Library/')):continue
            if Path(dependency).name=='ntdll.so' and path==binary:
                target='@rpath/ntdll.so'  # supplied by the selected Wine runtime
            elif Path(dependency).name=='libopenxr_loader.dylib' and path==binary:
                target='@loader_path/../lib/libopenxr_loader.dylib'
            else:raise ValueError('Unexpected native dependency: '+dependency)
            subprocess.run(['install_name_tool','-change',dependency,target,str(path)],check=True)
        commands=subprocess.check_output(['otool','-l',str(path)],text=True).splitlines()
        rpaths=[commands[i+2].strip().split('path ',1)[1].rsplit(' (offset',1)[0]
                for i,line in enumerate(commands) if line.strip()=='cmd LC_RPATH']
        for value in set(rpaths):
            subprocess.run(['install_name_tool','-delete_rpath',value,str(path)],check=True)
        if path==binary:
            # Supported composed layout: <wine>/bridge/x86_64-unix; no Wine binary is bundled.
            subprocess.run(['install_name_tool','-add_rpath','@loader_path/../../lib/wine/x86_64-unix',str(path)],check=True)
            subprocess.run(['install_name_tool','-add_rpath','@loader_path',str(path)],check=True)
        subprocess.run(['install_name_tool','-id','@rpath/'+path.name,str(path)],check=True)
        subprocess.run(['codesign','--force','--sign','-',str(path)],check=True)
        subprocess.run(['codesign','--verify',str(path)],check=True)

def archive_tree(root,target):
    validate_tree(root)
    def normalize(info):
        info.uid=info.gid=0;info.uname=info.gname='';info.mtime=0
        info.mode=0o755 if info.isdir() or info.mode&0o111 else 0o644
        return info
    with tarfile.open(target,'w:xz') as archive:
        archive.add(root,arcname=COMPONENT,filter=normalize)

def make_manifest(version,commit,workflow_run,entries):
    if not TOKEN.fullmatch(version) or version in ('.','..') or not re.fullmatch('[0-9a-f]{40}',commit):
        raise ValueError('Invalid release identity')
    if not re.fullmatch(r'https://github\.com/NikNakk/threshold-wine-xr/actions/runs/[0-9]+',workflow_run):
        raise ValueError('Wrong workflow provenance')
    if len(entries)!=2 or {e['platform'] for e in entries}!=set(PLATFORMS):
        raise ValueError('Both bridge halves must come from the same release')
    for entry in entries:
        if entry['name']!=f"{COMPONENT}-{version}-{entry['platform']}.tar.xz" or entry['role']!=PLATFORMS[entry['platform']]:
            raise ValueError('Unexpected archive identity')
    inputs=json.loads((Path(__file__).parent/'inputs.json').read_text())
    return dict(schema='threshold-xr/release-1',component=COMPONENT,repository=REPOSITORY,
        version=version,commit=commit,built=datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
        workflow_run=workflow_run,provides={'integration':'windows-steam',**{k+'_revision':v['revision'] for k,v in inputs.items()}},artifacts=entries)

def package(build,native_loader,windows_loader,source_archives,version,commit,workflow_run,output):
    root=Path(__file__).resolve().parents[1]
    if not TOKEN.fullmatch(version):raise ValueError('Invalid version')
    if subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()!=commit:
        raise ValueError('Source commit does not match this checkout')
    output=Path(output)
    output.mkdir(parents=True,exist_ok=False)
    entries=[]
    for platform,role in PLATFORMS.items():
        with tempfile.TemporaryDirectory(prefix='bridge-release-') as temporary:
            stage=Path(temporary)/COMPONENT;stage.mkdir()
            if platform=='macos-x86_64':
                copy_file(Path(build)/'x86_64-unix/wineopenxr.so',stage/'x86_64-unix/wineopenxr.so')
                copy_file(native_loader,stage/'lib/libopenxr_loader.dylib')
                for folder in ('scripts','tools'):
                    for path in (root/folder).glob('*'):
                        if path.is_file() and path.suffix in ('.zsh','.py'):copy_file(path,stage/folder/path.name)
                relocate_native(stage)
            else:
                for name in ('wineopenxr.dll',):
                    copy_file(Path(build)/'x86_64-windows'/name,stage/'x86_64-windows'/name)
                copy_file(Path(build)/'offscreen_unity_window.exe',stage/'offscreen_unity_window.exe')
                copy_file(windows_loader,stage/'openxr_loader.dll')
                for path in [stage/'x86_64-windows/wineopenxr.dll',stage/'openxr_loader.dll',stage/'offscreen_unity_window.exe']:
                    if 'PE32+ executable' not in subprocess.check_output(['file',str(path)],text=True):
                        raise ValueError('Expected Win64 binary')
                    imports=subprocess.check_output(['x86_64-w64-mingw32-objdump','-p',str(path)],text=True)
                    for library in re.findall(r'DLL Name:\s*(\S+)',imports):
                        if library.lower().startswith(('libgcc','libstdc++','libwinpthread')):
                            raise ValueError('Unbundled MinGW runtime dependency: '+library)
            for name in ('LICENSE','NOTICE.md','README.md'):copy_file(root/name,stage/name)
            for path in (root/'LICENSES').glob('*'):copy_file(path,stage/'LICENSES'/path.name)
            inputs_root=Path(source_archives).parent/'inputs'
            for checkout in inputs_root.iterdir():
                for path in checkout.rglob('*'):
                    relative=path.relative_to(checkout)
                    if '.git' not in relative.parts and path.is_file() and path.name.upper().startswith(('LICENSE','COPYING','NOTICE','AUTHORS')):
                        copy_file(path,stage/'LICENSES/dependencies'/checkout.name/relative)
            copy_file(root/'release/inputs.json',stage/'build-inputs.json')
            name=f'{COMPONENT}-{version}-{platform}.tar.xz'
            archive_tree(stage,output/name)
            entries.append(dict(name=name,platform=platform,role=role,sha256=digest(output/name),size=(output/name).stat().st_size))
    # Source and build recipe accompany binaries; development caches/SDKs never do.
    subprocess.run(['git','archive','--format=tar.gz','--prefix='+COMPONENT+'/', '-o',str(output.resolve()/f'{COMPONENT}-{version}-source.tar.gz'),commit],cwd=root,check=True)
    for path in Path(source_archives).glob('*-source.tar.gz'):copy_file(path,output/path.name)
    required={f"{name}-{value['revision']}-source.tar.gz" for name,value in json.loads((root/'release/inputs.json').read_text()).items()}
    if not required.issubset({p.name for p in output.iterdir()}):raise ValueError('Missing corresponding dependency source')
    manifest=make_manifest(version,commit,workflow_run,entries)
    (output/'threshold-release.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (output/'SHA256SUMS').write_text(''.join(digest(p)+'  '+p.name+'\n' for p in sorted(output.iterdir()) if p.is_file()))
    return manifest

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('build','native-loader','windows-loader','source-archives','version','commit','workflow-run','output'):parser.add_argument('--'+name,required=True)
    package(**vars(parser.parse_args()))
