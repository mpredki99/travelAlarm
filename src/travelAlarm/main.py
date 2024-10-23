from kivymd.app import MDApp
from kivy.lang import Builder

from database import Database
from mapwidget import MapWidget

class TravelAlarmApp(MDApp):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Create map_widget instance
        self.map_widget = MapWidget()

        # Create database instance
        self.pins_db = Database('pins.db')

    def on_stop(self):
        """Save map_widget state and disconnect from database."""
        # Save current map_widget state
        self.pins_db.save_mapview_state()

        # Close connection with database while turn off the app
        self.pins_db.disconnect()

    def on_pause(self):
        """Prepare app to close."""
        # Save current map_widget state
        self.pins_db.save_mapview_state()

        # Close connection with database while turn off the app
        self.pins_db.disconnect()

    def on_resume(self):
        """Return database connection."""
        # Reconnect to the database and reload the map state
        self.pins_db.connect('pins.db')

    def build(self):
        """Build app."""
        # Set app themes
        self.theme_cls.theme_style = self.pins_db.theme_style
        self.theme_cls.primary_palette = self.pins_db.primary_palette

        return Builder.load_file("main.kv")


if __name__ == '__main__':
    TravelAlarmApp().run()
