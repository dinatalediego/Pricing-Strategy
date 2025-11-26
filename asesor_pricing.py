import pandas as pd
import numpy as np

# 1) Cargar base
df = pd.read_csv(r"../data/Unidades.csv")   # <- cambia la ruta

# 2) Limpieza básica (ajusta nombres de columnas si difieren)
df = df.dropna(subset=['PISO', 'precio_lista'])
df['PISO'] = df['PISO'].astype(int)
df['precio_lista'] = df['precio_lista'].astype(float)

# (Opcional) si quieres trabajar por m2, descomenta:
# df['precio_m2'] = df['precio_lista'] / df['area_total']

# 3) Definir cómo agrupas la curva lógica de precios
group_cols = ['nombre_proyecto', 'nombre_subdivision', 'nombre_tipologia']
# Si no tienes nombre_tipologia, puedes usar dormitorios/orientación, etc.

# 4) Parámetros de negocio
UMBRAL_PCT = 0.03   # 3% de tolerancia; cámbialo a 0.02 (2%) o lo que quieras
COLUMNA_PRECIO = 'precio_lista'   # o 'precio_m2' si prefieres

registros = []

def analizar_grupo(g):
    g = g.copy()
    # ---- 4.1 Construir la curva esperada: promedio por piso y regresión lineal ----
    avg_floor = (
        g.groupby('PISO')[COLUMNA_PRECIO]
        .mean()
        .reset_index()
        .sort_values('PISO')
    )

    if avg_floor['PISO'].nunique() < 2:
        # con un solo piso no hay curva, devolvemos sin comentarios fuertes
        for _, row in g.iterrows():
            registros.append({
                **{col: row[col] for col in group_cols},
                'unidad'         : row.get('nombre', np.nan),
                'PISO'           : row['PISO'],
                'precio_real'    : row[COLUMNA_PRECIO],
                'precio_esperado': row[COLUMNA_PRECIO],
                'delta'          : 0,
                'delta_pct'      : 0,
                'estado'         : 'Sin curva (solo 1 piso)',
                'recomendacion'  : 'No hay suficiente data por piso, revisar manualmente.'
            })
        return

    # regresión lineal precio vs piso (curva esperada)
    x = avg_floor['PISO'].values
    y = avg_floor[COLUMNA_PRECIO].values
    slope, intercept = np.polyfit(x, y, 1)  # recta: precio = m*piso + b

    # ---- 4.2 Evaluar cada unidad contra la curva ----
    for _, row in g.iterrows():
        piso = row['PISO']
        real = row[COLUMNA_PRECIO]
        esperado = slope * piso + intercept

        delta = real - esperado
        delta_pct = delta / esperado if esperado != 0 else 0

        # Clasificación y recomendación
        if delta_pct > UMBRAL_PCT:
            estado = 'Sobre la curva (caro)'
            nuevo_precio = round(esperado, -2)  # redondear a la centena más cercana
            recomendacion = (
                f"Precio por encima de lo esperado (+{delta_pct*100:.1f}%). "
                f"Considerar BAJAR el precio a aprox. S/ {nuevo_precio:,.0f} "
                f"(∆ S/ {delta:,.0f})."
            )
        elif delta_pct < -UMBRAL_PCT:
            estado = 'Debajo de la curva (barato)'
            nuevo_precio = round(esperado, -2)
            recomendacion = (
                f"Precio por debajo de lo esperado ({delta_pct*100:.1f}%). "
                f"Considerar SUBIR el precio a aprox. S/ {nuevo_precio:,.0f} "
                f"(∆ S/ {abs(delta):,.0f})."
            )
        else:
            estado = 'En línea con la curva'
            nuevo_precio = real
            recomendacion = "Precio alineado a la curva esperada, mantener sin cambios."

        registros.append({
            **{col: row[col] for col in group_cols},
            'unidad'         : row.get('nombre', np.nan),
            'PISO'           : piso,
            'precio_real'    : real,
            'precio_esperado': esperado,
            'delta'          : delta,
            'delta_pct'      : delta_pct * 100,
            'estado'         : estado,
            'precio_sugerido': nuevo_precio,
            'recomendacion'  : recomendacion
        })


# 5) Aplicar por grupo
for key, g in df.groupby(group_cols, dropna=False):
    analizar_grupo(g)

resultado = pd.DataFrame(registros)

# 6) Ordenar para análisis (por proyecto, tipología y “peor desvío” primero)
resultado = resultado.sort_values(
    by=['nombre_proyecto', 'nombre_subdivision', 'nombre_tipologia', 'delta_pct'],
    ascending=[True, True, True, False]
)

# 7) Ver y exportar
print(resultado.head(30))
print("Total de unidades evaluadas:", len(resultado))

resultado.to_excel(r"pricing_curva_y_recomendaciones.xlsx", index=False)
# resultado.to_csv(r"C:\ruta\a\pricing_curva_y_recomendaciones.csv", index=False)
