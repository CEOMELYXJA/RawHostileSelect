"""Verify the main-screen protocol and bit explanations with real events."""
import unittest
import tkinter as tk

import app
from arena_engine import ArenaConfig, ArenaEngine


class CompactDashboardTests(unittest.TestCase):
    def setUp(self):
        try:
            self.ui = app.ArenaApp()
            self.ui.attributes('-alpha', 0.0)
        except tk.TclError as exc:
            self.skipTest(f'Tk display unavailable: {exc}')
        engine = ArenaEngine(ArenaConfig(population=8, generations=1, messages=3,
                                         message_kind='mixed', seed=42))
        self.ui.current = engine.step()
        self.ui.history = list(engine.history)
        self.ui.geometry('1380x900')
        self.ui._rebuild()
        self.ui.update()

    def tearDown(self):
        if getattr(self, 'ui', None) is not None:
            try:
                self.ui.update_idletasks()
                for callback in self.ui.tk.call('after', 'info'):
                    self.ui.after_cancel(callback)
                self.ui.destroy()
            except tk.TclError:
                pass

    def test_protocols_messages_and_controls_fit_without_main_scroll(self):
        ui = self.ui
        self.assertFalse(hasattr(ui, 'left_scroll'))
        for page in range(2):
            ui.protocol_page = page
            ui.render_protocol_page()
            for person in range(len(ui.visible_protocols)):
                ui.listbox.selection_clear(0, 'end')
                ui.listbox.selection_set(person)
                ui.select_protocol()
                self.assertEqual(ui.selected_protocol['id'], ui.visible_protocols[person]['id'])
                self.assertIn(ui.selected_protocol['id'], ui.protocol_recipe.get())
                for index, event in enumerate(ui.protocol_events):
                    ui.protocol_event_index = index
                    ui.show_protocol_message()
                    self.assertIn(ui.message_preview(event, 'original'), ui.protocol_message.get())
                    self.assertIn(ui.message_preview(event, 'decoded'), ui.protocol_message.get())
                    ui.update_idletasks()
                    for name in ('canvas', 'graph', 'listbox', 'protocol_recipe_label',
                                 'protocol_message_label', 'protocol_next_button',
                                 'bit_details_label', 'bit_next_button'):
                        widget = getattr(ui, name)
                        top = widget.winfo_rooty() - ui.winfo_rooty()
                        self.assertTrue(widget.winfo_viewable(), (name, top))
                        self.assertGreaterEqual(widget.winfo_height(), widget.winfo_reqheight(), name)
                        self.assertLessEqual(top + widget.winfo_height(), ui.winfo_height(), name)

    def test_bits_show_actual_values_and_uncertainty(self):
        ui = self.ui
        event = {'type':'transmission', 'scenario':'baseline', 'outcome':'corrupted',
                 'original_hex':'41', 'decoded_hex':'42', 'encoded_hex':'00ff',
                 'received_hex':'01fd', 'adversarial':False}
        ui.protocol_events = [event]
        ui.protocol_event_index = 0
        ui.show_protocol_message()
        self.assertEqual(len(ui.protocol_bits), 2)
        self.assertIn('bit 0', ui.bit_details.get())
        self.assertIn('0 → 1', ui.bit_details.get())
        self.assertIn(ui.t('bit_noise'), ui.bit_details.get())
        ui.change_protocol_bit(1)
        self.assertIn('bit 1', ui.bit_details.get())
        self.assertIn('1 → 0', ui.bit_details.get())
        event['adversarial'] = True
        ui.show_protocol_message()
        self.assertIn(ui.t('bit_attack'), ui.bit_details.get())
        ui.protocol_events = [{'received_hex': None}]
        ui.show_protocol_message()
        self.assertIn(ui.t('bit_no_receive'), ui.bit_details.get())
        ui.protocol_events = [{'received_hex': '00'}]
        ui.show_protocol_message()
        self.assertIn(ui.t('bit_unavailable'), ui.bit_details.get())

    def test_english_layout_keeps_main_panels_visible(self):
        ui = self.ui
        ui.lang.set('en')
        ui._rebuild()
        ui.update()
        for name in ('canvas', 'graph', 'listbox', 'protocol_recipe_label',
                     'protocol_message_label', 'protocol_next_button', 'bit_details_label', 'bit_next_button'):
            widget = getattr(ui, name)
            top = widget.winfo_rooty() - ui.winfo_rooty()
            self.assertTrue(widget.winfo_viewable(), (name, top))
            self.assertGreaterEqual(widget.winfo_height(), widget.winfo_reqheight(), name)
            self.assertLessEqual(top + widget.winfo_height(), ui.winfo_height(), name)


if __name__ == '__main__':
    unittest.main()
