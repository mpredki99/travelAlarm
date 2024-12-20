# Coding: UTF-8

# Copyright (C) 2024 Michał Prędki
# Licensed under the GNU General Public License v3.0.
# Full text of the license can be found in the LICENSE and COPYING files in the repository.

from kivymd.app import MDApp
from kivy.core.window import Window
from kivy_garden.mapview import MapMarkerPopup
from kivymd.uix.menu import MDDropdownMenu
from kivy.metrics import dp
from kivymd.uix.button import MDRaisedButton
from kivy.uix.boxlayout import BoxLayout
from geocode import geocode_by_lat_lon
from kivymd.toast import toast

from pinitem import PinItem


class PinMarker(MapMarkerPopup):

    def __init__(self, pin_id, is_active, address, buffer_size, buffer_unit, **kwargs):
        super().__init__(**kwargs)

        # Get app instance
        self.app = MDApp.get_running_app()

        # Get pins database instance
        pins = self.app.pins_db.pins

        # Determine pin marker color
        marker_color = self.app.theme_cls.primary_palette if pins[pin_id].get('is_active') else 'Red'

        # Get pin marker icon
        self.source = "icons/" + marker_color + ".png"

        # Determine popup widget size
        self.popup_size = Window.width * .9, Window.height * .1

        # Keep popup open while interactions
        self.is_open = True

        # Create instance of popup widget
        self.pin = PinItem(
                y = dp(10),
                pin_id=pin_id,
                is_active=is_active,
                address=address,
                buffer_size=buffer_size,
                buffer_unit=buffer_unit,
            )

        # Override three dots menu options
        self.pin.three_dots_menu = self.build_three_dots_menu()

        # Add pin item widget to pin marker
        self.add_widget(
            self.pin
        )

    def build_three_dots_menu(self):
        """Builds drop down menu for delete and show on list screen."""
        three_dots_menu_items = [
            {"icon": "delete", "viewclass": "MDIconButton", "on_release": lambda x="DEL": self.pin.on_delete_pin()},
            {"icon": "format-list-checks", "viewclass": "MDIconButton", "on_release": lambda x="LIST": self.on_to_list()}
        ]
        return MDDropdownMenu(
            caller=self.pin.ids.three_dots_menu_button,
            items=three_dots_menu_items,
            width_mult=2,
        )

    def on_to_list(self):
        """Show pin item on list screen"""
        # Get screen manager instance
        screen_manager = self.app.root.ids.screen_manager

        # Get list screen instance
        list_screen = screen_manager.get_screen('ListScreen')

        # Change screen to ListScreen
        screen_manager.transition.direction = 'right'
        screen_manager.current = 'ListScreen'

        # Close dropdown menu
        self.pin.three_dots_menu.dismiss()

        # Close popup widget
        self.close_marker_popup()

        # Call function to perform magic behavior
        list_screen.on_marker_popup(self.pin.pin_id)

    def close_marker_popup(self):
        """Close popup widget."""
        self.is_open = False


class AddPinMarker(MapMarkerPopup):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Get app instance
        self.app = MDApp.get_running_app()

        # Determine pin marker color
        marker_color = self.app.theme_cls.primary_palette

        # Get pin marker icon
        self.source = "icons/" + marker_color + ".png"

        # Open popup while initialization
        self.is_open = True

        # Add popup widget to the marker
        self.add_widget(self.build_popup())

    def build_popup(self):
        """Build popup widget to add pin or cancel operation."""
        # Initialize box layout
        box_layout = BoxLayout()

        # box_layout.size = self.popup_size

        # Create button for adding pin
        add_pin_button = MDRaisedButton(text='Add pin')
        add_pin_button.radius = [8, 8, 8, 8]
        add_pin_button.elevation = 0

        # Bind add pin method to the button
        add_pin_button.bind(on_release=self.add_pin)

        # Add button for adding pin to the layout
        box_layout.add_widget(add_pin_button)

        # Create button for canceling
        cancel_button = MDRaisedButton(text='Cancel')
        cancel_button.radius = [8, 8, 8, 8]
        cancel_button.elevation = 0

        # Bind remove marker method to the button
        cancel_button.bind(on_release=self.remove_marker)

        # Add button for canceling to the layout
        box_layout.add_widget(cancel_button)

        # Move layout from the marker
        box_layout.y = dp(10)

        # Add spacing to the layout
        box_layout.spacing = dp(5)

        # Determine popup widget size
        self.popup_size = add_pin_button.width + cancel_button.width + box_layout.spacing, add_pin_button.height
        box_layout.size = self.popup_size

        return box_layout

    def add_pin(self, *args):
        """Add pin by reverse geocoding."""
        try:
            # Get geocoded address and location
            address, latitude, longitude = geocode_by_lat_lon(self.lat, self.lon)

            # Add pin to database, add pin marker to map widget and get pin identifier
            pin_id = self.app.pins_db.add_pin_by_address_lat_lon(address, latitude, longitude)

            # Get map screen instance
            map_screen = self.app.root.ids.screen_manager.get_screen('MapScreen')

            # Close map marker popups except the added one
            map_screen.close_map_marker_popups(pin_id)

            # Get list screen instance
            list_screen = self.app.root.ids.screen_manager.get_screen('ListScreen')

            # Refresh pins list in list screen
            list_screen.refresh_pins_list()

            # Remove add pin marker
            self.remove_marker()

            # Show information on the screen
            toast(text=str("Pin Added"))

        except Exception as err:
            # Show information on the screen
            toast(text=str("Geocoding Failed"))
            return False

    def remove_marker(self, *args):
        """Remove add pin marker from map widget."""
        self.parent.parent.remove_marker(self)
