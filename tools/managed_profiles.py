# Copyright 2026 Nick Kennedy
# SPDX-License-Identifier: LGPL-2.1-or-later
"""The public Windows Steam profile contract; no native Steam integration."""
import hashlib
import json
import os
from pathlib import Path

SCHEMA='threshold-xr/launch-stack-1'
PUBLIC_KEYS={'MWXR_IN_PROCESS_WINE','MWXR_IN_PROCESS_BUILD','MWXR_XRIZER_ROOT',
 'MWXR_NATIVE_RUNTIME_JSON','MWXR_WINDOWS_OPENXR_LOADER','MWXR_IN_PROCESS_PREFIX','MWXR_PUBLIC_BRIDGE_ROOT'}
NATIVE_ENV={'MWXR_LSTEAMCLIENT','STEAM_COMPAT_CLIENT_INSTALL_PATH','ALYX_STEAM_STAND_IN','DYLD_INSERT_LIBRARIES','DYLD_LIBRARY_PATH','MWXR_ALYX','ALYX_STEAM','MWXR_STEAM_PLAY_PAYLOAD'}

def read_stack(path):
    source=Path(path).expanduser().resolve()
    value=json.loads(source.read_text())
    if value.get('schema')!=SCHEMA or not isinstance(value.get('id'),str) or not value['id']:
        raise ValueError('Unsupported launch-stack profile')
    value['_path']=str(source)
    return value

def required_files(env):
    wine=Path(env['MWXR_IN_PROCESS_WINE']);bridge=Path(env['MWXR_IN_PROCESS_BUILD'])
    return [wine/'bin/wine',wine/'bin/wineserver',wine/'lib/wine/x86_64-unix/ntdll.so',
        wine/'lib/wine/x86_64-windows/ntdll.dll',wine/'lib/wine/x86_64-unix/winemetal.so',
        wine/'lib/wine/x86_64-windows/d3d11.dll',wine/'lib/wine/x86_64-windows/dxgi.dll',
        bridge/'x86_64-unix/wineopenxr.so',bridge/'x86_64-windows/wineopenxr.dll',
        Path(env['MWXR_XRIZER_ROOT'])/'bin/vrclient_x64.dll',Path(env['MWXR_WINDOWS_OPENXR_LOADER']),
        Path(env['MWXR_NATIVE_RUNTIME_JSON']),
        Path(env['MWXR_PUBLIC_BRIDGE_ROOT'])/'scripts/run-in-process-openxr.zsh',
        Path(env['MWXR_PUBLIC_BRIDGE_ROOT'])/'scripts/run-openvr-game.zsh',
        Path(env['MWXR_PUBLIC_BRIDGE_ROOT'])/'scripts/run-windows-steam.zsh',
        Path(env['MWXR_PUBLIC_BRIDGE_ROOT'])/'scripts/install-windows-steam.zsh',
        Path(env['MWXR_PUBLIC_BRIDGE_ROOT'])/'scripts/windows-steam-env.zsh',
        Path(env['MWXR_PUBLIC_BRIDGE_ROOT'])/'scripts/openxr-launch-settings.zsh']

def public_environment(stack):
    selection=stack.get('windows_xr')
    if stack.get('steam_play') is not None:
        raise ValueError('Public Windows Steam and private native Steam profiles must be separate')
    if not isinstance(selection,dict) or selection.get('integration','windows-steam')!='windows-steam':
        raise ValueError('Prepare a Windows Steam profile first')
    env=selection.get('environment',{})
    if set(env)!=PUBLIC_KEYS or any(not isinstance(v,str) or not Path(v).is_absolute() for v in env.values()):
        raise ValueError('Invalid Windows Steam profile paths')
    hashes=selection.get('file_hashes',{})
    files=required_files(env)
    # Every shipped launch helper is executable code. Verify the full recorded inventory,
    # not only required binaries, before any script is started.
    if not isinstance(hashes,dict) or any(str(path) not in hashes for path in files):
        raise ValueError('Missing Windows Steam profile hashes')
    allowed=[Path(env[key]).resolve() for key in ('MWXR_IN_PROCESS_WINE','MWXR_IN_PROCESS_BUILD','MWXR_XRIZER_ROOT','MWXR_PUBLIC_BRIDGE_ROOT')]
    runtime=Path(env['MWXR_NATIVE_RUNTIME_JSON']).resolve()
    library=(runtime.parent/json.loads(runtime.read_text())['runtime']['library_path']).resolve()
    if str(library) not in hashes:raise ValueError('Missing native runtime library hash')
    for name,expected in hashes.items():
        path=Path(name)
        if not path.is_absolute() or (path.resolve() not in (runtime,library) and not any(path.resolve().is_relative_to(base) for base in allowed)):
            raise ValueError('Unexpected hashed profile path')
        if not path.is_file() or not isinstance(expected,str) or hashlib.sha256(path.read_bytes()).hexdigest()!=expected:
            raise ValueError('Managed Windows Steam file changed: '+path.name)
    return dict(env)

def launch_environment(stack,inherited=None):
    result=dict(os.environ if inherited is None else inherited)
    for key in NATIVE_ENV:result.pop(key,None)
    result.update(public_environment(stack))
    return result


def check_monado(stack, runtime_json, home=None):
    import plistlib
    import re
    home = Path.home() if home is None else Path(home)
    agent_path = home / 'Library/LaunchAgents/org.freedesktop.monado.service.plist'
    agent = plistlib.loads(agent_path.read_bytes())
    executable = agent.get('Program') or next(iter(agent.get('ProgramArguments', [])), None)
    if not executable:
        raise ValueError('Monado LaunchAgent has no service executable')
    tag = stack.get('monado_build_tag')
    document = json.loads(Path(runtime_json).read_text())
    library = (Path(runtime_json).parent / document['runtime']['library_path']).resolve()
    pattern = re.compile(rb'v\d+\.\d+\.\d+(?:-\d+-g[0-9a-f]+)?(?:-dirty)?(?=\0)')
    if not isinstance(tag, str) or not tag:
        raise ValueError('Selected stack has no Monado build tag')
    for binary in (Path(executable), library):
        match = pattern.search(binary.read_bytes())
        if not match or match.group().decode() != tag:
            raise ValueError(f'Selected stack needs Monado {tag}; {binary} has a different build tag. Activate the matching service before launching.')

    import subprocess
    for pid in subprocess.run(['/usr/bin/pgrep', '-x', 'monado-service'], capture_output=True, text=True, timeout=5).stdout.split():
        running = subprocess.run(['/bin/ps', '-o', 'comm=', '-p', pid], capture_output=True, text=True, timeout=5).stdout.strip()
        if running and Path(running).resolve() != Path(executable).resolve():
            raise ValueError(f'Another Monado service is running: {pid} {running}')
