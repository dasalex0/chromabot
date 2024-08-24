from utils import *


class Moderation(commands.Cog):
	def __init__(self, bot:commands.Bot):
		self.bot = bot
		self.katcapes = []

	def check_admin(self, member:disnake.Member):
		staff = member.guild.get_role(STAFF_ID)
		if member.id == ALEX or staff in member.roles:
			return True
		return False

	@commands.slash_command(name="add-money", description="👑 Видати гроші користувачу.", guild_ids=[GUILD_ID])
	@commands.cooldown(1, 3, commands.BucketType.user)
	async def addmoney(self, inter:disnake.CommandInter, учасник:disnake.Member, кількість:int=commands.Param(le=10000)):
		member, amount = учасник, кількість
		if self.check_admin(inter.author):
			#Перевірки
			if str(member.id) not in eco_db.full():
				return await error(inter, "**<:cross:1127281507430576219> Користувача немає в базі даних серверу!**")

			#БД
			money = eco_db.find(f"{member.id}.money")
			eco_db.update(f"{member.id}.money", money+amount)
			await success(inter, f"**<:check:1127281505153069136> Успішно видано {hf(amount)}{CURRENCY} на баланс користувача {member.mention}!**")

	@commands.slash_command(name="remove-money", description="👑 Прибрати гроші користувачу.", guild_ids=[GUILD_ID])
	@commands.cooldown(1, 3, commands.BucketType.user)
	async def removemoney(self, inter:disnake.CommandInter, учасник:disnake.Member, кількість:int=commands.Param(le=10000)):
		member, amount = учасник, кількість
		if self.check_admin(inter.author):
			#Перевірки
			if str(member.id) not in eco_db.full():
				return await error(inter, "**<:cross:1127281507430576219> Користувача немає в базі даних серверу!**")
			eco = eco_db.find(f"{member.id}")
			money = eco['money']
			if amount > money: amount = money

			#БД
			eco_db.update(f"{member.id}.money", money-amount)
			await success(inter, f"**<:check:1127281505153069136> Успішно знято {hf(amount)}{CURRENCY} з баланса користувача {member.mention}!**")


	@commands.slash_command(name="set-level", description="👑 Встановити рівень користувачу.", guild_ids=[GUILD_ID])
	@commands.cooldown(1, 300, commands.BucketType.user)
	async def setlevel(
		self, inter:disnake.CommandInter,
		учасник:disnake.Member,
		рівень:str=commands.Param(choices=list(LEVELS)),
		підрвень:int=commands.Param(ge=1, le=3),
		xp:int=commands.Param(default=0)
	):
		member, type, level = учасник, рівень, підрвень
		if self.check_admin(inter.author):
			#Перевірки
			if str(member.id) not in level_db.full():
				return await error(inter, "**<:cross:1127281507430576219> Користувача немає в базі даних серверу!**")
			if LEVELS[type]['levels'] < level:
				return await error(inter, f"**<:cross:1127281507430576219> У цього рівня максимальний підрвень {LEVELS[type]['levels']}!**")
			goal = get_xp_goal(member)
			if xp > goal: xp = goal
			message = ''
			if xp != 0: message = f' та `{xp}` XP'

			#БД
			update = level_db.find(f"{member.id}")
			update['type'] = type
			update['level'] = level
			update['xp'] = xp
			level_db.update(f"{member.id}", update)
			await success(inter, f"**<:check:1127281505153069136> Успішно встановлено рівень `{LEVELS[type]['name']} {level}`{message} користувачу {member.mention}!**")


	@commands.slash_command(name="svin", description="👑 Депортація в свинарник.", guild_ids=[GUILD_ID])
	@commands.cooldown(3, 3600, commands.BucketType.guild)
	async def svin(self, inter:disnake.CommandInter, учасник:disnake.Member):
		member = учасник
		if self.check_admin(inter.author):
			if member.bot:
				return await error(inter, "**<:cross:1127281507430576219> Ви не можете депортувати в свинарник бота!**")
			if member.id in (1165047047653691485, 1050301564310528021):
				return await error(inter, "**<:cross:1127281507430576219> Ви не можете депортувати в свинарник цього користувача!**")

			await success(inter, f"**<:check:1127281505153069136> Ви успішно депортували в свинарник {member.mention}!**")
			self.katcapes.append(member.id)
			try:
				await zakacap(member)
			except:
				return await error(inter, "**<:cross:1127281507430576219> Не вдалося депортувати в свинарник цього користувача!**")

	@commands.slash_command(name="desvin", description="👑 Витянути людину зі свинарника.", guild_ids=[GUILD_ID])
	@commands.cooldown(3, 3600, commands.BucketType.guild)
	async def desvin(self, inter:disnake.CommandInter, учасник:disnake.Member):
		member = учасник
		if self.check_admin(inter.author):
			kacaprole = inter.guild.get_role(KATCAP)
			if member.bot:
				return await error(inter, "**<:cross:1127281507430576219> Ви не можете витягнути зі свинарника бота!**")
			if kacaprole not in member.roles or member.id not in self.katcapes:
				return await error(inter, "**<:cross:1127281507430576219> Цей користувач не кацап!**")

			await success(inter, f"**<:check:1127281505153069136> Ви успішно витягнули {member.mention} зі свинарнику!**")
			try: await member.remove_roles(kacaprole)
			except: pass
			try: await member.add_roles(member.guild.get_role(MEMBER_ROLE_ID))
			except: pass
			self.katcapes.remove(member.id)


	@commands.slash_command(name="ban", description="👑 Заблокувати користувача на сервері.", guild_ids=[GUILD_ID])
	@commands.cooldown(3, 3600*3, commands.BucketType.guild)
	async def ban(self, inter:disnake.CommandInter, користувач:str, причина:str=commands.Param(max_length=100, default=None)):
		member, reason = користувач, причина
		if not reason: reason = "Не вказано"
		if not self.check_admin(inter.author): return
		#Бан по ID
		try:
			memberid = disnake.Object(id=int(member))
			mem = inter.guild.get_member(memberid.id)
			if mem:
				if inter.author.id == mem.id:
					return await error(inter, "<:cross:1127281507430576219> **Ви не можете заблокувати себе!**")
				if mem.bot:
					return await error(inter, "<:cross:1127281507430576219> **Ви не можете заблокувати бота!**")
				if check_active(mem.id):
					return await error(inter, "<:cross:1127281507430576219> **Ви не можете заблокувати цього користувача!**")
			await inter.guild.ban(memberid, reason=f"{inter.author} ({inter.author.id}) - {reason}",clean_history_duration=0)
			emb = disnake.Embed(description=f"<:check:1127281505153069136> Користувач <@{memberid.id}> був заблокований на сервері.", color=GREEN)
			emb.add_field(name="Модератор", value=inter.author.mention)
			emb.add_field(name="Причина", value=reason)
			await inter.send(embed=emb)
		#Звичайний бан
		except:
			member = member.replace("<@","").replace(">","").replace(" ","")
			member = inter.guild.get_member(int(member))
			if not member:
				return await error(inter, "<:cross:1127281507430576219> **Не вдалося заблокувати користувача**")
			if inter.author.id == member.id:
				return await error(inter, "<:cross:1127281507430576219> **Ви не можете заблокувати себе!**")
			if member.bot:
				return await error(inter, "<:cross:1127281507430576219> **Ви не можете заблокувати бота!**")
			if check_active(member.id):
				return await error(inter, "<:cross:1127281507430576219> **Ви не можете заблокувати цього користувача!**")
			#Бан користувача
			try:
				await member.ban(reason=f"{inter.author} ({inter.author.id}) - {reason}", clean_history_duration=0)
				emb = disnake.Embed(description=f"<:check:1127281505153069136> Користувач {member.mention} був заблокований на сервері!", color=GREEN)
				emb.add_field(name="Модератор", value=inter.author.mention)
				emb.add_field(name="Причина", value=reason)
				await inter.send(embed=emb)
			#Помилки
			except:
				await error(inter, "<:cross:1127281507430576219> Не вдалося заблокувати користувача**")

	@commands.slash_command(name="unban", description="👑 Розблокувати користувача на сервері.", guild_ids=[GUILD_ID])
	@commands.cooldown(5, 3600*3, commands.BucketType.user)
	async def unban(self, inter:disnake.CommandInter, id_користувача:int=commands.Param(large=True)):
		member_id = id_користувача
		if not self.check_admin(inter.author): return
		#Команда
		try:
			memberid = disnake.Object(id=member_id)
			await inter.guild.unban(memberid, reason=f"{inter.author} ({inter.author.id})")
			emb = disnake.Embed(description=f"<:check:1127281505153069136> Користувач <@{memberid.id}> був розблокований на сервері.",color=GREEN)
			emb.add_field(name="Модератор", value=inter.author.mention)
			await inter.send(embed=emb)
		except:
			return await error(inter, "<:cross:1127281507430576219> Не вдалося розблокувати користувача**")


	@commands.slash_command(name="kick", description="👑 Вигнати користувача з серверу.", guild_ids=[GUILD_ID])
	@commands.cooldown(3, 3600*3, commands.BucketType.user)
	async def kick(self, inter:disnake.CommandInter, користувач:disnake.Member, причина:str=commands.Param(max_length=100, default=None)):
		member, reason = користувач, причина
		if not reason: reason = "Не вказано"
		if not self.check_admin(inter.author): return
		if inter.author.id == member.id: return await error(inter, "<:cross:1127281507430576219> **Ви не можете вигнати себе!**")
		if check_active(member.id):
			return await error(inter, "<:cross:1127281507430576219> **Ви не можете вигнати цього користувача!**")

		#Кік користувача
		try:
			await member.kick(reason=f"{inter.author} ({inter.author.id}) - {reason}")
			emb = disnake.Embed(description=f"<:check:1127281505153069136> Користувач {member.mention} був вигнаний з серверу.", color=GREEN)
			emb.add_field(name="Модератор", value=inter.author.mention)
			emb.add_field(name="Причина", value=reason)
			await inter.send(embed=emb)
		#Помилки
		except:
			return await error(inter, "<:cross:1127281507430576219> **Не вдалося вигнати користувача!**")


	@commands.slash_command(name="mute", description="👑 Зам'ютити користувача на сервері.", guild_ids=[GUILD_ID])
	@commands.cooldown(3, 600, commands.BucketType.user)
	async def mute(self, inter: disnake.CommandInter, учасник:disnake.Member, тривалість:str, причина:str=commands.Param(default=None, max_length=100)):
		member, duration, reason = учасник, тривалість, причина
		if member.id == inter.author.id: return await error(inter, "<:cross:1127281507430576219> **Ви не можете замутити себе**")
		if not self.check_admin(inter.author): return
		if not reason: reason = "Не вказано"
		if not duration.endswith("s") and not duration.endswith("m") and not duration.endswith("h") and not duration.endswith("d"):
			return await error(inter, "<:cross:1127281507430576219> **Вкажіть час у форматі (s|m|h|d)! Наприклад: 5m**")

		#Час
		dtime = convert_time(duration)
		if dtime in (-1, -2):
			return await error(inter, "<:cross:1127281507430576219> **Вкажіть час у форматі (s|m|h|d)! Наприклад: 5m**")

		#М'ют користувача
		try:
			await member.timeout(duration=dtime, reason=f"{inter.author} ({inter.author.id}) - {reason}")
		except:
			return await error(inter, "<:cross:1127281507430576219> **Не вдалося зам'ютити користувача**")
		#Embed
		emb = disnake.Embed(description=f"<:check:1127281505153069136> Користувач {member.mention} був зам'ютчений на сервері.", color=GREEN)
		emb.add_field(name="Модератор", value=inter.author.mention)
		emb.add_field(name="Причина", value=reason)
		if duration.endswith("d"): duration = f"{duration[:-1]} днів."
		elif duration.endswith("h"): duration = f"{duration[:-1]} год."
		elif duration.endswith("m"): duration = f"{duration[:-1]} хв."
		elif duration.endswith("s"): duration = f"{duration[:-1]} сек."
		emb.add_field(name="Тривалість", value=duration, inline=False)
		await inter.send(embed=emb)

	@commands.slash_command(name="unmute", description="👑 Розм'ютити користувача на сервері.", guild_ids=[GUILD_ID])
	@commands.cooldown(5, 300, commands.BucketType.user)
	async def unmute(self, inter:disnake.CommandInter, користувач:disnake.Member):
		member = користувач
		if not self.check_admin(inter.author): return
		if member.current_timeout:
			try:
				await member.timeout(duration=0)
			except:
				return await error(inter, "<:cross:1127281507430576219> **Не вдалося розм'ютити користувача!**")
			#Відповідь
			emb = disnake.Embed(description=f"<:check:1127281505153069136> Користувач {member.mention} був розм'ютчений на сервері!", color=GREEN)
			emb.add_field(name="Модератор", value=inter.author.mention)
			await inter.send(embed=emb)
		else:
			return await error(inter, "<:cross:1127281507430576219> **Користувач не зам'ютчений!**")


	@commands.slash_command(name="clear", description="👑 Очистити кількість останніх повідомлень.", guild_ids=[GUILD_ID])
	@commands.cooldown(2, 3600, commands.BucketType.user)
	async def clear(self, inter: disnake.CommandInter, кількість:int, учасник:disnake.Member=commands.Param(default=None)):
		amount, member = кількість, учасник
		if inter.author.id != ALEX: return
		await inter.response.defer(ephemeral=True)
		#Всі повідомлення
		if not member:
			try:
				await inter.channel.purge(limit=amount+1)
			except:
				return await error(inter, "<:cross:1127281507430576219> **Не вдалося очистити повідомлення!**")
			await success(inter, f"<:check:1127281505153069136> **Успішно очищено {amount} повідомлень!**", ephemeral=True)
		#Учасник
		else:
			try:
				await inter.channel.purge(limit=amount, check=lambda m: m.author == member)
			except:
				return await error(inter, "<:cross:1127281507430576219> **Не вдалося очистити повідомлення!**")
			await success(inter, f"<:check:1127281505153069136> **Успішно очищено {amount} повідомлень від користувача {member.mention}!**", ephemeral=True)


def setup(bot:commands.Bot):
	bot.add_cog(Moderation(bot))