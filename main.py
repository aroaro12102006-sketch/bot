import datetime
import os
import json
import threading
from flask import Flask, render_template
import discord
from discord import app_commands
from discord.ext import commands, tasks

# --- KONFIGURACJA BOTA ---
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True

bot = commands.Bot(command_prefix='!', intents=intents)

# ID kanału tekstowego na życzenia
ID_KANALU_ZYCZEN = 1486806116590551094

# Plik bazy danych JSON
DATA_FILE = 'urodziny.json'

# --- FUNKCJE BAZY DANYCH ---
def load_data():
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# --- SERWER FLASK (STRONA WWW) ---
app = Flask(__name__)

@app.route('/')
def index():
    urodziny_data = load_data()
    return render_template('index.html', urodziny=urodziny_data)

def run_flask():
    app.run(host='0.0.0.0', port=5000, debug=False)

# --- ZDARZENIA BOTA ---
@bot.event
async def on_ready():
    print(f"Zalogowano jako {bot.user}")
    # Rejestracja komend / (slash commands) na Discordzie
    try:
        synced = await bot.tree.sync()
        print(f"Zasynchronizowano {len(synced)} komend(y) z ukośnikiem (/)")
    except Exception as e:
        print(f"Błąd synchronizacji komend: {e}")

    if not sprawdz_urodziny.is_running():
        sprawdz_urodziny.start()

# --- SLASH COMMANDS (KOMENDY Z UKOŚNIKIEM /) ---

@bot.tree.command(name="pomoc", description="Wyświetla listę dostępnych komend bota urodzinowego.")
async def pomoc(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🎂 Pomoc - Bot Urodzinowy",
        description="Oto lista dostępnych komend:",
        color=discord.Color.blue()
    )
    embed.add_field(
        name="`/urodziny data:<DD.MM>`", 
        value="Zapisuje lub aktualizuje Twoje urodziny (np. `/urodziny data:13.10`). Jeśli podasz nową datę, stara zostanie zmieniona!", 
        inline=False
    )
    embed.add_field(
        name="`/pomoc`", 
        value="Wyświetla tę listę podpowiedzi.", 
        inline=False
    )
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="urodziny", description="Zapisz lub zmień swoją datę urodzin.")
@app_commands.describe(data="Podaj datę urodzin w formacie DD.MM (np. 13.10)")
async def dodaj_urodziny(interaction: discord.Interaction, data: str):
    user_id = str(interaction.user.id)
    urodziny = load_data()

    czy_zmienia = user_id in urodziny
    urodziny[user_id] = data
    save_data(urodziny)

    if czy_zmienia:
        await interaction.response.send_message(
            f"✏️ {interaction.user.mention}, Twoja data urodzin została pomyślnie zaktualizowana na **{data}**!"
        )
    else:
        await interaction.response.send_message(
            f"🎉 {interaction.user.mention}, Twoje urodziny (**{data}**) zostały zapisane!"
        )

# --- AUTOMATYCZNE ŻYCZENIA ---
@tasks.loop(hours=24)
async def sprawdz_urodziny():
    dzisiaj = datetime.datetime.now().strftime("%d.%m")
    dane = load_data()
    kanal = bot.get_channel(ID_KANALU_ZYCZEN)

    if not kanal:
        return

    for user_id, data_urodzin in dane.items():
        if data_urodzin == dzisiaj:
            try:
                user = await bot.fetch_user(int(user_id))
                if user:
                    await kanal.send(f"🎉🎂 **Wszystkiego najlepszego {user.mention}!** 🥳🎈\nŻyczymy Ci wspaniałego dnia!")
            except Exception:
                pass

@sprawdz_urodziny.before_loop
async def before_sprawdz_urodziny():
    await bot.wait_until_ready()

# --- URUCHOMIENIE ---
if __name__ == '__main__':
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    print("🌐 Strona internetowa została uruchomiona!")

    bot.run('MTU1OTUxNjgwOTcxNDA3NzcxNw.GDngpg.-OnHz3hN118uqr1zreHwwnxHZRPMKTmUWBK5Uk')
