from math import radians, cos

from kivymd.app import MDApp
from kivy.graphics import Color, Ellipse, Line
from kivy_garden.mapview import MapLayer


class Buffer(MapLayer):

    # Values to calculate buffer size in meter
    unit_mult = {'m': 1, 'km': 1000}

    def __init__(self, is_active, latitude, longitude, buffer_size, buffer_unit, **kwargs):
        super().__init__(**kwargs)

        # Get app instance
        self.app = MDApp.get_running_app()

        # Get map_widget instance
        self.mapview = self.app.map_widget

        # Assign buffer attributes
        self.is_active = is_active
        self.latitude = latitude
        self.longitude = longitude
        self.buffer_size = buffer_size * self.unit_mult.get(buffer_unit, 0)

        # Initialize variable of buffer geometry
        self.buffer = None

        # Create buffer geometry
        self.draw_buffer()

    def draw_buffer(self):
        """Draw buffer on map_widget."""
        # Compute position and size of the buffer circle in pixels
        pos_x, pos_y = self.mapview.get_window_xy_from(lat=self.latitude, lon=self.longitude, zoom=self.mapview.zoom)
        buffer_size_px = self.calculate_buffer_radius()

        center_x = pos_x - buffer_size_px
        center_y = pos_y - buffer_size_px

        # Determine colors of buffer fill and outline
        theme_rgb = self.app.theme_cls.primary_color[:3]
        ellipse_color = theme_rgb + [.2]
        line_color = theme_rgb + [.4]

        with self.canvas.before:
            # Draw the buffer circle
            Color(*ellipse_color) if self.is_active else Color(1, 0, 0, 0.1)
            self.buffer = Ellipse(pos=(center_x, center_y), size=(buffer_size_px * 2, buffer_size_px * 2))

            # Draw the buffer outline
            Color(*line_color) if self.is_active else Color(1, 0, 0, 0.2)
            self.buffer = Line(width=1.5, circle=(pos_x, pos_y, buffer_size_px))

    def calculate_buffer_radius(self):
        """Calculate the buffer radius in pixels based on buffer size, buffer unit, and current zoom level."""

        # Get map_widget zoom
        zoom_level = self.mapview.zoom

        # Recalculate buffer latitude to radians
        lat_radian = radians(self.latitude)

        # Earth equatorial circumference
        earth_circumference = 40075017

        # Calculate factor to calculate the buffer size
        meters_per_pixel = (earth_circumference * cos(lat_radian)) / (2**zoom_level * 256)

        return self.buffer_size / meters_per_pixel

    def update_buffer(self):
        """Update buffer position and size."""
        # Clear any existing circle drawing
        self.canvas.before.clear()
        self.draw_buffer()

    def reposition(self, *args):
        """Reposition the circle when the map_widget moves or zooms."""
        self.update_buffer()
