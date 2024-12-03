from kivymd.app import MDApp
from kivy.core.window import Window
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.metrics import dp


class SettingsScreen(Screen):
    pass


class ThemeStyleSwitch(BoxLayout):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Get app instance
        self.app = MDApp.get_running_app()

        # Get database instance
        self.pins_db = self.app.pins_db

    def update_theme_style(self, active):
        """Update app style."""
        # Assign the value of active to the corresponding style
        map_theme_style = {True: "Dark", False: "Light"}

        # Get proper app style
        selected_theme = map_theme_style.get(active)

        if selected_theme:
            # Update app style
            self.app.theme_cls.theme_style = selected_theme

            # Update app style in database
            self.pins_db.update_app_theme_style(selected_theme)


class PrimaryPaletteToolbar(GridLayout):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Get app instance
        self.app = MDApp.get_running_app()

        # Get database instance
        self.pins_db = self.app.pins_db

        # Customize the grid layout appearance
        self.col_default_width = dp(50)
        self.row_default_height = dp(50)
        self.spacing = dp(10)

        # Get screen width
        screen_width_px = Window.width

        # Calculate available width for grid layout
        available_width = screen_width_px - self.spacing[0] * 2

        # Calculate number of columns
        num_cols = int(available_width // (self.col_default_width + self.spacing[0]))

        # Set the number of columns of layout
        self.cols = max(num_cols, 1)

    def update_primary_palette(self, new_palette):
        """Update primary palette."""
        # Assign the value of new_palette to the corresponding palette
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

        # Get proper palette
        selected_palette = map_primary_palette.get(new_palette)

        if selected_palette:
            # Update app primary palette
            self.app.theme_cls.primary_palette = map_primary_palette.get(new_palette)

            # Update app primary palette in database
            self.pins_db.update_app_primary_palette(map_primary_palette.get(new_palette))

            # Close pin marker popups
            self.app.root.ids.screen_manager.get_screen('MapScreen').close_map_marker_popups()

            # Update GPS marker colors
            if self.app.gps_marker is not None:
                self.app.gps_marker.update_marker()
                self.app.gps_marker.update_dialog_button_color()

            return True

        return False

class AlarmSoundsList(BoxLayout):
    pass
