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

    # Values to calculate buffer size in meter
    unit_mult = {'m': 1, 'km': 1000}

    def __init__(self, **kwargs):  # is_active, latitude, longitude, buffer_size, buffer_unit,
        super().__init__(**kwargs)
        # Get app instance
        self.app = MDApp.get_running_app()

    def add_widget(self, marker):
        super().add_widget(marker)
        if isinstance(marker, MarkerAdder):
            return
        self.draw_buffer(marker)

    def remove_widget(self, marker):
        super().remove_widget(marker)
        if isinstance(marker, MarkerAdder):
            return
        self.remove_buffer(marker)

    def draw_buffer(self, marker):
        """Draw buffer on map_widget."""
        # Compute position and size of the buffer circle in pixels
        pos_x, pos_y = self.parent.get_window_xy_from(lat=marker.lat, lon=marker.lon, zoom=self.parent.zoom)
        buffer_size_dp = self.calculate_buffer_radius(marker)

        center_x = pos_x - buffer_size_dp
        center_y = pos_y - buffer_size_dp

        # Determine colors of buffer fill and outline
        theme_rgb = self.app.theme_cls.primary_color[:3]
        ellipse_color = theme_rgb + [.2]
        outline_color = theme_rgb + [.4]

        with self.canvas.before:
            # Draw the buffer circle
            marker.buffer['ellipse_color'] = Color(*ellipse_color) if marker.pin.is_active else Color(1, 0, 0, 0.1)
            marker.buffer['ellipse'] = Ellipse(pos=(center_x, center_y), size=(buffer_size_dp * 2, buffer_size_dp * 2))

            # Draw the buffer outline
            marker.buffer['outline_color'] = Color(*outline_color) if marker.pin.is_active else Color(1, 0, 0, 0.2)
            marker.buffer['outline'] = Line(width=1.5, circle=(pos_x, pos_y, buffer_size_dp))

    def calculate_buffer_radius(self, marker):
        """Calculate the buffer radius in pixels based on buffer size, buffer unit, and current zoom level."""
        map_widget = self.parent
        # Get map_widget zoom
        zoom_level = map_widget.zoom

        # Get scaled tile size
        dp_tile_size = map_widget.map_source.dp_tile_size

        # Recalculate buffer latitude to radians
        lat_radian = radians(marker.lat)

        # Earth equatorial circumference
        earth_circumference = 40075017

        # Calculate factor to calculate the buffer size
        meters_per_pixel = (earth_circumference * cos(lat_radian)) / (dp_tile_size * 2**zoom_level)
        buffer_size = marker.pin.buffer_size * self.unit_mult.get(marker.pin.buffer_unit, 0)

        return (buffer_size / meters_per_pixel) * map_widget.scale

    def remove_buffer(self, marker):
        ellipse_color = marker.buffer.get('ellipse_color')
        ellipse = marker.buffer.get('ellipse')

        outline_color = marker.buffer.get('outline_color')
        outline = marker.buffer.get('outline')

        if ellipse_color: self.canvas.before.remove(ellipse_color)
        if ellipse: self.canvas.before.remove(ellipse)

        if outline_color: self.canvas.before.remove(outline_color)
        if outline: self.canvas.before.remove(outline)

    def update_buffer(self, marker):
        """Update buffer position and size."""
        self.remove_buffer(marker)
        self.draw_buffer(marker)

    def reposition(self):
        if not self.markers:
            return
        map_widget = self.parent
        # reposition the markers depending the latitude
        markers = sorted(self.markers, key=lambda pin: -pin.lat)
        for marker in markers:
            self.set_marker_position(map_widget, marker)
            if isinstance(marker, MarkerAdder):
                continue
            self.update_buffer(marker)
