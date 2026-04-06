#!/usr/bin/env python3
"""
actualizar_json.py — Generador de datos.json para Dashboard Población Inscrita
CESFAM Violeta Parra — Chillán, Ñuble

Uso:
    python actualizar_json.py [archivo.xlsx]

Si no se entrega ruta, el script busca automáticamente el .xlsx en la misma carpeta.

Columnas utilizadas del Excel:
  Col O  (índice 14) — SEXO
  Col V  (índice 21) — NACIONALIDAD
  Col X  (índice 23) — FECHA DE INSCRIPCIÓN
  Col AB (índice 27) — EDAD AÑOS
  Col AC (índice 28) — EDAD MESES
  Col AD (índice 29) — EDAD DIAS
  Col AF (índice 31) — PUEBLOS ORIGINARIOS (PUEBLO INDIG)
  Col AH (índice 33) — PREVISION (INSTITUCION PREVISIONAL)
  Col AQ (índice 42) — SECTOR

Dependencias: pip install pandas openpyxl
"""

import sys
import os
import json
import glob
from datetime import datetime
import pandas as pd

# ─── CONFIGURACIÓN ──────────────────────────────────────────────────────────────

HEADER_ROW = 17          # Fila 0-indexed donde están los encabezados del Excel
DATE_MIN   = "1990-01-01"
DATE_MAX   = datetime.today().strftime("%Y-%m-%d")
OUTPUT_FILE = "datos.json"

# Nombre canónico del dashboard
DASHBOARD_NOMBRE = "Población Inscrita CESFAM Violeta Parra"
AREA             = "Salud Familiar — S.S. Ñuble — Chillán"
VERSION          = "2.0"

# Grupos de edad: (label, condición como función)
GRUPOS_EDAD = [
    ("0-1 meses",    lambda df: (df["EDAD AÑOS"] == 0) & (df["EDAD MESES"] <= 1)),
    ("2-5 meses",    lambda df: (df["EDAD AÑOS"] == 0) & (df["EDAD MESES"] >= 2) & (df["EDAD MESES"] <= 5)),
    ("6-11 meses",   lambda df: (df["EDAD AÑOS"] == 0) & (df["EDAD MESES"] >= 6) & (df["EDAD MESES"] <= 11)),
    ("1 año",        lambda df: df["EDAD AÑOS"] == 1),
    ("2-5 años",     lambda df: (df["EDAD AÑOS"] >= 2) & (df["EDAD AÑOS"] <= 5)),
    ("6-9 años",     lambda df: (df["EDAD AÑOS"] >= 6) & (df["EDAD AÑOS"] <= 9)),
    ("10-14 años",   lambda df: (df["EDAD AÑOS"] >= 10) & (df["EDAD AÑOS"] <= 14)),
    ("15-19 años",   lambda df: (df["EDAD AÑOS"] >= 15) & (df["EDAD AÑOS"] <= 19)),
    ("20-24 años",   lambda df: (df["EDAD AÑOS"] >= 20) & (df["EDAD AÑOS"] <= 24)),
    ("25-34 años",   lambda df: (df["EDAD AÑOS"] >= 25) & (df["EDAD AÑOS"] <= 34)),
    ("35-44 años",   lambda df: (df["EDAD AÑOS"] >= 35) & (df["EDAD AÑOS"] <= 44)),
    ("45-54 años",   lambda df: (df["EDAD AÑOS"] >= 45) & (df["EDAD AÑOS"] <= 54)),
    ("55-64 años",   lambda df: (df["EDAD AÑOS"] >= 55) & (df["EDAD AÑOS"] <= 64)),
    ("65-69 años",   lambda df: (df["EDAD AÑOS"] >= 65) & (df["EDAD AÑOS"] <= 69)),
    ("70 y más",     lambda df: df["EDAD AÑOS"] >= 70),
]

# Mapeo canónico de sectores
SECTOR_MAP = {
    "no informado":                   "NO INFORMADO",
    "sector 1":                       "SECTOR 1",
    "sector 2":                       "SECTOR 2",
    "sector 3 (cecof padre hurtado)": "SECTOR 3 (CECOF PADRE HURTADO)",
    "sector 4":                       "SECTOR 4",
    "sector 5":                       "SECTOR 5",
    "sector 6":                       "SECTOR 6",
    "sector rural":                   "SECTOR RURAL (Sector 7)",
    "sector transversal":             "SECTOR TRANSVERSAL",
}

SECTORES_ORDEN = [
    "NO INFORMADO",
    "SECTOR 1",
    "SECTOR 2",
    "SECTOR 3 (CECOF PADRE HURTADO)",
    "SECTOR 4",
    "SECTOR 5",
    "SECTOR 6",
    "SECTOR RURAL (Sector 7)",
    "SECTOR TRANSVERSAL",
]

# Nacionalidades que NO se consideran extranjeras
NO_EXTRANJERO = {"chilena", "desconocido", "otro"}

# Sexos canónicos
SEXO_HOMBRE     = "Hombre"
SEXO_MUJER      = "Mujer"
SEXO_INTERSEX   = "Intersexual"


# ─── FUNCIONES ──────────────────────────────────────────────────────────────────

def encontrar_excel():
    """Busca automáticamente el .xlsx en la carpeta actual."""
    archivos = glob.glob("*.xlsx") + glob.glob("*.xls")
    if not archivos:
        sys.exit("❌  No se encontró ningún archivo .xlsx en la carpeta actual.")
    if len(archivos) > 1:
        print(f"⚠️  Se encontraron varios archivos: {archivos}")
        print(f"    Se usará el primero: {archivos[0]}")
    return archivos[0]


def leer_excel(ruta):
    print(f"📂  Leyendo: {ruta}")
    df_raw = pd.read_excel(ruta, sheet_name=0, header=None, skiprows=HEADER_ROW)
    encabezados = list(df_raw.iloc[0])
    df_raw.columns = encabezados
    df = df_raw.iloc[1:].reset_index(drop=True)
    print(f"✅  Registros totales cargados: {len(df):,}")
    return df


def normalizar(df):
    """Convierte tipos y normaliza valores clave."""
    df["EDAD AÑOS"]  = pd.to_numeric(df["EDAD AÑOS"],  errors="coerce").fillna(-1).astype(int)
    df["EDAD MESES"] = pd.to_numeric(df["EDAD MESES"], errors="coerce").fillna(-1).astype(int)
    df["EDAD DIAS"]  = pd.to_numeric(df["EDAD DIAS"],  errors="coerce").fillna(-1).astype(int)
    df["SEXO"]       = df["SEXO"].fillna("No Informado").astype(str).str.strip()
    df["SECTOR"]     = df["SECTOR"].fillna("NO INFORMADO").astype(str).str.strip()
    df["SECTOR_CANON"] = df["SECTOR"].str.lower().map(SECTOR_MAP).fillna("NO INFORMADO")
    df["NACIONALIDAD"] = df["NACIONALIDAD"].fillna("Desconocido").astype(str).str.strip()
    df["ES_EXTRANJERO"] = ~df["NACIONALIDAD"].str.lower().str.strip().isin(NO_EXTRANJERO)

    # Fecha inscripción → datetime
    df["FECHA_INSC"] = pd.to_datetime(df["FECHA DE INSCRIPCION"], dayfirst=True, errors="coerce")
    df["ANIO_INSC"]  = df["FECHA_INSC"].dt.year
    df["MES_INSC"]   = df["FECHA_INSC"].dt.month

    return df


def sexo_counts(sub):
    """Devuelve dict con conteos por sexo para un subconjunto de filas."""
    total = len(sub)
    hombres     = int((sub["SEXO"] == SEXO_HOMBRE).sum())
    mujeres     = int((sub["SEXO"] == SEXO_MUJER).sum())
    intersex    = int((sub["SEXO"] == SEXO_INTERSEX).sum())
    no_inform   = total - hombres - mujeres - intersex
    extranjeros = int(sub["ES_EXTRANJERO"].sum())
    return {
        "total":       total,
        "hombres":     hombres,
        "mujeres":     mujeres,
        "intersex":    intersex,
        "no_informado": max(0, no_inform),
        "extranjeros": extranjeros,
    }


def resumen_sectores(sub):
    """Devuelve un dict {sector: sexo_counts} para cada sector canónico."""
    result = {}
    for s in SECTORES_ORDEN:
        filt = sub[sub["SECTOR_CANON"] == s]
        result[s] = sexo_counts(filt)
    return result


def construir_grupos(df):
    grupos = []
    for label, cond_fn in GRUPOS_EDAD:
        mask = cond_fn(df)
        sub  = df[mask]
        base = sexo_counts(sub)
        base["grupo"] = label
        base["por_sector"] = resumen_sectores(sub)
        grupos.append(base)
    return grupos


def construir_serie_anual(df):
    """
    Para cada año de inscripción: total inscritos y conteo por grupo de edad.
    Útil para gráficos de tendencia histórica.
    """
    serie = {}
    anios = sorted(df["ANIO_INSC"].dropna().unique())
    for anio in anios:
        if pd.isna(anio):
            continue
        anio = int(anio)
        sub_anio = df[df["ANIO_INSC"] == anio]
        entry = sexo_counts(sub_anio)
        entry["anio"] = anio
        grupos_anio = []
        for label, cond_fn in GRUPOS_EDAD:
            mask = cond_fn(sub_anio)
            g = sexo_counts(sub_anio[mask])
            g["grupo"] = label
            grupos_anio.append(g)
        entry["grupos"] = grupos_anio
        serie[str(anio)] = entry
    return serie


def construir_extranjeros(df):
    """Detalle de extranjeros por nacionalidad y grupo de edad."""
    ext = df[df["ES_EXTRANJERO"]].copy()
    nac_counts = ext["NACIONALIDAD"].value_counts().to_dict()
    por_grupo = []
    for label, cond_fn in GRUPOS_EDAD:
        mask = cond_fn(ext)
        sub = ext[mask]
        entry = {"grupo": label, "total": len(sub)}
        nac = sub["NACIONALIDAD"].value_counts().to_dict()
        entry["por_nacionalidad"] = {k: int(v) for k, v in nac.items()}
        por_grupo.append(entry)
    return {
        "total": int(ext.shape[0]),
        "por_nacionalidad": {k: int(v) for k, v in nac_counts.items()},
        "por_grupo_edad": por_grupo,
    }


def construir_pueblos_originarios(df):
    """Conteo de pueblos originarios."""
    col = "PUEBLO INDIG" if "PUEBLO INDIG" in df.columns else None
    if col is None:
        return {}
    excluir = {"ninguno", "no sabe", "no contesta"}
    mask = ~df[col].fillna("ninguno").str.lower().isin(excluir)
    po = df[mask][col].value_counts().to_dict()
    return {"total": int(mask.sum()), "detalle": {k: int(v) for k, v in po.items()}}


def construir_prevision(df):
    col = "INSTITUCION PREVISIONAL" if "INSTITUCION PREVISIONAL" in df.columns else None
    if col is None:
        return {}
    prev = df[col].fillna("Sin información").value_counts().to_dict()
    return {k: int(v) for k, v in prev.items()}


def construir_serie_mensual(df):
    """
    Serie mensual compacta: año-mes → {total, hombres, mujeres, intersex, no_informado, extranjeros}
    Para permitir filtros de rango de fechas en el dashboard.
    """
    df2 = df.copy()
    df2["YM"] = df2["FECHA_INSC"].dt.to_period("M").astype(str)
    serie = {}
    for ym, sub in df2.groupby("YM"):
        if ym == "NaT":
            continue
        entry = sexo_counts(sub)
        entry["grupos"] = []
        for label, cond_fn in GRUPOS_EDAD:
            g = sexo_counts(sub[cond_fn(sub)])
            g["grupo"] = label
            entry["grupos"].append(g)
        serie[ym] = entry
    return serie


# ─── MAIN ────────────────────────────────────────────────────────────────────────

def main():
    ruta = sys.argv[1] if len(sys.argv) > 1 else encontrar_excel()
    if not os.path.exists(ruta):
        sys.exit(f"❌  Archivo no encontrado: {ruta}")

    df = leer_excel(ruta)
    df = normalizar(df)

    total = len(df)
    fecha_hoy = datetime.now().isoformat(timespec="seconds")

    print("⚙️   Calculando grupos de edad...")
    grupos = construir_grupos(df)

    print("⚙️   Calculando serie anual...")
    serie_anual = construir_serie_anual(df)

    print("⚙️   Calculando serie mensual...")
    serie_mensual = construir_serie_mensual(df)

    print("⚙️   Calculando extranjeros...")
    extranjeros = construir_extranjeros(df)

    print("⚙️   Calculando pueblos originarios...")
    pueblos = construir_pueblos_originarios(df)

    print("⚙️   Calculando previsión...")
    prevision = construir_prevision(df)

    # Resumen global
    resumen_global = sexo_counts(df)
    resumen_global["por_sector"] = resumen_sectores(df)

    datos = {
        "meta": {
            "dashboard_nombre":    DASHBOARD_NOMBRE,
            "area":                AREA,
            "establecimiento":     "Centro de Salud Familiar Violeta Parra [ÑUBLE]",
            "comuna":              "Chillán",
            "servicio_salud":      "S.S. Ñuble",
            "ultima_actualizacion": fecha_hoy,
            "total_registros":     total,
            "fecha_min":           DATE_MIN,
            "fecha_max":           DATE_MAX,
            "version":             VERSION,
            "fuente_excel":        os.path.basename(ruta),
        },
        "resumen": resumen_global,
        "grupos_edad": grupos,
        "serie_anual": serie_anual,
        "serie_mensual": serie_mensual,
        "extranjeros": extranjeros,
        "pueblos_originarios": pueblos,
        "prevision": prevision,
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)

    size_kb = os.path.getsize(OUTPUT_FILE) / 1024
    print(f"\n✅  JSON generado: {OUTPUT_FILE}  ({size_kb:.1f} KB)")
    print(f"    Registros procesados: {total:,}")
    print(f"    Grupos de edad: {len(grupos)}")
    print(f"    Años en serie: {len(serie_anual)}")
    print(f"    Extranjeros: {extranjeros['total']:,}")
    print(f"    Fecha: {fecha_hoy}")


if __name__ == "__main__":
    main()
