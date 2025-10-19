# ------------------------------------------------------------
# Anonimización de MYPEs con ruta fija (Windows)
# Lee:   E:\UC\PROYECTO 1\excel generado\ESF_ER_original.xlsx
# Crea:  E:\UC\PROYECTO 1\excel generado\ESF_ER_anon.xlsx
#        E:\UC\PROYECTO 1\excel generado\map_mypes.xlsx
# Requisitos: pandas, openpyxl
# ------------------------------------------------------------
import os, hashlib
import pandas as pd

# === 1) Ruta base (OJO: usar r"" por las barras invertidas y espacios) ===
BASE_DIR = r"E:\UC\PROYECTO 1\excel generado"
INPUT_XLSX = "ESF_ER_original.xlsx"

# Construir rutas absolutas
in_path   = os.path.join(BASE_DIR, INPUT_XLSX)
anon_path = os.path.join(BASE_DIR, "ESF_ER_anon.xlsx")
map_path  = os.path.join(BASE_DIR, "map_mypes.xlsx")

# === 2) Comprobaciones ===
if not os.path.exists(in_path):
    raise FileNotFoundError(
        f"No se encontró el archivo de entrada:\n{in_path}\n"
        "Verifica el nombre (ESF_ER_original.xlsx) y la carpeta."
    )

# === 3) Leer hojas ESF y ER ===
xl = pd.ExcelFile(in_path)  # requiere openpyxl instalado
req_esf, req_er = "ESF", "ER"
if req_esf not in xl.sheet_names or req_er not in xl.sheet_names:
    raise ValueError(
        f"Faltan hojas requeridas. Encontradas: {xl.sheet_names}\n"
        "Debes tener dos hojas llamadas exactamente: 'ESF' y 'ER'."
    )

esf = pd.read_excel(xl, sheet_name=req_esf)
er  = pd.read_excel(xl, sheet_name=req_er)

# Columnas mínimas esperadas (ajusta si tu plantilla difiere)
cols_keep_esf = ["razon_social","RUC","periodo",
                 "activo_corriente","activo_no_corriente",
                 "pasivo_corriente","pasivo_no_corriente",
                 "patrimonio","efectivo"]
cols_keep_er  = ["razon_social","RUC","periodo",
                 "ingresos","costos","gastos","utilidad"]

esf = esf[[c for c in cols_keep_esf if c in esf.columns]].copy()
er  = er[[c for c in cols_keep_er  if c in er.columns]].copy()

# === 4) Unificar por RUC + periodo ===
df = pd.merge(esf, er, on=["razon_social","RUC","periodo"], how="outer")

# === 5) Generar códigos y anonimizar ===
# IMPORTANTE: esta línea debe quedar en UNA SOLA LÍNEA
salt = os.getenv("PGD_SALT", "cambia-esta-semilla-robusta")  # <= no cortar

def make_code(i): 
    return f"MYP-{i:03d}"

df = df.reset_index(drop=True)
df["codigo"] = [make_code(i+1) for i in range(len(df))]

# hash con sal para trazabilidad sin exponer RUC
df["hash_salt"] = df["RUC"].astype(str).apply(
    lambda x: hashlib.sha256((x + salt).encode()).hexdigest()
)

# Diccionario (guardar cifrado y con permisos restringidos)
map_cols = ["codigo","razon_social","RUC","hash_salt"]
map_df = df[map_cols].copy()

# Dataset para análisis (sin identificadores)
anon = df.drop(columns=["razon_social","RUC","hash_salt"], errors="ignore")

# === 6) Guardar en la MISMA carpeta (E:\UC\PROYECTO 1\excel generado) ===
map_df.to_excel(map_path, index=False)   # PROTEGER con 7-Zip AES-256 / BitLocker
anon.to_excel(anon_path, index=False)

print("✅ Listo")
print("Mapa (proteger/cifrar):", map_path)
print("Dataset anonimizado (usar en análisis):", anon_path)
