# Práctica 3: Análisis de consumo de agua
import pandas as pd
from text_to_num import text2num

unidades = ["litros", "litro"]

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

df = pd.read_csv(r"C:\Users\benja\OneDrive\Escritorio\Datasets\consumo_agua.txt", header=None, names=["litros"])
df_raw = df.copy()
df["litros"] = df["litros"].apply(lambda x: convertir(str(x).strip()))
invalidos = df_raw[df["litros"].isna()]
df = df.dropna()

datos = df["litros"]

total_registros = len(datos)
total_consumo = datos.sum()
promedio = datos.mean()
mayor = datos.max()
menor = datos.min()
meta_cumplida = (datos >= 2.0).sum()
recomendacion = "Consumo adecuado" if promedio >= 2.0 else "Aumentar el consumo"

resultados = (
    ["--- Datos inválidos ---"] +
    (["Ninguno"] if invalidos.empty else invalidos["litros"].tolist()) +
    [
        "",
        "--- Primeras 10 líneas ---",
        df.head(10).to_string(index=False),
        f"Total de datos extraídos: {len(df)}",
        "",
        "=== Resumen de consumo de agua ===",
        f"Registros:      {total_registros}",
        f"Total:          {total_consumo:.2f} litros",
        f"Promedio:       {promedio:.2f} litros",
        f"Mayor:          {mayor} litros",
        f"Menor:          {menor} litros",
        f"Meta cumplida:  {meta_cumplida} días",
        f"Recomendación:  {recomendacion}",
    ]
)

with open("resultados_consumo_agua.txt", "w", encoding="utf-8") as f:
    for linea in resultados:
        print(linea)
        f.write(str(linea) + "\n")
