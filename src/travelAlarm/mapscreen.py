# Coding: UTF-8

# Copyright (C) 2024 Michał Prędki
# Licensed under the GNU General Public License v3.0.
# Full text of the license can be found in the LICENSE and COPYING files in the repository.

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
        # self.pins_db.draw_mapview_buffers()

    def center_map_widget_on_user_location(self):
        """Center the map widget on user GPS position."""
        # Add GPS marker if not in mapview
        self.app.add_gps_marker()

        # Get instance of GPS marker
        gps_marker = self.app.gps_marker

        # If no instance of GPS marker
        if gps_marker is None:
            return False

        # Get user location
        user_lat, user_lon = gps_marker.latitude, gps_marker.longitude

        # If GPS marker have no location data
        if user_lat is None or user_lon is None:
            return False

        # Center the map on the user's location
        self.center_mapview_on_lat_lon(user_lat, user_lon)
        return True

    def center_mapview_on_lat_lon(self, latitude, longitude):
        """Center map widget on provided latitude and longitude."""
        self.map_widget.center_on(latitude, longitude)
        self.map_widget.zoom = 11
