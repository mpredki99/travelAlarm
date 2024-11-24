from kivymd.app import MDApp
from kivy import platform
from kivy_garden.mapview import MapLayer
from kivy.graphics import Color, Ellipse
from kivy.animation import Animation
from kivymd.uix.button import MDFlatButton
from kivymd.uix.dialog import MDDialog
from kivy.clock import Clock, mainthread
from kivy.metrics import dp
from geopy.distance import geodesic

from buffer import Buffer
from alarm import Alarm


def check_gps_permission():
    """Check localization permissions for android devices."""
    if platform == 'android':
        from android.permissions import Permission, check_permission
        return check_permission(Permission.ACCESS_FINE_LOCATION) and check_permission(Permission.ACCESS_COARSE_LOCATION)
    elif platform == 'ios':
        return True

    return False


def request_location_permission():
    """Request localization permissions for android devices."""
    if platform == 'android' and not check_gps_permission():
        from android.permissions import Permission, request_permissions
        request_permissions([Permission.ACCESS_FINE_LOCATION, Permission.ACCESS_COARSE_LOCATION])

        return True


class GpsMarker(MapLayer):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Get app instance
        self.app = MDApp.get_running_app()

        # Get map widget instance
        self.map_widget = self.app.map_widget

        # Initialize GPS dialog
        self.gps_dialog = None
        self.gps_button = None
        self.build_gps_dialog()

        # Initialize position
        self.latitude = None
        self.longitude = None
        self.marker_center = None

        # Define size of marker
        self.base_size = dp(16)
        self.marker_size = (self.base_size, self.base_size)
        self.blinker_size = (self.base_size, self.base_size)

        # Initialize blinker attributes
        self.blinker = None
        self.blinker_color = None

        # Initialize provider status
        self.provider_status = 'provider-enabled'

        # Wait half second to build UI and then initialize GPS
        Clock.schedule_once(lambda dt: self.initialize_gps(), .5)

    def build_gps_dialog(self):
        """Build dialog window about providing localization."""

        # Build button to close dialog window
        self.gps_button = MDFlatButton(
            text='OK',
            theme_text_color='Custom',
            text_color=self.app.theme_cls.primary_color,
        )
        # Build dialog window
        self.gps_dialog = MDDialog(
            title='Enable Localization',
            text='Enable localization to ensure the application works properly.',
            buttons=[self.gps_button]
        )
        # Bind button event to close dialog window
        self.gps_button.bind(on_press=self.gps_dialog.dismiss)

        return True

    def update_dialog_button_color(self):
        """Update dialog button text color."""
        self.gps_button.text_color = self.app.theme_cls.primary_color

        return True

    def initialize_gps(self):
        """Configure plyer gps object to get user localization."""
        try:
            from plyer import gps

            # Configure gps object
            gps.configure(on_location=self.update_localization, on_status=self.update_status)
            gps.start(minTime=1000, minDistance=1)

            return True
        # Handle exceptions
        except NotImplementedError:
            return False
        except ModuleNotFoundError:
            return False
        except Exception:
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
            Clock.schedule_once(lambda dt: self.update_marker(), .5)

            return True

        return False

    @mainthread
    def enable_gps(self):
        """Open GPS dialog window on main thread."""
        self.gps_dialog.open()

        return True

    def update_localization(self, **kwargs):
        """Update marker localization attributes."""
        self.latitude = kwargs['lat']
        self.longitude = kwargs['lon']

        # Draw marker if not in map widget yet
        if self.blinker is None and self.blinker_color is None:
            Clock.schedule_once(lambda dt: self.update_marker(), .1)

        # Check if user is within active buffer
        self.is_within_buffer()

        return True

    def draw_marker(self):
        """Draw marker on map widget."""
        # Check if GPS marker has localization attributes
        if self.latitude is None or self.longitude is None:
            return False

        # Get marker position in screen coordinates
        self.marker_center = self.map_widget.get_window_xy_from(lat=self.latitude, lon=self.longitude, zoom=self.map_widget.zoom)

        # Define position of GPS marker
        marker_pos = (self.marker_center[0] - self.marker_size[0] / 2, self.marker_center[1] - self.marker_size[1] / 2)
        blinker_pos = (self.marker_center[0] - self.blinker_size[0] / 2, self.marker_center[1] - self.blinker_size[1] / 2)

        # Draw inner marker
        with self.canvas:
            Color(*self.app.theme_cls.primary_dark)
            Ellipse(size=self.marker_size, pos=marker_pos)

        # If localization is enabled
        if self.provider_status == 'provider-enabled':
            # Draw blinker marker
            with self.canvas.before:
                self.blinker_color = Color(*self.app.theme_cls.primary_dark)
                self.blinker = Ellipse(size=self.blinker_size, pos=blinker_pos)

            # Run blinking animation
            self.blink()

    def blink(self):
        """Run blinking animation on GPS marker."""
        # Define animation for blinker transparency
        anim_color = Animation(a=0)

        # Animation for size change to create a pulsing effect and keep it centered
        anim_size = Animation(size=(self.base_size * 3, self.base_size * 3))
        anim_size.bind(on_progress=self.update_blinker_position, on_complete=self.update_marker)

        # Start animations
        anim_color.start(self.blinker_color)
        anim_size.start(self.blinker)

    def update_blinker_position(self, *args):
        """Update blinker position while its size is increasing."""
        # Get actual blinker size
        new_size = self.blinker.size

        # Update blinker position
        self.blinker.pos = (self.marker_center[0] - new_size[0] / 2, self.marker_center[1] - new_size[1] / 2)

    def cancel_animations(self):
        """Cancel blinker animations and clear canvas."""
        # Cancel blinker animations
        Animation.cancel_all(self.blinker_color)
        Animation.cancel_all(self.blinker)

        # Clear any existing blinker drawing
        self.canvas.before.clear()

    def update_marker(self, *args):
        """Update GPS marker on map widget."""
        # Cancel animations before drawing new marker
        self.cancel_animations()

        # Clear inner marker drawing
        self.canvas.clear()

        # Draw GPS marker
        self.draw_marker()

    def reposition(self, *args):
        """Update map widget."""
        self.update_marker()

    def is_within_buffer(self):
        """Check if user is within active buffer and trigger alarm if so."""
        # Get pins from database
        pins = self.app.pins_db.pins

        # Get unit multiplier
        unit_mult = Buffer.unit_mult

        # Create user position tuple
        user_pos = (self.latitude, self.longitude)

        for pin_id in pins:
            # Skip buffer if pin is not active
            if not pins[pin_id].get('is_active'):
                continue

            # Create pin position tuple
            pin_pos = (pins[pin_id].get('latitude', 0), pins[pin_id].get('longitude', 0))

            # Get pin address, buffer size and buffer unit
            address = pins[pin_id].get('address')
            buffer_size = pins[pin_id].get('buffer_size', 0)
            buffer_unit = pins[pin_id].get('buffer_unit')

            # Convert buffer size to meters
            buffer_meters = buffer_size * unit_mult.get(buffer_unit, 0)

            # Calculate distance from user to pin
            buffer_distance = geodesic(user_pos, pin_pos).meters

            # Check if user is within buffer size
            if buffer_distance <= buffer_meters:
                # Create alarm object and trigger alarm
                Clock.schedule_once(lambda dt: Alarm(pin_id, address, buffer_size, buffer_unit), .1)
