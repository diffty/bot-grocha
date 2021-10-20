import sys
import traceback
import datetime

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
                    print("<!!> Error while kicking members : " + str(e))

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

                    message = await message.channel.send(f"<:lick:784211260732473376> **{' <:lick:784211260732473376> '.join(list(map(lambda m: m.name, members)))}** <:lick:784211260732473376>")

                elif "emojis" in message_split:
                    response = message.channel.send('MAOU <:brain:900421793934880808>\n_(je réfléchis...)_')
                    emojis = list(map(lambda e : {"emoji": e}, self.server.emojis))
                    for e in emojis:
                        if "here" in message_split:
                            text_channels = [message.channel]
                        else:
                            text_channels = self.get_text_channels()

                        score = 0
                        after = datetime.datetime.now() - datetime.timedelta(days = 180)
                        emoji_string = self.emoji_to_string(e["emoji"])
                        for channel in text_channels:
                            async for m in channel.history(limit = 100, after = after, oldest_first = False):
                                if m.author != self.user:
                                    score += len(list(filter(lambda r : r.emoji == e["emoji"], m.reactions)))
                                    score += m.content.count(emoji_string)
                        e["score"] = score

                    # Sort emojis from most to least used
                    emojis = sorted(emojis, key = lambda e : -e["score"])

                    await response.edit(content = "Emojis :\n" + "\n".join(list(map(lambda e : f'{self.emoji_to_string(e["emoji"])}: {str(e["score"])}', emojis))))

                elif "hurt" in message_split:
                    raise Exception("*grocha vient de chier une ogive, tape un sprint et se prend une porte*")

                else:
                    await message.channel.send("MAOU?")

        except Exception as e:
            await message.channel.send('MAOUUUUU :(\n_(je suis cassé! Regarde #mongrocha pour plus d\'infos sur le problème)_')
            tb = sys.exc_info()[2]
            exception_str = "\n".join(traceback.format_exception(e, value=e, tb=tb))
            await self.chan_debug.send(f'_Le bobo de Grocha :_\n```{exception_str}```')

        sys.stderr.flush()
        sys.stdout.flush()


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
        print("MAOU?")
        sys.stdout.flush()

    async def on_member_join(self, member):
        await self.get_guild_client(member.guild.id).on_member_join(member)

    async def on_reaction_add(self, reaction, user):
        await self.get_guild_client(user.guild.id).on_reaction_add(reaction, user)

    async def on_message(self, message):
        await self.get_guild_client(message.guild.id).on_message(message)

client = GrochaBot()
client.run(config.BOT_TOKEN)
