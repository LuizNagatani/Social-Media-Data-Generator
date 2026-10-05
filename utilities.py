import sys
from datetime import datetime, timedelta
from os import makedirs

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import Point
from shapely.ops import unary_union
import shapely


def insert_points_by_time(
    shapefile: gpd.GeoDataFrame,
    point_num: int,
    start_time: datetime,
    end_time: datetime,
    temporal_comp: int,
) -> pd.DataFrame:
    """
    Gera até ``point_num`` pontos dentro do shapefile, com distribuição
    uniforme na área e timestamps aleatórios entre ``start_time`` e
    ``end_time``.

    ``temporal_comp`` é mantido apenas por compatibilidade.

    Retorna um DataFrame vazio se a área for vazia ou tiver limites inválidos.
    """
    del temporal_comp

    if shapefile is None or shapefile.empty:
        print("Area vazia em insert_points_by_time; nenhum ponto gerado.")
        return pd.DataFrame(columns=["latitude", "longitude", "timestamp"])

    shapefile = shapefile[
        shapefile.geometry.notna() & ~shapefile.geometry.is_empty
    ]
    if shapefile.empty:
        print("Todas as geometrias estao vazias; nenhum ponto gerado.")
        return pd.DataFrame(columns=["latitude", "longitude", "timestamp"])

    minx, miny, maxx, maxy = shapefile.total_bounds
    bounds = np.array([minx, miny, maxx, maxy], dtype=float)

    if not np.isfinite(bounds).all() or maxx <= minx or maxy <= miny:
        print(
            "Bounds invalidos em insert_points_by_time "
            f"(minx={minx}, maxx={maxx}, miny={miny}, maxy={maxy}). "
            "Nenhum ponto sera gerado para esta area."
        )
        return pd.DataFrame(columns=["latitude", "longitude", "timestamp"])

    geom_union = shapefile.unary_union

    # Recortes estreitos e partes distantes tornam a rejeicao por bounds lenta.
    # A triangulacao restrita preserva bordas e buracos do poligono.
    bbox_area = (maxx - minx) * (maxy - miny)
    if (
        point_num > 0
        and geom_union.area / bbox_area < 0.05
        and hasattr(shapely, "constrained_delaunay_triangles")
    ):
        triangles = list(shapely.constrained_delaunay_triangles(geom_union).geoms)
        triangles = [triangle for triangle in triangles if triangle.area > 0]
        if triangles:
            areas = np.array([triangle.area for triangle in triangles])
            choices = np.random.choice(len(triangles), size=point_num, p=areas / areas.sum())
            vertices = np.array([list(triangle.exterior.coords)[:3] for triangle in triangles])
            selected = vertices[choices]
            u = np.sqrt(np.random.random(point_num))
            v = np.random.random(point_num)
            coords = ((1 - u)[:, None] * selected[:, 0]
                      + (u * (1 - v))[:, None] * selected[:, 1]
                      + (u * v)[:, None] * selected[:, 2])
            seconds = max((end_time - start_time).total_seconds(), 1)
            return pd.DataFrame({
                "latitude": coords[:, 1],
                "longitude": coords[:, 0],
                "timestamp": [start_time + timedelta(seconds=float(offset))
                              for offset in np.random.uniform(0, seconds, point_num)],
            })

    xs: list[float] = []
    ys: list[float] = []
    times: list[datetime] = []

    total_seconds = max((end_time - start_time).total_seconds(), 1)
    max_tries = point_num * 1000
    tries = 0

    while len(xs) < point_num and tries < max_tries:
        tries += 1

        x = float(np.random.uniform(minx, maxx))
        y = float(np.random.uniform(miny, maxy))
        point = Point(x, y)

        if geom_union.contains(point):
            xs.append(x)
            ys.append(y)

            offset = float(np.random.uniform(0, total_seconds))
            times.append(start_time + timedelta(seconds=offset))

    if len(xs) < point_num:
        print(
            f"So foi possivel gerar {len(xs)} pontos de {point_num} "
            f"solicitados apos {tries} tentativas."
        )

    return pd.DataFrame(
        {
            "latitude": ys,
            "longitude": xs,
            "timestamp": times,
        }
    )


def insert_points(
    shapefile: gpd.GeoDataFrame,
    point_num: int,
    start_time: datetime,
    end_time: datetime,
) -> tuple[list[float], list[float], list[str]]:
    """
    Gera pontos aleatórios dentro do shapefile com timestamps.

    Mantido por compatibilidade com versões anteriores.
    """
    total_bounds = shapefile.total_bounds
    lat_points: list[float] = []
    lon_points: list[float] = []
    times: list[str] = []

    while len(lat_points) < point_num:
        lon = float(np.random.uniform(total_bounds[0], total_bounds[2]))
        lat = float(np.random.uniform(total_bounds[1], total_bounds[3]))
        point = Point(lon, lat)

        if shapefile.contains(point).any():
            lat_points.append(lat)
            lon_points.append(lon)
            time = datetime.fromtimestamp(
                np.random.uniform(
                    start_time.timestamp(),
                    end_time.timestamp(),
                )
            )
            times.append(str(time))
            sys.stdout.write(f"\r{len(lat_points)}/{point_num} points added.")

    return lat_points, lon_points, times


def create_allowed_area(
    main_shape: gpd.GeoDataFrame,
    exclusion_shapes: list[gpd.GeoDataFrame],
) -> gpd.GeoDataFrame:
    """
    Cria a área permitida subtraindo exclusões do shapefile principal.

    Geometrias lineares são simplificadas e transformadas em buffers antes
    da operação espacial.
    """
    main_shape = main_shape.to_crs("EPSG:3857")
    buffered_geometries = []

    print("Iniciando processamento de exclusoes...")

    total_shapes = len(exclusion_shapes)
    for index, shape in enumerate(exclusion_shapes, start=1):
        shape = shape.to_crs(main_shape.crs)
        print(
            f"Processando shapefile {index}/{total_shapes} "
            f"com {len(shape)} geometrias..."
        )

        if "fclass" in shape.columns:
            shape = shape[
                shape["fclass"].isin(
                    ["motorway", "trunk", "primary", "secondary"]
                )
            ]
            print(
                "Apos filtro de fclass: "
                f"{len(shape)} geometrias restantes"
            )

        for geom_index, geom in enumerate(shape.geometry, start=1):
            if geom.geom_type in ["LineString", "MultiLineString"]:
                simplified = geom.simplify(5)
                buffered_geometries.append(simplified.buffer(10))
            else:
                buffered_geometries.append(geom)

            if geom_index % 500 == 0:
                print(f"{geom_index} geometrias processadas")

    print(
        f"Total de {len(buffered_geometries)} geometrias "
        "de exclusao acumuladas."
    )
    print("Unificando geometrias de exclusao...")

    unioned = gpd.GeoDataFrame(
        geometry=[unary_union(buffered_geometries)],
        crs=main_shape.crs,
    )

    print("Executando operacao espacial de diferenca...")
    allowed = gpd.overlay(main_shape, unioned, how="difference")

    print("Overlay finalizado. Retornando para EPSG:4326.")
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
    """
    Gera pontos priorizando uma área de concentração.

    Parte dos pontos é gerada na área de concentração e o restante na área
    permitida como um todo.
    """
    concentration_area = gpd.overlay(
        allowed_area,
        concentration_shape,
        how="intersection",
    )
    focused_points = int(point_num * concentration_ratio)
    remaining_points = point_num - focused_points

    print(
        f"Gerando {focused_points} pontos concentrados e "
        f"{remaining_points} pontos restantes..."
    )

    data_concentrated = insert_points_by_time(
        concentration_area,
        focused_points,
        start_time,
        end_time,
        temporal_comp,
    )
    data_remaining = insert_points_by_time(
        allowed_area,
        remaining_points,
        start_time,
        end_time,
        temporal_comp,
    )

    return pd.concat(
        [data_concentrated, data_remaining],
        ignore_index=True,
    )


def out_dir(output_path: str) -> None:
    """Cria o diretório de saída, caso ainda não exista."""
    makedirs(output_path, exist_ok=True)


def build_circular_concentration_area(
    shape: gpd.GeoDataFrame,
    radius_m: float,
    position: str,
) -> gpd.GeoDataFrame:
    """
    Cria uma área de concentração circular baseada no centroide do shapefile.

    ``position`` pode ser:
    - "in": apenas o buffer interno
    - "out": anel externo
    - "both": união das duas regiões
    """
    shape = shape.to_crs("EPSG:3857")
    center = shape.unary_union.centroid
    inner_buffer = center.buffer(radius_m)

    if position == "in":
        result = gpd.GeoDataFrame(
            geometry=[inner_buffer],
            crs=shape.crs,
        )
    elif position == "out":
        outer_buffer = center.buffer(radius_m * 1.25)
        ring = outer_buffer.difference(inner_buffer)
        result = gpd.GeoDataFrame(
            geometry=[ring],
            crs=shape.crs,
        )
    elif position == "both":
        outer_buffer = center.buffer(radius_m * 1.25)
        ring = outer_buffer.difference(inner_buffer)
        result = gpd.GeoDataFrame(
            geometry=[inner_buffer, ring],
            crs=shape.crs,
        )
    else:
        raise ValueError(
            "Posicao invalida para concentracao circular: "
            f"{position}"
        )

    return result.to_crs("EPSG:4326")
