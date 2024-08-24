from cogs.economy.pigs import Pigs
from utils import *


class Trades(commands.Cog):
	def __init__(self, bot:commands.Bot):
		self.bot = bot
		self.trades = {}


	@commands.Cog.listener("on_modal_submit")
	async def set_money_modal(self, inter:disnake.ModalInteraction):
		if inter.custom_id.startswith("trade_money"):
			eco = eco_db.full()
			msg = str(inter.message.id)
			amount = inter.text_values['amount']
			try: amount = int(amount)
			except:
				if amount == 'all': amount = eco[str(inter.author.id)]['money']
				else: return await error(inter, f"<:cross:1127281507430576219> **Не вдалося поставити гроші!**")
			if msg not in self.trades: return await error(inter, f"<:cross:1127281507430576219> **Такого обміну не існує!**")

			#Перевірка
			if amount < 1:
				return await error(inter, f"<:cross:1127281507430576219> **Ви не можете поставити менше 1{CURRENCY}!**")
			if eco[str(inter.author.id)]['money'] < amount:
				return await error(inter, f"<:cross:1127281507430576219> **Ви вказали більше грошей, ніж у вас є на балансі! ({eco[str(inter.author.id)]['money']}/{amount}{CURRENCY})**")

			#БД
			if self.trades[msg]["member1"] == inter.author.id: t = 'items1'
			elif self.trades[msg]["member2"] == inter.author.id: t = 'items2'
			self.trades[msg][t]['money'] = amount
			self.trades[msg]["accept"] = []
			await self.build_message(inter, msg, edit=True)


	@commands.Cog.listener("on_modal_submit")
	async def set_item_modal(self, inter:disnake.ModalInteraction):
		if inter.custom_id.startswith("trade_item"):
			item = inter.custom_id.split("_")[2]
			msg = inter.custom_id.split("_")[3]
			amount = inter.text_values['amount']
			try: amount = int(amount)
			except:
				if amount != 'all': return await error(inter, f"<:cross:1127281507430576219> **Не вдалося поставити предмет!**")
			if msg not in self.trades: return await error(inter, f"<:cross:1127281507430576219> **Такого обміну не існує!**")
			items = items_db.full()
			eco = eco_db.full()

			#Перевірка
			if item not in eco[str(inter.author.id)]:
				return await error(inter, f"<:cross:1127281507430576219> **У вас немає `{items[item]['name']} x{amount}`!**")
			if amount == 'all': amount = eco[str(inter.author.id)][item]
			if eco[str(inter.author.id)][item] < amount:
				return await error(inter, f"<:cross:1127281507430576219> **Вам не вистачає: `{items[item]['name']} x{amount-eco[str(inter.author.id)][item]}`!**")
			if item in self.trades[msg]['items2'] or item in self.trades[msg]['items1']:
				return await error(inter, f"<:cross:1127281507430576219> **Вказаний предмет вже поставлено на обмін!**")

			#БД
			if self.trades[msg]["member1"] == inter.author.id:
				self.trades[msg]["items1"][item] = amount
			elif self.trades[msg]["member2"] == inter.author.id:
				self.trades[msg]["items2"][item] = amount
			self.trades[msg]["accept"] = []
			await self.build_message(inter, msg, edit=True)


	@commands.Cog.listener("on_dropdown")
	async def select_option(self, inter:disnake.MessageInteraction):
		###
		### Вибір опції
		###
		if inter.component.custom_id.startswith("trade_selectoption"):
			if inter.message.embeds == []: return
			if inter.message.components == []: return
			msg = str(inter.message.id)
			if msg not in self.trades: return await error(inter, f"<:cross:1127281507430576219> **Такого обміну не існує!**")
			trade = self.trades[msg]
			if inter.author.id != trade['member1'] and inter.author.id != trade['member2']:
				return await error(inter, f"<:cross:1127281507430576219> **Ви не можете приймати участь в цьому обміні!**")

			#Гроші
			if inter.values[0] == "money":
				components = disnake.ui.TextInput(label="Кількість грошей", placeholder="Скільки ви віддасте грошей.", min_length=1, max_length=4, custom_id="amount")
				modal = disnake.ui.Modal(title="Гроші", components=components, custom_id=f"trade_money")
				await inter.response.send_modal(modal)

			#Предмет
			elif inter.values[0] == "item":
				eco = eco_db.find(f"{inter.author.id}")
				items = items_db.full()
				options = []
				for item in eco:
					if item not in items: continue
					if not 'name' in items[item]: continue
					if 'allow-trade' not in items[item]: continue
					if not items[item]['allow-trade']: continue
					options.append(disnake.SelectOption(label=items[item]['name'], emoji=items[item]['icon'], value=item))
				if options == []: return await error(inter, f"<:cross:1127281507430576219> **У вас немає предметів, які можна поставити на обмін!**")
				select = disnake.ui.StringSelect(placeholder="Виберіть предмет", options=options, custom_id=f"trade_selectitem_{msg}")
				await inter.response.send_message(components=[select], ephemeral=True)
			
			elif inter.values[0] == "pigskin":
				eco = eco_db.find(f"{inter.author.id}")
				try: pig = pigs_db.find(f"{inter.author.id}")
				except: return await error(inter, "<:cross:1127281507430576219> **У вас немає свині! Купити її можна в </shop:1213168795728879702>**")
				if pig['skins'] == [0] and pig['eyes'] == [0] and pig['hats'] == [0] and pig['decos'] == [0] and pig['faces'] == [0]:
					return await error(inter, f"<:cross:1127281507430576219> **У вас немає скінів свині, які можна поставити на обмін!**")
				options = [
					disnake.SelectOption(label="Скін", emoji="🐖", value="skin"),
					disnake.SelectOption(label="Очі", emoji="👀", value="eye"),
					disnake.SelectOption(label="Головний убір", emoji="🧢", value="hat"),
					disnake.SelectOption(label="Декорації (Одяг)", emoji="👕", value="deco"),
					disnake.SelectOption(label="Декорації обличчя", emoji="💄", value="face")
				]
				select = disnake.ui.StringSelect(placeholder="Виберіть категорію", options=options, custom_id=f"trade_selectpigcategory_{msg}")
				await inter.response.send_message("**[1/2]** Виберіть категорію скінів.", components=[select], ephemeral=True)
		
		###
		### Вибір предмету
		###
		if inter.component.custom_id.startswith("trade_selectitem"):
			msg = inter.component.custom_id.split("_")[2]
			if msg not in self.trades: return await error(inter, f"<:cross:1127281507430576219> **Такого обміну не існує!**")
			#Перевірка
			if inter.values[0] in self.trades[msg]['items2'] or inter.values[0] in self.trades[msg]['items1']:
				return await error(inter, f"<:cross:1127281507430576219> **Вказаний предмет вже поставлено на обмін!**")
			#Modal
			components = disnake.ui.TextInput(label="Кількість предметів", placeholder="all - передати всі, що є в інвентарі.", min_length=1, max_length=5, custom_id="amount")
			modal = disnake.ui.Modal(title="Предмет", components=components, custom_id=f"trade_item_{inter.values[0]}_{msg}")
			await inter.response.send_modal(modal)

		###
		### Вибір категорії скіна
		###
		if inter.component.custom_id.startswith("trade_selectpigcategory"):
			msg = inter.component.custom_id.split("_")[2]
			type = inter.values[0]
			if msg not in self.trades: return await error(inter, f"<:cross:1127281507430576219> **Такого обміну не існує!**")
			try: pig = pigs_db.find(f"{inter.author.id}")
			except: return await error(inter, "<:cross:1127281507430576219> **У вас немає свині! Купити її можна в </shop:1213168795728879702>**")
			if pig[type+'s'] == [0]:
				return await error(inter, f"<:cross:1127281507430576219> **У вас немає скінів свині, які можна поставити на обмін!**")
			#Скіни
			options = []
			for skin in pig[type+'s']:
				if skin <= 0: continue
				with open(f"img/pigs/{type}/{skin}.json", encoding='utf-8') as f: db = json.load(f)
				rare = Pigs.get_chance(type, skin)
				options.append(disnake.SelectOption(label=db['name'], emoji=rare, value=f"{type}:{skin}"))
			#Відповідь
			select = disnake.ui.StringSelect(placeholder="Виберіть скін", options=options, custom_id=f"trade_selectpigskin_{msg}")
			await inter.response.edit_message("**[2/2]** Виберіть скін, який ви хочете поставити на обмін.", components=[select])
		
		###
		### Вибір скіна
		###
		if inter.component.custom_id.startswith("trade_selectpigskin"):
			msg = inter.component.custom_id.split("_")[2]
			type, skin = inter.values[0].split(":")
			skin = int(skin)
			if msg not in self.trades: return await error(inter, f"<:cross:1127281507430576219> **Такого обміну не існує!**")
			items = items_db.full()
			eco = eco_db.full()

			#Перевірка
			try: pig = pigs_db.find(f"{inter.author.id}")
			except: return await error(inter, "<:cross:1127281507430576219> **У вас немає свині! Купити її можна в </shop:1213168795728879702>**")
			if skin not in pig[type+'s']:
				return await error(inter, f"<:cross:1127281507430576219> **У вас немає скінів свині, які можна поставити на обмін!**")
			if pig[type] == skin:
				return await error(inter, f"<:cross:1127281507430576219> **Ви не можете поставити на обмін вибраний скін!**")

			#БД
			if self.trades[msg]["member1"] == inter.author.id:
				self.trades[msg]["items1"][f"pig:{inter.values[0]}"] = 1
			elif self.trades[msg]["member2"] == inter.author.id:
				self.trades[msg]["items2"][f"pig:{inter.values[0]}"] = 1
			self.trades[msg]["accept"] = []
			await self.build_message(inter, msg, edit=True)


	@commands.Cog.listener("on_button_click")
	async def items_clear(self, inter: disnake.MessageInteraction):
		if inter.component.custom_id.startswith("trade_clear"):
			msg = str(inter.message.id)
			if msg not in self.trades: return await error(inter, f"<:cross:1127281507430576219> **Такого обміну не існує!**")

			#Перевірка
			if inter.author.id != self.trades[msg]['member1'] and inter.author.id != self.trades[msg]['member2']:
				return await error(inter, f"<:cross:1127281507430576219> **Ви не можете приймати участь в цьому обміні!**")
			#Очищення
			if self.trades[msg]["member1"] == inter.author.id: t = 'items1'
			elif self.trades[msg]["member2"] == inter.author.id: t = 'items2'
			if self.trades[msg][t] == {}:
				return await error(inter, f"<:cross:1127281507430576219> **У вас немає предметів для обміну!**")
			self.trades[msg][t] = {}
			self.trades[msg]["accept"] = []
			await self.build_message(inter, msg, edit=True)


	async def build_message(self, inter:disnake.Interaction, msg:str, edit:bool=False, end:int=0):
		items = items_db.full()
		if msg.startswith("empty_"):
			trade = {
				"member1": int(msg.split("_")[1]),
				"member2": int(msg.split("_")[2]),
				"accept": [],
				"items1": {},
				"items2": {}
			}
		else:
			if str(msg) not in self.trades: return
			trade = self.trades[str(msg)]
			message = await inter.channel.fetch_message(int(msg))

		#Користувачі
		member1 = inter.guild.get_member(int(trade['member1']))
		member2 = inter.guild.get_member(int(trade['member2']))

		#Предмети
		items1_db:dict[str, int] = trade['items1']
		items1 = ""
		for item in items1_db:
			if item == 'money':
				items1 += f"`{items1_db['money']}`{CURRENCY}\n"
				continue
			elif item.startswith("pig:"):
				_, type, skin = item.split(":")
				with open(f"img/pigs/{type}/{skin}.json", encoding='utf-8') as f: db = json.load(f)
				items1 += f"{Pigs.get_chance(type, int(skin))} `{db['name']}`\n"
				continue
			items1 += f"{items[item]['icon']} `{items[item]['name']} x{items1_db[item]}`\n"
		if items1 == "": items1 = "`Нічого`"
		#Предмети 2
		items2_db:dict[str, int] = trade['items2']
		items2 = ""
		for item in items2_db:
			if item == 'money':
				items2 += f"`{items2_db['money']}`{CURRENCY}\n"
				continue
			elif item.startswith("pig:"):
				_, type, skin = item.split(":")
				with open(f"img/pigs/{type}/{skin}.json", encoding='utf-8') as f: db = json.load(f)
				items2 += f"{Pigs.get_chance(type, int(skin))} `{db['name']}`\n"
				continue
			items2 += f"{items[item]['icon']} `{items[item]['name']} x{items2_db[item]}`\n"
		if items2 == "": items2 = "`Нічого`"

		#Колір та заголовок
		if end == 1:
			title, color = "✅ Обмін закінчено", GREEN
		elif end == 2:
			title, color = "❌ Обмін закінчено", RED
		else:
			title, color = "⚖️ Торгівля", EMBEDCOLOR

		#Embed
		emb = disnake.Embed(title=title, color=color)
		emb.add_field(name=f"{member1.display_name}", value=items1)
		emb.add_field(name=f"{member2.display_name}", value=items2)
		if end == 0: emb.set_footer(text="Цей обмін буде дійсний 10 хвилин.")
		emb.set_thumbnail(url="https://cdn.discordapp.com/attachments/1055589223492767867/1207772327719342100/22210_1706624515_128.png?ex=65e0dca2&is=65ce67a2&hm=1cf6aece5a3bba7d9c3baae1f05b9317e5d39d58867c3fd64912ece3571a3b93&")
		#Кнопки
		options = [
			disnake.SelectOption(label="Гроші", emoji=CURRENCY, value="money"),
			disnake.SelectOption(label="Предмет", emoji="⛏️", value="item"),
			disnake.SelectOption(label="Скін свині", emoji="🐖", value="pigskin")
		]
		select = disnake.ui.StringSelect(placeholder="Додати предмети", options=options, custom_id=f"trade_selectoption")
		check = bool(trade['items1'] == {} and trade['items2'] == {})
		btn = disnake.ui.Button(label=f"{len(trade['accept'])}/2", emoji="✅", style=disnake.ButtonStyle.green, custom_id=f"trade_accept", disabled=check)
		btn2 = disnake.ui.Button(label="Очистити", style=disnake.ButtonStyle.red, custom_id=f"trade_clear")
		components = []
		if end == 0: components = [select,btn,btn2]

		#Відправка
		if edit:
			await inter.response.defer(with_message=False)
			return await message.edit(content=f"{member1.mention} ⇄ {member2.mention}", embed=emb, components=components)
		return await inter.channel.send(content=f"{member1.mention} ⇄ {member2.mention}", embed=emb, components=components)


	@commands.slash_command(name="trade", description="💰 Обмінятися предметами з іншим користувачем.", guild_ids=[GUILD_ID])
	@commands.cooldown(1, 2, commands.BucketType.user)
	async def trade(
		self, inter:disnake.CommandInter,
		учасник:disnake.Member=commands.Param(description="Користувач, з яким ви хочете обмінятися предметами")
	):
		if inter.locale == disnake.Locale.ru:
			return await error(inter, "<:cross:1127281507430576219> **При ініціалізації мови сталася помилка!**")
		member = учасник
		register(inter.author)
		register(member)

		#Затримка
		check = await checkcooldown(inter.author, "trade")
		if check: return await cooldown_notice(inter, check)

		#Загальні перевірки
		if member.bot:
			return await error(inter, f"<:cross:1127281507430576219> **Ти звісно можеш спробувати поторгувати з ботом, але чи є в цьому сенс?**")
		elif member.id == inter.author.id:
			return await error(inter, f"<:cross:1127281507430576219> **Що ти вже зібрався собі продавати?**")

		#БД
		await success(inter, f"<:check:1127281505153069136> **Успішно створено обмін!**", ephemeral=True)
		msg:disnake.Message = await self.build_message(inter, f"empty_{inter.author.id}_{member.id}")
		self.trades[str(msg.id)] = {}
		self.trades[str(msg.id)]["member1"] = inter.author.id
		self.trades[str(msg.id)]["member2"] = member.id
		self.trades[str(msg.id)]["accept"] = []
		self.trades[str(msg.id)]["items1"] = {}
		self.trades[str(msg.id)]["items2"] = {}
		set_cooldown(inter.author, "trade", TRADE_COOLDOWN)

		#Видалення
		await asyncio.sleep(600)
		try: await msg.delete()
		except: pass
		if str(msg.id) in self.trades:
			try:
				self.trades.pop(str(msg.id))
				temp_db.update('trades', self.trades)
			except: pass
			try: await self.build_message(inter, str(msg.id), edit=True, end=2)
			except: pass


	@commands.Cog.listener("on_button_click")
	async def trade_accept(self, inter: disnake.MessageInteraction):
		if inter.component.custom_id.startswith("trade_accept"):
			msg = str(inter.message.id)
			if msg not in self.trades: return await error(inter, f"<:cross:1127281507430576219> **Такого обміну не існує!**")
			if inter.author.id != self.trades[msg]['member1'] and inter.author.id != self.trades[msg]['member2']:
				return await error(inter, f"<:cross:1127281507430576219> **Ви не можете приймати участь в цьому обміні!**")

			#Додавання 
			if inter.author.id in self.trades[msg]['accept']:
				return await error(inter, f"<:cross:1127281507430576219> **Ви вже прийняли цей обмін!**")
			self.trades[msg]['accept'].append(inter.author.id)
			accept = self.trades[msg]['accept']

			if len(accept) == 2:
				eco = eco_db.full()
				pigs = pigs_db.full()
				items = items_db.full()
				items1:dict[str, int] = self.trades[msg]["items1"]
				items2:dict[str, int] = self.trades[msg]["items2"]
				member1 = inter.guild.get_member(int(self.trades[msg]["member1"]))
				member2 = inter.guild.get_member(int(self.trades[msg]["member2"]))

				#Перевірки
				if any(not item.startswith("pig:") and item not in eco[str(member1.id)] for item in items1):
					return await error(inter, f"<:cross:1127281507430576219> **У {member1.mention} немає деяких предметів/грошей, поставлених на обмін!**", ephemeral=False)
				if any(not item.startswith("pig:") and item not in eco[str(member2.id)] for item in items2):
					return await error(inter, f"<:cross:1127281507430576219> **У {member2.mention} немає деяких предметів/грошей, поставлених на обмін!**", ephemeral=False)
				if any(not item.startswith("pig:") and items1[item] > eco[str(member1.id)][item] for item in items1):
					return await error(inter, f"<:cross:1127281507430576219> **У {member1.mention} не вистачає деяких предметів/грошей, поставлених на обмін!**", ephemeral=False)
				if any(not item.startswith("pig:") and items2[item] > eco[str(member2.id)][item] for item in items2):
					return await error(inter, f"<:cross:1127281507430576219> **У {member2.mention} не вистачає деяких предметів/грошей, поставлених на обмін!**", ephemeral=False)
				if any(not item.startswith("pig:") and item != "money" and eco[str(member1.id)][item]+items2[item] > items[item]['stack-limit'] for item in items2):
					return await error(inter, f"<:cross:1127281507430576219> **У {member1.mention} ліміт деяких предметів, поставлених на обмін!**", ephemeral=False)
				if any(not item.startswith("pig:") and item != "money" and eco[str(member2.id)][item]+items1[item] > items[item]['stack-limit'] for item in items2):
					return await error(inter, f"<:cross:1127281507430576219> **У {member2.mention} ліміт деяких предметів, поставлених на обмін!**", ephemeral=False)
				if eco[str(member1.id)]["money"] >= MAX_MONEY and "money" in items2:
					return await error(inter, f"<:cross:1127281507430576219> **У {member1.mention} ліміт грошей! ({hf(MAX_MONEY)}{CURRENCY})**")
				if eco[str(member2.id)]["money"] >= MAX_MONEY and "money" in items1:
					return await error(inter, f"<:cross:1127281507430576219> **У {member2.mention} ліміт грошей! ({hf(MAX_MONEY)}{CURRENCY})**")
				#Перевірки свиней
				if any(item.startswith("pig:") for item in items1) and str(member1.id) not in pigs:
					return await error(inter, f"<:cross:1127281507430576219> **У {member1.mention} не куплена свиня!**", ephemeral=False)
				if any(item.startswith("pig:") for item in items1) and str(member2.id) not in pigs:
					return await error(inter, f"<:cross:1127281507430576219> **У {member1.mention} не куплена свиня!**", ephemeral=False)
				if any(item.startswith("pig:") for item in items2) and str(member1.id) not in pigs:
					return await error(inter, f"<:cross:1127281507430576219> **У {member2.mention} не куплена свиня!**", ephemeral=False)
				if any(item.startswith("pig:") for item in items2) and str(member2.id) not in pigs:
					return await error(inter, f"<:cross:1127281507430576219> **У {member2.mention} не куплена свиня!**", ephemeral=False)
				if any(item.startswith("pig:") and int(item.split(":")[2]) not in pigs[str(member1.id)][item.split(":")[1]+"s"] for item in items1):
					return await error(inter, f"<:cross:1127281507430576219> **У {member1.mention} немає скіну свині, поставленого на обмін!**", ephemeral=False)
				if any(item.startswith("pig:") and int(item.split(":")[2]) not in pigs[str(member2.id)][item.split(":")[1]+"s"] for item in items2):
					return await error(inter, f"<:cross:1127281507430576219> **У {member2.mention} немає скіну свині, поставленого на обмін!**", ephemeral=False)
				if any(item.startswith("pig:") and int(item.split(":")[2]) == pigs[str(member1.id)][item.split(":")[1]] for item in items1):
					return await error(inter, f"<:cross:1127281507430576219> **У {member1.mention} вибраний один зі скінів свині, який поставлений на обмін!**", ephemeral=False)
				if any(item.startswith("pig:") and int(item.split(":")[2]) == pigs[str(member2.id)][item.split(":")[1]] for item in items2):
					return await error(inter, f"<:cross:1127281507430576219> **У {member2.mention} вибраний один зі скінів свині, який поставлений на обмін!**", ephemeral=False)

				#Предмети 1
				for item in items1:
					#Додавання в інвентар користувачу 2 (Свині)
					if item.startswith("pig:"):
						pigs[str(member1.id)][item.split(":")[1]+"s"].remove(int(item.split(":")[2]))
						pigs[str(member2.id)][item.split(":")[1]+"s"].append(int(item.split(":")[2]))
						continue
					#Додавання в інвентар користувачу 2
					if item in eco[str(member2.id)]:
						eco[str(member2.id)][item] += items1[item]
					else:
						eco[str(member2.id)][item] = items1[item]
					#Прибирання у користувача 1
					if eco[str(member1.id)][item] > items1[item]:
						eco[str(member1.id)][item] -= items1[item]
					else:
						if item == "money": eco[str(member1.id)][item] = 0
						else: eco[str(member1.id)].pop(item)
				#Предмети 2
				for item in items2:
					#Додавання в інвентар користувачу 1 (Свині)
					if item.startswith("pig:"):
						pigs[str(member2.id)][item.split(":")[1]+"s"].remove(int(item.split(":")[2]))
						pigs[str(member1.id)][item.split(":")[1]+"s"].append(int(item.split(":")[2]))
						continue
					#Додавання в інвентар користувачу 1
					if item in eco[str(member1.id)]:
						eco[str(member1.id)][item] += items2[item]
					else:
						eco[str(member1.id)][item] = items2[item]
					#Прибирання у користувача 2
					if eco[str(member2.id)][item] > items2[item]:
						eco[str(member2.id)][item] -= items2[item]
					else:
						if item == "money": eco[str(member2.id)][item] = 0
						else: eco[str(member2.id)].pop(item)

				await self.build_message(inter, msg, edit=True, end=1)
				self.trades.pop(msg)
				eco_db.update('', eco)
				pigs_db.update('', pigs)
				set_cooldown(member1, "trade", TRADE_COOLDOWN)
				set_cooldown(member2, "trade", TRADE_COOLDOWN)
				return
			await self.build_message(inter, msg, edit=True, end=0)


def setup(bot:commands.Bot):
	bot.add_cog(Trades(bot))