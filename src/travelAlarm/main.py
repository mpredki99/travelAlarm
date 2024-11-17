from kivy.clock import mainthread
from kivymd.app import MDApp
from kivy.lang import Builder
from kivy import platform
from kivymd.uix.button import MDFlatButton
from kivymd.uix.dialog import MDDialog
from kivymd.toast import toast

from plyer import gps

from database import Database
from mapwidget import MapWidget


class TravelAlarmApp(MDApp):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Create map_widget instance
        self.map_widget = MapWidget()

        # Create database instance
        self.pins_db = Database('pins.db')

        # Initialize gps provider status
        self.provider_status = 'provider-enabled'

        # Initialize gps dialog
        self.gps_dialog = None
        self.gps_button = None

        # Initialize user localization
        self.user_latitude = None
        self.user_longitude = None

    def build_gps_dialog(self):
        self.gps_button = MDFlatButton(
            text='OK',
            theme_text_color='Custom',
            text_color=self.theme_cls.primary_color,
        )
        self.gps_dialog = MDDialog(
            title='Enable Localization',
            text='Enable localization to ensure the application works properly.',
            buttons=[self.gps_button]
        )
        self.gps_button.bind(on_press=self.gps_dialog.dismiss)

        return True

    def check_gps_permission(self):
        if platform == 'android':
            from android.permissions import Permission, check_permission
            return check_permission(Permission.ACCESS_FINE_LOCATION) and check_permission(Permission.ACCESS_COARSE_LOCATION)
        elif platform == 'ios':
            return True

        return False

    def request_location_permission(self):
        if platform == 'android' and not self.check_gps_permission():
            from android.permissions import Permission, request_permissions
            request_permissions([Permission.ACCESS_FINE_LOCATION, Permission.ACCESS_COARSE_LOCATION])

    def update_status(self, stype, status):
        if stype == 'provider-disabled' and stype != self.provider_status:
            self.provider_status = stype
            self.enable_gps()
            toast(text='Enable Localization')

        elif stype == 'provider-enabled' and stype != self.provider_status:
            self.provider_status = stype

        return True

    def update_localization(self, **kwargs):
        self.user_latitude = kwargs['lat']
        self.user_longitude = kwargs['lon']
        return True

    @mainthread
    def enable_gps(self):
        self.gps_dialog.open()

    def build(self):
        """Build app."""
        # Set app themes
        self.theme_cls.theme_style = self.pins_db.theme_style
        self.theme_cls.primary_palette = self.pins_db.primary_palette

        # Request location permissions
        self.request_location_permission()

        # Build gps dialog
        self.build_gps_dialog()

        try:
            gps.configure(on_location=self.update_localization, on_status=self.update_status)
            gps.start(minTime=1000, minDistance=1)
        except NotImplementedError:
            pass
        except ModuleNotFoundError:
            pass
        except Exception:
            pass

        return Builder.load_file("main.kv")

    def on_pause(self):
        """Prepare app to close."""
        # Save map_widget state and close connection to database
        self.on_stop()

        return True

    def on_resume(self):
        """Return database connection."""
        # Reconnect to the database and reload the map state
        self.pins_db.connect('pins.db')

    def on_stop(self):
        """Save map_widget state and disconnect from database."""
        # Save current map_widget state
        self.pins_db.save_mapview_state()

        # Close connection with database while turn off the app
        self.pins_db.disconnect()

if __name__ == '__main__':
    TravelAlarmApp().run()
