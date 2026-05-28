import pandas as pd
import numpy as np
import time, unicodedata, sys
from multiprocessing import Pool
from collections import Counter
from text_to_num import alpha2digit

sys.stdout.reconfigure(encoding="utf-8")

RUTA_EXCEL   = r"C:\Users\benja\Downloads\transacciones_financieras.xlsx"
RUTA_RESUMEN = "resumen_transacciones.txt"

# ── Mapas de normalización ────────────────────────────────────────────────────
MAPA_CATEGORIAS = {
    "restaurante": "restaurante",   "restaurantes": "restaurante",
    "supermercado": "supermercado", "super mercado": "supermercado",
    "electronica": "electronico",   "electronicos": "electronico",
    "electronico": "electronico",   "educacion": "educacion",
}
VARIANTES_CONTADO = {"contado", "pago unico", "una exhibicion"}
VARIANTES_MSI     = {"msi", "credito msi", "meses sin intereses"}
MAPA_ESTADO       = {"activa": "activa", "pagada": "pagada", "liquidada": "pagada", "cancelada": "cancelada"}

# ── NIVEL DE MÓDULO: procesar_bloque (requerido por pickle en Windows) ────────
def procesar_bloque(bloque):
    parcial = bloque.groupby("id_cliente").agg(
        monto_total=("monto_compra", "sum"),
        num_transacciones=("monto_compra", "count")
    ).reset_index()
    return parcial

normalizar_unicode = lambda t: "".join(c for c in unicodedata.normalize("NFD",str(t)) if unicodedata.category(c)!="Mn")

# ── Funciones de limpieza ─────────────────────────────────────────────────────
def cargar_datos(ruta):
    df = pd.read_excel(ruta)
    print(df.columns.tolist()); print(df.shape); df.info(); print(df.isna().sum())
    return df

def limpiar_dataframe(df):
    n0, df = len(df), df.copy()
    # 2a
    raw = df["monto_compra"].astype(str).str.replace("$","",regex=False).str.replace(",","",regex=False).str.strip()
    df["monto_compra"] = pd.to_numeric(raw, errors="coerce")
    still_bad = df["monto_compra"].isna()
    if still_bad.any():
        df.loc[still_bad, "monto_compra"] = pd.to_numeric(
            raw[still_bad].apply(lambda x: alpha2digit(x, lang="es")), errors="coerce")
    df = df.dropna(subset=["id_cliente","monto_compra"]).copy()
    # 2b
    for c in ["id_cliente","categoria_comercio","tipo_pago","estado_compra"]:
        df[c] = df[c].astype(str).str.strip().str.lower().apply(normalizar_unicode)
    df = df[df["id_cliente"].str.len() > 0].copy()
    df["categoria_comercio"] = df["categoria_comercio"].map(lambda x: MAPA_CATEGORIAS.get(x,x))
    df["tipo_pago"]    = df["tipo_pago"].map(lambda x: "contado" if x in VARIANTES_CONTADO else "msi" if x in VARIANTES_MSI else "desconocido")
    df["estado_compra"] = df["estado_compra"].map(lambda x: MAPA_ESTADO.get(x,"desconocido"))
    # 2c
    df["fecha_compra"] = pd.to_datetime(df["fecha_compra"], errors="coerce")
    df["mes_compra"]   = df["fecha_compra"].dt.month
    df = df.dropna(subset=["fecha_compra"]).copy()
    # 2d
    for c in ["meses_sin_intereses","numero_pago_actual","total_pagos"]:
        df[c] = pd.to_numeric(df[c], errors="coerce").astype("Int64")
    bad = ((df["numero_pago_actual"].notna() & df["total_pagos"].notna() & (df["numero_pago_actual"] > df["total_pagos"])) |
           ((df["tipo_pago"]=="msi") & (df["meses_sin_intereses"].isna() | (df["meses_sin_intereses"]==0)))).fillna(False)
    df = df[~bad].copy()
    # 2e
    print(f"Registros válidos  : {len(df)}\nRegistros inválidos: {n0-len(df)}")
    return df.reset_index(drop=True)

# ── Funciones de análisis secuencial ─────────────────────────────────────────
def analisis_secuencial(df):
    inicio = time.time()

    secuencial = df.groupby("id_cliente").agg(
        monto_total=("monto_compra", "sum"),
        num_transacciones=("monto_compra", "count"),
        promedio_compra=("monto_compra", "mean")
    ).reset_index()

    tiempo_secuencial = time.time() - inicio
    print(f"Tiempo secuencial: {tiempo_secuencial:.6f} s")
    return secuencial, tiempo_secuencial

def analizar_actividad_df(df):
    s  = df.groupby("id_cliente")["monto_compra"].agg(["count","sum"])
    mc = df["mes_compra"].value_counts()
    return {
        "cliente_mas_transacciones": (s["count"].idxmax(), int(s["count"].max())),
        "cliente_mayor_monto":       (s["sum"].idxmax(),   float(s["sum"].max())),
        "ticket_promedio":           float(df["monto_compra"].mean()),
        "mes_mayor_actividad":       (int(mc.idxmax()), int(mc.max())),
        "total_transacciones":       len(df),
        "total_monto":               float(df["monto_compra"].sum()),
        "total_clientes_unicos":     int(df["id_cliente"].nunique()),
    }

def analizar_categorias_pagos_df(df):
    sc  = df.groupby("categoria_comercio")["monto_compra"].agg(["count","sum"])
    msi = df[df["tipo_pago"]=="msi"]
    return {
        "categoria_mas_transacciones": (sc["count"].idxmax(), int(sc["count"].max())),
        "categoria_mayor_monto":       (sc["sum"].idxmax(),   float(sc["sum"].max())),
        "plazo_msi_mas_usado": msi["meses_sin_intereses"].value_counts().idxmax() if len(msi) else None,
        "monto_promedio_msi":  float(msi["monto_compra"].mean()) if len(msi) else 0.0,
        "total_compras_msi":   len(msi),
    }

# ── Funciones de paralelización ──────────────────────────────────────────────
def partir_dataframe(df, num_procesos=4):
    bloques = np.array_split(df, num_procesos)
    for i, bloque in enumerate(bloques):
        print(f"Bloque {i+1}: {len(bloque)} filas")
    return bloques

def ejecutar_paralelo(bloques, num_procesos=4):
    inicio = time.time()
    with Pool(num_procesos) as pool:
        parciales = pool.map(procesar_bloque, bloques)
    tiempo_map = time.time() - inicio
    print(f"Tiempo map paralelo: {tiempo_map:.6f} s")
    return parciales, tiempo_map

def reducir_parciales(parciales):
    todos_parciales = pd.concat(parciales)

    resultado = todos_parciales.groupby("id_cliente").agg(
        monto_total=("monto_total", "sum"),
        num_transacciones=("num_transacciones", "sum")
    ).reset_index()

    resultado["promedio_compra"] = (
        resultado["monto_total"] / resultado["num_transacciones"]
    )
    return resultado

def comparar_resultados(secuencial, resultado, tiempo_secuencial, tiempo_map):
    print(f"Tiempo secuencial : {tiempo_secuencial:.6f} s")
    print(f"Tiempo paralelo   : {tiempo_map:.6f} s")

    validacion = secuencial.merge(
        resultado,
        on="id_cliente",
        suffixes=("_seq", "_par")
    )
    validacion["diff_monto"] = (
        validacion["monto_total_seq"] - validacion["monto_total_par"]
    ).abs()
    validacion["coincide"] = validacion["diff_monto"] < 0.01
    print(f"Resultados coinciden: {validacion['coincide'].all()}")
    print(validacion.head().to_string())
    return validacion

# ── Funciones de recomendaciones ─────────────────────────────────────────────
def recomendar_promocion_msi(df):
    cat_f = df.groupby("id_cliente")["categoria_comercio"].agg(lambda x: x.value_counts().idxmax())
    mask  = ((df["tipo_pago"]=="msi") & (df["estado_compra"]=="activa") &
             df["numero_pago_actual"].notna() & df["total_pagos"].notna() &
             (df["numero_pago_actual"] >= df["total_pagos"]-1)).fillna(False)
    return [{"id_cliente": r["id_cliente"],
             "tipo": "Promoción por MSI próximo a liquidar",
             "motivo": (f"Pago {r['numero_pago_actual']}/{r['total_pagos']} activo en "
                        f"{r['meses_sin_intereses']} MSI. Cat. frecuente: "
                        f"{(cat:=cat_f.get(r['id_cliente'],'desconocida'))}. Sugerir promoción en {cat}.")}
            for _, r in df[mask].iterrows()]

def recomendar_aumento_credito(df):
    s = df.groupby("id_cliente").agg(
        monto_acum=("monto_compra","sum"),
        total_tx=("monto_compra","count"),
        tx_contado=("tipo_pago", lambda x: (x=="contado").sum())
    ).reset_index()
    prom     = float(s["monto_acum"].mean()) if len(s) else 0.0
    s["pct"] = s["tx_contado"] / s["total_tx"]
    aumento  = lambda p: 20 if p>=.9 else 15 if p>=.8 else 10
    return [{"id_cliente": r["id_cliente"],
             "tipo": f"Aumento de línea de crédito {aumento(r['pct'])}%",
             "motivo": (f"{r['pct']*100:.1f}% contado ({int(r['tx_contado'])}/{int(r['total_tx'])} tx). "
                        f"Acum: ${r['monto_acum']:,.2f} (prom: ${prom:,.2f}). "
                        f"Aumento sugerido: {aumento(r['pct'])}%.")}
            for _, r in s[(s["pct"]>=.7) & (s["monto_acum"]>prom)].iterrows()]

# ── Funciones de formato y salida ────────────────────────────────────────────
def formatear_analisis(ra, rc):
    (cmt,n_tx),(cmm,monto),(mes,n_mes) = ra["cliente_mas_transacciones"],ra["cliente_mayor_monto"],ra["mes_mayor_actividad"]
    (cat_tx,n_cat),(cat_m,m_cat) = rc["categoria_mas_transacciones"],rc["categoria_mayor_monto"]
    msi_l = ([f"  Plazo MSI mas utilizado        : {rc['plazo_msi_mas_usado']} meses",
              f"  Monto promedio en MSI          : ${rc['monto_promedio_msi']:,.2f}"]
             if rc["plazo_msi_mas_usado"] is not None else ["  Sin compras MSI en el dataset."])
    return "\n".join([
        "ANALISIS DE TRANSACCIONES FINANCIERAS",
        "\nACTIVIDAD DE COMPRA",
        f"  Total de transacciones validas : {ra['total_transacciones']}",
        f"  Numero de clientes unicos      : {ra['total_clientes_unicos']}",
        f"  Monto total procesado          : ${ra['total_monto']:,.2f}",
        f"  Cliente con mas transacciones  : {cmt} ({n_tx} compras)",
        f"  Cliente con mayor monto acum.  : {cmm} (${monto:,.2f})",
        f"  Ticket promedio general        : ${ra['ticket_promedio']:,.2f}",
        f"  Mes con mayor actividad        : {mes:02d} ({n_mes} transacciones)",
        "\nCATEGORIAS Y PAGOS",
        f"  Categoria con mas transacciones: {cat_tx} ({n_cat})",
        f"  Categoria con mayor monto      : {cat_m} (${m_cat:,.2f})",
        f"  Total compras MSI              : {rc['total_compras_msi']}",
        *msi_l
    ])

def formatear_recomendaciones(recs):
    if not recs: return "\nRECOMENDACIONES\n  No se generaron recomendaciones con los criterios actuales."
    c = Counter(r["tipo"] for r in recs)
    return "\nRECOMENDACIONES\n" + "\n".join(f"  {t:<44}: {n} cliente(s)" for t,n in c.items())

formatear_invalidos = lambda n: (f"\nREGISTROS INVALIDOS\n  Total descartados: {n}\n"
                                  f"  (Eliminados: montos/fechas invalidos, id_cliente vacio, inconsistencias MSI/pagos.)")

def guardar_resumen(ruta, bloques):
    with open(ruta, "w", encoding="utf-8") as f: f.write("\n".join(bloques) + "\n")

# ── Punto de entrada — OBLIGATORIO en Windows para multiprocessing ────────────
if __name__ == "__main__":
    print(f"Cargando: {RUTA_EXCEL}")
    df_raw    = cargar_datos(RUTA_EXCEL)
    total_raw = len(df_raw)
    print(f"Total registros leidos: {total_raw}")

    print("\n--- ETAPA 2: Limpieza ---")
    df = limpiar_dataframe(df_raw)
    if df.empty: print("Sin registros validos."); sys.exit(1)
    num_inv = total_raw - len(df)

    print("\n--- ETAPA 3: Analisis Secuencial ---")
    secuencial, t_seq = analisis_secuencial(df)

    NUM_PROCESOS = 4
    print("\n--- ETAPA 4: Particion ---")
    bloques = partir_dataframe(df, NUM_PROCESOS)
    # numpy ≥2.0 convierte el DataFrame a ndarray; reconstruir como DataFrames
    bloques = [df.iloc[idx] for idx in np.array_split(np.arange(len(df)), NUM_PROCESOS)]

    print("\n--- ETAPA 6: Ejecucion Paralela ---")
    parciales, t_par = ejecutar_paralelo(bloques, NUM_PROCESOS)

    print("\n--- ETAPA 7: Reduccion ---")
    resultado = reducir_parciales(parciales)

    print("\n--- ETAPA 8: Comparacion ---")
    comparar_resultados(secuencial, resultado, t_seq, t_par)

    ra, rc = analizar_actividad_df(df), analizar_categorias_pagos_df(df)
    recs   = recomendar_promocion_msi(df) + recomendar_aumento_credito(df)
    textos = [formatear_analisis(ra, rc), formatear_recomendaciones(recs),
              formatear_invalidos(num_inv)]

    for t in textos: print(t)
    guardar_resumen(RUTA_RESUMEN, textos)
    print(f"\nResumen guardado en: {RUTA_RESUMEN}")
