# src/forecast_model.py
import pandas as pd
from prophet import Prophet
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def run_forecast(df_sep: pd.DataFrame, proyecto: str, tipo: str):
    g = df_sep[(df_sep["nombre_proyecto"]==proyecto) &
               (df_sep["nombre_tipologia"]==tipo)]

    df = g[["fecha","separaciones"]].rename(columns={"fecha":"ds","separaciones":"y"})
    
    model = Prophet()
    model.fit(df)

    future = model.make_future_dataframe(periods=90)
    forecast = model.predict(future)

    out = ROOT / "output" / f"forecast_{proyecto}_{tipo}.xlsx"
    forecast.to_excel(out, index=False)
    return out
