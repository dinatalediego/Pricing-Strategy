import pandas as pd

# 1) Cargar base
df = pd.read_csv(r"../data/Unidades.csv")   # <- cambia la ruta

# 2) Limpieza básica
df = df.dropna(subset=['PISO', 'precio_lista'])
df['PISO'] = df['PISO'].astype(int)
df['precio_lista'] = df['precio_lista'].astype(float)

# (Opcional) precio por m2, si quieres revisar por m2:
df['precio_m2'] = df['precio_lista'] / df['area_total']

# 3) Definir cómo agrupas la “curva lógica” de precios
#    Proyecto + Torre + Tipología (ajusta si quieres agrupar distinto)
group_cols = ['nombre_proyecto', 'nombre_subdivision', 'nombre_tipologia']

# 4) Función que detecta violaciones a la regla:
#    al subir de piso, el precio NO debería subir
def detectar_violaciones(grupo, col_precio='precio_lista', tolerancia_pct=0.01):
    g = grupo.sort_values('PISO').copy()
    violaciones = []

    precio_prev = None
    piso_prev = None

    for _, row in g.iterrows():
        if precio_prev is not None:
            # Regla: precio_actual <= precio_prev * (1 + tolerancia)
            if row[col_precio] > precio_prev * (1 + tolerancia_pct):
                violaciones.append({
                    'nombre_proyecto'   : row['nombre_proyecto'],
                    'nombre_subdivision': row['nombre_subdivision'],
                    'nombre_tipologia'  : row['nombre_tipologia'],
                    'unidad'            : row['nombre'],
                    'PISO'              : row['PISO'],
                    f'{col_precio}_actual': row[col_precio],
                    'PISO_ref'          : piso_prev,
                    f'{col_precio}_ref' : precio_prev,
                    'delta'             : row[col_precio] - precio_prev,
                    'delta_pct'         : (row[col_precio] - precio_prev) / precio_prev * 100
                })
        precio_prev = row[col_precio]
        piso_prev = row['PISO']

    return violaciones

# 5) Aplicar por grupo
registros = []
for key, g in df.groupby(group_cols, dropna=False):
    registros.extend(detectar_violaciones(g, col_precio='precio_lista', tolerancia_pct=0.01))
    # Si quieres revisar por m², usa:
    # registros.extend(detectar_violaciones(g, col_precio='precio_m2', tolerancia_pct=0.01))

outliers = pd.DataFrame(registros)

# 6) Ver y exportar
print(outliers.head(20))
print("Total de unidades fuera de curva:", len(outliers))

# Exportar a Excel/CSV para revisión
outliers.to_excel(r"precios_fuera_de_curva.xlsx", index=False)
# outliers.to_csv(r"C:\ruta\a\precios_fuera_de_curva.csv", index=False)
