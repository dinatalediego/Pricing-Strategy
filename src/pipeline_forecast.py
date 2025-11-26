# src/pipeline_forecast.py
from pathlib import Path
import pandas as pd

from forecast_model import run_forecast

ROOT = Path(__file__).resolve().parents[1]

def main() -> None:
    print(">>> [PIPELINE FORECAST] Cargando separaciones históricas...")
    sep_path = ROOT / "data" / "separaciones_mensual.csv"
    df_sep = pd.read_csv(sep_path)
    df_sep["fecha"] = pd.to_datetime(df_sep["fecha"])

    # Recorrer combos proyecto–tipología
    combos = (
        df_sep[["nombre_proyecto", "nombre_tipologia"]]
        .drop_duplicates()
        .itertuples(index=False)
    )

    for combo in combos:
        proyecto, tipo = combo
        print(f">>> [PIPELINE FORECAST] Forecast para {proyecto} / {tipo} ...")
        try:
            out = run_forecast(df_sep, proyecto, tipo)
            print(f"    Archivo: {out}")
        except Exception as e:
            print(f"    ⚠ Error con {proyecto} / {tipo}: {e}")

if __name__ == "__main__":
    main()
