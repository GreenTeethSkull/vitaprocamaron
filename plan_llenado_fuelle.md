# Plan de Llenado - Fact_Registro_Fuelle

## Objetivo

Llenar la tabla `Fact_Registro_Fuelle.csv` a partir de los datos contenidos en `FUELLE_2026_0.8.csv`, filtrando unicamente las filas cuya columna **FV** tenga un valor no nulo y no vacio.

---

## Variables de Configuracion

| Variable          | Valor                      | Descripcion                                              |
| ----------------- | -------------------------- | -------------------------------------------------------- |
| `tabla_principal` | `FUELLE_2026_0.8.csv`      | CSV fuente con los datos del fuelle                      |
| `tabla_a_llenar`  | `Fact_Registro_Fuelle.csv` | CSV destino donde se escribiran los registros procesados |
| `primer_registro` | `REG-0012001`              | ID del primer registro; se incrementa +1 por cada fila   |

---

## Logica de Asignacion de IdRegistro

Cada fila de la tabla principal (incluyendo las que NO se procesaran) tiene un IdRegistro **imaginario** asignado secuencialmente:

- Fila 0 (indice 0) -> `REG-0012001`
- Fila 1 (indice 1) -> `REG-0012002`
- Fila 2 (indice 2) -> `REG-0012003`
- ...y asi sucesivamente.

El IdRegistro se calcula como:
```
base = int("0012001")  # parte numerica de primer_registro
IdRegistro = f"REG-{(base + indice_fila):07d}"
```

**Solo se escriben en la tabla destino las filas cuyo campo FV NO sea nulo/vacio.**

---

## Criterio de Filtrado

Una fila se procesa (se escribe en `Fact_Registro_Fuelle.csv`) **unicamente si**:

1. El valor en la columna `FV` no es `NaN` (nulo de pandas).
2. El valor en la columna `FV`, al convertirlo a string y hacer `.strip()`, no es `""` (vacio).
3. El valor en la columna `FV` no es un espacio en blanco (` `).

Filas que no cumplan este criterio son **saltadas** pero su indice sigue contando para el IdRegistro.

---

## Mapeo de Columnas (Tabla Principal -> Tabla Destino)

| Columna Destino (`Fact_Registro_Fuelle`) | Columna Origen (`FUELLE_2026_0.8`) | Notas                                     |
| ---------------------------------------- | ---------------------------------- | ----------------------------------------- |
| `IdRegistro`                             | (calculado)                        | REG-XXXXXXX incremental desde fila 0      |
| `FechaVencimiento`                       | `FV`                               | Valor directo de la columna FV             |
| `Agregado`                               | `AGREGADO`                         | Valor directo                              |
| `Linea`                                  | `LINEA`                            | Valor directo (ej: E2, E3)                 |
| `Estado`                                 | `ESTADO `                          | Nota: la columna tiene espacio trailing    |
| `NroVersion`                             | `NUMERO DE VERSION`                | Valor directo (ej: V5, V4, V1)            |
| `Legibilidad`                            | `LEGIBILIDAD`                      | Valor directo                              |
| `Observaciones`                          | `Observaciones `                   | Nota: la columna tiene espacio trailing    |
| `AccionInmediata`                        | `Accion Inmediata `                | Nota: la columna tiene espacio trailing    |

> **Nota importante**: Algunas columnas del CSV fuente tienen espacios trailing en sus nombres (ej: `"ESTADO "`, `"Observaciones "`, `"Accion Inmediata "`). El script debe manejar esto con `.strip()` en los nombres de columna al cargar el CSV.

---

## Columna Adicional en Destino

La tabla `Fact_Registro_Fuelle.csv` tiene una columna adicional `FlagRegistroCompleto` que no se llena desde la tabla principal. Se dejara como valor vacio (`None`).

---

## Flujo del Proceso

```
1. Cargar FUELLE_2026_0.8.csv (tabla principal)
   - Limpiar nombres de columna (strip de espacios)
   
2. Iterar TODAS las filas (indice 0 a N-1)
   - Para cada fila, calcular su IdRegistro (base + indice)
   - Evaluar si FV tiene valor no nulo/no vacio
     - SI tiene valor: construir fila destino y agregarla a la lista
     - NO tiene valor: saltar fila (no escribir nada)
     
3. Cargar Fact_Registro_Fuelle.csv (tabla destino existente)

4. Concatenar registros nuevos al final de los existentes

5. Exportar CSV actualizado sin sobreescribir datos previos
```

---

## Ejemplo con Datos Reales

Del CSV fuente, las primeras filas se ven asi:

| Indice | FV          | AGREGADO | LINEA | ESTADO   | Se procesa? |
| ------ | ----------- | -------- | ----- | -------- | ----------- |
| 0      | ` ` (esp)   |          | E2    | CONFORME | NO          |
| 1      | `12/27/2026`| EXT      | E3    | CONFORME | SI          |
| 2      | ` ` (esp)   |          | E3    | CONFORME | NO          |
| 3      | ` ` (esp)   |          | E3    | CONFORME | NO          |
| 4      | `12/28/2026`| EXT      | E3    | CONFORME | SI          |
| 5      | `12/28/2026`| -        | E3    | CONFORME | SI          |

Resultado:
- Fila indice 0: IdRegistro = REG-0012001, **NO se escribe** (FV vacio)
- Fila indice 1: IdRegistro = REG-0012002, **SI se escribe** (FV = 12/27/2026)
- Fila indice 2: IdRegistro = REG-0012003, **NO se escribe** (FV vacio)
- Fila indice 3: IdRegistro = REG-0012004, **NO se escribe** (FV vacio)
- Fila indice 4: IdRegistro = REG-0012005, **SI se escribe** (FV = 12/28/2026)
- Fila indice 5: IdRegistro = REG-0012006, **SI se escribe** (FV = 12/28/2026)

---

## Modo Prueba

El script incluye un modo prueba (`MODO_PRUEBA = True`) que permite procesar solo N filas para validar antes de ejecutar el proceso completo.

---

## Validaciones y Reporte

Al finalizar, el script imprime:
- Total de filas en la tabla principal
- Total de filas que pasaron el filtro (FV no vacio)
- Total de filas que fueron saltadas
- Cantidad de filas escritas en el CSV destino
- Preview de los primeros registros generados
