import pandas as pd
import os
from datetime import timedelta

# ============================================================
# CONFIGURACIÓN EDITABLE
# ============================================================
ARCHIVO_PRINCIPAL = "EXT_CAMARON_2026_0.8.csv"
ARCHIVO_DIM_PRODUCTO = "Dim_Producto.csv"
ARCHIVO_DIM_DISENO = "Dim_Diseno_Producto.csv"

# Valores fijos editables
PROCESO = "Extruido"
TAMANO = "0,8"
HORA_INICIO = "00:00"
HORA_FIN = "23:59"

# Mapeo de columnas de la tabla principal (editable si cambian los nombres)
COL_CODIGO = "Codigo"
COL_CATEGORIA = "Categoria"
COL_AGRUPADOR = "Agrupador"
COL_LOTE = "Lote"
COL_PROTEINA = "Proteina F.(%)"
COL_HUMEDAD = "Humedad F.(%)"
COL_LIPIDOS = "Lipidos F. (%)"
COL_CENIZA = "Ceniza F.(%)"
COL_FIBRA = "Fibra F.(%)"
COL_ALMIDON = "Almidon F. (%)"
COL_VERSION = "Ver"

# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

def limpiar_porcentaje(valor):
    """Remueve el carácter '%' de valores numéricos y retorna el número o null."""
    if pd.isna(valor) or str(valor).strip() == "":
        return None
    valor_str = str(valor).strip()
    if valor_str.endswith("%"):
        valor_str = valor_str[:-1].strip()
    try:
        return float(valor_str)
    except ValueError:
        return None


def extraer_fecha_de_lote(lote):
    """
    Convierte el formato de Lote XXYYMMddXX a fecha.
    Ejemplo: PE260102BO → 02/01/2026
    Posiciones: [0:2]=XX, [2:4]=YY, [4:6]=MM, [6:8]=dd, [8:10]=XX
    """
    if pd.isna(lote) or str(lote).strip() == "":
        return None
    lote_str = str(lote).strip()
    if len(lote_str) < 8:
        return None
    try:
        yy = int(lote_str[2:4])
        mm = int(lote_str[4:6])
        dd = int(lote_str[6:8])
        year = 2000 + yy
        return pd.Timestamp(year=year, month=mm, day=dd)
    except (ValueError, IndexError):
        return None


def obtener_familia(categoria):
    """
    Deriva la Familia a partir de Categoria (case-insensitive).
    TERAP o TERAB → TER | CLASSIC → CLA | KATAL → KAT | otro → null
    """
    if pd.isna(categoria) or str(categoria).strip() == "":
        return None
    cat_lower = str(categoria).lower()
    if "terap" in cat_lower or "térap" in cat_lower:
        return "TER"
    elif "classic" in cat_lower:
        return "CLA"
    elif "katal" in cat_lower:
        return "KAT"
    else:
        return None


def valor_o_null(valor):
    """Retorna el valor o None si es vacío/NaN."""
    if pd.isna(valor) or str(valor).strip() == "":
        return None
    return valor


def calcular_fecha_fin(grupo_df):
    """
    Dentro de un grupo ordenado por FechaInicio ASC:
    - Última fila: FechaFin = vacío
    - Demás filas: FechaFin = FechaInicio de la siguiente fila - 1 día
    """
    grupo_df = grupo_df.sort_values("FechaInicio").reset_index(drop=True)
    fecha_fin = []
    for i in range(len(grupo_df)):
        if i < len(grupo_df) - 1:
            fecha_fin.append(grupo_df.loc[i + 1, "FechaInicio"] - timedelta(days=1))
        else:
            fecha_fin.append(None)
    grupo_df["FechaFin"] = fecha_fin
    return grupo_df

def cargar_existente(archivo, columnas):
    """
    Carga un archivo CSV existente. Si no existe, retorna un DataFrame vacío
    con las columnas indicadas.
    """
    if os.path.exists(archivo):
        df_existente = pd.read_csv(archivo, encoding="utf-8")
        print(f"  → Archivo existente cargado: {len(df_existente)} filas previas en {archivo}")
        return df_existente
    else:
        print(f"  → Archivo {archivo} no existe, se creará uno nuevo.")
        return pd.DataFrame(columns=columnas)


# ============================================================
# CARGA DE DATOS
# ============================================================
print(f"Cargando tabla principal: {ARCHIVO_PRINCIPAL}")
df_principal = pd.read_csv(ARCHIVO_PRINCIPAL, encoding="utf-8")
print(f"  → {len(df_principal)} filas cargadas.")
print(f"  → Columnas: {list(df_principal.columns)}")

# Extraer fecha de Lote para toda la tabla
df_principal["_fecha_lote"] = df_principal[COL_LOTE].apply(extraer_fecha_de_lote)

# ============================================================
# GENERAR Dim_Producto.csv
# ============================================================
print(f"\n--- Generando {ARCHIVO_DIM_PRODUCTO} ---")

# Paso 1: Agrupar por (Codigo, Agrupador) y tomar fecha mínima
grupo_producto = (
    df_principal.groupby([COL_CODIGO, COL_AGRUPADOR], sort=False)
    .agg(
        FechaInicio=("_fecha_lote", "min"),
        Categoria=(COL_CATEGORIA, "first"),
    )
    .reset_index()
)

# Paso 2: Construir columnas
grupo_producto["Proceso"] = PROCESO
grupo_producto["Tamano"] = TAMANO
grupo_producto["Familia"] = grupo_producto["Categoria"].apply(obtener_familia)
grupo_producto["PctProteina"] = None
grupo_producto["TiempoVidaMeses"] = None
grupo_producto["Version"] = None

# Renombrar columnas
grupo_producto = grupo_producto.rename(columns={
    COL_CODIGO: "Codigo",
    COL_AGRUPADOR: "Agrupador",
})

# Paso 3: Ordenar por Codigo, FechaInicio ASC
grupo_producto = grupo_producto.sort_values(["Codigo", "FechaInicio"]).reset_index(drop=True)

# Paso 4: Calcular FechaFin por cada Codigo
dim_producto_parts = []
for codigo, sub_df in grupo_producto.groupby("Codigo", sort=False):
    sub_df = calcular_fecha_fin(sub_df)
    dim_producto_parts.append(sub_df)

dim_producto = pd.concat(dim_producto_parts, ignore_index=True)

# Paso 5: FlagEstado
dim_producto["FlagEstado"] = dim_producto["FechaFin"].apply(lambda x: 0 if pd.notna(x) else 1)

# Paso 6: Formatear fechas a dd/MM/YY
dim_producto["FechaInicio"] = dim_producto["FechaInicio"].apply(
    lambda x: x.strftime("%d/%m/%y") if pd.notna(x) else None
)
dim_producto["FechaFin"] = dim_producto["FechaFin"].apply(
    lambda x: x.strftime("%d/%m/%y") if pd.notna(x) else ""
)

# Paso 7: Aplicar null donde corresponda
for col in ["Codigo", "Categoria", "Familia", "Agrupador"]:
    dim_producto[col] = dim_producto[col].apply(valor_o_null)

# Paso 8: Seleccionar y ordenar columnas finales
dim_producto = dim_producto[[
    "Codigo", "Proceso", "Tamano", "Categoria", "Familia",
    "PctProteina", "TiempoVidaMeses", "Version", "Agrupador",
    "FechaInicio", "FechaFin", "FlagEstado"
]]

# Paso 9: Cargar datos existentes y agregar nuevas filas sin duplicar
columnas_dim_producto = list(dim_producto.columns)
df_existente_prod = cargar_existente(ARCHIVO_DIM_PRODUCTO, columnas_dim_producto)

dim_producto_final = pd.concat([df_existente_prod, dim_producto], ignore_index=True)
dim_producto_final = dim_producto_final.drop_duplicates(
    subset=["Codigo", "Agrupador", "FechaInicio"], keep="first"
).reset_index(drop=True)

dim_producto_final.to_csv(ARCHIVO_DIM_PRODUCTO, index=False, encoding="utf-8")
filas_nuevas_prod = len(dim_producto_final) - len(df_existente_prod)
print(f"  → {filas_nuevas_prod} filas nuevas agregadas. Total: {len(dim_producto_final)} filas en {ARCHIVO_DIM_PRODUCTO}")

# ============================================================
# GENERAR Dim_Diseno_Producto.csv
# ============================================================
print(f"\n--- Generando {ARCHIVO_DIM_DISENO} ---")

# Paso 1: Limpiar columnas de porcentaje
cols_porcentaje = [COL_PROTEINA, COL_HUMEDAD, COL_LIPIDOS, COL_CENIZA, COL_FIBRA, COL_ALMIDON]
for col in cols_porcentaje:
    df_principal[f"_clean_{col}"] = df_principal[col].apply(limpiar_porcentaje)

# Columnas limpias para agrupar
clean_cols = [f"_clean_{c}" for c in cols_porcentaje]
grupo_cols = [COL_CODIGO] + clean_cols + [COL_VERSION]

# Paso 2: Agrupar y tomar fecha mínima
grupo_diseno = (
    df_principal.groupby(grupo_cols, sort=False, dropna=False)
    .agg(FechaInicio=("_fecha_lote", "min"))
    .reset_index()
)

# Paso 3: Renombrar columnas
grupo_diseno = grupo_diseno.rename(columns={
    COL_CODIGO: "Codigo",
    f"_clean_{COL_PROTEINA}": "Proteina",
    f"_clean_{COL_HUMEDAD}": "Humedad",
    f"_clean_{COL_LIPIDOS}": "Grasa",
    f"_clean_{COL_CENIZA}": "Ceniza",
    f"_clean_{COL_FIBRA}": "Fibra",
    f"_clean_{COL_ALMIDON}": "Almidon",
    COL_VERSION: "Version",
})

# Paso 4: Valores fijos
grupo_diseno["HoraInicio"] = HORA_INICIO
grupo_diseno["HoraFin"] = HORA_FIN

# Paso 5: Ordenar por Codigo, FechaInicio ASC
grupo_diseno = grupo_diseno.sort_values(["Codigo", "FechaInicio"]).reset_index(drop=True)

# Paso 6: Calcular FechaFin por cada Codigo
dim_diseno_parts = []
for codigo, sub_df in grupo_diseno.groupby("Codigo", sort=False):
    sub_df = calcular_fecha_fin(sub_df)
    dim_diseno_parts.append(sub_df)

dim_diseno = pd.concat(dim_diseno_parts, ignore_index=True)

# Paso 7: FlagEstado
dim_diseno["FlagEstado"] = dim_diseno["FechaFin"].apply(lambda x: 0 if pd.notna(x) else 1)

# Paso 8: Formatear fechas a dd/MM/YY
dim_diseno["FechaInicio"] = dim_diseno["FechaInicio"].apply(
    lambda x: x.strftime("%d/%m/%y") if pd.notna(x) else None
)
dim_diseno["FechaFin"] = dim_diseno["FechaFin"].apply(
    lambda x: x.strftime("%d/%m/%y") if pd.notna(x) else ""
)

# Paso 9: Aplicar null donde corresponda
for col in ["Codigo", "Proteina", "Humedad", "Grasa", "Ceniza", "Fibra", "Almidon", "Version"]:
    dim_diseno[col] = dim_diseno[col].apply(valor_o_null)

# Paso 10: Seleccionar y ordenar columnas finales
dim_diseno = dim_diseno[[
    "Codigo", "Proteina", "Humedad", "Grasa", "Ceniza", "Fibra", "Almidon",
    "Version", "FechaInicio", "HoraInicio", "FechaFin", "HoraFin", "FlagEstado"
]]

# Paso 11: Cargar datos existentes y agregar nuevas filas sin duplicar
columnas_dim_diseno = list(dim_diseno.columns)
df_existente_dis = cargar_existente(ARCHIVO_DIM_DISENO, columnas_dim_diseno)

dim_diseno_final = pd.concat([df_existente_dis, dim_diseno], ignore_index=True)
dim_diseno_final = dim_diseno_final.drop_duplicates(
    subset=["Codigo", "Proteina", "Humedad", "Grasa", "Ceniza", "Fibra", "Almidon", "Version", "FechaInicio"],
    keep="first"
).reset_index(drop=True)

dim_diseno_final.to_csv(ARCHIVO_DIM_DISENO, index=False, encoding="utf-8")
filas_nuevas_dis = len(dim_diseno_final) - len(df_existente_dis)
print(f"  → {filas_nuevas_dis} filas nuevas agregadas. Total: {len(dim_diseno_final)} filas en {ARCHIVO_DIM_DISENO}")

print("\n✅ Proceso completado exitosamente.")