from kivymd.app import MDApp
from kivymd.uix.button import MDFlatButton
from kivymd.uix.dialog import MDDialog


class Alarm:
    def __init__(self, pin_id, address, buffer_size, buffer_unit):

        # Get app instance
        self.app = MDApp.get_running_app()

        # Deactivate buffer
        self.app.pins_db.update_is_active(pin_id, False)

        # Close marker popup
        self.app.pins_db.pins[pin_id].get('marker').close_marker_popup()

        # Set attributes
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

        # Open dialog window
        self.alarm_dialog.open()
