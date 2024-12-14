# Coding: UTF-8

# Copyright (C) 2024 Michał Prędki
# Licensed under the GNU General Public License v3.0.
# Full text of the license can be found in the LICENSE and COPYING files in the repository.

from kivy_garden.mapview import MapView, MapSource
from kivy.clock import Clock

from markers import MarkerAdder
from markerslayer import MarkersLayer


class MapWidget(MapView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Set minimum zoom value as 3
        self.map_source = MapSource(min_zoom=3)
        # Enable smooth zooming
        self.snap_to_zoom = False

        # Variables for handling on_hold event
        self._is_screen_held = False
        self._hold_duration_clock = None

        self._default_marker_layer = MarkersLayer()
        self.add_layer(self._default_marker_layer)

    @property
    def marker_layer(self):
        """Property to get default marker layer."""
        return self._default_marker_layer

    def on_touch_down(self, touch):
        """Update the _is_screen_held flag and start the clock for on_hold event."""
        self._is_screen_held = True
        self._hold_duration_clock = Clock.schedule_once(lambda dt: self.on_hold(touch), 1)
        # Handle default touch down event
        return super().on_touch_down(touch)
        
    def on_touch_move(self, touch):
        """Update the _is_screen_held flag and cancel the clock for on_hold event."""
        self._is_screen_held = False
        if self._hold_duration_clock: self._hold_duration_clock.cancel()
        # Handle default touch move event
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        """Update the _is_screen_held flag and cancel the clock for on_hold event."""
        self._is_screen_held = False
        if self._hold_duration_clock: self._hold_duration_clock.cancel()
        # Handle default touch up event
        super().on_touch_up(touch)

    def on_hold(self, touch):
        """Add new marker to the map_widget."""
        if self._is_screen_held:
            touch_lat, touch_lon = self.get_latlon_at(*touch.pos, self.zoom)
            self.add_marker(MarkerAdder(lat=touch_lat, lon=touch_lon))
            return True
        else:
            return False
