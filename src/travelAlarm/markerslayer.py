# Coding: UTF-8

# Copyright (C) 2024 Michał Prędki
# Licensed under the GNU General Public License v3.0.
# Full text of the license can be found in the LICENSE and COPYING files in the repository.

from math import radians, cos
from kivymd.app import MDApp
from kivy.graphics import Color, Ellipse, Line
from kivy_garden.mapview import MarkerMapLayer

from markers import MarkerAdder


class MarkersLayer(MarkerMapLayer):
    # Values to convert buffer size to meter
    unit_mult = {'m': 1, 'km': 1000}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.app = MDApp.get_running_app()

    def add_widget(self, marker):
        """Draw marker's buffer while adding marker to the map."""
        super().add_widget(marker)
        if isinstance(marker, MarkerAdder):
            return
        self.draw_buffer(marker)

    def remove_widget(self, marker):
        """Remove marker's buffer while adding marker to the map."""
        super().remove_widget(marker)
        if isinstance(marker, MarkerAdder):
            return
        self.remove_buffer(marker)

    def draw_buffer(self, marker):
        """Draw buffer on map_widget."""
        # Buffer center in screen pixels coordinates
        center_x, center_y = self.parent.get_window_xy_from(lat=marker.lat, lon=marker.lon, zoom=self.parent.zoom)
        # Buffer size in pixels
        buffer_size_dp = self.calculate_buffer_radius(marker)

        pos_x = center_x - buffer_size_dp
        pos_y = center_y - buffer_size_dp

        # Determine colors of buffer fill and outline
        theme_rgb = self.app.theme_cls.primary_color[:3]
        ellipse_color = theme_rgb + [.2]
        outline_color = theme_rgb + [.4]

        with self.canvas.before:
            # Draw the buffer circle
            Color(*ellipse_color) if marker.pin.is_active else Color(1, 0, 0, 0.1)
            marker.buffer['ellipse'] = Ellipse(pos=(pos_x, pos_y), size=(buffer_size_dp * 2, buffer_size_dp * 2))
            # Draw the buffer outline
            Color(*outline_color) if marker.pin.is_active else Color(1, 0, 0, 0.2)
            marker.buffer['outline'] = Line(width=1.5, circle=(center_x, center_y, buffer_size_dp))

    def calculate_buffer_radius(self, marker):
        """Calculate the buffer radius in pixels based on the buffer size, buffer unit, and current zoom level."""
        map_widget = self.parent
        zoom_level = map_widget.zoom
        map_scale = map_widget.scale
        # Scaled tile size
        dp_tile_size = map_widget.map_source.dp_tile_size
        # Recalculate buffer latitude to radians
        lat_radian = radians(marker.lat)
        # Earth equatorial circumference
        earth_circumference = 40075017
        # Calculate factor to calculate the buffer size
        meters_per_pixel = (earth_circumference * cos(lat_radian)) / (dp_tile_size * 2**zoom_level)
        buffer_size = marker.pin.buffer_size * self.unit_mult.get(marker.pin.buffer_unit, 0)

        return (buffer_size / meters_per_pixel) * map_scale

    def remove_buffer(self, marker):
        """Remove the buffer from the map widget."""
        ellipse = marker.buffer.get('ellipse')
        outline = marker.buffer.get('outline')

        if ellipse: self.canvas.before.remove(ellipse)
        if outline: self.canvas.before.remove(outline)

    def update_buffer(self, marker):
        """Update buffer position and size."""
        self.remove_buffer(marker)
        self.draw_buffer(marker)

    def reposition(self):
        """Update markers position while map is repositioning."""
        if not self.markers:
            return
        map_widget = self.parent
        # Reposition the markers depend on the latitude
        markers = sorted(self.markers, key=lambda pin: -pin.lat)
        for marker in markers:
            self.set_marker_position(map_widget, marker)
            if isinstance(marker, MarkerAdder):
                continue
            self.update_buffer(marker)
