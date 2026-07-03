import pandas as pd
import os

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║         REGENERAR Fact_Registro_Fuelle - BASADO EN EXT_CAMARON             ║
# ╠══════════════════════════════════════════════════════════════════════════════╣
# ║  EXT_CAMARON define el numero de filas y los IDs.                          ║
# ║  FUELLE aporta los datos (FV, Agregado, Linea, etc).                       ║
# ║  Solo se escriben filas cuyo FV tenga valor.                               ║
# ║  Rango total: REG-0012001 a REG-0026222.                                   ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

# ===== CONFIGURACION =====
# (archivo_ext, archivo_fuelle, id_inicial)
ARCHIVOS = [
    ("EXT_CAMARON_2026_0.8.csv", "FUELLE_2026_0.8.csv", 12001),
    ("EXT_CAMARON_2025_0.8.csv", "FUELLE_2025_0.8.csv", 12146),
    ("EXT_CAMARON_2024_0.8.csv", "FUELLE_2024_0.8.csv", 20207),
    ("EXT_CAMARON_2026_0.5.csv", "FUELLE_2026_0.5.csv", 25262),
    ("EXT_CAMARON_2025_0.5.csv", "FUELLE_2025_0.5.csv", 25290),
]

ARCHIVO_DESTINO = "Fact_Registro_Fuelle.csv"
MAX_ID = 26222

# Mapeo: columna destino -> posibles nombres en FUELLE
MAPEO_COLUMNAS = {
    "FechaVencimiento": ["FV"],
    "Agregado":         ["AGREGADO"],
    "Linea":            ["LINEA"],
    "Estado":           ["ESTADO ", "ESTADO"],
    "NroVersion":       ["NUMERO DE VERSION"],
    "Legibilidad":      ["LEGIBILIDAD", "LIGIBILIDAD DE LA INFORMACION", "LIGIBILIDAD"],
    "Observaciones":    ["Observaciones ", "Observaciones"],
    "AccionInmediata":  ["Accion Inmediata ", "Accion Inmediata"],
}


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                    FUNCIONES AUXILIARES                                    ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

def cargar_csv_seguro(ruta, nombre):
    for enc in ["utf-8", "latin-1"]:
        try:
            df = pd.read_csv(ruta, encoding=enc, dtype=str)
            df.columns = df.columns.str.strip()
            print(f"  + {nombre}: {len(df)} filas ({enc})")
            return df
        except (UnicodeDecodeError, pd.errors.ParserError):
            continue
        except FileNotFoundError:
            print(f"  x ERROR: Archivo no encontrado: {ruta}")
            return None
    print(f"  x ERROR: No se pudo cargar {ruta}")
    return None


def encontrar_columna(df, posibles_nombres):
    for nombre in posibles_nombres:
        nombre_limpio = nombre.strip()
        for col in df.columns:
            if col.strip() == nombre_limpio:
                return col
    return None


def extraer_valor(fila, columna):
    if columna is None:
        return None
    try:
        valor = fila[columna]
        if pd.isna(valor):
            return None
        valor_str = str(valor).strip()
        if valor_str == "" or valor_str.lower() == "nan":
            return None
        return valor_str
    except (KeyError, TypeError):
        return None


def fv_tiene_valor(fila, columna_fv):
    if columna_fv is None:
        return False
    try:
        valor = fila[columna_fv]
        if pd.isna(valor):
            return False
        valor_str = str(valor).strip()
        if valor_str == "" or valor_str.lower() == "nan":
            return False
        return True
    except (KeyError, TypeError):
        return False


def generar_id(numero):
    return f"REG-{numero:07d}"


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                    PROCESO PRINCIPAL                                       ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

def ejecutar():
    print("=" * 70)
    print("  REGENERACION Fact_Registro_Fuelle")
    print("  EXT_CAMARON define filas/IDs | FUELLE aporta datos")
    print("  Rango: REG-0012001 a REG-0026222")
    print("=" * 70)

    todos_los_registros = []

    for archivo_ext, archivo_fuelle, id_inicial in ARCHIVOS:
        print(f"\n{'─' * 70}")
        print(f"  EXT:    {archivo_ext}")
        print(f"  FUELLE: {archivo_fuelle}")
        print(f"  ID ini: {generar_id(id_inicial)}")
        print(f"{'─' * 70}")

        # Cargar EXT_CAMARON (define cantidad de filas)
        df_ext = cargar_csv_seguro(archivo_ext, archivo_ext)
        if df_ext is None:
            continue

        # Cargar FUELLE (aporta datos)
        df_fuelle = cargar_csv_seguro(archivo_fuelle, archivo_fuelle)
        if df_fuelle is None:
            continue

        # Encontrar columna FV en FUELLE
        col_fv = encontrar_columna(df_fuelle, ["FV"])
        if col_fv is None:
            print(f"  x WARN: No se encontro columna FV en FUELLE, saltando...")
            continue

        # Preparar mapeo de columnas desde FUELLE
        mapeo_local = {}
        for col_destino, posibles in MAPEO_COLUMNAS.items():
            mapeo_local[col_destino] = encontrar_columna(df_fuelle, posibles)

        filas_escritas = 0
        filas_saltadas = 0
        filas_sin_match = 0

        # Iterar sobre EXT_CAMARON (autoridad de filas)
        num_filas = min(len(df_ext), len(df_fuelle))

        for idx in range(num_filas):
            id_num = id_inicial + idx

            if id_num > MAX_ID:
                break

            id_registro = generar_id(id_num)
            fila_fuelle = df_fuelle.iloc[idx]

            if not fv_tiene_valor(fila_fuelle, col_fv):
                filas_saltadas += 1
                continue

            registro = {"IdRegistro": id_registro}
            for col_destino, col_origen in mapeo_local.items():
                registro[col_destino] = extraer_valor(fila_fuelle, col_origen)
            registro["FlagRegistroCompleto"] = None

            todos_los_registros.append(registro)
            filas_escritas += 1

        if len(df_ext) != len(df_fuelle):
            print(f"  ! NOTA: EXT tiene {len(df_ext)} filas, FUELLE tiene {len(df_fuelle)}")
            print(f"    Se procesaron {num_filas} filas (la menor cantidad)")

        id_final_real = generar_id(id_inicial + num_filas - 1)
        print(f"  Filas procesadas:  {num_filas}")
        print(f"  Escritas (FV):     {filas_escritas}")
        print(f"  Saltadas:          {filas_saltadas}")
        print(f"  ID final:          {id_final_real}")

    # ─── Exportar ───
    if not todos_los_registros:
        print("\n  x ERROR: No se generaron registros.")
        return

    print(f"\n{'─' * 70}")
    print(f"  EXPORTANDO")
    print(f"{'─' * 70}")

    df_final = pd.DataFrame(todos_los_registros)
    df_final.to_csv(ARCHIVO_DESTINO, index=False, encoding="utf-8")

    ids = df_final["IdRegistro"].tolist()
    ids_unicos = set(ids)
    duplicados = len(ids) - len(ids_unicos)

    print(f"  Registros escritos:  {len(df_final)}")
    print(f"  IDs unicos:          {len(ids_unicos)}")
    print(f"  IDs duplicados:      {duplicados}")
    print(f"  Primer registro:     {df_final['IdRegistro'].iloc[0]}")
    print(f"  Ultimo registro:     {df_final['IdRegistro'].iloc[-1]}")

    max_real = max(int(r.replace("REG-", "")) for r in ids)
    if max_real > MAX_ID:
        print(f"  x ALERTA: ID maximo {generar_id(max_real)} excede el limite!")
    else:
        print(f"  OK: ID maximo {generar_id(max_real)} dentro del rango")

    print(f"\n{'=' * 70}")
    print(f"  PROCESO FINALIZADO")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    ejecutar()
