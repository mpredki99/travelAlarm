from kivymd.app import MDApp
from kivy.uix.boxlayout import BoxLayout
from kivymd.toast import toast
from kivymd.uix.menu import MDDropdownMenu
from kivy.properties import NumericProperty, BooleanProperty, StringProperty
from kivymd.uix.behaviors.magic_behavior import MagicBehavior
from kivy.uix.recycleview.views import RecycleDataViewBehavior

from buffer import Buffer


class PinItem(BoxLayout, MagicBehavior, RecycleDataViewBehavior):

    # Initialize pins' properties
    pin_id = NumericProperty()
    is_active = BooleanProperty()
    address = StringProperty()
    buffer_size = NumericProperty()
    buffer_unit = StringProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Get app instance
        self.app = MDApp.get_running_app()

        # Get database instance
        self.pins_db = self.app.pins_db

        # Dropdown menus
        self.buffer_unit_menu = self.build_buffer_unit_menu()
        self.three_dots_menu = self.build_three_dots_menu()

    def build_buffer_unit_menu(self):
        """Builds drop down menu for pin's buffer unit."""
        unit_items = [
            {"text": item, "viewclass": "OneLineListItem", "on_release": lambda x=item: self.on_buffer_unit_edit(x)}
            for item in ['m', 'km']
        ]
        return MDDropdownMenu(
            caller=self.ids.buffer_unit_menu_button,
            items=unit_items,
            width_mult=2,
        )

    def build_three_dots_menu(self):
        """Builds drop down menu for delete and zoom on map."""
        three_dots_menu_items = [
            {"icon": "delete", "viewclass": "MDIconButton", "on_release": lambda x="DEL": self.on_delete_pin()},
            {"icon": "map-marker", "viewclass": "MDIconButton", "on_release": lambda x="MAP": self.on_center_map_on_pin()}
        ]
        return MDDropdownMenu(
            caller=self.ids.three_dots_menu_button,
            items=three_dots_menu_items,
            width_mult=2,
        )

    def on_checkbox_click(self, new_is_active):
        """Update is_active attribute regarding checkbox state."""
        # Check if provided value is different to previous one
        if self.is_active == new_is_active:
            return False

        # Update pin's attribute
        self.is_active = new_is_active

        # Update database and map_widget
        self.pins_db.update_is_active(self.pin_id, self.is_active)

        # Refresh pins list
        self.refresh_pins_list_on_list_screen()

        # Close marker popup if edited on ListScreen
        self.close_marker_popup()

    def on_address_edit(self, new_address):
        """Update address attribute regarding value of text field."""
        # Check if provided value is different to previous one
        if self.address == new_address or new_address == "":
            # If empty restore text field to previous value
            self.ids.address_field.text = self.address
            return False

        try:
            # Update pin's attribute, database and map_widget
            self.address = self.pins_db.update_address(self.pin_id, new_address)

            # Set text field to new address value
            self.ids.address_field.text = self.address

            # Refresh pins list
            self.refresh_pins_list_on_list_screen()

            # Get name of current open screen
            screen = self.app.root.ids.screen_manager.current

            # Get id of pin to keep open if edited on MapScreen
            pin_id = self.pin_id if screen == 'MapScreen' else None

            # Close pin marker popups
            self.app.root.ids.screen_manager.get_screen("MapScreen").close_map_marker_popups(pin_id=pin_id)

            # Show information on the screen
            toast(text=str("Pin Edited"))

        # If geocode failed
        except Exception as err:
            # Restore text field to previous value
            self.ids.address_field.text = self.address

            # Show information on the screen
            toast(text=str("Geocoding Failed"))
            return False

    def on_buffer_size_edit(self, new_buffer_size):
        """Update buffer_size attribute regarding value of text field."""
        # Check if provided value is different to previous one
        if new_buffer_size == "" or self.buffer_size == float(new_buffer_size) or not self.valid_buffer_size(new_buffer_size, self.buffer_unit):
            # If empty restore text field to previous value
            self.ids.buffer_size_field.text = str(self.buffer_size)
            return False

        # Update pin's attribute
        self.buffer_size = float(new_buffer_size)

        # Update database and map_widget
        self.pins_db.update_buffer_size(self.pin_id, self.buffer_size)

        # Refresh pins list
        self.refresh_pins_list_on_list_screen()

        # Close marker popup if edited on ListScreen
        self.close_marker_popup()

    def on_buffer_unit_edit(self, new_buffer_unit):
        """Update buffer_unit attribute regarding value of text field."""
        # Check if provided value is different to previous one
        if self.buffer_unit == new_buffer_unit or not self.valid_buffer_size(self.buffer_size, new_buffer_unit):
            # Close drop down menu if click on the same unit
            self.buffer_unit_menu.dismiss()
            return False

        # Update pin's attribute
        self.buffer_unit = new_buffer_unit

        # Update database and map_widget
        self.pins_db.update_buffer_unit(self.pin_id, self.buffer_unit)

        # Close drop down menu
        self.buffer_unit_menu.dismiss()

        # Refresh pins list
        self.refresh_pins_list_on_list_screen()

        # Close marker popup if edited on ListScreen
        self.close_marker_popup()

    @staticmethod
    def valid_buffer_size(buffer_size, buffer_unit):
        buffer_size = float(buffer_size)
        if Buffer.unit_mult[buffer_unit] * buffer_size < 1:
            toast("Buffer size to small")
            return False
        else:
            return True

    def on_delete_pin(self):
        """Delete pin from list and database."""
        # Remove item from screen
        list_screen = self.app.root.ids.screen_manager.get_screen("ListScreen")
        list_screen.remove_pin(self.pin_id)

        # Update database and map_widget
        self.pins_db.delete_pin_by_id(self.pin_id)

        # Show information on the screen
        toast(text=str("Pin Deleted"))

        # Close drop down menu
        self.three_dots_menu.dismiss()

    def on_center_map_on_pin(self):
        """Center map on pin location."""
        # screen manager instance
        screen_manager = self.app.root.ids.screen_manager

        # Close drop down menu
        self.three_dots_menu.dismiss()

        # Get pin from database
        latitude, longitude = self.pins_db.get_pin_by_id(self.pin_id)[3:5]

        # Move to map screen
        screen_manager.transition.direction = "left" if screen_manager.current == "ListScreen" else "right"
        screen_manager.current = 'MapScreen'

        # Center on map location
        screen_manager.get_screen('MapScreen').center_mapview_on_lat_lon(latitude, longitude)

    def refresh_pins_list_on_list_screen(self):
        """Refresh ListScreen Recycle view."""
        # Refresh pins list
        self.app.root.ids.screen_manager.get_screen("ListScreen").refresh_pins_list()

    def close_marker_popup(self, screen='ListScreen'):
        """Close pin marker popup."""
        # Close pin marker popup if on screen provided in args
        current_screen = self.app.root.ids.screen_manager.current
        if current_screen == screen: self.pins_db.pins[self.pin_id].get('marker').close_marker_popup()

    def magic_grow(self):
        """Perform magic animation of pin item."""
        # Animation speed
        MagicBehavior.magic_speed = .2

        # Perform animation
        MagicBehavior.grow(self)
