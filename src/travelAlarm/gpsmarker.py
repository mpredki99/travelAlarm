from kivymd.app import MDApp
from kivy.graphics import Color, Ellipse
from kivy_garden.mapview import MapLayer
from kivy.animation import Animation
from kivy.metrics import dp
from plyer import gps
from kivymd.uix.button import MDFlatButton
from kivymd.uix.dialog import MDDialog
from kivymd.toast import toast


class GpsMarker(MapLayer):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Get app instance
        self.app = MDApp.get_running_app()

        # Get map_widget instance
        self.map_widget = self.app.map_widget

        # Define size of marker
        self.base_size = dp(16)
        self.marker_size = (self.base_size, self.base_size)
        self.blinker_size = (self.base_size, self.base_size)

        # Initialize blinker attributes
        self.blinker = None
        self.blinker_color = None
        self.blinker_center = None

        # Initialize marker positions
        self.latitude = None
        self.longitude = None

        # Initialize provider status
        self.provider = 'provider-enabled'

        try:
            gps.configure(on_location=self.update_lat_lon, on_status=self.on_status)
            gps.start(minTime=1000, minDistance=1)
        except NotImplementedError:
            self.enable_gps()

    def enable_gps(self):
        toast(text=str("Enable Localization"))
        # self.button = MDFlatButton(
        #                 text="OK",
        #                 theme_text_color="Custom",
        #                 text_color=self.app.theme_cls.primary_color,
        #             )
        # self.dialog = MDDialog(
        #         title="Enable Localization",
        #         text="Localization is required for the application to work properly.",
        #         buttons=[self.button]
        #     )
        # self.button.bind(on_release=self.dialog.dismiss)
        # self.dialog.open()

    def update_lat_lon(self, **kwargs):
        self.latitude = kwargs['lat']
        self.longitude = kwargs['lon']

        if self.blinker_color is None and self.blinker is None:
            self.draw_marker()

    def on_status(self, stype, status):
        if stype == 'provider-disabled' and stype != self.provider:
            self.provider = stype
            self.enable_gps()
            self.reposition()
            return False
        elif stype == 'provider-enabled' and stype != self.provider:
            self.provider = stype
            self.reposition()
            return True

    def draw_marker(self):
        if self.latitude is None or self.longitude is None:
            return False

        pos_x, pos_y = self.map_widget.get_window_xy_from(lat=self.latitude, lon=self.longitude, zoom=self.map_widget.zoom)
        self.blinker_center = (pos_x, pos_y)

        marker_pos = (pos_x - self.marker_size[0] / 2, pos_y - self.marker_size[1] / 2)
        blinker_pos = (pos_x - self.blinker_size[0] / 2, pos_y - self.blinker_size[1] / 2)

        with self.canvas.before:
            self.blinker_color = Color(*self.app.theme_cls.primary_dark)
            self.blinker = Ellipse(size=self.blinker_size, pos=blinker_pos)

            Color(*self.app.theme_cls.primary_dark)
            Ellipse(size=self.marker_size, pos=marker_pos)

        if self.provider == 'provider-enabled':
            self.blink()

    def update_marker(self, *args):
        # Cancel animations before drawing new marker
        self.cancel_animations()

        # Clear any existing circle drawing
        self.canvas.before.clear()
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