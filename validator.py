import geopandas as gpd
import numpy as np
from esda.moran import Moran
from libpysal.weights import KNN
from scipy.stats import pearsonr

# ---------------- CONFIG ----------------
AGG_PATH = "sp_aggregado.gpkg"
AGG_LAYER = "sp_counts"

COL_REAL = "cnt_real"
COL_SYNTH = "cnt_synth"

# número de vizinhos para o KNN (orientador sugeriu K = 1)
K = 1
# ----------------------------------------


def carregar_dados() -> gpd.GeoDataFrame:
    """
    Carrega o GeoPackage agregado e garante que as colunas de contagem
    existam e estejam sem NaN.
    """
    gdf = gpd.read_file(AGG_PATH, layer=AGG_LAYER)
    print(
        f"📦 {len(gdf)} distritos carregados para validação. "
        f"CRS = {gdf.crs}"
    )

    if COL_REAL not in gdf.columns or COL_SYNTH not in gdf.columns:
        raise ValueError(
            f"Colunas {COL_REAL} e/ou {COL_SYNTH} não encontradas."
        )

    gdf = gdf.copy()
    gdf[COL_REAL] = gdf[COL_REAL].fillna(0)
    gdf[COL_SYNTH] = gdf[COL_SYNTH].fillna(0)

    return gdf


def construir_pesos(gdf: gpd.GeoDataFrame) -> KNN:
    """
    Constrói matriz de vizinhança KNN a partir dos centróides dos distritos.

    Trabalha em CRS projetado para evitar distâncias esquisitas.
    """
    if gdf.crs is None:
        gdf = gdf.set_crs("EPSG:31983")
    gdf_proj = gdf.to_crs("EPSG:31983")

    print(f"🔗 Construindo matriz de vizinhança KNN com K={K} ...")
    weights = KNN.from_dataframe(gdf_proj, k=K)
    weights.transform = "r"  # normaliza pesos por linha

    return weights


def moran_global(
    y: np.ndarray,
    weights: KNN,
    label: str = "",
) -> Moran:
    """
    Calcula e imprime o Moran global para um vetor de valores y.
    """
    y_arr = np.asarray(y, dtype=float)
    mi = Moran(y_arr, weights)

    print(f"\n📊 Moran global – {label}")
    print(f"   I observado        : {mi.I:.4f}")
    print(f"   I esperado (EI)    : {mi.EI:.4f}")
    print(f"   z (normal)         : {mi.z_norm:.4f}")
    print(f"   p-valor (normal)   : {mi.p_norm:.4e}")

    return mi


def cohen_kappa_from_labels(
    a: np.ndarray,
    b: np.ndarray,
) -> tuple[float, float, float]:
    """
    Calcula Kappa de Cohen para dois vetores de rótulos inteiros (a, b),
    ignorando NaN.

    Retorna (kappa, p_o, p_e).
    """
    a = np.asarray(a)
    b = np.asarray(b)

    # remove NaN (se houver)
    mask = ~np.isnan(a) & ~np.isnan(b)
    a = a[mask]
    b = b[mask]

    if a.size == 0:
        return np.nan, np.nan, np.nan

    # classes presentes em qualquer um dos vetores
    classes = np.unique(np.concatenate([a, b]))
    n = float(len(a))

    # matriz de confusão
    m = len(classes)
    conf = np.zeros((m, m), dtype=float)

    for i, ci in enumerate(classes):
        for j, cj in enumerate(classes):
            conf[i, j] = np.sum((a == ci) & (b == cj))

    # acordo observado
    p_o = np.trace(conf) / n

    # marginais (probabilidades de cada classe em cada mapa)
    row_marg = conf.sum(axis=1) / n
    col_marg = conf.sum(axis=0) / n
    p_e = (row_marg * col_marg).sum()

    if 1.0 - p_e == 0:
        kappa = np.nan
    else:
        kappa = (p_o - p_e) / (1.0 - p_e)

    return kappa, p_o, p_e


def main() -> None:
    """
    Roda o pipeline de validação:
      - carrega dados agregados;
      - calcula Moran global para real e sintético;
      - calcula correlação de Pearson;
      - calcula índice Kappa para mapas classificados.
    """
    gdf = carregar_dados()

    y_real = gdf[COL_REAL].values
    y_synth = gdf[COL_SYNTH].values

    print("\nResumo das contagens por distrito:")
    print(gdf[[COL_REAL, COL_SYNTH]].describe())

    weights = construir_pesos(gdf)

    # Moran global para real e sintético
    moran_global(
        y_real,
        weights,
        label="contagens reais por distrito",
    )
    moran_global(
        y_synth,
        weights,
        label="contagens sintéticas por distrito",
    )

    # Correlação de Pearson entre os vetores
    r, p_val = pearsonr(y_real, y_synth)
    print(
        "\n🔗 Correlação de Pearson entre contagens "
        "real e sintética por distrito"
    )
    print(f"   r        : {r:.4f}")
    print(f"   p-valor  : {p_val:.4e}")

    # =========================================
    # 🔹 Índice Kappa entre mapas classificados
    # =========================================
    real = gdf[COL_REAL].to_numpy(dtype=float)
    synth = gdf[COL_SYNTH].to_numpy(dtype=float)

    # Considera apenas distritos com pelo menos 1 tweet real
    mask_pos = real > 0
    if mask_pos.sum() >= 2:
        # quantis dos distritos "ativos"
        qs = np.quantile(real[mask_pos], [0.2, 0.4, 0.6, 0.8])

        # monta bins: [0, q20, q40, q60, q80, max]
        bins = np.concatenate(([0.0], qs, [real.max()]))

        # garante que os limites sejam estritamente crescentes
        bins = np.unique(bins)
        if bins.size < 3:
            print(
                "\n⚠️  Variabilidade insuficiente para "
                "classes de Kappa."
            )
        else:
            # classes 1..K usando os MESMOS bins para real e sintético
            real_cls = np.digitize(real, bins, right=True)
            synth_cls = np.digitize(synth, bins, right=True)

            kappa, p_o, p_e = cohen_kappa_from_labels(
                real_cls,
                synth_cls,
            )

            print("\n🧮 Índice Kappa (classes de contagem por distrito)")
            print(f"   κ (Kappa)        : {kappa: .4f}")
            print(f"   P(o) acordo obs. : {p_o: .4f}")
            print(f"   P(e) acaso       : {p_e: .4f}")
    else:
        print(
            "\n⚠️  Poucos distritos com tweets reais > 0; "
            "Kappa não calculado."
        )


if __name__ == "__main__":
    main()
