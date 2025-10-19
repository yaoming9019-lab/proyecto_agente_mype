# ESF/ER – Fórmulas y Validaciones (versión alineada a PLANTILLA_ESF_ER_FINAL.xlsx)

Este documento describe las **fórmulas**, **validaciones** y **formatos condicionales** configurados en la plantilla `PLANTILLA_ESF_ER_FINAL.xlsx` (hojas **ESF**, **ER**, **LEEME** y **Diccionario**).

---

## 1) Hoja ESF (Estado de Situación Financiera)

**Columnas:**  
`codigo_mype | periodo | activo_corriente | activo_no_corriente | pasivo_corriente | pasivo_no_corriente | patrimonio | efectivo | activo_total | pasivo_total | validacion_balance`

### 1.1 Fórmulas por fila (ejemplo en fila 2)
- **activo_total (I2):**  
  `=C2 + D2`
- **pasivo_total (J2):**  
  `=E2 + F2`
- **validacion_balance (K2):**  
  `=IF(ROUND(I2,2)=ROUND(J2+G2,2),"OK","ERROR")`

> Notas:
> - Se utiliza `ROUND(...,2)` para evitar falsos negativos por decimales.
> - La fórmula de `validacion_balance` verifica la **identidad contable**:  
>   **Activo Total = Pasivo Total + Patrimonio**.

### 1.2 Validación de datos
- **periodo (columna B, celdas B2:B1000):**  
  Validación por **longitud de texto = 7** (formato `YYYY-MM`).  
  - Título: “Periodo (YYYY-MM)”  
  - Mensaje: “Ej.: 2024-12”

### 1.3 Formato condicional
- **validacion_balance (K2:K1000):**  
  Regla “Texto que contiene” → valor **ERROR** → resaltar con fondo rojo claro.

### 1.4 Formato numérico
- Columnas **C:H** y totales **I:J** con formato **numérico** `#,##0.00`.

---

## 2) Hoja ER (Estado de Resultados)

**Columnas:**  
`codigo_mype | periodo | ingresos | costos | gastos | utilidad | utilidad_calc | validacion_er`

### 2.1 Fórmulas por fila (ejemplo en fila 2)
- **utilidad_calc (G2):**  
  `=C2 - D2 - E2`
- **validacion_er (H2):**  
  `=IF(AND(NOT(ISBLANK(F2)),ROUND(F2,2)=ROUND(G2,2)),"OK",IF(ISBLANK(F2),"OK","REVISAR"))`

> Notas:
> - Si `utilidad (F2)` está vacía, el estado es **OK** (se usará `utilidad_calc`).
> - Si `utilidad` tiene valor, debe coincidir con `utilidad_calc` a 2 decimales; de lo contrario, **REVISAR**.

### 2.2 Validación de datos
- **periodo (columna B, celdas B2:B1000):**  
  Validación por **longitud de texto = 7** (formato `YYYY-MM`).  
  - Título: “Periodo (YYYY-MM)”  
  - Mensaje: “Ej.: 2024-12”

### 2.3 Formato condicional
- **validacion_er (H2:H1000):**  
  Regla “Texto que contiene” → valor **REVISAR** → resaltar con fondo rojo claro.

### 2.4 Formato numérico
- Columnas **C:G** con formato **numérico** `#,##0.00`.

---

## 3) Hoja LEEME (Instrucciones)
- Instrucciones de uso de la plantilla: anonimización del `codigo_mype`, formato de `periodo`, uso de punto decimal, y comportamiento de las columnas calculadas (`activo_total`, `pasivo_total`, `utilidad_calc`) y validaciones (`validacion_balance`, `validacion_er`).

## 4) Hoja Diccionario (Definiciones)
- Descripción de cada columna, hoja de pertenencia y explicación de su uso.

---

## 5) Buenas prácticas
- Ingresar números **sin comas** ni símbolos monetarios; usar **punto** como separador decimal.
- Mantener el formato `YYYY-MM` para `periodo` (ej.: `2024-12`).
- Si hay **ERROR** o **REVISAR**, corregir montos o revisar si `periodo` es el correcto.
- Usar siempre **códigos anonimizados** (`MYP-XXX`) en `codigo_mype`.

---

## 6) Versionado
Este documento corresponde a la plantilla `PLANTILLA_ESF_ER_FINAL.xlsx`. Si se modifican columnas o fórmulas, actualizar este archivo y renombrarlo como `05_docs_ESF_ER_formulas_validaciones_vX.Y.md`.

