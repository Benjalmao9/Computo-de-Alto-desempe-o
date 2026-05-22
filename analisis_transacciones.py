import sys
import unicodedata
from datetime import datetime, timedelta

sys.stdout.reconfigure(encoding="utf-8")

import openpyxl
from text_to_num import alpha2digit

RUTA_EXCEL = r"C:\Users\benja\Downloads\transacciones_financieras.xlsx"
RUTA_RESUMEN = "resumen_transacciones.txt"


def leer_excel(ruta):
    wb = openpyxl.load_workbook(ruta, read_only=True, data_only=True)
    ws = wb.active

    filas = list(ws.iter_rows(values_only=True))
    if not filas:
        return []

    headers = [str(h).strip() if h is not None else "" for h in filas[0]]

    registros = []
    for fila in filas[1:]:
        registro = dict(zip(headers, fila))
        registros.append(registro)

    wb.close()
    return registros


def normalizar_unicode(texto):
    nfd = unicodedata.normalize("NFD", texto)
    return "".join(c for c in nfd if unicodedata.category(c) != "Mn")


MAPA_CATEGORIAS = {
    "restaurante":   "restaurante",
    "restaurantes":  "restaurante",
    "supermercado":  "supermercado",
    "super mercado": "supermercado",
    "electronica":   "electronico",
    "electronicos":  "electronico",
    "electronico":   "electronico",
    "educacion":     "educacion",
}

VARIANTES_CONTADO = {
    "contado",
    "pago unico",
    "una exhibicion",
}
VARIANTES_MSI = {
    "msi",
    "credito msi",
    "meses sin intereses",
}

MAPA_ESTADO = {
    "activa":    "activa",
    "pagada":    "pagada",
    "liquidada": "pagada",
    "cancelada": "cancelada",
}


def limpiar_texto(registro):
    campos_texto = ["id_cliente", "categoria_comercio", "tipo_pago", "estado_compra"]

    for campo in campos_texto:
        valor = registro.get(campo)
        if valor is None:
            registro[campo] = ""
            continue
        valor = str(valor).strip().lower()
        valor = normalizar_unicode(valor)
        registro[campo] = valor

    cat = registro["categoria_comercio"]
    registro["categoria_comercio"] = MAPA_CATEGORIAS.get(cat, cat)

    tp = registro["tipo_pago"]
    if tp in VARIANTES_CONTADO:
        registro["tipo_pago"] = "contado"
    elif tp in VARIANTES_MSI:
        registro["tipo_pago"] = "msi"
    else:
        registro["tipo_pago"] = "desconocido"

    est = registro["estado_compra"]
    registro["estado_compra"] = MAPA_ESTADO.get(est, "desconocido")

    if not registro["id_cliente"]:
        return registro, "id_cliente vacío"
    return registro, None


def limpiar_monto(valor_raw):
    if valor_raw is None:
        return None

    if isinstance(valor_raw, (int, float)):
        return float(valor_raw)

    texto = str(valor_raw).strip()
    texto_limpio = texto.replace("$", "").replace(",", "").strip()
    try:
        return float(texto_limpio)
    except ValueError:
        pass

    try:
        convertido = alpha2digit(texto_limpio, lang="es")
        return float(convertido)
    except Exception:
        pass

    return None


def limpiar_fecha(valor_raw):
    if valor_raw is None:
        return None, None

    if isinstance(valor_raw, datetime):
        return valor_raw.strftime("%Y-%m-%d"), valor_raw.month

    try:
        serial = int(float(str(valor_raw)))
        fecha = datetime(1899, 12, 30) + timedelta(days=serial)
        return fecha.strftime("%Y-%m-%d"), fecha.month
    except Exception:
        return None, None


def limpiar_pagos(registro):
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

    if tipo == "msi" and (msi is None or msi == 0):
        return registro, "meses_sin_intereses inválido para compra MSI"

    if npa is not None and tp_t is not None:
        if npa > tp_t:
            return registro, f"numero_pago_actual ({npa}) > total_pagos ({tp_t})"

    return registro, None


def limpiar_registro(registro):
    registro, error_texto = limpiar_texto(registro)
    if error_texto:
        return registro, error_texto

    monto = limpiar_monto(registro.get("monto_compra"))
    if monto is None:
        return registro, f"monto_compra inválido ({registro.get('monto_compra')!r})"
    registro["monto_compra"] = monto

    fecha_str, mes = limpiar_fecha(registro.get("fecha_compra"))
    if fecha_str is None:
        return registro, f"fecha_compra inválida ({registro.get('fecha_compra')!r})"
    registro["fecha_compra"] = fecha_str
    registro["mes_compra"]   = mes

    registro, error_pagos = limpiar_pagos(registro)
    if error_pagos:
        return registro, error_pagos

    return registro, None


def procesar_registros(registros_raw):
    validos   = []
    invalidos = []

    for i, reg in enumerate(registros_raw, start=2):
        reg_copia = dict(reg)
        reg_limpio, error = limpiar_registro(reg_copia)
        if error:
            invalidos.append({"linea": i, "motivo": error, "datos": reg})
        else:
            validos.append(reg_limpio)

    return validos, invalidos


def contar_por_campo(registros, campo):
    conteo = {}
    for r in registros:
        val = r.get(campo)
        conteo[val] = conteo.get(val, 0) + 1
    return conteo


def sumar_por_campo(registros, campo_agrupacion, campo_suma):
    sumas = {}
    for r in registros:
        clave = r.get(campo_agrupacion)
        valor = r.get(campo_suma, 0) or 0
        sumas[clave] = sumas.get(clave, 0.0) + valor
    return sumas


def analizar_actividad(registros):
    conteo_clientes  = contar_por_campo(registros, "id_cliente")
    monto_clientes   = sumar_por_campo(registros, "id_cliente", "monto_compra")
    conteo_meses     = contar_por_campo(registros, "mes_compra")

    total_monto      = sum(r["monto_compra"] for r in registros)
    ticket_promedio  = total_monto / len(registros) if registros else 0.0

    cliente_mas_tx    = max(conteo_clientes, key=conteo_clientes.get)
    cliente_mas_monto = max(monto_clientes,  key=monto_clientes.get)
    mes_mas_activo    = max(conteo_meses,    key=conteo_meses.get)

    return {
        "cliente_mas_transacciones": (cliente_mas_tx, conteo_clientes[cliente_mas_tx]),
        "cliente_mayor_monto":       (cliente_mas_monto, monto_clientes[cliente_mas_monto]),
        "ticket_promedio":           ticket_promedio,
        "mes_mayor_actividad":       (mes_mas_activo, conteo_meses[mes_mas_activo]),
        "total_transacciones":       len(registros),
        "total_monto":               total_monto,
        "total_clientes_unicos":     len(conteo_clientes),
    }


def analizar_categorias_pagos(registros):
    conteo_cat = contar_por_campo(registros, "categoria_comercio")
    monto_cat  = sumar_por_campo(registros, "categoria_comercio", "monto_compra")

    cat_mas_tx    = max(conteo_cat, key=conteo_cat.get)
    cat_mas_monto = max(monto_cat,  key=monto_cat.get)

    compras_msi = [r for r in registros if r.get("tipo_pago") == "msi"]

    if compras_msi:
        conteo_plazos   = contar_por_campo(compras_msi, "meses_sin_intereses")
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


def categoria_frecuente(registros_cliente):
    conteo = contar_por_campo(registros_cliente, "categoria_comercio")
    return max(conteo, key=conteo.get) if conteo else "desconocida"


def recomendar_promocion_msi(registros):
    recomendaciones = []

    por_cliente = {}
    for r in registros:
        por_cliente.setdefault(r["id_cliente"], []).append(r)

    for cid, txs in por_cliente.items():
        for tx in txs:
            if (tx.get("tipo_pago") == "msi"
                    and tx.get("estado_compra") == "activa"
                    and tx.get("numero_pago_actual") is not None
                    and tx.get("total_pagos") is not None
                    and tx["numero_pago_actual"] >= tx["total_pagos"] - 1):

                cat = categoria_frecuente(por_cliente[cid])
                recomendaciones.append({
                    "id_cliente": cid,
                    "tipo":       "Promoción por MSI próximo a liquidar",
                    "motivo": (
                        f"Pago {tx['numero_pago_actual']}/{tx['total_pagos']} "
                        f"activo en {tx['meses_sin_intereses']} MSI. "
                        f"Categoría frecuente: {cat}. "
                        f"Sugerir promoción en {cat}."
                    ),
                })

    return recomendaciones


def recomendar_aumento_credito(registros):
    recomendaciones = []

    monto_por_cliente    = sumar_por_campo(registros, "id_cliente", "monto_compra")
    n_clientes           = len(monto_por_cliente)
    promedio_por_cliente = (sum(monto_por_cliente.values()) / n_clientes) if n_clientes else 0.0

    por_cliente = {}
    for r in registros:
        por_cliente.setdefault(r["id_cliente"], []).append(r)

    for cid, txs in por_cliente.items():
        total_tx    = len(txs)
        tx_contado  = sum(1 for t in txs if t.get("tipo_pago") == "contado")
        pct_contado = tx_contado / total_tx if total_tx else 0.0
        monto_acum  = monto_por_cliente.get(cid, 0.0)

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
    return recomendar_promocion_msi(registros) + recomendar_aumento_credito(registros)


def formatear_analisis(res_actividad, res_categorias):
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
    lineas = []
    lineas.append("\nREGISTROS INVALIDOS")
    lineas.append(f"  Total descartados: {len(invalidos)}")
    lineas.append(f"  Mostrando primeros {min(10, len(invalidos))} registros:\n")

    for inv in invalidos[:10]:
        lineas.append(f"  Linea {inv['linea']:>4}: {inv['motivo']}")

    return "\n".join(lineas)


def conclusion(res_actividad, res_categorias, recomendaciones, invalidos, total_raw):
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
    with open(ruta, "w", encoding="utf-8") as f:
        for bloque in bloques:
            f.write(bloque)
            f.write("\n")


def main():
    print(f"Leyendo archivo: {RUTA_EXCEL}")

    registros_raw = leer_excel(RUTA_EXCEL)
    total_raw = len(registros_raw)
    print(f"Registros leídos (sin encabezado): {total_raw}")

    validos, invalidos = procesar_registros(registros_raw)
    print(f"Registros válidos  : {len(validos)}")
    print(f"Registros inválidos: {len(invalidos)}")

    if not validos:
        print("No hay registros válidos para analizar. Revise el archivo de entrada.")
        return

    res_actividad  = analizar_actividad(validos)
    res_categorias = analizar_categorias_pagos(validos)

    bloque_analisis = formatear_analisis(res_actividad, res_categorias)
    print(bloque_analisis)

    recomendaciones = generar_recomendaciones(validos)
    bloque_rec      = formatear_recomendaciones(recomendaciones)
    print(bloque_rec)

    bloque_inv = formatear_invalidos(invalidos)
    print(bloque_inv)

    bloque_conclusion = conclusion(
        res_actividad, res_categorias, recomendaciones, invalidos, total_raw
    )
    print(bloque_conclusion)

    guardar_resumen(RUTA_RESUMEN, [
        bloque_analisis,
        bloque_rec,
        bloque_inv,
        bloque_conclusion,
    ])
    print(f"\nResumen guardado en: {RUTA_RESUMEN}")


if __name__ == "__main__":
    main()
