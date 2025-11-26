# src/reporting_econometrico.py

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def build_plots(panel_elast: pd.DataFrame):
    out_dir = ROOT / "output" / "plots_econometricos"
    out_dir.mkdir(parents=True, exist_ok=True)

    for (proj, tipo), g in panel_elast.groupby(["nombre_proyecto","nombre_tipologia"]):
        plt.figure(figsize=(7,5))
        sns.scatterplot(x="precio_lista", y="separaciones", data=g)
        sns.regplot(x="precio_lista", y="separaciones", data=g, scatter=False, color="red")
        plt.title(f"Demanda vs Precio – {proj} / {tipo}")
        plt.savefig(out_dir / f"demand_curve_{proj}_{tipo}.png", dpi=200)
        plt.close()

    # Elasticidad por proyecto / tipología
    plt.figure(figsize=(10,6))
    sns.boxplot(x="nombre_proyecto", y="elasticidad", data=panel_elast)
    plt.xticks(rotation=45)
    plt.title("Distribución de Elasticidad Precio-Demanda")
    plt.savefig(out_dir / "elasticidad_boxplot.png", dpi=200)
    plt.close()

    return out_dir
