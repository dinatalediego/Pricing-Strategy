# src/pipeline_elasticidad.py
from pathlib import Path
import pandas as pd

from elasticidad_model import run_elasticidad

ROOT = Path(__file__).resolve().parents[1]

def main() -> None:
    print(">>> [PIPELINE ELASTICIDAD] Cargando unidades limpias...")
    clean_unidades = ROOT / "data" / "intermediate" / "unidades_clean.parquet"
    df_unidades = pd.read_parquet(clean_unidades)

    print(">>> [PIPELINE ELASTICIDAD] Cargando separaciones mensuales...")
    sep_path = ROOT / "data" / "separaciones_mensual.csv"
    df_sep = pd.read_csv(sep_path)

    # Asegura columna mes en formato fecha (si viene como texto tipo '2025-10')
    if "mes" in df_sep.columns:
        df_sep["mes"] = pd.to_datetime(df_sep["mes"])

    print(">>> [PIPELINE ELASTICIDAD] Calculando elasticidad precio–cantidad...")
    panel = run_elasticidad(df_unidades, df_sep)

    out_path = ROOT / "output" / "elasticidad_panel.xlsx"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    panel.to_excel(out_path, index=False)

    print(f">>> [PIPELINE ELASTICIDAD] Panel guardado en: {out_path}")

if __name__ == "__main__":
    main()
