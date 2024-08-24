from cogs.stats import Stats
from utils import *


class Level(commands.Cog):
	def __init__(self, bot:commands.Bot):
		self.bot = bot
		self.clear_cd = 0
		self.lvl_cooldown = {}


	@tasks.loop(seconds=10)
	async def levelcheck(self):
		guild = self.bot.get_guild(GUILD_ID)
		level = level_db.full()
		await self.levelcheck_clear(guild, level)
		await self.levelcheck_voice(guild, level)

	async def levelcheck_clear(self, guild:disnake.Guild, level:dict):
		now = datetime.now(TIMEZONE)
		if now.hour == 0 and now.minute == 0 and self.clear_cd < curTime():
			week_time:list[int] = other_db.find('week_time')
			#Прибирання ролей
			await Stats.DaySummary(guild.get_channel(CHAT_CHANNEL))
			#Зкидання повідомлень
			for member in level:
				if week_time[0] == now.day and week_time[1] == now.month:
					level[member]['messages_week'] = 0
				level[member]['messages_today'] = 0
			#БД
			level_db.update('', level)
			self.clear_cd = curTime()+100
			#Тиждень
			if week_time[0] == now.day and week_time[1] == now.month:
				newtime = (now + timedelta(days=7))
				week_time = [newtime.day, newtime.month]
				other_db.update('week_time', week_time)
			#Актив роль
			role = guild.get_role(ACTIVE_ID)
			for member in role.members:
				if level[str(member.id)]['last_activity']+(86400*7) < curTime():
					try: await member.remove_roles(role)
					except: pass

	async def levelcheck_voice(self, guild:disnake.Guild, level:dict):
		await Stats.Voice(guild)
		for channel in guild.voice_channels:
			if len(channel.members) < 2: continue
			for member in channel.members:
				if member.bot: continue
				if str(member.id) not in level: continue
				if member.voice.self_mute or member.voice.self_deaf or member.voice.mute or member.voice.deaf: continue
				lvl = level_db.find(f"{member.id}")
				lvl["voice"] += 10
				lvl['last_activity'] = curTime()
				if random.randint(1,100) < 20:
					lvl["xp"] += int(len(channel.members)/2)
				level_db.update(f"{member.id}", lvl)


	async def change_level_roles(member:disnake.Member, nextlvl:str):
		try: await member.remove_roles(BRONZE_ID)
		except: pass
		for level in LEVELS:
			role = member.guild.get_role(LEVELS[level]['role'])
			if role in member.roles:
				await member.remove_roles(role)
		await member.add_roles(member.guild.get_role(LEVELS[nextlvl]['role']))

	def get_full_level(member:disnake.Member|int) -> int:
		if isinstance(member, disnake.Member): member = member.id
		level = level_db.find(f"{member}")
		typnm = 1
		for i in list(LEVELS):
			if i == level['type']: break
			typnm += LEVELS[i]['levels']
		return typnm + level['level']


	@commands.Cog.listener()
	async def on_ready(self):
		if not self.levelcheck.is_running():
			self.levelcheck.start()


	@commands.Cog.listener()
	async def on_message(self, message:disnake.Message):
		if not message.guild: return
		if message.guild.id != GUILD_ID: return
		if message.author.bot: return
		author = str(message.author.id)
		register(message.author)
		level = level_db.find(author)
		if author not in self.lvl_cooldown:
			self.lvl_cooldown[author] = {'msg': 0, 'money': 0}

		#Бустер
		if 'booster' in level and level['booster_expire'] <= curTime():
			try: eco_db.delete(f"{author}.booster_{level['booster']}")
			except: pass
			level.pop('booster')
			level.pop('booster_expire')

		#Повідомлення
		if message.channel.id in LVL_CHANNELS:
			level['messages'] += 1
			level['messages_today'] += 1
			level['messages_week'] += 1
		
		#Активність
		level['last_activity'] = curTime()
		if level['type'] != 'bronze':
			active = message.guild.get_role(ACTIVE_ID)
			if active not in message.author.roles:
				try: await message.author.add_roles(active)
				except: pass

		#Рівень
		if self.lvl_cooldown[author]['msg'] < curTime() and message.channel.id in LVL_CHANNELS and len(message.content) > 1:
			#Блок. русні
			if any(x in message.content.lower() for x in open_banwords()): return

			#Бустер
			addpercent = 0
			if 'booster' in level:
				booster = level['booster']
				if booster != 0: addpercent = percent(random.randint(20,65)*2, booster)

			#Гроші
			if self.lvl_cooldown[author]['money'] < curTime() and level['messages'] > 90 and random.randint(1,100) < 3 and message.channel.id == CHAT_CHANNEL:
				eco = eco_db.find(f"{author}.money")
				if eco >= 100:
					money = int(level['messages']/70 * random.uniform(1.0, 1.3))
					if money > 100: money = random.randint(80,101)
					#Embed
					emb = disnake.Embed(description=f"Ви отримали **{money}{CURRENCY}** за спілкування в чаті!\nПродовжуйте спілкуватись, щоб отримати більше.", color=GREEN, timestamp=message.created_at)
					await message.channel.send(f"{message.author.mention}", embed=emb)
					#БД
					self.lvl_cooldown[author]['money'] = curTime()+600
					eco_db.update(f"{author}.money", eco+money)

			#XP
			if level['type'] == list(LEVELS)[-1] and level['level'] >= LEVELS[level['type']]['levels']:
				return level_db.update(author, level)
			level['xp'] += random.randint(20,50) + int(addpercent)
			self.lvl_cooldown[author]['msg'] = curTime() + 25

			#Новий рівень
			if level['xp'] > get_xp_goal(message.author):
				level['level'] += 1
				level['xp'] = 0
				type = level['type']
				#Видача бронзи
				if type == "bronze":
					try: await message.author.add_roles(message.guild.get_role(BRONZE_ID))
					except: pass

				#Гроші за рівень
				eco = eco_db.find(f"{author}.money")
				money_reward = ""
				if eco >= 100:
					money = int(MONEY_PER_LEVEL * Level.get_full_level(message.author))
					money_reward = f"💸 Ви отримали **{money}{CURRENCY}**\n"
					eco_db.update(f"{author}.money", eco+money)
				#Зміна типу рівня
				nextlvl = level['type']
				if LEVELS[type]['levels'] > 0 and level['level'] > LEVELS[type]['levels']:
					lvls = list(LEVELS)
					nextlvl = lvls[lvls.index(type)+1]
					await Level.change_level_roles(message.author, nextlvl)
					level['type'] = nextlvl
					level['level'] = 1

				#Повідомлення
				emb = disnake.Embed(description=(
					f"### Вітаю, {message.author.mention}, ваш рівень було підвищено!\n"
					f"💬 Новий рівень — **` {LEVELS[nextlvl]['name']} {level['level']} `**!\n"
					f"{money_reward}"
					f"🏆 Для підвищення рівню, спілкуйся більше на сервері!"
				), color=str_to_hex(LEVELS[nextlvl]['color']))
				emb.set_footer(text=message.guild.name, icon_url=message.guild.icon)
				emb.set_thumbnail(url=message.guild.icon)
				await message.channel.send(embed=emb)
		level_db.update(author, level)


	@commands.slash_command(name="rank", description="📋 Подивитися свій рівень активу.", guild_ids=[GUILD_ID])
	@commands.cooldown(1, 2, commands.BucketType.user)
	async def rank(self, inter:disnake.CommandInteraction, учасник:disnake.Member = commands.Param(description="Користувач", default=None)):
		if inter.locale == disnake.Locale.ru:
			return await error(inter, "<:cross:1127281507430576219> **При ініціалізації мови сталася помилка!**")
		member = учасник
		if not member: member = inter.author
		register(member)
		level = level_db.find(f"{member.id}")
		img = Image.new("RGBA", (900,200), color="#121212")

		#Бустер
		boostermsg = ""
		if 'booster' in level:
			booster, boostexp = level['booster'], level['booster_expire']
			if boostexp <= curTime() and boostexp > 0:
				try: eco_db.delete(f"{member.id}.booster_{level['booster']}")
				except: pass
				level.pop('booster')
				level.pop('booster_expire')
				level_db.update(f"{member.id}", level)
			elif booster != 0:
				boostermsg = f"🚀 Активний бустер: +{booster}%"

		#Аватар
		mobile = ""
		if member.is_on_mobile(): mobile = "_mobile"
		data = BytesIO(await member.display_avatar.read())
		pfp = Image.open(data).resize((156,156)).convert('RGBA')
		mask = Image.open(f'./img/misc/mask_status{mobile}.png').resize((156,156)).convert('L')
		output = ImageOps.fit(pfp, mask.size, centering=(0.5, 0.5))
		output.putalpha(mask)
		paste(img, output, (22,22))

		#Статус
		size, offset = (34,34), (0,0)
		if mobile != '': size, offset = (34,52), (0,-20)
		status = Image.open(f"./img/status/{member.status}{mobile}.png").resize(size, resample=Image.NEAREST).convert("RGBA")
		paste(img, status, (137+offset[0],137+offset[1]))

		#Іконка
		type = level['type']
		icon = Image.open(f'./img/levels/{type}.png').resize((30,30)).convert('RGBA')
		paste(img, icon, (206,32))

		#Текст
		idraw = ImageDraw.Draw(img)
		idraw.text((247, 27), member.display_name, font=loadFont(28), fill="white")
		idraw.text((205, 108), "РІВ.", font=loadFont(18, "arial.ttf"), fill="white")
		lvl_text = f"{LEVELS[type]['name']} {str(level['level'])}"
		idraw.text((245, 92), lvl_text, font=loadFont(32),fill="white")

		#Отримання рангу
		sorted_top, lvls = {}, level_db.full()
		for mem in lvls:
			sorted_top[mem] = Level.get_full_level(int(mem))*50000 + lvls[mem]["xp"]
		sorted_top = sorted(sorted_top, key=lambda k: -sorted_top[k])
		toppos = sorted_top.index(str(member.id))+1
		#Ранг
		w = idraw.textlength(lvl_text, loadFont(32))
		idraw.text((255+w, 108), "РАНГ.", font=loadFont(18, "arial.ttf"), fill="white")
		idraw.text((310+w, 92), f"#{toppos}", font=loadFont(32), fill="white")

		#XP
		text = f"{level['xp']}/{get_xp_goal(member)} XP"
		w = idraw.textlength(text, loadFont(28))
		idraw.text((868-w, 97), text, font=loadFont(28), fill="white")

		#Войс
		icon = Image.open("img/misc/voice.png").resize((26,26))
		paste(img, icon, (840,72))
		text = f"{voicelevel(level['voice'])}"
		w = idraw.textlength(text, loadFont(24))
		idraw.text((836-w, 69), text, font=loadFont(24), fill="white")

		#Повідомлення
		icon = Image.open("img/misc/message.png").resize((26,26))
		paste(img, icon, (840,45))
		text = f"{level['messages']}"
		w = idraw.textlength(text, loadFont(24))
		idraw.text((836-w, 45), text, font=loadFont(24), fill="white")

		#Прогрес бар
		num = 100 * level['xp']
		num = num / get_xp_goal(member)
		image_bar(idraw, 200, 138, 640, 40, num/100,"#313131",f"#{LEVELS[type]['color']}")

		#Збереження
		img.save(f"rank_{member.id}.png")
		await inter.send(boostermsg, file=disnake.File(fp=f"rank_{member.id}.png"), delete_after=600)
		os.remove(f"rank_{member.id}.png")


def setup(bot:commands.Bot):
	bot.add_cog(Level(bot))