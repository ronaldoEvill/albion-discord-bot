import asyncio
import os
import discord
from discord.ext import commands
import requests

# Configuración de intents de Discord
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Ciudades principales de Albion Online
CITIES = ["Martlock", "Bridgewatch", "Lymhurst", "Fort Sterling", "Thetford", "Caerleon"]

# Lista de ítems populares para monitorear
ITEMS_TO_SCAN = [
    # Bolsas y Monturas
    "T4_BAG", "T5_BAG", "T6_BAG", "T7_BAG", "T8_BAG",
    "T4_MOUNT_RIDINGHORSE", "T5_MOUNT_RIDINGHORSE", "T6_MOUNT_RIDINGHORSE",
    "T4_MOUNT_ARMOREDHORSE", "T5_MOUNT_ARMOREDHORSE", "T6_MOUNT_ARMOREDHORSE",
    "T5_MOUNT_COW", "T8_MOUNT_COW",
    # Armas populares
    "T4_MAIN_SWORD", "T5_MAIN_SWORD", "T6_MAIN_SWORD", "T7_MAIN_SWORD", "T8_MAIN_SWORD",
    "T4_2H_BOW", "T5_2H_BOW", "T6_2H_BOW", "T7_2H_BOW", "T8_2H_BOW",
    "T4_2H_HOLYSTAFF", "T5_2H_HOLYSTAFF", "T6_2H_HOLYSTAFF", "T7_2H_HOLYSTAFF", "T8_2H_HOLYSTAFF",
    "T4_MAIN_CURSEDSTAFF", "T5_MAIN_CURSEDSTAFF", "T6_MAIN_CURSEDSTAFF", "T7_MAIN_CURSEDSTAFF", "T8_MAIN_CURSEDSTAFF",
    # Recursos refinados
    "T4_CLOTH", "T5_CLOTH", "T6_CLOTH", "T7_CLOTH", "T8_CLOTH",
    "T4_LEATHER", "T5_LEATHER", "T6_LEATHER", "T7_LEATHER", "T8_LEATHER",
    "T4_PLANKS", "T5_PLANKS", "T6_PLANKS", "T7_PLANKS", "T8_PLANKS", 
    "T4_METALBAR", "T5_METALBAR", "T6_METALBAR", "T7_METALBAR", "T8_METALBAR"
]

MIN_PROFIT = 20000
notification_channel_id = None


def find_transport_opportunities():
    """Consulta la API de Albion Online y calcula oportunidades de transporte."""
    items_str = ",".join(ITEMS_TO_SCAN)
    url = f"https://www.albion-online-data.com/api/v2/stats/prices/{items_str}.json"
    opportunities = []

    try:
        res = requests.get(url, timeout=15)
        if res.status_code != 200:
            return opportunities

        data = res.json()
        item_prices = {}

        for entry in data:
            item_id = entry["item_id"]
            city = entry["city"]
            sell_price = entry["sell_price_min"]

            if city not in CITIES or sell_price <= 0:
                continue

            if item_id not in item_prices:
                item_prices[item_id] = []

            item_prices[item_id].append({"city": city, "price": sell_price})

        for item_id, prices in item_prices.items():
            if len(prices) < 2:
                continue

            cheapest = min(prices, key=lambda x: x["price"])
            expensive = max(prices, key=lambda x: x["price"])

            buy_price = cheapest["price"]
            sell_price = expensive["price"]
            net_profit = (sell_price * 0.96) - buy_price

            if net_profit >= MIN_PROFIT and cheapest["city"] != expensive["city"]:
                opportunities.append({
                    "item": item_id,
                    "buy_city": cheapest["city"],
                    "buy_price": buy_price,
                    "sell_city": expensive["city"],
                    "sell_price": sell_price,
                    "profit": int(net_profit)
                })

    except Exception as e:
        print(f"Error consultando la API: {e}")

    return opportunities


async def auto_scanner_task():
    """Bucle automático que revisa el mercado cada 10 minutos."""
    await bot.wait_until_ready()
    while not bot.is_closed():
        if notification_channel_id:
            channel = bot.get_channel(notification_channel_id)
            if channel:
                opportunities = find_transport_opportunities()
                if opportunities:
                    opportunities.sort(key=lambda x: x["profit"], reverse=True)
                    msg = f"🚨 **¡OPORTUNIDADES DE TRANSPORTE DETECTADAS!** 🚨\n\n"
                    for opp in opportunities[:5]:
                        msg += (
                            f"📦 **Ítem:** `{opp['item']}`\n"
                            f"🛒 **Comprar en:** {opp['buy_city']} a {opp['buy_price']:,} plata\n"
                            f"💰 **Vender en:** {opp['sell_city']} a {opp['sell_price']:,} plata\n"
                            f"📈 **Ganancia neta aprox.:** +{opp['profit']:,} de plata\n"
                            f"----------------------------------------\n"
                        )
                    await channel.send(msg)

        await asyncio.sleep(600)


@bot.event
async def on_ready():
    print(f"¡Bot conectado con éxito como {bot.user}!")
    bot.loop.create_task(auto_scanner_task())


@bot.command()
async def activar(ctx):
    """Activa las notificaciones en el canal donde se ejecuta."""
    global notification_channel_id
    notification_channel_id = ctx.channel.id
    await ctx.send(
        f"✅ **Escáner de transporte activado.**\n"
        f"Revisaré el mercado cada 10 minutos buscando ganancias superiores a {MIN_PROFIT:,} de plata."
    )


@bot.command()
async def buscar(ctx):
    """Realiza un escaneo manual en el instante."""
    await ctx.send("🔍 Escaneando precios en el mercado de Albion...")
    opportunities = find_transport_opportunities()

    if not opportunities:
        await ctx.send("❌ No se encontraron oportunidades de transporte con más de 20,000 de ganancia en este momento.")
        return

    opportunities.sort(key=lambda x: x["profit"], reverse=True)
    msg = f"📊 **Resultados encontrados:**\n\n"
    for opp in opportunities[:5]:
        msg += (
            f"📦 **Ítem:** `{opp['item']}`\n"
            f"🛒 **Comprar en:** {opp['buy_city']} ({opp['buy_price']:,})\n"
            f"💰 **Vender en:** {opp['sell_city']} ({opp['sell_price']:,})\n"
            f"📈 **Ganancia neta:** +{opp['profit']:,} de plata\n\n"
        )
    await ctx.send(msg)


# Lee el Token de forma segura desde las variables de entorno de Render
TOKEN = os.environ.get("DISCORD_TOKEN")
if TOKEN:
    bot.run(TOKEN)
else:
    print("Error: No se encontró la variable de entorno DISCORD_TOKEN.")
