
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

df = pd.read_csv(r"C:\Users\benja\OneDrive\Escritorio\Datasets\calificaciones.txt", header=None, names=["calificacion"])
df["calificacion"] = df["calificacion"].apply(lambda x: convertir(str(x)))
df = df.dropna()

datos = df["calificacion"]

print("--- Primeras 10 líneas ---")
print(df.head(10).to_string(index=False))
print(f"Total de datos extraídos: {len(df)}")

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

print("=== Resumen de calificaciones ===")
print(f"Total:      {total}")
print(f"Promedio:   {promedio:.2f}")
print(f"Mayor:      {mayor}")
print(f"Menor:      {menor}")
print(f"Aprobados:  {aprobados}")
print(f"Reprobados: {reprobados}")
print(f"Desempeño:  {desempeno}")

print("""
--- Conclusión ---
El grupo refleja un desempeño general aceptable, con un promedio que indica que la mayoría
de los estudiantes comprende los contenidos evaluados. Sin embargo, la presencia de alumnos
reprobados señala que existe una parte del grupo que requiere apoyo adicional. La diferencia
entre la calificación máxima y la mínima muestra una dispersión considerable en el rendimiento,
lo que sugiere que las estrategias de enseñanza podrían enfocarse en reducir esa brecha.
""")
