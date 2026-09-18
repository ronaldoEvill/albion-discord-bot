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

# Catálogo expandido con ítems de ALTO VALOR (T6.1, T6.2, T7.1, T8.1, Capas de Facción/Artefacto)
HIGH_VALUE_ITEMS = [
    # Capas de Artefacto y Facción
    "T6_CAPEITEM_DEMON",
    "T6_CAPEITEM_DEMON@1",
    "T6_CAPEITEM_DEMON@2",
    "T7_CAPEITEM_DEMON@1",
    "T8_CAPEITEM_DEMON@1",
    "T6_CAPEITEM_UNDEAD",
    "T6_CAPEITEM_UNDEAD@1",
    "T6_CAPEITEM_UNDEAD@2",
    "T7_CAPEITEM_UNDEAD@1",
    "T6_CAPEITEM_HERETIC",
    "T6_CAPEITEM_HERETIC@1",
    "T6_CAPEITEM_FW_FORTSTERLING",
    "T6_CAPEITEM_FW_FORTSTERLING@1",
    "T6_CAPEITEM_FW_MARTLOCK",
    "T6_CAPEITEM_FW_MARTLOCK@1",
    "T6_CAPEITEM_FW_LYMHURST",
    "T6_CAPEITEM_FW_LYMHURST@1",
    "T6_CAPEITEM_FW_BRIDGEWATCH",
    "T6_CAPEITEM_FW_BRIDGEWATCH@1",
    "T6_CAPEITEM_FW_THETFORD",
    "T6_CAPEITEM_FW_THETFORD@1",
    # Monturas de Valor Medio/Alto
    "T6_MOUNT_ARMOREDHORSE",
    "T7_MOUNT_ARMOREDHORSE",
    "T8_MOUNT_ARMOREDHORSE",
    "T8_MOUNT_COW",
    "T7_MOUNT_DIREWOLF",
    "T8_MOUNT_DIREWOLF",
    # Equipamiento T6.1 - T8.1 Popular
    "T6_BAG@1",
    "T7_BAG@1",
    "T8_BAG",
    "T8_BAG@1",
    "T6_MAIN_SWORD@1",
    "T7_MAIN_SWORD@1",
    "T8_MAIN_SWORD",
    "T6_2H_BOW@1",
    "T7_2H_BOW@1",
    "T8_2H_BOW",
    "T6_2H_HOLYSTAFF@1",
    "T7_2H_HOLYSTAFF@1",
    "T8_2H_HOLYSTAFF",
    "T6_HEAD_PLATE_SET1@1",
    "T7_HEAD_PLATE_SET1@1",
    "T8_HEAD_PLATE_SET1",
    "T6_ARMOR_PLATE_SET1@1",
    "T7_ARMOR_PLATE_SET1@1",
    "T8_ARMOR_PLATE_SET1",
    "T6_SHOES_PLATE_SET1@1",
    "T7_SHOES_PLATE_SET1@1",
    "T8_SHOES_PLATE_SET1",
    # Consumibles de Alto Nivel
    "T8_POTION_HEAL",
    "T8_POTION_CLEANSE",
    "T8_OMELETTE",
    "T8_STEW",
]

# Configuración de límites para evitar compras masivas de bajo valor
MIN_UNIT_PRICE = 30000  # Solo ítems que cuesten más de 30,000 de plata c/u


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

                # Filtro clave: Ignorar ítems baratos para no comprar cientos de unidades
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
                        "compra": p_compra,
                        "venta": p_venta,
                        "ganancia_u": ganancia_unidad,
                        "roi": roi,
                    })

        if not oportunidades:
            return (
                None,
                f"No se encontraron oportunidades prácticas entre {ciudad_origen} y {ciudad_destino} con ítems mayores a {MIN_UNIT_PRICE:,} Silver.",
            )

        oportunidades.sort(key=lambda x: x["roi"], reverse=True)

        capital_restante = presupuesto
        carrito = []
        inversion_total = 0
        ganancia_total = 0

        for opp in oportunidades:
            if capital_restante < opp["compra"]:
                continue

            # Máximo 25% del presupuesto en un solo ítem para forzar diversidad
            max_inversion_item = presupuesto * 0.25
            unidades = int(
                min(capital_restante, max_inversion_item) // opp["compra"]
            )

            # Límite práctico: Máximo 20 unidades por ítem
            unidades = min(unidades, 20)

            if unidades > 0:
                costo_lote = unidades * opp["compra"]
                ganancia_lote = unidades * opp["ganancia_u"]

                capital_restante -= costo_lote
                inversion_total += costo_lote
                ganancia_total += ganancia_lote

                carrito.append({
                    "item": opp["item"],
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
    print(f"¡Bot de Inversión Práctica listo como {bot.user}!")


@bot.command()
async def invertir(
    ctx,
    monto: int = 10000000,
    origen: str = "Fort Sterling",
    destino: str = "Caerleon",
):
    await ctx.send(
        f"⏳ Analizando mercado de ítems de alto valor para invertir **{monto:,} Silver** desde **{origen}** hacia **{destino}**..."
    )

    resultado, error = calcular_portafolio_practico(monto, origen, destino)

    if error:
        await ctx.send(f"❌ {error}")
        return

    msg = (
        f"📊 **PORTAFOLIO DE INVERSIÓN PRÁCTICO**\n"
        f"📍 **Ruta:** {resultado['origen']} ➔ {resultado['destino']}\n"
        f"💰 **Presupuesto Usado:** {resultado['inversion']:,} / {monto:,} Silver\n"
        f"📈 **Ganancia Neta Estimada:** **+{resultado['ganancia']:,} Silver**\n"
        f"🚀 **Retorno de Inversión (ROI):** **{resultado['roi_total']}%**\n"
        f"----------------------------------------\n"
        f"🛒 **CARRITO DE COMPRAS (Ítems de Alto Valor):**\n\n"
    )

    for item in resultado["carrito"]:
        msg += (
            f"📦 **{item['unidades']}x** `{item['item']}`\n"
            f"   • Comprar en {resultado['origen']} a: {item['precio_compra']:,} c/u\n"
            f"   • Vender en {resultado['destino']} a: {item['precio_venta']:,} c/u\n"
            f"   • Ganancia lote: +{item['ganancia_lote']:,} Silver ({item['roi']}% ROI)\n\n"
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
