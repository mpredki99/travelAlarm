# Coding: UTF-8

# Copyright (C) 2024 Michał Prędki
# Licensed under the GNU General Public License v3.0.
# Full text of the license can be found in the LICENSE and COPYING files in the repository.

from kivymd.app import MDApp
from kivy.uix.screenmanager import Screen
from kivymd.uix.menu import MDDropdownMenu
from kivy.properties import ObjectProperty, BooleanProperty
from kivy.clock import Clock
from kivy.animation import Animation

from addresseslist import AddressesList


class ListScreen(Screen):

    app = MDApp.get_running_app()
    clock = ObjectProperty()
    list_order_menu = ObjectProperty()
    addresses_list = ObjectProperty()
    add_marker_mode = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.database = self.app.database

    def on_kv_post(self, base_widget):
        """Set list order menu button text and build dropdown menu."""
        # Build dropdown menu
        self.list_order_menu = self.build_list_order_menu()
        self.set_sort_menu_button_text()

    def build_list_order_menu(self):
        """Build list order dropdown menu."""
        order_items = [
            {'text': item, 'viewclass': 'OneLineListItem', 'on_release': lambda x=item: self.on_list_order_menu_item(x)}
            for item in ['time', 'active', 'address']
        ]
        return MDDropdownMenu(
            caller=self.ids.sort_menu_button,
            items=order_items,
        )

    def set_sort_menu_button_text(self, db_attribute=None):
        """Set text of list order menu button."""
        # Get markers list order attribute from database and assign it to the button text
        if not db_attribute: db_attribute = self.database.list_order
        map_db_attribute = {'insert_datetime': 'time', 'is_active': 'active', 'address': 'address'}
        button_text = map_db_attribute[db_attribute]
        # Set the button text
        self.ids.sort_menu_button.text = 'Sort by: ' + button_text

    def on_list_order_menu_item(self, new_order_by):
        """Sort list by new attribute."""
        # Assign the value of the button text to the database attribute
        map_button_text = {'time': 'insert_datetime', 'active': 'is_active', 'address': 'address'}
        db_attribute = map_button_text[new_order_by]
        # Set text on the list order menu button and update database
        self.set_sort_menu_button_text(db_attribute=db_attribute)
        self.database.update_list_order(db_attribute)
        # Refresh recycle view markers list
        self.set_list_data()
        # Close dropdown menu
        self.list_order_menu.dismiss()

    def on_pre_enter(self, *args):
        """Set markers list data before entering to the screen."""
        self.set_list_data()

    def clear_list_data(self):
        """Remove all data from markers list."""
        self.ids.pins_list.data = []

    def set_list_data(self):
        """Refresh markers list on the screen."""
        self.ids.pins_list.data = [
            {
                'pin_id': marker.pin.pin_id,
                'is_active': marker.pin.is_active,
                'address': marker.pin.address,
                'buffer_size': marker.pin.buffer_size,
                'buffer_unit': marker.pin.buffer_unit,
            }
            for marker in self.app.markers.values()
        ]

    def remove_marker(self, pin_id):
        """Remove item from the markers list."""
        self.ids.pins_list.data = [item for item in self.ids.pins_list.data if item.get('pin_id') != pin_id]

    def on_marker_popup(self, pin_id):
        """Perform magic animation on markers list item."""
        if self.clock: self.clock.cancel()
        self.clock = Clock.schedule_once(lambda dt: self.magic_grow_item_by_id(pin_id), 1)

    def magic_grow_item_by_id(self, pin_id):
        """Perform magic animation."""
        # Retrieve pin instance from pin list
        pin = next((pin for pin in self.ids.pins_list.view_adapter.views.values() if pin.pin_id == pin_id), None)
        # Perform magic animation
        if pin: pin.magic_grow()

    # Manage to prepare and hide add marker mode
    def prepare_search_view(self):
        """Switch screen to adding marker mode."""
        self.add_marker_mode = True

        box_layout = self.ids.box_layout
        text_field = self.ids.add_pin_text_field
        # Prepare switch mode on text field click
        if text_field.focus:
            # Calculate position of searched address text field
            pos_y = self.height - text_field.height - box_layout.padding[1] - box_layout.padding[3]
            # Begin animations and add addresses list to the screen
            animation = Animation(y=pos_y, duration=.3)
            animation.bind(on_complete=self.add_addresses_list)
            animation.start(self)

    def add_addresses_list(self, *args):
        """Add addresses list to the screen."""
        self.addresses_list = AddressesList(size_hint_y=None, height=self.y)
        self.add_widget(self.addresses_list)
        # Set position of addresses list
        self.addresses_list.y = -self.y

    def hide_search_view(self):
        """Switch screen back to list view mode."""
        if self.add_marker_mode:
            # Clean address text field
            self.ids.add_pin_text_field.text = ""

            self.add_marker_mode = False
            # Remove addresses list from screen
            self.remove_widget(self.addresses_list)
            Animation(y=0, duration=.3).start(self)
        else:
            return False
