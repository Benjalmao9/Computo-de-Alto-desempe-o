# Práctica 4: Registro de actividad física
import pandas as pd
from text_to_num import text2num

unidades = ["minutos", "minuto", "mins", "min"]

def limpiar(texto):
    for unidad in unidades:
        texto = texto.replace(unidad, "").strip()
    return texto

def convertir(texto):
    texto = limpiar(texto)
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
df_raw = df.copy()
df["minutos"] = df["minutos"].apply(lambda x: convertir(str(x).strip()))
invalidos = df_raw[df["minutos"].isna()]
df = df.dropna()

datos = df["minutos"]

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

resultados = (
    ["--- Datos inválidos ---"] +
    (["Ninguno"] if invalidos.empty else invalidos["minutos"].tolist()) +
    [
        "",
        "--- Primeras 10 líneas ---",
        df.head(10).to_string(index=False),
        f"Total de datos extraídos: {len(df)}",
        "",
        "=== Resumen de actividad física ===",
        f"Registros:          {total_registros}",
        f"Total:              {total_minutos} minutos",
        f"Promedio:           {promedio:.2f} minutos",
        f"Mayor:              {mayor} minutos",
        f"Menor:              {menor} minutos",
        f"Días sin ejercicio: {dias_sin_ejercicio}",
        f"Nivel:              {nivel}",
        "",
        "--- Conclusión ---",
        "El análisis de la actividad física diaria permite identificar si la persona mantiene hábitos",
        "de ejercicio consistentes y suficientes para su salud. El número de días sin ejercicio es un",
        "indicador clave: una cantidad elevada sugiere falta de constancia que puede afectar el bienestar",
        "físico a largo plazo. El promedio diario determina el nivel general de actividad, y en caso de",
        "ser bajo o moderado, se recomienda establecer rutinas más regulares para alcanzar los 30 minutos",
        "diarios recomendados por los estándares de salud.",
    ]
)

with open("resultados_actividad_fisica.txt", "w", encoding="utf-8") as f:
    for linea in resultados:
        print(linea)
        f.write(str(linea) + "\n")
