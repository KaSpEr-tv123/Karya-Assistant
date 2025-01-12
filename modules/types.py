import discord
from discord.ext import commands

class KaryaContext():
    def __init__(self, message: discord.Message, botmsg: discord.Message, bot: commands.Bot):
        self.message = message
        self.botmsg = botmsg
        self.bot = bot
        self.author = message.author
        self.channel = message.channel
        self.guild = message.guild
        self.content = message.content
        self.embeds = message.embeds
        self.attachments = message.attachments
        self.clean_content = message.clean_content 
        self.created_at = message.created_at
        self.edited_at = message.edited_at
        self.jump_url = message.jump_url
        self.pinned = message.pinned
        self.mention_everyone = message.mention_everyone
        self.mentions = message.mentions
        self.role_mentions = message.role_mentions
    
    async def reply(self, content=None, **kwargs):
        return await self.message.reply(content, **kwargs)
    
    async def send(self, content=None, **kwargs):
        return await self.channel.send(content, **kwargs)
    
    async def edit(self, content=None, **kwargs):
        return await self.botmsg.edit(content, **kwargs)
    
    async def delete(self):
        return await self.botmsg.delete()
    
    async def followup(self, content=None, **kwargs):
        return await self.botmsg.followup.send(content, **kwargs)
    
    async def followup_edit(self, content=None, **kwargs):
        return await self.botmsg.followup.edit(content, **kwargs)
    
    async def followup_delete(self):
        return await self.botmsg.followup.delete()
    
    async def add_reaction(self, emoji):
        return await self.message.add_reaction(emoji)
    
    async def clear_reactions(self):
        return await self.message.clear_reactions()
    
    async def remove_reaction(self, emoji, user):
        return await self.message.remove_reaction(emoji, user)


class KaryaCommand():
    def __init__(self, name: str, description: str, args: str, function):
        self.name = name
        self.description = description
        self.args = args
        self.function = function
        
class KaryaCommands():
    def __init__(self, commands: list[KaryaCommand] = []):
        self.commands = commands

    def __call__(self):
        return self.commands
        
    def get_command(self, name: str):
        for command in self.commands:
            if command.name == name:
                return command
        return None
        
    def get_strcommands(self):
        strcommands = ""
        for command in self.commands:
            strcommands += f"#{command.name}({command.args}) - {command.description}\n"
        return strcommands
    
    def add_command(self, command: KaryaCommand):
        self.commands.append(command)

    def remove_command(self, name: str):
        for command in self.commands:
            if command.name == name:
                self.commands.remove(command)
