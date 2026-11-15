"""Exercise the optional history window with real recorded transmissions."""
import time
import unittest
from unittest.mock import patch
import tkinter as tk

import app
from arena_engine import ArenaConfig, ArenaEngine


class MessageHistoryTests(unittest.TestCase):
    def setUp(self):
        try:
            self.window = app.ArenaApp()
        except tk.TclError as exc:
            self.skipTest(f'Tk display unavailable: {exc}')
        self.window.withdraw()

    def tearDown(self):
        if getattr(self, 'window', None) is not None:
            try:
                self.window.update_idletasks()
                for callback in self.window.tk.call('after', 'info'):
                    self.window.after_cancel(callback)
                self.window.destroy()
            except tk.TclError:
                pass

    def test_completed_mixed_run_remains_reviewable_until_restart(self):
        ui = self.window
        ui.population.set('2')
        ui.generations.set('2')
        ui.message_kind.set('mixed')
        ui.speed.set('fast')
        ui.start()
        deadline = time.monotonic() + 15
        while (ui.running or len(ui.history) < 2) and time.monotonic() < deadline:
            ui.update()
            time.sleep(.01)
        self.assertEqual(len(ui.history), 2)
        self.assertFalse(ui.running)

        ui.open_messages_history()
        ui.update()
        history_window = ui._messages_history_window
        self.assertTrue(history_window.winfo_exists())
        self.assertEqual(history_window.history_rounds.current(), 1)
        expected = [e for e in ui.history[1]['events'] if e.get('type') == 'transmission']
        self.assertEqual(len(history_window.history_table.get_children()), len(expected))
        first = expected[0]
        details = history_window.history_details.get('1.0', 'end')
        self.assertIn(ui.history_message(first, 'original'), details)
        self.assertIn(ui.history_message(first, 'decoded'), details)

        history_window.history_rounds.current(0)
        history_window.history_rounds.event_generate('<<ComboboxSelected>>')
        ui.update()
        expected_first = [e for e in ui.history[0]['events'] if e.get('type') == 'transmission']
        self.assertEqual(len(history_window.history_table.get_children()), len(expected_first))

        # Changing languages closes the view, but does not erase the run.
        ui.lang.set('en')
        ui._rebuild()
        ui.open_messages_history()
        ui.update()
        self.assertEqual(len(ui.history), 2)
        self.assertIn('Package history', ui._messages_history_window.title())

        # Lost, corrupted binary and empty payloads are distinct and honest.
        self.assertIn(ui.t('not_arrived'), ui.history_message({'decoded_hex': None}, 'decoded'))
        self.assertIn('HEX: ff', ui.history_message({'decoded_hex': 'ff'}, 'decoded'))
        self.assertIn(ui.t('history_empty_message'), ui.history_message({'decoded_hex': ''}, 'decoded'))

        ui.reset()
        self.assertEqual(ui.history, [])
        with patch.object(app.messagebox, 'showinfo') as info:
            ui.open_messages_history()
        info.assert_called_once()

    def test_open_history_gains_new_rounds_without_losing_the_selected_message(self):
        ui = self.window
        engine = ArenaEngine(ArenaConfig(population=2, generations=2, message_kind='phrase'))
        first = engine.step()
        ui.history = list(engine.history)
        ui.current = first
        ui.show_snapshot(first, animate=False)
        ui.open_messages_history()
        ui.update()
        history_window = ui._messages_history_window
        original_details = history_window.history_details.get('1.0', 'end')

        second = engine.step()
        ui.history = list(engine.history)
        ui.current = second
        ui.show_snapshot(second, animate=False)
        ui.update()
        self.assertEqual(len(history_window.history_rounds.cget('values')), 2)
        self.assertEqual(history_window.history_details.get('1.0', 'end'), original_details)
        history_window.history_rounds.current(1)
        history_window.history_rounds.event_generate('<<ComboboxSelected>>')
        ui.update()
        self.assertEqual(len(history_window.history_table.get_children()),
                         sum(e.get('type') == 'transmission' for e in second['events']))

        # A v3 event has recorded bytes but no message kind or decoded text.
        self.assertEqual(ui.history_message({'original_hex': '414243'}, 'original'), 'ABC')
        self.assertEqual(ui.history_message({'decoded_hex': 'ff' * 200}, 'decoded').count('ff'), 200)


if __name__ == '__main__':
    unittest.main()
