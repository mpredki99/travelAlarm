# Coding: UTF-8

# Copyright (C) 2024 Michał Prędki
# Licensed under the GNU General Public License v3.0.
# Full text of the license can be found in the LICENSE and COPYING files in the repository.

from kivymd.app import MDApp
from kivy import platform
from kivy.properties import ObjectProperty, NumericProperty, StringProperty
from kivy_garden.mapview import MapLayer
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton
from kivy.graphics import Color, Ellipse
from kivy.animation import Animation
from kivy.clock import Clock, mainthread
from kivy.metrics import dp
from geopy.distance import geodesic

from markerslayer import MarkersLayer
from alarm import Alarm


def request_location_permission():
    """Request localization permissions for android devices."""
    if platform == 'android' and not check_gps_permission():
        from android.permissions import Permission, request_permissions
        request_permissions([Permission.ACCESS_FINE_LOCATION, Permission.ACCESS_COARSE_LOCATION])


def check_gps_permission():
    """Check localization permissions for android devices."""
    if platform == 'android':
        from android.permissions import Permission, check_permission
        return check_permission(Permission.ACCESS_FINE_LOCATION) and check_permission(Permission.ACCESS_COARSE_LOCATION)
    elif platform == 'ios':
        return True
    return False


class GpsMarker(MapLayer):
    # Dialog box to enable GPS
    gps_dialog = ObjectProperty()
    gps_dialog_button = ObjectProperty()
    # User's geographic position
    latitude = NumericProperty(None)
    longitude = NumericProperty(None)
    # Marker's position on the screen
    marker_center = ()
    # Marker geometry attributes
    base_size = dp(16)
    marker_size = (base_size, base_size)
    inner_marker = ObjectProperty()
    blinker_color = ObjectProperty()
    blinker = ObjectProperty()
    # Localization provider status
    provider_status = StringProperty('provider-enabled')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.app = MDApp.get_running_app()
        self.map_widget = self.app.map_widget

        self.layer = self.app.map_widget.marker_layer

        self.build_gps_dialog()

        # Wait a second to build UI and then initialize GPS
        Clock.schedule_once(lambda dt: self.initialize_gps(), 1)

    def build_gps_dialog(self):
        """Build dialog window about providing localization service."""
        # Build button to close dialog window
        self.gps_dialog_button = MDFlatButton(
            text='OK',
            theme_text_color='Custom',
            text_color=self.app.theme_cls.primary_color,
        )
        # Build dialog window
        self.gps_dialog = MDDialog(
            title='Enable Localization',
            text='Enable localization to ensure the application works properly.',
            buttons=[self.gps_dialog_button]
        )
        # Bind button event to close dialog window
        self.gps_dialog_button.bind(on_press=self.gps_dialog.dismiss)

    def update_dialog_button_color(self):
        """Update gps dialog button text color."""
        self.gps_dialog_button.text_color = self.app.theme_cls.primary_color

    def initialize_gps(self):
        """Configure plyer gps object to get user localization."""
        try:
            from plyer import gps
            # Configure gps object
            gps.configure(on_location=self.update_localization, on_status=self.update_status)
            gps.start(minTime=1000, minDistance=1)
            return True
        except:
            # If provider wasn't initialized
            return False

    def update_status(self, stype, status):
        """Update gps provider status."""
        # Check if provider status value was changed
        if stype == 'provider-disabled' and stype != self.provider_status:
            # Update value of provider status
            self.provider_status = stype
            # Open dialog window
            self.enable_gps()
            return True

        # Check if provider status value was changed
        elif stype == 'provider-enabled' and stype != self.provider_status:
            # Update value of provider status
            self.provider_status = stype
            # Update GPS marker to start blinking again
            Clock.schedule_once(lambda dt: self.update_marker(), 0)
            return True

        # If status didn't change
        return False

    @mainthread
    def enable_gps(self):
        """Open GPS dialog window on main thread."""
        self.gps_dialog.open()

    def update_localization(self, **kwargs):
        """Update marker localization attributes."""
        self.latitude = kwargs['lat']
        self.longitude = kwargs['lon']

        # Draw marker if not in map widget yet
        if self.blinker is None:
            Clock.schedule_once(lambda dt: self.update_marker(), 0)

    def update_marker_center(self):
        """Update marker center in screen coordinates."""
        self.marker_center = self.map_widget.get_window_xy_from(lat=self.latitude, lon=self.longitude, zoom=self.map_widget.zoom)

    def draw_marker(self):
        """Draw marker on map widget."""
        # Check if GPS marker has the localization attributes
        if self.latitude is None or self.longitude is None:
            return False  # Marker hasn't been drawn

        self.update_marker_center()

        marker_pos = (self.marker_center[0] - self.marker_size[0] / 2, self.marker_center[1] - self.marker_size[1] / 2)
        with self.layer.canvas.before:
            Color(*self.app.theme_cls.primary_dark)
            self.inner_marker = Ellipse(size=self.marker_size, pos=marker_pos)

        if self.provider_status == 'provider-disabled':
            return True  # Marker has been drawn without blink

        with self.layer.canvas.before:
            self.blinker_color = Color(*self.app.theme_cls.primary_dark)
            self.blinker = Ellipse(size=self.marker_size, pos=marker_pos)

        self.blink()  # Run blinking animation
        return True  # Marker has been drawn with blink

    def blink(self):
        """Run blinking animation on GPS marker."""
        # Animation for blinker transparency
        anim_color = Animation(a=0)
        # Animation for size change to create a pulsing effect
        anim_size = Animation(size=(self.base_size * 3, self.base_size * 3))

        anim_size.bind(
            on_start=self.is_within_buffer,
            on_progress=self.update_blinker_position,
            on_complete=self.update_marker
        )
        # Start animations
        anim_color.start(self.blinker_color)
        anim_size.start(self.blinker)

    def update_blinker_position(self, *args):
        """Update blinker position while its size is increasing."""
        # Get actual blinker size
        new_size = self.blinker.size
        # Update blinker position
        self.blinker.pos = (self.marker_center[0] - new_size[0] / 2, self.marker_center[1] - new_size[1] / 2)

    def update_inner_marker_position(self):
        """Update marker position."""
        self.inner_marker.pos = (self.marker_center[0] - self.marker_size[0] / 2, self.marker_center[1] - self.marker_size[1] / 2)

    def cancel_animations(self):
        """Cancel blinker animation and clear marker geometry."""
        Animation.cancel_all(self.blinker_color)
        Animation.cancel_all(self.blinker)
        # Clear marker drawings
        if self.inner_marker: self.layer.canvas.before.remove(self.inner_marker)
        if self.blinker: self.layer.canvas.before.remove(self.blinker)

    def update_marker(self, *args):
        """Update GPS marker on map_widget."""
        self.cancel_animations()
        self.draw_marker()

    def reposition(self, *args):
        """Update marker position while map is moving."""
        if self.inner_marker is None or self.blinker is None:
            return False
        self.update_marker_center()
        self.update_inner_marker_position()
        self.update_blinker_position()

    def is_within_buffer(self, *args):
        """Check if user is within active buffer and trigger alarm if so."""
        # Get unit multiplier
        unit_mult = MarkersLayer.unit_mult
        # Create user position tuple
        user_pos = (self.latitude, self.longitude)

        for marker in self.app.markers.values():
            # Skip buffer if pin is not active
            if not marker.pin.is_active:
                continue
            # Create pin position tuple
            pin_pos = (marker.lat, marker.lon)
            # Get pin's buffer size
            buffer_size = marker.pin.buffer_size
            buffer_unit = marker.pin.buffer_unit
            buffer_size_meters = buffer_size * unit_mult.get(buffer_unit, 0)
            # Calculate distance from user to pin
            distance = geodesic(user_pos, pin_pos).meters
            # Check if user is within buffer size
            if distance <= buffer_size_meters:
                # Trigger alarm
                Alarm(marker)
