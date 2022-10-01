from discord.ext import commands
import os
import pathlib
import discord


intent = discord.Intents.all()

bot = commands.Bot(
    debug_guilds=os.getenv("GUILDS").split(","),
    intent=intent
)
TOKEN = os.getenv('TOKEN')

path = "./cogs"


@bot.event
async def on_ready():
    print(f"Bot名:{bot.user} On ready!!")


dir = "cogs"
files = pathlib.Path(dir).glob("*.py")
for file in files:
    print(f"{dir}.{file.name[:-3]}")
    bot.load_extension(name=f"{dir}.{file.name[:-3]}", store=False)


bot.run(TOKEN)
