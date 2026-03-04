import pandas as pd
import numpy as np
import os
import re

# ============================================================================
# 1. CONFIGURACIÓN EDITABLE
# ============================================================================

# ===== TABLA PRINCIPAL =====
TABLA_PRINCIPAL = "Extruido_2024.csv"

# ===== TABLAS DE SALIDA (12 tablas a llenar) =====
TABLA_01_REGISTRO            = "Fact_Registro.csv"
TABLA_02_LONGITUD            = "Fact_Longitud_Extruido_0_5.csv"
TABLA_03_DIAMETRO            = "Fact_Diametro_Extruido_0_5.csv"
TABLA_04_FINOS               = "Fact_Finos.csv"
TABLA_05_PARAMETROS_FISICOS  = "Fact_Parametros_Fisicos.csv"
TABLA_06_DENSIDAD            = "Fact_Densidad_Especifica.csv"
TABLA_07_PARTICULAS          = "Fact_Particulas.csv"
TABLA_08_FLOTABILIDAD        = "Fact_Flotabilidad.csv"
TABLA_09_QUIMICO             = "Fact_Quimico_Extruido_0_5.csv"
TABLA_10_PERMEABILIDAD       = "Fact_Permeabilidad.csv"
TABLA_11_OTROS_FISICO        = "Fact_Otros_Fisico_Extruido_0_5.csv"
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
Idrangolongitud   = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
Idrangodiametro   = [11, 12, 13, 14, 15, 16, 17, 18, 19, 20]
Idvariablequimica = [1, 2, 3, 14, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]

# ===== PARÁMETROS MANUALES =====
PROCESO = "Extruido"
TAMANO  = "0,8"

# ===== ID DE REGISTRO INICIAL =====
ID_REGISTRO_INICIO = 12001  # Parte numérica de REG-0012001

# ===== MAPEO DE CONVERSIÓN LÍNEA =====
CONVERSION_LINEA = {
    "A": 13,
    "B": 14,
    "C": 15
}

# ===== DIRECTORIO DE ENTRADA Y SALIDA =====
DIR_ENTRADA = "./"  # Editable: carpeta donde están los CSV de entrada
DIR_SALIDA  = "./"  # Editable: carpeta donde se guardarán los CSV de salida


# ============================================================================
# 2. FUNCIONES AUXILIARES
# ============================================================================

def generar_id_registro(indice):
    """Genera ID con formato REG-XXXXXXX a partir del índice."""
    numero = ID_REGISTRO_INICIO + indice
    return f"REG-{numero:07d}"


def limpiar_valor_numerico(valor):
    """
    Remueve el carácter '%' si existe al final del valor.
    Retorna None si el valor es vacío o nulo.
    """
    if valor is None:
        return None
    if isinstance(valor, (int, float)):
        if pd.isna(valor):
            return None
        return valor
    valor_str = str(valor).strip()
    if valor_str == "" or valor_str.lower() == "nan" or valor_str.lower() == "none":
        return None
    # Remover carácter %
    if valor_str.endswith("%"):
        valor_str = valor_str[:-1].strip()
    # Intentar convertir a número
    try:
        if "." in valor_str or "," in valor_str:
            valor_str = valor_str.replace(",", ".")
            return float(valor_str)
        return float(valor_str)
    except ValueError:
        return valor_str


def obtener_valor(fila, columna):
    """
    Extrae un valor de una fila. Si es nulo o vacío retorna None.
    """
    if columna not in fila.index:
        print(f"  [ADVERTENCIA] Columna '{columna}' no encontrada en la tabla principal.")
        return None
    valor = fila[columna]
    if pd.isna(valor):
        return None
    valor_str = str(valor).strip()
    if valor_str == "" or valor_str.lower() == "nan" or valor_str.lower() == "none":
        return None
    return valor


def obtener_valor_limpio(fila, columna):
    """Extrae un valor y aplica limpieza numérica (remueve %)."""
    valor = obtener_valor(fila, columna)
    if valor is None:
        return None
    return limpiar_valor_numerico(valor)


def buscar_en_dimension(df_dim, columna_busqueda, valor, columna_resultado="ID"):
    """
    Busca un valor en una tabla dimensional y retorna el ID correspondiente.
    Retorna None si no encuentra coincidencia o si el valor es nulo.
    """
    if valor is None:
        return None
    valor_str = str(valor).strip()
    if valor_str == "" or valor_str.lower() == "nan":
        return None
    # Buscar coincidencia
    df_dim[columna_busqueda] = df_dim[columna_busqueda].astype(str).str.strip()
    coincidencias = df_dim[df_dim[columna_busqueda] == valor_str]
    if coincidencias.empty:
        print(f"  [ADVERTENCIA] Valor '{valor_str}' no encontrado en columna '{columna_busqueda}' de tabla dimensional.")
        return None
    return coincidencias.iloc[0][columna_resultado]


def buscar_motivo_causa(df_dim, motivo, causa):
    """
    Busca coincidencia simultánea de Motivo y Causa en la tabla dimensional.
    Retorna el ID o None.
    """
    if motivo is None and causa is None:
        return None
    motivo_str = str(motivo).strip() if motivo is not None else ""
    causa_str = str(causa).strip() if causa is not None else ""
    if motivo_str.lower() in ("", "nan", "none") and causa_str.lower() in ("", "nan", "none"):
        return None
    df_dim["Motivo"] = df_dim["Motivo"].astype(str).str.strip()
    df_dim["Causa"] = df_dim["Causa"].astype(str).str.strip()
    coincidencias = df_dim[
        (df_dim["Motivo"] == motivo_str) & (df_dim["Causa"] == causa_str)
    ]
    if coincidencias.empty:
        print(f"  [ADVERTENCIA] Motivo='{motivo_str}', Causa='{causa_str}' no encontrado en Dim_Motivo_Causa.")
        return None
    return coincidencias.iloc[0]["ID"]


def convertir_lote_a_fecha(lote):
    """
    Convierte un lote con formato XXYYddMMXX a dd/MM/YY.
    Ejemplo: PE260102BO → 01/02/26
    """
    if lote is None:
        return None
    lote_str = str(lote).strip()
    if len(lote_str) < 10:
        print(f"  [ADVERTENCIA] Formato de lote '{lote_str}' no cumple XXYYddMMXX.")
        return None
    try:
        yy = lote_str[2:4]
        dd = lote_str[4:6]
        mm = lote_str[6:8]
        # Validar que sean numéricos
        int(yy)
        int(dd)
        int(mm)
        return f"{dd}/{mm}/{yy}"
    except (ValueError, IndexError):
        print(f"  [ADVERTENCIA] No se pudo convertir lote '{lote_str}' a fecha.")
        return None


def convertir_linea(letra):
    """Convierte letra de línea a número según el mapeo editable."""
    if letra is None:
        return None
    letra_str = str(letra).strip().upper()
    if letra_str in CONVERSION_LINEA:
        return CONVERSION_LINEA[letra_str]
    print(f"  [ADVERTENCIA] Letra de línea '{letra_str}' no está en el mapeo.")
    return None


def identificar_columnas_longitud(columnas):
    """
    Identifica las columnas AF - para longitud:
    todas las que empiezan con 'AF - ' hasta antes de 'AF - Conforme Longitud'.
    """
    cols_af = [c for c in columnas if c.startswith("AF - ")]
    resultado = []
    for col in cols_af:
        if "Conforme Longitud" in col:
            break
        resultado.append(col)
    return resultado


def identificar_columnas_diametro(columnas):
    """
    Identifica las columnas AF - para diámetro:
    después de 'AF - Longitud <= 10.00 %' hasta antes de 'AF - Conforme Diametro'.
    """
    cols_af = [c for c in columnas if c.startswith("AF - ")]
    # Encontrar el índice de la columna que contiene "Longitud" y "10.00"
    inicio = None
    for i, col in enumerate(cols_af):
        if "Longitud" in col and "10.00" in col:
            inicio = i + 1
            break
    # Encontrar el índice de "Conforme Longitud" como alternativa
    if inicio is None:
        for i, col in enumerate(cols_af):
            if "Conforme Longitud" in col:
                inicio = i + 1
                break
    if inicio is None:
        print("  [ADVERTENCIA] No se encontró columna delimitadora para diámetro.")
        return []
    resultado = []
    for col in cols_af[inicio:]:
        if "Conforme Diametro" in col:
            break
        resultado.append(col)
    return resultado


def identificar_columnas_quimico(columnas):
    """Identifica todas las columnas que empiezan con 'VQ - '."""
    return [c for c in columnas if c.startswith("VQ - ")]


def cargar_csv(ruta, nombre_archivo):
    """Carga un CSV con manejo de errores."""
    filepath = os.path.join(ruta, nombre_archivo)
    try:
        df = pd.read_csv(filepath, encoding="utf-8")
        print(f"  [OK] Cargado: {nombre_archivo} ({len(df)} filas, {len(df.columns)} columnas)")
        return df
    except UnicodeDecodeError:
        try:
            df = pd.read_csv(filepath, encoding="latin-1")
            print(f"  [OK] Cargado (latin-1): {nombre_archivo} ({len(df)} filas, {len(df.columns)} columnas)")
            return df
        except Exception as e:
            print(f"  [ERROR FATAL] No se pudo cargar '{nombre_archivo}': {e}")
            return None
    except FileNotFoundError:
        print(f"  [ERROR FATAL] Archivo no encontrado: '{filepath}'")
        return None
    except Exception as e:
        print(f"  [ERROR FATAL] Error al cargar '{nombre_archivo}': {e}")
        return None


# ============================================================================
# 3. FUNCIÓN PRINCIPAL
# ============================================================================

def ejecutar_llenado():
    print("=" * 70)
    print("INICIO DEL PROCESO DE LLENADO DE TABLAS CSV")
    print("=" * 70)

    # -----------------------------------------------------------------
    # PASO 1: Cargar tabla principal y tablas dimensionales
    # -----------------------------------------------------------------
    print("\n--- PASO 1: Cargando archivos CSV ---")

    df_principal = cargar_csv(DIR_ENTRADA, TABLA_PRINCIPAL)
    if df_principal is None:
        print("[ERROR FATAL] No se pudo cargar la tabla principal. Proceso detenido.")
        return

    # Cargar tablas dimensionales
    dim_turno       = cargar_csv(DIR_ENTRADA, DIM_TURNO)
    dim_tecnico     = cargar_csv(DIR_ENTRADA, DIM_TECNICO)
    dim_producto    = cargar_csv(DIR_ENTRADA, DIM_PRODUCTO)
    dim_linea       = cargar_csv(DIR_ENTRADA, DIM_LINEA)
    dim_etapa       = cargar_csv(DIR_ENTRADA, DIM_ETAPA)
    dim_diseno      = cargar_csv(DIR_ENTRADA, DIM_DISENO_PRODUCTO)
    dim_autorizador = cargar_csv(DIR_ENTRADA, DIM_AUTORIZADOR)
    dim_motivo      = cargar_csv(DIR_ENTRADA, DIM_MOTIVO_CAUSA)
    dim_decision    = cargar_csv(DIR_ENTRADA, DIM_DECISION_EMPLEO)

    # Verificar que todas las dimensionales se cargaron
    dimensionales = {
        DIM_TURNO: dim_turno, DIM_TECNICO: dim_tecnico,
        DIM_PRODUCTO: dim_producto, DIM_LINEA: dim_linea,
        DIM_ETAPA: dim_etapa, DIM_DISENO_PRODUCTO: dim_diseno,
        DIM_AUTORIZADOR: dim_autorizador, DIM_MOTIVO_CAUSA: dim_motivo,
        DIM_DECISION_EMPLEO: dim_decision
    }
    for nombre, df in dimensionales.items():
        if df is None:
            print(f"[ERROR FATAL] Tabla dimensional '{nombre}' no cargada. Proceso detenido.")
            return

    # -----------------------------------------------------------------
    # PASO 2: Identificar columnas dinámicas
    # -----------------------------------------------------------------
    print("\n--- PASO 2: Identificando columnas dinámicas ---")

    columnas_principal = list(df_principal.columns)
    cols_longitud = identificar_columnas_longitud(columnas_principal)
    cols_diametro = identificar_columnas_diametro(columnas_principal)
    cols_quimico  = identificar_columnas_quimico(columnas_principal)

    print(f"  Columnas Longitud ({len(cols_longitud)}): {cols_longitud}")
    print(f"  Columnas Diámetro ({len(cols_diametro)}): {cols_diametro}")
    print(f"  Columnas Químico  ({len(cols_quimico)}): {cols_quimico}")

    # Validar cantidades vs arrays de IDs
    if len(cols_longitud) != len(Idrangolongitud):
        print(f"  [ADVERTENCIA] Columnas longitud ({len(cols_longitud)}) != Idrangolongitud ({len(Idrangolongitud)})")
    if len(cols_diametro) != len(Idrangodiametro):
        print(f"  [ADVERTENCIA] Columnas diámetro ({len(cols_diametro)}) != Idrangodiametro ({len(Idrangodiametro)})")
    if len(cols_quimico) != len(Idvariablequimica):
        print(f"  [ADVERTENCIA] Columnas químico ({len(cols_quimico)}) != Idvariablequimica ({len(Idvariablequimica)})")

    # -----------------------------------------------------------------
    # PASO 3 y 4: Iterar filas y llenar las 12 tablas
    # -----------------------------------------------------------------
    print("\n--- PASO 3-4: Iterando filas y llenando tablas ---")

    # Listas para acumular filas de cada tabla
    filas_t01 = []
    filas_t02 = []
    filas_t03 = []
    filas_t04 = []
    filas_t05 = []
    filas_t06 = []
    filas_t07 = []
    filas_t08 = []
    filas_t09 = []
    filas_t10 = []
    filas_t11 = []
    filas_t12 = []

    total_filas = len(df_principal)

    for idx, fila in df_principal.iterrows():
        id_registro = generar_id_registro(idx)

        if (idx + 1) % 100 == 0 or idx == 0:
            print(f"  Procesando fila {idx + 1}/{total_filas} - {id_registro}")

        # ==============================================================
        # TABLA 01: Fact_Registro
        # ==============================================================
        # Lookups
        turno_val = obtener_valor(fila, "Turno")
        id_turno = buscar_en_dimension(dim_turno, "Turno", turno_val)

        tac_val = obtener_valor(fila, "TAC")
        id_tecnico = buscar_en_dimension(dim_tecnico, "AbreviaturaNombre", tac_val)

        codigo_val = obtener_valor(fila, "Codigo")
        id_producto = buscar_en_dimension(dim_producto, "Codigo", codigo_val)

        linea_val = obtener_valor(fila, "Linea")
        linea_num = convertir_linea(linea_val)
        id_linea = buscar_en_dimension(dim_linea, "Linea", linea_num) if linea_num is not None else None

        etapa_val = obtener_valor(fila, "Etapa")
        id_etapa = buscar_en_dimension(dim_etapa, "Etapa", etapa_val)

        id_diseno = buscar_en_dimension(dim_diseno, "Codigo", codigo_val)

        autorizador_val = obtener_valor(fila, "Autorizado por:")
        id_autorizador = buscar_en_dimension(dim_autorizador, "AbreviaturaNombre", autorizador_val)

        lote_val = obtener_valor(fila, "Lote")
        fecha_produccion = convertir_lote_a_fecha(lote_val)

        filas_t01.append({
            "IdRegistro":       id_registro,
            "Proceso":          PROCESO,
            "Tamano":           TAMANO,
            "Fecha":            obtener_valor(fila, "Fecha"),
            "IdTurno":          id_turno,
            "IdIngeniero":      None,
            "IdTecnico":        id_tecnico,
            "IdProducto":       id_producto,
            "IdLinea":          id_linea,
            "Hora":             obtener_valor(fila, "Hora"),
            "Lote":             lote_val,
            "FechaProduccion":  fecha_produccion,
            "IdEtapa":          id_etapa,
            "TolvaPorEnvasar":  None,
            "CantidadBolsas":   obtener_valor(fila, "Total Bolsas"),
            "Toneladas":        obtener_valor(fila, "TN"),
            "CodigoQM":         obtener_valor(fila, "Codigo QM"),
            "IdDisenoProducto": id_diseno,
            "IdAutorizador":    id_autorizador,
            "VerEspTecnica":    None,
            "VerEtiqueta":      None,
            "VerFormula":       obtener_valor(fila, "Ver"),
            "Agrupador":        obtener_valor(fila, "Agrupador"),
        })

        # ==============================================================
        # TABLA 02: Fact_Longitud_Extruido_0_5
        # ==============================================================
        for i, col in enumerate(cols_longitud):
            id_rango = Idrangolongitud[i] if i < len(Idrangolongitud) else None
            filas_t02.append({
                "IdRegistro": id_registro,
                "IdRango":    id_rango,
                "Valor":      obtener_valor_limpio(fila, col),
            })

        # ==============================================================
        # TABLA 03: Fact_Diametro_Extruido_0_5
        # ==============================================================
        for i, col in enumerate(cols_diametro):
            id_rango = Idrangodiametro[i] if i < len(Idrangodiametro) else None
            filas_t03.append({
                "IdRegistro": id_registro,
                "IdRango":    id_rango,
                "Valor":      obtener_valor_limpio(fila, col),
            })

        # ==============================================================
        # TABLA 04: Fact_Finos
        # ==============================================================
        filas_t04.append({
            "IdRegistro":      id_registro,
            "Muestra":         None,
            "ChampasGr":       None,
            "FinosBajo250um":  obtener_valor_limpio(fila, "AF - % de Finos <250 um"),
            "FinosBajo800um":  None,
            "FinosBajo1000um": None,
            "PctChampas":      None,
            "PcFinosBajo250um":  None,
            "PcFinosBajo500um":  None,
            "PcFinosBajo800um":  None,
            "PcFinosBajo1000um": None,
        })

        # ==============================================================
        # TABLA 05: Fact_Parametros_Fisicos
        # ==============================================================
        filas_t05.append({
            "IdRegistro":      id_registro,
            "PctConfLongitud": obtener_valor_limpio(fila, "AF - Conforme Longitud"),
            "PctConfDiametro": obtener_valor_limpio(fila, "AF - Conforme Diametro"),
        })

        # ==============================================================
        # TABLA 06: Fact_Densidad_Especifica
        # ==============================================================
        filas_t06.append({
            "IdRegistro":        id_registro,
            "Vol1":              obtener_valor_limpio(fila, "DE - VOL.1"),
            "Vol2":              obtener_valor_limpio(fila, "DE - VOL.2"),
            "DiferenciaVolumen": obtener_valor_limpio(fila, "DE - DIF. VOLUMEN"),
            "Peso":              obtener_valor_limpio(fila, "DE - PESO"),
            "DensidadEspecifica": obtener_valor_limpio(fila, "DE - DENSIDAD ESPECIFICA (kg/L)"),
        })

        # ==============================================================
        # TABLA 07: Fact_Particulas
        # ==============================================================
        filas_t07.append({
            "IdRegistro":        id_registro,
            "NroParticulas":     obtener_valor_limpio(fila, "PPG - Particulas"),
            "Peso":              obtener_valor_limpio(fila, "PPG - Peso"),
            "ParticulasPorGramo": obtener_valor_limpio(fila, "PPG - Part./g"),
        })

        # ==============================================================
        # TABLA 08: Fact_Flotabilidad
        # ==============================================================
        filas_t08.append({
            "IdRegistro":        id_registro,
            "NroParticulas":     obtener_valor_limpio(fila, "FH - Pellets que Flotan 140 PPT"),
            "Peso":              obtener_valor_limpio(fila, "FH - PESO2"),
            "TiempoHundimiento": obtener_valor_limpio(fila, "FH - Tiempo de Hundimiento 140ppt(seg)2"),
            "PctFlotabilidad":   obtener_valor_limpio(fila, "FH - Flotabilidad % 140 (10s)ppt"),
            "PctHundimiento":    obtener_valor_limpio(fila, "FH - % Hundimiento 140"),
        })

        # ==============================================================
        # TABLA 09: Fact_Quimico_Extruido_0_5
        # ==============================================================
        for i, col in enumerate(cols_quimico):
            id_variable = Idvariablequimica[i] if i < len(Idvariablequimica) else None
            filas_t09.append({
                "IdRegistro": id_registro,
                "IdVariable": id_variable,
                "Valor":      obtener_valor_limpio(fila, col),
            })

        # ==============================================================
        # TABLA 10: Fact_Permeabilidad
        # ==============================================================
        filas_t10.append({
            "IdRegistro":      id_registro,
            "IdPermeabilidad": 1,
            "Peso1":           50,
            "Peso2":           obtener_valor_limpio(fila, "AF - W2"),
            "Permeabilidad":   obtener_valor_limpio(fila, "AF - PM"),
        })

        # ==============================================================
        # TABLA 11: Fact_Otros_Fisico_Extruido_0_5
        # ==============================================================
        # Fila 1: Hidroestabilidad
        filas_t11.append({
            "IdRegistro": id_registro,
            "IdVariable": 1,
            "Valor":      obtener_valor_limpio(fila, "AF - Hidroestabilidad"),
        })
        # Fila 2: Apariencia
        filas_t11.append({
            "IdRegistro": id_registro,
            "IdVariable": 2,
            "Valor":      obtener_valor(fila, "AF - Apariencia"),  # Puede ser texto
        })
        # Fila 3: % Rebabas
        filas_t11.append({
            "IdRegistro": id_registro,
            "IdVariable": 4,
            "Valor":      obtener_valor_limpio(fila, "AF - % Rebabas"),
        })

        # ==============================================================
        # TABLA 12: Fact_Control_Calidad
        # ==============================================================
        motivo_val = obtener_valor(fila, "Motivo Pulmon")
        causa_val  = obtener_valor(fila, "Causas Pulmon")
        id_motivo_causa = buscar_motivo_causa(dim_motivo, motivo_val, causa_val)

        decision_val = obtener_valor(fila, "D. Empleo")
        id_decision = buscar_en_dimension(dim_decision, "Decision", decision_val)

        filas_t12.append({
            "IdRegistro":       id_registro,
            "IdMotivo_Causa":   id_motivo_causa,
            "IdDecision":       id_decision,
            "ObservacionPulmon": obtener_valor(fila, "Observaciones"),
        })

    # -----------------------------------------------------------------
    # PASO 5: Exportar las 12 tablas a archivos CSV
    # -----------------------------------------------------------------
    print("\n--- PASO 5: Exportando tablas CSV ---")

    tablas_salida = {
        TABLA_01_REGISTRO:           filas_t01,
        TABLA_02_LONGITUD:           filas_t02,
        TABLA_03_DIAMETRO:           filas_t03,
        TABLA_04_FINOS:              filas_t04,
        TABLA_05_PARAMETROS_FISICOS: filas_t05,
        TABLA_06_DENSIDAD:           filas_t06,
        TABLA_07_PARTICULAS:         filas_t07,
        TABLA_08_FLOTABILIDAD:       filas_t08,
        TABLA_09_QUIMICO:            filas_t09,
        TABLA_10_PERMEABILIDAD:      filas_t10,
        TABLA_11_OTROS_FISICO:       filas_t11,
        TABLA_12_CONTROL_CALIDAD:    filas_t12,
    }

    for nombre_archivo, filas in tablas_salida.items():
        df_salida = pd.DataFrame(filas)
        ruta_salida = os.path.join(DIR_SALIDA, nombre_archivo)
        df_salida.to_csv(ruta_salida, index=False, encoding="utf-8")
        print(f"  [OK] Exportado: {nombre_archivo} ({len(df_salida)} filas)")

    # -----------------------------------------------------------------
    # PASO 6: Log de resumen
    # -----------------------------------------------------------------
    print("\n" + "=" * 70)
    print("RESUMEN DEL PROCESO")
    print("=" * 70)
    print(f"  Filas en tabla principal: {total_filas}")
    print(f"  ID Registro: {generar_id_registro(0)} → {generar_id_registro(total_filas - 1)}")
    print("-" * 70)
    for nombre_archivo, filas in tablas_salida.items():
        print(f"  {nombre_archivo:45s} → {len(filas):>6} filas")
    total_generadas = sum(len(f) for f in tablas_salida.values())
    print("-" * 70)
    print(f"  {'TOTAL FILAS GENERADAS':45s} → {total_generadas:>6} filas")
    print("=" * 70)
    print("PROCESO FINALIZADO EXITOSAMENTE")
    print("=" * 70)


# ============================================================================
# 4. EJECUCIÓN
# ============================================================================

if __name__ == "__main__":
    ejecutar_llenado()