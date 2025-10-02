import argparse
from datetime import datetime
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import geopandas as gpd
from utilities import (
    insert_points_by_time,
    out_dir,
    create_allowed_area,
    build_circular_concentration_area,
)

parser = argparse.ArgumentParser(description="Generate spatiotemporal points within allowed areas")
parser.add_argument("points_number", type=int)
parser.add_argument("temporal_component", type=int)
parser.add_argument("start_timestamp", type=int)
parser.add_argument("end_timestamp", type=int)
parser.add_argument("shapefile_main", type=str)
parser.add_argument("exclusion_shapefiles", type=str, nargs="+")
parser.add_argument("--concentration_targets", type=str, nargs="*", default=[],
                    help="List of shapefile:ratio pairs for point concentration")

def validate_shapefiles(main_shape, exclusions):
    if not os.path.exists(main_shape):
        raise FileNotFoundError(f"Main file not found: {main_shape}")
    for excl in exclusions:
        if not os.path.exists(excl):
            raise FileNotFoundError(f"Exclusion file not found: {excl}")

def main():
    args = parser.parse_args()
    output_path = "output/"
    out_dir(output_path)

    validate_shapefiles(args.shapefile_main, args.exclusion_shapefiles)

    main_shape = gpd.read_file(args.shapefile_main).to_crs("EPSG:4326")
    exclusions = [gpd.read_file(excl).to_crs(main_shape.crs) for excl in args.exclusion_shapefiles]
    allowed_area = create_allowed_area(main_shape, exclusions)

    if allowed_area.empty:
        raise ValueError("No valid area remaining after exclusions!")

    start_time = datetime.fromtimestamp(args.start_timestamp)
    end_time = datetime.fromtimestamp(args.end_timestamp)

    total_points = args.points_number
    dataframes = []
    allocation_plan = []
    total_ratio = 0.0

    for target in args.concentration_targets:
        parts = target.split(":")
        if len(parts) < 2:
            raise ValueError(f"Formato inválido em concentration_target: {target}")

        path = parts[0]
        ratio = float(parts[1])
        mode = parts[2] if len(parts) > 2 else "polygon"
        radius = float(parts[3]) if len(parts) > 3 else None
        position = parts[4] if len(parts) > 4 else "in"

        total_ratio += ratio
        qtd = int(total_points * ratio)

        allocation_plan.append({
            "path": path,
            "ratio": ratio,
            "mode": mode,
            "radius": radius,
            "position": position,
            "points": qtd
        })

    if total_ratio > 1.0:
        raise ValueError("Soma das concentrações excede 100%")

    for item in allocation_plan:
        path = item["path"]
        qtd = item["points"]
        mode = item["mode"]

        print(f"🎯 Gerando {qtd} pontos em {path} com modo {mode}")

        if not os.path.exists(path):
            raise FileNotFoundError(f"Arquivo de concentração não encontrado: {path}")

        shape = gpd.read_file(path).to_crs("EPSG:4326")

        if mode == "circle":
            radius = item["radius"]
            position = item["position"]
            area = build_circular_concentration_area(shape, radius, position)
        else:
            area = gpd.overlay(allowed_area, shape, how="intersection")

        df = insert_points_by_time(area, qtd, start_time, end_time, args.temporal_component)
        dataframes.append(df)

    # pontos restantes
    allocated_total = sum(item["points"] for item in allocation_plan)
    remaining = total_points - allocated_total
    if remaining > 0:
        print(f"🔄 Gerando {remaining} pontos restantes fora das concentrações")
        df = insert_points_by_time(allowed_area, remaining, start_time, end_time, args.temporal_component)
        dataframes.append(df)

    # se ainda faltar pontos
    total_final = sum(len(df) for df in dataframes)
    deficit = total_points - total_final
    if deficit > 0:
        print(f"⚠️ Regerando {deficit} pontos faltantes para atingir {total_points}")
        df = insert_points_by_time(allowed_area, deficit, start_time, end_time, args.temporal_component)
        dataframes.append(df)

    data = pd.concat(dataframes, ignore_index=True)
    data.to_csv(f"{output_path}points.csv", index=False)

    # mapas
    fig, ax = plt.subplots(figsize=(12, 8))
    allowed_area.plot(ax=ax, color="white", edgecolor="black")
    gdf = gpd.GeoDataFrame(data, geometry=gpd.points_from_xy(data.longitude, data.latitude, crs="EPSG:4326"))
    gdf.plot(ax=ax, color="red", markersize=20)
    plt.savefig(f"{output_path}map.png")
    plt.close()

    m = allowed_area.explore(color="white", height=500)
    gdf.explore(m=m, color="red", name="Generated Points")
    m.save(f"{output_path}map.html")


if __name__ == "__main__":
    main()
