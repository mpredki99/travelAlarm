# Coding: UTF-8
from kivymd.toast import toast
# Copyright (C) 2024 Michał Prędki
# Licensed under the GNU General Public License v3.0.
# Full text of the license can be found in the LICENSE and COPYING files in the repository.

from kivymd.app import MDApp
from kivy.lang import Builder
from kivy.properties import ObjectProperty, StringProperty, DictProperty

from database import Database
from mapwidget import MapWidget
from gpsmarker import GpsMarker, check_gps_permission, request_location_permission


class TravelAlarmApp(MDApp):
    """
    Travel alarm application. The alarm is triggered when the user
    is within a buffer range set in relation to a specified location.

    Application contains three main screens:
    - MapScreen - displays Open Street Map, user's location and user's markers;
    - ListScreen - displays list of user's markers and enables searching new locations based on provided address;
    - SettingsScreen - enables choosing of app mode, theme, alarm sound and save the settings into database;
    """

    map_widget = ObjectProperty()
    database = ObjectProperty()
    alarm_file = StringProperty()
    gps_marker = ObjectProperty()
    markers = DictProperty()

    def build(self):
        """Build the app."""
        self.map_widget = MapWidget()
        self.database = Database('pins.db')

        # Get data from database
        self.theme_cls.theme_style = self.database.theme_style
        self.theme_cls.primary_palette = self.database.primary_palette
        self.alarm_file = self.database.alarm_file
        self.markers = self.database.get_markers()

        # Request location permissions for android devices
        request_location_permission()

        return Builder.load_file("main.kv")

    def on_start(self):
        """Add GPS marker at user's location when the app is started."""
        # self.add_gps_marker()
        return True

    def on_pause(self):
        """Prepare the app to close when it is moving to the background."""
        self.on_stop()
        return True

    def on_resume(self):
        """Reconnect to the database when the app is returning from the background."""
        self.database.connect()
        return True

    def on_stop(self):
        """Save map_widget state and disconnect with the database when the app is closing."""
        self.database.save_mapview_state()
        self.database.disconnect()
        return True

    def add_gps_marker(self):
        """Add gps marker to the map_widget."""
        if check_gps_permission() and self.gps_marker is None:
            # self.gps_marker = GpsMarker()
            # self.map_widget.add_layer(self.gps_marker)
            return True  # If marker was added
        return False # If no location permissions have been granted or gps_marker is already on the map_widget


if __name__ == '__main__':
    TravelAlarmApp().run()
