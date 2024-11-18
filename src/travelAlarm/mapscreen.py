from kivymd.app import MDApp
from kivy.uix.screenmanager import Screen


class MapScreen(Screen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Get app instance
        self.app = MDApp.get_running_app()

        # Get pins database instance
        self.pins_db = self.app.pins_db

        # Get map_widget instance
        self.map_widget = self.app.map_widget

        # Add map_widget to the MapScreen
        self.add_widget(self.map_widget)

        # Draw pins from database to the map
        for pin_id in self.pins_db.pins:
            self.pins_db.draw_mapview_buffer(pin_id)

            # Close pin marker popups
            pin = self.pins_db.pins[pin_id].get('marker')
            if pin: pin.close_marker_popup()

    def close_map_marker_popups(self, pin_id=None):
        """Close pin marker popups. Skip for pin with provided pin id."""
        for key, value in self.pins_db.pins.items():
            # Skip id pin id is the same as provided
            if key == pin_id:
                continue

            # Close pin marker popup
            pin = value.get('marker')
            if pin: pin.close_marker_popup()

    def center_mapview_on_user_location(self):
        """Center the map_widget on user GPS position."""
        self.app.add_gps_marker()
        gps_marker = self.app.gps_marker

        # If gps in mapview
        if gps_marker is not None:
            # Get user location
            user_lat, user_lon = gps_marker.latitude, gps_marker.longitude

            # if GPS marker have no location data
            if user_lat is None or user_lon is None:
                return False

            # Center the map on the user's location
            self.center_mapview_on_lat_lon(user_lat, user_lon)
            return True

        # If no instance of GPS marker
        return False

    def center_mapview_on_lat_lon(self, latitude, longitude):
        """Center map_widget on provided latitude and longitude."""
        self.map_widget.center_on(latitude, longitude)
        self.map_widget.zoom = 11
