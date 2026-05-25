# Práctica 2: Control de asistencia
import pandas as pd
import unicodedata
from text_to_num import text2num

def normalizar(texto):
    texto = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in texto if unicodedata.category(c) != "Mn")

def convertir(texto):
    texto = normalizar(texto.strip())
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
df["asistencia"] = df["asistencia"].apply(lambda x: convertir(str(x)))
df = df.dropna()

datos = df["asistencia"]

print("--- Primeras 10 líneas ---")
print(df.head(10).to_string(index=False))
print(f"Total de datos extraídos: {len(df)}")

total = len(datos)
asistencias = int(datos.sum())
faltas = total - asistencias
porcentaje = (asistencias / total) * 100
estado = "Tiene derecho a evaluación" if porcentaje >= 80 else "No tiene derecho a evaluación"

print("=== Resumen de asistencia ===")
print(f"Total de clases: {total}")
print(f"Asistencias:     {asistencias}")
print(f"Faltas:          {faltas}")
print(f"Porcentaje:      {porcentaje:.2f}%")
print(f"Estado:          {estado}")

print("""
--- Conclusión ---
El registro de asistencia permite evaluar el nivel de compromiso del estudiante con la materia.
Un porcentaje alto de asistencia indica constancia y mayor posibilidad de éxito académico,
mientras que un porcentaje bajo puede reflejar situaciones personales o falta de motivación.
El umbral del 80% establece un criterio mínimo para garantizar que el estudiante haya tenido
suficiente exposición al contenido impartido en clase para ser evaluado de forma justa.
""")
