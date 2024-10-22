from kivy_garden.mapview import MapMarker, MapLayer
from kivy.graphics import Color, Ellipse
from kivy.metrics import dp
from kivymd.app import MDApp


class GpsMarker(MapLayer):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.app = MDApp.get_running_app()
        self.map_widget = self.app.map_widget

        # self.source = ""
        self.marker_symbol = None

        rgb = self.app.theme_cls.primary_color[:3]
        self.marker_color = rgb + [.8]

        self.pos = self.map_widget.get_window_xy_from(lat=50, lon=20, zoom=10)

        print(self.pos)

        with self.canvas:
            Color(*self.marker_color)
            self.marker_symbol = Ellipse(size=(50, 50), pos=self.pos)
