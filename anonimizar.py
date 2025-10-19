# 04_codigo/anonimizar.py
import os, hashlib
import pandas as pd

# === RUTA BASE: AJUSTA A TU EQUIPO ===
BASE_DIR = r"E:\UC\PROYECTO 1\excel generado"  # o ...\PROYECTO_1
INPUT_XLSX = "ESF_ER_original.xlsx"

in_path   = os.path.join(BASE_DIR, INPUT_XLSX)
anon_path = os.path.join(BASE_DIR, "ESF_ER_anon.xlsx")
map_path  = os.path.join(BASE_DIR, "map_mypes.xlsx")

if not os.path.exists(in_path):
    raise FileNotFoundError(f"No existe: {in_path}")

xl = pd.ExcelFile(in_path)
esf = pd.read_excel(xl, "ESF")
er  = pd.read_excel(xl, "ER")

# Columnas esperadas (ajusta si difiere)
cols_esf = ["razon_social","RUC","periodo","activo_corriente",
            "activo_no_corriente","pasivo_corriente","pasivo_no_corriente",
            "patrimonio","efectivo"]
cols_er  = ["razon_social","RUC","periodo","ingresos","costos","gastos","utilidad"]

esf = esf[[c for c in cols_esf if c in esf.columns]].copy()
er  = er[[c for c in cols_er  if c in er.columns]].copy()

df = pd.merge(esf, er, on=["razon_social","RUC","periodo"], how="outer")

# Generar códigos MYP-xxx y hash con sal (no exponer hash en dataset analítico)
salt = os.getenv("PGD_SALT", "cambia-esta-semilla-robusta")

def make_code(i): return f"MYP-{i:03d}"
df = df.reset_index(drop=True)
df["codigo_mype"] = [make_code(i+1) for i in range(len(df))]
df["hash_salt"] = df["RUC"].astype(str).apply(
    lambda x: hashlib.sha256((x + salt).encode()).hexdigest()
)

# Diccionario reservado (solo IP)
map_cols = ["codigo_mype","razon_social","RUC","hash_salt"]
map_df = df[map_cols].drop_duplicates()

# Dataset para análisis (sin identificadores)
drop_cols = ["razon_social","RUC","hash_salt"]
anon = df.drop(columns=drop_cols, errors="ignore")

# Guardar
map_df.to_excel(map_path, index=False)   # PROTEGER con 7-Zip AES-256 o BitLocker
anon.to_excel(anon_path, index=False)
print("Listo ✔")
print("Mapa (proteger):", map_path)
print("Anónimo (usar en análisis):", anon_path)
