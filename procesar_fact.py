from pickle import FALSE
import pandas as pd
import numpy as np
import os
from datetime import datetime

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                    SECCIÓN 1: CONFIGURACIÓN EDITABLE                       ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

# ===== TABLA PRINCIPAL =====
TABLA_PRINCIPAL = "EXT_CAMARON_2025_0.8.csv"

# ===== TABLAS DE SALIDA (12 tablas a llenar) =====
TABLA_01_REGISTRO            = "Fact_Registro.csv"
TABLA_02_LONGITUD            = "Fact_Longitud_Extruido_0_8.csv"
TABLA_03_DIAMETRO            = "Fact_Diametro_Extruido_0_8.csv"
TABLA_04_FINOS               = "Fact_Finos.csv"
TABLA_05_PARAMETROS_FISICOS  = "Fact_Parametros_Fisicos.csv"
TABLA_06_DENSIDAD            = "Fact_Densidad_Especifica.csv"
TABLA_07_PARTICULAS          = "Fact_Particulas.csv"
TABLA_08_FLOTABILIDAD        = "Fact_Flotabilidad.csv"
TABLA_09_QUIMICO             = "Fact_Quimico_Extruido_0_8.csv"
TABLA_10_PERMEABILIDAD       = "Fact_Permeabilidad.csv"
TABLA_11_OTROS_FISICO        = "Fact_Otros_Fisico_Extruido_0_8.csv"
TABLA_12_CONTROL_CALIDAD     = "Fact_Control_Calidad.csv"

# ===== TABLAS DIMENSIONALES (lookup) =====
DIM_TURNO           = "Dim_Turno.csv"
DIM_TECNICO         = "Dim_Tecnico.csv"
DIM_PRODUCTO        = "Dim_Producto.csv"
DIM_LINEA           = "Dim_Linea.csv"
DIM_ETAPA           = "Dim_Etapa.csv"
DIM_DISENO_PRODUCTO = "Dim_Diseno_Producto.csv"
DIM_AUTORIZADOR     = "Dim_Autorizador.csv"
DIM_MOTIVO_CAUSA    = "Dim_Motivo_Causa_No_Conforme.csv"
DIM_DECISION_EMPLEO = "Dim_Decision_Empleo.csv"

# ===== VARIABLES DE CONFIGURACIÓN =====
Idrangolongitud   = [129, 130, 131, 132, 133, 134, 135, 136, 137]
Idrangodiametro   = [152, 153, 154, 155, 156, 157, 158, 159, 160]
Idvariablequimica = [1, 2, 3, 14, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]

# ===== PARÁMETROS MANUALES =====
PROCESO = "Extruido"
TAMANO  = "0,8"

# ===== ID DE REGISTRO INICIAL =====
# ID_REGISTRO_INICIO = "REG-0012001"  # Formato: REG-XXXXXXX, incremental
ID_REGISTRO_INICIO = "REG-0012145"

# ===== FLAG DE PRUEBAS (Editable) =====
MODO_PRUEBA  = False   # True = modo prueba, False = procesar todas las filas
FILAS_PRUEBA = 1      # Cantidad de filas a procesar en modo prueba (1, 2, etc.)

# ===== MAPEO DE CONVERSIÓN LÍNEA =====
CONVERSION_LINEA = {
    "A": 13,
    "B": 14,
    "C": 15
}


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                    SECCIÓN 2: FUNCIONES AUXILIARES                         ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

def generar_id_registro(indice):
    """Genera ID con formato REG-XXXXXXX a partir del índice base."""
    base = int(ID_REGISTRO_INICIO.replace("REG-", ""))
    numero = base + indice
    return f"REG-{numero:07d}"


def limpiar_valor_numerico(valor):
    """Remueve '%' y retorna el valor limpio. Retorna None si es nulo/vacío."""
    if valor is None:
        return None
    valor_str = str(valor).strip()
    if valor_str == "" or valor_str.lower() == "nan" or valor_str.lower() == "none":
        return None
    if valor_str.endswith("%"):
        valor_str = valor_str[:-1].strip()
    if valor_str == "":
        return None
    return valor_str


def extraer_valor(fila, columna):
    """Extrae un valor de la fila. Retorna None si la columna no existe o el valor es nulo."""
    try:
        valor = fila[columna]
        if pd.isna(valor):
            return None
        if isinstance(valor, float) and valor == int(valor):
            valor_str = str(int(valor)).strip()
        else:
            valor_str = str(valor).strip()
        if valor_str == "" or valor_str.lower() == "nan":
            return None
        return valor_str
    except (KeyError, TypeError):
        return None


def buscar_en_dimension(df_dim, columna_busqueda, valor, columna_resultado="ID"):
    """Busca valor en columna_busqueda del DataFrame. Retorna columna_resultado o None."""
    if valor is None:
        return None
    valor_str = str(valor).strip()
    if valor_str == "" or valor_str.lower() == "nan":
        return None
    try:
        coincidencias = df_dim[df_dim[columna_busqueda].astype(str).str.strip() == valor_str]
        if len(coincidencias) >= 1:
            resultado = coincidencias.iloc[0][columna_resultado]
            if pd.isna(resultado):
                return None
            return resultado
        return None
    except (KeyError, TypeError):
        return None


def convertir_lote_a_fecha(lote):
    """
    Convierte lote formato XXYYMMddXX a fecha dd/MM/YY.
    Ejemplo: PE260102BO → 02/01/26
    Posiciones: YY=2-3, MM=4-5, dd=6-7
    """
    if lote is None:
        return None
    lote_str = str(lote).strip()
    if len(lote_str) < 8:
        return None
    try:
        yy = lote_str[2:4]
        mm = lote_str[4:6]
        dd = lote_str[6:8]
        # Validar que sean numéricos
        int(yy)
        int(mm)
        int(dd)
        return f"{dd}/{mm}/{yy}"
    except (ValueError, IndexError):
        return None


def fecha_str_a_date(fecha_str):
    """Convierte fecha string dd/MM/YY a objeto date para comparaciones."""
    if fecha_str is None:
        return None
    try:
        return datetime.strptime(fecha_str.strip(), "%d/%m/%y").date()
    except (ValueError, AttributeError):
        # Intentar otros formatos comunes
        for fmt in ["%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%d-%m-%y"]:
            try:
                return datetime.strptime(fecha_str.strip(), fmt).date()
            except (ValueError, AttributeError):
                continue
        return None


def buscar_con_filtros_fecha(df_dim, codigo, fecha_produccion_str):
    """
    Búsqueda escalonada para IdProducto e IdDisenoProducto.
    1er filtro: Codigo
    2do filtro: FechaProduccion >= FechaInicio
    3er filtro: FechaProduccion <= FechaFin
    Fallback: si los filtros no reducen a 1, retornar el primer ID por Codigo.
    Solo retorna null si no hay ninguna coincidencia por Codigo.
    """
    if codigo is None:
        return None
    codigo_str = str(codigo).strip()
    if codigo_str == "" or codigo_str.lower() == "nan":
        return None

    try:
        # 1er filtro: buscar por Codigo
        coincidencias = df_dim[
            df_dim["Codigo"].astype(str).str.strip().str.replace(r'\.0$', '', regex=True) == codigo_str
        ]

        if len(coincidencias) == 0:
            # No hay ninguna coincidencia → null
            return None
        if len(coincidencias) == 1:
            resultado = coincidencias.iloc[0]["ID"]
            return None if pd.isna(resultado) else resultado

        # Guardar primer ID como fallback (primera coincidencia por Codigo)
        primer_id = coincidencias.iloc[0]["ID"]
        primer_id = None if pd.isna(primer_id) else primer_id

        # Hay varias coincidencias → intentar 2do filtro
        fecha_prod = fecha_str_a_date(fecha_produccion_str)
        if fecha_prod is None:
            # No se puede parsear la fecha → fallback al primer ID
            return primer_id

        # 2do filtro: FechaProduccion >= FechaInicio
        filtradas = []
        for _, row in coincidencias.iterrows():
            fecha_inicio_str = str(row.get("FechaInicio", "")).strip()
            fecha_inicio = fecha_str_a_date(fecha_inicio_str)
            if fecha_inicio is not None and fecha_prod >= fecha_inicio:
                filtradas.append(row)

        if len(filtradas) == 0:
            # Ninguna cumple el 2do filtro → fallback al primer ID
            return primer_id
        if len(filtradas) == 1:
            resultado = filtradas[0]["ID"]
            return None if pd.isna(resultado) else resultado

        # 3er filtro: FechaProduccion <= FechaFin
        filtradas_final = []
        for row in filtradas:
            fecha_fin_str = str(row.get("FechaFin", "")).strip()
            fecha_fin = fecha_str_a_date(fecha_fin_str)
            if fecha_fin is not None and fecha_prod <= fecha_fin:
                filtradas_final.append(row)

        if len(filtradas_final) == 1:
            resultado = filtradas_final[0]["ID"]
            return None if pd.isna(resultado) else resultado

        # Fallback: los 3 filtros no redujeron a 1 → retornar primer ID
        return primer_id

    except (KeyError, TypeError) as e:
        print(f"  [WARN] Error en buscar_con_filtros_fecha: {e}")
        return None


def convertir_linea(letra):
    """Convierte letra de línea a número según mapeo editable."""
    if letra is None:
        return None
    letra_str = str(letra).strip().upper()
    return CONVERSION_LINEA.get(letra_str, None)


def buscar_motivo_causa(df_dim, motivo, causa):
    """Busca coincidencia simultánea de Motivo y Causa en Dim_Motivo_Causa."""
    if motivo is None and causa is None:
        return None
    motivo_str = str(motivo).strip() if motivo is not None else ""
    causa_str = str(causa).strip() if causa is not None else ""
    if motivo_str.lower() in ("", "nan") and causa_str.lower() in ("", "nan"):
        return None
    try:
        mask = (df_dim["Motivo"].astype(str).str.strip() == motivo_str) & \
                (df_dim["Causa"].astype(str).str.strip() == causa_str)
        coincidencias = df_dim[mask]
        if len(coincidencias) >= 1:
            resultado = coincidencias.iloc[0]["ID"]
            return None if pd.isna(resultado) else resultado
        return None
    except (KeyError, TypeError):
        return None


def cargar_csv_seguro(ruta, nombre_referencia):
    """Carga un CSV de forma segura. Retorna DataFrame o None si falla."""
    try:
        df = pd.read_csv(ruta, encoding="utf-8")
        print(f"  ✓ {nombre_referencia}: {len(df)} filas cargadas")
        return df
    except UnicodeDecodeError:
        try:
            df = pd.read_csv(ruta, encoding="latin-1")
            print(f"  ✓ {nombre_referencia}: {len(df)} filas cargadas (latin-1)")
            return df
        except Exception as e:
            print(f"  ✗ ERROR cargando {nombre_referencia}: {e}")
            return None
    except FileNotFoundError:
        print(f"  ✗ ERROR: Archivo no encontrado: {ruta}")
        return None
    except Exception as e:
        print(f"  ✗ ERROR cargando {nombre_referencia}: {e}")
        return None


def exportar_csv_sin_sobreescribir(df_nuevo, ruta_archivo):
    """
    Exporta DataFrame a CSV sin sobreescribir contenido existente.
    Si el archivo ya existe, agrega las nuevas filas al final.
    Si no existe, crea uno nuevo con encabezados.
    """
    if os.path.exists(ruta_archivo):
        try:
            df_existente = pd.read_csv(ruta_archivo, encoding="utf-8")
        except UnicodeDecodeError:
            df_existente = pd.read_csv(ruta_archivo, encoding="latin-1")
        df_combinado = pd.concat([df_existente, df_nuevo], ignore_index=True)
        df_combinado.to_csv(ruta_archivo, index=False, encoding="utf-8")
        filas_previas = len(df_existente)
        filas_nuevas = len(df_nuevo)
        print(f"  → {ruta_archivo}: {filas_previas} filas previas + {filas_nuevas} nuevas = {len(df_combinado)} total")
    else:
        df_nuevo.to_csv(ruta_archivo, index=False, encoding="utf-8")
        print(f"  → {ruta_archivo}: {len(df_nuevo)} filas creadas (archivo nuevo)")


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                    SECCIÓN 3: FUNCIÓN PRINCIPAL                            ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

def ejecutar_llenado():
    print("=" * 70)
    print("  INICIO DEL PROCESO DE LLENADO DE 12 TABLAS CSV")
    print("=" * 70)

    if MODO_PRUEBA:
        print(f"\n  ⚠ MODO PRUEBA ACTIVADO: procesando solo {FILAS_PRUEBA} fila(s)\n")
    else:
        print(f"\n  ✓ MODO COMPLETO: procesando todas las filas\n")

    # ─────────────────────────────────────────────────────────────────────────
    # PASO 1: Cargar tabla principal y tablas dimensionales
    # ─────────────────────────────────────────────────────────────────────────
    print("─" * 70)
    print("  PASO 1: Cargando archivos CSV")
    print("─" * 70)

    df_principal = cargar_csv_seguro(TABLA_PRINCIPAL, "Tabla Principal")
    if df_principal is None:
        print("\n  ✗ ERROR FATAL: No se pudo cargar la tabla principal. Proceso detenido.")
        return

    # Cargar dimensionales
    dims = {}
    dims_config = {
        "Turno": DIM_TURNO,
        "Tecnico": DIM_TECNICO,
        "Producto": DIM_PRODUCTO,
        "Linea": DIM_LINEA,
        "Etapa": DIM_ETAPA,
        "DisenoProducto": DIM_DISENO_PRODUCTO,
        "Autorizador": DIM_AUTORIZADOR,
        "MotivoCausa": DIM_MOTIVO_CAUSA,
        "DecisionEmpleo": DIM_DECISION_EMPLEO,
    }
    error_fatal = False
    for nombre, archivo in dims_config.items():
        df_dim = cargar_csv_seguro(archivo, f"Dim_{nombre}")
        if df_dim is None:
            print(f"\n  ✗ ERROR FATAL: No se pudo cargar {archivo}. Proceso detenido.")
            error_fatal = True
            break
        dims[nombre] = df_dim

    if error_fatal:
        return

    # ─────────────────────────────────────────────────────────────────────────
    # PASO 2: Identificar columnas dinámicas
    # ─────────────────────────────────────────────────────────────────────────
    print("\n" + "─" * 70)
    print("  PASO 2: Identificando columnas dinámicas")
    print("─" * 70)

    todas_columnas = list(df_principal.columns)

    # Columnas AF - para LONGITUD (antes de "AF - Conforme Longitud")
    cols_af = [c for c in todas_columnas if c.startswith("AF - ")]
    try:
        idx_conf_long = todas_columnas.index("AF - Conforme Longitud")
        cols_longitud = [c for c in cols_af if todas_columnas.index(c) < idx_conf_long]
    except ValueError:
        cols_longitud = []
        print("  [WARN] No se encontró columna 'AF - Conforme Longitud'")

    # Columnas AF - para DIÁMETRO (después de "AF - Longitud <= 10.00 %" y antes de "AF - Conforme Diametro")
    try:
        idx_long_10 = todas_columnas.index("AF - Longitud <=  10.00 %")
        idx_conf_diam = todas_columnas.index("AF - Conforme Diametro")
        cols_diametro = [c for c in cols_af
                        if todas_columnas.index(c) > idx_long_10
                        and todas_columnas.index(c) < idx_conf_diam]
    except ValueError:
        cols_diametro = []
        print("  [WARN] No se encontraron columnas delimitadoras para diámetro")

    # Columnas VQ - para QUÍMICO
    cols_quimico = [c for c in todas_columnas if c.startswith("VQ - ")]

    print(f"  Columnas Longitud (AF -): {len(cols_longitud)} encontradas (esperadas: {len(Idrangolongitud)})")
    print(f"  Columnas Diámetro (AF -): {len(cols_diametro)} encontradas (esperadas: {len(Idrangodiametro)})")
    print(f"  Columnas Químico  (VQ -): {len(cols_quimico)} encontradas (esperadas: {len(Idvariablequimica)})")

    if len(cols_longitud) != len(Idrangolongitud):
        print(f"  [WARN] Cantidad de columnas de longitud ({len(cols_longitud)}) no coincide con Idrangolongitud ({len(Idrangolongitud)})")
    if len(cols_diametro) != len(Idrangodiametro):
        print(f"  [WARN] Cantidad de columnas de diámetro ({len(cols_diametro)}) no coincide con Idrangodiametro ({len(Idrangodiametro)})")
    if len(cols_quimico) != len(Idvariablequimica):
        print(f"  [WARN] Cantidad de columnas de químico ({len(cols_quimico)}) no coincide con Idvariablequimica ({len(Idvariablequimica)})")

    # ─────────────────────────────────────────────────────────────────────────
    # PASO 3: Inicializar listas para acumular filas
    # ─────────────────────────────────────────────────────────────────────────
    filas_t01 = []  # Fact_Registro
    filas_t02 = []  # Fact_Longitud
    filas_t03 = []  # Fact_Diametro
    filas_t04 = []  # Fact_Finos
    filas_t05 = []  # Fact_Parametros_Fisicos
    filas_t06 = []  # Fact_Densidad_Especifica
    filas_t07 = []  # Fact_Particulas
    filas_t08 = []  # Fact_Flotabilidad
    filas_t09 = []  # Fact_Quimico
    filas_t10 = []  # Fact_Permeabilidad
    filas_t11 = []  # Fact_Otros_Fisico
    filas_t12 = []  # Fact_Control_Calidad

    # ─────────────────────────────────────────────────────────────────────────
    # PASO 4: Iterar fila por fila de la tabla principal
    # ─────────────────────────────────────────────────────────────────────────
    print("\n" + "─" * 70)
    print("  PASO 3-4: Iterando filas y llenando tablas")
    print("─" * 70)

    total_filas = len(df_principal)
    if MODO_PRUEBA:
        filas_a_procesar = min(FILAS_PRUEBA, total_filas)
    else:
        filas_a_procesar = total_filas

    print(f"  Total filas en tabla principal: {total_filas}")
    print(f"  Filas a procesar: {filas_a_procesar}\n")

    errores_lookup = []

    for idx in range(filas_a_procesar):
        fila = df_principal.iloc[idx]
        id_registro = generar_id_registro(idx)

        # --- Valores comunes ---
        lote = extraer_valor(fila, "Lote")
        fecha_produccion = convertir_lote_a_fecha(lote)
        codigo = extraer_valor(fila, "Codigo")

        # ═══════════════════════════════════════════════════════════════════
        # TABLA 01: Fact_Registro
        # ═══════════════════════════════════════════════════════════════════
        id_turno = buscar_en_dimension(dims["Turno"], "Turno", extraer_valor(fila, "Turno"))
        id_tecnico = buscar_en_dimension(dims["Tecnico"], "AbreviaturaNombre", extraer_valor(fila, "TAC"))
        id_producto = buscar_con_filtros_fecha(dims["Producto"], codigo, fecha_produccion)
        linea_letra = extraer_valor(fila, "Linea")
        linea_num = convertir_linea(linea_letra)
        id_linea = buscar_en_dimension(dims["Linea"], "Linea", linea_num)
        id_etapa = buscar_en_dimension(dims["Etapa"], "Etapa", extraer_valor(fila, "Etapa"))
        id_diseno = buscar_con_filtros_fecha(dims["DisenoProducto"], codigo, fecha_produccion)
        id_autorizador = buscar_en_dimension(dims["Autorizador"], "AbreviaturaNombre", extraer_valor(fila, "Autorizado por:"))

        fila_t01 = {
            "IdRegistro":       id_registro,
            "Proceso":          PROCESO,
            "Tamano":           TAMANO,
            "Fecha":            extraer_valor(fila, "Fecha"),
            "IdTurno":          id_turno,
            "IdIngeniero":      None,
            "IdTecnico":        id_tecnico,
            "IdProducto":       id_producto,
            "IdLinea":          id_linea,
            "Hora":             extraer_valor(fila, "Hora"),
            "Lote":             lote,
            "FechaProduccion":  fecha_produccion,
            "IdEtapa":          id_etapa,
            "TolvaPorEnvasar":  None,
            "CantidadBolsas":   extraer_valor(fila, "Total Bolsas"),
            "Toneladas":        extraer_valor(fila, "TN"),
            "CodigoQM":         extraer_valor(fila, "Codigo QM"),
            "IdDisenoProducto": id_diseno,
            "IdAutorizador":    id_autorizador,
            "VerEspTecnica":    None,
            "VerEtiqueta":      None,
            "VerFormula":       extraer_valor(fila, "Ver"),
            "Agrupador":        extraer_valor(fila, "Agrupador"),
        }
        filas_t01.append(fila_t01)

        # Registrar errores de lookup
        if id_turno is None and extraer_valor(fila, "Turno") is not None:
            errores_lookup.append(f"Fila {idx}: Turno '{extraer_valor(fila, 'Turno')}' no encontrado")
        if id_tecnico is None and extraer_valor(fila, "TAC") is not None:
            errores_lookup.append(f"Fila {idx}: Técnico '{extraer_valor(fila, 'TAC')}' no encontrado")
        if id_producto is None and codigo is not None:
            errores_lookup.append(f"Fila {idx}: Producto '{codigo}' no encontrado")
        if id_linea is None and linea_letra is not None:
            errores_lookup.append(f"Fila {idx}: Línea '{linea_letra}' no encontrada")
        if id_etapa is None and extraer_valor(fila, "Etapa") is not None:
            errores_lookup.append(f"Fila {idx}: Etapa '{extraer_valor(fila, 'Etapa')}' no encontrada")
        if id_diseno is None and codigo is not None:
            errores_lookup.append(f"Fila {idx}: DiseñoProducto '{codigo}' no encontrado")
        if id_autorizador is None and extraer_valor(fila, "Autorizado por:") is not None:
            errores_lookup.append(f"Fila {idx}: Autorizador '{extraer_valor(fila, 'Autorizado por:')}' no encontrado")

        # ═══════════════════════════════════════════════════════════════════
        # TABLA 02: Fact_Longitud (N filas por cada fila principal)
        # ═══════════════════════════════════════════════════════════════════
        for j, col in enumerate(cols_longitud):
            if j < len(Idrangolongitud):
                filas_t02.append({
                    "IdRegistro": id_registro,
                    "IdRango":    Idrangolongitud[j],
                    "Valor":      limpiar_valor_numerico(extraer_valor(fila, col)),
                })

        # ═══════════════════════════════════════════════════════════════════
        # TABLA 03: Fact_Diametro (N filas por cada fila principal)
        # ═══════════════════════════════════════════════════════════════════
        for j, col in enumerate(cols_diametro):
            if j < len(Idrangodiametro):
                filas_t03.append({
                    "IdRegistro": id_registro,
                    "IdRango":    Idrangodiametro[j],
                    "Valor":      limpiar_valor_numerico(extraer_valor(fila, col)),
                })

        # ═══════════════════════════════════════════════════════════════════
        # TABLA 04: Fact_Finos
        # ═══════════════════════════════════════════════════════════════════
        filas_t04.append({
            "IdRegistro":      id_registro,
            "Muestra":         None,
            "ChampasGr":       None,
            "FinosBajo250um":  limpiar_valor_numerico(extraer_valor(fila, "AF - % de Finos <250 um")),
            "FinosBajo800um":  None,
            "FinosBajo1000um": None,
            "PctChampas":      None,
            "PcFinosBajo250um":  None,
            "PcFinosBajo500um":  None,
            "PcFinosBajo800um":  None,
            "PcFinosBajo1000um": None,
        })

        # ═══════════════════════════════════════════════════════════════════
        # TABLA 05: Fact_Parametros_Fisicos
        # ═══════════════════════════════════════════════════════════════════
        filas_t05.append({
            "IdRegistro":      id_registro,
            "PctConfLongitud": limpiar_valor_numerico(extraer_valor(fila, "AF - Conforme Longitud")),
            "PctConfDiametro": limpiar_valor_numerico(extraer_valor(fila, "AF - Conforme Diametro")),
        })

        # ═══════════════════════════════════════════════════════════════════
        # TABLA 06: Fact_Densidad_Especifica
        # ═══════════════════════════════════════════════════════════════════
        filas_t06.append({
            "IdRegistro":         id_registro,
            "Vol1":               limpiar_valor_numerico(extraer_valor(fila, "DE - VOL.1")),
            "Vol2":               limpiar_valor_numerico(extraer_valor(fila, "DE - VOL.2")),
            "DiferenciaVolumen":  limpiar_valor_numerico(extraer_valor(fila, "DE - DIF. VOLUMEN")),
            "Peso":               limpiar_valor_numerico(extraer_valor(fila, "DE - PESO")),
            "DensidadEspecifica": limpiar_valor_numerico(extraer_valor(fila, "DE - DENSIDAD ESPECIFICA (kg/L)")),
        })

        # ═══════════════════════════════════════════════════════════════════
        # TABLA 07: Fact_Particulas
        # ═══════════════════════════════════════════════════════════════════
        filas_t07.append({
            "IdRegistro":         id_registro,
            "NroParticulas":      limpiar_valor_numerico(extraer_valor(fila, "PPG - Particulas")),
            "Peso":               limpiar_valor_numerico(extraer_valor(fila, "PPG - Peso")),
            "ParticulasPorGramo": limpiar_valor_numerico(extraer_valor(fila, "PPG - Part./g")),
        })

        # ═══════════════════════════════════════════════════════════════════
        # TABLA 08: Fact_Flotabilidad
        # ═══════════════════════════════════════════════════════════════════
        filas_t08.append({
            "IdRegistro":        id_registro,
            "NroParticulas":     limpiar_valor_numerico(extraer_valor(fila, "FH - Pellets que Flotan 140 PPT")),
            "Peso":              limpiar_valor_numerico(extraer_valor(fila, "FH - PESO2")),
            "TiempoHundimiento": limpiar_valor_numerico(extraer_valor(fila, "FH - Tiempo de Hundimiento 140ppt(seg)2")),
            "PctFlotabilidad":   limpiar_valor_numerico(extraer_valor(fila, "FH - Flotabilidad % 140 (10s)ppt")),
            "PctHundimiento":    limpiar_valor_numerico(extraer_valor(fila, "FH - % Hundimiento 140")),
        })

        # ═══════════════════════════════════════════════════════════════════
        # TABLA 09: Fact_Quimico (N filas por cada fila principal)
        # ═══════════════════════════════════════════════════════════════════
        for j, col in enumerate(cols_quimico):
            if j < len(Idvariablequimica):
                filas_t09.append({
                    "IdRegistro": id_registro,
                    "IdVariable": Idvariablequimica[j],
                    "Valor":      limpiar_valor_numerico(extraer_valor(fila, col)),
                })

        # ═══════════════════════════════════════════════════════════════════
        # TABLA 10: Fact_Permeabilidad
        # ═══════════════════════════════════════════════════════════════════
        filas_t10.append({
            "IdRegistro":      id_registro,
            "IdPermeabilidad": 1,
            "Peso1":           50,
            "Peso2":           limpiar_valor_numerico(extraer_valor(fila, "AF - W2")),
            "Permeabilidad":   limpiar_valor_numerico(extraer_valor(fila, "AF - PM")),
        })

        # ═══════════════════════════════════════════════════════════════════
        # TABLA 11: Fact_Otros_Fisico (3 filas por cada fila principal)
        # ═══════════════════════════════════════════════════════════════════
        filas_t11.append({
            "IdRegistro": id_registro,
            "IdVariable": 1,
            "Valor":      extraer_valor(fila, "AF - Hidroestabilidad"),
        })
        filas_t11.append({
            "IdRegistro": id_registro,
            "IdVariable": 2,
            "Valor":      extraer_valor(fila, "AF - Apariencia"),
        })
        filas_t11.append({
            "IdRegistro": id_registro,
            "IdVariable": 4,
            "Valor":      limpiar_valor_numerico(extraer_valor(fila, "AF - % Rebabas")),
        })

        # ═══════════════════════════════════════════════════════════════════
        # TABLA 12: Fact_Control_Calidad
        # ═══════════════════════════════════════════════════════════════════
        motivo = extraer_valor(fila, "Motivo Pulmon")
        causa = extraer_valor(fila, "Causas Pulmon")
        id_motivo_causa = buscar_motivo_causa(dims["MotivoCausa"], motivo, causa)
        id_decision = buscar_en_dimension(dims["DecisionEmpleo"], "Decision", extraer_valor(fila, "D. Empleo"))

        filas_t12.append({
            "IdRegistro":       id_registro,
            "IdMotivo_Causa":   id_motivo_causa,
            "IdDecision":       id_decision,
            "ObservacionPulmon": extraer_valor(fila, "Observaciones"),
        })

        # Progreso
        if (idx + 1) % 100 == 0 or idx == filas_a_procesar - 1:
            print(f"  Procesadas {idx + 1}/{filas_a_procesar} filas...")

    # ─────────────────────────────────────────────────────────────────────────
    # PASO 5: Exportar las 12 tablas a archivos CSV (sin sobreescribir)
    # ─────────────────────────────────────────────────────────────────────────
    print("\n" + "─" * 70)
    print("  PASO 5: Exportando tablas CSV (sin sobreescribir existentes)")
    print("─" * 70)

    tablas_salida = {
        TABLA_01_REGISTRO:           pd.DataFrame(filas_t01),
        TABLA_02_LONGITUD:           pd.DataFrame(filas_t02),
        TABLA_03_DIAMETRO:           pd.DataFrame(filas_t03),
        TABLA_04_FINOS:              pd.DataFrame(filas_t04),
        TABLA_05_PARAMETROS_FISICOS: pd.DataFrame(filas_t05),
        TABLA_06_DENSIDAD:           pd.DataFrame(filas_t06),
        TABLA_07_PARTICULAS:         pd.DataFrame(filas_t07),
        TABLA_08_FLOTABILIDAD:       pd.DataFrame(filas_t08),
        TABLA_09_QUIMICO:            pd.DataFrame(filas_t09),
        TABLA_10_PERMEABILIDAD:      pd.DataFrame(filas_t10),
        TABLA_11_OTROS_FISICO:       pd.DataFrame(filas_t11),
        TABLA_12_CONTROL_CALIDAD:    pd.DataFrame(filas_t12),
    }

    for nombre_archivo, df in tablas_salida.items():
        exportar_csv_sin_sobreescribir(df, nombre_archivo)

    # ─────────────────────────────────────────────────────────────────────────
    # RESUMEN FINAL
    # ─────────────────────────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("  RESUMEN DEL PROCESO")
    print("=" * 70)
    print(f"  Filas procesadas de tabla principal: {filas_a_procesar}")
    print(f"  Modo: {'PRUEBA' if MODO_PRUEBA else 'COMPLETO'}")
    print()
    print(f"  {'Tabla':<45} {'Filas Nuevas':>12}")
    print(f"  {'─' * 45} {'─' * 12}")
    for nombre_archivo, df in tablas_salida.items():
        print(f"  {nombre_archivo:<45} {len(df):>12}")
    total_filas_generadas = sum(len(df) for df in tablas_salida.values())
    print(f"  {'─' * 45} {'─' * 12}")
    print(f"  {'TOTAL':<45} {total_filas_generadas:>12}")

    if errores_lookup:
        print(f"\n  ⚠ Errores de lookup encontrados: {len(errores_lookup)}")
        for err in errores_lookup[:20]:  # Mostrar máximo 20
            print(f"    - {err}")
        if len(errores_lookup) > 20:
            print(f"    ... y {len(errores_lookup) - 20} errores más")
    else:
        print("\n  ✓ No se encontraron errores de lookup")

    print("\n" + "=" * 70)
    print("  PROCESO FINALIZADO")
    print("=" * 70)


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                    SECCIÓN 4: EJECUCIÓN                                    ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

if __name__ == "__main__":
    ejecutar_llenado()