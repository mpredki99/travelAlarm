from kivymd.app import MDApp
from kivymd.uix.button import MDFlatButton
from kivymd.uix.dialog import MDDialog
from kivy.clock import Clock
from plyer import vibrator

from kivymd.toast import toast


class Alarm:
    def __init__(self, pin_marker):
        from kivymd.toast import toast
        # Get app instance
        self.app = MDApp.get_running_app()

        # Initialize pin object in alarm
        self.pin = pin_marker.pin

        # Deactivate checkbox with UI update
        Clock.schedule_once(lambda dt: self.pin.on_checkbox_click(False), 0)

        # Get pin address, buffer size and buffer unit
        self.address = self.pin.address
        self.buffer_size = self.pin.buffer_size
        self.buffer_unit = self.pin.buffer_unit


        # Build button to close dialog window
        self.alarm_button = MDFlatButton(
            text='OK',
            theme_text_color='Custom',
            text_color=self.app.theme_cls.primary_color,
        )
        # Build dialog window
        self.alarm_dialog = MDDialog(
            title='Wake up!',
            text=f'You are within {self.buffer_size} {self.buffer_unit} from {self.address}',
            buttons=[self.alarm_button]
        )
        # Bind button event to close dialog window
        self.alarm_button.bind(on_press=self.alarm_dialog.dismiss)

        # Open dialog window
        self.alarm_dialog.open()

        # Trigger vibrations
        self.vibrate()

    def vibrate(self):
        if vibrator.exists():
            for i in range(3):
                Clock.schedule_once(lambda dt: vibrator.vibrate(1), 1 + i * 2)
