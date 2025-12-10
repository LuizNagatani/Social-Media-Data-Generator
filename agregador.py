import pandas as pd
import geopandas as gpd
from pathlib import Path

# ---------------- CONFIGURAÇÃO ----------------
# arquivos de entrada
base_poligonos = "Distrito-SP.zip"     # distritos / setores / células
csv_sintetico = "points-sintetico.csv"  # saída do gerador
csv_real = "tweets-reais.csv"           # dados reais

# número de pontos reais que você quer amostrar (None = usa todos)
amostra_reais = 10000

# nome do arquivo de saída (GeoPackage é prático)
saida_gpkg = "sp_aggregado.gpkg"
saida_layer = "sp_counts"

# colunas de coordenadas
col_lat_synth = "latitude"
col_lon_synth = "longitude"

col_lat_real = "lat"
col_lon_real = "lon"
# ------------------------------------------------


def carregar_poligonos(path):
    gdf = gpd.read_file(path)
    if gdf.crs is None:
        # distritos do GeoSampa normalmente vêm em SIRGAS 2000 / UTM 23S (EPSG:31983)
        # se for outro caso depois a gente ajusta, mas mantemos essa hipótese por padrão
        gdf = gdf.set_crs("EPSG:31983")
        print(f"⚠️  CRS do shapefile base não definido. Assumindo EPSG:31983.")
    print(f"📦 Polígonos: {len(gdf)} feições, CRS = {gdf.crs}")
    return gdf


def carregar_pontos_sinteticos(path, crs_alvo):
    df = pd.read_csv(path)
    print(f"📊 Sintéticos: {len(df)} linhas lidas")

    # pontos do gerador vêm em WGS84 (lat/lon)
    gdf = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df[col_lon_synth], df[col_lat_synth]),
        crs="EPSG:4326",
    )
    gdf = gdf.to_crs(crs_alvo)
    return gdf


def carregar_pontos_reais(path, crs_alvo, n_amostra=None):
    df = pd.read_csv(path)
    print(f"📊 Reais: {len(df)} linhas lidas do CSV")

    if n_amostra is not None and n_amostra < len(df):
        df = df.sample(n=n_amostra, random_state=42)
        print(f"   → Amostra aleatória de {len(df)} pontos reais")

    gdf = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df[col_lon_real], df[col_lat_real]),
        crs="EPSG:4326",
    )
    gdf = gdf.to_crs(crs_alvo)
    return gdf


def contar_por_poligono(pontos, poligonos, label=""):
    """
    Faz spatial join (pontos dentro de polígono) e conta por índice de polígono.
    Retorna uma Series com o mesmo índice de 'poligonos'.
    """
    print(f"🔄 Join espacial para pontos {label}...")

    joined = gpd.sjoin(
        pontos,
        poligonos,
        how="inner",     # só pontos que caem em algum polígono
        predicate="within",
    )

    # índice dos polígonos vem em 'index_right'
    counts = joined["index_right"].value_counts()

    # Reindexa pra garantir alinhamento com poligonos.index
    counts = counts.reindex(poligonos.index, fill_value=0).astype(int)

    print(f"   → {counts.sum()} pontos {label} atribuídos a polígonos")
    return counts


def main():
    # 1. Polígonos base (distritos)
    polys = carregar_poligonos(base_poligonos)

    # 2. Pontos sintéticos
    pts_synth = carregar_pontos_sinteticos(csv_sintetico, polys.crs)

    # 3. Pontos reais (com amostragem, se configurado)
    pts_real = carregar_pontos_reais(csv_real, polys.crs, amostra_reais)

    # 4. Contagens por polígono
    cnt_synth = contar_por_poligono(pts_synth, polys, label="sintéticos")
    cnt_real = contar_por_poligono(pts_real, polys, label="reais")

    # 5. Anexa as contagens ao GeoDataFrame
    polys = polys.copy()
    polys["cnt_synth"] = cnt_synth
    polys["cnt_real"] = cnt_real

    print("\nResumo rápido das contagens por polígono:")
    print(polys[["cnt_synth", "cnt_real"]].describe())

    # 6. Salva em GeoPackage (um arquivo só, bom pra QGIS e pro comparador/validator)
    Path(saida_gpkg).unlink(missing_ok=True)  # se já existir, apaga

    polys.to_file(saida_gpkg, layer=saida_layer, driver="GPKG")
    print(f"\n✅ Arquivo salvo em: {saida_gpkg}, camada: {saida_layer}")


if __name__ == "__main__":
    main()
