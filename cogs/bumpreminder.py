from utils import *


class BumpReminder(commands.Cog):
	def __init__(self, bot:commands.Bot):
		self.bot = bot


	###
	### Нагадування про бамп
	###
	@tasks.loop(seconds=15)
	async def bump_reminder(self):
		db = other_db.find('reminders')
		#ceServers /bump
		if db['ceservers']['time'] <= time() and db['ceservers']['sended'] == False:
			channel = self.bot.get_channel(BUMPREMINDER_CHANNEL)
			emb = disnake.Embed(title="⏰ ceServers", description="Час бампнути сервер!\n\n**Команда: </bump:1099601802753749023>**", color=GREEN)
			emb.set_thumbnail(url="https://cdn.discordapp.com/avatars/1081576202902442145/9d6e64701964dac97f072e9cfb8a604a.png?size=1024&format=webp&quality=lossless&width=0&height=281")
			await channel.send("<@&1213500677666504744>", embed=emb)
			db['ceservers']['sended'] = True
			other_db.update('reminders', db)
		#Disflip /bump
		if db['disflip']['time'] <= time() and db['disflip']['sended'] == False:
			channel = self.bot.get_channel(BUMPREMINDER_CHANNEL)
			emb = disnake.Embed(title="⏰ Disflip", description="Час бампнути сервер!\n\n**Команда: </up:1215222844552912928>**", color=GREEN)
			emb.set_thumbnail(url="https://disflip.com/static/images/logo.png")
			await channel.send("<@&1213500677666504744>", embed=emb)
			db['disflip']['sended'] = True
			other_db.update('reminders', db)
		#DISBOARD /bump
		if db['disboard']['time'] <= time() and db['disboard']['sended'] == False:
			channel = self.bot.get_channel(BUMPREMINDER_CHANNEL)
			emb = disnake.Embed(title="⏰ DISBOARD", description="Час бампнути сервер!\n\n**Команда: </bump:947088344167366698>**", color=GREEN)
			emb.set_thumbnail(url="https://cdn3.emoji.gg/emojis/8700-disboard.png")
			await channel.send("<@&1213500677666504744>", embed=emb)
			db['disboard']['sended'] = True
			other_db.update('reminders', db)

	@commands.Cog.listener()
	async def on_ready(self):
		if not self.bump_reminder.is_running():
			self.bump_reminder.start()


	###
	### Нагорода за бамп
	###
	@commands.Cog.listener()
	async def on_message(self, message: disnake.Message):
		if not message.guild: return
		if message.guild.id != GUILD_ID: return
		if message.channel.id != BUMPREMINDER_CHANNEL: return
		inter, bumped = message.interaction, False
		if inter == None: return
		#ceServers /bump
		elif message.author.id == 1081576202902442145 and inter.name.lower() == "bump":
			if len(message.embeds) < 1: return
			if "повідомлення розсилається" in str(message.embeds[0].description).lower():
				db = other_db.find('reminders')
				if db['ceservers']['time'] > curTime(): return
				db['ceservers']['time'] = curTime()+3600*4
				db['ceservers']['sended'] = False
				other_db.update('reminders', db)
				bumped = True
		#Disflip /up
		elif message.author.id == 1125000104970031144 and inter.name.lower() == "up":
			db = other_db.find('reminders')
			if db['disflip']['time'] > curTime(): return
			db['disflip']['time'] = curTime()+3600*4
			db['disflip']['sended'] = False
			other_db.update('reminders', db)
			bumped = True
		#DISBOARD /bump
		elif message.author.id == 302050872383242240 and inter.name.lower() == "bump":
			if len(message.embeds) < 1: return
			if "bump done" in str(message.embeds[0].description).lower():
				db = other_db.find('reminders')
				if db['disboard']['time'] > curTime(): return
				db['disboard']['time'] = curTime()+3600*2
				db['disboard']['sended'] = False
				other_db.update('reminders', db)
				bumped = True
		#Нагорода
		if bumped:
			money:int = eco_db.find(f'{inter.author.id}.money')
			reward = 20
			if datetime.now(TIMEZONE).hour >= 23 or datetime.now(TIMEZONE).hour <= 8:
				reward *= 2
			money += int(reward)
			eco_db.update(f'{inter.author.id}.money', money)
			await message.channel.send(f":heart: Дякуємо за бамп серверу, {inter.author.mention}! Ви отримали {reward}{CURRENCY}", reference=message)


	###
	### Команда
	###
	@commands.slash_command(name="remaining", description="📋 Подивитися, скільки залишилося до бампу.", guild_ids=[GUILD_ID])
	@commands.cooldown(1, 2, commands.BucketType.guild)
	async def remaining(self, inter:disnake.CommandInter):
		if inter.locale == disnake.Locale.ru:
			return await error(inter, "При ініціалізації мови сталася помилка!")
		reminders = other_db.find('reminders')

		#ceServers
		ceservers = "<:check:1127281505153069136> Час бампати!"
		if int(reminders['ceservers']['time']) > curTime():
			ceservers = f"<t:{reminders['ceservers']['time']}:R>, <t:{reminders['ceservers']['time']}:T>"
		#Disflip
		disflip = "<:check:1127281505153069136> Час бампати!"
		if int(reminders['disflip']['time']) > curTime():
			disflip = f"<t:{reminders['disflip']['time']}:R>, <t:{reminders['disflip']['time']}:T>"
		#DISBOARD
		disboard = "<:check:1127281505153069136> Час бампати!"
		if int(reminders['disboard']['time']) > curTime():
			disboard = f"<t:{reminders['disboard']['time']}:R>, <t:{reminders['disboard']['time']}:T>"

		#Embed
		emb = disnake.Embed(description=(
			f"**⏰ Час до бампу:**\n"
			f"- **<:ceServers:1230172702673862786> </bump:1099601802753749023> - {ceservers}**\n"
			f"- **<:Disflip:1230173169130803270> </up:1215222844552912928> - {disflip}**\n"
			f"- **<:Disboard:1230173167440498739> </bump:947088344167366698> - {disboard}**"
		), color=EMBEDCOLOR)
		emb.set_author(name=f"@{inter.author}", icon_url=inter.author.display_avatar)
		await inter.send(embed=emb)


def setup(bot:commands.Bot):
	bot.add_cog(BumpReminder(bot))