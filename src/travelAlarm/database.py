# Coding: UTF-8

# Copyright (C) 2024 Michał Prędki
# Licensed under the GNU General Public License v3.0.
# Full text of the license can be found in the LICENSE and COPYING files in the repository.

import sqlite3

from kivymd.app import MDApp

from markers import Marker


class Database:
    def __init__(self, db_filename):
        # Initialize connection to database
        self.connection = sqlite3.connect(db_filename)
        self.cursor = self.connection.cursor()

        # Get map_widget instance
        self.app = MDApp.get_running_app()
        self.map_widget = self.app.map_widget

        # Initialize database tables
        self.init_pins_table()
        self.init_customizations_table()

        # Set map_widget initial state
        self.set_mapview_initial_state()

    def init_pins_table(self):
        """Create pins table id does not exist yet."""
        # Initialize pins table if it doesn't exist
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS pins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                is_active BOOLEAN,
                address TEXT,
                latitude REAL,
                longitude REAL,
                buffer_size REAL,
                buffer_unit TEXT CHECK (buffer_unit IN ('m', 'km')),
                insert_datetime DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        ''')
        # Save the table
        self.connection.commit()

    def init_customizations_table(self):
        """Create customizations table id does not exist yet."""
        # Initialize pins table if it doesn't exist
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS customizations (
                key TEXT PRIMARY KEY,
                value TEXT);
        ''')
        # Save the table
        self.connection.commit()

    # Manage pins table
    def get_markers(self):
        """Get all pins from database ordered by provided attribute."""
        # Get order by attribute from database
        order_by = self.list_order

        # Build SQL query
        if order_by in ['is_active', 'address', 'insert_datetime']:
            query = f'SELECT * FROM pins ORDER BY {order_by} {"ASC" if order_by == "address" else "DESC"};'
        else:
            query = f'SELECT * FROM pins ORDER BY insert_datetime DESC;'

        self.cursor.execute(query)

        return {
            pin_id: Marker(pin_id, is_active, address, buffer_size, buffer_unit, lat=latitude, lon=longitude)
            for pin_id, is_active, address, latitude, longitude, buffer_size, buffer_unit, _ in
            self.cursor.fetchall()
        }

    def update_pins(self):
        """Update pins dictionary and map_widget."""
        # Clear map_widget buffers
        for marker in self.app.markers.values():
            marker.erase_from_map_widget()

        # Update pins dict
        self.app.markers = self.get_markers()

    def get_pin_by_id(self, pin_id):
        """Get pin from database by provided identifier."""
        self.cursor.execute(f'SELECT * FROM pins WHERE id={pin_id}')
        return self.cursor.fetchall()[0]

    def delete_pin_by_id(self, pin_id):
        """Delete pin from database by provided identifier."""
        # Update database
        self.cursor.execute("DELETE FROM pins WHERE id = ?", (pin_id,))
        self.connection.commit()

    def add_pin_by_address_lat_lon(self, address, latitude, longitude):
        """Add pin to database by geocoded address."""
        # Add pin to database
        self.cursor.execute(
            '''INSERT INTO pins (is_active, address, latitude, longitude, buffer_size, buffer_unit)
                VALUES (TRUE, ?, ?, ?, 1, 'km')
            ''', (address, latitude, longitude))
        self.connection.commit()

        # Save the pins in dict
        self.update_pins()

    def update_is_active(self, pin_id, new_is_active):
        """Update pin's is active attribute."""
        # Update database
        self.cursor.execute("UPDATE pins SET is_active = ? WHERE id = ?", (new_is_active, pin_id))
        self.connection.commit()

    def update_address(self, pin_id, new_address, new_latitude, new_longitude):
        """Update pin's address attribute."""
        # Update database
        self.cursor.execute(
            "UPDATE pins "
            "SET address = ?, latitude = ?, longitude = ?, insert_datetime = CURRENT_TIMESTAMP "
            "WHERE id = ?",
            (new_address, new_latitude, new_longitude, pin_id)
        )
        self.connection.commit()

    def update_buffer_size(self, pin_id, new_buffer_size):
        """Update pin's buffer_size attribute."""
        # Update database
        self.cursor.execute("UPDATE pins SET buffer_size = ? WHERE id = ?", (new_buffer_size, pin_id))
        self.connection.commit()

    def update_buffer_unit(self, pin_id, new_buffer_unit):
        """Update pin's buffer_unit attribute."""
        # Update database
        self.cursor.execute("UPDATE pins SET buffer_unit = ? WHERE id = ?", (new_buffer_unit, pin_id))
        self.connection.commit()

    # Manage customizations table
    def save_mapview_state(self):
        """Save current map_widget state to database."""
        self.cursor.execute(
            'REPLACE INTO customizations (key,value) VALUES ("mapstate", ?);',
            (f'{self.map_widget.lat} {self.map_widget.lon} {self.map_widget.zoom}',)
        )
        self.connection.commit()

    def set_mapview_initial_state(self):
        """Set map_widget center and zoom to initial state."""
        # Get values from database
        self.cursor.execute('SELECT value FROM customizations WHERE key="mapstate";')
        map_state = self.cursor.fetchall()

        if len(map_state) > 0:
            # Values from previous end of session
            latitude, longitude, zoom = map_state[0][0].split(' ')
        else:
            # Default value while open first time - Cracow coordinates
            latitude, longitude, zoom = 50.053756, 19.940927, 10

        # Set map_widget initial state
        self.map_widget.zoom = int(zoom)
        self.map_widget.center_on(float(latitude), float(longitude))

    def update_list_order(self, new_order_by):
        """Update list order in database."""
        self.cursor.execute('REPLACE INTO customizations (key,value) VALUES ("listorder", ?);', (new_order_by,))
        self.connection.commit()

        # Update pins dictionary
        self.update_pins()

    @property
    def list_order(self):
        """Return pins list order from database."""
        self.cursor.execute('SELECT value FROM customizations WHERE key="listorder";')
        list_order = self.cursor.fetchall()

        if len(list_order) > 0:
            # Value from previous end of session
            order_by = list_order[0][0]
        else:
            # Default value while open first time
            order_by = "insert_datetime"

        return order_by

    def update_app_theme_style(self, new_theme_style):
        """Update app theme style in database."""
        self.cursor.execute('REPLACE INTO customizations (key,value) VALUES ("themestyle", ?);', (new_theme_style,))
        self.connection.commit()

    @property
    def theme_style(self):
        """Return app theme style from database."""
        self.cursor.execute('SELECT value FROM customizations WHERE key="themestyle";')
        theme_style = self.cursor.fetchall()

        if len(theme_style) > 0:
            # Value from previous end of session
            theme_style = theme_style[0][0]
        else:
            # Default value while open first time
            theme_style = "Light"

        return theme_style

    def update_app_primary_palette(self, new_primary_palette):
        """Update app primary palette in database."""
        self.cursor.execute('REPLACE INTO customizations (key,value) VALUES ("primarypalette", ?);', (new_primary_palette,))
        self.connection.commit()

        # Update pins dictionary
        for marker in self.app.markers.values():
            marker.set_pin_icon()
            marker.update_buffer()

    @property
    def primary_palette(self):
        """Return app primary palette from database."""
        self.cursor.execute('SELECT value FROM customizations WHERE key="primarypalette";')
        theme_style = self.cursor.fetchall()

        if len(theme_style) > 0:
            # Value from previous end of session
            theme_style = theme_style[0][0]
        else:
            # Default value while open first time
            theme_style = "LightGreen"

        return theme_style


    def update_alarm_sound(self, new_alarm_sound):
        """Update alarm sound in database."""
        self.cursor.execute('REPLACE INTO customizations (key,value) VALUES ("alarmsound", ?);', (new_alarm_sound,))
        self.connection.commit()

    @property
    def alarm_file(self):
        """Return alarm sound from database."""
        self.cursor.execute('SELECT value FROM customizations WHERE key="alarmsound";')
        alarm_sound = self.cursor.fetchall()

        if len(alarm_sound) > 0:
            # Value from previous end of session
            alarm_sound = alarm_sound[0][0]
        else:
            # Default value while open first time
            alarm_sound = "alarm_1.mp3"

        return f'sounds/{alarm_sound}'

    def disconnect(self):
        """Close the database connection."""
        self.cursor.close()
        self.connection.close()

    def connect(self, db_filename):
        """Close the database connection."""
        # Initialize connection to database and cursor
        self.connection = sqlite3.connect(db_filename)
        self.cursor = self.connection.cursor()
