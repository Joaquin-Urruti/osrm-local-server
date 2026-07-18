import json
from pathlib import Path

import fiona
import geopandas as gpd
import pandas as pd
import yaml

fiona.drvsupport.supported_drivers["LIBKML"] = "rw"
fiona.drvsupport.supported_drivers["KML"] = "rw"


LAT_COLS = {"lat", "latitude", "latitud", "y"}
LON_COLS = {"lon", "long", "longitude", "longitud", "x"}


def _find_col(columns, options):
    for col in columns:
        if col.lower() in options:
            return col
    return None


def _resolve_col(columns, name):
    for col in columns:
        if col.lower() == name.lower():
            return col
    return None


def _set_id_column(gdf, id_col):
    """Copy id_col into gdf['id']. Raises if column is missing or has duplicates."""
    resolved = _resolve_col(gdf.columns, id_col)
    if resolved is None:
        raise KeyError(
            f"Identifier column '{id_col}' does not exist. "
            f"Available columns: {list(gdf.columns)}"
        )
    dups = gdf[resolved][gdf[resolved].duplicated(keep=False)].unique()
    if len(dups) > 0:
        raise ValueError(
            f"Column '{resolved}' has duplicate values: {list(dups)}. "
            "It must be a unique identifier."
        )
    gdf["id"] = gdf[resolved].astype(str).str.strip().values
    return gdf[["id"] + [c for c in gdf.columns if c != "id"]]


def _set_composite_id_column(gdf, destination_type, name_col):
    """Build id as '{destination_type}_{name}' and set destination_type column."""
    resolved = _resolve_col(gdf.columns, name_col)
    if resolved is None:
        raise KeyError(
            f"Identifier column '{name_col}' does not exist. "
            f"Available columns: {list(gdf.columns)}"
        )
    gdf["destination_type"] = destination_type
    gdf["id"] = destination_type + "_" + gdf[resolved].astype(str).str.strip()
    dups = gdf["id"][gdf["id"].duplicated(keep=False)].unique()
    if len(dups) > 0:
        raise ValueError(
            f"Duplicate composite IDs: {list(dups)}. "
            "Each destination must have a unique id."
        )
    front = ["id", "destination_type"]
    return gdf[front + [c for c in gdf.columns if c not in front]]


def to_point_layer(df, id_col=None, destination_type=None, name_col=None):
    """Normalize an input to a point GeoDataFrame in EPSG:4326.

    - GeoDataFrame with geometry -> sanitize + centroids.
    - lat/lon (or x/y) columns -> build points.
    - id_col: column used as unique identifier for origins.
    - destination_type + name_col: build id as '{type}_{name}' for destinations.
    """
    if isinstance(df, gpd.GeoDataFrame) and df.geometry.notna().any():
        if df.crs is None:
            df = df.set_crs("EPSG:4326")
        gdf = df
    else:
        lat = _find_col(df.columns, LAT_COLS)
        lon = _find_col(df.columns, LON_COLS)
        if not (lat and lon):
            raise ValueError("No polygon geometry nor lat/lon columns found in input")
        gdf = gpd.GeoDataFrame(
            df, geometry=gpd.points_from_xy(df[lon], df[lat]), crs="EPSG:4326"
        ).rename(columns={lon: "x", lat: "y"})

    # geometry ops (make_valid, centroid) on a projected CRS (UTM)
    proj = gdf.to_crs(gdf.estimate_utm_crs())
    proj["geometry"] = proj.geometry.make_valid()
    if not set(proj.geom_type.dropna()) <= {"Point"}:
        proj["geometry"] = proj.geometry.centroid

    result = proj.to_crs("EPSG:4326")

    # keep x/y consistent with the final point geometry
    result["x"] = result.geometry.x
    result["y"] = result.geometry.y

    if destination_type is not None:
        if not name_col:
            raise ValueError("name_col is required when destination_type is used")
        return _set_composite_id_column(result, destination_type, name_col)
    if not id_col:
        raise ValueError("id_col is required for origins")
    return _set_id_column(result, id_col)


def _read_file(path, gpkg_layer=None):
    """Read a single input file into a (Geo)DataFrame based on its extension."""
    ext = path.suffix.lower()
    if ext in {".shp", ".geojson"}:
        return gpd.read_file(path)
    if ext == ".gpkg":
        return (
            gpd.read_file(path, layer=gpkg_layer) if gpkg_layer else gpd.read_file(path)
        )
    if ext in {".kml", ".kmz"}:
        return gpd.read_file(path, driver="LIBKML")
    if ext == ".csv":
        return pd.read_csv(path)
    if ext == ".json":
        return pd.read_json(path)
    if ext in {".xlsx", ".xls"}:
        return pd.read_excel(path)
    raise ValueError(f"Unsupported extension: {ext}")


def load_origins(path, id_col, gpkg_layer=None, save=False):
    """Process an origin input file given its absolute or relative path.

    id_col must name a column with unique values (case-insensitive match).
    When save=True, writes the resulting point layer as origin_centroids.geojson
    in the same directory as the input file.
    """
    path = Path(path).expanduser()
    if not path.is_file():
        raise FileNotFoundError(f"File does not exist: {path}")

    print(f"input file: {path.name}")
    df = _read_file(path, gpkg_layer=gpkg_layer)
    gdf = to_point_layer(df, id_col)

    if save:
        out_path = path.parent / "origin_centroids.geojson"
        gdf.to_file(out_path, driver="GeoJSON")
        print(f"saved: {out_path}")

    return gdf


def load_destination(path, destination_type, name_col, gpkg_layer=None, save=False):
    """Process a destination layer; id = '{destination_type}_{name}'."""
    path = Path(path).expanduser()
    if not path.is_file():
        raise FileNotFoundError(f"File does not exist: {path}")

    print(
        f"destination file: {path.name}"
        + (f" (layer={gpkg_layer})" if gpkg_layer else "")
    )
    try:
        df = _read_file(path, gpkg_layer=gpkg_layer)
    except Exception as exc:
        if gpkg_layer and path.suffix.lower() == ".gpkg":
            layers = fiona.listlayers(path)
            raise ValueError(
                f"Could not read layer '{gpkg_layer}' in {path.name}. "
                f"Available layers: {layers}"
            ) from exc
        raise
    gdf = to_point_layer(df, destination_type=destination_type, name_col=name_col)

    if save:
        out_path = path.parent / f"destinations_{destination_type}.geojson"
        gdf.to_file(out_path, driver="GeoJSON")
        print(f"saved: {out_path}")

    return gdf


_REQUIRED_DEST_KEYS = {"path", "type", "name_col"}


def load_destination_layers(config_path, base_dir=None):
    """Load destination layer entries from a YAML or JSON config file."""
    config_path = Path(config_path).expanduser()
    if not config_path.is_file():
        raise FileNotFoundError(
            f"Config file does not exist: {config_path}. "
            "Copy inputs/destinations.example.yaml to inputs/destinations.yaml"
        )

    raw = config_path.read_text(encoding="utf-8")
    data = (
        yaml.safe_load(raw)
        if config_path.suffix.lower() in {".yaml", ".yml"}
        else json.loads(raw)
    )
    layers = data.get("destinations", data)
    if not isinstance(layers, list) or not layers:
        raise ValueError("The config must contain a non-empty 'destinations' list")

    base = Path(base_dir) if base_dir else config_path.parent
    for i, entry in enumerate(layers, start=1):
        missing = _REQUIRED_DEST_KEYS - entry.keys()
        if missing:
            raise ValueError(
                f"Entry {i} is incomplete, missing fields: {sorted(missing)}"
            )

    return layers, base


def load_destinations(layers, base_dir=None, save=False):
    """Process and merge all destination layers from a config list."""
    base_dir = Path(base_dir) if base_dir else Path(".")
    gdfs = []
    for entry in layers:
        path = Path(entry["path"])
        if not path.is_absolute():
            path = base_dir / path
        gdf = load_destination(
            path,
            destination_type=entry["type"],
            name_col=entry["name_col"],
            gpkg_layer=entry.get("layer"),
        )
        gdfs.append(gdf)

    result = gpd.GeoDataFrame(pd.concat(gdfs, ignore_index=True), crs="EPSG:4326")
    dups = result["id"][result["id"].duplicated(keep=False)].unique()
    if len(dups) > 0:
        raise ValueError(f"Duplicate IDs across destination layers: {list(dups)}")

    if save:
        out_path = base_dir / "destinations.geojson"
        result.to_file(out_path, driver="GeoJSON")
        print(f"saved: {out_path}")

    return result
