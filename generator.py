import argparse
<<<<<<< HEAD
from datetime import datetime
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import geopandas as gpd
=======
import os
from datetime import datetime

import geopandas as gpd
import matplotlib
import matplotlib.pyplot as plt
>>>>>>> 0b6ef74 (Updated project files)
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

from utilities import (
<<<<<<< HEAD
    insert_points_by_time,
    out_dir,
    create_allowed_area,
    build_circular_concentration_area,
)

=======
    build_circular_concentration_area,
    create_allowed_area,
    insert_points_by_time,
    out_dir,
)

matplotlib.use("Agg")

DEFAULT_WORKING_EPSG = "EPSG:31983"

>>>>>>> 0b6ef74 (Updated project files)
parser = argparse.ArgumentParser(
    description="Generate spatiotemporal points within allowed areas"
)
parser.add_argument("points_number", type=int)
parser.add_argument("temporal_component", type=int)
parser.add_argument("start_timestamp", type=int)
parser.add_argument("end_timestamp", type=int)
parser.add_argument("shapefile_main", type=str)
parser.add_argument("exclusion_shapefiles", type=str, nargs="+")
parser.add_argument(
    "--concentration_targets",
    type=str,
    nargs="*",
    default=[],
    help=(
        "List of shapefile:ratio[:mode[:radius[:position]]] "
        "for point concentration"
    ),
)
parser.add_argument(
    "--weighted_shapefile",
    type=str,
    default=None,
    help=(
        "Optional shapefile (ZIP/SHP) with a 'prob' column to weight "
        "remaining random points"
    ),
)

<<<<<<< HEAD
DEFAULT_WORKING_EPSG = "EPSG:31983"  # SIRGAS 2000 / UTM 23S (comum em SP)


def add_north_arrow(ax, size_frac=0.1, pad_frac=0.02):
    """
    Adiciona uma seta de norte simples no canto superior direito do mapa.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        Eixo onde a seta será desenhada.
    size_frac : float
        Fração da altura do mapa usada pela seta.
    pad_frac : float
        Afastamento da borda.
=======

def add_north_arrow(ax, size_frac=0.1, pad_frac=0.02):
    """
    Add a simple north arrow to the upper-right corner of the map.
>>>>>>> 0b6ef74 (Updated project files)
    """
    x_min, x_max = ax.get_xlim()
    y_min, y_max = ax.get_ylim()

    dx = x_max - x_min
    dy = y_max - y_min

    x = x_min + dx * (1 - pad_frac)
    y0 = y_min + dy * (1 - pad_frac - size_frac)
    y1 = y_min + dy * (1 - pad_frac)

    ax.annotate(
        "",
        xy=(x, y1),
        xytext=(x, y0),
        arrowprops={
            "facecolor": "black",
            "edgecolor": "black",
            "arrowstyle": "-|>",
            "linewidth": 1.2,
        },
        zorder=10,
    )

    ax.text(
        x,
        y1 + dy * 0.01,
        "N",
        ha="center",
        va="bottom",
        fontsize=10,
        fontweight="bold",
        zorder=10,
    )


def add_scalebar(ax, length_m=1000, location=(0.5, 0.01), height_frac=0.01):
    """
<<<<<<< HEAD
    Adiciona uma barra de escala em metros.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        Eixo onde a barra será desenhada.
    length_m : float
        Comprimento da barra (em unidades do CRS; em UTM ~ metros).
    location : tuple
        Posição relativa (fração do eixo) da origem da barra.
    height_frac : float
        Espessura vertical em fração da altura.
=======
    Add a scale bar in meters.
>>>>>>> 0b6ef74 (Updated project files)
    """
    x_min, x_max = ax.get_xlim()
    y_min, y_max = ax.get_ylim()
    dx = x_max - x_min
    dy = y_max - y_min

    x0 = x_min + dx * location[0]
    y0 = y_min + dy * location[1]
    x1 = x0 + length_m

    if x1 > x_max:
        length_m = (x_max - x0) * 0.8
        x1 = x0 + length_m

    ax.plot([x0, x1], [y0, y0], color="black", linewidth=2, zorder=10)

    ax.plot(
        [x0, x0],
        [y0 - dy * height_frac / 2, y0 + dy * height_frac / 2],
        color="black",
        linewidth=2,
        zorder=10,
    )
    ax.plot(
        [x1, x1],
        [y0 - dy * height_frac / 2, y0 + dy * height_frac / 2],
        color="black",
        linewidth=2,
        zorder=10,
    )

    label_km = int(round(length_m / 1000))
    ax.text(
        (x0 + x1) / 2,
        y0 + dy * height_frac,
        f"{label_km} km",
        ha="center",
        va="bottom",
        fontsize=9,
        zorder=10,
    )


def add_map_legend(ax):
    """
<<<<<<< HEAD
    Cria uma legenda básica para área permitida e pontos gerados.
=======
    Create a basic legend for allowed area and generated points.
>>>>>>> 0b6ef74 (Updated project files)
    """
    legend_elements = [
        Patch(
            facecolor="#f7f7f7",
            edgecolor="#555555",
            label="Área permitida",
        ),
        Line2D(
            [0],
            [0],
            marker="o",
            color="none",
            markerfacecolor="#d62728",
            markersize=6,
            label="Pontos gerados",
        ),
    ]

    ax.legend(
        handles=legend_elements,
        loc="lower left",
        bbox_to_anchor=(0.001, 0),
        frameon=True,
        framealpha=0.9,
        facecolor="white",
        edgecolor="#cccccc",
        fontsize=9,
    )


def main():
    args = parser.parse_args()
    output_path = "output/"
    out_dir(output_path)

<<<<<<< HEAD
    # ============================
    # Leitura e CRS do shapefile principal
    # ============================
=======
>>>>>>> 0b6ef74 (Updated project files)
    if not os.path.exists(args.shapefile_main):
        raise FileNotFoundError(
            f"Main file not found: {args.shapefile_main}"
        )

    main_shape = gpd.read_file(args.shapefile_main)
    if main_shape.crs is None:
        print(
<<<<<<< HEAD
            f"⚠️  CRS não definido no shapefile principal. "
=======
            "CRS nao definido no shapefile principal. "
>>>>>>> 0b6ef74 (Updated project files)
            f"Definindo como {DEFAULT_WORKING_EPSG}."
        )
        main_shape.set_crs(DEFAULT_WORKING_EPSG, inplace=True)
    working_crs = main_shape.crs

<<<<<<< HEAD
    # ============================
    # Processamento de exclusões (opcional)
    # ============================
=======
>>>>>>> 0b6ef74 (Updated project files)
    if args.exclusion_shapefiles and args.exclusion_shapefiles != [""]:
        exclusions = [
            gpd.read_file(excl).to_crs(working_crs)
            for excl in args.exclusion_shapefiles
            if os.path.exists(excl)
        ]
<<<<<<< HEAD
        print("🔹 Iniciando processamento de exclusões...")
        allowed_area = create_allowed_area(main_shape, exclusions)
    else:
        print(
            "⚠️  Nenhum shapefile de exclusão fornecido. "
            "Usando toda a área do shapefile principal."
=======
        print("Iniciando processamento de exclusoes.")
        allowed_area = create_allowed_area(main_shape, exclusions)
    else:
        print(
            "Nenhum shapefile de exclusao fornecido. "
            "Usando toda a area do shapefile principal."
>>>>>>> 0b6ef74 (Updated project files)
        )
        allowed_area = main_shape.copy()

    if allowed_area.crs is None:
        print(
<<<<<<< HEAD
            f"⚠️  CRS de allowed_area indefinido. "
=======
            "CRS de allowed_area indefinido. "
>>>>>>> 0b6ef74 (Updated project files)
            f"Definindo como {working_crs}."
        )
        allowed_area.set_crs(working_crs, inplace=True)
    else:
        allowed_area = allowed_area.to_crs(working_crs)

    if allowed_area.empty:
        raise ValueError("No valid area remaining after exclusions!")

<<<<<<< HEAD
    # ============================
    # Parâmetros temporais
    # ============================
=======
>>>>>>> 0b6ef74 (Updated project files)
    start_time = datetime.fromtimestamp(args.start_timestamp)
    end_time = datetime.fromtimestamp(args.end_timestamp)

    total_points = args.points_number
    dataframes = []
    allocation_plan = []
    total_ratio = 0.0

<<<<<<< HEAD
    # ============================
    # Concentrações opcionais
    # ============================
=======
>>>>>>> 0b6ef74 (Updated project files)
    for target in args.concentration_targets:
        parts = target.split(":")
        if len(parts) < 2:
            raise ValueError(
<<<<<<< HEAD
                f"Formato inválido em concentration_target: {target}"
=======
                f"Formato invalido em concentration_target: {target}"
>>>>>>> 0b6ef74 (Updated project files)
            )

        path = parts[0]
        ratio = float(parts[1])
        mode = parts[2] if len(parts) > 2 else "polygon"
        radius = float(parts[3]) if len(parts) > 3 else None
        position = parts[4] if len(parts) > 4 else "in"

        total_ratio += ratio
        qtd = int(total_points * ratio)

        allocation_plan.append(
            {
                "path": path,
                "ratio": ratio,
                "mode": mode,
                "radius": radius,
                "position": position,
                "points": qtd,
            }
        )

    if total_ratio > 1.0:
<<<<<<< HEAD
        raise ValueError("Soma das concentrações excede 100%")

    # ============================
    # Geração dos pontos concentrados
    # ============================
=======
        raise ValueError("Soma das concentracoes excede 100%")

>>>>>>> 0b6ef74 (Updated project files)
    for item in allocation_plan:
        path = item["path"]
        qtd = item["points"]
        mode = item["mode"]

<<<<<<< HEAD
        print(f"🎯 Gerando {qtd} pontos em {path} com modo {mode}")

        if not os.path.exists(path):
            raise FileNotFoundError(
                f"Arquivo de concentração não encontrado: {path}"
=======
        print(f"Gerando {qtd} pontos em {path} com modo {mode}")

        if not os.path.exists(path):
            raise FileNotFoundError(
                f"Arquivo de concentracao nao encontrado: {path}"
>>>>>>> 0b6ef74 (Updated project files)
            )

        shape = gpd.read_file(path).to_crs(working_crs)

        if mode == "circle":
            radius = item["radius"]
            position = item["position"]
            area = build_circular_concentration_area(shape, radius, position)
        else:
            area = gpd.overlay(allowed_area, shape, how="intersection")

        df = insert_points_by_time(
            area,
            qtd,
            start_time,
            end_time,
            args.temporal_component,
        )

        gdf_tmp = gpd.GeoDataFrame(
            df,
            geometry=gpd.points_from_xy(df["longitude"], df["latitude"]),
            crs=working_crs,
        )
        gdf_tmp_4326 = gdf_tmp.to_crs("EPSG:4326")

        df["longitude"] = gdf_tmp_4326.geometry.x
        df["latitude"] = gdf_tmp_4326.geometry.y

        dataframes.append(df)

<<<<<<< HEAD
    # ============================
    # Pontos restantes (fora das concentrações)
    # ============================
=======
>>>>>>> 0b6ef74 (Updated project files)
    allocated_total = sum(item["points"] for item in allocation_plan)
    remaining = total_points - allocated_total

    if remaining > 0:
        print(
<<<<<<< HEAD
            f"🔄 Gerando {remaining} pontos restantes "
            "fora das concentrações"
=======
            f"Gerando {remaining} pontos restantes fora das concentracoes."
>>>>>>> 0b6ef74 (Updated project files)
        )

        if args.weighted_shapefile and os.path.exists(
            args.weighted_shapefile
        ):
            print(
<<<<<<< HEAD
                f"🧮 Usando shapefile ponderado: {args.weighted_shapefile}"
=======
                f"Usando shapefile ponderado: {args.weighted_shapefile}"
>>>>>>> 0b6ef74 (Updated project files)
            )

            weights_gdf = gpd.read_file(args.weighted_shapefile)
            if weights_gdf.crs is None:
                print(
<<<<<<< HEAD
                    "⚠️  CRS do shapefile ponderado não definido. "
=======
                    "CRS do shapefile ponderado nao definido. "
>>>>>>> 0b6ef74 (Updated project files)
                    f"Assumindo {working_crs}."
                )
                weights_gdf = weights_gdf.set_crs(allowed_area.crs)
            else:
                weights_gdf = weights_gdf.set_crs(allowed_area.crs)

            if "prob" not in weights_gdf.columns:
                raise ValueError(
<<<<<<< HEAD
                    "Shapefile ponderado não possui coluna 'prob'."
=======
                    "Shapefile ponderado nao possui coluna 'prob'."
>>>>>>> 0b6ef74 (Updated project files)
                )

            weights_gdf = weights_gdf[["prob", "geometry"]].copy()
            weights_gdf = weights_gdf[
                weights_gdf["prob"].notna() & (weights_gdf["prob"] > 0)
            ]

            if weights_gdf.empty:
                print(
<<<<<<< HEAD
                    "⚠️  Shapefile ponderado sem probabilidades válidas. "
                    "Voltando para distribuição uniforme no allowed_area."
=======
                    "Shapefile ponderado sem probabilidades validas. "
                    "Voltando para distribuicao uniforme em allowed_area."
>>>>>>> 0b6ef74 (Updated project files)
                )
                df = insert_points_by_time(
                    allowed_area,
                    remaining,
                    start_time,
                    end_time,
                    args.temporal_component,
                )
                dataframes.append(df)
            else:
                weighted_area = gpd.overlay(
                    weights_gdf,
                    allowed_area,
                    how="intersection",
                )
                if weighted_area.empty:
                    print(
<<<<<<< HEAD
                        "⚠️  Interseção entre área permitida e shapefile "
                        "ponderado é vazia. Voltando para distribuição "
                        "uniforme no allowed_area."
=======
                        "Intersecao entre area permitida e shapefile "
                        "ponderado vazia. Voltando para distribuicao "
                        "uniforme em allowed_area."
>>>>>>> 0b6ef74 (Updated project files)
                    )
                    df = insert_points_by_time(
                        allowed_area,
                        remaining,
                        start_time,
                        end_time,
                        args.temporal_component,
                    )
                    dataframes.append(df)
                else:
<<<<<<< HEAD
                    probs = weighted_area["prob"].astype(float).clip(
                        lower=0
                    )
                    total_prob = probs.sum()
                    if total_prob <= 0:
                        print(
                            "⚠️  Probabilidades na área intersectada somam "
                            "zero. Voltando para distribuição uniforme no "
=======
                    probs = weighted_area["prob"].astype(float).clip(lower=0)
                    total_prob = probs.sum()

                    if total_prob <= 0:
                        print(
                            "Probabilidades na area intersectada somam "
                            "zero. Voltando para distribuicao uniforme em "
>>>>>>> 0b6ef74 (Updated project files)
                            "allowed_area."
                        )
                        df = insert_points_by_time(
                            allowed_area,
                            remaining,
                            start_time,
                            end_time,
                            args.temporal_component,
                        )
                        dataframes.append(df)
                    else:
                        weighted_area["prob_norm"] = probs / total_prob
                        weighted_area["points_alloc"] = (
                            weighted_area["prob_norm"] * remaining
                        ).round().astype(int)

                        diff = remaining - int(
                            weighted_area["points_alloc"].sum()
                        )
                        if diff != 0:
                            order = weighted_area["prob_norm"].sort_values(
                                ascending=False
                            ).index
                            step = 1 if diff > 0 else -1
                            for idx in order[: abs(diff)]:
<<<<<<< HEAD
                                weighted_area.loc[idx, "points_alloc"] += (
                                    step
                                )
=======
                                weighted_area.loc[idx, "points_alloc"] += step
>>>>>>> 0b6ef74 (Updated project files)

                        for _, row in weighted_area.iterrows():
                            n_points = int(row["points_alloc"])
                            if n_points <= 0:
                                continue
<<<<<<< HEAD
=======

>>>>>>> 0b6ef74 (Updated project files)
                            poly_gdf = gpd.GeoDataFrame(
                                geometry=[row.geometry],
                                crs=working_crs,
                            )
                            df_part = insert_points_by_time(
                                poly_gdf,
                                n_points,
                                start_time,
                                end_time,
                                args.temporal_component,
                            )
                            dataframes.append(df_part)
        else:
            df = insert_points_by_time(
                allowed_area,
                remaining,
                start_time,
                end_time,
                args.temporal_component,
            )
            dataframes.append(df)

<<<<<<< HEAD
    # ============================
    # Ajuste final se faltarem pontos
    # ============================
=======
>>>>>>> 0b6ef74 (Updated project files)
    total_final = sum(len(df) for df in dataframes)
    deficit = total_points - total_final
    if deficit > 0:
        print(
<<<<<<< HEAD
            f"⚠️ Regerando {deficit} pontos faltantes "
            f"para atingir {total_points}"
=======
            f"Regerando {deficit} pontos faltantes para atingir "
            f"{total_points}."
>>>>>>> 0b6ef74 (Updated project files)
        )
        df = insert_points_by_time(
            allowed_area,
            deficit,
            start_time,
            end_time,
            args.temporal_component,
        )
        dataframes.append(df)

<<<<<<< HEAD
    # ============================
    # Consolidação e salvamento
    # ============================
=======
>>>>>>> 0b6ef74 (Updated project files)
    if not dataframes:
        raise ValueError(
            "Nenhum ponto foi gerado (lista de dataframes vazia)."
        )

    data = pd.concat(dataframes, ignore_index=True)

    if allowed_area.crs is None:
        allowed_area = allowed_area.set_crs("EPSG:4326")

    gdf_points = gpd.GeoDataFrame(
        data,
        geometry=gpd.points_from_xy(data["longitude"], data["latitude"]),
        crs=allowed_area.crs,
    )

    gdf_latlon = gdf_points.to_crs("EPSG:4326")
    gdf_latlon["latitude"] = gdf_latlon.geometry.y
    gdf_latlon["longitude"] = gdf_latlon.geometry.x

    gdf_latlon.drop(columns="geometry").to_csv(
        f"{output_path}points.csv",
        index=False,
    )

<<<<<<< HEAD
    # ============================
    # Plot estático (PNG)
    # ============================
=======
>>>>>>> 0b6ef74 (Updated project files)
    if allowed_area.crs.is_geographic:
        crs_plot = "EPSG:3857"
        allowed_plot = allowed_area.to_crs(crs_plot)
        gdf_plot = gdf_latlon.to_crs(crs_plot)
    else:
<<<<<<< HEAD
        crs_plot = allowed_area.crs
        allowed_plot = allowed_area
        gdf_plot = gdf_latlon.to_crs(crs_plot)
=======
        allowed_plot = allowed_area
        gdf_plot = gdf_latlon.to_crs(allowed_area.crs)
>>>>>>> 0b6ef74 (Updated project files)

    fig, ax = plt.subplots(figsize=(8, 8))

    allowed_plot.boundary.plot(
        ax=ax,
        color="black",
        linewidth=0.5,
        label="Área permitida",
    )

    gdf_plot.plot(
        ax=ax,
        color="red",
        markersize=5,
        alpha=0.7,
        label="Pontos gerados",
    )

    minx, miny, maxx, maxy = allowed_plot.total_bounds
    dx = maxx - minx
    dy = maxy - miny
    margin_x = 0.05 * dx
    margin_y = 0.05 * dy

<<<<<<< HEAD
    extra_top = 2 * margin_y
    extra_bottom = 2 * margin_y

    bottom = miny - extra_bottom
    top = maxy + extra_top
=======
    bottom = miny - 2 * margin_y
    top = maxy + 2 * margin_y
>>>>>>> 0b6ef74 (Updated project files)

    ax.set_xlim(minx - margin_x, maxx + margin_x)
    ax.set_ylim(bottom, top)
    ax.set_aspect("equal")
    ax.set_axis_off()
    ax.set_title("Pontos sintéticos gerados", fontsize=16)

    arrow_x = minx + dx * 0.5
    arrow_y_head = top - 0.6 * margin_y
    arrow_y_tail = arrow_y_head - 0.8 * margin_y

    ax.annotate(
        "",
        xy=(arrow_x, arrow_y_head),
        xytext=(arrow_x, arrow_y_tail),
<<<<<<< HEAD
        arrowprops={"arrowstyle": "->", "color": "black", "linewidth": 1.5},
=======
        arrowprops={
            "arrowstyle": "->",
            "color": "black",
            "linewidth": 1.5,
        },
>>>>>>> 0b6ef74 (Updated project files)
    )
    ax.text(
        arrow_x,
        arrow_y_head + 0.2 * margin_y,
        "N",
        ha="center",
        va="bottom",
        fontsize=12,
    )

    scalebar_km = 2
    scalebar_len = scalebar_km * 1000.0
<<<<<<< HEAD

=======
>>>>>>> 0b6ef74 (Updated project files)
    sb_x0 = minx + dx * 0.3
    sb_y = bottom + 0.8 * margin_y

    ax.plot(
        [sb_x0, sb_x0 + scalebar_len],
        [sb_y, sb_y],
        color="black",
        linewidth=2,
    )
    ax.text(
        sb_x0 + scalebar_len / 2,
        sb_y - 0.4 * margin_y,
        f"{scalebar_km} km",
        ha="center",
        va="top",
        fontsize=10,
    )

    handles, labels = ax.get_legend_handles_labels()
    ax.legend(
        handles,
        labels,
        loc="lower right",
        frameon=True,
        fontsize=11,
    )

    plt.tight_layout()
    plt.savefig(f"{output_path}map.png", dpi=300)
    plt.close()

<<<<<<< HEAD
    # ============================
    # Plot interativo (HTML)
    # ============================
    allowed_area_latlon = allowed_area.to_crs("EPSG:4326")

    m = allowed_area_latlon.explore(
=======
    allowed_area_latlon = allowed_area.to_crs("EPSG:4326")

    map_object = allowed_area_latlon.explore(
>>>>>>> 0b6ef74 (Updated project files)
        color="white",
        edgecolor="black",
        height=600,
        name="Área permitida",
        style_kwds={"fillOpacity": 0.0},
    )
    gdf_latlon.explore(
<<<<<<< HEAD
        m=m,
=======
        m=map_object,
>>>>>>> 0b6ef74 (Updated project files)
        color="red",
        name="Pontos gerados",
        marker_kwds={"radius": 3, "fillOpacity": 0.8},
    )
<<<<<<< HEAD
    m.save(f"{output_path}map.html")

    print("✅ Mapas gerados com sucesso!")


if __name__ == "__main__":
    main()
=======
    map_object.save(f"{output_path}map.html")

    print("Mapas gerados com sucesso.")


if __name__ == "__main__":
    main()
>>>>>>> 0b6ef74 (Updated project files)
