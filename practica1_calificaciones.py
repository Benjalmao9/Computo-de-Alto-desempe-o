
import pandas as pd
from text_to_num import text2num

def convertir(texto):
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

df = pd.read_csv(r"C:\Users\benja\OneDrive\Escritorio\Datasets\calificaciones.txt", header=None, names=["calificacion"])
df_raw = df.copy()
df["calificacion"] = df["calificacion"].apply(lambda x: convertir(str(x).strip()))
invalidos = df_raw[df["calificacion"].isna()]
df = df.dropna()

datos = df["calificacion"]

total = len(datos)
promedio = datos.mean()
mayor = datos.max()
menor = datos.min()
aprobados = (datos >= 6.0).sum()
reprobados = total - aprobados

if promedio >= 9:
    desempeno = "Excelente"
elif promedio >= 7:
    desempeno = "Bueno"
elif promedio >= 6:
    desempeno = "Regular"
else:
    desempeno = "Requiere atención"

resultados = (
    ["--- Datos inválidos ---"] +
    (["Ninguno"] if invalidos.empty else invalidos["calificacion"].tolist()) +
    [
        "",
        "--- Primeras 10 líneas ---",
        df.head(10).to_string(index=False),
        f"Total de datos extraídos: {len(df)}",
        "",
        "=== Resumen de calificaciones ===",
        f"Total:      {total}",
        f"Promedio:   {promedio:.2f}",
        f"Mayor:      {mayor}",
        f"Menor:      {menor}",
        f"Aprobados:  {aprobados}",
        f"Reprobados: {reprobados}",
        f"Desempeño:  {desempeno}",
    ]
)

with open("resultados_calificaciones.txt", "w", encoding="utf-8") as f:
    for linea in resultados:
        print(linea)
        f.write(str(linea) + "\n")
