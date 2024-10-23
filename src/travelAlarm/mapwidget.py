from kivy_garden.mapview import MapView, MapSource, MarkerMapLayer
from kivy.clock import Clock

from pinmarkers import AddPinMarker


class MapWidget(MapView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Set min zoom value as 3
        self.map_source = MapSource(min_zoom=3)

        # Initialize clock variable
        self.clock = None

        # Initialize hold state
        self.hold = False

    def on_touch_down(self, touch):
        """Override touch down method and add functionality to add pin by hold."""
        # Change hold state
        self.hold = True

        # Display proposed addresses on the screen
        self.clock = Clock.schedule_once(lambda dt: self.on_hold(touch), 1)

        # Handle default touch down event
        return super().on_touch_down(touch)
        
    def on_touch_move(self, touch):
        """Override touch move method and cancel hold state."""
        # Cancel hold state
        self.hold = False

        # Cancel clock
        if self.clock: self.clock.cancel()

        # Handle default touch move event
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        """Override touch up method and cancel hold state."""
        # Change hold state
        self.hold = False

        # Cancel clock
        if self.clock: self.clock.cancel()

        # Handle default touch up event
        super().on_touch_up(touch)

    def on_hold(self, touch):
        """Add marker to the map widget."""
        # If map widget is in hold state
        if self.hold:
            # Get latitude and longitude of touch position
            touch_lat, touch_lon = self.get_latlon_at(*touch.pos, self.zoom)

            # Add marker to the map widget
            self.add_marker(AddPinMarker(lat=touch_lat, lon=touch_lon))

        else:
            return False
