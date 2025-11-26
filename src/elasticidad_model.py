# src/elasticidad_model.py
import pandas as pd
import numpy as np
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def run_elasticidad(df_unidades: pd.DataFrame, df_sep: pd.DataFrame) -> pd.DataFrame:
    """
    df_unidades: precios por unidad / tipología / mes
    df_sep: separaciones por tipología / mes
    """

    # 1) Aggregar por mes + tipología + proyecto
    precios = (
        df_unidades
        .groupby(["nombre_proyecto","nombre_tipologia","mes"])
        ["precio_lista"]
        .mean()
        .reset_index()
    )

    qty = (
        df_sep
        .groupby(["nombre_proyecto","nombre_tipologia","mes"])
        ["separaciones"]
        .sum()
        .reset_index()
    )

    panel = precios.merge(qty, on=["nombre_proyecto","nombre_tipologia","mes"])

    # Cambios % mes a mes
    panel["pct_delta_p"] = panel.groupby(["nombre_proyecto","nombre_tipologia"])["precio_lista"].pct_change()
    panel["pct_delta_q"] = panel.groupby(["nombre_proyecto","nombre_tipologia"])["separaciones"].pct_change()

    # Elasticidad
    panel["elasticidad"] = panel["pct_delta_q"] / panel["pct_delta_p"]

    return panel
