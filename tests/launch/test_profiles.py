# Copyright 2026 Nick Kennedy
# SPDX-License-Identifier: LGPL-2.1-or-later
import json
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
import managed_profiles as profiles
import prepare_runtime as prepare
import run_profile

class Profiles(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='public profile ');self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name).resolve();self.wine=self.root/'external wine';self.bridge=self.root/'bridge'
        def write(base,name,data=b'fixture'):
            path=base/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data);return path
        self.write=write
        for name in ['bin/wine','bin/wineserver','lib/wine/x86_64-unix/ntdll.so','lib/wine/x86_64-windows/ntdll.dll']:
            write(self.wine,name)
        for name in ['x86_64-unix/wineopenxr.so','x86_64-windows/wineopenxr.dll']:
            write(self.bridge,name)
        for name in ['run-in-process-openxr','run-openvr-game','run-windows-steam','install-windows-steam','windows-steam-env','openxr-launch-settings']:
            write(self.bridge,'scripts/'+name+'.zsh')
        self.loader=write(self.root,'openxr_loader.dll')
        artifacts={key:str(self.root/key) for key in ['monado/macos-x86_64','xrizer/windows-x86_64','dxmt/macos-x86_64','dxmt/windows-x86_64']}
        monado=Path(artifacts['monado/macos-x86_64'])
        write(monado,'share/openxr/1/openxr_monado.json',b'{"runtime":{"library_path":"../../../lib/libopenxr_monado.dylib"}}')
        write(monado,'lib/libopenxr_monado.dylib',b'v25.1.0-1-gabcdef1\0')
        write(Path(artifacts['xrizer/windows-x86_64']),'bin/vrclient_x64.dll')
        write(Path(artifacts['dxmt/macos-x86_64']),'x86_64-unix/winemetal.so')
        for name in ['d3d10core.dll','d3d11.dll','dxgi.dll','winemetal.dll']:
            write(Path(artifacts['dxmt/windows-x86_64']),'x86_64-windows/'+name)
        self.stack=write(self.root,'stack.json',json.dumps({'schema':profiles.SCHEMA,'id':'public-test',
            'artifacts':artifacts,'monado_build_tag':'v25.1.0-1-gabcdef1'}).encode())
        self.output=self.root/'prepared';self.prefix=self.root/'persistent Windows prefix'

    def prepare(self):
        path=prepare.prepare(self.stack,self.wine,self.bridge,self.loader,self.output,self.prefix)
        return profiles.read_stack(path)

    def test_public_profile_needs_no_native_steam_and_preserves_input_and_prefix(self):
        stack=self.prepare();env=profiles.public_environment(stack)
        self.assertEqual(env['MWXR_IN_PROCESS_PREFIX'],str(self.prefix))
        self.assertNotIn('ALYX_STEAM_STAND_IN',env)
        self.assertFalse(self.prefix.exists())
        self.assertFalse((self.wine/'bridge').exists())
        with self.assertRaisesRegex(ValueError,'new output'):self.prepare()

    def test_inherited_native_redirects_are_removed(self):
        env=profiles.launch_environment(self.prepare(),{'MWXR_LSTEAMCLIENT':'1','DYLD_INSERT_LIBRARIES':'private','PATH':'test','MWXR_ALYX':'native'})
        self.assertNotIn('MWXR_LSTEAMCLIENT',env);self.assertNotIn('DYLD_INSERT_LIBRARIES',env)
        self.assertEqual(env['PATH'],'test');self.assertNotIn('MWXR_ALYX',env)

    def test_mixed_or_unknown_integration_is_rejected(self):
        stack=self.prepare();stack['steam_play']={}
        with self.assertRaisesRegex(ValueError,'separate'):profiles.public_environment(stack)
        del stack['steam_play'];stack['windows_xr']['integration']='native-steam'
        with self.assertRaises(ValueError):profiles.public_environment(stack)

    def test_tampered_helper_is_rejected_before_execution(self):
        stack=self.prepare()
        (self.output/'wine/bridge/scripts/run-openvr-game.zsh').write_text('changed')
        with self.assertRaisesRegex(ValueError,'changed'):profiles.public_environment(stack)

    def test_private_wine_base_and_nested_prefix_are_rejected(self):
        self.write(self.wine,'lib/wine/x86_64-windows/lsteamclient.dll')
        with self.assertRaisesRegex(ValueError,'native Steam'):self.prepare()
        self.assertFalse(self.output.exists())
        (self.wine/'lib/wine/x86_64-windows/lsteamclient.dll').unlink()
        with self.assertRaisesRegex(ValueError,'outside'):prepare.prepare(self.stack,self.wine,self.bridge,self.loader,self.output,self.output/'prefix')

    def test_monado_library_tamper_is_rejected(self):
        stack=self.prepare()
        library=self.root/'monado/macos-x86_64/lib/libopenxr_monado.dylib';library.write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'changed'):profiles.public_environment(stack)

    def test_public_command_uses_only_installed_public_helpers(self):
        stack=self.prepare()
        with patch.object(run_profile,'check_monado'):
            cmd,env=run_profile.command(stack,'openvr',['game with spaces.exe','-vr'])
        self.assertEqual(cmd,['zsh',str(self.output/'wine/bridge/scripts/run-openvr-game.zsh'),'game with spaces.exe','-vr'])
