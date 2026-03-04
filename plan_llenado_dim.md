# Plan de Algoritmo de Llenado de Tablas CSV

---

## 1. Configuración de Archivos (Editable)

| Parámetro | Valor |
|---|---|
| **Tabla Principal** | `Extruido_2024.csv` |
| **Primera Tabla (salida)** | `Dim_Producto.csv` |
| **Segunda Tabla (salida)** | `Dim_Diseno_Producto.csv` |

> ⚠️ Los nombres de archivos son editables manualmente en el código antes de la ejecución.

---

## 2. Reglas Generales

- Si un valor no se encuentra en la tabla principal o es `null`/vacío → colocar **null**.
- Valores numéricos que terminen en `%` → remover el carácter `%` y conservar solo el número.
  - Ejemplo: `99.65%` → `99.65`
- Las comparaciones de texto son **case-insensitive** (no distinguen mayúsculas/minúsculas).

---

## 3. Llenado de `Dim_Producto.csv`

### 3.1 Columnas y Origen de Datos

| Columna Destino | Origen / Regla |
|---|---|
| **Codigo** | Columna `Codigo` de la tabla principal |
| **Proceso** | Valor fijo = `Extruido` |
| **Tamano** | Valor editable manual = `0,8` (configurable) |
| **Categoria** | Columna `Categoria` de la tabla principal |
| **Familia** | Derivado de `Categoria` (ver regla 3.2) |
| **PctProteina** | Dejar en blanco (se llenará después) |
| **TiempoVidaMeses** | Dejar en blanco (se llenará después) |
| **Version** | Dejar en blanco |
| **Agrupador** | Columna `Agrupador` de la tabla principal |
| **FechaInicio** | Derivado de columna `Lote` (ver regla 3.3) |
| **FechaFin** | Derivado de `FechaInicio` (ver regla 3.4) |
| **FlagEstado** | Derivado de `FechaFin` (ver regla 3.5) |

### 3.2 Regla de Familia

Evaluar el contenido de la columna `Categoria` (**case-insensitive**, no distingue mayúsculas/minúsculas):

| Si `Categoria` contiene... | Familia |
|---|---|
| `TERAP` o `TÉRAP` | `TER` |
| `CLASSIC` | `CLA` |
| `KATAL` | `KAT` |
| Ninguno de los anteriores | `null` |

### 3.3 Regla de FechaInicio (desde Lote)

1. **Formato del Lote:** `XXYYddMMXX`
   - Posiciones 2-3 → Año (YY)
   - Posiciones 4-5 → Día (dd)
   - Posiciones 6-7 → Mes (MM)
   - Ejemplo: `PE260102BO` → Año=26, Día=01, Mes=02 → `01/02/26`

2. **Agrupación:** Las filas se agrupan por la combinación de `Codigo` + `Agrupador`.
3. **Selección:** Dentro de cada grupo, se toma **una única fila** con la **fecha mínima** extraída de `Lote`.
4. Si `Codigo` es el mismo pero `Agrupador` cambia → **es otra fila distinta**.

### 3.4 Regla de FechaFin

- Las filas resultantes se ordenan por `Codigo` y `FechaInicio`.
- **Última fila (o fila única):** `FechaFin` = vacío.
- **Demás filas:** `FechaFin` = `FechaInicio` de la fila siguiente **- 1 día**.

> Nota: "siguiente fila" se refiere a la siguiente fila **del mismo Codigo**, ordenada por `FechaInicio` ascendente.

### 3.5 Regla de FlagEstado

| Condición | FlagEstado |
|---|---|
| `FechaFin` tiene valor (no vacío) | `0` |
| `FechaFin` está vacío | `1` |

---

## 4. Llenado de `Dim_Diseno_Producto.csv`

### 4.1 Columnas y Origen de Datos

| Columna Destino | Origen / Regla |
|---|---|
| **Codigo** | Columna `Codigo` de la tabla principal |
| **Proteina** | Columna `Proteina F.(%)` de la tabla principal (sin `%`) |
| **Humedad** | Columna `Humedad F.(%)` de la tabla principal (sin `%`) |
| **Grasa** | Columna `Lipidos F. (%)` de la tabla principal (sin `%`) |
| **Ceniza** | Columna `Ceniza F.(%)` de la tabla principal (sin `%`) |
| **Fibra** | Columna `Fibra F.(%)` de la tabla principal (sin `%`) |
| **Almidon** | Columna `Almidon F. (%)` de la tabla principal (sin `%`) |
| **Version** | Columna `Ver` de la tabla principal |
| **FechaInicio** | Derivado de columna `Lote` (ver regla 4.2) |
| **HoraInicio** | Valor fijo = `00:00` |
| **FechaFin** | Derivado de `FechaInicio` (ver regla 4.3) |
| **HoraFin** | Valor fijo = `23:59` |
| **FlagEstado** | Derivado de `FechaFin` (ver regla 4.4) |

### 4.2 Regla de FechaInicio (desde Lote)

1. **Conversión de Lote:** Igual que en Dim_Producto (formato `XXYYddMMXX`).
2. **Agrupación:** Las filas se agrupan por la combinación de:
   - `Codigo`
   - `Proteina F.(%)`
   - `Humedad F.(%)`
   - `Lipidos F. (%)`
   - `Ceniza F.(%)`
   - `Fibra F.(%)`
   - `Almidon F. (%)`
   - `Ver`
3. **Selección:** Dentro de cada grupo, se toma **una única fila** con la **fecha mínima** extraída de `Lote`.
4. Si **cualquiera** de las columnas del grupo cambia → **es otra fila distinta**, aunque el `Codigo` sea el mismo.

### 4.3 Regla de FechaFin

- Las filas resultantes se ordenan por `Codigo` y `FechaInicio`.
- **Última fila (o fila única):** `FechaFin` = vacío.
- **Demás filas:** `FechaFin` = `FechaInicio` de la fila siguiente **- 1 día**.

> Nota: "siguiente fila" se refiere a la siguiente fila **del mismo Codigo**, ordenada por `FechaInicio` ascendente.

### 4.4 Regla de FlagEstado

| Condición | FlagEstado |
|---|---|
| `FechaFin` tiene valor (no vacío) | `0` |
| `FechaFin` está vacío | `1` |

---

## 5. Flujo del Algoritmo (Resumen de Pasos)

```
INICIO
│
├─ 1. Cargar tabla principal (Extruido_2024.csv)
│
├─ 2. Limpieza de datos:
│     ├─ Remover carácter "%" de columnas numéricas
│     └─ Reemplazar valores vacíos/nulos por "null"
│
├─ 3. Extraer fecha de columna "Lote" (formato XXYYddMMXX → dd/MM/YY)
│
├─ 4. GENERAR Dim_Producto.csv:
│     ├─ 4.1 Agrupar por (Codigo, Agrupador)
│     ├─ 4.2 Tomar fecha mínima por grupo
│     ├─ 4.3 Derivar Familia desde Categoria
│     ├─ 4.4 Asignar valores fijos (Proceso, Tamano)
│     ├─ 4.5 Ordenar por Codigo, FechaInicio ASC
│     ├─ 4.6 Calcular FechaFin (siguiente FechaInicio - 1 día; última = vacío)
│     ├─ 4.7 Calcular FlagEstado
│     └─ 4.8 Exportar a Dim_Producto.csv
│
├─ 5. GENERAR Dim_Diseno_Producto.csv:
│     ├─ 5.1 Agrupar por (Codigo, Proteina, Humedad, Grasa, Ceniza, Fibra, Almidon, Ver)
│     ├─ 5.2 Tomar fecha mínima por grupo
│     ├─ 5.3 Limpiar valores numéricos (sin %)
│     ├─ 5.4 Asignar valores fijos (HoraInicio, HoraFin)
│     ├─ 5.5 Ordenar por Codigo, FechaInicio ASC
│     ├─ 5.6 Calcular FechaFin (siguiente FechaInicio - 1 día; última = vacío)
│     ├─ 5.7 Calcular FlagEstado
│     └─ 5.8 Exportar a Dim_Diseno_Producto.csv
│
FIN
```

---

## 6. Valores Editables (Resumen)

| Variable | Valor por defecto | Descripción |
|---|---|---|
| `ARCHIVO_PRINCIPAL` | `Extruido_2024.csv` | Nombre del archivo fuente |
| `ARCHIVO_DIM_PRODUCTO` | `Dim_Producto.csv` | Nombre del archivo de salida 1 |
| `ARCHIVO_DIM_DISENO` | `Dim_Diseno_Producto.csv` | Nombre del archivo de salida 2 |
| `PROCESO` | `Extruido` | Valor fijo para columna Proceso |
| `TAMANO` | `0,8` | Valor fijo para columna Tamano |
| `HORA_INICIO` | `00:00` | Valor fijo para HoraInicio |
| `HORA_FIN` | `23:59` | Valor fijo para HoraFin |

---

## 7. Consideraciones Adicionales

- El algoritmo debe manejar correctamente caracteres especiales en nombres de columna (asteriscos, paréntesis, espacios).
- La conversión de fechas desde `Lote` debe validar que el formato sea correcto; si no lo es → `null`.
- El ordenamiento para calcular `FechaFin` es **por Codigo** y luego **por FechaInicio ascendente**.
- Los duplicados dentro de un mismo grupo se eliminan al tomar la fecha mínima.