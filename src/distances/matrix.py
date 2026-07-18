import pandas as pd

from distances.inputs import (
    _resolve_col,
    load_destination_layers,
    load_destinations,
    load_origins,
)
from distances.osrm import get_driving_distance, snap_to_road
from distances.settings import (
    DESTINATIONS_EXAMPLE_CONFIG,
    INPUTS_DIR,
    load_settings,
    resolve_project_path,
)


def build_distance_matrix(
    origin_layer=None,
    origin_id_col=None,
    destinations_config=None,
    settings_path=None,
):
    """Generate origin/destination point layers and distance matrix via local OSRM."""
    settings = load_settings(settings_path)
    defaults = settings["defaults"]
    osrm_host = settings["osrm"]["host"]
    osrm_port = settings["osrm"]["port"]

    origin_layer = resolve_project_path(
        origin_layer or defaults["origin_layer"]
    )
    origin_id_col = origin_id_col or defaults["origin_id_col"]
    destinations_config = resolve_project_path(
        destinations_config or defaults["destinations_config"]
    )

    origin_gdf = load_origins(origin_layer, id_col=origin_id_col, save=True)

    config_path = destinations_config
    if not config_path.is_file():
        config_path = DESTINATIONS_EXAMPLE_CONFIG
        print(
            f"warning: {destinations_config} no existe, "
            f"usando {DESTINATIONS_EXAMPLE_CONFIG}"
        )

    destination_layers, _ = load_destination_layers(config_path, base_dir=INPUTS_DIR)
    destination_gdf = load_destinations(
        destination_layers, base_dir=INPUTS_DIR, save=True
    )

    origin_coord = {
        row["id"]: (row.geometry.y, row.geometry.x) for _, row in origin_gdf.iterrows()
    }
    destination_coord = {
        row["id"]: (row.geometry.y, row.geometry.x)
        for _, row in destination_gdf.iterrows()
    }

    origin_coord_snapped = {
        name: snap_to_road(lat, lon, host=osrm_host, port=osrm_port)
        for name, (lat, lon) in origin_coord.items()
    }
    destination_coord_snapped = {
        name: snap_to_road(lat, lon, host=osrm_host, port=osrm_port)
        for name, (lat, lon) in destination_coord.items()
    }

    rows = []
    for k1, v1 in origin_coord_snapped.items():
        for k2, v2 in destination_coord_snapped.items():
            distance = get_driving_distance(
                v1, v2, host=osrm_host, port=osrm_port
            )
            rows.append(
                {
                    "origen_id": k1,
                    "origen_x": v1[1],
                    "origen_y": v1[0],
                    "destino_id": k2,
                    "destino_x": v2[1],
                    "destino_y": v2[0],
                    "distancia": int(distance),
                }
            )

    df = pd.DataFrame(rows)
    origin_label_col = _resolve_col(origin_gdf.columns, origin_id_col)
    results = pd.merge(
        df,
        origin_gdf[["id", origin_label_col]],
        left_on="origen_id",
        right_on="id",
        how="left",
    ).drop(columns="id")
    results = results[
        [
            origin_label_col,
            "origen_id",
            "origen_x",
            "origen_y",
            "destino_id",
            "destino_x",
            "destino_y",
            "distancia",
        ]
    ]

    return results
