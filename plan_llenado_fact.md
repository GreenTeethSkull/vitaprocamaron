# Plan de Algoritmo de Llenado de 12 Tablas CSV

---

## 1. Configuración Editable

### 1.1 Nombres de Archivos (Editables)

```python
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
```

### 1.2 Variables Editables

```python
# ===== VARIABLES DE CONFIGURACIÓN =====
Idrangolongitud   = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
Idrangodiametro   = [11, 12, 13, 14, 15, 16, 17, 18, 19, 20]
Idvariablequimica = [1, 2, 3, 14, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]

# ===== PARÁMETROS MANUALES =====
PROCESO = "Extruido"
TAMANO  = "0,8"  # Editable manualmente

# ===== ID DE REGISTRO INICIAL =====
ID_REGISTRO_INICIO = "REG-0012001"  # Formato: REG-XXXXXXX, incremental
```

### 1.3 Mapeo de Conversión Línea (Editable)

```python
CONVERSION_LINEA = {
    "A": 13,
    "B": 14,
    "C": 15
}
```

---

## 2. Reglas Generales de Procesamiento

### 2.1 Manejo de Valores Nulos o Vacíos
- Si al buscar un valor en una tabla dimensional **no se encuentra coincidencia**, colocar `null`.
- Si el valor de origen en la tabla principal es **vacío, nulo o inexistente**, colocar `null`.
- Aplica para **todas** las 12 tablas.

### 2.2 Limpieza de Valores Numéricos
- Si un valor numérico termina con el carácter `%`, se debe **remover el carácter `%`** antes de insertarlo.
  - Ejemplo: `99.65%` → `99.65`
- Aplica para **todos** los campos numéricos de todas las tablas.

### 2.3 Generación de ID de Registro
- Se genera un **ID único** por cada fila de la tabla principal.
- Formato: `REG-XXXXXXX` (7 dígitos con ceros a la izquierda).
- Inicia en `REG-0012001` y se incrementa secuencialmente: `REG-0012001`, `REG-0012002`, `REG-0012003`, ...
- Este ID se reutiliza en **todas** las 12 tablas de salida para la misma fila de origen.

---

## 3. Flujo General del Algoritmo

```
┌─────────────────────────────────────────────────┐
│  PASO 0: Cargar configuración editable          │
│  (nombres de archivos, variables, parámetros)   │
└──────────────────────┬──────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────┐
│  PASO 1: Cargar tabla principal y todas las     │
│  tablas dimensionales (lookup)                  │
└──────────────────────┬──────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────┐
│  PASO 2: Identificar columnas dinámicas         │
│  (columnas "AF - " para longitud, diámetro;     │
│   columnas "VQ - " para químico)                │
└──────────────────────┬──────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────┐
│  PASO 3: Iterar por cada fila de la tabla       │
│  principal y generar el IdRegistro              │
└──────────────────────┬──────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────┐
│  PASO 4: Por cada fila, llenar las 12 tablas    │
│  aplicando reglas de lookup, conversión,        │
│  limpieza y manejo de nulos                     │
└──────────────────────┬──────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────┐
│  PASO 5: Exportar las 12 tablas a archivos CSV  │
└─────────────────────────────────────────────────┘
```

---

## 4. Funciones Auxiliares Requeridas

### 4.1 `generar_id_registro(indice)`
- Genera el ID con formato `REG-XXXXXXX` a partir del índice base.
- Ejemplo: índice 0 → `REG-0012001`, índice 1 → `REG-0012002`.

### 4.2 `buscar_en_dimension(df_dim, columna_busqueda, valor, columna_resultado)`
- Busca `valor` en `columna_busqueda` del DataFrame `df_dim`.
- Retorna el valor de `columna_resultado` si encuentra coincidencia.
- Retorna `null` si no encuentra coincidencia o si `valor` es nulo/vacío.

### 4.3 `limpiar_valor_numerico(valor)`
- Remueve el carácter `%` si existe al final del valor.
- Retorna `null` si el valor es vacío o nulo.
- Ejemplo: `"99.65%"` → `99.65`

### 4.4 `convertir_lote_a_fecha(lote)`
- Recibe un lote con formato `XXYYddMMXX`.
- Extrae posiciones: `YY` = año, `dd` = día, `MM` = mes.
- Retorna fecha en formato `dd/MM/YY`.
- Ejemplo: `PE260102BO` → `01/02/26`

### 4.5 `convertir_linea(letra)`
- Convierte letra a número según el mapeo editable: `A=13, B=14, C=15`.
- Retorna `null` si la letra no está en el mapeo.

---

## 5. Detalle de Llenado por Tabla

---

### 5.1 Tabla 01: `Fact_Registro.csv`

**Relación:** 1 fila en tabla principal → 1 fila en esta tabla.

| Columna Destino    | Origen / Lógica                                                                                                                                                                                                 |
| ------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| IdRegistro         | ID generado (`REG-XXXXXXX`)                                                                                                                                                                                    |
| Proceso            | Valor fijo: `"Extruido"`                                                                                                                                                                                       |
| Tamano             | Valor manual editable: `"0,8"`                                                                                                                                                                                 |
| Fecha              | Extraer de columna `Fecha`                                                                                                                                                                                     |
| IdTurno            | Extraer valor de columna `Turno` → buscar en `Dim_Turno.csv` columna `Turno` → extraer `ID`                                                                                                                   |
| IdIngeniero        | Dejar vacío                                                                                                                                                                                                    |
| IdTecnico          | Extraer valor de columna `TAC` → buscar en `Dim_Tecnico.csv` columna `AbreviaturaNombre` → extraer `ID`                                                                                                       |
| IdProducto         | Extraer valor de columna `Codigo` → buscar en `Dim_Producto.csv` columna `Codigo` → extraer `ID`                                                                                                              |
| IdLinea            | Extraer valor de columna `Linea` → convertir letra a número (`A=13, B=14, C=15`) → buscar en `Dim_Linea.csv` columna `Linea` → extraer `ID`                                                                  |
| Hora               | Extraer de columna `Hora`                                                                                                                                                                                      |
| Lote               | Extraer de columna `Lote`                                                                                                                                                                                      |
| FechaProduccion    | Extraer de columna `Lote` → convertir formato `XXYYddMMXX` → `dd/MM/YY`. Ejemplo: `PE260102BO` → `01/02/26`                                                                                                  |
| IdEtapa            | Extraer valor de columna `Etapa` → buscar en `Dim_Etapa.csv` columna `Etapa` → extraer `ID`                                                                                                                   |
| TolvaPorEnvasar    | Dejar en blanco                                                                                                                                                                                                |
| CantidadBolsas     | Extraer de columna `Total Bolsas`                                                                                                                                                                              |
| Toneladas          | Extraer de columna `TN`                                                                                                                                                                                        |
| CodigoQM           | Extraer de columna `Codigo QM`                                                                                                                                                                                 |
| IdDisenoProducto   | Extraer valor de columna `Codigo` → buscar en `Dim_Diseno_Producto.csv` columna `Codigo` → extraer `ID`                                                                                                       |
| IdAutorizador      | Extraer valor de columna `Autorizado por:` → buscar en `Dim_Autorizador.csv` columna `AbreviaturaNombre` → extraer `ID`                                                                                       |
| VerEspTecnica      | Dejar en blanco                                                                                                                                                                                                |
| VerEtiqueta        | Dejar en blanco                                                                                                                                                                                                |
| VerFormula         | Extraer de columna `Ver`                                                                                                                                                                                       |
| Agrupador          | Extraer de columna `Agrupador`                                                                                                                                                                                 |

**Lookups requeridos:** `Dim_Turno`, `Dim_Tecnico`, `Dim_Producto`, `Dim_Linea`, `Dim_Etapa`, `Dim_Diseno_Producto`, `Dim_Autorizador`.

---

### 5.2 Tabla 02: `Fact_Longitud_Extruido_0_5.csv`

**Relación:** 1 fila en tabla principal → **N filas** (una por cada columna `AF - ` de longitud).

**Lógica de identificación de columnas:**
- Tomar todas las columnas que empiecen con `"AF - "` **hasta antes** de la columna `"AF - Conforme Longitud"` (sin incluirla).
- Deben ser exactamente **10 columnas** (correspondientes a los 10 valores de `Idrangolongitud`).

| Columna Destino | Origen / Lógica                                                                 |
| --------------- | ------------------------------------------------------------------------------- |
| IdRegistro      | ID generado (mismo para todas las filas de la iteración)                        |
| IdRango         | Valor del array `Idrangolongitud` según el orden de la columna (posición 0→1, 1→2, ..., 9→10) |
| Valor           | Valor extraído de la columna `AF - ` correspondiente. Aplicar limpieza numérica (`%` → sin `%`) |

---

### 5.3 Tabla 03: `Fact_Diametro_Extruido_0_5.csv`

**Relación:** 1 fila en tabla principal → **N filas** (una por cada columna `AF - ` de diámetro).

**Lógica de identificación de columnas:**
- Tomar todas las columnas que empiecen con `"AF - "` **después** de la columna `"AF - Longitud <= 10.00 %"` **hasta antes** de la columna `"AF - Conforme Diametro"` (sin incluirla).
- Deben ser exactamente **10 columnas** (correspondientes a los 10 valores de `Idrangodiametro`).

| Columna Destino | Origen / Lógica                                                                   |
| --------------- | --------------------------------------------------------------------------------- |
| IdRegistro      | ID generado (mismo para todas las filas de la iteración)                          |
| IdRango         | Valor del array `Idrangodiametro` según el orden de la columna (posición 0→11, 1→12, ..., 9→20) |
| Valor           | Valor extraído de la columna `AF - ` correspondiente. Aplicar limpieza numérica   |

---

### 5.4 Tabla 04: `Fact_Finos.csv`

**Relación:** 1 fila en tabla principal → 1 fila en esta tabla.

| Columna Destino   | Origen / Lógica                                                  |
| ----------------- | ---------------------------------------------------------------- |
| IdRegistro        | ID generado                                                      |
| Muestra           | Dejar en blanco                                                  |
| ChampasGr         | Dejar en blanco                                                  |
| FinosBajo250um    | Extraer de columna `AF - % de Finos <250 um`. Limpieza numérica |
| FinosBajo800um    | Dejar en blanco                                                  |
| FinosBajo1000um   | Dejar en blanco                                                  |
| PctChampas        | Dejar en blanco                                                  |
| PcFinosBajo250um  | Dejar en blanco                                                  |
| PcFinosBajo500um  | Dejar en blanco                                                  |
| PcFinosBajo800um  | Dejar en blanco                                                  |
| PcFinosBajo1000um | Dejar en blanco                                                  |

---

### 5.5 Tabla 05: `Fact_Parametros_Fisicos.csv`

**Relación:** 1 fila en tabla principal → 1 fila en esta tabla.

| Columna Destino | Origen / Lógica                                                       |
| --------------- | --------------------------------------------------------------------- |
| IdRegistro      | ID generado                                                           |
| PctConfLongitud | Extraer de columna `AF - Conforme Longitud`. Limpieza numérica       |
| PctConfDiametro | Extraer de columna `AF - Conforme Diametro`. Limpieza numérica       |

---

### 5.6 Tabla 06: `Fact_Densidad_Especifica.csv`

**Relación:** 1 fila en tabla principal → 1 fila en esta tabla.

| Columna Destino    | Origen / Lógica                                                              |
| ------------------ | ---------------------------------------------------------------------------- |
| IdRegistro         | ID generado                                                                  |
| Vol1               | Extraer de columna `DE - VOL.1`. Limpieza numérica                          |
| Vol2               | Extraer de columna `DE - VOL.2`. Limpieza numérica                          |
| DiferenciaVolumen  | Extraer de columna `DE - DIF. VOLUMEN`. Limpieza numérica                   |
| Peso               | Extraer de columna `DE - PESO`. Limpieza numérica                           |
| DensidadEspecifica | Extraer de columna `DE - DENSIDAD ESPECIFICA (kg/L)`. Limpieza numérica     |

---

### 5.7 Tabla 07: `Fact_Particulas.csv`

**Relación:** 1 fila en tabla principal → 1 fila en esta tabla.

| Columna Destino    | Origen / Lógica                                                    |
| ------------------ | ------------------------------------------------------------------ |
| IdRegistro         | ID generado                                                        |
| NroParticulas      | Extraer de columna `PPG - Particulas`. Limpieza numérica           |
| Peso               | Extraer de columna `PPG - Peso`. Limpieza numérica                 |
| ParticulasPorGramo | Extraer de columna `PPG - Part./g`. Limpieza numérica              |

---

### 5.8 Tabla 08: `Fact_Flotabilidad.csv`

**Relación:** 1 fila en tabla principal → 1 fila en esta tabla.

| Columna Destino    | Origen / Lógica                                                                          |
| ------------------ | ---------------------------------------------------------------------------------------- |
| IdRegistro         | ID generado                                                                              |
| NroParticulas      | Extraer de columna `FH - Pellets que Flotan 140 PPT`. Limpieza numérica                 |
| Peso               | Extraer de columna `FH - PESO2`. Limpieza numérica                                      |
| TiempoHundimiento  | Extraer de columna `FH - Tiempo de Hundimiento 140ppt(seg)2`. Limpieza numérica         |
| PctFlotabilidad    | Extraer de columna `FH - Flotabilidad % 140 (10s)ppt`. Limpieza numérica                |
| PctHundimiento     | Extraer de columna `FH - % Hundimiento 140`. Limpieza numérica                          |

---

### 5.9 Tabla 09: `Fact_Quimico_Extruido_0_5.csv`

**Relación:** 1 fila en tabla principal → **N filas** (una por cada columna `VQ - `).

**Lógica de identificación de columnas:**
- Tomar todas las columnas que empiecen con `"VQ - "` en orden de aparición.
- Deben ser exactamente **14 columnas** (correspondientes a los 14 valores de `Idvariablequimica`).

| Columna Destino | Origen / Lógica                                                                       |
| --------------- | ------------------------------------------------------------------------------------- |
| IdRegistro      | ID generado (mismo para todas las filas de la iteración)                              |
| IdVariable      | Valor del array `Idvariablequimica` según el orden de la columna                      |
| Valor           | Valor extraído de la columna `VQ - ` correspondiente. Aplicar limpieza numérica       |

---

### 5.10 Tabla 10: `Fact_Permeabilidad.csv`

**Relación:** 1 fila en tabla principal → 1 fila en esta tabla.

| Columna Destino  | Origen / Lógica                                              |
| ---------------- | ------------------------------------------------------------ |
| IdRegistro       | ID generado                                                  |
| IdPermeabilidad  | Valor fijo: `1`                                              |
| Peso1            | Valor fijo: `50`                                             |
| Peso2            | Extraer de columna `AF - W2`. Limpieza numérica             |
| Permeabilidad    | Extraer de columna `AF - PM`. Limpieza numérica             |

---

### 5.11 Tabla 11: `Fact_Otros_Fisico_Extruido_0_5.csv`

**Relación:** 1 fila en tabla principal → **3 filas** en esta tabla.

| Fila | IdRegistro  | IdVariable | Valor (columna origen)                    |
| ---- | ----------- | ---------- | ----------------------------------------- |
| 1    | ID generado | `1`        | Columna `AF - Hidroestabilidad`           |
| 2    | ID generado | `2`        | Columna `AF - Apariencia`                 |
| 3    | ID generado | `4`        | Columna `AF - % Rebabas`. Limpieza numérica |

---

### 5.12 Tabla 12: `Fact_Control_Calidad.csv`

**Relación:** 1 fila en tabla principal → 1 fila en esta tabla.

| Columna Destino    | Origen / Lógica                                                                                                                                                                                                                                  |
| ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| IdRegistro         | ID generado                                                                                                                                                                                                                                      |
| IdMotivo_Causa     | Extraer valores de columnas `Motivo Pulmon` y `Causas Pulmon` → buscar en `Dim_Motivo_Causa_No_Conforme.csv` donde coincidan columnas `Motivo` y `Causa` simultáneamente → extraer `ID`. Si no hay coincidencia → `null`                        |
| IdDecision         | Extraer valor de columna `D. Empleo` → buscar en `Dim_Decision_Empleo.csv` columna `Decision` → extraer `ID`                                                                                                                                   |
| ObservacionPulmon  | Extraer de columna `Observaciones`                                                                                                                                                                                                               |

---

## 6. Resumen de Relaciones Fila Principal → Filas Generadas

| #  | Tabla de Salida                        | Filas por cada fila principal |
| -- | -------------------------------------- | ----------------------------- |
| 01 | Fact_Registro                          | 1                             |
| 02 | Fact_Longitud_Extruido_0_5             | 10 (iteración columnas AF -)  |
| 03 | Fact_Diametro_Extruido_0_5             | 10 (iteración columnas AF -)  |
| 04 | Fact_Finos                             | 1                             |
| 05 | Fact_Parametros_Fisicos                | 1                             |
| 06 | Fact_Densidad_Especifica               | 1                             |
| 07 | Fact_Particulas                        | 1                             |
| 08 | Fact_Flotabilidad                      | 1                             |
| 09 | Fact_Quimico_Extruido_0_5              | 14 (iteración columnas VQ -)  |
| 10 | Fact_Permeabilidad                     | 1                             |
| 11 | Fact_Otros_Fisico_Extruido_0_5         | 3                             |
| 12 | Fact_Control_Calidad                   | 1                             |

**Total de filas generadas por cada fila de la tabla principal:** **45 filas** distribuidas en 12 tablas.

---

## 7. Tablas Dimensionales Requeridas (Lookup)

| Tabla Dimensional                    | Columna de Búsqueda    | Columna de Resultado | Usada en Tabla(s) |
| ------------------------------------ | ---------------------- | -------------------- | ------------------ |
| Dim_Turno.csv                        | Turno                  | ID                   | 01                 |
| Dim_Tecnico.csv                      | AbreviaturaNombre      | ID                   | 01                 |
| Dim_Producto.csv                     | Codigo                 | ID                   | 01                 |
| Dim_Linea.csv                        | Linea                  | ID                   | 01                 |
| Dim_Etapa.csv                        | Etapa                  | ID                   | 01                 |
| Dim_Diseno_Producto.csv              | Codigo                 | ID                   | 01                 |
| Dim_Autorizador.csv                  | AbreviaturaNombre      | ID                   | 01                 |
| Dim_Motivo_Causa_No_Conforme.csv     | Motivo + Causa         | ID                   | 12                 |
| Dim_Decision_Empleo.csv              | Decision               | ID                   | 12                 |

---

## 8. Orden de Ejecución del Algoritmo

1. **Cargar configuración** (nombres de archivos, variables, parámetros manuales).
2. **Cargar todos los CSV** (tabla principal + 9 tablas dimensionales).
3. **Identificar columnas dinámicas:**
   - Columnas `AF - ` para longitud (antes de `AF - Conforme Longitud`).
   - Columnas `AF - ` para diámetro (después de `AF - Longitud <= 10.00 %` y antes de `AF - Conforme Diametro`).
   - Columnas `VQ - ` para químico.
4. **Inicializar 12 DataFrames vacíos** con las columnas correspondientes.
5. **Iterar fila por fila** de la tabla principal:
   - a. Generar `IdRegistro`.
   - b. Llenar fila de Tabla 01 (Registro) con lookups.
   - c. Llenar N filas de Tabla 02 (Longitud) iterando columnas AF -.
   - d. Llenar N filas de Tabla 03 (Diámetro) iterando columnas AF -.
   - e. Llenar fila de Tabla 04 (Finos).
   - f. Llenar fila de Tabla 05 (Parámetros Físicos).
   - g. Llenar fila de Tabla 06 (Densidad Específica).
   - h. Llenar fila de Tabla 07 (Partículas).
   - i. Llenar fila de Tabla 08 (Flotabilidad).
   - j. Llenar N filas de Tabla 09 (Químico) iterando columnas VQ -.
   - k. Llenar fila de Tabla 10 (Permeabilidad).
   - l. Llenar 3 filas de Tabla 11 (Otros Físico).
   - m. Llenar fila de Tabla 12 (Control Calidad) con lookups.
6. **Aplicar limpieza general** (remover `%`, manejar nulos).
7. **Exportar los 12 DataFrames** a archivos CSV.
8. **Log de resumen:** cantidad de filas generadas por tabla, errores de lookup encontrados.

---

## 9. Validaciones y Manejo de Errores

| Validación                                      | Acción                                                    |
| ----------------------------------------------- | --------------------------------------------------------- |
| Valor no encontrado en tabla dimensional        | Colocar `null`                                            |
| Valor vacío o nulo en tabla principal            | Colocar `null`                                            |
| Letra de línea no está en mapeo (A, B, C)       | Colocar `null`                                            |
| Formato de Lote no cumple `XXYYddMMXX`          | Colocar `null` en FechaProduccion                         |
| Columnas `AF -` o `VQ -` no coinciden en cantidad con arrays de ID | Generar advertencia en log y procesar las que existan     |
| Valor numérico con carácter `%`                 | Remover `%` y conservar el número                         |
| Archivo dimensional no encontrado               | Error fatal: detener ejecución e informar                 |
| Tabla principal vacía                           | Advertencia: generar archivos vacíos con solo encabezados |