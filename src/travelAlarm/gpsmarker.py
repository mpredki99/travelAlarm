from kivymd.app import MDApp
from kivy.graphics import Color, Ellipse
from kivy_garden.mapview import MapLayer
from kivy.animation import Animation
from kivy.metrics import dp

from kivymd.uix.button import MDFlatButton
from kivymd.uix.dialog import MDDialog
from kivy.clock import Clock, mainthread


class GpsMarker(MapLayer):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Get app instance
        self.app = MDApp.get_running_app()

        # Get map_widget instance
        self.map_widget = self.app.map_widget

        # Initialize gps dialog
        self.gps_dialog = None
        self.gps_button = None
        self.build_gps_dialog()

        # Initialize position
        self.latitude = None
        self.longitude = None

        # Define size of marker
        self.base_size = dp(16)
        self.marker_size = (self.base_size, self.base_size)
        self.blinker_size = (self.base_size, self.base_size)

        # Initialize blinker attributes
        self.blinker = None
        self.blinker_color = None
        self.blinker_center = None

        # Initialize provider status
        self.provider_status = 'provider-enabled'

        # Wait half second to build UI and then initialize GPS
        Clock.schedule_once(lambda dt: self.initialize_gps(), .5)

    def build_gps_dialog(self):
        self.gps_button = MDFlatButton(
            text='OK',
            theme_text_color='Custom',
            text_color=self.app.theme_cls.primary_color,
        )
        self.gps_dialog = MDDialog(
            title='Enable Localization',
            text='Enable localization to ensure the application works properly.',
            buttons=[self.gps_button]
        )
        self.gps_button.bind(on_press=self.gps_dialog.dismiss)

        return True

    def initialize_gps(self):
        try:
            from plyer import gps

            gps.configure(on_location=self.update_localization, on_status=self.update_status)
            gps.start(minTime=1000, minDistance=1)
            return True
        except NotImplementedError:
            return False
        except ModuleNotFoundError:
            return False
        except Exception:
            return False

    def update_status(self, stype, status):
        if stype == 'provider-disabled' and stype != self.provider_status:
            self.provider_status = stype
            self.enable_gps()
            return True

        elif stype == 'provider-enabled' and stype != self.provider_status:
            self.provider_status = stype
            Clock.schedule_once(lambda dt: self.reposition(), .5)
            return True

        return False

    @mainthread
    def enable_gps(self):
        self.gps_dialog.open()

    def update_localization(self, **kwargs):
        self.latitude = kwargs['lat']
        self.longitude = kwargs['lon']

        if self.blinker_color is None and self.blinker is None:
            self.update_marker()

        return True

    def draw_marker(self):
        if self.latitude is None or self.longitude is None:
            return False
        pos_x, pos_y = self.map_widget.get_window_xy_from(lat=self.latitude, lon=self.longitude, zoom=self.map_widget.zoom)
        self.blinker_center = (pos_x, pos_y)

        marker_pos = (pos_x - self.marker_size[0] / 2, pos_y - self.marker_size[1] / 2)
        blinker_pos = (pos_x - self.blinker_size[0] / 2, pos_y - self.blinker_size[1] / 2)

        with self.canvas:
            Color(*self.app.theme_cls.primary_dark)
            Ellipse(size=self.marker_size, pos=marker_pos)

        if self.provider_status == 'provider-enabled':
            with self.canvas.before:
                self.blinker_color = Color(*self.app.theme_cls.primary_dark)
                self.blinker = Ellipse(size=self.blinker_size, pos=blinker_pos)

            self.blink()

    def update_marker(self, *args):
        # Cancel animations before drawing new marker
        self.cancel_animations()
        self.canvas.clear()

        self.draw_marker()

    def reposition(self, *args):
        self.update_marker()

    def update_blinker_position(self, *args):
        new_size = self.blinker.size
        self.blinker.pos = (self.blinker_center[0] - new_size[0] / 2, self.blinker_center[1] - new_size[1] / 2)

    def blink(self):
        anim_color = Animation(a=0)
        anim_color.start(self.blinker_color)

        # Animation for size change to create a pulsing effect and keep it centered
        anim_size = Animation(size=(self.base_size * 3, self.base_size * 3))
        anim_size.bind(on_progress=self.update_blinker_position, on_complete=self.update_marker)
        anim_size.start(self.blinker)

    def cancel_animations(self):
        # Cancel blinker animations
        Animation.cancel_all(self.blinker_color)
        Animation.cancel_all(self.blinker)

        # Clear any existing blinker drawing
        self.canvas.before.clear()

        self.blinker = None
        self.blinker_color = None
