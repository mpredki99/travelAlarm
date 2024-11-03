from geopy.geocoders import Nominatim


# Get geolocator instance
geolocator = Nominatim(user_agent="travelAlarm")


def geocode_by_address(address_to_geocoding, exactly_one=True, limit=1):
    """Geocode location by address."""
    try:
        # Geocode address
        location = geolocator.geocode(address_to_geocoding, exactly_one=exactly_one, limit=limit, timeout=10)

        if exactly_one:
            return return_one_location(location)
        else:
            return return_location_list(location)

    # If geolocation failed
    except Exception as err:
        raise ValueError(f'Geocoding failed: {err}')


def geocode_by_lat_lon(latitude, longitude):
    """Geocode location latitude and longitude."""
    try:
        # Geocode address
        location = geolocator.reverse(f'{latitude}, {longitude}', timeout=10)

        return return_one_location(location)

    # If geolocation failed
    except Exception as err:
        raise ValueError(f'Geocoding failed: {err}')


def return_one_location(location):
    """Return formated address and coordinates of location."""
    # Get latitude and longitude of location
    latitude, longitude = location.latitude, location.longitude

    # Create address label
    address = location.address.split(',')
    if len(address) > 1:
        address = address[0].strip() + ', ' + address[1].strip()
    elif len(address) == 1:
        address = address[0].strip()
    else:
        address = location.address.strip()

    # Return address and coordinates
    return address, latitude, longitude


def return_location_list(locations):
    """Return list of formated address and coordinates of location."""
    # Initialize lists of addresses and coordinates
    addresses, latitudes, longitudes = [], [], []

    # Iterate through all founded locations
    for location in locations:
        # Get formated address and coordinates of location
        address, latitude, longitude = return_one_location(location)

        # Add addresses and coordinates to the lists
        addresses.append(address)
        latitudes.append(latitude)
        longitudes.append(longitude)

    # Return lists address and coordinates
    return addresses, latitudes, longitudes
