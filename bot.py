# Force rebuild
import os
import requests
import discord
from discord.ext import tasks

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

ITEMS = {
    404: "Item 404"
}

client = discord.Client(
    intents=discord.Intents.default()
)

tracked = {}

def get_top_buy(item_id):
    url = f"https://query.idleclans.com/api/PlayerMarket/items/prices/latest/comprehensive/{item_id}"
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    data = response.json()
    top = data["highestBuyPricesWithVolume"][0]
    return {
        "price": int(top["key"]),
        "qty": int(top["value"])
    }

@tasks.loop(seconds=60)
async def monitor_market():
    channel = client.get_channel(CHANNEL_ID)
    if channel is None:
        return
    
    for item_id, item_name in ITEMS.items():
        try:
            current = get_top_buy(item_id)
            if item_id not in tracked:
                tracked[item_id] = current
                print(
                    f"Tracking {item_name}: "
                    f"{current['price']} ({current['qty']})"
                )
                continue
            
            previous = tracked[item_id]
            if current["price"] > previous["price"]:
                await channel.send(
                    "@everyone\n\n"
                    f"🚨 NEW HIGHEST BUY ORDER 🚨\n\n"
                    f"Item: {item_name}\n"
                    f"Old Price: {previous['price']:,}\n"
                    f"New Price: {current['price']:,}\n"
                    f"Quantity: {current['qty']:,}"
                )
                tracked[item_id] = current
        except Exception as e:
            print(f"Error checking {item_name}: {e}")

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    monitor_market.start()

client.run(TOKEN)
