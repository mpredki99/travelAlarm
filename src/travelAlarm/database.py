import sqlite3

from kivymd.app import MDApp

from geocode import geocode_by_address
from pinmarkers import PinMarker
from buffer import Buffer

from kivy_garden.mapview import MapLayer


class Database:
    def __init__(self, db_filename):
        # Initialize connection to database
        self.connection = sqlite3.connect(db_filename)
        self.cursor = self.connection.cursor()

        # Get map_widget instance
        self.map_widget = MDApp.get_running_app().map_widget

        self.buffer_layer = MapLayer()

        # Initialize database tables
        self.init_pins_table()
        self.init_customizations_table()

        # Retrieve pins from database
        self.pins = self.get_pins()

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
    def get_pins(self):
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
            pin_id: {
                'is_active': is_active,
                'address': address,
                'latitude': latitude,
                'longitude': longitude,
                'buffer_size': buffer_size,
                'buffer_unit': buffer_unit,
            } for pin_id, is_active, address, latitude, longitude, buffer_size, buffer_unit, _ in
            self.cursor.fetchall()
        }

    def update_pins(self):
        """Update pins dictionary and map_widget."""
        # Clear map_widget buffers
        for pin_id in self.pins:
            self.erase_mapview_buffer(pin_id)

        # Update pins dict
        self.pins = self.get_pins()

        # Draw buffers on the map_widget
        for pin_id in self.pins:
            self.draw_mapview_buffer(pin_id)

    def get_pin_by_id(self, pin_id):
        """Get pin from database by provided identifier."""
        self.cursor.execute(f'SELECT * FROM pins WHERE id={pin_id}')
        return self.cursor.fetchall()[0]

    def delete_pin_by_id(self, pin_id):
        """Delete pin from database by provided identifier."""
        # Remove buffer and marker from map_widget
        self.erase_mapview_buffer(pin_id)

        # Update database
        self.cursor.execute("DELETE FROM pins WHERE id = ?", (pin_id,))
        self.connection.commit()

        # Update dict
        self.pins.pop(pin_id)

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

        return self.cursor.lastrowid

    def update_is_active(self, pin_id, new_is_active):
        """Update pin's is active attribute."""
        # Update database
        self.cursor.execute("UPDATE pins SET is_active = ? WHERE id = ?", (new_is_active, pin_id))
        self.connection.commit()

        # Update dict
        self.pins[pin_id]['is_active'] = new_is_active

        # Update map_widget
        self.update_mapview_buffer(pin_id)

    def update_address(self, pin_id, new_address):
        """Update pin's address attribute."""
        try:
            # Get coordinates of new address
            address, latitude, longitude = geocode_by_address(new_address)

            # Update database
            self.cursor.execute(
                "UPDATE pins "
                "SET address = ?, latitude = ?, longitude = ?, insert_datetime = CURRENT_TIMESTAMP "
                "WHERE id = ?",
                (address, latitude, longitude, pin_id)
            )
            self.connection.commit()

            # Update dict
            self.update_pins()

            # Update map_widget
            self.update_mapview_buffer(pin_id)

            # Return new address to update text field on ListScreen
            return address

        # If geocoding failed
        except Exception as err:
            raise ValueError('Geocoding failed')

    def update_buffer_size(self, pin_id, new_buffer_size):
        """Update pin's buffer_size attribute."""
        # Update database
        self.cursor.execute("UPDATE pins SET buffer_size = ? WHERE id = ?", (new_buffer_size, pin_id))
        self.connection.commit()

        # Update dict
        self.pins[pin_id]['buffer_size'] = new_buffer_size

        # Update map_widget
        self.update_mapview_buffer(pin_id)

    def update_buffer_unit(self, pin_id, new_buffer_unit):
        """Update pin's buffer_unit attribute."""
        # Update database
        self.cursor.execute("UPDATE pins SET buffer_unit = ? WHERE id = ?", (new_buffer_unit, pin_id))
        self.connection.commit()

        # Update dict
        self.pins[pin_id]['buffer_unit'] = new_buffer_unit

        # Update map_widget
        self.update_mapview_buffer(pin_id)


    # Manage map_widget
    def draw_mapview_buffer(self, pin_id):
        """Draw pin marker buffer and create pin marker popup on map_widget."""
        # Get pin's attributes
        is_active = self.pins[pin_id].get('is_active')
        address = self.pins[pin_id].get('address')
        latitude = self.pins[pin_id].get('latitude')
        longitude = self.pins[pin_id].get('longitude')
        buffer_size = self.pins[pin_id].get('buffer_size')
        buffer_unit = self.pins[pin_id].get('buffer_unit')

        # Create pin marker and pin buffer
        self.pins[pin_id]['buffer'] = Buffer(is_active, latitude, longitude, buffer_size, buffer_unit)
        self.pins[pin_id]['marker'] = PinMarker(pin_id, is_active, address, buffer_size, buffer_unit, lat=latitude, lon=longitude)

        # Add new buffer and marker to map_widget
        self.map_widget.add_marker(self.pins[pin_id]['marker'])
        self.map_widget.add_layer(self.pins[pin_id]['buffer'])

    def erase_mapview_buffer(self, pin_id):
        """Remove pin marker buffer and pin marker popup from map_widget."""
        # Remove buffer and marker from map_widget
        self.map_widget.remove_layer(self.pins[pin_id]['buffer'])
        self.map_widget.remove_marker(self.pins[pin_id]['marker'])

    def update_mapview_buffer(self, pin_id):
        """Update pin marker buffer and pin marker popup on map_widget."""
        self.erase_mapview_buffer(pin_id)
        self.draw_mapview_buffer(pin_id)


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
        self.update_pins()

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

    def disconnect(self):
        """Close the database connection."""
        self.cursor.close()
        self.connection.close()

    def connect(self, db_filename):
        """Close the database connection."""
        # Initialize connection to database and cursor
        self.connection = sqlite3.connect(db_filename)
        self.cursor = self.connection.cursor()
