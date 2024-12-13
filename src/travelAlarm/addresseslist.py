# Coding: UTF-8

# Copyright (C) 2024 Michał Prędki
# Licensed under the GNU General Public License v3.0.
# Full text of the license can be found in the LICENSE and COPYING files in the repository.

from kivy.uix.screenmanager import Screen
from kivy.clock import Clock

from geocode import geocode_by_address


class AddressesList(Screen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.clock = None

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
                self.ids.addresses_list.data.insert(
                    0,
                    {"text": address,
                     "on_release": lambda args=(address, latitude, longitude): self.add_pin(*args)}
                )

        except:
            return False

    def add_pin(self, address, latitude, longitude):
        """Add new pin to the list and database."""
        list_screen = self.parent

        # Add pin to database
        list_screen.database.add_pin_by_address_lat_lon(address, latitude, longitude)

        # Refresh pins list
        list_screen.set_list_data()

        # Switch back to list view mode
        list_screen.hide_search_view()
