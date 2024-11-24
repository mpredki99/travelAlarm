from kivymd.app import MDApp
from kivymd.uix.button import MDFlatButton
from kivymd.uix.dialog import MDDialog
from kivy.clock import Clock


class Alarm:
    def __init__(self, pin_id, address, buffer_size, buffer_unit):
        self.app = MDApp().get_running_app()
        from kivymd.toast import toast
        try:
            self.app.pins_db.update_is_active(pin_id, False)
        except Exception as e:
            toast(text=str(e))

        self.address = address
        self.buffer_size =  buffer_size
        self.buffer_unit = buffer_unit

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

        self.alarm_dialog.open()
        # Clock.schedule_once(lambda dt: self.app.pins_db.update_is_active(pin_id, False), .5)
