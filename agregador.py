from pathlib import Path

import geopandas as gpd
import pandas as pd

BASE_POLIGONOS = "Distrito-SP.zip"
CSV_SINTETICO = "points-sintetico.csv"
CSV_REAL = "tweets-reais.csv"

AMOSTRA_REAIS = 10000

SAIDA_GPKG = "sp_aggregado.gpkg"
SAIDA_LAYER = "sp_counts"

COL_LAT_SYNTH = "latitude"
COL_LON_SYNTH = "longitude"

COL_LAT_REAL = "lat"
COL_LON_REAL = "lon"


def carregar_poligonos(path):
    gdf = gpd.read_file(path)
    if gdf.crs is None:
        gdf = gdf.set_crs("EPSG:31983")
        print("CRS do shapefile base não definido. Assumindo EPSG:31983.")
    print(f"Polígonos: {len(gdf)} feições, CRS = {gdf.crs}")
    return gdf


def carregar_pontos_sinteticos(path, crs_alvo):
    df = pd.read_csv(path)
    print(f"Sintéticos: {len(df)} linhas lidas")

    gdf = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df[COL_LON_SYNTH], df[COL_LAT_SYNTH]),
        crs="EPSG:4326",
    )
    return gdf.to_crs(crs_alvo)


def carregar_pontos_reais(path, crs_alvo, n_amostra=None):
    df = pd.read_csv(path)
    print(f"Reais: {len(df)} linhas lidas do CSV")

    if n_amostra is not None and n_amostra < len(df):
        df = df.sample(n=n_amostra, random_state=42)
        print(f"Amostra aleatória de {len(df)} pontos reais")

    gdf = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df[COL_LON_REAL], df[COL_LAT_REAL]),
        crs="EPSG:4326",
    )
    return gdf.to_crs(crs_alvo)


def contar_por_poligono(pontos, poligonos, label=""):
    """
    Faz spatial join e conta os pontos por índice de polígono.

    Retorna uma Series com o mesmo índice de ``poligonos``.
    """
    print(f"Join espacial para pontos {label}...")

    joined = gpd.sjoin(
        pontos,
        poligonos,
        how="inner",
        predicate="within",
    )

    counts = joined["index_right"].value_counts()
    counts = counts.reindex(poligonos.index, fill_value=0).astype(int)

    print(f"{counts.sum()} pontos {label} atribuídos a polígonos")
    return counts


def main():
    polys = carregar_poligonos(BASE_POLIGONOS)

    pts_synth = carregar_pontos_sinteticos(CSV_SINTETICO, polys.crs)
    pts_real = carregar_pontos_reais(CSV_REAL, polys.crs, AMOSTRA_REAIS)

    cnt_synth = contar_por_poligono(pts_synth, polys, label="sintéticos")
    cnt_real = contar_por_poligono(pts_real, polys, label="reais")

    polys = polys.copy()
    polys["cnt_synth"] = cnt_synth
    polys["cnt_real"] = cnt_real

    print("\nResumo das contagens por polígono:")
    print(polys[["cnt_synth", "cnt_real"]].describe())

    Path(SAIDA_GPKG).unlink(missing_ok=True)
    polys.to_file(SAIDA_GPKG, layer=SAIDA_LAYER, driver="GPKG")

    print(f"\nArquivo salvo em: {SAIDA_GPKG}, camada: {SAIDA_LAYER}")


if __name__ == "__main__":
    main()