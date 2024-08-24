from utils import *


class Economy(commands.Cog):
	def __init__(self, bot:commands.Bot):
		self.bot = bot
		self.blackjack_cooldown = {}


	async def autocomplete_sell(inter:disnake.ApplicationCommandInteraction, user_input:str):
		items = items_db.full()
		eco = eco_db.find(f"{inter.author.id}")
		item_list = []
		for item in items:
			if not 'name' in items[item]: continue
			if 'allow-sell' in items[item] and not items[item]['allow-sell']: continue
			if user_input.lower() in items[item]['name'].lower():
				if item not in eco: continue
				item_list.append(items[item]['name'])
		return item_list

	def icon(self, member:disnake.Member, icon:str|list[str]) -> str:
		if isinstance(icon, str):
			return icon
		elif isinstance(icon, list):
			if member.guild.get_role(BOY_ID) in member.roles:
				return icon[0]
			elif member.guild.get_role(GIRL_ID) in member.roles:
				return icon[1]


	### Баланс
	@commands.slash_command(name="balance", description="📋 Подивитися свій баланс.", guild_ids=[GUILD_ID])
	@commands.cooldown(1, 2, commands.BucketType.user)
	async def balance(self, inter:disnake.CommandInter, учасник:disnake.Member=commands.Param(description="Учасник", default=None)):
		if inter.locale == disnake.Locale.ru:
			return await error(inter, "<:cross:1127281507430576219> **При ініціалізації мови сталася помилка!**")
		member = учасник
		if not member: member = inter.author
		if member.bot: return await error(inter, "<:cross:1127281507430576219> **Боти не можуть мати грошей!**")

		register(inter.author)
		register(member)
		ecos = eco_db.full()
		eco = ecos[str(member.id)]
		cooldown = cooldown_db.find(f"{member.id}")
		pigs = pigs_db.full()
		jobs = jobs_db.full()
		job = str(eco['job'])

		#Гроші на балансі свині
		pig_money = 0
		max_pig_money = 0
		if str(member.id) in pigs:
			pig_money = pigs[str(member.id)]["balance"]
			max_pig_money = int(pigs[str(member.id)]["mass"]*50)

		#Команди
		cmds = ""
		sorting = {"work": "Підробіток", "crime": "Злочин", "mine": "Копати в шахті", "blackjack": "Гра Блекджек", "pig-feed": "Годувати свиню"}
		for cmd in list(sorting):
			if cmd not in cooldown: continue
			if int(cooldown[cmd]) > curTime(): continue
			#Додаткові перевірки
			if cmd == "mine" and not any("pick" in item for item in eco):
				continue
			if cmd == "blackjack" and eco["money"] < BJ_LIMIT[0]:
				continue
			if cmd == "pig-feed" and (str(member.id) not in pigs or "pigfood" not in eco):
				continue
			#Додавання
			cmds += f"> - {sorting[cmd]}: `/{cmd}`\n"
		if cmds == "": cmds = "> Немає доступних команд."

		#Місце в топі
		sorted_top = {}
		for m in ecos:
			money = ecos[m]['money']
			if m in pigs: money += pigs[m]['balance']
			sorted_top[m] = money
		sorted_top = sorted(sorted_top, key=lambda k: -sorted_top[k])
		toppos = sorted_top.index(str(member.id))+1

		#Embed
		emb = disnake.Embed(title=member.display_name, color=EMBEDCOLOR)
		emb.set_thumbnail(url=member.display_avatar)
		emb.set_footer(text=f"Ранг: #{toppos}")
		
		emb.add_field(name="Гроші:", value=(
			f"> 💸 На руках: `{hf(eco['money'])}/{hf(MAX_MONEY)}`{CURRENCY}\n"
			f"> 🐖 Баланс свині: `{hf(pig_money)}/{hf(max_pig_money)}`{CURRENCY}\n"
			f"> 💰 Загалом: `{hf(eco['money']+pig_money)}`{CURRENCY}"
		), inline=False)
		icon = ""
		if int(job) != 0:
			icon = f"{self.icon(member, jobs[job]['icon'])} "
		emb.add_field(name="Робота:", value=(
			f"> {icon}{jobs[job]['name']}"
		), inline=False)
		emb.add_field(name="Доступні команди:", value=cmds, inline=False)

		await inter.send(embed=emb)


	### Затримки
	@commands.slash_command(name="cooldowns", description="📋 Подивитися список затримок.", guild_ids=[GUILD_ID])
	@commands.cooldown(1, 2, commands.BucketType.user)
	async def cooldowns(self, inter:disnake.CommandInter, учасник:disnake.Member=commands.Param(description="Учасник", default=None)):
		if inter.locale == disnake.Locale.ru:
			return await error(inter, "<:cross:1127281507430576219> **При ініціалізації мови сталася помилка!**")
		member = учасник
		if not member: member = inter.author
		if member.bot: return await error(inter, '<:cross:1127281507430576219> **Ви не можете дивитися затримку ботів!**')
		register(inter.author)
		if member != inter.author: register(member)
		cooldown = cooldown_db.find(f"{member.id}")
		content = ""
		sorting = ['work', 'crime', 'mine', 'pay', 'trade', 'blackjack', 'card', 'pig-feed', 'pig-fight', 'color']
		#Додавання нових команд
		for cmd in cooldown:
			if cmd in ("gencommands"): continue
			if cmd not in sorting:
				sorting.append(cmd)
		#Сортування
		for cmd in sorting:
			if cmd not in cooldown: continue
			if int(cooldown[cmd]) < curTime():
				content += f"**`/{cmd}` — <:check:1127281505153069136> Готово!**\n"
			else: content += f"**`/{cmd}` —** <t:{cooldown[cmd]}:R>, <t:{cooldown[cmd]}:T>\n"
		emb = disnake.Embed(title=member.display_name, description=content, color=EMBEDCOLOR, timestamp=inter.created_at)
		emb.set_thumbnail(url=member.display_avatar)
		await inter.send(embed=emb)


	### Пахати
	@commands.slash_command(name="work", description="💰 Працювати і заробляти гроші.", guild_ids=[GUILD_ID])
	@commands.cooldown(1, 2, commands.BucketType.user)
	async def work(self, inter:disnake.CommandInter):
		if inter.locale == disnake.Locale.ru:
			return await error(inter, "<:cross:1127281507430576219> **При ініціалізації мови сталася помилка!**")
		register(inter.author)
		eco = eco_db.find(f"{inter.author.id}")
		jobs = jobs_db.full()
		if eco['job'] < 1:
			return await error(inter, "<:cross:1127281507430576219> **Наразі ви безробітний! Влаштуватися на роботу можна в </jobs:1213168795728879701>**")
		job = jobs[str(eco['job'])]
		if eco["money"] >= MAX_MONEY:
			return await error(inter, f"<:cross:1127281507430576219> **Ви не можете заробити більше ніж {hf(MAX_MONEY)}{CURRENCY}**")

		#Затримка
		check = await checkcooldown(inter.author, "work")
		if check: return await cooldown_notice(inter, check)
		set_cooldown(inter.author, "work", job['cooldown'])

		#Гроші
		MIN, MAX = job['payout']
		amount = random.randint(MIN, MAX)
		eco['money'] += amount
		eco_db.update(f"{inter.author.id}", eco)

		#Відповідь
		reply = random.choice(job['messages'])
		reply = f"**{self.icon(inter.author, job['icon'])} {reply}**".replace("{amount}", f"{hf(amount)}{CURRENCY}")
		await success(inter, reply, footer=f"{job['name']} • Баланс: {hf(eco['money'])}₴")


	### Злочин
	@commands.slash_command(name="crime", description="💰 Великий прибуток, але є шанс втратити гроші.", guild_ids=[GUILD_ID])
	@commands.cooldown(1, 2, commands.BucketType.user)
	async def crime(self, inter: disnake.CommandInter):
		if inter.locale == disnake.Locale.ru:
			return await error(inter, "<:cross:1127281507430576219> **При ініціалізації мови сталася помилка!**")
		register(inter.author)
		eco = eco_db.find(f"{inter.author.id}")
		jobs = jobs_db.full()
		if eco['job'] == 0: eco['job'] = 1
		job = jobs[str(eco['job'])]
		if eco["money"] >= MAX_MONEY:
			return await error(inter, f"<:cross:1127281507430576219> **Ви не можете заробити більше ніж {hf(MAX_MONEY)}{CURRENCY}**")

		#Затримка
		check = await checkcooldown(inter.author, "crime")
		if check: return await cooldown_notice(inter, check)
		set_cooldown(inter.author, "crime", int(job['cooldown']*1.5))

		#Гроші
		MIN, MAX = job['payout']
		amount = random.randint(MIN, MAX)
		fail = False
		if random.randint(1,100) < CRIME_CHANCE: fail = True

		#Відпоівдь
		if fail:
			amount = int(amount*1.1)
			reply = f"**<:cross:1127281507430576219> {random.choice(FAIL_CRIME_REPLIES)}**".replace("{amount}", f"{hf(amount)}{CURRENCY}")
			await error(inter, reply, ephemeral=False, footer=f"Баланс: {hf(eco['money']-amount)}₴")
			eco['money'] -= amount
		else:
			amount = int(amount*1.5)
			reply = f"**{random.choice(CRIME_REPLIES)}**".replace("{amount}", f"{hf(amount)}{CURRENCY}")
			await success(inter, reply, footer=f"Баланс: {hf(eco['money']+amount)}₴")
			eco['money'] += amount
		eco_db.update(f"{inter.author.id}", eco)


	### Передати гроші
	@commands.slash_command(name="pay", description="💰 Передати гроші користувачу.", guild_ids=[GUILD_ID])
	@commands.cooldown(1, 2, commands.BucketType.user)
	async def pay(self, inter:disnake.CommandInter, учасник:disnake.Member, кількість:str=commands.Param(description="Кількість грошей. all - всі ваші гроші.")):
		if inter.locale == disnake.Locale.ru:
			return await error(inter, "<:cross:1127281507430576219> **При ініціалізації мови сталася помилка!**")
		member, amount = учасник, кількість
		all_arg = ('all', 'всі', 'все', 'oll', 'усі', 'усе')
		register(inter.author)
		register(member)
		if member.bot: return await error(inter, "<:cross:1127281507430576219> **Боти не можуть мати грошей!**")
		if member.id == inter.author.id: return await error(inter, f"<:cross:1127281507430576219> **Як ти зібрався передавати гроші собі?**")
		eco = eco_db.full()
		#Кількість
		if amount.lower() in all_arg:
			amount = eco[str(inter.author.id)]['money']
		try: amount = int(amount)
		except:
			return await error(inter, f"<:cross:1127281507430576219> **Не вдалося передати гроші!**")

		#Затримка
		check = await checkcooldown(inter.author, "pay")
		if check: return await cooldown_notice(inter, check)
		if eco[str(inter.author.id)]['money'] < amount:
			return await error(inter, f"<:cross:1127281507430576219> **У вас не вистачає грошей! ({hf(eco[str(inter.author.id)]['money'])}/{hf(amount)}{CURRENCY})**")

		#Перевірки
		if amount <= 0: return await error(inter, f"<:cross:1127281507430576219> **Цікаво, як ти зібрався передавати негативну кількість грошей?**")
		if amount > PAY_LIMIT: return await error(inter, f"<:cross:1127281507430576219> **Ви не можете передати більше за {PAY_LIMIT}{CURRENCY}**")
		if eco[str(member.id)]["money"]+amount >= MAX_MONEY:
			return await error(inter, f"<:cross:1127281507430576219> **У {member.mention} ліміт грошей! ({hf(MAX_MONEY)}{CURRENCY})**")

		#Комісія
		commision = int(percent(amount, 4))
		if commision < 1: commision = 1
		if amount+commision > eco[str(inter.author.id)]['money']:
			amount -= commision

		#БД
		set_cooldown(inter.author, "pay", PAY_COOLDOWN)
		eco[str(inter.author.id)]['money'] -= amount+commision
		eco[str(member.id)]['money'] += amount
		eco_db.update('', eco)
		#Відповідь
		emb = disnake.Embed(description=(
			f"**<:check:1127281505153069136> Успішно передано гроші користувачу <@{member.id}>!**\n"
			f"> **Сума: {hf(amount)}{CURRENCY}**\n"
			f"> **Комісія: {hf(commision)}{CURRENCY} (4%)**"
		), color=GREEN, timestamp=inter.created_at)
		await inter.response.send_message(member.mention, embed=emb)


	### Роботи
	@commands.slash_command(name="jobs", description="💰 Переглянути роботи.", guild_ids=[GUILD_ID])
	@commands.cooldown(1, 2, commands.BucketType.user)
	async def jobscmd(self, inter:disnake.CommandInter):
		if inter.locale == disnake.Locale.ru:
			return await error(inter, "<:cross:1127281507430576219> **При ініціалізації мови сталася помилка!**")
		await self.jobs_func(inter, 1)

	async def jobs_func(self, inter: disnake.CommandInteraction, page:int, edit=False):
		register(inter.author)
		jobs = jobs_db.full()
		eco = eco_db.find(f"{inter.author.id}")
		counts, options = 0, []
		#Embed
		emb = disnake.Embed(title="Роботи", description="Роботи впливають на зарплату та затримку </work:1213168795728879698>", color=EMBEDCOLOR)
		emb.set_thumbnail(url=inter.guild.icon)
		#Роботи
		for job in jobs:
			if int(job) <= 0: continue
			counts += 1
			if counts > page*5-5 and counts <= page*5:
				emb.add_field(name=f"{self.icon(inter.author, jobs[job]['icon'])}・{jobs[job]['name']}", value=(
					f"```\n"
					f"{jobs[job]['description']}\n"
					f"Ціна: {hf(jobs[job]['price'])}💵\n"
					f"Зарплата: {hf(jobs[job]['payout'][0])}-{hf(jobs[job]['payout'][1])}💵 / {voicelevel(jobs[job]['cooldown'])}\n"
					f"```"
				), inline=False)
				options.append(disnake.SelectOption(label=jobs[job]['name'], description=jobs[job]['description'], emoji=self.icon(inter.author, jobs[job]['icon']), value=job, default=bool(eco['job'] == int(job))))

		#Сторінки
		final_page = int(counts/5)
		if counts % 5 != 0:
			final_page += 1
		emb.set_footer(text=f"Сторінка: {page}/{final_page}")

		#Відправка
		select = disnake.ui.StringSelect(placeholder="Влаштуватися на роботу", options=options, custom_id="jobs:select")
		prev = disnake.ui.Button(emoji="<:1_:1074946080858460201>", custom_id="jobs:prev", disabled=bool(page <= 1))
		next = disnake.ui.Button(emoji="<:2_:1074946078618685520>", custom_id="jobs:next", disabled=bool(page >= final_page))
		if edit:
			return await inter.response.edit_message(embed=emb, components=[select,prev,next])
		await inter.send(embed=emb, components=[select,prev,next])


	### Магаз
	@commands.slash_command(name="shop", description="💰 Переглянути магазин серверу.", guild_ids=[GUILD_ID])
	@commands.cooldown(1, 2, commands.BucketType.user)
	async def shopcmd(self, inter:disnake.CommandInter):
		if inter.locale == disnake.Locale.ru:
			return await error(inter, "<:cross:1127281507430576219> **При ініціалізації мови сталася помилка!**")
		await self.shop_func(inter, 1)

	async def shop_func(self, inter:disnake.CommandInteraction, page:int, edit=False):
		register(inter.author)
		items = items_db.full()
		counts, options = 0, []

		#Embed
		emb = disnake.Embed(title="Магазин", description=(
			"Тут ви можете купити якісь предмети.\n"
			"**</sell:1213168795728879703>** - продати предмет."
		),color=EMBEDCOLOR)
		emb.set_thumbnail(url=inter.guild.icon)
		#Предмети
		for item in items:
			if not items[item]["allow-buy"]: continue
			counts += 1
			if counts > page*5-5 and counts <= page*5:
				#Необхідні предмети
				req_items = ""
				if items[item]["required_items"] != {}:
					req_items += "Необхідні предмети:\n"
					for req_item in items[item]["required_items"]:
						req_items += f" {items[req_item]['name']} x{hf(items[item]['required_items'][req_item])}\n"
				#Предмет
				emb.add_field(name=f"{items[item]['icon']}・{items[item]['name']}", value=(
					f"```\n"
					f"{items[item]['description']}\n"
					f"Ціна: {hf(items[item]['price'])}💵\n"
					f"{req_items}"
					f"```"
				),inline=False)
				options.append(disnake.SelectOption(label=items[item]['name'], description=items[item]['description'], emoji=items[item]['icon'], value=item))

		#Сторінки
		final_page = int(counts/5)
		if counts % 5 != 0:
			final_page += 1
		emb.set_footer(text=f"Сторінка: {page}/{final_page}")

		#Відправка
		select = disnake.ui.StringSelect(placeholder="Купити предмет", options=options, custom_id="shop:buy")
		prev = disnake.ui.Button(emoji="<:1_:1074946080858460201>", custom_id="shop:prev", disabled=bool(page <= 1))
		next = disnake.ui.Button(emoji="<:2_:1074946078618685520>", custom_id="shop:next", disabled=bool(page >= final_page))
		if edit:
			return await inter.response.edit_message(embed=emb, components=[select,prev,next])
		await inter.send(embed=emb, components=[select,prev,next])


	async def buy_item(self, inter:disnake.MessageInteraction, item:str, amount:int=1):
		items = items_db.full()
		eco = eco_db.find(f"{inter.author.id}")
		#Перевірки
		if 'stack-limit' not in items[item]:
			items[item]["stack-limit"] = 999
		if items[item]["price"] <= 0:
			return await error(inter, "<:cross:1127281507430576219> **Не вдалося купити цей предмет!**")
		elif 'allow-buy' not in items[item] or items[item]['allow-buy'] == False:
			return await error(inter, f"<:cross:1127281507430576219> **Нема такого предмета!**")
		elif item in eco and eco[item]+amount > items[item]["stack-limit"]:
			return await error(inter, f"<:cross:1127281507430576219> **Ви не можете мати кількість `{items[item]['name']}` більше за {items[item]['stack-limit']}!**")
		elif amount > items[item]["stack-limit"]:
			return await error(inter, f"<:cross:1127281507430576219> **Ви не можете мати кількість `{items[item]['name']}` більше за {items[item]['stack-limit']}!**")
		elif eco["money"] < items[item]["price"] * amount:
			return await error(inter, f"<:cross:1127281507430576219> **У вас не вистачає грошей! ({hf(eco['money'])}/{hf(items[item]['price'] * amount)}{CURRENCY})**")
		#Скрипт
		script = True
		if 'script_name' in items[item] and items[item]["script_name"] != None:
			script = await run_script(items[item]["script_name"], inter.author)
		if script != True: return await error(inter, f"{script}")
		eco = eco_db.find(f"{inter.author.id}")
		#Потрібні предмети
		if items[item]["required_items"] != {}:
			for ri in items[item]["required_items"]:
				#Перевірка
				required_amount = items[item]["required_items"][ri]
				required_item = items_db.find(ri)
				if not ri in eco:
					return await error(inter, f"<:cross:1127281507430576219> **Вам не вистачає: {required_item['name']} x{required_amount}**")

				#Прибрати потрібні предмети
				if "dont_remove_reqitems" not in items[item]:
					if eco[ri] > required_amount:
						eco[ri] -= required_amount
					elif eco[ri] == required_amount:
						eco.pop(ri)
					else:
						return await error(inter, f"<:cross:1127281507430576219> **Вам не вистачає: {required_item['name']} x{required_amount-eco[ri]}**")

		#Видача предмета
		if 'inventory' in items[item] and items[item]["inventory"] == True:
			if not item in eco:
				eco[item] = 0
			eco[item] += amount

		#Відправлення повідомлення
		eco['money'] -= int(items[item]['price']*amount)
		eco_db.update(f"{inter.author.id}", eco)
		reply_message = ""
		if "reply_message" in items[item]: reply_message = items[item]["reply_message"]
		await success(inter, f"<:check:1127281505153069136> **Успішно куплено предмет {items[item]['name']} x{amount} по ціні {hf(int(items[item]['price']*amount))}{CURRENCY}**\n{reply_message}", footer=f"Баланс: {hf(eco['money'])}₴")


	@commands.Cog.listener("on_modal_submit")
	async def modal(self, inter:disnake.ModalInteraction):
		if inter.custom_id.startswith("shop:buy:"):
			custom_id = inter.custom_id.split(":")
			await self.buy_item(inter, custom_id[2], int(inter.text_values['amount']))


	@commands.Cog.listener("on_dropdown")
	async def dropdown(self, inter:disnake.MessageInteraction):
		if inter.component.custom_id == "shop:buy":
			author = inter.message.interaction.author.id
			if inter.author.id != author:
				return await error(inter, "<:cross:1127281507430576219> **Ви не автор повідомлення!**")
			item = inter.values[0]
			items = items_db.full()
			eco = eco_db.find(f"{inter.author.id}")
			amount = 1
			#Перевірки
			if 'stack-limit' not in items[item]:
				items[item]["stack-limit"] = 9999
			if items[item]["price"] <= 0:
				return await error(inter, "<:cross:1127281507430576219> **Не вдалося купити цей предмет!**")
			elif 'allow-buy' not in items[item] or items[item]['allow-buy'] == False:
				return await error(inter, f"<:cross:1127281507430576219> **Нема такого предмета!**")
			elif item in eco and eco[item]+amount > items[item]["stack-limit"]:
				return await error(inter, f"<:cross:1127281507430576219> **Ви не можете мати кількість `{items[item]['name']}` більше за {items[item]['stack-limit']}!**")
			elif amount > items[item]["stack-limit"]:
				return await error(inter, f"<:cross:1127281507430576219> **Ви не можете мати кількість `{items[item]['name']}` більше за {items[item]['stack-limit']}!**")
			elif eco["money"] < items[item]["price"] * amount:
				return await error(inter, f"<:cross:1127281507430576219> **У вас не вистачає грошей! ({hf(eco['money'])}/{hf(items[item]['price'] * amount)}{CURRENCY})**")
			#Купівля
			if items[item]["stack-limit"] > 1:
				components = disnake.ui.TextInput(label="Кількість предметів", custom_id="amount", min_length=1, max_length=3, placeholder=f"1 - {items[item]['stack-limit']}")
				modal = disnake.ui.Modal(title="Кількість", components=components, custom_id=f"shop:buy:{item}")
				return await inter.response.send_modal(modal)
			await self.buy_item(inter, item, 1)

		elif inter.component.custom_id.startswith("jobs:select"):
			author = inter.message.interaction.author.id
			if inter.author.id != author:
				return await error(inter, "<:cross:1127281507430576219> **Ви не автор повідомлення!**")
			eco = eco_db.find(f"{inter.author.id}")
			job = inter.values[0]
			jobs = jobs_db.full()
			#Перевірки
			if int(job) == eco['job']:
				return await error(inter, "<:cross:1127281507430576219> **Ви вже працюєте на цій роботі!**")
			if eco['job'] > int(job):
				return await error(inter, "<:cross:1127281507430576219> **Ви вже працюєте на кращій роботі!**")
			elif jobs[job]['price'] > 0 and eco["money"] < jobs[job]["price"]:
				return await error(inter, f"<:cross:1127281507430576219> **У вас не вистачає грошей! ({hf(eco['money'])}/{hf(jobs[job]['price'])}{CURRENCY})**")

			#Відправлення повідомлення
			eco['job'] = int(job)
			eco['money'] -= int(jobs[job]['price'])
			eco_db.update(f"{inter.author.id}", eco)
			set_cooldown(inter.author, "work", 0)
			set_cooldown(inter.author, "crime", 0)
			await success(inter, f"<:check:1127281505153069136> **Ви успішно влаштувалися на роботу {jobs[job]['name']}!**", footer=f"Баланс: {hf(eco['money'])}₴")


	@commands.Cog.listener("on_button_click")
	async def button(self, inter:disnake.MessageInteraction):
		if inter.component.custom_id.startswith("sell:"):
			eco = eco_db.find(f"{inter.author.id}")
			items = items_db.full()
			custom_id = inter.component.custom_id.split(":")
			name, amount = custom_id[1], int(custom_id[2])
			item = items[name]

			#Перевірки
			if name not in eco:
				return await error(inter, f"<:cross:1127281507430576219> **У вас немає {item['name']}!**")
			elif name in eco and int(amount) > eco[name]:
				return await error(inter, f"<:cross:1127281507430576219> **Недостатньо предметів для продажу! ({eco[name]}/{int(amount)})**")

			#Видалення предмету
			if eco[name] > amount:
				eco[name] -= amount
			else:
				eco.pop(name)

			#Ціна
			sellprice = item["sell-price"]*amount
			if eco["money"]+sellprice >= MAX_MONEY:
				return await error(inter, f"<:cross:1127281507430576219> **Ви не можете заробити більше ніж {hf(MAX_MONEY)}{CURRENCY}**")
			#БД
			eco['money'] += sellprice
			eco_db.update(f"{inter.author.id}", eco)
			await success(inter, f"<:check:1127281505153069136> **Ви успішно продали {item['name']} x{amount} і отримали {hf(sellprice)}{CURRENCY}**", ephemeral=True, footer=f"Баланс: {hf(eco['money'])}₴")

		elif inter.component.custom_id.startswith(("shop:", "jobs:")):
			author = inter.message.interaction.author.id
			text = inter.message.embeds[0].footer.text
			page = int(text.replace("Сторінка: ", "").split("/")[0])
			if inter.author.id != author:
				return await error(inter, "<:cross:1127281507430576219> **Ви не автор повідомлення!**")
			#Сторінки
			if "prev" in inter.component.custom_id: page -= 1
			elif "next" in inter.component.custom_id: page += 1
			#Відправка
			if inter.component.custom_id.startswith("shop:"):
				await self.shop_func(inter, page, edit=True)
			elif inter.component.custom_id.startswith("jobs:"):
				await self.jobs_func(inter, page, edit=True)


	### Продати предмет
	@commands.slash_command(name="sell", description="💰 Продати предмет.", guild_ids=[GUILD_ID])
	@commands.cooldown(1, 2, commands.BucketType.user)
	async def sell(self, inter:disnake.CommandInter, назва_предмету:str=commands.Param(description="Назва предмету", autocomplete=autocomplete_sell), кількість:str=commands.Param(description="Кількість предметів", default="1")):
		if inter.locale == disnake.Locale.ru:
			return await error(inter, "<:cross:1127281507430576219> **При ініціалізації мови сталася помилка!**")
		name, amount = назва_предмету, кількість
		all_arg = ('all', 'всі', 'все', 'oll', 'усі', 'усе')
		register(inter.author)
		items = items_db.full()
		eco = eco_db.find(f"{inter.author.id}")
		#Кількість
		try: amount = int(amount)
		except:
			if amount.lower() not in all_arg:
				return await error(inter, f"<:cross:1127281507430576219> **Не вдалося продати цей предмет!**")
		#Пошук предмету
		search = []
		for item in items:
			if len(search) >= 20: break
			if 'name' not in items[item]: continue
			if 'allow-sell' not in items[item]: continue
			if not items[item]['allow-sell']: continue
			if name.lower() == items[item]['name'].lower():
				search.append(item)
		if len(search) != 1:
			return await error(inter, f"<:cross:1127281507430576219> **Нема такого предмета!**")
		item = search[0]
		#Перевірки
		if item not in eco:
			return await error(inter, f"<:cross:1127281507430576219> **У вас немає {items[item]['name']}!**")
		elif 'allow-sell' not in items[item] or items[item]['allow-sell'] == False:
			return await error(inter, f"<:cross:1127281507430576219> **Цей предмет не можливо продати!**")
		if amount in all_arg:
			amount = int(eco[item])
		if amount <= 0:
			return await error(inter, f"<:cross:1127281507430576219> **Кількість не може бути меншою за 0!**")
		if item in eco and int(amount) > eco[item]:
			return await error(inter, f"<:cross:1127281507430576219> **Недостатньо предметів для продажу! ({eco[item]}/{int(amount)})**")

		#Ціна
		if 'sell-price' in items[item]:
			sellprice = items[item]["sell-price"]*amount
		#Кайло
		if "pick" in item:
			one = int(items[item]['price'] / PICK_DURABILITY[item])
			sellprice = one * eco["pick_durability"]
		
		#Перевірка
		if eco["money"]+sellprice >= MAX_MONEY:
			return await error(inter, f"<:cross:1127281507430576219> **Ви не можете заробити більше ніж {hf(MAX_MONEY)}{CURRENCY}**")

		#Видалення предмету
		if eco[item] > amount:
			eco[item] -= amount
		else:
			eco.pop(item)

		eco['money'] += sellprice
		eco_db.update(f"{inter.author.id}", eco)
		await success(inter, f"<:check:1127281505153069136> **Ви успішно продали {items[item]['name']} x{amount} і отримали {hf(sellprice)}{CURRENCY}**", footer=f"Баланс: {hf(eco['money'])}₴")


	### Шахта
	@commands.slash_command(name="mine", description="💰 Добувати руди, які потім можна продати. Потребує кайло.", guild_ids=[GUILD_ID])
	@commands.cooldown(1, 2, commands.BucketType.user)
	async def mine(self, inter:disnake.CommandInter):
		if inter.locale == disnake.Locale.ru:
			return await error(inter, "<:cross:1127281507430576219> **При ініціалізації мови сталася помилка!**")
		register(inter.author)
		eco = eco_db.find(f"{inter.author.id}")
		items = items_db.full()
		btns = []

		check = await checkcooldown(inter.author, "mine")
		if check: return await cooldown_notice(inter, check)

		#Кайло
		if not any(x in eco for x in list(PICK_DURABILITY)):
			return await error(inter, f"<:cross:1127281507430576219> **У вас немає кайла! Купити його можна в </shop:1213168795728879702>**", ephemeral=False)
		curPickaxe = None
		for p in list(PICK_DURABILITY):
			if p in eco:
				curPickaxe = p
				break
		picks = list(PICK_DURABILITY)
		picks.reverse()
		multiple = picks.index(curPickaxe)/10+1 * random.uniform(1,1.4)
		materials = ""
		not_limited_resources = 0

		#Камінь
		rocks = int(random.randint(MINE_ROCKS[0], MINE_ROCKS[1]) * multiple)
		if rocks < 0: rocks = 1
		if rocks > 0:
			if not 'rock' in eco: eco['rock'] = 0
			if eco['rock']+rocks > items['rock']['stack-limit']:
				materials += f"- {items['rock']['icon']} `❗ Ліміт`\n"
				btns.append(disnake.ui.Button(emoji=f"{items['rock']['icon']}", custom_id=f"sell:rock:{eco['rock']}"))
			else:
				not_limited_resources += 1
				eco['rock'] += rocks
				materials += f"- {items['rock']['icon']} `{items['rock']['name']} x{rocks}`\n"
				btns.append(disnake.ui.Button(emoji=items['rock']['icon'], custom_id=f"sell:rock:{rocks}"))

		#Залізо
		iron = int(random.randint(MINE_IRON[0], MINE_IRON[1]) * multiple)
		if iron < 0: iron = 1
		try: chance = {'pick': 60, 'pick2': 75, 'pick3': 90, 'pick4': 101, 'pick5': 101}[curPickaxe]
		except: chance = 0
		if random.randint(1,100) < chance:
			if not "iron" in eco: eco['iron'] = 0
			if eco['iron']+iron > items['iron']['stack-limit']:
				materials += f"- {items['iron']['icon']} `❗ Ліміт`\n"
				btns.append(disnake.ui.Button(emoji=f"{items['iron']['icon']}", custom_id=f"sell:iron:{eco['iron']}"))
			else:
				not_limited_resources += 1
				eco['iron'] += iron
				materials += f"- {items['iron']['icon']} `{items['iron']['name']} x{iron}`\n"
				btns.append(disnake.ui.Button(emoji=items['iron']['icon'], custom_id=f"sell:iron:{iron}"))

		#Золото
		gold = int(random.randint(MINE_GOLD[0], MINE_GOLD[1]) * multiple)
		if gold < 0: gold = 1
		try: chance = {'pick2': 60, 'pick3': 70, 'pick4': 75, "pick5": 101}[curPickaxe]
		except: chance = 0
		if random.randint(1,100) < chance:
			if not "gold" in eco: eco['gold'] = 0
			if eco['gold']+gold > items['gold']['stack-limit']:
				materials += f"- {items['gold']['icon']} `❗ Ліміт`\n"
				btns.append(disnake.ui.Button(emoji=f"{items['gold']['icon']}", custom_id=f"sell:gold:{eco['gold']}"))
			else:
				not_limited_resources += 1
				eco['gold'] += gold
				materials += f"- {items['gold']['icon']} `{items['gold']['name']} x{gold}`\n"
				btns.append(disnake.ui.Button(emoji=items['gold']['icon'], custom_id=f"sell:gold:{gold}"))

		#Діамант
		diamond = int(random.randint(MINE_DIAMOND[0], MINE_DIAMOND[1]) * multiple)
		if diamond < 0: diamond = 1
		try: chance = {'pick2': 15, 'pick3': 20, 'pick4': 30, "pick5": 45}[curPickaxe]
		except: chance = 0
		if random.randint(1,100) < chance:
			if not "diamond" in eco: eco['diamond'] = 0
			if eco['diamond']+diamond > items['diamond']['stack-limit']:
				materials += f"- {items['diamond']['icon']} `❗ Ліміт`\n"
				btns.append(disnake.ui.Button(emoji=f"{items['diamond']['icon']}", custom_id=f"sell:diamond:{eco['diamond']}"))
			else:
				not_limited_resources += 1
				eco['diamond'] += diamond
				materials += f"- {items['diamond']['icon']}`{items['diamond']['name']} x{diamond}`\n"
				btns.append(disnake.ui.Button(emoji=f"{items['diamond']['icon']}", custom_id=f"sell:diamond:{diamond}"))

		#Смарагд
		emerald = int(random.randint(MINE_EMERALD[0], MINE_EMERALD[1]) * multiple)
		if emerald < 0: emerald = 1
		try: chance = {'pick3': 10, 'pick4': 15, "pick5": 20}[curPickaxe]
		except: chance = 0
		if random.randint(1,100) < chance:
			if not "emerald" in eco: eco['emerald'] = 0
			if eco['emerald']+emerald > items['emerald']['stack-limit']:
				materials += f"- {items['emerald']['icon']} `❗ Ліміт`\n"
				btns.append(disnake.ui.Button(emoji=f"{items['emerald']['icon']}", custom_id=f"sell:emerald:{eco['emerald']}"))
			else:
				not_limited_resources += 1
				eco['emerald'] += emerald
				materials += f"- {items['emerald']['icon']} `{items['emerald']['name']} x{emerald}`\n"
				btns.append(disnake.ui.Button(emoji=f"{items['emerald']['icon']}", custom_id=f"sell:emerald:{emerald}"))

		#Енергокамінь
		try: chance = {'pick3': 4, 'pick4': 8, "pick5": 12}[curPickaxe]
		except: chance = 0
		if random.randint(1,100) < chance:
			if not "energystone" in eco: eco['energystone'] = 0
			if eco['energystone']+1 > items['energystone']['stack-limit']:
				materials += f"- {items['energystone']['icon']} `❗ Ліміт`\n"
				btns.append(disnake.ui.Button(emoji=f"{items['energystone']['icon']}", custom_id=f"sell:energystone:{eco['energystone']}"))
			else:
				not_limited_resources += 1
				eco['energystone'] += 1
				materials += f"- {items['energystone']['icon']} `{items['energystone']['name']} x1`\n"
				btns.append(disnake.ui.Button(emoji=f"{items['energystone']['icon']}", custom_id=f"sell:energystone:1"))

		#Зламання
		brokenpick = ""
		if not_limited_resources > 0:
			eco["pick_durability"] -= len(btns)
			brokenpick = "<:pick_broken:1188447824736702494> **Ваше кайло зламалося!**" if eco['pick_durability'] < 1 else ''
			if eco["pick_durability"] < 1:
				eco.pop(curPickaxe)
				eco.pop("pick_durability")

		#Відповідь
		if not_limited_resources > 0:
			set_cooldown(inter.author, "mine", MINE_COOLDOWN)
			eco_db.update(f"{inter.author.id}", eco)
		await success(inter, f"**Ви добули:\n{materials}**\n{brokenpick}", components=btns, footer="Ресурси можна продати кнопками нижче.")


	### Колір
	@commands.slash_command(name="color", description="🎨 Встановити собі кастомний колір.", guild_ids=[GUILD_ID])
	@commands.cooldown(1, 2, commands.BucketType.user)
	async def color(self, inter:disnake.CommandInter, колір:str=commands.Param(description="HEX колір, наприклад: #ff0000")):
		hex_color = колір.replace("#","").lower()
		if inter.locale == disnake.Locale.ru:
			return await error(inter, "<:cross:1127281507430576219> **При ініціалізації мови сталася помилка!**")
		#Затримка
		check = await checkcooldown(inter.author, "color")
		if check: return await cooldown_notice(inter, check)

		#Перевірка кольору
		eco = eco_db.find(f"{inter.author.id}")
		if 'custom_color' not in eco:
			return await error(inter, "<:cross:1127281507430576219> **У вас немає власного кольору! Його можна купити в </shop:1213168795728879702>**")
		if len(hex_color) < 6 or len(hex_color) > 7:
			return await error(inter, "<:cross:1127281507430576219> **Вкажіть колір у вигляді HEX, наприклад #ff0000**")
		try: newcolor = str_to_hex(hex_color)
		except:
			return await error(inter, "<:cross:1127281507430576219> **Вкажіть колір у вигляді HEX, наприклад #ff0000**")

		#Ролі
		given_role = None
		for role in inter.guild.roles:
			if role.name.lower() == f"#{hex_color}".lower():
				given_role = role
		if given_role == None:
			given_role = await inter.guild.create_role(name=f"#{hex_color}".lower(), color=newcolor)
			await given_role.edit(position=inter.guild.get_role(944886784041558057).position+1)

		#Видача ролі
		for r in inter.author.roles:
			if not r.name.startswith("#"): continue
			if len(r.members) == 1:
				try: await r.delete()
				except: pass
			else:
				try: await inter.author.remove_roles(r)
				except: pass
		await inter.author.add_roles(given_role)

		#Відповідь
		emb = disnake.Embed(description=f"**<:check:1127281505153069136> Успішно встановлено новий колір нікнейму! {given_role.mention}**", color=newcolor, timestamp=inter.created_at)
		emb.set_author(name=f"@{inter.author}", icon_url=inter.author.display_avatar)
		await inter.send(embed=emb)
		set_cooldown(inter.author, "color", 300)


	@commands.slash_command(name="color-remove", description="🎨 Прибрати кастомний колір.", guild_ids=[GUILD_ID])
	@commands.cooldown(1, 15, commands.BucketType.user)
	async def colorremove(self, inter:disnake.CommandInter):
		if inter.locale == disnake.Locale.ru:
			return await error(inter, "<:cross:1127281507430576219> **При ініціалізації мови сталася помилка!**")

		#Прибирання ролі
		role_removed = False
		for r in inter.author.roles:
			if not r.name.startswith("#"): continue
			if len(r.members) == 1:
				try: await r.delete()
				except: pass
				role_removed = True
			else:
				try: await inter.author.remove_roles(r)
				except: pass
				role_removed = True
		if not role_removed:
			return await error(inter, "<:cross:1127281507430576219> **У вас вже немає власного кольору!**")

		#Відповідь
		await success(inter, "**<:check:1127281505153069136> Успішно прибрано ваш кастомний колір!**")


def setup(bot:commands.Bot):
	bot.add_cog(Economy(bot))