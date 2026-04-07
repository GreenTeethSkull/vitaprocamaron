import pandas as pd
import os

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                    SECCION 1: CONFIGURACION EDITABLE                       ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

# ===== ARCHIVOS =====
tabla_principal = "FUELLE_2025_0.5.csv"
tabla_a_llenar  = "Fact_Registro_Fuelle.csv"

# ===== ID DE REGISTRO INICIAL =====
primer_registro = "REG-0025290"

# ===== FLAG DE PRUEBAS =====
MODO_PRUEBA  = False   # True = modo prueba, False = procesar todas las filas
FILAS_PRUEBA = 5       # Cantidad de filas a procesar en modo prueba

# ===== MAPEO DE COLUMNAS =====
# Columna destino -> Columna origen en la tabla principal
MAPEO_COLUMNAS = {
    "FechaVencimiento": "FV",
    "Agregado":         "AGREGADO",
    "Linea":            "LINEA",
    "Estado":           "ESTADO",
    "NroVersion":       "NUMERO DE VERSION",
    "Legibilidad":      "LEGIBILIDAD",
    "Observaciones":    "Observaciones",
    "AccionInmediata":  "Accion Inmediata",
}


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                    SECCION 2: FUNCIONES AUXILIARES                         ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

def generar_id_registro(indice):
    """Genera ID con formato REG-XXXXXXX a partir del indice de fila."""
    base = int(primer_registro.replace("REG-", ""))
    numero = base + indice
    return f"REG-{numero:07d}"


def extraer_valor(fila, columna):
    """Extrae un valor de la fila. Retorna None si la columna no existe o el valor es nulo/vacio."""
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


def fv_tiene_valor(fila):
    """Evalua si la columna FV tiene un valor valido (no nulo, no vacio, no solo espacios)."""
    try:
        valor = fila["FV"]
        if pd.isna(valor):
            return False
        valor_str = str(valor).strip()
        if valor_str == "" or valor_str.lower() == "nan":
            return False
        return True
    except (KeyError, TypeError):
        return False


def cargar_csv_seguro(ruta, nombre_referencia):
    """Carga un CSV de forma segura con manejo de encoding."""
    try:
        df = pd.read_csv(ruta, encoding="utf-8")
        print(f"  + {nombre_referencia}: {len(df)} filas cargadas")
        return df
    except UnicodeDecodeError:
        try:
            df = pd.read_csv(ruta, encoding="latin-1")
            print(f"  + {nombre_referencia}: {len(df)} filas cargadas (latin-1)")
            return df
        except Exception as e:
            print(f"  x ERROR cargando {nombre_referencia}: {e}")
            return None
    except FileNotFoundError:
        print(f"  x ERROR: Archivo no encontrado: {ruta}")
        return None
    except Exception as e:
        print(f"  x ERROR cargando {nombre_referencia}: {e}")
        return None


def exportar_csv_sin_sobreescribir(df_nuevo, ruta_archivo):
    """
    Exporta DataFrame a CSV sin sobreescribir contenido existente.
    Si el archivo ya tiene datos, agrega las nuevas filas al final.
    """
    if os.path.exists(ruta_archivo):
        try:
            df_existente = pd.read_csv(ruta_archivo, encoding="utf-8")
        except UnicodeDecodeError:
            df_existente = pd.read_csv(ruta_archivo, encoding="latin-1")

        filas_previas = len(df_existente)
        if filas_previas > 0:
            df_combinado = pd.concat([df_existente, df_nuevo], ignore_index=True)
            df_combinado.to_csv(ruta_archivo, index=False, encoding="utf-8")
            print(f"  -> {ruta_archivo}: {filas_previas} previas + {len(df_nuevo)} nuevas = {len(df_combinado)} total")
        else:
            # Archivo existe pero solo tiene encabezados (0 filas de datos)
            df_nuevo.to_csv(ruta_archivo, index=False, encoding="utf-8")
            print(f"  -> {ruta_archivo}: {len(df_nuevo)} filas escritas (archivo tenia solo encabezados)")
    else:
        df_nuevo.to_csv(ruta_archivo, index=False, encoding="utf-8")
        print(f"  -> {ruta_archivo}: {len(df_nuevo)} filas creadas (archivo nuevo)")


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                    SECCION 3: FUNCION PRINCIPAL                            ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

def ejecutar_llenado():
    print("=" * 70)
    print("  INICIO DEL PROCESO DE LLENADO - Fact_Registro_Fuelle")
    print("=" * 70)

    if MODO_PRUEBA:
        print(f"\n  [PRUEBA] Procesando solo {FILAS_PRUEBA} fila(s)\n")
    else:
        print(f"\n  [COMPLETO] Procesando todas las filas\n")

    # ─────────────────────────────────────────────────────────────────────────
    # PASO 1: Cargar tabla principal
    # ─────────────────────────────────────────────────────────────────────────
    print("-" * 70)
    print("  PASO 1: Cargando tabla principal")
    print("-" * 70)

    df_principal = cargar_csv_seguro(tabla_principal, "Tabla Principal")
    if df_principal is None:
        print("\n  x ERROR FATAL: No se pudo cargar la tabla principal. Proceso detenido.")
        return

    # Limpiar nombres de columna (quitar espacios trailing/leading)
    df_principal.columns = df_principal.columns.str.strip()
    print(f"  Columnas encontradas: {list(df_principal.columns)}")

    # Verificar que la columna FV existe
    if "FV" not in df_principal.columns:
        print("\n  x ERROR FATAL: La columna 'FV' no existe en la tabla principal.")
        print(f"  Columnas disponibles: {list(df_principal.columns)}")
        return

    # ─────────────────────────────────────────────────────────────────────────
    # PASO 2: Iterar filas y construir registros
    # ─────────────────────────────────────────────────────────────────────────
    print("\n" + "-" * 70)
    print("  PASO 2: Iterando filas y filtrando por FV")
    print("-" * 70)

    total_filas = len(df_principal)
    if MODO_PRUEBA:
        filas_a_procesar = min(FILAS_PRUEBA, total_filas)
    else:
        filas_a_procesar = total_filas

    print(f"  Total filas en tabla principal: {total_filas}")
    print(f"  Filas a evaluar: {filas_a_procesar}\n")

    filas_resultado = []
    filas_saltadas = 0

    for idx in range(filas_a_procesar):
        fila = df_principal.iloc[idx]
        id_registro = generar_id_registro(idx)

        # Filtro: solo procesar si FV tiene valor
        if not fv_tiene_valor(fila):
            filas_saltadas += 1
            continue

        # Construir fila destino
        fila_destino = {"IdRegistro": id_registro}

        for col_destino, col_origen in MAPEO_COLUMNAS.items():
            fila_destino[col_destino] = extraer_valor(fila, col_origen)

        # Columna adicional del destino que no se mapea
        fila_destino["FlagRegistroCompleto"] = None

        filas_resultado.append(fila_destino)

    print(f"  Filas con FV valido (a escribir): {len(filas_resultado)}")
    print(f"  Filas saltadas (FV nulo/vacio):   {filas_saltadas}")

    # ─────────────────────────────────────────────────────────────────────────
    # PASO 3: Preview de registros generados
    # ─────────────────────────────────────────────────────────────────────────
    if filas_resultado:
        print("\n" + "-" * 70)
        print("  PASO 3: Preview de primeros registros generados")
        print("-" * 70)

        preview_count = min(5, len(filas_resultado))
        for i in range(preview_count):
            r = filas_resultado[i]
            print(f"  [{i+1}] {r['IdRegistro']} | FV={r['FechaVencimiento']} | "
                  f"Agregado={r['Agregado']} | Linea={r['Linea']} | "
                  f"Estado={r['Estado']} | Ver={r['NroVersion']}")

        if len(filas_resultado) > preview_count:
            print(f"  ... y {len(filas_resultado) - preview_count} registros mas")

    # ─────────────────────────────────────────────────────────────────────────
    # PASO 4: Exportar a CSV
    # ─────────────────────────────────────────────────────────────────────────
    if len(filas_resultado) == 0:
        print("\n  [INFO] No hay filas para escribir. Proceso terminado sin cambios.")
        return

    print("\n" + "-" * 70)
    print("  PASO 4: Exportando a CSV")
    print("-" * 70)

    df_nuevo = pd.DataFrame(filas_resultado)
    exportar_csv_sin_sobreescribir(df_nuevo, tabla_a_llenar)

    # ─────────────────────────────────────────────────────────────────────────
    # RESUMEN FINAL
    # ─────────────────────────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("  RESUMEN DEL PROCESO")
    print("=" * 70)
    print(f"  Tabla principal:              {tabla_principal}")
    print(f"  Tabla destino:                {tabla_a_llenar}")
    print(f"  Primer registro configurado:  {primer_registro}")
    print(f"  Modo:                         {'PRUEBA' if MODO_PRUEBA else 'COMPLETO'}")
    print(f"  Filas evaluadas:              {filas_a_procesar}")
    print(f"  Filas escritas (FV valido):   {len(filas_resultado)}")
    print(f"  Filas saltadas (FV vacio):    {filas_saltadas}")
    print("=" * 70)
    print("  PROCESO FINALIZADO")
    print("=" * 70)


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                    SECCION 4: EJECUCION                                    ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

if __name__ == "__main__":
    ejecutar_llenado()
