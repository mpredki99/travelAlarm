# Coding: UTF-8

# Copyright (C) 2024 Michał Prędki
# Licensed under the GNU General Public License v3.0.
# Full text of the license can be found in the LICENSE and COPYING files in the repository.

from kivy.animation import Animation
from kivymd.app import MDApp
from kivy.uix.screenmanager import Screen
from kivymd.uix.menu import MDDropdownMenu
from kivy.clock import Clock

from geocode import geocode_by_address
from addresseslist import AddressesList


class ListScreen(Screen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Get app instance
        self.app = MDApp.get_running_app()

        # Get database instance
        self.pins_db = self.app.pins_db

        # Initialize list order menu button
        self.list_order_menu = None

        # Whether screen on search or list mode
        self.search_mode = False

        # Initialize clock variable
        self.clock = None

        # Initialize searched addresses list
        self.addresses_list = None

    def on_kv_post(self, base_widget):
        """Set list order menu button text and build dropdown menu."""
        # Set list order menu button text
        self.set_sort_menu_button_text()

        # Build dropdown menu
        self.list_order_menu = self.build_list_order_menu()

    def set_sort_menu_button_text(self):
        """Set text of list order menu button."""
        # Get attribute value from database
        db_attribute = self.pins_db.list_order

        # Assign the value of the database attribute to the button text
        map_db_attribute = {'insert_datetime': 'time', 'is_active': 'active', 'address': 'address'}

        # Set button text
        self.ids.sort_menu_button.text = 'Sort by: ' + map_db_attribute[db_attribute]

    def build_list_order_menu(self):
        from kivy.metrics import dp
        """Build list order dropdown menu."""
        # Create list of menu items
        order_items = [
            {"text": item, "viewclass": "OneLineListItem", "on_release": lambda x=item: self.on_list_order_menu(x)}
            for item in ['time', 'active', 'address']
        ]
        return MDDropdownMenu(
            caller=self.ids.sort_menu_button,
            items=order_items,
        )

    def on_list_order_menu(self, new_order_by):
        """Sort list by new attribute."""
        print(self.list_order_menu.width)
        # Check if different value was clicked
        if self.ids.sort_menu_button.text == 'Sort by: ' + new_order_by:
            # Close drop down menu if click on the same unit
            self.list_order_menu.dismiss()
            return False

        # Assign the value of the button text to the database attribute
        map_button_text = {'time': 'insert_datetime', 'active': 'is_active', 'address': 'address'}

        # Update order by attribute in database
        self.pins_db.update_list_order(map_button_text[new_order_by])

        # Set text of list order menu button
        self.set_sort_menu_button_text()

        # Refresh recycle view pins list
        self.refresh_pins_list()

        # Close pin marker popups
        self.app.root.ids.screen_manager.get_screen("MapScreen").close_map_marker_popups()

        # Close dropdown menu
        self.list_order_menu.dismiss()

    def prepare_search_view(self):
        """Switch screen to search mode."""
        # Update screen mode attribute
        self.search_mode = True

        # Get instance of screen box layout
        box_layout = self.ids.box_layout

        # Prepare switch mode on text field click
        if self.ids.add_pin_text_field.focus:
            # Calculate position of searched address text field
            pos = self.height - self.ids.add_pin_text_field.height - box_layout.padding[1] - box_layout.padding[3]

            # Begin animations and add addresses list to the screen
            animation = Animation(y=pos, duration=.3)
            animation.bind(on_complete=self.add_addresses_list)
            animation.start(self)

    def add_addresses_list(self, *args):
        """Add addresses list to the screen."""
        # Create addresses list
        self.addresses_list = AddressesList(size_hint_y=None, height=self.y)

        # Add addresses list to the screen
        self.add_widget(self.addresses_list)

        # Set position of addresses list
        self.addresses_list.y = -self.y

    def hide_search_view(self):
        """Switch screen back to list view mode."""
        if self.search_mode:
            # Update search mode attribute
            self.search_mode = False

            # Remove addresses list from screen
            self.remove_widget(self.addresses_list)
            Animation(y=0, duration=.3).start(self)

            # Clean address text field
            self.ids.add_pin_text_field.text = ""
        else:
            return False

    def on_address_typing(self, text):
        """Wait half a second and display proposed addresses on the screen."""
        # Wait half a second after the user finishes entering the address
        if self.clock: self.clock.cancel()

        # Display proposed addresses on the screen
        self.clock = Clock.schedule_once(lambda dt: self.display_proposed_addresses(text), .5)

    def display_proposed_addresses(self, text):
        """Display proposed addresses on the screen."""
        # Do not do anything if empty text
        if len(text) == 0: return False

        try:
            # Get list of proposed addresses and locations
            addresses, latitudes, longitudes = geocode_by_address(text, exactly_one=False, limit=5)

            # Add proposed addresses to the list
            for address, latitude, longitude in zip(addresses, latitudes, longitudes):
                self.addresses_list.ids.addresses_list.data.insert(
                    0,
                    {"text": address,
                     "on_release": lambda args=(address, latitude, longitude): self.add_pin(*args)}
                )

        except Exception as err:
            return False

    def add_pin(self, address, latitude, longitude):
        """Add new pin to the list and database."""
        # Add pin to database
        self.pins_db.add_pin_by_address_lat_lon(address, latitude, longitude)

        # Refresh pins list
        self.refresh_pins_list()

        # Close pin marker popups
        self.app.root.ids.screen_manager.get_screen("MapScreen").close_map_marker_popups()

        # Switch back to list view mode
        self.hide_search_view()

    def get_pins_list(self):
        """Read pins' data from the pins database."""
        return [
            {
                'pin_id': pin_id,
                'is_active': attributes.get('is_active'),
                'address': attributes.get('address'),
                'buffer_size': attributes.get('buffer_size'),
                'buffer_unit': attributes.get('buffer_unit'),
            }
            for pin_id, attributes in self.pins_db.pins.items()
        ]

    def refresh_pins_list(self):
        """Refresh pins list on the screen."""
        self.ids.pins_list.data = self.get_pins_list()

    def remove_pin(self, pin_id):
        """Remove pin from the RecycleView data."""
        self.ids.pins_list.data = [item for item in self.ids.pins_list.data if item.get('pin_id') != pin_id]

    def on_marker_popup(self, pin_id):
        """Perform magic animation on pin list item."""
        # Wait a second after switch to the list screen
        if self.clock: self.clock.cancel()

        # Begin magic grow on the pin list item
        self.clock = Clock.schedule_once(lambda dt: self.magic_grow_pin_by_id(pin_id), 1)

    def magic_grow_pin_by_id(self, pin_id):
        """Perform magic animation."""
        # Retrieve pin instance from pin list
        pin = next((pin for pin in self.ids.pins_list.view_adapter.views.values() if pin.pin_id == pin_id), None)

        # Perform magic animation
        if pin: pin.magic_grow()
