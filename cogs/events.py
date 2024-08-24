from utils import *


class Events(commands.Cog):
	def __init__(self, bot:commands.Bot):
		self.bot = bot
		self.welcome_cd = 0

	@commands.Cog.listener()
	async def on_slash_command_error(self, inter, e:commands.CommandError):
		if isinstance(e, commands.MemberNotFound):
			await error(inter, "<:cross:1127281507430576219> **Користувача не знайдено!**")
		elif isinstance(e, commands.CommandOnCooldown):
			await cooldown_notice(inter, int(curTime()+e.retry_after))
		else:
			raise e.with_traceback(None)

	@commands.Cog.listener()
	async def on_member_join(self, member:disnake.Member):
		if member.guild.id != GUILD_ID or member.bot: return
		if curTime() - member.created_at.timestamp() < YOUNG_TIME: return
		#Ролі при заході
		for role in JOIN_ROLES:
			try: await member.add_roles(member.guild.get_role(role))
			except: continue

	@commands.Cog.listener()
	async def on_member_remove(self, member:disnake.Member):
		if member.guild.id != GUILD_ID or member.bot: return
		#Кольоровий нікнейм
		for role in member.roles:
			if role.name.startswith("#") and role.members == []:
				try: await role.delete()
				except: pass

		#БД
		if str(member.id) in level_db.full():
			level_db.delete(f"{member.id}")
		if str(member.id) in card_db.full():
			card_db.delete(f"{member.id}")
		if str(member.id) in eco_db.full():
			eco_db.delete(f"{member.id}")
		if str(member.id) in cooldown_db.full():
			cooldown_db.delete(f"{member.id}")
		if str(member.id) in pigs_db.full():
			pigs_db.delete(f"{member.id}")
		if str(member.id) in voice_db.full():
			voice_db.delete(f"{member.id}")


	###
	### Рахувалочка та слова
	###
	@commands.Cog.listener("on_message")
	async def minigames(self, message:disnake.Message):
		###
		### Рахувалочка
		###
		if message.channel.id == COUNT_MINIGAME:
			db = other_db.find('minigames')
			if message.content == str(db["Count"]) and message.author.id != int(db["LastCounter"]):
				db["Count"] += 1
				db["LastCounter"] = message.author.id
				db["LastCountMessage"] = message.id
				if message.content.endswith("00"):
					await message.add_reaction('💯')
				elif message.content.endswith("000"):
					await message.add_reaction('🫡')
				elif message.content == "666":
					await message.add_reaction('😱')
				elif message.content == "1488":
					await message.add_reaction('🙋')
				else:
					await message.add_reaction('✅')
				return other_db.update('minigames', db)
			await message.delete()
		###
		### Слова
		###
		elif message.channel.id == WORDS_MINIGAME and not message.author.bot:
			db = other_db.find('minigames')
			lastletter = message.content.lower()[-1]
			msgc = message.content.lower()
			if len(msgc) > 2 and len(msgc) < 15 and msgc[0] == str(db["Letter"]) and message.author.id != int(db["LastWorder"]):
				#Перевірка букв
				for i in msgc:
					if i not in LETTER_LIST:
						return await message.delete()
				#Перевірка останньої літери
				prevlastletter = message.content.lower()[-2]
				if lastletter in ("ь", "и"):
					if prevlastletter in ("ь", "и"):
						return await message.delete()
					else:
						db["Letter"] = prevlastletter
						await message.channel.send(f"Оскільки слів на {lastletter} не існує, наступна буква: **{prevlastletter}**")
				else:
					db["Letter"] = lastletter
				#DB
				db["LastWorder"] = int(message.author.id)
				db["LastWordMessage"] = int(message.id)
				await message.add_reaction('✅')
				return other_db.update('minigames', db)
			await message.delete()

	@commands.Cog.listener("on_message_edit")
	async def minigames_edit(self, before, after:disnake.Message):
		if not after.guild: return
		if after.guild.id != GUILD_ID: return
		if after.channel.id == COUNT_MINIGAME:
			db = other_db.find('minigames')
			if after.id == db["LastCountMessage"]:
				await after.delete()
		elif after.channel.id == WORDS_MINIGAME:
			db = other_db.find('minigames')
			if after.id == db["LastWordMessage"]:
				await after.delete()

	@commands.Cog.listener("on_message_delete")
	async def minigames_delete(self, message:disnake.Message):
		if not message.guild: return
		if message.guild.id != GUILD_ID: return
		if message.channel.id == COUNT_MINIGAME:
			db = other_db.find('minigames')
			if message.id == db["LastCountMessage"]:
				await message.channel.send(f"{message.author.mention} видалив/змінив своє повідомлення! Наступна цифра: **{db['Count']}**")
		if message.channel.id == WORDS_MINIGAME:
			db = other_db.find('minigames')
			if message.id == db["LastWordMessage"]:
				await message.channel.send(f"{message.author.mention} видалив/змінив своє повідомлення! Наступна буква: **{db['Letter']}**")


	@commands.Cog.listener()
	async def on_message(self, message:disnake.Message):
		if not message.guild: return
		if message.guild.id != GUILD_ID: return
		if message.author.bot: return
		###
		### Привітання
		###
		if message.type == disnake.MessageType.new_member and self.welcome_cd < time():
			self.welcome_cd = time()+8
			await asyncio.sleep(2)
			emb = disnake.Embed(description=(
				f"### 👋 Вітаємо, {message.author.mention}!\n"
				f"- **📔 Загальна інформація: <#{INFO_CHANNEL}>**\n"
				f"- **📰 Новини серверу: ⁠<#{NEWS_CHANNEL}>**\n"
				f"- **💸 Економіка серверу: <#{ECONOMY_CHANNEL}>**\n"
			), color=EMBEDCOLOR)
			emb.set_thumbnail(url=message.author.display_avatar)
			emb.set_footer(text="Хай щастить, та доброго шляху на нашому сервері!")
			await message.channel.send(embed=emb)
		###
		### Боти
		###
		if message.channel.id == BOTS_CHANNEL and message.application_id == None:
			try: return await message.delete()
			except: pass
		###
		### Медіа
		###
		if message.channel.id == MEDIA_CHANNEL:
			links = ("youtu.be/", "youtube.com/", "tiktok.com/", "tenor.com/", "discordapp.net/", "discordapp.com/", "twitch.tv/")
			extensions = ('png', 'webp', 'jpg', 'gif', 'jpeg', 'mp4', "mov", "webm", 'avi', 'jfif', 'mp3', 'wav', 'ogg', 'psd')
			if message.attachments != []:
				if message.attachments[0].url.split('.')[-1].split('?')[0].lower() not in extensions:
					await message.delete()
				else: await message.channel.create_thread(name="Коментарі", auto_archive_duration=60, slowmode_delay=5, message=message)
			else:
				if not any(x in message.content.lower() for x in links):
					await message.delete()
				else: await message.channel.create_thread(name="Коментарі", auto_archive_duration=60, slowmode_delay=5, message=message)


	###
	### Пропозиції
	###
	@commands.Cog.listener("on_message")
	async def sug_onmessage(self, message:disnake.Message):
		if not message.guild: return
		if message.author.bot: return
		if message.channel.id != SUGGESTIONS_CHANNEL: return
		if len(message.content) < 5: return await message.delete()
		#Відповідь від адміністрації
		if message.reference and message.author.id == ALEX:
			msg = await message.channel.fetch_message(message.reference.message_id)
			emb = msg.embeds[0]
			num = emb.title.replace(" (Прийнято)","").replace(" (Відхилено)","").split("#")[1]
			sug = sug_db.find(num)
			#Перевірка
			try: await message.delete()
			except: pass
			if sug == {}: return
			if len(sug['answers']) >= 10: return
			if message.content not in ('[accept]', '[deny]', '[view]') and str(message.author.id) in sug['answers']:
				return

			#БД
			if '[accept]' in message.content:
				sug['status'] = 1
			elif '[deny]' in message.content:
				sug['status'] = 2
			elif '[view]' in message.content:
				sug['status'] = 3
			if message.content not in ('[accept]', '[deny]', '[view]'):
				m = message.content.replace("[accept]", "").replace("[deny]", "").replace("[view]", "")
				sug['answers'][str(message.author.id)] = m
			sug_db.update(num, sug)
			await self.generate_sug(msg, num)
		#Нова пропозиція
		else:
			sug = sug_db.full()
			#Перевірка
			await asyncio.sleep(0.8)
			try: await message.channel.fetch_message(message.id)
			except: return
			try: await message.delete()
			except: return
			if list(sug) == []: num = "1"
			else: num = str(int(list(sug)[-1])+1)

			#Реєстрація
			update = {}
			update['author'] = message.author.id
			update['status'] = 0
			update['like'] = []
			update['dislike'] = []
			update['answers'] = {}
			sug_db.update(num, update)

			#Повідомлення
			msg = await self.generate_sug(message, num, edit=False)
			await msg.create_thread(name="Обговорення", slowmode_delay=5)

	@commands.Cog.listener("on_button_click")
	async def sug_button(self, inter:disnake.MessageInteraction):
		if not inter.guild: return
		if inter.author.bot: return
		if inter.channel.id != SUGGESTIONS_CHANNEL: return
		if inter.component.custom_id.startswith("sug_"):
			sug_type = inter.component.custom_id.split("_")[1]
			e = inter.message.embeds[0]
			num = e.title.replace(" (Прийнято)","").replace(" (Відхилено)","").split("#")[1]
			sug = sug_db.find(num)
			if sug == {}: return
			if sug['author'] == inter.author.id: return await error(inter, "<:cross:1127281507430576219> **Ви не можете голосувати за свою пропозицію!**")
			if inter.author.id not in sug['like'] and inter.author.id not in sug['dislike']:
				sug[sug_type].append(inter.author.id)
				sug_db.update(num, sug)
				await inter.response.defer()
				await self.generate_sug(inter.message, num)
			else:
				return await error(inter, "<:cross:1127281507430576219> **Ви вже проголосували за цю пропозицію!**")

	async def generate_sug(self, message:disnake.Message, num:str, edit:bool=True):
		sug = sug_db.find(num)
		stardict = {
			1: "<:star1:1164911815587803156>", 2: "<:star2:1164911818347642960>", 3: "⭐",
			4: "<:star3:1164911820767772692>", 5: "<:star4:1164911824278388787>"
		}
		colordict = {0: 0x1E1F22, 1: GREEN, 2: RED, 3: 0xF2D530}
		titledict = {0: "", 1: " (Прийнято)", 2: " (Відхилено)", 3: " (Розглянуто)"}
		color = colordict[sug['status']]
		title = titledict[sug['status']]

		#Оцінка
		totallike = sug['like']
		totaldislike = sug['dislike']
		totalnum = len(totallike)+len(totaldislike)
		if totalnum != 0:
			rating = (len(totallike)*5 + len(totaldislike)) / totalnum

		#Повідомлення
		if edit:
			e = message.embeds[0]
			emb = disnake.Embed(title=f"💡 Пропозиція #{num}{title}", description=e.description, timestamp=message.created_at, color=color)
			emb.set_author(name=e.author.name, icon_url=e.author.icon_url)
			#Оцінка
			if totalnum == 0:
				emb.add_field(name="📊 Оцінка учасників (0)", value="Поки що оцінки відсутні.")
			else:
				emb.add_field(name=f"📊 Оцінка учасників ({totalnum})", value=f"{round(rating, 1)} {stardict[round(rating)]}")
			#Відповіді
			for author in sug['answers']:
				answer = sug['answers'][author]
				author = message.guild.get_member(int(author))
				emb.add_field(name=f"💬 Відповідь від @{author}:", value=answer, inline=False)

			#Кнопки
			components = []
			if sug['status'] == 0:
				like = disnake.ui.Button(emoji="👍", custom_id="sug_like")
				dislike = disnake.ui.Button(emoji="👎", custom_id="sug_dislike")
				components = [like, dislike]
			else:
				emb.set_footer(text="Пропозиція була розглянута")
				emb.timestamp = datetime.now()
				sug = {}
				sug_db.update(num, sug)
			return await message.edit(embed=emb, components=components)
		else:
			emb = disnake.Embed(title=f"💡 Пропозиція #{num}", description=message.content, timestamp=message.created_at)
			emb.set_author(name=f"@{message.author}", icon_url=message.author.display_avatar)
			emb.add_field(name="📊 Оцінка учасників (0)", value="Поки що оцінки відсутні.")
			like = disnake.ui.Button(emoji="👍", custom_id="sug_like")
			dislike = disnake.ui.Button(emoji="👎", custom_id="sug_dislike")
			return await message.channel.send(embed=emb, components=[like,dislike])


def setup(bot:commands.Bot):
	bot.add_cog(Events(bot))