import sys
from datetime import datetime, timedelta
from os import makedirs

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import Point
from shapely.ops import unary_union


def insert_points_by_time(
    shapefile: gpd.GeoDataFrame,
    point_num: int,
    start_time: datetime,
    end_time: datetime,
    temporal_comp: int,
) -> pd.DataFrame:
    """
    Gera até ``point_num`` pontos dentro do shapefile (uniforme na área),
    com timestamps aleatórios entre ``start_time`` e ``end_time``.

    ``temporal_comp`` é ignorado (mantido apenas por compatibilidade).

    Se a área for vazia ou tiver bounds inválidos, retorna um DataFrame vazio.
    """
    # 1) Sanitizar geometria
    if shapefile is None or shapefile.empty:
        print("⚠️ Área vazia em insert_points_by_time; nenhum ponto gerado.")
        return pd.DataFrame(
            columns=["latitude", "longitude", "timestamp"]
        )

    shapefile = shapefile[
        shapefile.geometry.notna() & ~shapefile.geometry.is_empty
    ]
    if shapefile.empty:
        print("⚠️ Todas as geometrias estão vazias; nenhum ponto gerado.")
        return pd.DataFrame(
            columns=["latitude", "longitude", "timestamp"]
        )

    # 2) Bounds seguros
    minx, miny, maxx, maxy = shapefile.total_bounds
    bounds = np.array([minx, miny, maxx, maxy], dtype=float)

    if (
        not np.isfinite(bounds).all()
        or maxx <= minx
        or maxy <= miny
    ):
        print(
            "⚠️ Bounds inválidos em insert_points_by_time "
            f"(minx={minx}, maxx={maxx}, miny={miny}, maxy={maxy}). "
            "Nenhum ponto será gerado para esta área."
        )
        return pd.DataFrame(
            columns=["latitude", "longitude", "timestamp"]
        )

    # 3) União das geometrias para teste de pertinência
    geom_union = shapefile.unary_union

    xs: list[float] = []
    ys: list[float] = []
    times: list[datetime] = []

    # total de segundos no intervalo de tempo
    total_seconds = max(
        (end_time - start_time).total_seconds(),
        1,
    )

    # limite de tentativas para não travar se a área for muito pequena
    max_tries = point_num * 1000
    tries = 0

    while len(xs) < point_num and tries < max_tries:
        tries += 1

        x = float(np.random.uniform(minx, maxx))
        y = float(np.random.uniform(miny, maxy))
        p = Point(x, y)

        if geom_union.contains(p):
            xs.append(x)
            ys.append(y)

            offset = float(np.random.uniform(0, total_seconds))
            times.append(start_time + timedelta(seconds=offset))

    if len(xs) < point_num:
        print(
            f"⚠️ Só foi possível gerar {len(xs)} pontos de {point_num} "
            f"solicitados após {tries} tentativas."
        )

    df = pd.DataFrame(
        {
            "latitude": ys,   # y
            "longitude": xs,  # x
            "timestamp": times,
        }
    )
    return df


def insert_points(
    shapefile: gpd.GeoDataFrame,
    point_num: int,
    start_time: datetime,
    end_time: datetime,
) -> tuple[list, list, list]:
    """
    Gera pontos aleatórios dentro do shapefile com timestamps.

    Mantido por compatibilidade com versões anteriores.
    """
    total_bounds = shapefile.total_bounds
    lat_points: list[float] = []
    lon_points: list[float] = []
    times: list[str] = []

    while len(lat_points) < point_num:
        lon = float(
            np.random.uniform(total_bounds[0], total_bounds[2])
        )
        lat = float(
            np.random.uniform(total_bounds[1], total_bounds[3])
        )
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
            sys.stdout.write(
                f"\r{len(lat_points)}/{point_num} points added."
            )
    return lat_points, lon_points, times


def create_allowed_area(
    main_shape: gpd.GeoDataFrame,
    exclusion_shapes: list[gpd.GeoDataFrame],
) -> gpd.GeoDataFrame:
    """
    Cria área permitida subtraindo exclusões do shapefile principal.

    Inclui tratamento de geometrias lineares (rodovias etc.) com buffer.
    """
    main_shape = main_shape.to_crs("EPSG:3857")
    buffered_geometries: list = []

    print("🔹 Iniciando processamento de exclusões...")

    total_shapes = len(exclusion_shapes)
    for i, shape in enumerate(exclusion_shapes):
        shape = shape.to_crs(main_shape.crs)
        print(
            f"  ↪ Processando shapefile {i + 1}/{total_shapes} "
            f"com {len(shape)} geometrias..."
        )

        # Se houver coluna de classificação de rodovias, filtrar por tipos principais
        if "fclass" in shape.columns:
            shape = shape[
                shape["fclass"].isin(
                    ["motorway", "trunk", "primary", "secondary"]
                )
            ]
            print(
                "    • Após filtro de fclass: "
                f"{len(shape)} geometrias restantes"
            )

        for j, geom in enumerate(shape.geometry):
            if geom.geom_type in ["LineString", "MultiLineString"]:
                simplified = geom.simplify(5)  # simplificar em 5 metros
                buffered_geometries.append(simplified.buffer(10))
            else:
                buffered_geometries.append(geom)

            if (j + 1) % 500 == 0:
                print(f"    • {j + 1} geometrias processadas")

    print(
        f"✅ Total de {len(buffered_geometries)} "
        "geometrias de exclusão acumuladas."
    )
    print("🔄 Unificando todas as geometrias em um único polígono...")

    unioned = gpd.GeoDataFrame(
        geometry=[unary_union(buffered_geometries)],
        crs=main_shape.crs,
    )

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
    """
    Gera pontos priorizando uma área de concentração.

    Parte dos pontos cai na área de concentração, o restante na área
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
        f"🎯 Gerando {focused_points} pontos concentrados e "
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
    """
    Cria diretório de saída se ele ainda não existir.

    Parameters
    ----------
    output_path : str
        Caminho do diretório de saída.
    """
    makedirs(output_path, exist_ok=True)


def build_circular_concentration_area(
    shape: gpd.GeoDataFrame,
    radius_m: float,
    position: str,
) -> gpd.GeoDataFrame:
    """
    Cria uma área de concentração circular baseada no centroide do shapefile.

    Parameters
    ----------
    shape : geopandas.GeoDataFrame
        Geometrias de referência.
    radius_m : float
        Raio do círculo interno, em metros (no CRS projetado).
    position : str
        Uma das opções:
        - "in": apenas o buffer interno
        - "out": anel externo (buffer maior - buffer menor)
        - "both": união das duas regiões

    Returns
    -------
    geopandas.GeoDataFrame
        Geometria(s) da área de concentração, em EPSG:4326.
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
            "Posição inválida para concentração circular: "
            f"{position}"
        )

    return result.to_crs("EPSG:4326")
