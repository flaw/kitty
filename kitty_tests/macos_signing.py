#!/usr/bin/env python
# License: GPLv3 Copyright: 2026, Kovid Goyal <kovid at kovidgoyal.net>

import runpy
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import patch

from .base import BaseTest


class TestMacOSSigning(BaseTest):
    def test_local_app_signing(self):
        script = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'sign-macos.py'))
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            app = root / 'kitty.app'
            contents = app / 'Contents'
            contents.mkdir(parents=True)
            (contents / 'Info.plist').write_text('test')
            binary = contents / 'MacOS' / 'kitty'
            binary.parent.mkdir()
            binary.write_bytes(b'\xcf\xfa\xed\xfetest binary')
            nested = contents / 'quick-access.app'
            helper = nested / 'Contents' / 'MacOS' / 'helper'
            helper.parent.mkdir(parents=True)
            helper.write_bytes(b'\xca\xfe\xba\xbetest universal binary')
            external = root / 'external.dylib'
            external.write_bytes(b'\xcf\xfa\xed\xfeoutside bundle')
            (contents / 'external.dylib').symlink_to(external)
            (contents / 'external-dir').symlink_to(root, target_is_directory=True)
            targets = script['signing_targets'](app)
            self.ae(targets[-2:], [nested, app])
            self.ae(set(targets[:-2]), {binary, helper})
            self.assertNotIn(external, targets)
            with patch('subprocess.run') as run:
                script['sign_app'](app, 'Local Test Identity')
            commands = [call.args[0] for call in run.call_args_list]
            self.ae([Path(cmd[-1]) for cmd in commands[:-1]], targets)
            for call in run.call_args_list:
                self.assertTrue(call.kwargs['check'])
            self.assertIn('Local Test Identity', commands[0])
            self.assertNotIn('--deep', commands[0])
            self.ae(commands[-1][1:5], ['--verify', '--deep', '--strict', '--verbose=2'])
            with patch('subprocess.run', side_effect=subprocess.CalledProcessError(1, 'codesign')):
                with self.assertRaises(subprocess.CalledProcessError):
                    script['sign_app'](app, '-')
            with self.assertRaises(ValueError):
                script['sign_app'](app, '')
            with self.assertRaises(ValueError):
                script['sign_app'](root / 'missing.app', '-')
