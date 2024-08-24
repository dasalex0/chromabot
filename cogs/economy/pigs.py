from utils import *


class Pigs(commands.Cog):
	def __init__(self, bot:commands.Bot):
		self.bot = bot
		self.clear_cd = 0
		self.pig_battles = {}


	@tasks.loop(seconds=30)
	async def update_shop(self):
		if datetime.now(TIMEZONE).hour == 0 and datetime.now(TIMEZONE).minute == 0 and self.clear_cd < curTime():
			skins = []
			while len(skins) != 8:
				type = random.choice(['deco', 'eye', 'hat', 'skin', 'face'])
				files = os.listdir(f'img/pigs/{type}')
				random.shuffle(files)
				for file in files:
					if not file.endswith('.json'): continue
					with open(f"img/pigs/{type}/{file}", encoding='utf-8') as f: chance = json.load(f)['chance']
					if random.randint(1,100) < chance and f"{type}:{file[:-5]}" not in skins:
						skins.append(f"{type}:{file[:-5]}")
						break
			self.clear_cd = curTime()+100
			temp_db.update('pig_shop', skins)

	@commands.Cog.listener()
	async def on_ready(self):
		if not self.update_shop.is_running():
			self.update_shop.start()


	def check(self, member:disnake.Member, pigfood:bool=False, other:bool=False):
		inv = eco_db.find(f"{member.id}")
		#Свиня
		if "pig" not in inv:
			if other: return f"У {member.mention} немає свині! Купити її можна в </shop:1213168795728879702>"
			return "У вас немає свині! Купити її можна в </shop:1213168795728879702>"
		#Їжа для свині
		if "pigfood" not in inv and pigfood:
			if other: return f"У {member.mention} немає їжі для свині! Купити її можна в </shop:1213168795728879702>"
			return "У вас немає їжі для свині! Купити її можна в </shop:1213168795728879702>"
		#Реєстрування
		if str(member.id) not in pigs_db.full():
			register_pig(member)

	def get_chance(type:str, skin_id:int):
		with open(f"img/pigs/{type}/{skin_id}.json", encoding='utf-8') as f: chance = json.load(f)['chance']
		chance_dict = {30: '<:pig_legendary:1206239198085120011>', 65: '<:pig_rare:1206239195090387024>', 100: '<:pig_common:1206239196549742612>'}
		if chance > 0:
			for i in chance_dict:
				if chance < i: return chance_dict[i]
		return '<:pig_common:1206239196549742612>'

	def get_age(self, created:int):
		age = curTime()-int(created)
		if age < 3600:
			minutes = round(age/60, 1)
			if minutes == 1: msg = "хвилина"
			elif minutes in (2,3,4): msg = "хвилини"
			else: msg = "хвилин"
			return f"{minutes} {msg}"
		elif age < 86400:
			hours = round(age/60/60, 1)
			if hours == 1: msg = "година"
			elif hours in (2,3,4): msg = "години"
			else: msg = "годин"
			return f"{hours} {msg}"
		elif age < 86400*30:
			days = round(age/24/60/60, 1)
			if days == 1: msg = "день"
			elif days in (2,3,4): msg = "дня"
			else: msg = "днів"
			return f"{days} {msg}"
		else:
			months = round(age/30/24/60/60, 1)
			if months == 1: msg = "місяць"
			elif months in (2,3,4): msg = "місяці"
			else: msg = "місяців"
			return f"{months} {msg}"

	def get_final_page(self, type:str):
		counts = len(os.listdir(f"img/pigs/{type}"))/2
		final_page = int(counts/8)
		if counts % 8 != 0:
			final_page += 1
		if final_page < 1: final_page = 1
		return final_page


	async def GenSelectImage(self, member:disnake.Member, type:str, page:int=1):
		pig = pigs_db.find(f"{member.id}")
		#Фон
		img = Image.new("RGBA", (1425,988), "#292929")
		idraw = ImageDraw.Draw(img)
		idraw.rectangle([(0,0), (1424,987)], width=34, outline="black")

		#Заголовок
		title = {'skin': 'скіну', 'eye': 'очей', 'hat': 'головного убору', 'deco': 'декорації', 'face': 'декорацій обличчя'}[type]
		text = f"Вибір {title} для свині"
		w = idraw.textlength(text, loadFont(42))
		idraw.text((img.width/2-w/2, 40), text, font=loadFont(42), fill="#CCCCCC", stroke_width=2, stroke_fill="black")

		#Предмети
		toppos = 0
		options, index = [], 0
		x, y = 67, 116
		for item in sorted(os.listdir(f"img/pigs/{type}"), key=lambda k: int(k.split('.')[0])):
			if not item.endswith('.png'): continue
			toppos += 1
			if not (toppos > page*8-8 and toppos <= page*8): continue
			#Основа
			skin_id = int(item[:-4])
			if skin_id in pig[type+'s']:
				with open(f"img/pigs/{type}/{skin_id}.json", encoding='utf-8') as f: db = json.load(f)
				rare = Pigs.get_chance(type, skin_id)
				options.append(disnake.SelectOption(label=db['name'], emoji=rare, value=str(skin_id), default=bool(pig[type] == skin_id)))

				#Якщо скін
				if type == "skin":
					custom = Image.open(f"img/pigs/{type}/{skin_id}.png").convert("RGBA").resize((297,297))
					paste(img, custom, (x,y))
				#Додавання вже існуючих частин
				if type != "skin":
					skin = Image.open(f"img/pigs/skin/{pig['skin']}.png").convert("RGBA").resize((297,297))
					paste(img, skin, (x,y))
				if type != "eye":
					eye = Image.open(f"img/pigs/eye/{pig['eye']}.png").convert("RGBA").resize((297,297))
					paste(img, eye, (x,y))
				if type != "deco":
					deco = Image.open(f"img/pigs/deco/{pig['deco']}.png").convert("RGBA").resize((297,297))
					paste(img, deco, (x,y))
				if type != "face":
					face = Image.open(f"img/pigs/face/{pig['face']}.png").convert("RGBA").resize((297,297))
					paste(img, face, (x,y))
				if type != "hat":
					hat = Image.open(f"img/pigs/hat/{pig['hat']}.png").convert("RGBA").resize((297,297))
					paste(img, hat, (x,y))
				#Якщо не скін
				if type != "skin":
					custom = Image.open(f"img/pigs/{type}/{skin_id}.png").convert("RGBA").resize((297,297))
					paste(img, custom, (x,y))
				#Текст
				if skin_id == pig[type]: color = "#D6A019"
				else: color = "#CCCCCC"
				w = idraw.textlength(db['name'], loadFont(26))
				idraw.text((int(x+310/2-w/2), y+305), db['name'], font=loadFont(26), fill=color, stroke_width=2, stroke_fill="black")
			else:
				custom = Image.open(f"img/pigs/unknown.png").convert("RGBA").resize((297,297))
				paste(img, custom, (x,y))
			#Кординати
			x += 331
			index += 1
			if index == 4:
				x = 67
				y = 530

		#Сторінка
		final_page = self.get_final_page(type)
		text = f"{page}/{final_page}"
		w = idraw.textlength(text, loadFont(36))
		idraw.text((img.width/2-w/2, img.height-34-45), text, font=loadFont(36), fill="#CCCCCC", stroke_width=2, stroke_fill="black")

		#Відповідь
		img.save(f"{member.id}.png")
		if options == []: options = ['disabled']
		return options


	async def GenPigImage(self, member:disnake.Member):
		pig = pigs_db.find(f"{member.id}")
		#Видалення старого скіну
		if "default.png" not in pig['image'] and pig['image_id']:
			try:
				channel = self.bot.get_channel(1202307855743733811)
				msg = await channel.fetch_message(pig['image_id'])
				await msg.delete()
			except: pass
		#Дефолтний скін
		if pig['skin'] == 0 and pig['eye'] == 0 and pig['deco'] == 0 and pig['face'] == 0 and pig['hat'] == 0:
			pigs_db.update(f"{member.id}.image", "https://cdn.discordapp.com/attachments/1202307855743733811/1205250828269523034/default.png")
			return
		#Скін
		img = Image.open(f"img/pigs/skin/{pig['skin']}.png").convert("RGBA").resize((256,256))
		#Око
		eye = Image.open(f"img/pigs/eye/{pig['eye']}.png").convert("RGBA").resize((256,256))
		paste(img, eye, (0,0))
		#Декорації
		deco = Image.open(f"img/pigs/deco/{pig['deco']}.png").convert("RGBA").resize((256,256))
		paste(img, deco, (0,0))
		#Декорації для обличчя
		face = Image.open(f"img/pigs/face/{pig['face']}.png").convert("RGBA").resize((256,256))
		paste(img, face, (0,0))
		#Головний убір
		hat = Image.open(f"img/pigs/hat/{pig['hat']}.png").convert("RGBA").resize((256,256))
		paste(img, hat, (0,0))
		#Збереження
		img.save(f"pig_{member.id}.png")
		channel = self.bot.get_channel(1202307855743733811)
		msg = await channel.send(file=disnake.File(fp=f"pig_{member.id}.png"))
		image = msg.attachments[0].url
		pig['image'] = image
		pig['image_id'] = msg.id
		pigs_db.update(f"{member.id}", pig)
		try: os.remove(f"pig_{member.id}.png")
		except: pass


	@commands.Cog.listener("on_button_click")
	async def edit_pig_button(self, inter: disnake.MessageInteraction):
		### Редагування свині
		if inter.component.custom_id.startswith("editpig_"):
			if int(inter.component.custom_id.split("_")[1]) != inter.author.id:
				return await error(inter, "<:cross:1127281507430576219> **Ви можете редагувати тільки свою свиню!**")
			await self.edit_pig(inter, edit=False)

		### Переключення між свинями
		elif inter.component.custom_id.startswith(("prev_pig", "next_pig")):
			if inter.component.custom_id.startswith("prev_pig"): n = -1
			else: n = 1
			type, num = inter.component.custom_id.split("/")[1].split(":")

			#Сторінка
			toppos = 0
			for item in sorted(os.listdir(f"img/pigs/{type}"), key=lambda k: int(k.split('.')[0])):
				if not item.endswith('.png'): continue
				toppos += 1
			#Створення зображення
			final_page = self.get_final_page(type)
			options = await self.GenSelectImage(inter.author, type, page=int(num)+n)

			#Назад
			check = bool(int(num)+n <= 1)
			prevbtn = disnake.ui.Button(emoji="<:1_:1074946080858460201>", custom_id=f"prev_pig/{type}:{int(num)+n}", disabled=check)
			#Вперед
			check = bool(int(num)+n >= final_page)
			nextbtn = disnake.ui.Button(emoji="<:2_:1074946078618685520>", custom_id=f"next_pig/{type}:{int(num)+n}", disabled=check)
			#Вибрати
			select = disnake.ui.StringSelect(placeholder="Вибрати скін", custom_id=f"pig_select/{type}:{int(num)+n}", options=options, disabled=bool(options == ['disabled']))

			await inter.response.edit_message(attachments=None, files=[disnake.File(fp=f"{inter.author.id}.png")], components=[select,prevbtn,nextbtn])
			try: os.remove(f"{inter.author.id}.png")
			except: pass


	@commands.Cog.listener("on_dropdown")
	async def edit_pig_dropdown(self, inter:disnake.MessageInteraction):
		### Купити свиню
		if inter.component.custom_id == "pig_buy":
			pigshop:list[str] = temp_db.find("pig_shop")
			eco = eco_db.find(f"{inter.author.id}")
			type, skin_id = inter.values[0].split(":")
			if inter.values[0] not in pigshop:
				return await error(inter, "<:cross:1127281507430576219> **Скін, який ви намагаєтеся купити, наразі немає в магазині!**")
			with open(f"img/pigs/{type}/{skin_id}.json", encoding='utf-8') as f: db = json.load(f)
			update:list = pigs_db.find(f"{inter.author.id}.{type}s")
			if int(skin_id) in update:
				return await error(inter, f"<:cross:1127281507430576219> **У вас вже є {db['name']}!**")
			#Купівля
			if eco['money'] >= db['price']:
				eco_db.update(f"{inter.author.id}.money", eco['money']-db['price'])
				update.append(int(skin_id))
				pigs_db.update(f"{inter.author.id}.{type}s", update)
				await success(inter, f"<:check:1127281505153069136> **Успішно куплено `{db['name']}` по ціні {db['price']}{CURRENCY}!**", ephemeral=True)
			else:
				return await error(inter, f"<:cross:1127281507430576219> **У вас не вистачає грошей! ({hf(eco['money'])}/{hf(db['price'])}{CURRENCY})**")

		### Вибрати свиню
		elif inter.component.custom_id.startswith("pig_select"):
			type, page = inter.component.custom_id.split("/")[1].split(":")
			page = int(page)
			skin_id = int(inter.values[0])

			#Генерація зображення
			final_page = self.get_final_page(type)
			pigs_db.update(f"{inter.author.id}.{type}", skin_id)
			options = await self.GenSelectImage(inter.author, type, page=page)

			#Інформація про скін
			with open(f"img/pigs/{type}/{skin_id}.json", encoding='utf-8') as f: db = json.load(f)
			name = db['name']

			#Назад
			check = bool(page <= 1)
			prevbtn = disnake.ui.Button(emoji="<:1_:1074946080858460201>", custom_id=f"prev_pig/{type}:{page}", disabled=check)
			#Вперед
			check = bool(page >= final_page)
			nextbtn = disnake.ui.Button(emoji="<:2_:1074946078618685520>", custom_id=f"next_pig/{type}:{page}", disabled=check)
			#Вибрати
			select = disnake.ui.StringSelect(placeholder="Вибрати скін", custom_id=f"pig_select/{type}:{page}", options=options, disabled=bool(options == ['disabled']))

			await inter.response.edit_message(attachments=None, files=[disnake.File(fp=f"{inter.author.id}.png")], components=[select,prevbtn,nextbtn])
			await success(inter, f"<:check:1127281505153069136> **Успішно вибрано `{name}`!**", ephemeral=True)
			await self.GenPigImage(inter.author)
			try: os.remove(f"{inter.author.id}.png")
			except: pass

		if inter.component.custom_id != "pig_edit": return
		if inter.values[0] in ("skin", "eye", "hat", "deco", "face"):
			#Отримання куплених скінів
			type = inter.values[0]
			#Сторінка
			toppos = 0
			for item in sorted(os.listdir(f"img/pigs/{type}"), key=lambda k: int(k.split('.')[0])):
				if not item.endswith('.png'): continue
				toppos += 1
			final_page = self.get_final_page(type)
			#Зображення
			options = await self.GenSelectImage(inter.author, type)

			#Назад
			prevbtn = disnake.ui.Button(emoji="<:1_:1074946080858460201>", custom_id=f"prev_pig/{type}:1", disabled=True)
			#Вперед
			nextbtn = disnake.ui.Button(emoji="<:2_:1074946078618685520>", custom_id=f"next_pig/{type}:1", disabled=bool(1 >= final_page))
			#Вибрати
			select = disnake.ui.StringSelect(placeholder="Вибрати скін", custom_id=f"pig_select/{type}:1", options=options, disabled=bool(options == ['disabled']))
			
			#Відправлення
			await inter.response.edit_message(content=None, embeds=[], file=disnake.File(fp=f"{inter.author.id}.png"), components=[select,prevbtn,nextbtn])
			try: os.remove(f"{inter.author.id}.png")
			except: pass

		if inter.values[0] in ("rename"):
			components = disnake.ui.TextInput(label="Нове ім'я", min_length=3, max_length=15, custom_id="name")
			modal = disnake.ui.Modal(title="Перейменування свині", components=[components], custom_id="rename_pig")
			await inter.response.send_modal(modal)


	@commands.Cog.listener("on_modal_submit")
	async def edit_pig_modal(self, inter:disnake.ModalInteraction):
		if inter.custom_id != "rename_pig": return
		name = inter.text_values['name']
		register(inter.author)

		pig = pigs_db.full()
		check = self.check(inter.author)
		if check: return await error(inter, f"<:cross:1127281507430576219> **{check}**")

		if pig[str(inter.author.id)]["name"] == name:
			return await error(inter, "<:cross:1127281507430576219> **У вас вже стоїть це ім'я!**")
		if name.lower().startswith("безіменна свиня #"):
			return await error(inter, "<:cross:1127281507430576219> **Не можна встановити таке ім'я!**")
		for p in pig:
			if pig[p]["name"] == name: return await error(inter, "<:cross:1127281507430576219> **Таке ім'я вже зайнято! Придумай щось інше.**")

		pigs_db.update(f"{inter.author.id}.name", name)
		await self.edit_pig(inter, edit=True)


	async def edit_pig(self, inter:disnake.Interaction, edit:bool):
		register(inter.author)
		pig = pigs_db.find(f"{inter.author.id}")
		with open(f"img/pigs/skin/{pig['skin']}.json", encoding='utf-8') as f: skin = json.load(f)['name']
		with open(f"img/pigs/eye/{pig['eye']}.json", encoding='utf-8') as f: eye = json.load(f)['name']
		with open(f"img/pigs/hat/{pig['hat']}.json", encoding='utf-8') as f: hat = json.load(f)['name']
		with open(f"img/pigs/deco/{pig['deco']}.json", encoding='utf-8') as f: deco = json.load(f)['name']
		with open(f"img/pigs/face/{pig['face']}.json", encoding='utf-8') as f: face = json.load(f)['name']
		emb = disnake.Embed(title=pig['name'], color=EMBEDCOLOR)

		emb.add_field("Скін", value=f"{Pigs.get_chance('skin', pig['skin'])} `{skin}`", inline=False)
		emb.add_field("Очі", value=f"{Pigs.get_chance('eye', pig['eye'])} `{eye}`", inline=False)
		emb.add_field("Головний убір", value=f"{Pigs.get_chance('hat', pig['hat'])} `{hat}`", inline=False)
		emb.add_field("Декорації", value=f"{Pigs.get_chance('deco', pig['deco'])} `{deco}`", inline=False)
		emb.add_field("Декорації для обличчя", value=f"{Pigs.get_chance('face', pig['face'])} `{face}`", inline=False)

		emb.set_thumbnail(url=pig['image'])
		emb.set_footer(text="Купити прикраси можна в /pig-shop")
		options = [
			disnake.SelectOption(label="Перейменувати", emoji="📝", value="rename"),
			disnake.SelectOption(label="Змінити скін", emoji="🐖", value="skin"),
			disnake.SelectOption(label="Змінити очі", emoji="👀", value="eye"),
			disnake.SelectOption(label="Змінити головний убір", emoji="🧢", value="hat"),
			disnake.SelectOption(label="Змінити декорації", emoji="👕", value="deco"),
			disnake.SelectOption(label="Змінити декорації обличчя", emoji="💄", value="face")
		]
		dropdown = disnake.ui.StringSelect(min_values=1, max_values=1, options=options, custom_id="pig_edit")
		if edit: await inter.response.edit_message(embed=emb, components=dropdown)
		else: await inter.response.send_message(embed=emb, components=dropdown, ephemeral=True)


	@commands.slash_command(name="pig-info", description="🐖 Подивитися інформацію про свиню.", guild_ids=[GUILD_ID])
	@commands.cooldown(1, 2, commands.BucketType.user)
	async def info(self, inter:disnake.CommandInter, учасник:disnake.Member=commands.Param(description="Користувач",default=None)):
		if inter.locale == disnake.Locale.ru:
			return await error(inter, "<:cross:1127281507430576219> **При ініціалізації мови сталася помилка!**")
		member = учасник
		if not member: member = inter.author
		if member.bot: return await error(inter, "<:cross:1127281507430576219> **У користувача немає свині!**")
		register(inter.author)
		register(member)

		if "pig" in eco_db.find(f"{member.id}"):
			if str(member.id) not in pigs_db.full(): register_pig(member)
			pigs = pigs_db.full()
			#Основне
			sorted_top = sorted(pigs, key=lambda k: -(pigs[k]["mass"]+pigs[k]["power"]*3))
			toppos = sorted_top.index(str(member.id))+1
			pig = pigs[str(member.id)]
			max_amount = int(pig['mass']*50)
			emb = disnake.Embed(title=f"{pig['name']}", description=(
				f"**Вік свині:** `{self.get_age(pig['created'])}`\n"
				f"**Баланс свині:** `{hf(pig['balance'])}/{hf(max_amount)}`{CURRENCY}"
			), color=EMBEDCOLOR)

			#БД скінів
			skin_string, eye_string, hat_string, deco_string, face_string = "", "", "", "", ""
			with open(f"img/pigs/skin/{pig['skin']}.json", encoding='utf-8') as f: skin = json.load(f)['name']
			with open(f"img/pigs/eye/{pig['eye']}.json", encoding='utf-8') as f: eye = json.load(f)['name']
			with open(f"img/pigs/hat/{pig['hat']}.json", encoding='utf-8') as f: hat = json.load(f)['name']
			with open(f"img/pigs/deco/{pig['deco']}.json", encoding='utf-8') as f: deco = json.load(f)['name']
			with open(f"img/pigs/face/{pig['face']}.json", encoding='utf-8') as f: face = json.load(f)['name']

			#Статистика
			emb.add_field(name="Статистика:", value=(
				f"**Сила:** `{pig['power']}/100`💪\n"
				f"**Перемог:** `{pig['wins']}`⚔️\n"
				f"**Поразок:** `{pig['loses']}`💀\n"
				f"**Маса:** `{round(pig['mass'], 1)} кг.`"
			))

			#Скін
			if pig['skin'] > 0: skin_string = f"{Pigs.get_chance('skin', pig['skin'])} `{skin}`\n"
			if pig['eye'] > 0: eye_string = f"{Pigs.get_chance('eye', pig['eye'])} `{eye}`\n"
			if pig['hat'] > 0: hat_string = f"{Pigs.get_chance('hat', pig['hat'])} `{hat}`\n"
			if pig['deco'] > 0: deco_string = f"{Pigs.get_chance('deco', pig['deco'])} `{deco}`\n"
			if pig['face'] > 0: face_string = f"{Pigs.get_chance('face', pig['face'])} `{face}`"
			if pig['skin'] == 0 and pig['eye'] == 0 and pig['hat'] == 0 and pig['deco'] == 0 and pig['face'] == 0:
				skin_string = "`Нічого`"
			emb.add_field(name="Скін:", value=f"**{skin_string}{eye_string}{hat_string}{deco_string}{face_string}**")

			#Відповідь
			emb.set_footer(text=f"Ранг: #{toppos}")
			emb.set_thumbnail(url=pig['image'])
			btn = disnake.ui.Button(emoji="<:pencil3:1109780156685492274>", custom_id=f"editpig_{member.id}", disabled=bool(inter.author.id != member.id))
			await inter.send(embed=emb, components=[btn])
		elif member.id == inter.author.id:
			return await error(inter, "<:cross:1127281507430576219> **У вас немає свині! Купити її можна в </shop:1213168795728879702>**")
		else:
			return await error(inter, "<:cross:1127281507430576219> **У користувача немає свині!**")


	@commands.slash_command(name="pig-deposit", description="🐖 Покласти гроші на баланс свині.", guild_ids=[GUILD_ID])
	@commands.cooldown(1, 2, commands.BucketType.user)
	async def deposit(self, inter:disnake.CommandInter, кількість:str=commands.Param(description="Кількість грошей, які ви збираєтеся покласти на баланс свині. all - всі гроші.")):
		if inter.locale == disnake.Locale.ru:
			return await error(inter, "<:cross:1127281507430576219> **При ініціалізації мови сталася помилка!**")
		amount = кількість
		all_arg = ('all', 'всі', 'все', 'oll', 'усі', 'усе')
		eco = eco_db.find(f"{inter.author.id}")
		register(inter.author)

		if "pig" in eco:
			pig = pigs_db.find(f"{inter.author.id}")
			#Кількість
			try: amount = int(amount)
			except:
				if amount.lower() not in all_arg:
					return await error(inter, f"<:cross:1127281507430576219> **Не вдалося продати цей предмет!**")
				else:
					amount = eco['money']

			#Перевірка
			money = amount
			max_amount = int(pig['mass']*50)
			if (pig['balance']+money > max_amount):
				money = max_amount-pig['balance']
				if money <= 0:
					return await error(inter, f"<:cross:1127281507430576219> **На балансі свині ліміт! ({max_amount}{CURRENCY})\nЩоб підняти його, годуйте вашу свиню </pig-feed:1213168795976466435>.**")
			#Перевірка грошей
			if money > eco['money']:
				return await error(inter, f"<:cross:1127281507430576219> **У вас не вистачає грошей! ({hf(eco['money'])}/{hf(money)}{CURRENCY})**")

			#БД
			eco['money'] -= money
			pig['balance'] += money
			eco_db.update(f"{inter.author.id}", eco)
			pigs_db.update(f"{inter.author.id}", pig)
			#Відповідь
			await success(inter, f"<:check:1127281505153069136> **Ви поклали {hf(money)}{CURRENCY} на баланс свині.**", footer=f"Баланс свині: {hf(pig['balance'])}/{hf(max_amount)}₴")
		else:
			return await error(inter, "<:cross:1127281507430576219> **У вас немає свині! Купити її можна в </shop:1213168795728879702>**")


	@commands.slash_command(name="pig-withdraw", description="🐖 Забрати гроші з балансу свині.", guild_ids=[GUILD_ID])
	@commands.cooldown(1, 2, commands.BucketType.user)
	async def withdraw(self, inter:disnake.CommandInter, кількість:str=commands.Param(description="Кількість грошей, які ви збираєтеся забрати з балансу свині. all - всі гроші.")):
		if inter.locale == disnake.Locale.ru:
			return await error(inter, "<:cross:1127281507430576219> **При ініціалізації мови сталася помилка!**")
		amount = кількість
		all_arg = ('all', 'всі', 'все', 'oll', 'усі', 'усе')
		eco = eco_db.find(f"{inter.author.id}")
		register(inter.author)

		if "pig" in eco:
			pig = pigs_db.find(f"{inter.author.id}")
			#Кількість
			try: amount = int(amount)
			except:
				if amount.lower() not in all_arg:
					return await error(inter, f"<:cross:1127281507430576219> **Не вдалося продати цей предмет!**")
				else:
					amount = pig['balance']
			
			#Перевірка
			money = amount
			if (eco['money']+money > MAX_MONEY):
				money = MAX_MONEY-eco['money']
				if money <= 0:
					return await error(inter, f"<:cross:1127281507430576219> **У вас ліміт грошей! ({hf(MAX_MONEY)}{CURRENCY})**")
			#Перевірка грошей
			if money > pig['balance']:
				return await error(inter, f"<:cross:1127281507430576219> **Ви вказали більше, ніж у вас є на балансі свині! ({hf(pig['balance'])}/{hf(money)}{CURRENCY})**")

			#БД
			eco['money'] += money
			pig['balance'] -= money
			eco_db.update(f"{inter.author.id}", eco)
			pigs_db.update(f"{inter.author.id}", pig)
			#Відповідь
			await success(inter, f"<:check:1127281505153069136> **Ви забрали {hf(money)}{CURRENCY} з балансу свині.**", footer=f"Ваш баланс: {hf(eco['money'])}₴")
		else:
			return await error(inter, "<:cross:1127281507430576219> **У вас немає свині! Купити її можна в </shop:1213168795728879702>**")


	@commands.slash_command(name="pig-shop", description="🐖 Щоденний магазин зі скінами для свині.", guild_ids=[GUILD_ID])
	@commands.cooldown(1, 6, commands.BucketType.user)
	async def shop(self, inter:disnake.CommandInter):
		if inter.locale == disnake.Locale.ru:
			return await error(inter, "<:cross:1127281507430576219> **При ініціалізації мови сталася помилка!**")
		#БД
		pigshop:list[str] = temp_db.find("pig_shop")
		register(inter.author)
		#Перевірка
		check = self.check(inter.author)
		if check: return await error(inter, f"<:cross:1127281507430576219> **{check}**")
		pig = pigs_db.find(f"{inter.author.id}")

		#Фон
		img = Image.new("RGBA", (1425,988), "#222B33")
		idraw = ImageDraw.Draw(img)
		idraw.rectangle([(0,0), (1424,987)], width=34, outline="black")

		#Заголовок
		text = "Щоденний магазин аксесуарів для свині"
		w = idraw.textlength(text, loadFont(42))
		idraw.text((img.width/2-w/2, 40), text, font=loadFont(42), fill="#CCCCCC", stroke_width=2, stroke_fill="black")

		#Предмети
		options, index = [], 0
		x, y = 67, 116
		for item in pigshop:
			#Основа
			type, skin_id = item.split(":")
			is_bought = bool(int(skin_id) in pig[type+'s'])
			with open(f"img/pigs/{type}/{skin_id}.json", encoding='utf-8') as f: db = json.load(f)
			types = {'skin': '🐖 Скін свині', 'eye': '👀 Очі свині', 'hat': '🧢 Головний убір', 'deco': '👕 Декорації (Одяг)', 'face': '💄 Декорації для обличчя'}
			rare = Pigs.get_chance(type, skin_id)
			options.append(disnake.SelectOption(label=db['name'], emoji=("✅" if is_bought else rare), description=types[type], value=item))
			if is_bought:
				color = "#888888"
			else:
				color = "#CCCCCC"

			#Якщо не скін
			if type != "skin":
				item = Image.open(f"img/pigs/skin/0.png").convert("RGBA").resize((297,297))
				if is_bought:
					enhancer = ImageEnhance.Brightness(item)
					item = enhancer.enhance(0.45)
				paste(img, item, (x,y))
			#Якщо скін
			else:
				item = Image.open(f"img/pigs/{type}/{skin_id}.png").convert("RGBA").resize((297,297))
				if is_bought:
					enhancer = ImageEnhance.Brightness(item)
					item = enhancer.enhance(0.45)
				paste(img, item, (x,y))
			#Око
			if type != "eye":
				item = Image.open(f"img/pigs/eye/0.png").convert("RGBA").resize((297,297))
				if is_bought:
					enhancer = ImageEnhance.Brightness(item)
					item = enhancer.enhance(0.45)
				paste(img, item, (x,y))
			#Предмет
			if type != "skin":
				item = Image.open(f"img/pigs/{type}/{skin_id}.png").convert("RGBA").resize((297,297))
				if is_bought:
					enhancer = ImageEnhance.Brightness(item)
					item = enhancer.enhance(0.45)
				paste(img, item, (x,y))
			
			#Текст
			w = idraw.textlength(db['name'], loadFont(26))
			idraw.text((int(x+310/2-w/2), y+305), db['name'], font=loadFont(26), fill=color, stroke_width=2, stroke_fill="black")
			#Ціна
			if is_bought:
				w = idraw.textlength("-- Куплено --", loadFont(24))
				idraw.text((int(x+310/2-w/2), y+345), "-- Куплено --", font=loadFont(24), fill=color, stroke_width=2, stroke_fill="black")
			else:
				w = idraw.textlength(f"{db['price']}", loadFont(24))
				i = Image.open(f'./img/misc/money.png').resize((27,27)).convert('RGBA')
				paste(img, i, (int(x+310/2-w/2-16), y+345))
				idraw.text((int(x+310/2-w/2+16), y+345), f"{db['price']}", font=loadFont(24), fill=color, stroke_width=2, stroke_fill="black")
			#Кординати
			x += 331
			index += 1
			if index == 4:
				x = 67
				y = 530

		#Відповідь
		img.save("pig_shop.png")
		select = disnake.ui.StringSelect(placeholder="Купити скін", custom_id="pig_buy", options=options)
		await inter.send(file=disnake.File(fp="pig_shop.png"), components=[select], ephemeral=True)
		try: os.remove("pig_shop.png")
		except: pass


	@commands.slash_command(name="pig-feed", description="🐖 Годувати вашу свиню.", guild_ids=[GUILD_ID])
	@commands.cooldown(1, 2, commands.BucketType.user)
	async def feed(self, inter:disnake.CommandInter):
		if inter.locale == disnake.Locale.ru:
			return await error(inter, "<:cross:1127281507430576219> **При ініціалізації мови сталася помилка!**")
		register(inter.author)
		#Перевірка
		check = self.check(inter.author, pigfood=True)
		if check: return await error(inter, f"<:cross:1127281507430576219> **{check}**")

		#Затримка
		check = await checkcooldown(inter.author,"pig-feed")
		if check: return await cooldown_notice(inter, check)

		#БД
		eco = eco_db.find(f"{inter.author.id}")
		pig = pigs_db.find(f"{inter.author.id}")
		set_cooldown(inter.author, "pig-feed", 1200)

		#Маса
		message = ""
		mass = random.randint(8, 39)/10
		pig["mass"] = round(pig["mass"]+mass, 1)
		#Сила
		if random.randint(1,100) < int(85-pig["power"]*1.5) and pig["power"] < 100:
			pig["power"] += 1
			message += f"> `+1`💪\n"
		message += f"> `+{mass} кг.`"
		
		#Видалення предмету
		if eco["pigfood"] > 1:
			eco["pigfood"] -= 1
		else:
			eco.pop("pigfood")

		#БД
		pigs_db.update(f"{inter.author.id}", pig)
		eco_db.update(f"{inter.author.id}", eco)
		#Embed
		emb = disnake.Embed(description=f"**🐖 Ви погодували свиню.\n{message}**", color=GREEN)
		emb.set_author(name=f"@{inter.author}", icon_url=inter.author.display_avatar)
		emb.set_thumbnail(url=pig['image'])
		emb.set_footer(text=f"Маса: {round(pig['mass'], 1)} кг.")
		await inter.response.send_message(embed=emb)


	@commands.slash_command(name="pig-fight", description="🐖 Почати битву з іншим гравцем.", guild_ids=[GUILD_ID])
	@commands.cooldown(1, 2, commands.BucketType.user)
	async def fight(self, inter:disnake.CommandInter, учасник:disnake.Member, ставка:int):
		if inter.locale == disnake.Locale.ru:
			return await error(inter, "<:cross:1127281507430576219> **При ініціалізації мови сталася помилка!**")
		money = ставка
		member = учасник
		register(inter.author)
		check = await checkcooldown(inter.author,"pig-fight")
		if check: return await cooldown_notice(inter, check)

		if member == inter.author: return await error(inter, "<:cross:1127281507430576219> **Для битви потрібна друга людина. Як ти збираєшся битися сам з собою?**")
		check = self.check(inter.author)
		if check: return await error(inter, f"<:cross:1127281507430576219> **{check}**")
		check = self.check(member, other=True)
		if check: return await error(inter, f"<:cross:1127281507430576219> **{check}**")
		eco = eco_db.full()
		pig = pigs_db.full()

		if money > 2000: return await error(inter, "<:cross:1127281507430576219> **Ви не можете ставити ставку більше 2,000!**")
		if money < 100: return await error(inter, "<:cross:1127281507430576219> **Ви не можете ставити ставку менше 100!**")
		if eco[str(inter.author.id)]['money'] < money: return await error(inter, f"<:cross:1127281507430576219> **У вас недостатньо грошей! ({eco[str(inter.author.id)]['money']}/{money}{CURRENCY})**")
		if eco[str(member.id)]['money'] < money: return await error(inter, f"<:cross:1127281507430576219> **У {member.mention} недостатньо грошей! ({eco[str(inter.author.id)]['money']}/{money}{CURRENCY})**")

		set_cooldown(inter.author, "pig-fight", 600)
		await success(inter, f"<:check:1127281505153069136> **Ви кинули запрошення на дуель {member.mention}, у нього є 120 секунд, щоб приймати його!**", ephemeral=True)
		emb = disnake.Embed(title="🐖 Свино-дуель", description=f"Користувач {inter.author.mention} надіслав вам запит на дуель! (Ставка {money}{CURRENCY})\nУ вас є 2 хвилини, щоб прийняти цю битву!", color=GREEN, timestamp=inter.created_at)
		emb.add_field(name=f"{pig[str(inter.author.id)]['name']}",value=(
			f"**Сила:** `{pig[str(inter.author.id)]['power']}/100`💪\n"
			f"**Перемог:** `{pig[str(inter.author.id)]['wins']}`⚔️\n"
			f"**Поразок:** `{pig[str(inter.author.id)]['loses']}`💀\n"
			f"**Маса:** `{round(pig[str(inter.author.id)]['mass'], 1)} кг.`"
		))
		emb.add_field(name=f"{pig[str(member.id)]['name']}",value=(
			f"**Сила:** `{pig[str(member.id)]['power']}/100`💪\n"
			f"**Перемог:** `{pig[str(member.id)]['wins']}`⚔️\n"
			f"**Поразок:** `{pig[str(member.id)]['loses']}`💀\n"
			f"**Маса:** `{round(pig[str(member.id)]['mass'], 1)} кг.`"
		))
		emb.set_image(url=pig[str(inter.author.id)]['image'])
		btn = disnake.ui.Button(label="Прийняти", style=disnake.ButtonStyle.green, custom_id="pigbattle_accept")
		msg = await inter.channel.send(member.mention, embed=emb, components=[btn])

		self.pig_battles[str(msg.id)] = {}
		self.pig_battles[str(msg.id)]['user1'] = inter.author.id
		self.pig_battles[str(msg.id)]['user2'] = member.id
		self.pig_battles[str(msg.id)]['money'] = int(money)

		await asyncio.sleep(120)
		try: self.pig_battles.pop(str(msg.id))
		except: pass
		emb = msg.embeds[0]
		emb.title = "🐖 Свино-Дуель (Закінчено)"
		emb.description = emb.description.split("\n")[0]
		emb.color = 0x000000
		await msg.edit(msg.content, embed=emb, components=[])


	@commands.Cog.listener("on_button_click")
	async def fight_button(self, inter:disnake.MessageInteraction):
		if inter.component.custom_id == "pigbattle_accept":
			if str(inter.message.id) not in self.pig_battles: return
			
			#Отримання юзерів
			member1 = inter.guild.get_member(self.pig_battles[str(inter.message.id)]['user1'])
			member2 = inter.guild.get_member(self.pig_battles[str(inter.message.id)]['user2'])
			money = self.pig_battles[str(inter.message.id)]['money']
			if member1 == None: return
			if member2 == None: return
			if inter.author.id != member2.id: return

			#Редагування повідомлення
			emb = inter.message.embeds[0]
			emb.title = "🐖 Свино-Дуель (Закінчено)"
			emb.description = emb.description.split("\n")[0]
			emb.color = 0x000000
			await inter.message.edit(inter.message.content, embed=emb, components=[])

			#Перевірка
			check = self.check(member1)
			if check: return await error(inter, f"<:cross:1127281507430576219> **{check}**", ephemeral=False)
			check = self.check(member2, other=True)
			if check: return await error(inter, f"<:cross:1127281507430576219> **{check}**", ephemeral=False)
			pig = pigs_db.full()
			eco = eco_db.full()
			if eco[str(member1.id)]['money'] < money: return await error(inter, f"<:cross:1127281507430576219> **У {member1.mention} не вистачає грошей! ({eco[str(member1.id)]['money']}/{money}{CURRENCY})**", ephemeral=False)
			if eco[str(member2.id)]['money'] < money: return await error(inter, f"<:cross:1127281507430576219> **У {member2.mention} не вистачає грошей! ({eco[str(member2.id)]['money']}/{money}{CURRENCY})**", ephemeral=False)

			self.pig_battles.pop(str(inter.message.id))
			set_cooldown(member1, "pig-fight", 600)
			set_cooldown(member2, "pig-fight", 600)

			#Отримання статистики
			you = {}
			you['power'] = pig[str(member1.id)]['power']
			you['mass'] = pig[str(member1.id)]['mass']
			opponent = {}
			opponent['power'] = pig[str(member2.id)]['power']
			opponent['mass'] = pig[str(member2.id)]['mass']
			pig_name = pig[str(member1.id)]['name']
			pig2_name = pig[str(member2.id)]['name']

			#Вибір переможця
			points_1 = int(you['mass']) + you['power']*3
			points_2 = int(opponent['mass']) + opponent['power']*3
			points_min = min(points_1, points_2)
			points_max = max(points_1, points_2)
			looser = {points_1: member1, points_2: member2}[points_min]
			winner = {points_1: member1, points_2: member2}[points_max]
			winnername = pig[str(winner.id)]['name']
			battlemsg = ""
			
			#Стата
			pig[str(looser.id)]['loses'] += 1
			eco[str(looser.id)]['money'] -= money
			battlemsg += f"> **{looser.mention}:** `-{money}`{CURRENCY}\n"
			pig[str(winner.id)]['wins'] += 1
			eco[str(winner.id)]['money'] += money
			battlemsg += f"> **{winner.mention}:** `+{money}`{CURRENCY}\n"

			#Маса
			mass1 = round(random.uniform(0.5,5.8), 1)
			pig[str(member1.id)]['mass'] -= mass1
			if pig[str(member1.id)]['mass'] < 1: pig[str(member1.id)]['mass'] = 1
			battlemsg += f"> **{pig_name}:** `-{mass1} кг.`\n"
			
			mass2 = round(random.uniform(0.5,5.8), 1)
			pig[str(member2.id)]['mass'] -= mass2
			if pig[str(member2.id)]['mass'] < 1: pig[str(member2.id)]['mass'] = 1
			battlemsg += f"> **{pig2_name}:** `-{mass2} кг.`\n"

			#Сила
			if pig[str(member1.id)]['power'] < 100:
				pig[str(member1.id)]['power'] += 2
				if pig[str(member1.id)]['power'] > 100: pig[str(member1.id)]['power'] = 100
				battlemsg += f"> **{pig_name}:** `+2`💪\n"
			if pig[str(member2.id)]['power'] < 100:
				pig[str(member2.id)]['power'] += 2
				if pig[str(member2.id)]['power'] > 100: pig[str(member2.id)]['power'] = 100
				battlemsg += f"> **{pig2_name}:** `+2`💪\n"

			#Embed
			pigs_db.update('', pig)
			eco_db.update('', eco)
			emb = disnake.Embed(title="🐖 Свино-дуель", description=f"В дуелі перемагає свиня користувача {winner.mention} **{winnername}**!\n{battlemsg}", color=GREEN)
			emb.set_thumbnail(url=pig[str(winner.id)]['image'])
			try: await inter.send(embed=emb)
			except: await inter.channel.send(embed=emb)


def setup(bot:commands.Bot):
	bot.add_cog(Pigs(bot))