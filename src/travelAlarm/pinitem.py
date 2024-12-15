# Coding: UTF-8

# Copyright (C) 2024 Michał Prędki
# Licensed under the GNU General Public License v3.0.
# Full text of the license can be found in the LICENSE and COPYING files in the repository.

from kivymd.app import MDApp
from kivy.uix.boxlayout import BoxLayout
from kivymd.toast import toast
from kivymd.uix.menu import MDDropdownMenu
from kivy.properties import NumericProperty, BooleanProperty, StringProperty
from kivymd.uix.behaviors.magic_behavior import MagicBehavior
from kivy.lang import Builder

from geocode import geocode_by_address

# Build the widget's UI
Builder.load_file('pinitem.kv')

class PinItem(BoxLayout, MagicBehavior):

    # Pin's properties
    pin_id = NumericProperty()
    is_active = BooleanProperty()
    address = StringProperty()
    buffer_size = NumericProperty()
    buffer_unit = StringProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.app = MDApp.get_running_app()
        self.database = self.app.database

        # Build dropdown menus
        self.buffer_unit_menu = self.build_buffer_unit_menu()
        self.three_dots_menu = self.build_three_dots_menu()

    def build_buffer_unit_menu(self):
        """Builds drop down menu for pin's buffer unit."""
        unit_items = [
            {'text': item, 'viewclass': 'OneLineListItem', 'on_release': lambda x=item: self.on_buffer_unit_edit(x)}
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
            {'icon': 'delete', 'viewclass': 'MDIconButton', 'on_release': lambda x='DEL': self.on_delete_pin()},
            {'icon': 'map-marker', 'viewclass': 'MDIconButton', 'on_release': lambda x='MAP': self.on_center_map_on_pin()}
        ]
        return MDDropdownMenu(
            caller=self.ids.three_dots_menu_button,
            items=three_dots_menu_items,
            width_mult=2,
        )

    @property
    def map_marker(self):
        """Get the marker instance from the marker dictionary."""
        return self.app.markers[self.pin_id]

    def on_checkbox_click(self, new_is_active):
        """Update is_active attribute regarding checkbox state."""
        # Check if provided value is different to previous one
        if self.is_active == new_is_active:
            return False
        # Update UI on ListScreen
        self.is_active = new_is_active
        # Update UI on the map_widget
        self.map_marker.pin.is_active = new_is_active
        self.map_marker.update_buffer()
        self.map_marker.set_pin_icon()
        # Update the database
        self.database.update_is_active(self.pin_id, self.is_active)

    def on_address_edit(self, new_address):
        """Update address attribute regarding value of text field."""
        # Check if provided value is different to previous one
        if self.address == new_address or new_address == "":
            # If empty restore text field to previous value
            self.ids.address_field.text = self.address
            return False

        try:
            address, latitude, longitude = geocode_by_address(new_address)
            # Update UI on ListScreen
            self.address = address
            # Update UI on the map_widget
            self.map_marker.pin.address = address
            self.map_marker.lat = latitude
            self.map_marker.lon = longitude
            self.map_marker.update_buffer()
            self.map_marker.set_marker_position()
            # Set text field to the new address value
            self.ids.address_field.text = self.address
            # Update the database
            self.database.update_address(self.pin_id, address, latitude, longitude)
            # Show information on the screen
            toast(text='Pin Edited')

        # If geocode failed
        except:
            # Restore text field to previous value
            self.ids.address_field.text = self.address
            # Show information on the screen
            toast(text='Geocoding Failed')
            return False

    def on_buffer_size_edit(self, new_buffer_size):
        """Update buffer_size attribute regarding value of text field."""
        # Check if provided value is different to previous one
        if (new_buffer_size == '' or self.buffer_size == float(new_buffer_size) or
                not self.valid_buffer_size(new_buffer_size, self.buffer_unit)):
            # If empty restore text field to previous value
            self.ids.buffer_size_field.text = str(self.buffer_size)
            return False
        # Update UI on ListScreen
        self.buffer_size = float(new_buffer_size)
        # Update UI on the map_widget
        self.map_marker.pin.buffer_size = float(new_buffer_size)
        self.map_marker.update_buffer()
        # Update the database
        self.database.update_buffer_size(self.pin_id, self.buffer_size)

    def on_buffer_unit_edit(self, new_buffer_unit):
        """Update buffer_unit attribute regarding value of text field."""
        # Check if provided value is different to previous one
        if self.buffer_unit == new_buffer_unit or not self.valid_buffer_size(self.buffer_size, new_buffer_unit):
            # Close drop down menu if click on the same unit
            self.buffer_unit_menu.dismiss()
            return False
        # Update UI on ListScreen
        self.buffer_unit = new_buffer_unit
        # Update UI on the map_widget
        self.map_marker.pin.buffer_unit = new_buffer_unit
        self.map_marker.update_buffer()
        # Close drop down menu
        self.buffer_unit_menu.dismiss()
        # Update the database
        self.database.update_buffer_unit(self.pin_id, self.buffer_unit)

    @staticmethod
    def valid_buffer_size(buffer_size, buffer_unit):
        """Ensure buffer_size is greater then 1 meter."""
        from markerslayer import MarkersLayer
        # Get values to convert buffer size to meter
        unit_mult = MarkersLayer.unit_mult
        # Convert buffer size to meters
        buffer_size = float(buffer_size)
        buffer_size_meter = unit_mult[buffer_unit] * buffer_size

        if buffer_size_meter < 1:
            toast('Buffer size to small')
            return False
        else:
            return True

    def on_delete_pin(self):
        """Delete pin from ListScreen, map_widget and database."""
        # Remove item from screen
        list_screen = self.app.root.ids.screen_manager.get_screen('ListScreen')
        list_screen.remove_pin(self.pin_id)
        # Remove buffer and marker from map_widget
        self.map_marker.erase_from_map_widget()
        # Remove marker from marker dictionary
        self.app.markers.pop(self.pin_id)
        # Update the database
        self.database.delete_pin_by_id(self.pin_id)
        # Show information on the screen
        toast(text='Pin Deleted')
        # Close drop down menu
        self.three_dots_menu.dismiss()

    def on_center_map_on_pin(self):
        """Center map_widget on pin's location."""
        screen_manager = self.app.root.ids.screen_manager
        # Get pin's localization
        latitude, longitude = self.map_marker.lat, self.map_marker.lon
        # Change screen to the MapScreen
        screen_manager.transition.direction = 'left' if screen_manager.current == 'ListScreen' else 'right'
        screen_manager.current = 'MapScreen'
        # Close drop down menu
        self.three_dots_menu.dismiss()

        map_screen = screen_manager.get_screen('MapScreen')
        map_screen.center_map_widget_on_lat_lon(latitude, longitude)

    def magic_grow(self):
        """Perform magic animation on the pin item."""
        # Animation speed
        MagicBehavior.magic_speed = .2
        # Perform animation
        MagicBehavior.grow(self)
