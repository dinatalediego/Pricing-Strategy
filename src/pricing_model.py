# src/pricing_model.py
import numpy as np
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

GROUP_COLS = ["nombre_proyecto", "nombre_subdivision", "nombre_tipologia"]
UMBRAL_PCT = 0.03          # 3% tolerancia
PRICE_COL = "precio_lista" # o "precio_m2"

def run_pricing_model(clean_path: Path) -> Path:
    df = pd.read_parquet(clean_path)

    registros = []

    def analizar_grupo(g: pd.DataFrame):
        g = g.copy()
        avg_floor = (
            g.groupby("PISO")[PRICE_COL]
             .mean()
             .reset_index()
             .sort_values("PISO")
        )

        # Sin curva (un solo piso)
        if avg_floor["PISO"].nunique() < 2:
            for _, row in g.iterrows():
                registros.append({
                    **{c: row.get(c) for c in GROUP_COLS},
                    "unidad"          : row.get("nombre_unidad"),
                    "PISO"            : row["PISO"],
                    "precio_real"     : row[PRICE_COL],
                    "precio_esperado" : row[PRICE_COL],
                    "delta"           : 0.0,
                    "delta_pct"       : 0.0,
                    "estado"          : "Sin curva (solo 1 piso)",
                    "precio_sugerido" : row[PRICE_COL],
                    "recomendacion"   : (
                        "No hay suficiente data por piso; revisar manualmente."
                    ),
                })
            return

        x = avg_floor["PISO"].values
        y = avg_floor[PRICE_COL].values
        slope, intercept = np.polyfit(x, y, 1)

        for _, row in g.iterrows():
            piso = row["PISO"]
            real = row[PRICE_COL]
            esperado = slope * piso + intercept
            delta = real - esperado
            delta_pct = delta / esperado if esperado != 0 else 0.0

            if delta_pct > UMBRAL_PCT:
                estado = "Sobre la curva (caro)"
                nuevo_precio = round(esperado, -2)
                recomendacion = (
                    f"Precio sobre la curva (+{delta_pct*100:.1f}%). "
                    f"Considerar BAJAR a ~S/ {nuevo_precio:,.0f} "
                    f"(∆ S/ {delta:,.0f})."
                )
            elif delta_pct < -UMBRAL_PCT:
                estado = "Debajo de la curva (barato)"
                nuevo_precio = round(esperado, -2)
                recomendacion = (
                    f"Precio bajo la curva ({delta_pct*100:.1f}%). "
                    f"Considerar SUBIR a ~S/ {nuevo_precio:,.0f} "
                    f"(∆ S/ {abs(delta):,.0f})."
                )
            else:
                estado = "En línea con la curva"
                nuevo_precio = real
                recomendacion = "Precio alineado, mantener sin cambios."

            registros.append({
                **{c: row.get(c) for c in GROUP_COLS},
                "unidad"          : row.get("nombre_unidad"),
                "PISO"            : piso,
                "precio_real"     : real,
                "precio_esperado" : esperado,
                "delta"           : delta,
                "delta_pct"       : delta_pct * 100,
                "estado"          : estado,
                "precio_sugerido" : nuevo_precio,
                "recomendacion"   : recomendacion,
            })

    for _, g in df.groupby(GROUP_COLS, dropna=False):
        analizar_grupo(g)

    result = pd.DataFrame(registros)
    result = result.sort_values(
        by=["nombre_proyecto", "nombre_subdivision", "nombre_tipologia", "delta_pct"],
        ascending=[True, True, True, False],
    )

    out_path = ROOT / "output" / "pricing_curva_y_recomendaciones.xlsx"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    result.to_excel(out_path, index=False)
    return out_path

if __name__ == "__main__":
    clean = ROOT / "data" / "intermediate" / "unidades_clean.parquet"
    out = run_pricing_model(clean)
    print(f"Reporte pricing guardado en: {out}")
