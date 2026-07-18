import requests


def snap_to_road(lat, lon, host="localhost", port=5000):
    """Snap a coordinate to the nearest road using local OSRM."""
    url = f"http://{host}:{port}/nearest/v1/driving/{lon},{lat}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data["code"] == "Ok":
                snapped = data["waypoints"][0]["location"]
                return (snapped[1], snapped[0])
        return (lat, lon)
    except Exception as e:
        print(f"Error connecting to OSRM server: {e}")
        return (lat, lon)


def get_driving_distance(source_coordinates, dest_coordinates, host="localhost", port=5000):
    """Return driving distance in km between two (lat, lon) tuples."""
    base_url = f"http://{host}:{port}/route/v1/driving"
    src_lon, src_lat = source_coordinates[1], source_coordinates[0]
    dst_lon, dst_lat = dest_coordinates[1], dest_coordinates[0]
    url = f"{base_url}/{src_lon},{src_lat};{dst_lon},{dst_lat}?overview=false"

    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data["routes"][0]["distance"] / 1000
        print(f"Request failed. Status code: {response.status_code}")
        return -9999
    except Exception as e:
        print(f"Error connecting to OSRM server: {e}")
        return -9999
