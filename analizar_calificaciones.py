import pandas as pd
from text_to_num import alpha2digit

RUTA_CSV = r"C:\Users\benja\Downloads\calificaciones_medio_superior.csv"
df = pd.read_csv(RUTA_CSV, encoding="utf-8-sig")

for col in ["nombre", "apellido", "escuela", "tipo_examen"]:
    df[col] = df[col].astype(str).str.strip().str.title()

ti_norm = (
    df["tipo_institucion"]
    .astype(str)
    .str.strip()
    .str.lower()
    .str.normalize("NFKD")
    .str.encode("ascii", errors="ignore")
    .str.decode("ascii")
)
df["tipo_institucion"] = pd.NA
df.loc[ti_norm.str.contains("publi", na=False), "tipo_institucion"] = "Pública"
df.loc[ti_norm.str.contains("priva", na=False), "tipo_institucion"] = "Privada"

registros_invalidos = []


def convertir_calificacion(valor):
    if valor is None:
        return None
    if isinstance(valor, float) and pd.isna(valor):
        return None
    texto = str(valor).strip()
    if texto == "" or texto.lower() in {"n/a", "na", "null", "none", "nan"}:
        return None

    numero = None
    try:
        numero = float(texto)
    except (ValueError, TypeError):
        try:
            convertido = alpha2digit(texto.lower(), lang="es")
            numero = float(convertido)
        except (ValueError, TypeError):
            return None
    if numero > 10:
        numero = numero / 10
    return numero


valores_normalizados = []
for idx, valor_original in enumerate(df["calificacion"].tolist()):
    resultado = convertir_calificacion(valor_original)
    if resultado is None:
        registros_invalidos.append((idx + 2, valor_original))
    valores_normalizados.append(resultado)

df["calificacion_normalizada"] = valores_normalizados

print("RESULTADO 1 — Distribución de instituciones y estudiantes")
escuelas_publicas = df.loc[df["tipo_institucion"] == "Pública", "escuela"].nunique()
escuelas_privadas = df.loc[df["tipo_institucion"] == "Privada", "escuela"].nunique()
estudiantes_por_tipo = df["tipo_institucion"].value_counts()
print(f"Escuelas únicas públicas : {escuelas_publicas}")
print(f"Escuelas únicas privadas : {escuelas_privadas}")
print("Estudiantes por tipo de institución:")
for tipo, conteo in estudiantes_por_tipo.items():
    print(f"  - {tipo}: {conteo}")

print("\nRESULTADO 2 — Estudiante con la calificación más alta")
df_valido = df.dropna(subset=["calificacion_normalizada"])
mejor = df_valido.loc[df_valido["calificacion_normalizada"].idxmax()]
total_max = (df_valido["calificacion_normalizada"] == mejor["calificacion_normalizada"]).sum()
print(f"Nombre              : {mejor['nombre']}")
print(f"Apellido            : {mejor['apellido']}")
print(f"Escuela             : {mejor['escuela']}")
print(f"Tipo de institución : {mejor['tipo_institucion']}")
print(f"Tipo de examen      : {mejor['tipo_examen']}")
print(f"Calificación        : {mejor['calificacion_normalizada']:.2f}")
print(f"Estudiantes con esta misma calificación: {total_max}")

print("\nRESULTADO 3 — Institución con más aprobados (>= 6.0)")
aprobados = df_valido[df_valido["calificacion_normalizada"] >= 6.0]
conteo_aprobados = aprobados.groupby("escuela").size().sort_values(ascending=False)
escuela_top = conteo_aprobados.index[0]
num_aprobados = int(conteo_aprobados.iloc[0])

df_escuela = df_valido[df_valido["escuela"] == escuela_top]
tipo_inst = df_escuela["tipo_institucion"].mode().iloc[0]
promedio = df_escuela["calificacion_normalizada"].mean()
max_nota = df_escuela["calificacion_normalizada"].max()
mejores_en_escuela = df_escuela[df_escuela["calificacion_normalizada"] == max_nota]

print(f"Institución           : {escuela_top}")
print(f"Tipo                  : {tipo_inst}")
print(f"Número de aprobados   : {num_aprobados}")
print(f"Promedio institucional: {promedio:.2f}")
print(f"Mejor calificación    : {max_nota:.2f}")
print(f"Mejores estudiantes   : {len(mejores_en_escuela)} empatados")
for _, est in mejores_en_escuela.iterrows():
    print(f"  - {est['nombre']} {est['apellido']} "
          f"({est['tipo_examen']}) — {est['calificacion_normalizada']:.2f}")

print("\nREGISTROS INVÁLIDOS")
print(f"Total descartados: {len(registros_invalidos)}")
print("Primeros 10 (línea, valor original):")
for linea, valor in registros_invalidos[:10]:
    print(f"  línea {linea}: {valor!r}")

RUTA_NULOS = r"C:\Users\benja\OneDrive\Escritorio\Computo de alto desemp\valores_nulos.txt"
RUTA_RESULTADOS = r"C:\Users\benja\OneDrive\Escritorio\Computo de alto desemp\resultados.txt"


def exportar_nulos(registros, ruta):
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(f"Total de registros inválidos: {len(registros)}\n")
        f.write(f"{'Línea':>8} | Valor original\n")
        for linea, valor in registros:
            f.write(f"{linea:>8} | {valor!r}\n")


def exportar_resultados(mejor, total_max, escuela_top, tipo_inst,
                       num_aprobados, promedio, mejores_en_escuela, max_nota,
                       escuelas_publicas, escuelas_privadas, estudiantes_por_tipo,
                       total_invalidos, ruta):
    with open(ruta, "w", encoding="utf-8") as f:
        f.write("RESULTADO 1 — Distribución de instituciones y estudiantes\n")
        f.write(f"Escuelas únicas públicas : {escuelas_publicas}\n")
        f.write(f"Escuelas únicas privadas : {escuelas_privadas}\n")
        f.write("Estudiantes por tipo de institución:\n")
        for tipo, conteo in estudiantes_por_tipo.items():
            f.write(f"  - {tipo}: {conteo}\n")

        f.write("\nRESULTADO 2 — Estudiante con la calificación más alta\n")
        f.write(f"Nombre              : {mejor['nombre']}\n")
        f.write(f"Apellido            : {mejor['apellido']}\n")
        f.write(f"Escuela             : {mejor['escuela']}\n")
        f.write(f"Tipo de institución : {mejor['tipo_institucion']}\n")
        f.write(f"Tipo de examen      : {mejor['tipo_examen']}\n")
        f.write(f"Calificación        : {mejor['calificacion_normalizada']:.2f}\n")
        f.write(f"Estudiantes con esta misma calificación: {total_max}\n")

        f.write("\nRESULTADO 3 — Institución con más aprobados (>= 6.0)\n")
        f.write(f"Institución           : {escuela_top}\n")
        f.write(f"Tipo                  : {tipo_inst}\n")
        f.write(f"Número de aprobados   : {num_aprobados}\n")
        f.write(f"Promedio institucional: {promedio:.2f}\n")
        f.write(f"Mejor calificación    : {max_nota:.2f}\n")
        f.write(f"Mejores estudiantes   : {len(mejores_en_escuela)} empatados\n")
        for _, est in mejores_en_escuela.iterrows():
            f.write(f"  - {est['nombre']} {est['apellido']} "
                    f"({est['tipo_examen']}) — {est['calificacion_normalizada']:.2f}\n")

        f.write(f"\nTotal de registros inválidos descartados: {total_invalidos}\n")


exportar_nulos(registros_invalidos, RUTA_NULOS)
exportar_resultados(
    mejor, total_max, escuela_top, tipo_inst, num_aprobados, promedio,
    mejores_en_escuela, max_nota, escuelas_publicas, escuelas_privadas,
    estudiantes_por_tipo, len(registros_invalidos), RUTA_RESULTADOS,
)

print(f"\nValores inválidos -> {RUTA_NULOS}")
print(f"Resultados        -> {RUTA_RESULTADOS}")
