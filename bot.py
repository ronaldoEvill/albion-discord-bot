import asyncio
import datetime
import os
from threading import Thread
from flask import Flask
import discord
from discord.ext import commands
import requests

app = Flask("")


@app.route("/")
def home():
    return "Bot de Inversión Avanzada Albion 24/7"


def run_http():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)


intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Diccionario de traducción de IDs técnicos de la API a nombres amigables en español
ITEM_NAMES_ES = {
    # Capas de Artefacto y Facción
    "T6_CAPEITEM_DEMON": "Capa de Demonio -T6.0-",
    "T6_CAPEITEM_DEMON@1": "Capa de Demonio -T6.1-",
    "T6_CAPEITEM_DEMON@2": "Capa de Demonio -T6.2-",
    "T7_CAPEITEM_DEMON@1": "Capa de Demonio -T7.1-",
    "T8_CAPEITEM_DEMON@1": "Capa de Demonio -T8.1-",
    "T6_CAPEITEM_UNDEAD": "Capa de No Muerto -T6.0-",
    "T6_CAPEITEM_UNDEAD@1": "Capa de No Muerto -T6.1-",
    "T6_CAPEITEM_UNDEAD@2": "Capa de No Muerto -T6.2-",
    "T7_CAPEITEM_UNDEAD@1": "Capa de No Muerto -T7.1-",
    "T6_CAPEITEM_HERETIC": "Capa de Hereje -T6.0-",
    "T6_CAPEITEM_HERETIC@1": "Capa de Hereje -T6.1-",
    "T6_CAPEITEM_FW_FORTSTERLING": "Capa de Fort Sterling -T6.0-",
    "T6_CAPEITEM_FW_FORTSTERLING@1": "Capa de Fort Sterling -T6.1-",
    "T6_CAPEITEM_FW_MARTLOCK": "Capa de Martlock -T6.0-",
    "T6_CAPEITEM_FW_MARTLOCK@1": "Capa de Martlock -T6.1-",
    "T6_CAPEITEM_FW_LYMHURST": "Capa de Lymhurst -T6.0-",
    "T6_CAPEITEM_FW_LYMHURST@1": "Capa de Lymhurst -T6.1-",
    "T6_CAPEITEM_FW_BRIDGEWATCH": "Capa de Bridgewatch -T6.0-",
    "T6_CAPEITEM_FW_BRIDGEWATCH@1": "Capa de Bridgewatch -T6.1-",
    "T6_CAPEITEM_FW_THETFORD": "Capa de Thetford -T6.0-",
    "T6_CAPEITEM_FW_THETFORD@1": "Capa de Thetford -T6.1-",
    # Monturas
    "T6_MOUNT_ARMOREDHORSE": "Caballo Blindado -T6.0-",
    "T7_MOUNT_ARMOREDHORSE": "Caballo Blindado -T7.0-",
    "T8_MOUNT_ARMOREDHORSE": "Caballo Blindado -T8.0-",
    "T8_MOUNT_COW": "Buey de Transporte -T8.0-",
    "T7_MOUNT_DIREWOLF": "Lobo Huargo -T7.0-",
    "T8_MOUNT_DIREWOLF": "Lobo Huargo -T8.0-",
    # Equipamiento y Bolsas
    "T6_BAG@1": "Bolsa -T6.1-",
    "T7_BAG@1": "Bolsa -T7.1-",
    "T8_BAG": "Bolsa -T8.0-",
    "T8_BAG@1": "Bolsa -T8.1-",
    "T6_MAIN_SWORD@1": "Espada Ancha -T6.1-",
    "T7_MAIN_SWORD@1": "Espada Ancha -T7.1-",
    "T8_MAIN_SWORD": "Espada Ancha -T8.0-",
    "T6_2H_BOW@1": "Arco -T6.1-",
    "T7_2H_BOW@1": "Arco -T7.1-",
    "T8_2H_BOW": "Arco -T8.0-",
    "T6_2H_HOLYSTAFF@1": "Bastón Sagrado -T6.1-",
    "T7_2H_HOLYSTAFF@1": "Bastón Sagrado -T7.1-",
    "T8_2H_HOLYSTAFF": "Bastón Sagrado -T8.0-",
    # Consumibles
    "T8_POTION_HEAL": "Poción de Curación -T8.0-",
    "T8_POTION_CLEANSE": "Poción de Limpieza -T8.0-",
    "T8_OMELETTE": "Tortilla -T8.0-",
    "T8_STEW": "Guisado -T8.0-",
}

HIGH_VALUE_ITEMS = list(ITEM_NAMES_ES.keys())
MIN_UNIT_PRICE = 30000


def calcular_portafolio_practico(
    presupuesto=10000000,
    ciudad_origen="Fort Sterling",
    ciudad_destino="Caerleon",
):
    items_str = ",".join(HIGH_VALUE_ITEMS)
    url = f"https://www.albion-online-data.com/api/v2/stats/prices/{items_str}.json"

    try:
        res = requests.get(url, timeout=15)
        if res.status_code != 200:
            return None, "Error consultando la API de Albion Data."

        data = res.json()
        precios_origen = {}
        precios_destino = {}

        for entry in data:
            item_id = entry["item_id"]
            city = entry["city"]
            sell_price = entry["sell_price_min"]

            if sell_price <= 0:
                continue

            if city == ciudad_origen:
                precios_origen[item_id] = sell_price
            elif city == ciudad_destino:
                precios_destino[item_id] = sell_price

        oportunidades = []

        for item_id in HIGH_VALUE_ITEMS:
            if (
                item_id in precios_origen
                and item_id in precios_destino
            ):
                p_compra = precios_origen[item_id]
                p_venta = precios_destino[item_id]

                if p_compra < MIN_UNIT_PRICE:
                    continue

                ingreso_neto_unidad = p_venta * 0.935
                ganancia_unidad = ingreso_neto_unidad - p_compra
                roi = (
                    ganancia_unidad / p_compra
                ) * 100 if p_compra > 0 else 0

                if roi >= 10.0 and ganancia_unidad > 0:
                    oportunidades.append({
                        "item": item_id,
                        "nombre_es": ITEM_NAMES_ES.get(item_id, item_id),
                        "compra": p_compra,
                        "venta": p_venta,
                        "ganancia_u": ganancia_unidad,
                        "roi": roi,
                    })

        if not oportunidades:
            return (
                None,
                f"No se encontraron oportunidades prácticas entre {ciudad_origen} y {ciudad_destino}.",
            )

        oportunidades.sort(key=lambda x: x["roi"], reverse=True)

        capital_restante = presupuesto
        carrito = []
        inversion_total = 0
        ganancia_total = 0

        for opp in oportunidades:
            if capital_restante < opp["compra"]:
                continue

            max_inversion_item = presupuesto * 0.25
            unidades = int(
                min(capital_restante, max_inversion_item) // opp["compra"]
            )

            unidades = min(unidades, 20)

            if unidades > 0:
                costo_lote = unidades * opp["compra"]
                ganancia_lote = unidades * opp["ganancia_u"]

                capital_restante -= costo_lote
                inversion_total += costo_lote
                ganancia_total += ganancia_lote

                carrito.append({
                    "nombre_es": opp["nombre_es"],
                    "unidades": unidades,
                    "precio_compra": opp["compra"],
                    "precio_venta": opp["venta"],
                    "ganancia_lote": int(ganancia_lote),
                    "roi": round(opp["roi"], 1),
                })

        return {
            "origen": ciudad_origen,
            "destino": ciudad_destino,
            "inversion": int(inversion_total),
            "ganancia": int(ganancia_total),
            "roi_total": round((ganancia_total / inversion_total) * 100, 2)
            if inversion_total > 0
            else 0,
            "carrito": carrito,
        }, None

    except Exception as e:
        return None, f"Error inesperado: {str(e)}"


@bot.event
async def on_ready():
    print(f"¡Bot listo con nombres en español como {bot.user}!")


@bot.command()
async def invertir(
    ctx,
    monto: int = 10000000,
    origen: str = "Fort Sterling",
    destino: str = "Caerleon",
):
    await ctx.send(
        f"⏳ Analizando mercado para invertir **{monto:,} Silver** desde **{origen}** hacia **{destino}**..."
    )

    resultado, error = calcular_portafolio_practico(monto, origen, destino)

    if error:
        await ctx.send(f"❌ {error}")
        return

    msg = (
        f"📊 **PORTAFOLIO DE INVERSIÓN SUGERIDO**\n"
        f"📍 **Ruta:** {resultado['origen']} ➔ {resultado['destino']}\n"
        f"💰 **Inversión Total:** {resultado['inversion']:,} / {monto:,} Silver\n"
        f"📈 **Ganancia Neta Estimada:** **+{resultado['ganancia']:,} Silver** ({resultado['roi_total']}% ROI)\n"
        f"----------------------------------------\n"
        f"🛒 **CARRITO DE COMPRAS:**\n\n"
    )

    for item in resultado["carrito"]:
        msg += (
            f"📦 **{item['nombre_es']} {item['unidades']} unidades**\n"
            f"   • Comprar a: {item['precio_compra']:,} c/u | Vender a: {item['precio_venta']:,} c/u\n"
            f"   • Ganancia estimada del lote: +{item['ganancia_lote']:,} Silver\n\n"
        )

    await ctx.send(msg)


if __name__ == "__main__":
    t = Thread(target=run_http, daemon=True)
    t.start()

    TOKEN = os.environ.get("DISCORD_TOKEN")
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("Error: La variable DISCORD_TOKEN no está configurada.")
