from kivymd.app import MDApp
from kivy.lang import Builder
from kivy import platform

from plyer import gps

from database import Database
from mapwidget import MapWidget
from gpsmarker import GpsMarker


class TravelAlarmApp(MDApp):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Create map_widget instance
        self.map_widget = MapWidget()

        # Create database instance
        self.pins_db = Database('pins.db')

        # Initialize gps marker
        self.gps_marker = None

    def check_gps_permission(self):
        if platform == 'android':
            from android.permissions import Permission, check_permission
            return check_permission(Permission.ACCESS_FINE_LOCATION) and check_permission(Permission.ACCESS_COARSE_LOCATION)
        elif platform == 'ios':
            return True

        return False

    def request_location_permission(self):
        if platform == 'android' and not self.check_gps_permission():
            from android.permissions import Permission, request_permissions
            request_permissions([Permission.ACCESS_FINE_LOCATION, Permission.ACCESS_COARSE_LOCATION])

    def add_gps_marker(self):
        """Add gps marker to map widget."""
        if self.check_gps_permission() and self.gps_marker is None:
            # Initialize gps marker object
            self.gps_marker = GpsMarker()

            # Add gps marker to map widget
            self.map_widget.add_layer(self.gps_marker)
            return True
        return False

    def build(self):
        """Build app."""
        # Set app themes
        self.theme_cls.theme_style = self.pins_db.theme_style
        self.theme_cls.primary_palette = self.pins_db.primary_palette

        # Request location permissions
        self.request_location_permission()

        return Builder.load_file("main.kv")

    def on_start(self):
        self.add_gps_marker()

    def on_pause(self):
        """Prepare app to close."""
        # Save map_widget state and close connection to database
        self.on_stop()

        return True

    def on_resume(self):
        """Return database connection."""
        # Reconnect to the database and reload the map state
        self.pins_db.connect('pins.db')

    def on_stop(self):
        """Save map_widget state and disconnect from database."""
        # Save current map_widget state
        self.pins_db.save_mapview_state()

        # Close connection with database while turn off the app
        self.pins_db.disconnect()

if __name__ == '__main__':
    TravelAlarmApp().run()
