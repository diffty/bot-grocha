import sys
import traceback
import datetime
import subprocess

import discord

import config


class GrochaGuild:
    def __init__(self, bot, guild):
        self.bot = bot
        self.user = self.bot.user
        self.server = guild
        self.greet_messages_in_wait = {}
        self.kick_messages_in_wait = {}
        self.chan_welcome = self.get_channel_by_name(config.WELCOME_CHANNEL_NAME)
        self.chan_main = self.get_channel_by_name(config.MAIN_CHANNEL_NAME)
        self.chan_debug = self.get_channel_by_name(config.DEBUG_CHANNEL_NAME)
        self.role_main = self.get_role_by_name(config.MAIN_ROLE_NAME)

        if not self.role_main:
            raise Exception(f"<!!> Can't find role named {config.MAIN_ROLE_NAME}")

        self.grant_emoji = self.get_emoji_by_name(config.GRANT_EMOJI_NAME)

    def get_channel_by_name(self, channel_name):
        return discord.utils.get(self.server.channels, name = channel_name)

    def get_role_by_name(self, role_name):
        return discord.utils.get(self.server.roles, name = role_name)

    def get_emoji_by_name(self, emoji_name):
        return discord.utils.get(self.server.emojis, name = emoji_name)

    def emoji_to_string(self, emoji):
        return f'<{"a" if emoji.animated else ""}:{emoji.name}:{str(emoji.id)}>'

    def get_text_channels(self):
        return list(filter(lambda c : isinstance(c, discord.channel.TextChannel), self.server.channels))

    async def on_ready(self):
        print(f"Connected on Discord server {self.server}")
        sys.stdout.flush()
        sys.stderr.flush()

        if self.chan_debug:
            await self.chan_debug.send(f'MAOOWWWWWW _(I just awakened)_')

    async def on_member_join(self, member):
        message = await self.chan_main.send(f"MAOU! **{member.name}** vient d'arriver sur le serveur.\nRéagis à ce message avec l'emoji {self.emoji_to_string(self.grant_emoji)} pour lui donner les droits!")
        self.greet_messages_in_wait[message.id] = member

    async def on_reaction_add(self, reaction, user):
        message = reaction.message

        if message.id in self.greet_messages_in_wait.keys():
            member = self.greet_messages_in_wait[message.id]
            #print(f"Bienvenue à {member.name} !")

            users_emoji = []
            for r in message.reactions:
                if r.emoji == self.grant_emoji:
                    users = await r.users().flatten()
                    for u in users:
                        users_emoji.append(u.name)

            users_emoji = list(set(users_emoji))

            if users_emoji:
                await member.add_roles(self.role_main, reason=f"Permission accordée par {', '.join(users_emoji)} & Grocha le {(datetime.datetime.now() + datetime.timedelta(1)).strftime('%Y-%m-%d %H:%M:%S')}")
                del self.greet_messages_in_wait[message.id]

        if message.id in self.kick_messages_in_wait.keys():
            members = self.kick_messages_in_wait[message.id]

            users_emoji = []
            for r in message.reactions:
                if r.emoji == self.grant_emoji:
                    users = await r.users().flatten()
                    for u in users:
                        users_emoji.append(u.name)

            users_emoji = list(set(users_emoji))

            if len(users_emoji) > 2:
                try:
                    for m in members:
                        await self.server.kick(m, reason=f"Utilisateur kické par {', '.join(users_emoji)} & Grocha le {(datetime.datetime.now() + datetime.timedelta(1)).strftime('%Y-%m-%d %H:%M:%S')}")
                    del self.kick_messages_in_wait[message.id]
                except Exception as e:
                    await self.deal_with_exception(e, message.channel)

    async def on_message(self, message):
        try:
            if self.user.mentioned_in(message):
                message_split = message.content.split()
                if "kick" in message_split:
                    members = list(filter(lambda u: u != self.user, message.mentions))
                    if members:
                        message = await self.chan_main.send(f"MAOU! **{', '.join(list(map(lambda m: m.name, members)))}** est sur le point d'être kické.\nRéagissez à ce message avec au moins 3 emojis {self.emoji_to_string(self.grant_emoji)} pour valider la décision!")
                        self.kick_messages_in_wait[message.id] = members

                elif "lick" in message_split:
                    members = list(filter(lambda u: u != self.user, message.mentions))
                    if not members:
                        members = [message.author]

                    lick = self.emoji_to_string(self.get_emoji_by_name('lick'))
                    message = await message.channel.send(f"{lick} **{f' {lick} '.join(list(map(lambda m: m.name, members)))}** {lick}")

                elif "emojis" in message_split:
                    response = await message.channel.send('MAOU :brain:\n_(je réfléchis...)_')
                    emojis = list(map(lambda e : {"emoji": e, "score": 0, "string": self.emoji_to_string(e)}, self.server.emojis))
                    if "here" in message_split:
                        channels = [message.channel]
                    else:
                        channels = self.get_text_channels()

                    after = datetime.datetime.now() - datetime.timedelta(days = 180)
                    for channel in channels:
                        async for m in channel.history(limit = 100, after = after, oldest_first = False):
                            if m.author != self.user:
                                for e in emojis:
                                    e["score"] += sum(map(lambda r : r.count, filter(lambda r : r.emoji == e["emoji"], m.reactions))) + m.content.count(e["string"])

                    # Sort emojis from most to least used
                    emojis = sorted(emojis, key = lambda e : -e["score"])

                    # Put emojis with their scores into strings
                    emojis = list(map(lambda e : f'{self.emoji_to_string(e["emoji"])}`{str(e["score"]).zfill(3)}`', emojis))

                    # Join into a single string
                    emojis = "Emojis :\n" + "".join(emojis)

                    await response.edit(content = emojis[:2000])

                elif "hurt" in message_split:
                    raise Exception("*grocha vient de chier une ogive, tape un sprint et se prend une porte*")

                elif "version" in message_split:
                    sha1 = subprocess.run(['git', 'rev-parse', 'HEAD'], capture_output=True, text=True).stdout.strip()
                    date = subprocess.run(['git', 'log', '-1', '--format=%cd'], capture_output=True, text=True).stdout.strip()
                    await message.channel.send(f'MAOU :date:\nSha1: `{sha1}`\nDate: `{date}`')

                elif "update" in message_split:
                    rebase_results = subprocess.run(['git stash && git pull --rebase && git stash pop'], shell=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                    await message.channel.send(f'MAOU! _(updating myself!)_\n**Results**\n```{rebase_results.stdout.strip()}```')

                elif "restart" in message_split:
                    await message.channel.send(f'MAOU~ _(takin a short nap bruh)_')
                    restart_results = subprocess.run(['systemctl', '--user', 'restart', 'bot-grocha'], capture_output=True, text=True).stderr.strip()

                else:
                    await message.channel.send("MAOU?")

        except Exception as e:
            await self.deal_with_exception(e, message.channel)

        sys.stderr.flush()
        sys.stdout.flush()

    async def deal_with_exception(self, e, channel):
        # Allow a debugger to catch the exception if it's watching
        if not sys.gettrace() is None:
            raise e

        # Warn the original channel about the problem
        if channel:
            await channel.send(f"MAOUUUUU :frowning:\n_(je suis cassé! Regarde #{self.chan_debug.name} pour plus d'infos sur le problème)_")

        # Send callstack to debug channel
        tb = sys.exc_info()[2]
        exception_str = "\n".join(traceback.format_exception(e, value=e, tb=tb))
        await self.chan_debug.send(f'_Le bobo de Grocha :_\n```{exception_str}```')


class GrochaBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.reactions = True
        intents.presences = True

        discord.Client.__init__(self, intents=intents)

        self.guild_clients = {}

    def get_guild_client(self, guild_id):
        if not guild_id in self.guild_clients.keys():
            self.guild_clients[guild_id] = GrochaGuild(self, self.get_guild(guild_id))
        return self.guild_clients[guild_id]

    async def on_ready(self):
        for guild in self.guilds:
            await self.get_guild_client(guild.id).on_ready()

    async def on_member_join(self, member):
        await self.get_guild_client(member.guild.id).on_member_join(member)

    async def on_reaction_add(self, reaction, user):
        await self.get_guild_client(user.guild.id).on_reaction_add(reaction, user)

    async def on_message(self, message):
        await self.get_guild_client(message.guild.id).on_message(message)

client = GrochaBot()
client.run(config.BOT_TOKEN)
