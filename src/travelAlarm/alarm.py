from kivymd.app import MDApp
from kivymd.uix.button import MDFlatButton
from kivymd.uix.dialog import MDDialog
from kivy.clock import Clock
from kivy.core.audio import SoundLoader
from plyer import vibrator


class Alarm:
    def __init__(self, pin_marker):
        from kivymd.toast import toast
        # Get app instance
        self.app = MDApp.get_running_app()

        # Initialize pin object in alarm
        self.pin = pin_marker.pin

        # Deactivate buffer with UI update
        self.pin.on_checkbox_click(False)

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
        self.alarm_button.bind(on_release=lambda x: self.stop_alarm())

        # alarm_1 - 501880__greenworm__cellphone-alarm-clock
        self.alarm_sound = SoundLoader.load(self.app.alarm_file)

        # Open dialog window
        self.alarm_dialog.open()

        # Trigger vibrations
        self.vibration_event = Clock.schedule_interval(lambda dt: vibrator.vibrate(1), 2.5)

        # Sound alarm
        self.sound()

    def sound(self):
        if self.alarm_sound:
            self.alarm_sound.loop = True
            self.alarm_sound.play()

    def stop_alarm(self, *args):
        if self.alarm_sound:
            self.alarm_sound.stop()

        # Stop the vibration
        if self.vibration_event:
            Clock.unschedule(self.vibration_event)

        self.alarm_dialog.dismiss()
