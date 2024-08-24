from utils import *


class Card(commands.Cog):
	def __init__(self, bot:commands.Bot):
		self.bot = bot


	def GMC(type:str):
		files = os.listdir(f"./img/card/{type}")
		largest = 0
		for number in files:
			if not number.endswith('.png'): continue 
			if 'mobile' in number: continue
			if int(number.replace(".png","")) > largest:
				largest = int(number.replace(".png",""))
		return largest


	@commands.Cog.listener("on_button_click")
	async def edit_card_button(self, inter: disnake.MessageInteraction):
		### Редагування картки
		if inter.component.custom_id.startswith("editcard_"):
			if int(inter.component.custom_id.split("_")[1]) != inter.author.id:
				return await error(inter, "<:cross:1127281507430576219> **Ви можете редагувати тільки свою картку!**")
			await self.edit_card(inter, edit=False)

		### Назад
		elif inter.component.custom_id.startswith("back_"):
			if int(inter.component.custom_id.split("_")[1]) != inter.author.id:
				return await error(inter, "<:cross:1127281507430576219> **Дивитися інвентар може тільки виконавець команди!**")
			member = inter.guild.get_member(int(inter.component.custom_id.split("_")[2]))
			if member == None:
				return await error(inter, "<:cross:1127281507430576219> **Не вдалося знайти користувача! (Можливо його більше немає на сервері)**")
			await self.card_func(inter, member, edit=True)

		### Інвентар
		elif inter.component.custom_id.startswith("inv_"):
			if int(inter.component.custom_id.split("_")[1]) != inter.author.id:
				return await error(inter, "<:cross:1127281507430576219> **Дивитися інвентар може тільки виконавець команди!**")
			member = inter.guild.get_member(int(inter.component.custom_id.split("_")[2]))
			if member == None:
				return await error(inter, "<:cross:1127281507430576219> **Не вдалося знайти користувача! (Можливо його більше немає на сервері)**")
			await self.inventory(inter, member, inter.author)


		### Переключення між картками
		elif inter.component.custom_id in ("prev_card", "next_card"):
			if inter.component.custom_id == "prev_card": n = -1
			else: n = 1
			type, num = inter.message.components[0].children[1].custom_id.split("/")[1].split(":")
			carddb = card_db.find(f"{inter.author.id}")

			bought = type+'s'
			await Card.GenSelectImage(inter.author, int(num)+n, type)

			#Назад
			check = bool(int(num)+n < 1)
			prevbtn = disnake.ui.Button(emoji="<:1_:1074946080858460201>", custom_id="prev_card", disabled=check)
			#Вперед
			check = bool(int(num)+n >= Card.GMC(type))
			nextbtn = disnake.ui.Button(emoji="<:2_:1074946078618685520>", custom_id="next_card", disabled=check)
			#Купити
			if not int(num)+n in carddb[bought]:
				with open(f"img/card/{type}/{int(num)+n}.json", encoding='utf-8') as f: price = json.load(f)['price']
				chosbtn = disnake.ui.Button(style=disnake.ButtonStyle.green, label=f"{price}", emoji=CURRENCY, custom_id=f"buy_card/{type}:{int(num)+n}")
			#Вибрати
			else:
				check = bool(carddb[type] == int(num)+n)
				chosbtn = disnake.ui.Button(style=disnake.ButtonStyle.blurple, label="Вибрано" if check else "Вибрати", custom_id=f"choose_card/{type}:{int(num)+n}", disabled=check)

			await inter.response.edit_message(attachments=None, files=[disnake.File(fp=f"{inter.author.id}.png")], components=[prevbtn,chosbtn,nextbtn])
			try: os.remove(f"{inter.author.id}.png")
			except: pass


		### Вибрати картку
		elif inter.component.custom_id.startswith("choose_card"):
			type, num = inter.message.components[0].children[1].custom_id.split("/")[1].split(":")
			with open(f"img/card/{type}/{num}.json", encoding='utf-8') as f: db = json.load(f)
			name = db['name']

			#Назад
			check = bool(int(num) < 1)
			prevbtn = disnake.ui.Button(emoji="<:1_:1074946080858460201>", custom_id="prev_card", disabled=check)
			#Вперед
			check = bool(int(num) >= Card.GMC(type))
			nextbtn = disnake.ui.Button(emoji="<:2_:1074946078618685520>", custom_id="next_card", disabled=check)
			#Вибрати
			chosbtn = disnake.ui.Button(style=disnake.ButtonStyle.blurple, label="Вибрано", custom_id=f"choose_card/{type}:{num}", disabled=True)

			card_db.update(f"{inter.author.id}.{type}", int(num))
			await inter.response.edit_message(components=[prevbtn,chosbtn,nextbtn])
			await success(inter, f"<:check:1127281505153069136> **Успішно вибрано `{name}`!**", ephemeral=True)


		### Купівля картки
		elif inter.component.custom_id.startswith("buy_card"):
			type, num = inter.message.components[0].children[1].custom_id.split("/")[1].split(":")
			bought = type+'s'
			eco = eco_db.find(f"{inter.author.id}")
			with open(f"img/card/{type}/{num}.json", encoding='utf-8') as f: db = json.load(f)
			price, name = db['price'], db['name']
			#Купівля
			if eco['money'] >= price:
				#Назад
				check = bool(int(num) < 1)
				prevbtn = disnake.ui.Button(emoji="<:1_:1074946080858460201>", custom_id="prev_card", disabled=check)
				#Назад
				check = bool(int(num) >= Card.GMC(type))
				nextbtn = disnake.ui.Button(emoji="<:2_:1074946078618685520>", custom_id="next_card", disabled=check)
				#Вибрати
				chosbtn = disnake.ui.Button(style=disnake.ButtonStyle.blurple, label="Вибрати", custom_id=f"choose_card/{type}:{num}")
				await inter.response.edit_message(components=[prevbtn,chosbtn,nextbtn])
				#Видавання
				eco_db.update(f"{inter.author.id}.money", eco['money']-price)
				update:list = card_db.find(f"{inter.author.id}.{bought}")
				update.append(int(num))
				card_db.update(f"{inter.author.id}.{bought}", update)
				await success(inter, f"<:check:1127281505153069136> **Успішно куплено `{name}` по ціні {price}{CURRENCY}!**", ephemeral=True)
			else: return await error(inter, f"<:cross:1127281507430576219> **У вас не вистачає грошей! ({hf(eco['money'])}/{hf(price)}{CURRENCY})**")


	@commands.Cog.listener("on_dropdown")
	async def edit_card_dropdown(self, inter:disnake.MessageInteraction):
		if inter.component.custom_id == "card_edit":
			if inter.values[0] in ("background", "frame", "deco"):
				cardb = card_db.find(f"{inter.author.id}")
				num = cardb[inter.values[0]]
				#Назад
				check = bool(int(num)-1 < 1)
				prevbtn = disnake.ui.Button(emoji="<:1_:1074946080858460201>", custom_id="prev_card", disabled=check)
				#Вперед
				check = bool(int(num)+1 >= Card.GMC(inter.values[0]))
				nextbtn = disnake.ui.Button(emoji="<:2_:1074946078618685520>", custom_id="next_card", disabled=check)
				#Вибрати
				chosbtn = disnake.ui.Button(style=disnake.ButtonStyle.blurple, label="Вибрати", custom_id=f"choose_card/{inter.values[0]}:{num}", disabled=True)
				await Card.GenSelectImage(inter.author, num, inter.values[0])
				await inter.response.edit_message(content=None, embeds=[], file=disnake.File(fp=f"{inter.author.id}.png"), components=[prevbtn,chosbtn,nextbtn])
				try: os.remove(f"{inter.author.id}.png")
				except: pass

			elif inter.values[0] in ('color'):
				value = card_db.find(f"{inter.author.id}.color")
				components = disnake.ui.TextInput(label="Колір", placeholder="Колір", value=value, custom_id="color", min_length=6, max_length=7)
				modal = disnake.ui.Modal(title="Змінити колір", custom_id="edit_color", components=components)
				await inter.response.send_modal(modal)


	@commands.Cog.listener(name="on_modal_submit")
	async def edit_card_modal(self, inter:disnake.ModalInteraction):
		if inter.custom_id == "edit_color":
			text = list(inter.text_values.items())[0][1]

			try: hex_color = str(text).replace("#","")
			except: return await error(inter, f"<:cross:1127281507430576219> **Вкажіть колір у вигляді HEX, наприклад #ff0000**")

			try: str_to_hex(hex_color)
			except: return await error(inter, f"<:cross:1127281507430576219> **Вкажіть колір у вигляді HEX, наприклад #ff0000**")

			card_db.update(f"{inter.author.id}.color", str(hex_color))
			await self.edit_card(inter, edit=True)


	async def edit_card(self, inter:disnake.Interaction, edit:bool):
		register(inter.author)
		carddb = card_db.find(f"{inter.author.id}")
		color = carddb['color']

		with open(f"img/card/background/{carddb['background']}.json", encoding='utf-8') as f: background = json.load(f)['name']
		with open(f"img/card/frame/{carddb['frame']}.json", encoding='utf-8') as f: frame = json.load(f)['name']
		with open(f"img/card/deco/{carddb['deco']}.json", encoding='utf-8') as f: deco = json.load(f)['name']
		emb = disnake.Embed(color=str_to_hex(color))
		emb.add_field("🎨・Фон картки", value=f" `{background}`", inline=False)
		emb.add_field("🎨・Рамка картки", value=f" `{frame}`", inline=False)
		emb.add_field("🎨・Рамка аватарки", value=f" `{deco}`", inline=False)
		emb.set_author(name=f"@{inter.author}", icon_url=inter.author.display_avatar)

		options = [
			disnake.SelectOption(label="Змінити колір", emoji="🎨", value="color"),
			disnake.SelectOption(label="Змінити фон картки", emoji="🎨", value="background"),
			disnake.SelectOption(label="Змінити рамку картки", emoji="🎨", value="frame"),
			disnake.SelectOption(label="Змінити рамку аватарки", emoji="🎨", value="deco")
		]
		dropdown = disnake.ui.StringSelect(min_values=1, max_values=1, options=options, custom_id="card_edit")
		if edit: await inter.response.edit_message(embed=emb, components=dropdown)
		else: await inter.response.send_message(embed=emb, components=dropdown, ephemeral=True)


	async def GenSelectImage(member:disnake.Member, num:int, type:str):
		#Створення Зображення
		carddb = card_db.find(f'{member.id}')
		img = Image.new("RGBA", (950, 439), "#292929")
		idraw = ImageDraw.Draw(img)
		idraw.rectangle([(0,0), (949,438)], width=24, outline="black")

		#Інше
		bg = Image.open(f"img/card/background/{carddb['background']}.png").convert("RGBA").resize((500,315))
		mobile = ""
		if member.is_on_mobile(): mobile = "_mobile"

		#Заголовок
		title = {'background': 'фону картки', 'frame': 'рамки картки', 'deco': 'рамки аватарки'}[type]
		idraw.text((31, 27), f"Вибір {title}", font=loadFont(22), fill="#CCCCCC", stroke_width=2, stroke_fill="black")
		#Сторінка
		text = f"{num}/{Card.GMC(type)}"
		w = idraw.textlength(text, loadFont(16))
		idraw.text((img.width/2-w/2, 393), text, font=loadFont(16), fill="#CCCCCC", stroke_width=2, stroke_fill="black")

		#1 Картка
		if num > 0:
			custom = Image.open(f"img/card/{type}/{num-1}.png").convert("RGBA").resize((500,315))
			paste(img, bg, (70,76))
			paste(img, custom, (70,76))

		#3 Картка
		if num < int(Card.GMC(type)):
			custom = Image.open(f"img/card/{type}/{num+1}.png").convert("RGBA").resize((500,315))
			paste(img, bg, (378,76))
			paste(img, custom, (378,76))

		#Центральна картка
		deco = Image.open(f"img/card/decorations{mobile}.png").convert("RGBA").resize((526,330))
		alpha = deco.getchannel('A')
		deco = Image.new('RGBA', deco.size, color=f"#{carddb['color']}")
		deco.putalpha(alpha)
		deco2 = Image.open(f"img/card/decorations_1.png").convert("RGBA").resize((526,330))
		custom = Image.open(f"img/card/{type}/{num}.png").convert("RGBA").resize((526,330))
		#Вставлення
		bg = bg.resize((526,330))
		paste(img, bg, (211,67))
		if type == "background":
			paste(img, custom, (211,67))
			paste(img, deco, (211,67))
		else:
			paste(img, deco, (211,67))
			paste(img, custom, (211,67))
		paste(img, deco2, (211,67))

		img.save(f"{member.id}.png")


	async def inventory(self, inter:disnake.MessageInteraction, member:disnake.Member, author:disnake.Member):
		register(inter.author)
		register(member)
		jobs = jobs_db.full()
		eco = eco_db.find(f"{member.id}")
		carddb = card_db.find(f"{member.id}")
		if 'pig' in eco: pig = pigs_db.find(f"{member.id}")
		items = items_db.full()

		#Створення зображення
		mobile = ""
		if member.is_on_mobile(): mobile = "_mobile"

		#Фон
		bgtype = carddb['background']
		if not os.path.exists(f"img/card/background/{bgtype}.png"): bgtype = 0
		img = Image.open(f"img/card/background/{bgtype}.png").convert("RGBA")
		idraw = ImageDraw.Draw(img)

		#Рамка
		frametype = carddb['frame']
		if not os.path.exists(f"img/card/frame/{frametype}.png"): frametype = 0
		frame = Image.open(f"img/card/frame/{frametype}.png").convert("RGBA")
		paste(img, frame, (0,0))

		#Декорація
		decotype = carddb['deco']
		if os.path.exists(f'img/card/deco/{decotype}{mobile}.png'):
			carddeco = f"img/card/deco/{decotype}{mobile}.png"
		else:
			carddeco = f"img/card/deco/{decotype}.png"
		if not os.path.exists(carddeco): decotype = 0
		carddeco = Image.open(carddeco).convert("RGBA")

		#Основа
		deco1 = Image.open(f"img/card/decorations_1.png").convert("RGBA")
		paste(img, deco1, (0,0))
		deco = Image.open(f"img/card/decorations{mobile}.png").convert("RGBA")
		alpha = deco.getchannel('A')
		deco = Image.new('RGBA', deco.size, color=f"#{carddb['color']}")
		deco.putalpha(alpha)
		paste(img, deco, (0,0))

		#Аватар
		asset = member.display_avatar.with_size(256)
		data = BytesIO(await asset.read())
		pfp = Image.open(data).convert("RGBA").resize((215,215))
		mask = Image.open(f'./img/misc/mask_status{mobile}.png').resize((215,215)).convert('L')
		output = ImageOps.fit(pfp, mask.size, centering=(0.5, 0.5))
		output.putalpha(mask)
		paste(img, output, (76,137))

		#Статус
		size, offset = (54,54), (0,0)
		if mobile != '': size, offset = (54,80), (5,-24)
		status = Image.open(f"./img/status/{member.status}{mobile}.png").resize(size, resample=Image.NEAREST).convert("RGBA")
		paste(img, status, (230+offset[0], 293+offset[1]))

		#Нік
		text = member.display_name[:26]
		idraw.text((320, 145), text, font=loadFont(30), fill="white")
		w = idraw.textlength(text, loadFont(30))
		if member.display_name != str(member) and member.display_name not in (None,'') and len(text) < 20:
			idraw.text((320+w+8, 152), f"(@{member})", font=loadFont(22), fill="#999999")

		#Робота
		text = jobs[str(eco['job'])]['name']
		size = int(26 - len(text)/3)
		w = int(idraw.textlength(text, loadFont(size)))
		x = int(66+(235 - w) / 2)
		idraw.text((x, 377), text, font=loadFont(size), fill="white", stroke_width=2, stroke_fill="black")
		#Гроші
		text = f"{hf(eco['money'])}"
		w = int(idraw.textlength(text, loadFont(28)))
		x = int(66+(233 - w) / 2)
		idraw.text((x-10, 377+size+9), text, font=loadFont(26), fill=("#DD5858" if eco['money'] < 0 else "white"), stroke_width=2, stroke_fill="black")
		#Гроші (Іконка)
		i = Image.open(f'./img/misc/money.png').resize((31,31)).convert('RGBA')
		paste(img, i, (x+w-7, 377+size+9+2))

		x, y, count = 317, 214, 1
		#Предмети
		bg = Image.open(f"img/card/inventory.png").convert("RGBA")
		paste(img, bg, (311, 208))
		for item in eco:
			if item not in items: continue
			i = Image.open(f"img/items/{item}.png").convert("RGBA").resize((47,47))
			paste(img, i, (x+2,y+2))
			if "pick" in item:
				num = 100 * eco["pick_durability"]
				num = num / PICK_DURABILITY[item]
				prog = num/100
				color = pick_color(prog)
				image_bar(idraw, x, y+47, 50, 5, prog, "black", color)
			count += 1
			x += 50+6
			if count > 9:
				count, x = 1, 317
				y += 50+7
		#Кількість предметів
		x, y, count = 317, 214, 1
		for item in eco:
			if item not in items: continue
			if int(eco[item]) != 1:
				idraw.text((x+35, y+37), str(eco[item]), font=loadFont(18), fill="white", stroke_width=1, stroke_fill="black")
			count += 1
			x += 50+6
			if count > 9:
				count, x = 1, 317
				y += 50+7

		#Зберігання
		paste(img, carddeco, (0,0))
		img.save(f"inv_{inter.author.id}.png")
		backbtn = disnake.ui.Button(emoji="↩️", custom_id=f"back_{author.id}_{member.id}")
		await inter.response.edit_message(attachments=None, file=disnake.File(fp=f"inv_{inter.author.id}.png"), components=[backbtn])
		try: os.remove(f"inv_{inter.author.id}.png")
		except: pass


	###
	### Картка
	###
	@commands.slash_command(name="card", description="📋 Показує інформацію про вказаного учасника.", guild_ids=[GUILD_ID])
	@commands.cooldown(1, 30, commands.BucketType.user)
	async def card(self, inter:disnake.CommandInteraction, учасник:disnake.Member = None):
		if inter.locale == disnake.Locale.ru:
			return await error(inter, "<:cross:1127281507430576219> **При ініціалізації мови сталася помилка!**")
		await self.card_func(inter, учасник)

	async def card_func(self, inter:disnake.CommandInteraction, member:disnake.Member=None, edit:bool=False):
		#Загальне
		if not member: member = inter.author
		if member.bot: return await error(inter, "<:cross:1127281507430576219> **Ви не можете дивитися картку ботів!**")
		if not edit:
			await inter.response.send_message("**<a:loading:1161659712773832835> Малюємо картку...**", delete_after=600)
		#БД
		register(member)
		carddb = card_db.find(f"{member.id}")
		level = level_db.find(f"{member.id}")
		money = eco_db.find(f"{member.id}.money")


		#Фон
		bgtype = carddb['background']
		if not os.path.exists(f"img/card/background/{bgtype}.png"): bgtype = 0
		img = Image.open(f"img/card/background/{bgtype}.png").convert("RGBA")
		idraw = ImageDraw.Draw(img)
		mobile = ""
		if member.is_on_mobile(): mobile = "_mobile"

		#Рамка
		frametype = carddb['frame']
		if not os.path.exists(f"img/card/frame/{frametype}.png"): frametype = 0
		frame = Image.open(f"img/card/frame/{frametype}.png").convert("RGBA")
		paste(img, frame, (0,0))

		#Декорація
		decotype = carddb['deco']
		if os.path.exists(f'img/card/deco/{decotype}{mobile}.png'):
			carddeco = f"img/card/deco/{decotype}{mobile}.png"
		else:
			carddeco = f"img/card/deco/{decotype}.png"
		if not os.path.exists(carddeco): decotype = 0
		carddeco = Image.open(carddeco).convert("RGBA")

		#Основа
		deco1 = Image.open(f"img/card/decorations_1.png").convert("RGBA")
		paste(img, deco1, (0,0))
		deco = Image.open(f"img/card/decorations{mobile}.png").convert("RGBA")
		alpha = deco.getchannel('A')
		deco = Image.new('RGBA', deco.size, color=f"#{carddb['color']}")
		deco.putalpha(alpha)
		paste(img, deco, (0,0))


		#Аватар
		asset = member.display_avatar.with_size(256)
		data = BytesIO(await asset.read())
		pfp = Image.open(data).convert("RGBA").resize((215,215))
		mask = Image.open(f'./img/misc/mask_status{mobile}.png').resize((215,215)).convert('L')
		output = ImageOps.fit(pfp, mask.size, centering=(0.5, 0.5))
		output.putalpha(mask)
		paste(img, output, (76,137))

		#Статус
		size, offset = (54,54), (0,0)
		if mobile != '': size, offset = (54,80), (5,-24)
		status = Image.open(f"./img/status/{member.status}{mobile}.png").resize(size, resample=Image.NEAREST).convert("RGBA")
		paste(img, status, (230+offset[0], 293+offset[1]))


		#Іконки
		x = 317
		iconsdict = {BOY_ID: "boy",  GIRL_ID: "girl",  STAFF_ID: "staff",  DONATER_ID: "donater",  BOOSTER_ID: "booster",  ACTIVE_ID: "active",  PROGRAM_ID: "program"}
		for icon in iconsdict:
			if inter.guild.get_role(icon) not in member.roles: continue
			icon = Image.open(f'./img/card/icons/{iconsdict[icon]}.png').resize((37,37)).convert('RGBA')
			paste(img, icon, (x,197))
			x += 45


		#Нік
		text = member.display_name[:26]
		idraw.text((320, 145), text, font=loadFont(30), fill="white")
		w = idraw.textlength(text, loadFont(30))
		if member.display_name != str(member) and member.display_name not in (None,'') and len(text) < 20:
			idraw.text((320+w+8, 152), f"(@{member})", font=loadFont(22), fill="#999999")

		#Текст
		texts:list[str] = []
		y = 250
		if inter.guild.get_role(BOY_ID) in member.roles:
			texts.append(f"Приєднався: {member.joined_at.day} {MONTHS[member.joined_at.month]} {member.joined_at.year} року")
			texts.append(f"Відправив {hf(level['messages'])} повідомлень")
		elif inter.guild.get_role(GIRL_ID) in member.roles:
			texts.append(f"Приєдналася: {member.joined_at.day} {MONTHS[member.joined_at.month]} {member.joined_at.year} року")
			texts.append(f"Відправила {hf(level['messages'])} повідомлень")
		texts.append(f"Повідомлень за сьогодні: {hf(level['messages_today'])}")
		texts.append("%skip_20%")
		texts.append(f"%img_money% Гроші: {hf(money)}")
		for text in texts:
			x = 0
			if text.startswith("%skip_"): y += int(text.split('_')[1][:-1]); continue
			if "%img_money%" in text:
				i = Image.open(f'./img/misc/money.png').resize((27,27)).convert('RGBA')
				paste(img, i, (316, y+3))
				x = 27
			idraw.text((x+317, y), text.replace("%img_money%",""), font=loadFont(24), fill="white", stroke_width=2, stroke_fill="black")
			y += 45


		#Рівень
		type = level['type']
		text = f"{LEVELS[type]['name']} {str(level['level'])}"
		w = idraw.textlength(text, loadFont(22))
		idraw.text((66+int((233 - w) / 2), 369), text, font=loadFont(22), fill="white", stroke_width=2, stroke_fill="black")
		#Войс
		text = f"Войс: {voicelevel(level['voice'])}"
		w = idraw.textlength(text, loadFont(22))
		idraw.text((66+int((233 - w) / 2), 405), text, font=loadFont(22), fill="white", stroke_width=2, stroke_fill="black")

		#Іконка
		medal = Image.open(f'./img/levels/{type}.png').resize((66,66)).convert('RGBA')
		paste(img, medal, (142,443))


		#Збереження
		paste(img, carddeco, (0,0))
		img.save(f"card_{inter.author.id}.png")
		editbtn = disnake.ui.Button(emoji="<:pencil3:1109780156685492274>", custom_id=f"editcard_{member.id}", disabled=bool(inter.author.id != member.id))
		invbtn = disnake.ui.Button(emoji="💼", custom_id=f"inv_{inter.author.id}_{member.id}")
		if edit:
			await inter.response.edit_message(content="", attachments=[], file=disnake.File(fp=f"card_{inter.author.id}.png"), components=[editbtn, invbtn])
		else:
			await inter.edit_original_response(content="", attachments=[], file=disnake.File(fp=f"card_{inter.author.id}.png"), components=[editbtn, invbtn])
		try: os.remove(f"card_{inter.author.id}.png")
		except: pass


def setup(bot:commands.Bot):
	bot.add_cog(Card(bot))