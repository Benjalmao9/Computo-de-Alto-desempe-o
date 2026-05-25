# Práctica 3: Análisis de consumo de agua
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

df = pd.read_csv(r"C:\Users\benja\OneDrive\Escritorio\Datasets\consumo_agua.txt", header=None, names=["litros"])
df["litros"] = df["litros"].apply(lambda x: convertir(str(x)))
df = df.dropna()

datos = df["litros"]

print("--- Primeras 10 líneas ---")
print(df.head(10).to_string(index=False))
print(f"Total de datos extraídos: {len(df)}")

total_registros = len(datos)
total_consumo = datos.sum()
promedio = datos.mean()
mayor = datos.max()
menor = datos.min()
meta_cumplida = (datos >= 2.0).sum()
recomendacion = "Consumo adecuado" if promedio >= 2.0 else "Aumentar el consumo"

print("=== Resumen de consumo de agua ===")
print(f"Registros:      {total_registros}")
print(f"Total:          {total_consumo:.2f} litros")
print(f"Promedio:       {promedio:.2f} litros")
print(f"Mayor:          {mayor} litros")
print(f"Menor:          {menor} litros")
print(f"Meta cumplida:  {meta_cumplida} días")
print(f"Recomendación:  {recomendacion}")

print("""
--- Conclusión ---
El análisis del consumo diario de agua revela si los hábitos de hidratación se encuentran
dentro de los rangos saludables recomendados. Un promedio por debajo de 2 litros diarios
indica que la persona no está cubriendo la ingesta mínima necesaria para un funcionamiento
óptimo del organismo. Los días en que se cumple la meta representan una oportunidad para
reforzar el hábito, mientras que los días deficientes señalan áreas de mejora prioritarias.
""")
