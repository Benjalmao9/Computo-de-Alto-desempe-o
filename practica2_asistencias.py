# Práctica 2: Control de asistencia
import pandas as pd
from text_to_num import text2num

import unicodedata

estado_asistencia = {
    "asistio": 1.0,
    "falto": 0.0,
    "no asistio": 0.0,
}

def normalizar(texto):
    texto = unicodedata.normalize("NFKD", texto.lower().strip())
    return "".join(c for c in texto if unicodedata.category(c) != "Mn")

def convertir(texto):
    clave = normalizar(texto)
    if clave in estado_asistencia:
        return estado_asistencia[clave]
    try:
        return float(texto)
    except ValueError:
        pass
    try:
        partes = texto.split(" punto ")
        numeros = [str(text2num(p.strip(), "es")) for p in partes]
        return float(".".join(numeros))
    except (ValueError, KeyError):
        return None

df = pd.read_csv(r"C:\Users\benja\OneDrive\Escritorio\Datasets\asistencias.txt", header=None, names=["asistencia"])
df_raw = df.copy()
df["asistencia"] = df["asistencia"].apply(lambda x: convertir(str(x).strip()))
invalidos = df_raw[df["asistencia"].isna()]
df = df.dropna()

datos = df["asistencia"]
conteo = df["asistencia"].value_counts()

total = len(datos)
asistencias = conteo.get(1.0, 0)
faltas = conteo.get(0.0, 0)
porcentaje = (asistencias / total) * 100
estado = "Tiene derecho a evaluación" if porcentaje >= 80 else "No tiene derecho a evaluación"

resultados = (
    ["--- Datos inválidos ---"] +
    (["Ninguno"] if invalidos.empty else invalidos["asistencia"].tolist()) +
    [
        "",
        "--- Primeras 10 líneas ---",
        df.head(10).to_string(index=False),
        f"Total de datos extraídos: {len(df)}",
        "",
        "=== Resumen de asistencia ===",
        f"Total de clases: {total}",
        f"Asistencias:     {asistencias}",
        f"Faltas:          {faltas}",
        f"Porcentaje:      {porcentaje:.2f}%",
        f"Estado:          {estado}",
        ""
    ]
)

with open("resultados_asistencias.txt", "w", encoding="utf-8") as f:
    for linea in resultados:
        print(linea)
        f.write(str(linea) + "\n")
