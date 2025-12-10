import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np

# ---------------- CONFIG ----------------
agg_path = "sp_aggregado.gpkg"
agg_layer = "sp_counts"

# Nome das colunas de contagem
COL_REAL = "cnt_real"
COL_SYNTH = "cnt_synth"

# Arquivo de saída da figura
saida_png = "comparacao_distritos.png"
# ----------------------------------------


def preparar_metricas(gdf):
    """
    Usa contagens por distrito como métrica.
    Se em algum momento você tiver população por distrito, dá pra trocar aqui
    para taxa, mas por ora trabalhamos com cnt_real / cnt_synth.
    """
    if COL_REAL not in gdf.columns or COL_SYNTH not in gdf.columns:
        raise ValueError(f"Colunas {COL_REAL} e/ou {COL_SYNTH} não encontradas no GPKG.")

    gdf = gdf.copy()
    gdf["metric_real"] = gdf[COL_REAL].fillna(0)
    gdf["metric_synth"] = gdf[COL_SYNTH].fillna(0)

    print("📊 Estatísticas por distrito (contagens):")
    print(gdf[["metric_real", "metric_synth"]].describe())

    return gdf


def plot_comparacao(gdf, saida_png):
    """
    Plota dois mapas lado a lado:
      - esquerda: contagem real por distrito
      - direita: contagem sintética por distrito

    Usa quantis separados para cada mapa (escala relativa independente).
    """
    # Garante algum CRS projetado para plot (opcional, só pra deixar mais bonitinho)
    if gdf.crs is None:
        gdf = gdf.set_crs("EPSG:31983")
    gdf_plot = gdf.to_crs("EPSG:31983")

    fig, axes = plt.subplots(1, 2, figsize=(12, 8))

    # --- Mapa real ---
    gdf_plot.plot(
        column="metric_real",
        scheme="Quantiles",
        k=5,
        cmap="Reds",
        linewidth=0.3,
        edgecolor="black",
        legend=True,
        ax=axes[0],
    )
    axes[0].set_title("Distribuição real de tweets por distrito", fontsize=12)
    axes[0].axis("off")

    # --- Mapa sintético ---
    gdf_plot.plot(
        column="metric_synth",
        scheme="Quantiles",
        k=5,
        cmap="Reds",
        linewidth=0.3,
        edgecolor="black",
        legend=True,
        ax=axes[1],
    )
    axes[1].set_title("Distribuição sintética de pontos por distrito", fontsize=12)
    axes[1].axis("off")

    plt.tight_layout()
    plt.savefig(saida_png, dpi=300)
    plt.close()
    print(f"✅ Figura salva em: {saida_png}")


def main():
    print(f"📂 Lendo agregados de: {agg_path} (camada: {agg_layer})")
    gdf = gpd.read_file(agg_path, layer=agg_layer)
    print(f"📦 {len(gdf)} distritos carregados. CRS = {gdf.crs}")

    gdf = preparar_metricas(gdf)
    plot_comparacao(gdf, saida_png)


if __name__ == "__main__":
    main()
