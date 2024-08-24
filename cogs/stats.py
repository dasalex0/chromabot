from utils import *


class Stats(commands.Cog):
	def __init__(self, bot:commands.Bot):
		self.bot = bot
		self.emoji_cache = {}

	@commands.Cog.listener("on_dropdown")
	async def stats_select(self, inter:disnake.MessageInteraction):
		if inter.component.custom_id == "stats_type":
			author_id = inter.message.interaction.author.id
			if inter.author.id != author_id:
				return await error(inter, "<:cross:1127281507430576219> **Ви не автор повідомлення!**")
			await self.stats_func(inter, inter.values[0], edit=True)

	@commands.slash_command(name="stats", description="📋 Подивитися статистику серверу.", guild_ids=[GUILD_ID])
	@commands.cooldown(1, 30, commands.BucketType.user)
	async def stats(self, inter:disnake.CommandInter):
		await self.stats_func(inter, "messages")

	async def stats_func(self, inter:disnake.CommandInter, type:str="messages", edit:bool=False):
		stats = stats_db.find(type)
		size = (1120, 426)
		color = (245, 132, 48)
		secondary_color = (245, 132, 48, 50)
		#Завантаження
		if edit:
			select = disnake.ui.StringSelect(options=[disnake.SelectOption(emoji="<a:loading:1161659712773832835>", label="Завантаження...", default=True)], custom_id="stats_type", disabled=True)
			await inter.response.edit_message(components=[select])
		else:
			await inter.response.send_message("**<a:loading:1161659712773832835> Отримання інформації...**", delete_after=300)
		#Отримання статистики
		chart = {}
		if type == "emojis":
			for emoji in sorted(stats, key=lambda k: -stats[k]):
				chart[emoji] = stats[emoji]
		else:
			for key in list(stats)[-15:]:
				if isinstance(stats[key], list):
					chart[key] = len(stats[key])
				else:
					chart[key] = stats[key]
			chart_values = list(chart.values())

		#Фон
		img = Image.open("img/misc/stats.png").convert("RGBA")
		idraw = ImageDraw.Draw(img)
		bgimg = Image.open("img/misc/stats3.png").convert("RGBA")
		paste(img, bgimg, (18, 149))

		#Емодзі
		if type == "emojis":
			index, gindex = 1, 1
			y = 205
			text = "Топ 40 найпопулярніших емодзі"
			w = idraw.textlength(text, font=loadFont(32))
			idraw.text((img.width/2-w/2, 150), text, fill="#CCCCCC", font=loadFont(32))
			for e in list(chart):
				if gindex > 40: break
				x = index*113-34
				emoji = disnake.utils.find(lambda m: m.name.lower() == str(e).lower(), inter.guild.emojis)
				if not emoji: continue
				if emoji in self.emoji_cache:
					url = self.emoji_cache[emoji]
				else:
					response = requests.get(emoji.url)
					url = BytesIO(response.content)
					self.emoji_cache[emoji] = url
				emoji = Image.open(url).convert("RGBA").resize((96,96))
				paste(img, emoji, (x, y))
				w = idraw.textlength(hf(stats[e]), font=loadFont(22))
				idraw.text((x+96/2-w/2, y+94), hf(stats[e]), fill="#CCCCCC", font=loadFont(22))
				index += 1
				gindex += 1
				if index > 10:
					index = 1
					y += 122
		#Графік
		else:
			#Лінії
			img2 = Image.new('RGBA', (size[0], size[1]), (0,0,0,0))
			idraw2 = ImageDraw.Draw(img2)
			#Графік
			img3 = Image.new('RGBA', (size[0], size[1]), (0,0,0,0))
			idraw3 = ImageDraw.Draw(img3)
			maxvalue = int(max(chart_values))
			minvalue = int(min(chart_values))
			def normalize_data_point(x:int, y:int):
				normalized_x = 0 + (x / (len(chart) - 1)) * (img3.width - 0)
				normalized_y = img3.height - 0 - ((y - minvalue) / (maxvalue - minvalue)) * (img3.height - 0)
				return normalized_x, normalized_y

			#Промальовка графіку
			index = 0
			for i in range(len(chart)-1):
				#Координати
				x1, y1 = normalize_data_point(index, chart_values[i])
				x2, y2 = normalize_data_point(index+1, chart_values[i + 1])
				if y1 > 12: y1 -= 7
				else: y1 += 7
				if y2 > 12: y2 -= 7
				else: y2 += 7
				idraw3.ellipse((x1-2, y1-2, x1+2, y1+2), color, width=15)
				idraw3.line((x1, y1, x2, y2), color, width=5)
				#Текст
				text = list(chart.keys())[i].split('.')[:-1]
				if len(text[0]) == 1: text[0] = '0'+text[0]
				if len(text[1]) == 1: text[1] = '0'+text[1]
				text = '.'.join(text)
				idraw.text((70+x1, 623), text, "#797E89", font=loadFont(15, 'arial.ttf'))
				index += 1
			text = list(chart.keys())[-1].split('.')[:-1]
			if len(text[0]) == 1: text[0] = '0'+text[0]
			if len(text[1]) == 1: text[1] = '0'+text[1]
			text = '.'.join(text)
			idraw.text((70+normalize_data_point(index, chart_values[-1])[0], 623), text, "#797E89", font=loadFont(15, 'arial.ttf'))
			ImageDraw.floodfill(img3, (7, img3.height-1), secondary_color)

			#Горизонтальні Лінії
			line_count = 4.0
			label_interval = (maxvalue - minvalue) / line_count
			idraw2.line((0, 2, img.width, 2), (220, 220, 220, 20), 3)
			for i in range(int(line_count+1)):
				#Текст
				value = abs(int(minvalue + i * label_interval))
				if type == 'voice':
					value /= 60*60
					value = round(value, 1)
				else:
					value = hf(value)
				w = idraw.textlength(str(value), loadFont(22, 'arial.ttf'))
				label_y = img3.height - ((minvalue + i * label_interval - minvalue) / (maxvalue - minvalue)) * (img3.height - 0)
				idraw.text((84-w, 184+(label_y-6)), str(value), fill="#FFFFFF", font=loadFont(22, 'arial.ttf'))
				idraw2.line((0, label_y-4, img.width, label_y-3), (220, 220, 220, 20), 3)

			#Об'єднання графіка й ліній
			chartimg = Image.alpha_composite(Image.new('RGBA', (size[0], size[1]), "#2C2C2D"), img2)
			chartimg = Image.alpha_composite(chartimg, img3)
			paste(img, chartimg, (92, 191))
			idraw.line((92, 616, 92+chartimg.width, 616), "#959DAC", 1)

		#Тип (заголовок під хромою)
		title = {"members": "Учасники", "messages": "Повідомлення", "voice": "Години в войсі", "contributors": "Люди в чаті", "voice_contributors": "Люди у войсі", "emojis": "Емодзі"}[type]
		idraw.text((150, 85), f"#{title}", "#797B7F", font=loadFont(24))
		#Заголовок
		value = 0
		if type == 'members':
			value = hf(int(chart[f"{datetime.now(TIMEZONE).day}.{datetime.now(TIMEZONE).month}.{datetime.now(TIMEZONE).year}"]))
			title = "Учасники:"
			title2 = "За сьогодні:"
			value2 = int(chart[f"{datetime.now(TIMEZONE).day}.{datetime.now(TIMEZONE).month}.{datetime.now(TIMEZONE).year}"])
			value2 = int(value2-chart[list(chart)[-2]])
			if value2 > 0:
				value2 = f"+{value2}"
		elif type == 'messages':
			for i in chart_values: value += i
			title = "Загалом:"
			value = hf(value)
			title2 = "За сьогодні:"
			value2 = hf(int(chart[f"{datetime.now(TIMEZONE).day}.{datetime.now(TIMEZONE).month}.{datetime.now(TIMEZONE).year}"]))
		elif type == 'voice':
			for i in chart_values: value += i
			value = voicelevel(value)
			title = "Загалом:"
			title2 = "За сьогодні:"
			value2 = int(chart[f"{datetime.now(TIMEZONE).day}.{datetime.now(TIMEZONE).month}.{datetime.now(TIMEZONE).year}"])
			value2 = voicelevel(value2)
		elif type == 'contributors':
			value = hf(int(chart[f"{datetime.now(TIMEZONE).day}.{datetime.now(TIMEZONE).month}.{datetime.now(TIMEZONE).year}"]))
			title = "За сьогодні:"
		elif type == 'voice_contributors':
			value = hf(int(chart[f"{datetime.now(TIMEZONE).day}.{datetime.now(TIMEZONE).month}.{datetime.now(TIMEZONE).year}"]))
			title = "За сьогодні:"
		elif type == 'emojis':
			title = "Всі емодзі:"
			value = len(inter.guild.emojis)
		titleimg = Image.open("img/misc/stats2.png").convert("RGBA")
		#1 Заголовок
		paste(img, titleimg, (953, 21))
		idraw.text((967, 30), title, "#AAAAAA", font=loadFont(26, 'arial.ttf'))
		idraw.text((967, 60), str(value), "#D6D9DB", font=loadFont(50))
		#2 Заголовок
		if type in ("members", "messages", "voice"):
			paste(img, titleimg, (615, 21))
			idraw.text((629, 30), title2, "#AAAAAA", font=loadFont(26, 'arial.ttf'))
			idraw.text((629, 60), str(value2), "#D6D9DB", font=loadFont(50))

		#Футер
		if type != 'emojis':
			text = "Статистика за останні 15 днів"
			w = idraw.textlength(text, loadFont(28))
			idraw.text((img.width/2-w/2, 682), text, font=loadFont(26), fill="#7C7E7F")

		#Відправка
		options = [
			disnake.SelectOption(label="Учасники", emoji="<:people:1120347122835922984>", value="members", default=bool(type == 'members')),
			disnake.SelectOption(label="Повідомлення", emoji="💬", value="messages", default=bool(type == 'messages')),
			disnake.SelectOption(label="Години в войсі", emoji="🎤", value="voice", default=bool(type == 'voice')),
			disnake.SelectOption(label="Люди в чаті", emoji="<:chr_smilePC:1139909949980422268>", value="contributors", default=bool(type == 'contributors')),
			disnake.SelectOption(label="Люди у войсі", emoji="🗣️", value="voice_contributors", default=bool(type == 'voice_contributors')),
			disnake.SelectOption(label="Емодзі", emoji="<:chr_smileHz:1139909888596783195>", value="emojis", default=bool(type == 'emojis'))
		]
		select = disnake.ui.StringSelect(placeholder="Оберіть тип статистики", options=options, custom_id="stats_type")
		img.save("stats.png")
		if edit:
			await inter.edit_original_response(content="", attachments=[], components=[select], file=disnake.File(fp="stats.png"))
		else:
			await inter.edit_original_response(content="", components=[select], file=disnake.File(fp="stats.png"))
		os.remove("stats.png")



	async def DaySummary(channel:disnake.TextChannel):
		stats = stats_db.full()
		guild = channel.guild
		pattern_old:str = list(stats['voice'])[-2]
		pattern:str = list(stats['voice'])[-1]
		newmembers = int(stats['members'][pattern]-stats['members'][pattern_old])
		if int(newmembers) > 0: newmembers = f"`(+{newmembers})`"
		elif int(newmembers) < 0: newmembers = f"`({newmembers})`"
		else: newmembers = ""

		#Контрібутори
		if isinstance(stats['contributors'][pattern], list): contributors = len(stats['contributors'][pattern])
		else: contributors = stats['contributors'][pattern]
		if isinstance(stats['voice_contributors'][pattern], list): voice_contributors = len(stats['voice_contributors'][pattern])
		else: voice_contributors = stats['voice_contributors'][pattern]

		#Embed
		emb = disnake.Embed(description=(
			f"**<:people:1120347122835922984> Учасники: `{stats['members'][pattern]}` {newmembers}**\n"
			f"**💬 Повідомлень: `{hf(stats['messages'][pattern])}`**\n"
			f"**🎤 Час у войсі: `{voicelevel(stats['voice'][pattern])}`**\n"
			f"**<:chr_smilePC:1139909949980422268> Людей в чатах: `{contributors}`**\n"
			f"**🗣️ Людей у войсах: `{voice_contributors}`**"
		), color=EMBEDCOLOR)
		emb.set_author(name=f"Підсумки дня ({pattern.split('.')[0]} {MONTHS[int(pattern.split('.')[1])]} {pattern.split('.')[2]} р.)", icon_url=guild.icon)
		emb.set_footer(text="Подивитися детальну статистику - /stats")
		await channel.send(embed=emb)
		#Реєстрація паттернів
		if pattern not in stats['members']:
			stats['members'][pattern] = len(channel.guild.members)
		if pattern not in stats['contributors']:
			stats['contributors'][pattern] = []
		if pattern not in stats['voice_contributors']:
			stats['voice_contributors'][pattern] = []
		if pattern not in stats['messages']:
			stats['messages'][pattern] = 0
		if pattern not in stats['voice']:
			stats['voice'][pattern] = 0
		stats_db.update('', stats)


	@commands.Cog.listener()
	async def on_message(self, message:disnake.Message):
		if not message.guild: return
		if message.guild.id != GUILD_ID: return
		if message.author.bot: return
		await Stats.Emojies(message)
		await Stats.Messages(message)

	@commands.Cog.listener()
	async def on_member_join(self, member:disnake.Member):
		await self.Members(member.guild)

	@commands.Cog.listener()
	async def on_member_remove(self, member:disnake.Member):
		await self.Members(member.guild)


	async def Members(self, guild:disnake.Guild):
		if not guild: return
		if guild.id != GUILD_ID: return
		stats = stats_db.full()
		pattern = f"{datetime.now(TIMEZONE).day}.{datetime.now(TIMEZONE).month}.{datetime.now(TIMEZONE).year}"
		stats['members'][pattern] = len(guild.members)
		stats_db.update("members", stats['members'])


	async def Messages(message:disnake.Message):
		if message.channel.id == SVINARNYK: return
		stats = stats_db.full()
		pattern = f"{datetime.now(TIMEZONE).day}.{datetime.now(TIMEZONE).month}.{datetime.now(TIMEZONE).year}"
		#Оптимізація
		for i in stats["contributors"]:
			if i == pattern: continue
			if not isinstance(stats['contributors'][i], list): continue
			stats["contributors"][i] = len(stats["contributors"][i])
		for i in stats["voice_contributors"]:
			if i == pattern: continue
			if not isinstance(stats['voice_contributors'][i], list): continue
			stats["voice_contributors"][i] = len(stats["voice_contributors"][i])
		#Контрібутори
		if pattern not in stats["contributors"]:
			stats["contributors"][pattern] = []
		if message.author.id not in stats["contributors"][pattern]:
			stats["contributors"][pattern].append(message.author.id)
		#Повідомлення
		if pattern in stats["messages"]:
			stats["messages"][pattern] += 1
		else:
			stats["messages"][pattern] = 1
		stats_db.update("", stats)


	async def Emojies(message:disnake.Message):
		if message.channel.id == SVINARNYK: return
		emojis = re.findall(r"<:\w+:\d+>", message.content)
		if emojis == []: return
		if len(emojis) > 3: return
		stats = stats_db.find("emojis")
		guild_emojies = [e.name for e in message.guild.emojis]
		for emoji in emojis:
			emoji = emoji.split(":")[1]
			if emoji not in guild_emojies: continue
			if emoji in stats:
				stats[emoji] += 1
			else:
				stats[emoji] = 1
		stats_db.update("emojis", stats)


	async def Voice(guild:disnake.Guild):
		stats = stats_db.full()
		pattern = f"{datetime.now(TIMEZONE).day}.{datetime.now(TIMEZONE).month}.{datetime.now(TIMEZONE).year}"
		#Контрібутори
		if pattern not in stats["voice_contributors"]:
			stats["voice_contributors"][pattern] = []
		if pattern not in stats['voice']:
			stats['voice'][pattern] = 0
		#Канали
		for channel in guild.voice_channels:
			if channel.members == []: continue
			#Учасники каналів
			for member in channel.members:
				if member.bot: continue
				if member.id not in stats["voice_contributors"][pattern]:
					stats["voice_contributors"][pattern].append(member.id)
				if member.voice.self_mute or member.voice.self_deaf or member.voice.mute or member.voice.deaf: continue
				stats['voice'][pattern] += 10
		stats_db.update("", stats)


def setup(bot:commands.Bot):
	bot.add_cog(Stats(bot))