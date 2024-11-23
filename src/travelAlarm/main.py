from kivymd.app import MDApp
from kivy.lang import Builder

from database import Database
from mapwidget import MapWidget
from gpsmarker import GpsMarker, check_gps_permission, request_location_permission
# from alarm import Alarm

class TravelAlarmApp(MDApp):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Create map_widget instance
        self.map_widget = MapWidget()

        # Create database instance
        self.pins_db = Database('pins.db')

        # Initialize GPS marker
        self.gps_marker = None

        # # Initialize alarm
        # self.alarm = None

    def add_gps_marker(self):
        """Add gps marker to map widget."""
        if check_gps_permission() and self.gps_marker is None:
            # Initialize GPS marker object
            self.gps_marker = GpsMarker()

            # Add GPS marker to map widget
            self.map_widget.add_layer(self.gps_marker)

            return True
        # If gps marker not added
        return False

    # def run_alarm(self, address, buffer_size, buffer_unit):
    #     self.alarm = Alarm(address, buffer_size, buffer_unit)

    def build(self):
        """Build app."""
        # Set app themes
        self.theme_cls.theme_style = self.pins_db.theme_style
        self.theme_cls.primary_palette = self.pins_db.primary_palette

        # Request location permissions
        request_location_permission()

        return Builder.load_file("main.kv")

    def on_start(self):
        """Check localization permissions and add gps marker to map widget."""
        self.add_gps_marker()

        return True

    def on_pause(self):
        """Prepare app to close."""
        # Save map_widget state and close connection to database
        self.on_stop()

        return True

    def on_resume(self):
        """Return database connection."""
        # Reconnect to the database and reload the map state
        self.pins_db.connect('pins.db')

        return True

    def on_stop(self):
        """Save map_widget state and disconnect from database."""
        # Save current map_widget state
        self.pins_db.save_mapview_state()

        # Close connection with database while turn off the app
        self.pins_db.disconnect()

        return True

if __name__ == '__main__':
    TravelAlarmApp().run()
