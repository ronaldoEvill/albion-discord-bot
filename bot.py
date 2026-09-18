import asyncio
import datetime
import os
from threading import Thread
from flask import Flask
import discord
from discord.ext import commands
import requests

# 1. Servidor Flask para mantener vivo el Web Service en Render
app = Flask("")


@app.route("/")
def home():
    return "Bot de Inversión y Mercado Albion 24/7 en línea"


def run_http():
    # Render asigna dinámicamente un puerto en la variable PORT
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)


# 2. Configuración de Discord
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# 3. Catálogo exclusivo de Ítems de ALTA ROTACIÓN (Liquidez garantizada)
HIGH_LIQUIDITY_ITEMS = [
    # Consumibles
    "T6_POTION_HEAL",
    "T7_POTION_HEAL",
    "T8_POTION_HEAL",
    "T6_POTION_CLEANSE",
    "T8_POTION_CLEANSE",
    "T7_MEATPIE",
    "T8_MEATPIE",
    "T7_OMELETTE",
    "T8_OMELETTE",
    "T7_STEW",
    "T8_STEW",
    # Recursos Refinados (Materia prima de alta demanda)
    "T4_CLOTH",
    "T5_CLOTH",
    "T6_CLOTH",
    "T7_CLOTH",
    "T8_CLOTH",
    "T4_LEATHER",
    "T5_LEATHER",
    "T6_LEATHER",
    "T7_LEATHER",
    "T8_LEATHER",
    "T4_PLANKS",
    "T5_PLANKS",
    "T6_PLANKS",
    "T7_PLANKS",
    "T8_PLANKS",
    "T4_METALBAR",
    "T5_METALBAR",
    "T6_METALBAR",
    "T7_METALBAR",
    "T8_METALBAR",
    # Equipamiento Meta y Monturas
    "T4_BAG",
    "T5_BAG",
    "T6_BAG",
    "T7_BAG",
    "T8_BAG",
    "T5_MOUNT_ARMOREDHORSE",
    "T6_MOUNT_ARMOREDHORSE",
    "T5_MOUNT_COW",
    "T8_MOUNT_COW",
    "T4_CAPE",
    "T5_CAPE",
    "T6_CAPE",
]

CITIES = [
    "Martlock",
    "Bridgewatch",
    "Lymhurst",
    "Fort Sterling",
    "Thetford",
    "Caerleon",
]


# 4. Lógica de inversión y análisis de mercado
def calcular_portafolio_inversion(
    presupuesto=10000000,
    ciudad_origen="Fort Sterling",
    ciudad_destino="Caerleon",
):
    items_str = ",".join(HIGH_LIQUIDITY_ITEMS)
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

        for item_id in HIGH_LIQUIDITY_ITEMS:
            if (
                item_id in precios_origen
                and item_id in precios_destino
            ):
                p_compra = precios_origen[item_id]
                p_venta = precios_destino[item_id]

                # Descuento del 6.5% (4% Impuesto de mercado Premium + 2.5% Tasa de orden)
                ingreso_neto_unidad = p_venta * 0.935
                ganancia_unidad = ingreso_neto_unidad - p_compra
                roi = (
                    ganancia_unidad / p_compra
                ) * 100 if p_compra > 0 else 0

                # Filtro de Seguridad: Mínimo 12% de ROI para evitar estancamiento
                if roi >= 12.0 and ganancia_unidad > 0:
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
                f"No se encontraron oportunidades seguras entre {ciudad_origen} y {ciudad_destino} con ROI superior al 12%.",
            )

        # Ordenar por el mejor Retorno de Inversión (ROI)
        oportunidades.sort(key=lambda x: x["roi"], reverse=True)

        # Algoritmo de optimización de presupuesto (Knapsack Simplificado)
        capital_restante = presupuesto
        carrito = []
        inversion_total = 0
        ganancia_total = 0

        for opp in oportunidades:
            if capital_restante < opp["compra"]:
                continue

            # Límite por item para diversificar el riesgo (máximo 35% del presupuesto por ítem)
            max_inversion_item = presupuesto * 0.35
            unidades = int(
                min(capital_restante, max_inversion_item) // opp["compra"]
            )

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


# 5. Comandos de Discord
@bot.event
async def on_ready():
    print(f"¡Bot de Inversión listo como {bot.user}!")


@bot.command()
async def invertir(
    ctx,
    monto: int = 10000000,
    origen: str = "Fort Sterling",
    destino: str = "Caerleon",
):
    await ctx.send(
        f"⏳ Analizando mercado de liquidez alta para invertir **{monto:,} Silver** desde **{origen}** hacia **{destino}**..."
    )

    resultado, error = calcular_portafolio_inversion(monto, origen, destino)

    if error:
        await ctx.send(f"❌ {error}")
        return

    msg = (
        f"📊 **PORTAFOLIO DE INVERSIÓN SUGERIDO**\n"
        f"📍 **Ruta:** {resultado['origen']} ➔ {resultado['destino']}\n"
        f"💰 **Presupuesto Usado:** {resultado['inversion']:,} / {monto:,} Silver\n"
        f"📈 **Ganancia Neta Estimada:** **+{resultado['ganancia']:,} Silver**\n"
        f"🚀 **Retorno de Inversión (ROI):** **{resultado['roi_total']}%**\n"
        f"----------------------------------------\n"
        f"🛒 **CARRITO DE COMPRAS:**\n\n"
    )

    for item in resultado["carrito"]:
        msg += (
            f"📦 **{item['unidades']}x** `{item['item']}`\n"
            f"   • Comprar en {resultado['origen']} a: {item['precio_compra']:,}\n"
            f"   • Vender en {resultado['destino']} a: {item['precio_venta']:,}\n"
            f"   • Ganancia lote: +{item['ganancia_lote']:,} Silver ({item['roi']}% ROI)\n\n"
        )

    await ctx.send(msg)


# 6. Inicio seguro de procesos (Solución al error de puertos HTTP)
if __name__ == "__main__":
    # Iniciar Flask en un hilo independiente ANTES de que discord.py bloquee el hilo principal
    t = Thread(target=run_http, daemon=True)
    t.start()

    TOKEN = os.environ.get("DISCORD_TOKEN")
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("Error: La variable DISCORD_TOKEN no está configurada.")
