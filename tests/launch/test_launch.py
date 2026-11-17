# Copyright 2026, Nick Kennedy
# SPDX-License-Identifier: LGPL-2.1-or-later
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]

class LaunchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='threshold launcher ')
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.wine = self.base / 'Wine runtime'
        (self.wine / 'bin').mkdir(parents=True)
        fake = self.wine / 'bin/wine'
        fake.write_text('#!/usr/bin/env python3\nimport json, os, sys\n'
            'if sys.argv[1:2] == ["winepath"]: print("Z:" + sys.argv[-1].replace("/", chr(92)))\n'
            'with open(os.environ["TEST_CALLS"], "a") as f: f.write(json.dumps({"args":sys.argv[1:],'
            '"prefix":os.environ.get("WINEPREFIX"),"redirect":os.environ.get("MWXR_LSTEAMCLIENT"),'
            '"injection":os.environ.get("DYLD_INSERT_LIBRARIES")}) + "\\n")\n')
        fake.chmod(0o755)
        self.prefix = self.base / 'Windows prefix'
        self.log = self.base / 'calls.jsonl'
        self.env = {**os.environ, 'MWXR_IN_PROCESS_WINE': str(self.wine),
            'MWXR_IN_PROCESS_PREFIX': str(self.prefix), 'TEST_CALLS': str(self.log),
            'MWXR_LSTEAMCLIENT': '1'}

    def run_script(self, name, *args):
        return subprocess.run(['zsh', str(ROOT/'scripts'/name), *map(str,args)],
            env=self.env, text=True, capture_output=True)

    def calls(self):
        return [json.loads(line) for line in self.log.read_text().splitlines()]

    def test_installer_initializes_only_selected_prefix_and_preserves_arguments(self):
        setup = self.base / 'Steam Setup.exe'; setup.touch()
        result = self.run_script('install-windows-steam.zsh', setup, '/S')
        self.assertEqual(result.returncode, 0, result.stderr)
        calls = self.calls()
        self.assertEqual([c['args'] for c in calls], [['wineboot','--init'],[str(setup),'/S']])
        self.assertTrue(all(c['prefix'] == str(self.prefix) and c['redirect'] is None for c in calls))

    def test_existing_prefix_is_not_reinitialized(self):
        self.prefix.mkdir(); (self.prefix/'system.reg').touch()
        setup = self.base/'SteamSetup.exe'; setup.touch()
        result = self.run_script('install-windows-steam.zsh', setup)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(self.calls()), 1)

    def test_missing_installer_does_not_start_wine(self):
        self.assertEqual(self.run_script('install-windows-steam.zsh', self.base/'missing.exe').returncode, 2)
        self.assertFalse(self.log.exists())

    def test_steam_uses_installed_client_without_native_redirect(self):
        steam=self.prefix/'drive_c/Program Files (x86)/Steam/steam.exe'
        steam.parent.mkdir(parents=True); steam.touch()
        result=self.run_script('run-windows-steam.zsh','-silent')
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(self.calls()[0]['args'],[str(steam),'-silent'])
        self.assertIsNone(self.calls()[0]['redirect'])

    def test_missing_client_and_relative_prefix_fail_before_launch(self):
        self.assertEqual(self.run_script('run-windows-steam.zsh').returncode,2)
        self.env['MWXR_IN_PROCESS_PREFIX']='relative-prefix'
        self.assertEqual(self.run_script('run-windows-steam.zsh').returncode,2)
        self.assertFalse(self.log.exists())

    def test_openxr_registration_and_game_arguments(self):
        build=self.base/'Bridge build'
        for directory in ['x86_64-unix','x86_64-windows']:
            (build/directory).mkdir(parents=True)
        (build/'x86_64-unix/wineopenxr.so').touch()
        (build/'x86_64-windows/wineopenxr.dll').touch()
        (self.prefix/'drive_c/windows/system32').mkdir(parents=True)
        (self.prefix/'system.reg').touch()
        self.env.update(MWXR_IN_PROCESS_BUILD=str(build),MWXR_NATIVE_RUNTIME_JSON='/external/openxr.json',
            MWXR_FOVEATION='off',MWXR_VULKAN='',MWXR_DESKTOP_MIRROR='window')
        result=self.run_script('run-in-process-openxr.zsh','C:\\Games\\game.exe','argument with spaces')
        self.assertEqual(result.returncode,0,result.stderr)
        calls=self.calls()
        self.assertEqual(calls[0]['args'][:2],['reg','add'])
        self.assertEqual(calls[-1]['args'],['C:\\Games\\game.exe','argument with spaces'])
        manifest=json.loads((self.prefix/'drive_c/openxr/wineopenxr64.json').read_text())
        self.assertEqual(manifest['runtime']['library_path'],'C:\\windows\\system32\\wineopenxr.dll')
        self.assertEqual((self.prefix/'drive_c/windows/system32/wineopenxr.dll').read_bytes(),b'')

    def test_openvr_routes_through_xrizer_and_writes_valid_registry(self):
        build=self.base/'Bridge build'
        for directory in ['x86_64-unix','x86_64-windows']:
            (build/directory).mkdir(parents=True)
        (build/'x86_64-unix/wineopenxr.so').touch()
        (build/'x86_64-windows/wineopenxr.dll').touch()
        (self.prefix/'drive_c/windows/system32').mkdir(parents=True)
        (self.prefix/'drive_c/users/tester').mkdir(parents=True)
        (self.prefix/'system.reg').touch()
        xrizer=self.base/'xrizer runtime'
        (xrizer/'bin').mkdir(parents=True)
        (xrizer/'bin/vrclient_x64.dll').touch()
        (xrizer/'openxr_loader.dll').touch()
        self.env.update(MWXR_IN_PROCESS_BUILD=str(build),MWXR_NATIVE_RUNTIME_JSON='/external/openxr.json',
            MWXR_XRIZER_ROOT=str(xrizer),MWXR_FOVEATION='off',MWXR_VULKAN='',MWXR_DESKTOP_MIRROR='window')
        result=self.run_script('run-openvr-game.zsh','game.exe','argument with spaces')
        self.assertEqual(result.returncode,0,result.stderr)
        manifest=json.loads((self.prefix/'drive_c/users/tester/AppData/Local/openvr/openvrpaths.vrpath').read_text())
        self.assertEqual(manifest['runtime'],['Z:'+str(xrizer).replace('/',chr(92))])
        self.assertEqual(self.calls()[-1]['args'],['game.exe','argument with spaces'])
        self.assertTrue((self.prefix/'drive_c/windows/system32/openxr_loader.dll').is_file())

if __name__ == '__main__': unittest.main()
