# Coding: UTF-8

# Copyright (C) 2024 Michał Prędki
# Licensed under the GNU General Public License v3.0.
# Full text of the license can be found in the LICENSE and COPYING files in the repository.

from kivymd.app import MDApp
from kivymd.uix.button import MDFlatButton
from kivymd.uix.dialog import MDDialog
from kivy.core.audio import SoundLoader
from kivy.clock import Clock
from plyer import vibrator


class Alarm:
    def __init__(self, marker):
        self.app = MDApp.get_running_app()

        # Marker's pin reference
        self.pin = marker.pin

        # Deactivate buffer with UI update
        self.pin.on_checkbox_click(False)
        # Refresh UI on ListScreen
        self.refresh_list_screen()
        # Build button to close dialog window
        self.alarm_button = MDFlatButton(
            text='OK',
            theme_text_color='Custom',
            text_color=self.app.theme_cls.primary_color,
        )
        # Build dialog window
        self.alarm_dialog = MDDialog(
            title='Wake up!',
            text=f'You are within {self.pin.buffer_size} {self.pin.buffer_unit} from {self.pin.address}',
            buttons=[self.alarm_button]
        )
        # Bind button event to close dialog window
        self.alarm_button.bind(on_release=lambda x: self.stop_alarm())

        # Load alarm file sound
        self.alarm_sound = SoundLoader.load(self.app.alarm_file)
        # Open dialog window
        self.alarm_dialog.open()

        # Trigger vibrations if device has a vibrator
        self.vibration_event = None
        if vibrator.exists():
            self.vibration_event = Clock.schedule_interval(lambda dt: vibrator.vibrate(1), 2.5)

        self.sound_alarm()

    def refresh_list_screen(self):
        """Refresh UI on ListScreen."""
        list_screen = self.app.root.ids.screen_manager.get_screen('ListScreen')
        list_screen.clear_list_data()
        list_screen.set_list_data()

    def sound_alarm(self):
        """Turn on the alarm sound."""
        if self.alarm_sound:
            self.alarm_sound.loop = True
            self.alarm_sound.play()
            return True
        return False

    def stop_alarm(self, *args):
        """Turn off the alarm and vibrations."""
        if self.alarm_sound:
            self.alarm_sound.stop()

        if self.vibration_event:
            Clock.unschedule(self.vibration_event)

        self.alarm_dialog.dismiss()
