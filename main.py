# main.py
import discord
import os
import asyncio
from dotenv import load_dotenv
from discord.ext import commands
import openai
from flask import Flask
import threading

# Charger les variables d'environnement
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Config OpenAI
openai.api_key = OPENAI_API_KEY

# Config bot Discord
INTENTS = discord.Intents.default()
INTENTS.message_content = True
bot = commands.Bot(command_prefix="!", intents=INTENTS)

# ----------- Fonction pour récupérer la réponse GPT ----------- #
async def get_gpt_response(question: str) -> str:
    try:
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": question}],
                temperature=0.7,
            )
        )
        answer = response['choices'][0]['message']['content'].strip()
        return answer
    except Exception as e:
        return f"❌ Erreur lors de l'appel à l'API GPT: {e}"

# ----------- Events Discord ----------- #
@bot.event
async def on_ready():
    print(f"✅ Connecté en tant que {bot.user}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    if message.channel.id == CHANNEL_ID:
        thinking_msg = await message.channel.send("Je réfléchis...")

        response = await get_gpt_response(message.content)

        await thinking_msg.delete()
        await message.channel.send(response)

# ----------- Petit serveur Flask pour keep-alive ----------- #
app = Flask(__name__)

@app.route("/")
def home():
    return "✅ Bot Discord is running!"

def run_flask():
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)

# ----------- Lancer bot + Flask ----------- #
if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    bot.run(DISCORD_TOKEN)
