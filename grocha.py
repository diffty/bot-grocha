import sys
import datetime

import discord

import config


class GrochaBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.reactions = True
        intents.presences = True

        discord.Client.__init__(self, intents=intents)

        self.greet_messages_in_wait = {}
        self.kick_messages_in_wait = {}
    
    def search_for_main_role(self, role_name):
        for role in self.server.roles:
            if role.name == role_name:
                return role

    def search_for_emoji(self, emoji_name):
        for emoji in self.server.emojis:
            if emoji.name == emoji_name:
                return emoji

    async def on_ready(self):
        print("MAOU?")
        sys.stdout.flush()

        self.server = self.get_guild(config.GUILD_ID)
        self.chan_welcome = self.server.get_channel(config.WELCOME_CHANNEL_ID)
        self.chan_main = self.server.get_channel(config.MAIN_CHANNEL_ID)
        self.role_main = self.search_for_main_role(config.MAIN_ROLE_NAME)

        if not self.role_main:
            raise Exception(f"<!!> Can't find role named {config.MAIN_ROLE_NAME}")

        self.grant_emoji = self.search_for_emoji(config.GRANT_EMOJI_NAME)

        if not self.grant_emoji:
            raise Exception(f"<!!> Can't find emoji named {config.GRANT_EMOJI_NAME}")

    async def on_member_join(self, member):
        message = await self.chan_main.send(f"MAOU! **{member.name}** vient d'arriver sur le serveur.\nRéagis à ce message avec l'emoji <:{self.grant_emoji.name}:{self.grant_emoji.id}> pour lui donner les droits!")
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
        if self.user.mentioned_in(message):
            if "kick" in message.content.split():
                members = list(filter(lambda u: u != self.user, message.mentions))
                if members:
                    message = await self.chan_main.send(f"MAOU! **{', '.join(list(map(lambda m: m.name, members)))}** est sur le point d'être kické.\nRéagissez à ce message avec au moins 3 emojis <:{self.grant_emoji.name}:{self.grant_emoji.id}> pour valider la décision!")
                    self.kick_messages_in_wait[message.id] = members

            if "lick" in message.content.split():
                members = list(filter(lambda u: u != self.user, message.mentions))
                if not members:
                    members = [message.author]

                message = await message.channel.send(f"<:lick:784211260732473376> **{' <:lick:784211260732473376> '.join(list(map(lambda m: m.name, members)))}** <:lick:784211260732473376>")

            else:
                await message.channel.send("MAOU?")


client = GrochaBot()
client.run(config.BOT_TOKEN)
