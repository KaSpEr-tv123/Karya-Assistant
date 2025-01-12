from discord.ext import commands
from discord import Embed, Color
import discord
from .chat import karya_request
from .command_compiler import CommandCompiler
from .types import KaryaContext
from threading import Thread
import traceback

class KaryaDiscord(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        if message.reference is None:
            reference = None
            penos = False
        else:
            reference = message.reference.resolved
            if reference is None or isinstance(reference, discord.DeletedReferencedMessage):
                return
            penos = reference.author.id == self.bot.user.id

        karya = message.content.lower().startswith('каря')
        if karya or self.bot.user.mentioned_in(message):
            try:
                bot_msg = await message.reply(embed=Embed(title="Каря Discord Assistant", description="<a:Loading:1327321867886788608>", color=Color.purple()))
                response = karya_request(
                    f"(Сообщение из Discord, user ID: {message.author.id}, "
                    f"channel ID: {message.channel.id}, guild ID: {message.guild.id}, "
                    f"message ID: {message.id}, username: {message.author.name}"
                    f"permissions: (administrator: {message.author.guild_permissions.administrator}, manage_messages: {message.author.guild_permissions.manage_messages}, manage_roles: {message.author.guild_permissions.manage_roles}))",
                    message.content[5:] if karya else message.content.replace(self.bot.user.mention, "", 1),
                    CommandCompiler.commands,
                    message,
                    "discord"
                )

                if len(response) > 2000:
                    response = response[:2000]

                await bot_msg.edit(embed=Embed(title="Каря Discord Assistant", description=response, color=Color.purple()))
                bot_msg.embeds = [Embed(title="Каря Discord Assistant", description=response, color=Color.purple())]

                await CommandCompiler.compile(response, KaryaContext(message, bot_msg, self.bot), "discord")

            except Exception as e:
                await message.channel.send(
                    embed=Embed(
                        description=f"Произошла ошибка: ```py\n{traceback.format_exc()}```",
                        color=Color.red()
                    )
                )

    @commands.Cog.listener()
    async def on_ready(self):
        print("Каря запущена в боте Discord")

    @commands.command()
    @commands.is_owner()
    async def stop(self, ctx):
        await ctx.send(embed=Embed(description="Каря остановлена", color=Color.red()))
        await self.bot.close()

class KaryaDiscordBot(commands.Bot):
    async def setup_hook(self):
        await self.add_cog(KaryaDiscord(self))

def connectBot(token: str) -> None:
    intents = discord.Intents.default()
    intents.message_content = True
    bot = KaryaDiscordBot(command_prefix=">", intents=intents, activity=discord.Game('Karya Discord Assistant'), status=discord.Status.idle)
    thread = Thread(target=bot.run, args=(token,))
    thread.start()
