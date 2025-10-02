import sys
from datetime import datetime, timedelta
from os import makedirs
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely import Point
from shapely.ops import unary_union

def insert_points_by_time(
    shapefile: gpd.GeoDataFrame,
    point_num: int,
    start_time: datetime,
    end_time: datetime,
    temporal_comp: int,
) -> pd.DataFrame:
    """Generates spatiotemporal points within a shapefile."""
    delta = timedelta(minutes=temporal_comp)
    epochs = int((end_time - start_time).total_seconds() / 60 // temporal_comp)
    data = pd.DataFrame(columns=["latitude", "longitude", "time"])
    actual_time = start_time

    for actual_epoch in range(epochs):
        sys.stdout.write(f"\r{actual_epoch + 1}/{epochs} epochs...")
        latitude, longitude, times = insert_points(
            shapefile, point_num, actual_time, end_time
        )
        actual_time += delta

        for lat, lon, t in zip(latitude, longitude, times):
            data.loc[len(data)] = [lat, lon, t]
    return data

def insert_points(
    shapefile: gpd.GeoDataFrame,
    point_num: int,
    start_time: datetime,
    end_time: datetime,
) -> tuple[list, list, list]:
    """Generates random points within a shapefile with timestamps."""
    total_bounds = shapefile.total_bounds
    lat_points, lon_points, times = [], [], []

    while len(lat_points) < point_num:
        lon = np.random.uniform(total_bounds[0], total_bounds[2])
        lat = np.random.uniform(total_bounds[1], total_bounds[3])
        point = Point(lon, lat)

        if shapefile.contains(point).any():
            lat_points.append(lat)
            lon_points.append(lon)
            time = datetime.fromtimestamp(
                np.random.uniform(start_time.timestamp(), end_time.timestamp())
            )
            times.append(str(time))
            sys.stdout.write(f"\r{len(lat_points)}/{point_num} points added.")
    return lat_points, lon_points, times

def create_allowed_area(
    main_shape: gpd.GeoDataFrame, exclusion_shapes: list[gpd.GeoDataFrame]
) -> gpd.GeoDataFrame:
    """Creates allowed area by subtracting exclusions (including filtered and buffered lines) from main shape."""
    main_shape = main_shape.to_crs("EPSG:3857")
    buffered_geometries = []

    print("🔹 Iniciando processamento de exclusões...")

    total_shapes = len(exclusion_shapes)
    for i, shape in enumerate(exclusion_shapes):
        shape = shape.to_crs(main_shape.crs)
        print(f"  ↪ Processando shapefile {i+1}/{total_shapes} com {len(shape)} geometrias...")

        # Se houver coluna de classificação de rodovias, filtrar por tipos principais
        if "fclass" in shape.columns:
            shape = shape[shape["fclass"].isin(["motorway", "trunk", "primary", "secondary"])]
            print(f"    • Após filtro de fclass: {len(shape)} geometrias restantes")

        for j, geom in enumerate(shape.geometry):
            if geom.geom_type in ["LineString", "MultiLineString"]:
                simplified = geom.simplify(5)  # Simplificar em 5 metros
                buffered_geometries.append(simplified.buffer(10))
            else:
                buffered_geometries.append(geom)

            if (j + 1) % 500 == 0:
                print(f"    • {j+1} geometrias processadas")

    print(f"✅ Total de {len(buffered_geometries)} geometrias de exclusão acumuladas.")
    print("🔄 Unificando todas as geometrias em um único polígono...")

    unioned = gpd.GeoDataFrame(geometry=[unary_union(buffered_geometries)], crs=main_shape.crs)

    print("🔸 Iniciando operação espacial de exclusão (overlay)...")
    allowed = gpd.overlay(main_shape, unioned, how="difference")

    print("✅ Overlay finalizado. Retornando para EPSG:4326")
    return allowed.to_crs("EPSG:4326")

def generate_points_with_concentration(
    allowed_area: gpd.GeoDataFrame,
    concentration_shape: gpd.GeoDataFrame,
    point_num: int,
    start_time: datetime,
    end_time: datetime,
    temporal_comp: int,
    concentration_ratio: float,
) -> pd.DataFrame:
    """Generates points prioritizing a concentration area."""
    concentration_area = gpd.overlay(allowed_area, concentration_shape, how="intersection")
    focused_points = int(point_num * concentration_ratio)
    remaining_points = point_num - focused_points

    print(f"🎯 Gerando {focused_points} pontos concentrados e {remaining_points} pontos restantes...")

    data_concentrated = insert_points_by_time(
        concentration_area, focused_points, start_time, end_time, temporal_comp
    )
    data_remaining = insert_points_by_time(
        allowed_area, remaining_points, start_time, end_time, temporal_comp
    )

    return pd.concat([data_concentrated, data_remaining], ignore_index=True)

def out_dir(output_path: str) -> None:
    """Creates output directory if it doesn't exist."""
    makedirs(output_path, exist_ok=True)

def build_circular_concentration_area(shape: gpd.GeoDataFrame, radius_m: float, position: str) -> gpd.GeoDataFrame:
    """
    Cria uma área de concentração circular baseada no centroide do shapefile.
    - position = "in": apenas o buffer interno
    - position = "out": anel externo (buffer maior - buffer menor)
    - position = "both": união das duas
    """
    shape = shape.to_crs("EPSG:3857")
    center = shape.unary_union.centroid
    inner_buffer = center.buffer(radius_m)

    if position == "in":
        result = gpd.GeoDataFrame(geometry=[inner_buffer], crs=shape.crs)
    elif position == "out":
        outer_buffer = center.buffer(radius_m * 1.25)
        ring = outer_buffer.difference(inner_buffer)
        result = gpd.GeoDataFrame(geometry=[ring], crs=shape.crs)
    elif position == "both":
        outer_buffer = center.buffer(radius_m * 1.25)
        ring = outer_buffer.difference(inner_buffer)
        result = gpd.GeoDataFrame(geometry=[inner_buffer, ring], crs=shape.crs)
    else:
        raise ValueError(f"Posição inválida para concentração circular: {position}")

    return result.to_crs("EPSG:4326")
