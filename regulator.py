<<<<<<< HEAD
#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Módulo de regulação de probabilidades para o gerador sintético."""

import argparse
import os
import shutil
import warnings

import geopandas as gpd
import numpy as np
import pandas as pd

# Nomes de colunas conforme descrito
DENSITY_COL = "dd_hab_hec"  # densidade (habitantes por hectare)
IPVS_COL = "cd_indice_"  # índice IPVS (0–6)
POP_COL = "qt_habitan"  # população do setor

# SIRGAS 2000 / UTM 23S (São Paulo costuma usar)
DEFAULT_WORKING_EPSG = "EPSG:31983"


def build_parser() -> argparse.ArgumentParser:
    """
    Constrói o parser de linha de comando.

    Returns
    -------
    argparse.ArgumentParser
        Parser configurado para o script.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Combina shapefile de densidade e shapefile de IPVS, "
            "calcula pesos normalizados e salva um novo shapefile "
            "com coluna 'prob'."
        )
    )
    parser.add_argument(
        "dens_zip",
        help=(
            "Shapefile (ZIP) base de densidade "
            f"(contendo coluna {DENSITY_COL})"
        ),
    )
    parser.add_argument(
        "ipvs_zip",
        help=(
            "Shapefile (ZIP) de IPVS "
            f"com {IPVS_COL} e {POP_COL}"
        ),
    )
    parser.add_argument(
        "--lambda-dens",
        type=float,
        default=0.5,
        help=(
            "Peso da densidade no fator multiplicativo (λ). "
            "Default: 0.5"
        ),
    )
    parser.add_argument(
        "--mu-ipvs",
        type=float,
        default=0.5,
        help=(
            "Peso da vulnerabilidade (já invertida, ipvs_good_norm) "
            "no fator multiplicativo (μ). Default: 0.5"
        ),
    )
    parser.add_argument(
        "--out-prefix",
        default="SP_regulated",
        help="Prefixo da pasta/arquivo de saída. Default: SP_regulated",
    )
    parser.add_argument(
        "--no-zip",
        action="store_true",
        help="Se informado, não cria o .zip, apenas a pasta com o shapefile",
    )
    return parser


def clip_minmax(series: pd.Series, qmin: float = 0.05, qmax: float = 0.95) -> pd.Series:
    """
    Corta cauda de outliers pelos quantis e retorna a série clipada.

    Parameters
    ----------
    series : pandas.Series
        Série numérica a ser tratada.
    qmin : float
        Quantil mínimo para o corte.
    qmax : float
        Quantil máximo para o corte.

    Returns
    -------
    pandas.Series
        Série com valores limitados pelos quantis.
    """
    q_low, q_high = series.quantile([qmin, qmax])
    return series.clip(q_low, q_high)


def main() -> None:
    """Ponto de entrada principal do script."""
    warnings.filterwarnings("ignore", category=UserWarning)

    parser = build_parser()
    args = parser.parse_args()

    # -----------------------------
    # 1) Leitura dos shapefiles
    # -----------------------------
    print("🔹 Lendo shapefile de densidade:", args.dens_zip)
    dens = gpd.read_file(args.dens_zip)

    if dens.crs is None:
        print(
            "⚠️  CRS do shapefile de densidade não definido. "
            f"Definindo como {DEFAULT_WORKING_EPSG} por hipótese."
        )
        dens.set_crs(DEFAULT_WORKING_EPSG, inplace=True)

    print("🔹 Lendo shapefile de IPVS:", args.ipvs_zip)
    ipvs = gpd.read_file(args.ipvs_zip)

    if ipvs.crs is None:
        print(
            "⚠️  CRS do shapefile de IPVS não definido. "
            f"Assumindo {DEFAULT_WORKING_EPSG} e reprojetando para "
            "o mesmo do shapefile de densidade."
        )
        ipvs.set_crs(DEFAULT_WORKING_EPSG, inplace=True)

    # Reprojeta IPVS para o CRS da densidade
    ipvs = ipvs.to_crs(dens.crs)

    if DENSITY_COL not in dens.columns:
        raise ValueError(
            f"Coluna '{DENSITY_COL}' não encontrada no shapefile de densidade."
        )
    if IPVS_COL not in ipvs.columns:
        raise ValueError(
            f"Coluna '{IPVS_COL}' não encontrada no shapefile de IPVS."
        )
    if POP_COL not in ipvs.columns:
        raise ValueError(
            f"Coluna '{POP_COL}' não encontrada no shapefile de IPVS."
        )

    # -----------------------------
    # 2) Join espacial: densidade -> IPVS
    # -----------------------------
    print("🔄 Fazendo join espacial (dd_hab_hec → malha IPVS)...")
    dens_for_join = dens[[DENSITY_COL, "geometry"]].copy()

    joined = gpd.sjoin(
        ipvs,
        dens_for_join,
        how="left",
        predicate="intersects",
    )

    # Mantém geometria do IPVS
    gdf = joined.drop(
        columns=[
            c for c in joined.columns
            if c.endswith("_right")
        ],
        errors="ignore",
    )
    if "index_right" in gdf.columns:
        gdf = gdf.drop(columns=["index_right"])

    # -----------------------------
    # 3) Normalização de densidade
    # -----------------------------
    print("📐 Normalizando densidade (dd_hab_hec)...")
    dens_raw = gdf[DENSITY_COL].astype(float)

    # log para reduzir assimetria
    dens_log = np.log1p(dens_raw.replace({np.inf: np.nan}))

    # máscara de valores válidos
    valid = dens_log.notna()
    if not valid.any():
        raise ValueError(
            "Não há valores válidos em dd_hab_hec para normalização."
        )

    # corta outliers (5%-95%) apenas nos válidos
    q_low, q_high = dens_log[valid].quantile([0.05, 0.95])
    dens_clip = dens_log.clip(q_low, q_high)

    # min–max usando apenas válidos
    dens_min = dens_clip[valid].min()
    dens_max = dens_clip[valid].max()
    if dens_max == dens_min:
        dens_norm = pd.Series(0.5, index=dens_clip.index)
    else:
        dens_norm = (dens_clip - dens_min) / (dens_max - dens_min)

    dens_norm = dens_norm.fillna(dens_norm.mean())
    gdf["dens_norm"] = dens_norm

    # -----------------------------
    # 4) Normalização de IPVS
    #     (menos vulnerável = maior valor)
    # -----------------------------
    print("📐 Normalizando IPVS (cd_indice_)...")
    ipvs_raw = gdf[IPVS_COL].astype(float)

    # 0 = sem classificação -> tratamos como NaN
    ipvs_raw = ipvs_raw.replace(0, np.nan)

    # vulnerabilidade 1–6 -> [0,1] (1 = 0, 6 = 1)
    ipvs_vuln_norm = (ipvs_raw - 1.0) / (6.0 - 1.0)

    # inverte: agora 1 = menos vulnerável, 0 = mais vulnerável
    ipvs_good_norm = 1.0 - ipvs_vuln_norm

    # preenche NaN com média (neutro)
    mean_good = ipvs_good_norm.mean()
    ipvs_good_norm = ipvs_good_norm.fillna(mean_good)

    gdf["ipvs_good_norm"] = ipvs_good_norm

    # -----------------------------
    # 5) Fatores multiplicativos
    # -----------------------------
    lambda_d = args.lambda_dens
    mu_v = args.mu_ipvs

    print(
        "⚖️  Construindo fatores multiplicativos com "
        f"λ={lambda_d:.2f} (densidade) e "
        "μ={mu:.2f} (IPVS invertido: maior = menos vulnerável)...".format(
            mu=mu_v
        )
    )

    dens_n = gdf["dens_norm"].fillna(gdf["dens_norm"].mean())
    ipvs_n = gdf["ipvs_good_norm"].fillna(
        gdf["ipvs_good_norm"].mean()
    )

    f_dens = 1.0 + lambda_d * (dens_n - dens_n.mean())
    f_ipvs = 1.0 + mu_v * (ipvs_n - ipvs_n.mean())

    eps = 1e-3
    f_dens = f_dens.clip(lower=eps)
    f_ipvs = f_ipvs.clip(lower=eps)

    gdf["f_dens"] = f_dens
    gdf["f_ipvs"] = f_ipvs

    # -----------------------------
    # 6) População efetiva e probabilidade
    # -----------------------------
    print("👥 Calculando população efetiva e probabilidade final (prob)...")
    pop_raw = gdf[POP_COL].astype(float).fillna(0.0)

    pop_eff = pop_raw * f_dens * f_ipvs
    gdf["pop_eff"] = pop_eff

    total_eff = pop_eff.sum()
    if total_eff <= 0:
        raise ValueError(
            "População efetiva total é zero ou negativa. "
            "Verifique os dados de entrada."
        )

    gdf["prob"] = pop_eff / total_eff

    # -----------------------------
    # 7) Salvar shapefile
    # -----------------------------
    out_dir = args.out_prefix
    if os.path.exists(out_dir):
        print(
            f"⚠️  Pasta de saída '{out_dir}' já existe. "
            "Apagando para recriar..."
        )
        shutil.rmtree(out_dir)

    os.makedirs(out_dir, exist_ok=True)

    out_path_shp = os.path.join(out_dir, f"{args.out_prefix}.shp")
    print("💾 Salvando shapefile regulado com pesos em:", out_path_shp)
    gdf.to_file(out_path_shp, driver="ESRI Shapefile")

    if not args.no_zip:
        zip_name = args.out_prefix + ".zip"
        print("📦 Compactando shapefile em:", zip_name)
        shutil.make_archive(args.out_prefix, "zip", out_dir)
        print("✅ Arquivo ZIP criado com sucesso.")

    print("✨ Pronto! Shapefile final contém, entre outras, as colunas:")
    print(f"   - {DENSITY_COL} (densidade original)")
    print(f"   - {IPVS_COL} (IPVS original)")
    print(f"   - {POP_COL} (população original)")
    print("   - dens_norm        (densidade normalizada)")
    print("   - ipvs_good_norm   (IPVS normalizado, 1 = menos vulnerável)")
    print("   - f_dens, f_ipvs   (fatores multiplicativos)")
    print("   - pop_eff          (população efetiva)")
    print("   - prob             (peso final para geração de pontos)")


if __name__ == "__main__":
    main()
=======
#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Módulo de regulação de probabilidades para o gerador sintético."""

import argparse
import os
import shutil
import warnings

import geopandas as gpd
import numpy as np
import pandas as pd

DENSITY_COL = "dd_hab_hec"
IPVS_COL = "cd_indice_"
POP_COL = "qt_habitan"

DEFAULT_WORKING_EPSG = "EPSG:31983"


def build_parser() -> argparse.ArgumentParser:
    """
    Constrói o parser de linha de comando.

    Returns
    -------
    argparse.ArgumentParser
        Parser configurado para o script.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Combina shapefile de densidade e shapefile de IPVS, "
            "calcula pesos normalizados e salva um novo shapefile "
            "com coluna 'prob'."
        )
    )
    parser.add_argument(
        "dens_zip",
        help=(
            "Shapefile (ZIP) base de densidade "
            f"(contendo coluna {DENSITY_COL})"
        ),
    )
    parser.add_argument(
        "ipvs_zip",
        help=f"Shapefile (ZIP) de IPVS com {IPVS_COL} e {POP_COL}",
    )
    parser.add_argument(
        "--lambda-dens",
        type=float,
        default=0.5,
        help=(
            "Peso da densidade no fator multiplicativo (λ). "
            "Default: 0.5"
        ),
    )
    parser.add_argument(
        "--mu-ipvs",
        type=float,
        default=0.5,
        help=(
            "Peso da vulnerabilidade (ja invertida, ipvs_good_norm) "
            "no fator multiplicativo (μ). Default: 0.5"
        ),
    )
    parser.add_argument(
        "--out-prefix",
        default="SP_regulated",
        help="Prefixo da pasta/arquivo de saída. Default: SP_regulated",
    )
    parser.add_argument(
        "--no-zip",
        action="store_true",
        help="Se informado, não cria o .zip, apenas a pasta com o shapefile",
    )
    return parser


def clip_minmax(
    series: pd.Series,
    qmin: float = 0.05,
    qmax: float = 0.95,
) -> pd.Series:
    """
    Corta a cauda de outliers pelos quantis e retorna a série clipada.
    """
    q_low, q_high = series.quantile([qmin, qmax])
    return series.clip(q_low, q_high)


def main() -> None:
    """Ponto de entrada principal do script."""
    warnings.filterwarnings("ignore", category=UserWarning)

    parser = build_parser()
    args = parser.parse_args()

    print("Lendo shapefile de densidade:", args.dens_zip)
    dens = gpd.read_file(args.dens_zip)

    if dens.crs is None:
        print(
            "CRS do shapefile de densidade não definido. "
            f"Definindo como {DEFAULT_WORKING_EPSG} por hipótese."
        )
        dens.set_crs(DEFAULT_WORKING_EPSG, inplace=True)

    print("Lendo shapefile de IPVS:", args.ipvs_zip)
    ipvs = gpd.read_file(args.ipvs_zip)

    if ipvs.crs is None:
        print(
            "CRS do shapefile de IPVS não definido. "
            f"Assumindo {DEFAULT_WORKING_EPSG} e reprojetando para "
            "o mesmo do shapefile de densidade."
        )
        ipvs.set_crs(DEFAULT_WORKING_EPSG, inplace=True)

    ipvs = ipvs.to_crs(dens.crs)

    if DENSITY_COL not in dens.columns:
        raise ValueError(
            f"Coluna '{DENSITY_COL}' não encontrada no shapefile de densidade."
        )
    if IPVS_COL not in ipvs.columns:
        raise ValueError(
            f"Coluna '{IPVS_COL}' não encontrada no shapefile de IPVS."
        )
    if POP_COL not in ipvs.columns:
        raise ValueError(
            f"Coluna '{POP_COL}' não encontrada no shapefile de IPVS."
        )

    print("Fazendo join espacial (dd_hab_hec -> malha IPVS)...")
    dens_for_join = dens[[DENSITY_COL, "geometry"]].copy()

    joined = gpd.sjoin(
        ipvs,
        dens_for_join,
        how="left",
        predicate="intersects",
    )

    gdf = joined.drop(
        columns=[col for col in joined.columns if col.endswith("_right")],
        errors="ignore",
    )
    if "index_right" in gdf.columns:
        gdf = gdf.drop(columns=["index_right"])

    print("Normalizando densidade (dd_hab_hec)...")
    dens_raw = gdf[DENSITY_COL].astype(float)
    dens_log = np.log1p(dens_raw.replace({np.inf: np.nan}))

    valid = dens_log.notna()
    if not valid.any():
        raise ValueError(
            "Não há valores válidos em dd_hab_hec para normalização."
        )

    q_low, q_high = dens_log[valid].quantile([0.05, 0.95])
    dens_clip = dens_log.clip(q_low, q_high)

    dens_min = dens_clip[valid].min()
    dens_max = dens_clip[valid].max()
    if dens_max == dens_min:
        dens_norm = pd.Series(0.5, index=dens_clip.index)
    else:
        dens_norm = (dens_clip - dens_min) / (dens_max - dens_min)

    dens_norm = dens_norm.fillna(dens_norm.mean())
    gdf["dens_norm"] = dens_norm

    print("Normalizando IPVS (cd_indice_)...")
    ipvs_raw = gdf[IPVS_COL].astype(float)
    ipvs_raw = ipvs_raw.replace(0, np.nan)

    ipvs_vuln_norm = (ipvs_raw - 1.0) / (6.0 - 1.0)
    ipvs_good_norm = 1.0 - ipvs_vuln_norm

    mean_good = ipvs_good_norm.mean()
    ipvs_good_norm = ipvs_good_norm.fillna(mean_good)

    gdf["ipvs_good_norm"] = ipvs_good_norm

    lambda_d = args.lambda_dens
    mu_v = args.mu_ipvs

    print(
        "Construindo fatores multiplicativos com "
        f"λ={lambda_d:.2f} (densidade) e "
        f"μ={mu_v:.2f} (IPVS invertido: maior = menos vulnerável)..."
    )

    dens_n = gdf["dens_norm"].fillna(gdf["dens_norm"].mean())
    ipvs_n = gdf["ipvs_good_norm"].fillna(gdf["ipvs_good_norm"].mean())

    f_dens = 1.0 + lambda_d * (dens_n - dens_n.mean())
    f_ipvs = 1.0 + mu_v * (ipvs_n - ipvs_n.mean())

    eps = 1e-3
    f_dens = f_dens.clip(lower=eps)
    f_ipvs = f_ipvs.clip(lower=eps)

    gdf["f_dens"] = f_dens
    gdf["f_ipvs"] = f_ipvs

    print("Calculando população efetiva e probabilidade final (prob)...")
    pop_raw = gdf[POP_COL].astype(float).fillna(0.0)

    pop_eff = pop_raw * f_dens * f_ipvs
    gdf["pop_eff"] = pop_eff

    total_eff = pop_eff.sum()
    if total_eff <= 0:
        raise ValueError(
            "População efetiva total é zero ou negativa. "
            "Verifique os dados de entrada."
        )

    gdf["prob"] = pop_eff / total_eff

    out_dir = args.out_prefix
    if os.path.exists(out_dir):
        print(
            f"Pasta de saída '{out_dir}' já existe. "
            "Apagando para recriar..."
        )
        shutil.rmtree(out_dir)

    os.makedirs(out_dir, exist_ok=True)

    out_path_shp = os.path.join(out_dir, f"{args.out_prefix}.shp")
    print("Salvando shapefile regulado com pesos em:", out_path_shp)
    gdf.to_file(out_path_shp, driver="ESRI Shapefile")

    if not args.no_zip:
        zip_name = args.out_prefix + ".zip"
        print("Compactando shapefile em:", zip_name)
        shutil.make_archive(args.out_prefix, "zip", out_dir)
        print("Arquivo ZIP criado com sucesso.")

    print("Shapefile final contém, entre outras, as colunas:")
    print(f"   - {DENSITY_COL} (densidade original)")
    print(f"   - {IPVS_COL} (IPVS original)")
    print(f"   - {POP_COL} (população original)")
    print("   - dens_norm        (densidade normalizada)")
    print("   - ipvs_good_norm   (IPVS normalizado, 1 = menos vulnerável)")
    print("   - f_dens, f_ipvs   (fatores multiplicativos)")
    print("   - pop_eff          (população efetiva)")
    print("   - prob             (peso final para geração de pontos)")


if __name__ == "__main__":
    main()
>>>>>>> 0b6ef74 (Updated project files)
