#!/usr/bin/env python
# License: GPLv3 Copyright: 2026, Kovid Goyal <kovid at kovidgoyal.net>

import tempfile
from contextlib import ExitStack
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from kitty.boss import Boss
from kitty.options.utils import parse_key_action
from kitty.session import default_save_as_session_opts, save_as_session_part2

from .base import BaseTest


class TestToasts(BaseTest):
    def test_toast_action_and_target(self):
        self.set_options({})
        action = parse_key_action('show_toast Session saved')
        self.ae(action.func, 'show_toast')
        self.ae(action.args, ('Session saved',))
        boss = SimpleNamespace(active_tab_manager_with_dispatch=SimpleNamespace(os_window_id=7), os_window_map={7: object()})
        with patch('kitty.fast_data_types.set_os_window_toast') as setter, patch('kitty.fast_data_types.pt_to_px', return_value=2):
            Boss._show_toast(boss, 'hello\nworld\x07')
            setter.assert_called_once_with(7, 'hello world', 2.0, False, 2)
            Boss._show_toast(boss, 'Error', is_error=True, os_window_id=7)
            setter.assert_called_with(7, 'Error', 4.0, True, 2)
            self.set_options({'window_border_width': (3.0, 'px')})
            Boss._show_toast(boss, 'Pixel border')
            setter.assert_called_with(7, 'Pixel border', 2.0, False, 3)
            self.set_options({'window_border_width': (0.0, 'px')})
            Boss._show_toast(boss, 'No border')
            setter.assert_called_with(7, 'No border', 2.0, False, 0)
            count = setter.call_count
            Boss._show_toast(boss, ' \n\x07')
            Boss._show_toast(boss, 'Closed window', os_window_id=99)
            boss.active_tab_manager_with_dispatch = None
            Boss._show_toast(boss, 'No window')
            self.ae(setter.call_count, count)

    def test_session_save_toast_only_after_write(self):
        opts = default_save_as_session_opts()
        opts.save_only = True
        boss = Mock()
        boss.serialize_state_as_session.return_value = ['launch']
        with tempfile.TemporaryDirectory() as tmp:
            target = str(Path(tmp) / 'test.kitty-session')
            with patch('kitty.config.atomic_save') as save:

                def write(data, path):
                    boss.show_toast.assert_not_called()
                    self.ae(data, b'launch')
                    self.ae(path, target)

                save.side_effect = write
                save_as_session_part2(boss, opts, target)
            boss.show_toast.assert_called_once_with('Session saved')
            boss.reset_mock()
            with patch('kitty.config.atomic_save', side_effect=OSError('disk full')):
                save_as_session_part2(boss, opts, target)
            boss.show_toast.assert_not_called()
            boss._show_toast.assert_called_once_with('Session save failed', is_error=True)
            boss.show_error.assert_called_once()
            boss.reset_mock()
            boss.serialize_state_as_session.return_value = []
            save_as_session_part2(boss, opts, target)
            boss.show_toast.assert_not_called()
            boss.show_error.assert_called_once()

    def test_config_reload_feedback(self):
        old_opts = SimpleNamespace(all_config_paths=('config',), config_overrides=())
        boss = Mock()
        boss.active_tab_manager_with_dispatch.os_window_id = 7
        with ExitStack() as stack:
            stack.enter_context(patch('kitty.boss.get_options', return_value=old_opts))
            loader = stack.enter_context(patch('kitty.config.load_config'))
            for name in (
                'kitty.fonts.render.clear_font_caches',
                'kitty.open_actions.clear_caches',
                'kitty.guess_mime_type.clear_mime_cache',
                'kitty.boss.store_effective_config',
                'kitty.tab_bar.clear_caches',
                'kitty.shaders.slang.clear_caches',
            ):
                stack.enter_context(patch(name))
            Boss.load_config_file(boss)
            boss._show_toast.assert_called_once_with('Configuration reloaded', is_error=False, os_window_id=7)
            boss.reset_mock()
            Boss.load_config_file(boss, show_feedback=False)
            boss._show_toast.assert_not_called()

            def bad_config(*paths, **kwargs):
                kwargs['accumulate_bad_lines'].append('bad config')
                return loader.return_value

            loader.side_effect = bad_config
            Boss.load_config_file(boss, show_feedback=False)
            boss.show_bad_config_lines.assert_called_once()
            boss._show_toast.assert_called_once_with('Configuration has errors', is_error=True, os_window_id=7)
