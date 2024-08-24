from utils import *


class Blackjack(commands.Cog):
	def __init__(self, bot:commands.Bot):
		self.bot = bot
		self.blackjack_cooldown = {}
		self.blackjack_sessions = {}


	def check_bj(self, member:disnake.Member):
		cd = BJ_COOLDOWN
		if str(member.id) not in self.blackjack_cooldown:
			self.blackjack_cooldown[str(member.id)] = {'win': 0, 'lastwin': 0}
		if self.blackjack_cooldown[str(member.id)]['win'] >= BJ_MAX and self.blackjack_cooldown[str(member.id)]['lastwin']+cd > curTime():
			self.blackjack_cooldown[str(member.id)] = {'win': 0, 'lastwin': 0}
			set_cooldown(member, 'blackjack', cd)

	def acard(self, points):
		if points+11 > 21: return 1
		return 11

	@commands.Cog.listener("on_button_click")
	async def blackjack_button(self, inter: disnake.MessageInteraction):
		if inter.component.custom_id.startswith(("bj_hit:", "bj_skip:")):
			custom_id = inter.component.custom_id.split(":")
			session = custom_id[1]
			if session not in self.blackjack_sessions: return
			db = self.blackjack_sessions[session]
			#Перевірки
			if inter.author.id not in [db["member"]["id"], db["dealer"]["id"]]:
				return await error(inter, "<:cross:1127281507430576219> **Ви не приймаєте участь в цій грі!**")
			if inter.author.id == db["member"]["id"] and not db["member"]["hit"]:
				return await error(inter, "<:cross:1127281507430576219> **Зараз не ваш хід!**")
			if inter.author.id == db["dealer"]["id"] and not db["dealer"]["hit"]:
				return await error(inter, "<:cross:1127281507430576219> **Зараз не ваш хід!**")
			#Дія
			if inter.component.custom_id.startswith("bj_hit:"):
				await self.hit(inter, session)
			elif inter.component.custom_id.startswith("bj_skip:"):
				await self.skip(inter, session)

		elif inter.component.custom_id == "bj_help":
			emb = disnake.Embed(description=(
				"### Ціль\n"
				"Сума всіх ваших карт повинна бути більшою, ніж у вашого суперника, але не перевищувати 21.\n"
				"Валети (J), дами (Q) та королі (K) - вартують 10 очок. Тузи (A) можуть вартувати 1 або 11 очок.\n"
				"### Ігровий процес\n"
				"На початку ви та другий гравець отримуєте по одній карті. Вам надається пару варіантів того, що робити з цими картками:\n"
				"> `Взяти картку`: Ви отримуєте ще одну карту, і хід передається супернику, якщо ви не перевищили 21.\n"
				"> `Пропустити хід`: Ви пропускаєте свій хід, і він передається супернику.\n"
				"### Порівняння карт | Фінал\n"
				"Якщо гра заходить в \"глухий кут\", тобто коли обидва гравці пропускають свої ходи, то починається перевірка карт. Виграє гравець з найбільшою кількістю очок.\n"
				"Проте, гра може закінчитися і раніше: Якщо будь-який гравець набере більше 21 очок, він автоматично програє, або виграє, якщо набере рівно 21 очко."
			), color=EMBEDCOLOR)
			await inter.send(embed=emb, ephemeral=True)

		elif inter.component.custom_id.startswith("bj_accept:"):
			custom_id = inter.component.custom_id.split(":")
			member_id = int(custom_id[1])
			author_id = int(custom_id[2])
			bet = custom_id[3]
			if inter.author.id != member_id:
				return await error(inter, "<:cross:1127281507430576219> **Це запрошення адресовано не вам!**")
			member1 = inter.guild.get_member(author_id)
			if not member1: return
			member2 = inter.guild.get_member(member_id)
			if not member2: return
			await self.start_blackjack(inter, member1, member2, int(bet))

		elif inter.component.custom_id.startswith("bj_deny:"):
			custom_id = inter.component.custom_id.split(":")
			member_id = int(custom_id[1])
			if inter.author.id != member_id:
				return await error(inter, "<:cross:1127281507430576219> **Це запрошення адресовано не вам!**")
			emb = disnake.Embed(title="🃏 Блекджек", description=f"**{inter.author.id} відхилив гру в блекджек!**", color=RED, timestamp=inter.created_at)
			emb.set_thumbnail(url=inter.author.display_avatar)
			try: await inter.response.edit_message(content="", embed=emb, components=[])
			except: pass


	async def hit(self, inter:disnake.MessageInteraction, session:str):
		#Загальне
		if session not in self.blackjack_sessions: return
		db = self.blackjack_sessions[session]
		if inter.author.id == db["member"]["id"]:
			you = "member"
		if inter.author.id == db["dealer"]["id"]:
			you = "dealer"

		#Затримка
		self.check_bj(inter.author)
		check = await checkcooldown(inter.author, "blackjack")
		if check: return await cooldown_notice(inter, check)

		#Отримання карток
		BJ_TABLE_NEW = BJ_TABLE()
		for card in db[you]["cards"]:
			BJ_TABLE_NEW.pop(card)
		
		#Поінти
		points = 0
		for card in db[you]["cards"]:
			value = BJ_TABLE()[card]
			if value == "rnd": value = self.acard(points)
			points += value

		#Діставання випадкової картки
		card = random.choice(list(BJ_TABLE_NEW))
		value = BJ_TABLE_NEW[card]
		if value == "rnd": value = self.acard(points)
		BJ_TABLE_NEW.pop(card)
		points += value
		db[you]["cards"].append(card)
		self.blackjack_sessions[session] = db

		#Зрада чи перемога
		if points > 21:
			if you == "member":
				return await self.end_game(inter, session, 1)
			elif you == "dealer":
				return await self.end_game(inter, session, 2)
		elif points == 21:
			self.blackjack_cooldown[str(inter.author.id)]['win'] += db["bet"]
			self.blackjack_cooldown[str(inter.author.id)]['lastwin'] = curTime()
			if you == "member":
				return await self.end_game(inter, session, 2)
			elif you == "dealer":
				return await self.end_game(inter, session, 1)

		await self.skip(inter, session, by_button=False)


	async def dealer_hit(self, inter:disnake.MessageInteraction, session:str):
		#Загальне
		if session not in self.blackjack_sessions: return
		db = self.blackjack_sessions[session]

		#Отримання карток
		BJ_TABLE_NEW = BJ_TABLE()
		for card in db["dealer"]["cards"]:
			BJ_TABLE_NEW.pop(card)
		
		#Поінти гравця
		points1 = 0
		for card in db["member"]["cards"]:
			value = BJ_TABLE()[card]
			if value == "rnd": value = self.acard(points1)
			points1 += value
		
		#Поінти ділера
		points2 = 0
		for card in db["dealer"]["cards"]:
			value = BJ_TABLE()[card]
			if value == "rnd": value = self.acard(points2)
			points2 += value

		#Хід
		if (points2 < 17) or (points2 >= 17 and points2 != 20 and points2 < points1 and random.randint(1,2) == 2):
			#Діставання випадкової картки
			card = random.choice(list(BJ_TABLE_NEW))
			value = BJ_TABLE_NEW[card]
			if value == "rnd": value = self.acard(points2)
			BJ_TABLE_NEW.pop(card)
			points2 += value
			db["dealer"]["cards"].append(card)
		#Скіп
		else:
			db["skips"] += 1

		#Зміна ходу
		db["dealer"]["hit"] = False
		db["member"]["hit"] = True

		#Зрада чи перемога
		if points2 > 21:
			self.blackjack_cooldown[str(inter.author.id)]['win'] += db["bet"]
			self.blackjack_cooldown[str(inter.author.id)]['lastwin'] = curTime()
			return await self.end_game(inter, session, 2)
		elif points2 == 21:
			if db["dealer"]["id"] != "bot":
				self.blackjack_cooldown[str(db["dealer"]["id"])]['win'] += db["bet"]
				self.blackjack_cooldown[str(db["dealer"]["id"])]['lastwin'] = curTime()
			return await self.end_game(inter, session, 1)
		self.blackjack_sessions[session] = db

		#Embed
		emb = self.blackjack_embed(session)
		components = [
			disnake.ui.Button(label="Взяти картку", style=disnake.ButtonStyle.blurple, custom_id=f"bj_hit:{session}"),
			disnake.ui.Button(label="Пропустити хід", style=disnake.ButtonStyle.green, custom_id=f"bj_skip:{session}"),
			disnake.ui.Button(label="Як грати?", emoji="❔", custom_id="bj_help")
		]
		if db["dealer"]["hit"]:
			await inter.edit_original_response(embed=emb, components=components)
		else:
			await inter.edit_original_response(embed=emb, components=components)


	async def skip(self, inter:disnake.MessageInteraction, session:str, by_button:bool=True):
		#Загальне
		if session not in self.blackjack_sessions: return
		db = self.blackjack_sessions[session]
		if inter.author.id == db["member"]["id"]:
			you = "member"
		if inter.author.id == db["dealer"]["id"]:
			you = "dealer"

		#Затримка
		self.check_bj(inter.author)
		check = await checkcooldown(inter.author, "blackjack")
		if check: return await cooldown_notice(inter, check)

		#Зміна ходу
		if by_button:
			db["skips"] += 1
		db[you]["hit"] = False
		if you == "member":
			db["dealer"]["hit"] = True
		else:
			db["member"]["hit"] = True

		self.blackjack_sessions[session] = db
		
		#Порівняння
		if db["skips"] > BJ_MAX_SKIPS:
			points = 0
			for card in db["member"]["cards"]:
				value = BJ_TABLE()[card]
				if value == "rnd": value = self.acard(points)
				points += value
			points2 = 0
			for card in db["dealer"]["cards"]:
				value = BJ_TABLE()[card]
				if value == "rnd": value = self.acard(points2)
				points2 += value
			if points > 21:
				if db["dealer"]["id"] != "bot":
					self.blackjack_cooldown[str(db["dealer"]["id"])]['win'] += db["bet"]
					self.blackjack_cooldown[str(db["dealer"]["id"])]['lastwin'] = curTime()
				return await self.end_game(inter, session, 1)
			if points2 > 21:
				self.blackjack_cooldown[str(inter.author.id)]['win'] += db["bet"]
				self.blackjack_cooldown[str(inter.author.id)]['lastwin'] = curTime()
				return await self.end_game(inter, session, 2)
			if points > points2:
				self.blackjack_cooldown[str(inter.author.id)]['win'] += db["bet"]
				self.blackjack_cooldown[str(inter.author.id)]['lastwin'] = curTime()
				return await self.end_game(inter, session, 2)
			if points < points2:
				if db["dealer"]["id"] != "bot":
					self.blackjack_cooldown[str(db["dealer"]["id"])]['win'] += db["bet"]
					self.blackjack_cooldown[str(db["dealer"]["id"])]['lastwin'] = curTime()
				return await self.end_game(inter, session, 1)
			if points == points2:
				return await self.end_game(inter, session, 3)

		#Повідомлення
		emb = self.blackjack_embed(session)
		if db["dealer"]["id"] == "bot":
			loadbtn = disnake.ui.Button(emoji="<a:typing:1231169977315495957>", disabled=True)
			if db["dealer"]["hit"]:
				await inter.response.edit_message(embed=emb, components=[loadbtn])
			else:
				await inter.response.edit_message(embed=emb, components=[loadbtn])
			await asyncio.sleep(random.uniform(0.8, 1.9))
			await self.dealer_hit(inter, session)
		else:
			await inter.response.edit_message(embed=emb)


	async def end_game(self, inter:disnake.MessageInteraction, session:str, result:int):
		if session not in self.blackjack_sessions: return
		db = self.blackjack_sessions[session]
		money = eco_db.find(f"{db['member']['id']}.money")
		member = inter.guild.get_member(db['member']['id'])
		if db['dealer']['id'] != "bot":
			member2 = inter.guild.get_member(db['dealer']['id'])
			money2 = eco_db.find(f"{db['dealer']['id']}.money")
		#Програш (для 1 гравця)
		if result == 1:
			db['dealer']['hit'] = True
			db['member']['hit'] = False
			if db['dealer']['id'] == "bot":
				color = RED
				message = "**Дилер** переміг гравця!\n**Ви втратили:** {amount}"
			else:
				color = GREEN
				eco_db.update(f"{db['dealer']['id']}.money", money2+db['bet']*2)
				message = f"{member2.mention} переміг користувача {member.mention}!"
		#Перемога (для 1 гравця)
		elif result == 2:
			eco_db.update(f"{db['member']['id']}.money", money+db['bet']*2)
			db['member']['hit'] = True
			db['dealer']['hit'] = False
			if db['dealer']['id'] == "bot":
				message = f"{member.mention} переміг дилера!"+"\n**Ви виграли:** {amount}"
			else:
				message = f"{member.mention} переміг користувача {member2.mention}!"
			color = GREEN
		#Нічия
		elif result == 3:
			db['dealer']['hit'] = False
			db['member']['hit'] = False
			eco_db.update(f"{db['member']['id']}.money", money+db['bet'])
			if db['dealer']['id'] != "bot":
				eco_db.update(f"{db['dealer']['id']}.money", money2+db['bet'])
			message = "**Нічия!**"
			color = disnake.Colour.orange()

		#Embed
		emb = self.blackjack_embed(session, message, color)
		components = [
			disnake.ui.Button(label="Взяти картку", style=disnake.ButtonStyle.blurple, disabled=True),
			disnake.ui.Button(label="Пропустити хід", style=disnake.ButtonStyle.green, disabled=True),
			disnake.ui.Button(label="Як грати?", emoji="❔", custom_id="bj_help")
		]
		if not inter.response.is_done():
			await inter.response.defer()
		await inter.edit_original_response(embed=emb, components=components)
		self.blackjack_sessions.pop(session)


	def blackjack_embed(self, session:str, message:str=None, color:int=INVISIBLE):
		db = self.blackjack_sessions[session]
		#Гравець
		member = self.bot.get_guild(GUILD_ID).get_member(db["member"]["id"])
		member_cards = db["member"]["cards"]
		member_cards_str = " ".join(member_cards)
		member_points = 0
		for card in member_cards:
			value = BJ_TABLE()[card]
			if value == "rnd": value = self.acard(member_points)
			member_points += value
		if db["member"]["hit"] and not message:
			if db["dealer"]["id"] == "bot":
				message = f"{member.mention}, ваш хід!"
			else:
				message = f"Хід {member.mention}!"

		#Дилер
		dealer = self.bot.get_guild(GUILD_ID).get_member(db["dealer"]["id"])
		dealer_cards = db["dealer"]["cards"]
		dealer_cards_str = " ".join(dealer_cards)
		dealer_points = 0
		for card in dealer_cards:
			value = BJ_TABLE()[card]
			if value == "rnd": value = self.acard(dealer_points)
			dealer_points += value
		if db["dealer"]["hit"] and not message:
			if db["dealer"]["id"] == "bot":
				message = f"Хід **дилера**!"
			else:
				message = f"Хід {dealer.mention}!"

		#Embed
		if member_points == 21: member_points = "BJ"
		if dealer_points == 21: dealer_points = "BJ"
		emb = disnake.Embed(description=message.replace("{amount}", f"{hf(db['bet'])}{CURRENCY}"), color=color)
		emb.title = "🃏 Блекджек"
		if db["member"]["hit"]:
			emb.set_thumbnail(member.display_avatar)
		elif db["dealer"]["hit"] and db["dealer"]["id"] != "bot":
			emb.set_thumbnail(dealer.display_avatar)
		else:
			emb.set_thumbnail(member.display_avatar)
		if db["dealer"]["id"] == "bot":
			emb.add_field(name=f"Картки гравця ({member_points})", value=member_cards_str)
			emb.add_field(name=f"Картки дилера ({dealer_points})", value=dealer_cards_str)
		else:
			emb.add_field(name=f"{member.display_name} ({member_points})", value=member_cards_str)
			emb.add_field(name=f"{dealer.display_name} ({dealer_points})", value=dealer_cards_str)
		emb.set_footer(text=f"Ставка: {hf(db['bet'])}₴")
		return emb


	async def start_blackjack(self, inter:disnake.MessageInteraction, member1:disnake.Member, member2:disnake.Member, bet:int):
		money = eco_db.find(f"{member1.id}.money")
		if member2:
			money2 = eco_db.find(f"{member2.id}.money")

		#Перевірка на активну сесію
		for game in self.blackjack_sessions:
			if self.blackjack_sessions[game]["member"]["id"] == member1.id or self.blackjack_sessions[game]["dealer"]["id"] == member1.id:
				return await error(inter, f"<:cross:1127281507430576219> **{member1.mention} вже приймає участь в іншій грі!**", ephemeral=False)
			if self.blackjack_sessions[game]["member"]["id"] == member2.id or self.blackjack_sessions[game]["dealer"]["id"] == member2.id:
				return await error(inter, f"<:cross:1127281507430576219> **{member2.mention} вже приймає участь в іншій грі!**", ephemeral=False)

		#Знімання грошей
		money -= bet
		eco_db.update(f"{member1.id}.money", money)
		if member2:
			money2 -= bet
			eco_db.update(f"{member2.id}.money", money2)

		#Карти
		BJ_TABLE_NEW = BJ_TABLE()
		card = random.choice(list(BJ_TABLE_NEW))
		value = BJ_TABLE()[card]
		BJ_TABLE_NEW.pop(card)
		card2 = random.choice(list(BJ_TABLE_NEW))

		#Створення сесії
		session = str(random.randint(1000,9999))
		while session in self.blackjack_sessions:
			session = str(random.randint(1000,9999))
		self.blackjack_sessions[session] = {}
		self.blackjack_sessions[session]["member"] = {"id": member1.id, "cards": [card], "hit": True}
		if member2:
			self.blackjack_sessions[session]["dealer"] = {"id": member2.id, "cards": [card2], "hit": False}
		else:
			self.blackjack_sessions[session]["dealer"] = {"id": "bot", "cards": [card2], "hit": False}
		self.blackjack_sessions[session]["bet"] = bet
		self.blackjack_sessions[session]["skips"] = 0

		#Embed
		if value == 21:
			self.blackjack_cooldown[str(member1.id)]['win'] += bet
			self.blackjack_cooldown[str(member1.id)]['lastwin'] = curTime()
			return await self.end_game(inter, session, 2)
		else:
			emb = self.blackjack_embed(session)

		#Надсилання
		components = [
			disnake.ui.Button(label="Взяти картку", style=disnake.ButtonStyle.blurple, custom_id=f"bj_hit:{session}"),
			disnake.ui.Button(label="Пропустити хід", style=disnake.ButtonStyle.green, custom_id=f"bj_skip:{session}"),
			disnake.ui.Button(label="Як грати?", emoji="❔", custom_id="bj_help")
		]
		if not inter.response.is_done():
			await inter.response.defer()
		await inter.edit_original_response("", embed=emb, components=components)
		
		#Видалення
		await asyncio.sleep(180)
		if session in self.blackjack_sessions:
			try: return await self.end_game(inter, session, 3)
			except: pass
			try: self.blackjack_sessions.pop(session)
			except: pass


	@commands.slash_command(name="blackjack", description="💰 Грати в гру blackjack.", guild_ids=[GUILD_ID])
	@commands.cooldown(1, 2, commands.BucketType.user)
	async def blackjack(self, inter:disnake.CommandInter, ставка:str=commands.Param(description="Ставка. (all - всі ваші гроші.)"), учасник:disnake.Member=commands.Param(default=None, description="Якщо не вказувати, ви будете грати проти бота.")):
		member = учасник
		bet = ставка
		all_arg = ('all', 'всі', 'все', 'oll', 'усі', 'усе')
		register(inter.author)
		money = eco_db.find(f"{inter.author.id}.money")
		if member:
			money2 = eco_db.find(f"{member.id}.money")
		if bet.lower() in all_arg:
			bet = money

		#Перевірки
		try: bet = int(bet)
		except:
			return await error(inter, f"<:cross:1127281507430576219> **Вкажіть ставку, як ціле число, або \"all\" для всіх грошей.**")
		if bet > BJ_LIMIT[1]:
			bet = BJ_LIMIT[1]
		if bet > money:
			return await error(inter, f"<:cross:1127281507430576219> **Ви вказали більше, ніж у вас є на балансі! ({hf(money)}/{hf(bet)}{CURRENCY})**")
		if member and bet > money2:
			return await error(inter, f"<:cross:1127281507430576219> **У {member.mention} не вистачає грошей! ({hf(money2)}/{hf(bet)}{CURRENCY})**")
		if bet < BJ_LIMIT[0]:
			return await error(inter, f"<:cross:1127281507430576219> **Ставка не може бути меншою за {BJ_LIMIT[0]}{CURRENCY}**")

		#Перевірка на активну сесію
		for game in self.blackjack_sessions:
			if self.blackjack_sessions[game]["member"]["id"] == inter.author.id or self.blackjack_sessions[game]["dealer"]["id"] == inter.author.id:
				return await error(inter, f"<:cross:1127281507430576219> **Ви вже приймаєте участь в іншій грі!**")
			if member and (self.blackjack_sessions[game]["member"]["id"] == member.id or self.blackjack_sessions[game]["dealer"]["id"] == member.id):
				return await error(inter, f"<:cross:1127281507430576219> **{member.mention} вже приймає участь в іншій грі!**")

		#Затримка
		self.check_bj(inter.author)
		check = await checkcooldown(inter.author, "blackjack")
		if check: return await cooldown_notice(inter, check)

		#Надсилання
		if not member:
			await self.start_blackjack(inter, inter.author, None, bet)
		else:
			emb = disnake.Embed(title="🃏 Блекджек", description=f"Користувач {inter.author.mention} надіслав вам запит на гру в блекджек.\n**Ставка:** {hf(bet)}{CURRENCY}", color=GREEN, timestamp=inter.created_at)
			emb.set_thumbnail(inter.author.display_avatar)
			await inter.response.send_message(f"<:check:1127281505153069136> **Успішно надіслано запит!**", ephemeral=True)
			acceptbtn = disnake.ui.Button(label="Прийняти", style=disnake.ButtonStyle.green, custom_id=f"bj_accept:{member.id}:{inter.author.id}:{bet}")
			denybtn = disnake.ui.Button(label="Відхилити", style=disnake.ButtonStyle.red, custom_id=f"bj_deny:{member.id}")
			msg = await inter.channel.send(member.mention, embed=emb, components=[acceptbtn, denybtn])

			#Видалення
			await asyncio.sleep(60)
			try:
				msg = await msg.channel.fetch_message(msg.id)
				if msg.components[0].children[0].custom_id.startswith("bj_accept"):
					await msg.delete()
			except: pass


def setup(bot:commands.Bot):
	bot.add_cog(Blackjack(bot))