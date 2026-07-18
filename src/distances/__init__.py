"""Package to generate origin-destination distance matrices with a local OSRM server."""

from distances.inputs import (
    load_destination,
    load_destination_layers,
    load_destinations,
    load_origins,
    to_point_layer,
)
from distances.matrix import build_distance_matrix
from distances.osrm import get_driving_distance, get_driving_route, snap_to_road
from distances.settings import PROJECT_ROOT, load_settings

__all__ = [
    "PROJECT_ROOT",
    "build_distance_matrix",
    "get_driving_distance",
    "get_driving_route",
    "load_destination",
    "load_destination_layers",
    "load_destinations",
    "load_origins",
    "load_settings",
    "snap_to_road",
    "to_point_layer",
]
