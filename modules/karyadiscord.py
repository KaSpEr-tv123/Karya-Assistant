from disnake.ext import commands
from disnake import Embed, Color
import disnake
from .chat import karya_request
from .command_compiler import CommandCompiler
from .types import KaryaContext
from threading import Thread
import traceback

class KaryaDiscord(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: disnake.Message):
        if message.author.bot:
            return
        if message.reference is None:
            reference = None
            penos = False
        else:
            reference =  await message.channel.fetch_message(message.reference.message_id)
            penos = reference.author.id == self.bot.user.id
        
        if message.content.lower().startswith('каря') or message.content.startswith(self.bot.user.mention) or penos:
            try:
                bot_msg = await message.reply(embed=Embed(title="Каря Discord Assistant", description="<a:Loading:1327321867886788608>", color=Color.purple()))
                response = karya_request(
                    f"(сообщение из дискорда, userid: {message.author.id}, "
                    f"channelid: {message.channel.id}, guildid: {message.guild.id}, "
                    f"messageid: {message.id}, username: {message.author.name}"
                    f"permissions: (administrator: {message.author.guild_permissions.administrator}, manage_messages: {message.author.guild_permissions.manage_messages}, manage_roles: {message.author.guild_permissions.manage_roles}))",
                    message.content.replace("kasperenok", message.author.name).replace("каря", "", 1).replace(self.bot.user.mention, "", 1),
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
        await self.bot.change_presence(activity=disnake.Activity(type=disnake.ActivityType.playing, name="Karya Discord Assistant"), status=disnake.Status.idle)
        


    @commands.command(name="stop")
    @commands.is_owner()
    async def stop(self, ctx):
        await ctx.send(embed=Embed(description="Каря остановлена", color=Color.red()))
        await self.bot.close()

def connectBot(token):
    bot = commands.Bot(command_prefix=">", intents=disnake.Intents.all())
    bot.add_cog(KaryaDiscord(bot))
    def run():
        bot.run(token)

    thread = Thread(target=run)
    thread.start()