# src/etl_unidades.py
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def run_etl_unidades() -> Path:
    raw_path = ROOT / "data" / "Unidades.csv"
    out_path = ROOT / "data" / "intermediate" / "unidades_clean.parquet"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(raw_path)

    # Ajusta estos nombres a tus columnas reales
    rename_map = {
        "nombre": "nombre_unidad",
        "proyecto": "nombre_proyecto",
        "torre": "nombre_subdivision",
        "tipologia": "nombre_tipologia",
        "PISO": "PISO",
        "precio_lista": "precio_lista",
        "area_total": "area_total",
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

    # Filtros básicos
    df = df.dropna(subset=["PISO", "precio_lista"])
    df["PISO"] = df["PISO"].astype(int)
    df["precio_lista"] = df["precio_lista"].astype(float)

    if "area_total" in df.columns:
        df["precio_m2"] = df["precio_lista"] / df["area_total"]

    df.to_parquet(out_path, index=False)
    return out_path

if __name__ == "__main__":
    p = run_etl_unidades()
    print(f"Unidades limpias guardadas en: {p}")
