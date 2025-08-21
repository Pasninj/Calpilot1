import discord
import asyncio
import os
import subprocess
import threading
from dotenv import load_dotenv
from flask import Flask
from playwright.async_api import async_playwright
from discord.ext import commands

# Charger les variables depuis .env
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = 1407496727375642644  # ⚡️ cast en int

SESSION_FILE = "storage_state.json"

INTENTS = discord.Intents.default()
INTENTS.message_content = True
bot = commands.Bot(command_prefix="!", intents=INTENTS)

# ----------- Vérification session ----------- #
def ensure_session():
    if not os.path.exists(SESSION_FILE):
        print("⚠️ Pas de session trouvée, lancement de loginCop.py...")
        subprocess.run(["python", "loginCop.py"], check=True)
    else:
        print("✅ Session GitHub trouvée.")

# ----------- Fonction Copilot ----------- #
async def get_copilot_response(question: str) -> str:
    async with async_playwright() as p:
        # ⚡️ Utiliser Chromium plutôt que Firefox
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(storage_state=SESSION_FILE)
        page = await context.new_page()

        await page.goto("https://github.com/copilot")

        try:
            await page.wait_for_selector("#copilot-chat-textarea", timeout=15000)
            print("✅ Champ de saisie trouvé")
        except:
            await browser.close()
            raise RuntimeError("Impossible de trouver le champ de saisie Copilot")

        prompt = f"{question}\nAjoute 'ended' à la fin de ta réponse."
        await page.fill("#copilot-chat-textarea", prompt)
        await page.keyboard.press("Enter")

        response_text = ""
        for _ in range(60):
            try:
                messages = await page.query_selector_all("div.ChatMessage-module__content--sWQll")
                all_texts = [await m.inner_text() for m in messages]

                possibles = [txt for txt in all_texts if question not in txt]

                if possibles and "ended" in possibles[-1]:
                    response_text = possibles[-1]
                    break
            except:
                pass
            await asyncio.sleep(1)

        await browser.close()

        if not response_text:
            return "⚠️ Pas de réponse reçue de Copilot."

        cleaned = response_text.replace("Ajoute 'ended' à la fin de ta réponse.", "").replace("ended", "").strip()
        if cleaned.lower().startswith("copilot said:"):
            cleaned = cleaned[len("copilot said:"):].strip()

        lines = [line.strip() for line in cleaned.splitlines() if line.strip()]
        if not lines:
            return ""
        return max(lines, key=len)

# ----------- Event Discord ----------- #
@bot.event
async def on_ready():
    print(f"✅ Connecté en tant que {bot.user}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    if message.channel.id == CHANNEL_ID:
        thinking_msg = await message.channel.send("Je réfléchis...")

        try:
            response = await get_copilot_response(message.content)
        except Exception as e:
            response = f"❌ Erreur lors de l'appel à Copilot: {e}"

        await thinking_msg.delete()
        await message.channel.send(response)

# ----------- Serveur Flask pour Render ----------- #
app = Flask(__name__)

@app.route("/")
def home():
    return "✅ Bot Discord is running!"

def run_flask():
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)

# ----------- Lancer le bot + Flask ----------- #
if __name__ == "__main__":
    ensure_session()
    threading.Thread(target=run_flask, daemon=True).start()
    bot.run(DISCORD_TOKEN)
