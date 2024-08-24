from utils import *


class Automod(commands.Cog):
	def __init__(self, bot:commands.Bot):
		self.bot = bot
		self.spam_dict = {}


	#Автомод молодого акаунта
	@commands.Cog.listener()
	async def on_member_join(self, member:disnake.Member):
		if member.bot: return
		if member.guild.id != GUILD_ID: return
		if curTime() - member.created_at.timestamp() < YOUNG_TIME and member.id not in [1246163469552848950]:
			try: await member.send(f"Привіт, {member.mention}! Ваш акакунт занадто молодий, тому він був тимчасово заблокований на сервері **{member.guild.name}**!")
			except: pass
			await member.ban(reason="Автомодерація: Молодий акаунт")
			channel = self.bot.get_channel(ADMIN_TRASH)
			return await channel.send(f"❗ Учасник {member.mention} (@{member}) був заблокований на сервері, по причині: Молодий акаунт\nID: {member.id}\nДата реєстрації: <t:{str(int(member.created_at.timestamp()))}:f>")


	#Кацап покинув сервер
	@commands.Cog.listener()
	async def on_member_remove(self, member:disnake.Member):
		if member.guild.id != GUILD_ID: return
		if member.bot: return
		if member.guild.get_role(KATCAP) in member.roles:
			try: await member.ban(reason="кацап", clean_history_duration=0)
			except: pass
			channel = member.guild.get_channel(SVINARNYK)
			await channel.send(f"🐖 Нажаль кацап {member.mention} не витерпів і покинув сервер, тому він був автоматично заблокований.")


	#Захист від русні
	@commands.Cog.listener()
	async def on_message(self, message:disnake.Message):
		if not message.guild: return
		if message.author.bot: return
		if message.guild.id != GUILD_ID: return
		#Заборона російської мови
		if any(x in message.content.lower() for x in open_banwords()):
			if not message.guild.get_role(UG_IGNORE) in message.author.roles:
				if message.channel.id == SVINARNYK: return
				try: await message.delete()
				except: pass
				msg = await message.channel.send(f"<:chr_norussia:1004631904210927666> Вибачте, <@{message.author.id}>, але на цьому сервері заборонено говорити російською мовою!")
				try: await msg.delete(delay=10)
				except: pass
		#Свинарник
		if message.channel.id == SVINARNYK and message.guild.get_role(KATCAP) in message.author.roles:
			content = emj.replace_emoji(message.content, ":emoji:")
			emojies = re.findall(r":\w+:", content)
			#гімн расієї менше 200 символів
			if len(message.content) >= 200:
				try: await message.delete()
				except: pass
			#кацапам не треба посилання
			if "https://" in message.content.lower() or "http://" in message.content.lower():
				try: await message.delete()
				except: pass
			#стікери, емодзі та пінги, ну і так зрозуміло
			if message.stickers != [] or (message.mentions != [] and not message.reference) or emojies != []:
				try: await message.delete()
				except: pass

	#Захист від русні
	@commands.Cog.listener()
	async def on_message_edit(self, before, after:disnake.Message):
		if not after.guild: return
		if after.guild.id != GUILD_ID: return
		if after.author.bot: return
		#Заборона російської мови
		if any(x in after.content.lower() for x in open_banwords()):
			if not after.guild.get_role(UG_IGNORE) in after.author.roles:
				if after.channel.id == SVINARNYK: return
				try: await after.delete()
				except: pass


def setup(bot:commands.Bot):
	bot.add_cog(Automod(bot))