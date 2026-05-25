# Práctica 4: Registro de actividad física
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

df = pd.read_csv(r"C:\Users\benja\OneDrive\Escritorio\Datasets\activida_fisica.txt", header=None, names=["minutos"])
df["minutos"] = df["minutos"].apply(lambda x: convertir(str(x)))
df = df.dropna()

datos = df["minutos"]

print("--- Primeras 10 líneas ---")
print(df.head(10).to_string(index=False))
print(f"Total de datos extraídos: {len(df)}")

total_registros = len(datos)
total_minutos = int(datos.sum())
promedio = datos.mean()
mayor = int(datos.max())
menor = int(datos.min())
dias_sin_ejercicio = int((datos == 0).sum())

if promedio >= 30:
    nivel = "Actividad adecuada"
elif promedio >= 15:
    nivel = "Actividad moderada"
else:
    nivel = "Actividad baja"

print("=== Resumen de actividad física ===")
print(f"Registros:          {total_registros}")
print(f"Total:              {total_minutos} minutos")
print(f"Promedio:           {promedio:.2f} minutos")
print(f"Mayor:              {mayor} minutos")
print(f"Menor:              {menor} minutos")
print(f"Días sin ejercicio: {dias_sin_ejercicio}")
print(f"Nivel:              {nivel}")

print("""
--- Conclusión ---
El análisis de la actividad física diaria permite identificar si la persona mantiene hábitos
de ejercicio consistentes y suficientes para su salud. El número de días sin ejercicio es un
indicador clave: una cantidad elevada sugiere falta de constancia que puede afectar el bienestar
físico a largo plazo. El promedio diario determina el nivel general de actividad, y en caso de
ser bajo o moderado, se recomienda establecer rutinas más regulares para alcanzar los 30 minutos
diarios recomendados por los estándares de salud.
""")
