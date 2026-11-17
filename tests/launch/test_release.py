# Copyright 2026 Nick Kennedy
# SPDX-License-Identifier: LGPL-2.1-or-later
import importlib.util
from pathlib import Path
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('release_package',ROOT/'release/package.py')
package=importlib.util.module_from_spec(spec);spec.loader.exec_module(package)

class Release(unittest.TestCase):
    def test_public_payload_rejects_steam_wine_and_symlink_escape(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            for name in ['lsteamclient.dll','steam.exe','ntdll.so']:
                path=root/name;path.write_bytes(b'private')
                with self.assertRaises(ValueError):package.validate_tree(root)
                path.unlink()
            (root/'escape').symlink_to('/etc/passwd')
            with self.assertRaises(ValueError):package.validate_tree(root)

    def entries(self):
        return [dict(name=f'threshold-wine-xr-test-{platform}.tar.xz',platform=platform,role=role,sha256='a'*64,size=1)
            for platform,role in package.PLATFORMS.items()]

    def test_manifest_requires_both_halves_and_own_provenance(self):
        url='https://github.com/NikNakk/threshold-wine-xr/actions/runs/1'
        result=package.make_manifest('test','a'*40,url,self.entries())
        self.assertEqual(result['provides']['integration'],'windows-steam')
        with self.assertRaises(ValueError):package.make_manifest('test','a'*40,url,self.entries()[:1])
        with self.assertRaises(ValueError):package.make_manifest('test','a'*40,url.replace('threshold-wine-xr','macos-wine-xr'),self.entries())
        with self.assertRaises(ValueError):package.make_manifest('../escape','a'*40,url,self.entries())
