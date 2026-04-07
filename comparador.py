import geopandas as gpd
import matplotlib.pyplot as plt

AGG_PATH = "sp_aggregado.gpkg"
AGG_LAYER = "sp_counts"

COL_REAL = "cnt_real"
COL_SYNTH = "cnt_synth"

SAIDA_PNG = "comparacao_distritos.png"


def preparar_metricas(gdf):
    """
    Usa contagens por distrito como métrica.

    Caso futuramente exista população por distrito, esta função pode ser
    adaptada para trabalhar com taxas.
    """
    if COL_REAL not in gdf.columns or COL_SYNTH not in gdf.columns:
        raise ValueError(
            f"Colunas {COL_REAL} e/ou {COL_SYNTH} não encontradas no GPKG."
        )

    gdf = gdf.copy()
    gdf["metric_real"] = gdf[COL_REAL].fillna(0)
    gdf["metric_synth"] = gdf[COL_SYNTH].fillna(0)

    print("Estatísticas por distrito (contagens):")
    print(gdf[["metric_real", "metric_synth"]].describe())

    return gdf


def plot_comparacao(gdf, saida_png):
    """
    Plota dois mapas lado a lado:
    - esquerda: contagem real por distrito
    - direita: contagem sintética por distrito

    Usa quantis separados para cada mapa.
    """
    if gdf.crs is None:
        gdf = gdf.set_crs("EPSG:31983")
    gdf_plot = gdf.to_crs("EPSG:31983")

    fig, axes = plt.subplots(1, 2, figsize=(12, 8))

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
    axes[1].set_title(
        "Distribuição sintética de pontos por distrito",
        fontsize=12,
    )
    axes[1].axis("off")

    plt.tight_layout()
    plt.savefig(saida_png, dpi=300)
    plt.close()

    print(f"Figura salva em: {saida_png}")


def main():
    print(f"Lendo agregados de: {AGG_PATH} (camada: {AGG_LAYER})")
    gdf = gpd.read_file(AGG_PATH, layer=AGG_LAYER)
    print(f"{len(gdf)} distritos carregados. CRS = {gdf.crs}")

    gdf = preparar_metricas(gdf)
    plot_comparacao(gdf, SAIDA_PNG)


if __name__ == "__main__":
    main()