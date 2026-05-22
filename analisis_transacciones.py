# =============================================================================
# analisis_transacciones.py
# Análisis de transacciones financieras simuladas desde un archivo Excel.
# Restricciones: solo openpyxl, unicodedata, datetime, text2num.
# =============================================================================

import sys
import unicodedata
from datetime import datetime, timedelta

# Forzar UTF-8 en la salida estándar para evitar errores en consolas Windows
# que usan cp1252 cuando el texto contiene caracteres especiales.
sys.stdout.reconfigure(encoding="utf-8")

import openpyxl
from text_to_num import alpha2digit

# ----------------------------------------------------------------------------
# CONFIGURACIÓN — ajustar la ruta antes de ejecutar
# ----------------------------------------------------------------------------
RUTA_EXCEL = r"C:\Users\benja\Downloads\transacciones_financieras.xlsx"
RUTA_RESUMEN = "resumen_transacciones.txt"


# ============================================================================
# SECCIÓN 1: LECTURA
# ============================================================================

def leer_excel(ruta):
    """
    Lee el archivo Excel con openpyxl en modo read-only.
    Devuelve una lista de diccionarios, uno por fila de datos.
    La primera fila se trata como encabezados.
    """
    wb = openpyxl.load_workbook(ruta, read_only=True, data_only=True)
    ws = wb.active

    filas = list(ws.iter_rows(values_only=True))
    if not filas:
        return []

    # Primera fila → encabezados
    headers = [str(h).strip() if h is not None else "" for h in filas[0]]

    registros = []
    for fila in filas[1:]:
        # Cada fila se convierte en diccionario usando zip con los encabezados
        registro = dict(zip(headers, fila))
        registros.append(registro)

    wb.close()
    return registros


# ============================================================================
# SECCIÓN 2: LIMPIEZA — una función por tipo de dato
# ============================================================================

def normalizar_unicode(texto):
    """
    Elimina acentos y caracteres combinantes usando NFD.
    Ejemplo: "crédito" → "credito", "única" → "unica".
    """
    nfd = unicodedata.normalize("NFD", texto)
    # Filtramos los combining characters (categoría Mn)
    return "".join(c for c in nfd if unicodedata.category(c) != "Mn")


# ---- Mapas de normalización -------------------------------------------------

# Categorías equivalentes → forma canónica
# Solo se unifican grupos semánticamente equivalentes según el enunciado;
# el resto de categorías se conserva tal como viene (ya normalizada sin acentos).
MAPA_CATEGORIAS = {
    # restaurante / restaurantes
    "restaurante":   "restaurante",
    "restaurantes":  "restaurante",
    # supermercado
    "supermercado":  "supermercado",
    "super mercado": "supermercado",
    # electrónica / electrónico
    "electronica":   "electronico",
    "electronicos":  "electronico",
    "electronico":   "electronico",
    # educación (con y sin tilde — la NFD dejará "educacion" en ambas formas)
    "educacion":     "educacion",
}

# Variantes de tipo_pago → tres valores canónicos.
# Se comparan DESPUÉS de normalizar unicode (sin acentos) y en minúsculas,
# por eso las entradas no llevan tildes.
VARIANTES_CONTADO = {
    "contado",
    "pago unico",       # "pago único" normalizado
    "una exhibicion",   # "una exhibición" normalizado
}
VARIANTES_MSI = {
    "msi",
    "credito msi",          # "crédito msi" normalizado
    "meses sin intereses",
}

# Variantes de estado_compra → forma canónica
MAPA_ESTADO = {
    "activa":     "activa",
    "pagada":     "pagada",
    "liquidada":  "pagada",   # "liquidada" se trata como "pagada"
    "cancelada":  "cancelada",
}


def limpiar_texto(registro):
    """
    Limpia los campos de texto:
      - strip + lower
      - normalización de acentos (NFD)
      - unificación de categorías, tipo_pago y estado_compra
    Devuelve el registro modificado y un mensaje de error si hay campos críticos vacíos.
    """
    campos_texto = ["id_cliente", "categoria_comercio", "tipo_pago", "estado_compra"]

    for campo in campos_texto:
        valor = registro.get(campo)
        if valor is None:
            registro[campo] = ""
            continue
        valor = str(valor).strip().lower()
        valor = normalizar_unicode(valor)
        registro[campo] = valor

    # -- Unificar categoria_comercio ------------------------------------------
    cat = registro["categoria_comercio"]
    registro["categoria_comercio"] = MAPA_CATEGORIAS.get(cat, cat)

    # -- Unificar tipo_pago → "contado" | "msi" | "desconocido" ---------------
    tp = registro["tipo_pago"]
    if tp in VARIANTES_CONTADO:
        registro["tipo_pago"] = "contado"
    elif tp in VARIANTES_MSI:
        registro["tipo_pago"] = "msi"
    else:
        registro["tipo_pago"] = "desconocido"

    # -- Unificar estado_compra ------------------------------------------------
    est = registro["estado_compra"]
    registro["estado_compra"] = MAPA_ESTADO.get(est, "desconocido")

    # Verificación de campos críticos
    if not registro["id_cliente"]:
        return registro, "id_cliente vacío"
    return registro, None


def limpiar_monto(valor_raw):
    """
    Convierte el campo monto_compra a float.
    Estrategia:
      1. Si ya es numérico (int/float de Excel), convertir directo.
      2. Si es texto, quitar '$' y ',' e intentar float().
      3. Si falla, intentar text2num (texto en español → número).
      4. Si todo falla, retornar None.
    """
    if valor_raw is None:
        return None

    # Caso 1: valor numérico nativo de Excel
    if isinstance(valor_raw, (int, float)):
        return float(valor_raw)

    # Caso 2: texto con símbolos monetarios
    texto = str(valor_raw).strip()
    texto_limpio = texto.replace("$", "").replace(",", "").strip()
    try:
        return float(texto_limpio)
    except ValueError:
        pass

    # Caso 3: texto en español ("ocho mil quinientos")
    try:
        # alpha2digit convierte palabras numéricas a dígitos en el texto
        convertido = alpha2digit(texto_limpio, lang="es")
        return float(convertido)
    except Exception:
        pass

    # Caso 4: no se pudo convertir
    return None


def limpiar_fecha(valor_raw):
    """
    Convierte el campo fecha_compra a (fecha_str "YYYY-MM-DD", mes_int).
    openpyxl con data_only=True entrega las fechas como objetos datetime
    nativos de Python; también se acepta el número serial de Excel como
    fallback (epoch 1899-12-30).
    Retorna (None, None) si no se puede interpretar el valor.
    """
    if valor_raw is None:
        return None, None

    # Caso 1: ya es un objeto datetime (lo más común con openpyxl data_only)
    if isinstance(valor_raw, datetime):
        return valor_raw.strftime("%Y-%m-%d"), valor_raw.month

    # Caso 2: número serial de Excel
    try:
        serial = int(float(str(valor_raw)))
        fecha = datetime(1899, 12, 30) + timedelta(days=serial)
        return fecha.strftime("%Y-%m-%d"), fecha.month
    except Exception:
        return None, None


def limpiar_pagos(registro):
    """
    Convierte meses_sin_intereses, numero_pago_actual y total_pagos a entero.
    Valida que numero_pago_actual <= total_pagos.
    Si tipo_pago es "contado", meses_sin_intereses = 0 es aceptable.
    Retorna (registro_modificado, mensaje_error_o_None).
    """
    campos_entero = ["meses_sin_intereses", "numero_pago_actual", "total_pagos"]

    for campo in campos_entero:
        val = registro.get(campo)
        if val is None:
            registro[campo] = None
            continue
        try:
            registro[campo] = int(float(str(val)))
        except (ValueError, TypeError):
            registro[campo] = None

    msi  = registro["meses_sin_intereses"]
    npa  = registro["numero_pago_actual"]
    tp_t = registro["total_pagos"]
    tipo = registro.get("tipo_pago", "")

    # meses_sin_intereses = 0 es válido si es compra de contado
    if tipo == "msi" and (msi is None or msi == 0):
        return registro, "meses_sin_intereses inválido para compra MSI"

    # numero_pago_actual no puede superar total_pagos
    if npa is not None and tp_t is not None:
        if npa > tp_t:
            return registro, (
                f"numero_pago_actual ({npa}) > total_pagos ({tp_t})"
            )

    return registro, None


# ---- Orquestador de limpieza ------------------------------------------------

def limpiar_registro(registro):
    """
    Aplica todas las funciones de limpieza a un registro.
    Retorna (registro_limpio, error) donde error es None si el registro es válido.
    """
    # 1. Texto
    registro, error_texto = limpiar_texto(registro)
    if error_texto:
        return registro, error_texto

    # 2. Monto
    monto = limpiar_monto(registro.get("monto_compra"))
    if monto is None:
        return registro, f"monto_compra inválido ({registro.get('monto_compra')!r})"
    registro["monto_compra"] = monto

    # 3. Fecha
    fecha_str, mes = limpiar_fecha(registro.get("fecha_compra"))
    if fecha_str is None:
        return registro, f"fecha_compra inválida ({registro.get('fecha_compra')!r})"
    registro["fecha_compra"] = fecha_str
    registro["mes_compra"]   = mes

    # 4. Pagos
    registro, error_pagos = limpiar_pagos(registro)
    if error_pagos:
        return registro, error_pagos

    return registro, None


def procesar_registros(registros_raw):
    """
    Itera sobre los registros crudos, aplica la limpieza y separa
    válidos de inválidos.
    Retorna (lista_validos, lista_invalidos).
    """
    validos   = []
    invalidos = []

    for i, reg in enumerate(registros_raw, start=2):  # start=2 porque fila 1 son headers
        # Trabajamos sobre una copia para no mutar el original
        reg_copia = dict(reg)
        reg_limpio, error = limpiar_registro(reg_copia)
        if error:
            invalidos.append({"linea": i, "motivo": error, "datos": reg})
        else:
            validos.append(reg_limpio)

    return validos, invalidos


# ============================================================================
# SECCIÓN 3: ANÁLISIS
# ============================================================================

def contar_por_campo(registros, campo):
    """Cuenta cuántas veces aparece cada valor distinto en un campo."""
    conteo = {}
    for r in registros:
        val = r.get(campo)
        conteo[val] = conteo.get(val, 0) + 1
    return conteo


def sumar_por_campo(registros, campo_agrupacion, campo_suma):
    """Suma los valores de campo_suma agrupando por campo_agrupacion."""
    sumas = {}
    for r in registros:
        clave = r.get(campo_agrupacion)
        valor = r.get(campo_suma, 0) or 0
        sumas[clave] = sumas.get(clave, 0.0) + valor
    return sumas


def analizar_actividad(registros):
    """
    Calcula:
      - Cliente con más transacciones
      - Cliente con mayor monto acumulado
      - Ticket promedio general
      - Mes con mayor actividad
    """
    conteo_clientes = contar_por_campo(registros, "id_cliente")
    monto_clientes  = sumar_por_campo(registros, "id_cliente", "monto_compra")
    conteo_meses    = contar_por_campo(registros, "mes_compra")

    total_monto = sum(r["monto_compra"] for r in registros)
    ticket_promedio = total_monto / len(registros) if registros else 0.0

    cliente_mas_tx   = max(conteo_clientes, key=conteo_clientes.get)
    cliente_mas_monto = max(monto_clientes, key=monto_clientes.get)
    mes_mas_activo   = max(conteo_meses, key=conteo_meses.get)

    return {
        "cliente_mas_transacciones":  (cliente_mas_tx, conteo_clientes[cliente_mas_tx]),
        "cliente_mayor_monto":        (cliente_mas_monto, monto_clientes[cliente_mas_monto]),
        "ticket_promedio":            ticket_promedio,
        "mes_mayor_actividad":        (mes_mas_activo, conteo_meses[mes_mas_activo]),
        "total_transacciones":        len(registros),
        "total_monto":                total_monto,
        "total_clientes_unicos":      len(conteo_clientes),
    }


def analizar_categorias_pagos(registros):
    """
    Calcula:
      - Categoría con más transacciones
      - Categoría con mayor monto acumulado
      - Plazo de MSI más utilizado
      - Monto promedio en compras MSI
    """
    conteo_cat = contar_por_campo(registros, "categoria_comercio")
    monto_cat  = sumar_por_campo(registros, "categoria_comercio", "monto_compra")

    cat_mas_tx    = max(conteo_cat, key=conteo_cat.get)
    cat_mas_monto = max(monto_cat, key=monto_cat.get)

    # Filtrar solo compras MSI
    compras_msi = [r for r in registros if r.get("tipo_pago") == "msi"]

    if compras_msi:
        conteo_plazos = contar_por_campo(compras_msi, "meses_sin_intereses")
        plazo_mas_usado = max(conteo_plazos, key=conteo_plazos.get)
        monto_prom_msi  = sum(r["monto_compra"] for r in compras_msi) / len(compras_msi)
    else:
        plazo_mas_usado = None
        monto_prom_msi  = 0.0

    return {
        "categoria_mas_transacciones": (cat_mas_tx, conteo_cat[cat_mas_tx]),
        "categoria_mayor_monto":       (cat_mas_monto, monto_cat[cat_mas_monto]),
        "plazo_msi_mas_usado":         plazo_mas_usado,
        "monto_promedio_msi":          monto_prom_msi,
        "total_compras_msi":           len(compras_msi),
    }


# ============================================================================
# SECCIÓN 4: RECOMENDACIONES
# ============================================================================

def categoria_frecuente(registros_cliente):
    """Retorna la categoría de compra más frecuente de un cliente."""
    conteo = contar_por_campo(registros_cliente, "categoria_comercio")
    return max(conteo, key=conteo.get) if conteo else "desconocida"


def recomendar_promocion_msi(registros):
    """
    Regla: cliente con tipo_pago="msi", estado_compra="activa",
    y numero_pago_actual >= total_pagos - 1 (último o penúltimo pago).
    Recomendación basada en la categoría más frecuente del cliente.
    """
    recomendaciones = []

    # Agrupar todos los registros por cliente
    por_cliente = {}
    for r in registros:
        cid = r["id_cliente"]
        por_cliente.setdefault(cid, []).append(r)

    for cid, txs in por_cliente.items():
        for tx in txs:
            if (tx.get("tipo_pago") == "msi"
                    and tx.get("estado_compra") == "activa"
                    and tx.get("numero_pago_actual") is not None
                    and tx.get("total_pagos") is not None
                    and tx["numero_pago_actual"] >= tx["total_pagos"] - 1):

                cat = categoria_frecuente(por_cliente[cid])
                recomendaciones.append({
                    "id_cliente":  cid,
                    "tipo":        "Promoción por MSI próximo a liquidar",
                    "motivo": (
                        f"Pago {tx['numero_pago_actual']}/{tx['total_pagos']} "
                        f"activo en {tx['meses_sin_intereses']} MSI. "
                        f"Categoría frecuente: {cat}. "
                        f"Sugerir promoción en {cat}."
                    ),
                })

    return recomendaciones


def recomendar_aumento_credito(registros):
    """
    Regla: clientes que pagan principalmente de contado y cuyo monto acumulado
    supera el promedio general por cliente.
      70–79 % contado → +10 %
      80–89 % contado → +15 %
      90 %+  contado → +20 %
    """
    recomendaciones = []

    # Monto promedio por cliente
    monto_por_cliente = sumar_por_campo(registros, "id_cliente", "monto_compra")
    n_clientes = len(monto_por_cliente)
    promedio_por_cliente = (sum(monto_por_cliente.values()) / n_clientes) if n_clientes else 0.0

    # Agrupar por cliente
    por_cliente = {}
    for r in registros:
        por_cliente.setdefault(r["id_cliente"], []).append(r)

    for cid, txs in por_cliente.items():
        total_tx   = len(txs)
        tx_contado = sum(1 for t in txs if t.get("tipo_pago") == "contado")
        pct_contado = tx_contado / total_tx if total_tx else 0.0

        monto_acum = monto_por_cliente.get(cid, 0.0)

        # Solo si supera el promedio y tiene mayoría de pagos de contado (≥70 %)
        if pct_contado >= 0.70 and monto_acum > promedio_por_cliente:
            if pct_contado >= 0.90:
                aumento = 20
            elif pct_contado >= 0.80:
                aumento = 15
            else:
                aumento = 10

            recomendaciones.append({
                "id_cliente": cid,
                "tipo":       f"Aumento de línea de crédito {aumento}%",
                "motivo": (
                    f"{pct_contado*100:.1f}% de compras de contado "
                    f"({tx_contado}/{total_tx} transacciones). "
                    f"Monto acumulado: ${monto_acum:,.2f} "
                    f"(promedio: ${promedio_por_cliente:,.2f}). "
                    f"Supera el promedio → aumento sugerido del {aumento}%."
                ),
            })

    return recomendaciones


def generar_recomendaciones(registros):
    """Combina ambos tipos de recomendaciones en una sola lista."""
    rec_msi     = recomendar_promocion_msi(registros)
    rec_credito = recomendar_aumento_credito(registros)
    return rec_msi + rec_credito


# ============================================================================
# SECCIÓN 5 y 6: REPORTE DE INVÁLIDOS Y GUARDADO EN .TXT
# ============================================================================

def formatear_analisis(res_actividad, res_categorias):
    """Construye el bloque de texto del análisis para mostrar en pantalla y guardar."""
    lineas = []
    lineas.append("ANALISIS DE TRANSACCIONES FINANCIERAS")

    lineas.append("\nACTIVIDAD DE COMPRA")
    cmt, n_tx  = res_actividad["cliente_mas_transacciones"]
    cmm, monto = res_actividad["cliente_mayor_monto"]
    mes, n_mes = res_actividad["mes_mayor_actividad"]
    lineas.append(f"  Total de transacciones validas : {res_actividad['total_transacciones']}")
    lineas.append(f"  Numero de clientes unicos      : {res_actividad['total_clientes_unicos']}")
    lineas.append(f"  Monto total procesado          : ${res_actividad['total_monto']:,.2f}")
    lineas.append(f"  Cliente con mas transacciones  : {cmt} ({n_tx} compras)")
    lineas.append(f"  Cliente con mayor monto acum.  : {cmm} (${monto:,.2f})")
    lineas.append(f"  Ticket promedio general        : ${res_actividad['ticket_promedio']:,.2f}")
    lineas.append(f"  Mes con mayor actividad        : {mes:02d} ({n_mes} transacciones)")

    lineas.append("\nCATEGORIAS Y PAGOS")
    cat_tx, n_cat = res_categorias["categoria_mas_transacciones"]
    cat_m,  m_cat = res_categorias["categoria_mayor_monto"]
    lineas.append(f"  Categoria con mas transacciones: {cat_tx} ({n_cat})")
    lineas.append(f"  Categoria con mayor monto      : {cat_m} (${m_cat:,.2f})")
    lineas.append(f"  Total compras MSI              : {res_categorias['total_compras_msi']}")
    if res_categorias["plazo_msi_mas_usado"] is not None:
        lineas.append(f"  Plazo MSI mas utilizado        : {res_categorias['plazo_msi_mas_usado']} meses")
        lineas.append(f"  Monto promedio en MSI          : ${res_categorias['monto_promedio_msi']:,.2f}")
    else:
        lineas.append("  Sin compras MSI en el dataset.")

    return "\n".join(lineas)


def formatear_recomendaciones(recomendaciones):
    """Construye el bloque de texto de recomendaciones."""
    lineas = []
    lineas.append("\nRECOMENDACIONES")

    if not recomendaciones:
        lineas.append("  No se generaron recomendaciones con los criterios actuales.")
        return "\n".join(lineas)

    for i, rec in enumerate(recomendaciones, 1):
        lineas.append(f"\n  [{i}] Cliente : {rec['id_cliente']}")
        lineas.append(f"       Tipo    : {rec['tipo']}")
        lineas.append(f"       Motivo  : {rec['motivo']}")

    return "\n".join(lineas)


def formatear_invalidos(invalidos):
    """Construye el bloque de texto de registros inválidos."""
    lineas = []
    lineas.append("\nREGISTROS INVALIDOS")
    lineas.append(f"  Total descartados: {len(invalidos)}")
    lineas.append(f"  Mostrando primeros {min(10, len(invalidos))} registros:\n")

    for inv in invalidos[:10]:
        lineas.append(f"  Linea {inv['linea']:>4}: {inv['motivo']}")

    return "\n".join(lineas)


def conclusion(res_actividad, res_categorias, recomendaciones, invalidos, total_raw):
    """Genera un bloque interpretando los resultados del análisis."""
    pct_invalidos = len(invalidos) / total_raw * 100 if total_raw else 0
    n_rec_msi     = sum(1 for r in recomendaciones if "MSI" in r["tipo"])
    n_rec_credito = sum(
        1 for r in recomendaciones
        if "credito" in normalizar_unicode(r["tipo"].lower())
    )

    cat_top, _ = res_categorias["categoria_mas_transacciones"]
    mes_top, _ = res_actividad["mes_mayor_actividad"]

    return (
        f"\nCONCLUSION DEL ANALISIS\n"
        f"  El dataset muestra mayor concentracion de compras en la categoria\n"
        f"  '{cat_top}', con el mes {mes_top:02d} como periodo de mayor actividad.\n"
        f"  Se identificaron {len(recomendaciones)} recomendaciones en total:\n"
        f"  {n_rec_msi} promociones por MSI proximo a liquidarse y {n_rec_credito}\n"
        f"  aumentos de linea de credito para clientes de alto perfil de contado.\n"
        f"  La limpieza fue esencial: {pct_invalidos:.1f}% de los registros ({len(invalidos)})\n"
        f"  presentaron errores en montos, fechas o inconsistencias de pago,\n"
        f"  lo que habria distorsionado promedios y conteos sin correccion previa.\n"
        f"  Limitacion principal: el analisis es estatico (snapshot); no detecta\n"
        f"  cambios de comportamiento en el tiempo ni fraudes por patrones anomalos."
    )


def guardar_resumen(ruta, bloques):
    """Escribe todos los bloques de texto en el archivo de resumen."""
    with open(ruta, "w", encoding="utf-8") as f:
        for bloque in bloques:
            f.write(bloque)
            f.write("\n")


# ============================================================================
# PUNTO DE ENTRADA PRINCIPAL
# ============================================================================

def main():
    print(f"Leyendo archivo: {RUTA_EXCEL}")

    # -- Lectura --------------------------------------------------------------
    registros_raw = leer_excel(RUTA_EXCEL)
    total_raw = len(registros_raw)
    print(f"Registros leídos (sin encabezado): {total_raw}")

    # -- Limpieza -------------------------------------------------------------
    validos, invalidos = procesar_registros(registros_raw)
    print(f"Registros válidos  : {len(validos)}")
    print(f"Registros inválidos: {len(invalidos)}")

    if not validos:
        print("No hay registros válidos para analizar. Revise el archivo de entrada.")
        return

    # -- Análisis -------------------------------------------------------------
    res_actividad   = analizar_actividad(validos)
    res_categorias  = analizar_categorias_pagos(validos)

    bloque_analisis = formatear_analisis(res_actividad, res_categorias)
    print(bloque_analisis)

    # -- Recomendaciones ------------------------------------------------------
    recomendaciones    = generar_recomendaciones(validos)
    bloque_rec         = formatear_recomendaciones(recomendaciones)
    print(bloque_rec)

    # -- Registros inválidos --------------------------------------------------
    bloque_inv = formatear_invalidos(invalidos)
    print(bloque_inv)

    # -- Conclusión -----------------------------------------------------------
    bloque_conclusion = conclusion(
        res_actividad, res_categorias, recomendaciones, invalidos, total_raw
    )
    print(bloque_conclusion)

    # -- Guardar resumen .txt -------------------------------------------------
    guardar_resumen(RUTA_RESUMEN, [
        bloque_analisis,
        bloque_rec,
        bloque_inv,
        bloque_conclusion,
    ])
    print(f"\nResumen guardado en: {RUTA_RESUMEN}")


if __name__ == "__main__":
    main()
