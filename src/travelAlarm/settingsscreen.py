# Coding: UTF-8

# Copyright (C) 2024 Michał Prędki
# Licensed under the GNU General Public License v3.0.
# Full text of the license can be found in the LICENSE and COPYING files in the repository.

from kivymd.app import MDApp
from kivy.core.window import Window
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.properties import ObjectProperty
from kivy.metrics import dp
from kivy.core.audio import SoundLoader


class SettingsScreen(Screen):

    def on_pre_leave(self, *args):
        """Stop alarm sound sample while leaving the settings screen."""
        self.ids.alarm_sounds_list.stop_alarm_sound()


class ThemeStyleSwitch(BoxLayout):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.app = MDApp.get_running_app()
        self.database = self.app.database

    def update_theme_style(self, active):
        """Switch between light and dark theme."""
        map_theme_style = {True: 'Dark', False: 'Light'}
        selected_theme = map_theme_style.get(active)

        if selected_theme:
            self.app.theme_cls.theme_style = selected_theme
            self.database.update_app_theme_style(selected_theme)
            return True
        return False


class PrimaryPaletteToolbar(GridLayout):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.app = MDApp.get_running_app()
        self.database = self.app.database
        # Customize the grid layout appearance
        self.col_default_width = dp(50)
        self.row_default_height = dp(50)
        self.spacing = dp(10)

        # Get screen width
        screen_width_px = Window.width
        available_width = screen_width_px - self.spacing[0] * 2
        # Calculate number of columns
        num_cols = int(available_width // (self.col_default_width + self.spacing[0]))
        # Set the number of columns of layout
        self.cols = max(num_cols, 1)

    def update_primary_palette(self, new_palette):
        """Set app color palette."""
        map_primary_palette = {
            'Light Green': 'LightGreen',
            'Cyan': 'Cyan',
            'Light Blue': 'LightBlue',
            'Indigo': 'Indigo',
            'Purple': 'Purple',
            'Orange': 'Orange',
            'Amber': 'Amber',
            'Yellow': 'Yellow',
        }
        selected_palette = map_primary_palette.get(new_palette)

        if selected_palette:
            self.app.theme_cls.primary_palette = selected_palette
            self.database.update_app_primary_palette(selected_palette)
            # Update markers color
            for marker in self.app.markers.values():
                marker.set_pin_icon()
                marker.update_buffer()
            # Update GPS marker color
            if self.app.gps_marker:
                self.app.gps_marker.update_marker()
                self.app.gps_marker.update_dialog_button_color()
            return True
        return False

class AlarmSoundsList(BoxLayout):

    alarm_sound = ObjectProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.app = MDApp.get_running_app()

    def update_alarm_file(self, alarm_file):
        """Set new alarm file."""
        self.app.alarm_file = f'sounds/{alarm_file}'
        self.app.database.update_alarm_file(alarm_file)

    def sound_alarm_sample(self):
        """Start sound alarm sample."""
        self.alarm_sound = SoundLoader.load(self.app.alarm_file)

        if self.alarm_sound:
            self.alarm_sound.loop = False
            self.alarm_sound.play()

    def stop_alarm_sound(self):
        """Stop sound alarm sample."""
        if self.alarm_sound:
            self.alarm_sound.stop()

    def on_touch_down(self, touch):
        """Stop sound alarm sample when touch the screen."""
        self.stop_alarm_sound()
        super().on_touch_down(touch)
