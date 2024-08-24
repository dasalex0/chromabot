from utils import *


class Programs(commands.Cog):
	def __init__(self, bot:commands.Bot):
		self.bot = bot
		self.edit_cooldown = {}


	###
	### Питання
	###
	async def question(self, inter:disnake.MessageInteraction, channel:disnake.TextChannel, custom_id:str, use_price:bool=True):
		#БД
		if use_price:
			price = items_db.find(custom_id)['price']
		#Затримка
		if str(channel.id) not in self.edit_cooldown: self.edit_cooldown[str(channel.id)] = 0
		if self.edit_cooldown[str(channel.id)] > time():
			return await cooldown_notice(inter, self.edit_cooldown[str(channel.id)])
		#Назва
		if custom_id == 'program_name':
			text = "Ви збираєтеся змінити назву програми.\n"
		#Тема
		elif custom_id == 'program_topic':
			text = "Ви збираєтеся змінити тему програми.\n"
		#Тема
		elif custom_id == 'program_emoji':
			text = "Ви збираєтеся змінити іконку програми.\n"
		#Підняття програми
		elif custom_id == 'program_up':
			text = "Ви збираєтеся підняти програму на 1 позицію вгору.\n"
			uppos = len(channel.category.channels)-get_position(inter.guild, channel)+1
			price = 250+400*uppos
			if price > MAX_MONEY: price = MAX_MONEY
			use_price = True
		#Передача власності
		elif custom_id.startswith('program_transfer'):
			text = f"Ви збираєтеся передати програму користувачу <@{custom_id.split('_')[2]}>.\nЦе не можна буде скасувати! Продовжити?\n"
		#Embed
		if use_price:
			text += f"Це коштуватиме вам {hf(price)}{CURRENCY}. Продовжити?\n"
		emb = disnake.Embed(description=f"**{text}**", color=INVISIBLE)
		emb.set_author(name=f"@{inter.author.name}", icon_url=inter.author.display_avatar)
		confirm = disnake.ui.Button(label='Підтвердити', style=disnake.ButtonStyle.green, custom_id=f"{custom_id}:{channel.id}:{inter.author.id}")
		await inter.response.send_message(embed=emb, ephemeral=True, components=[confirm])


	@commands.Cog.listener()
	async def on_button_click(self, inter:disnake.MessageInteraction):
		if inter.component.custom_id.startswith('program_'):
			#Перевірка
			items = items_db.full()
			custom_id = inter.component.custom_id.split(':')[0]
			channel_id = int(inter.component.custom_id.split(':')[1])
			author_id = int(inter.component.custom_id.split(':')[2])
			if inter.author.id != author_id and custom_id == 'program_join':
				return await error(inter, "<:cross:1127281507430576219> **Це запрошення адресовано не вам!**")
			elif inter.author.id != author_id:
				return await error(inter, "<:cross:1127281507430576219> **Керувати програмою може лише той учасник, що виконав команду!**")
			channel = inter.guild.get_channel(channel_id)
			if channel == None:
				return await error(inter, "<:cross:1127281507430576219> **У вас немає програми! Купити її можна в </shop:1213168795728879702>**")

			#Затримка
			if str(channel.id) not in self.edit_cooldown: self.edit_cooldown[str(channel.id)] = 0
			if self.edit_cooldown[str(channel.id)] > time():
				return await cooldown_notice(inter, self.edit_cooldown[str(channel.id)])

			#Покидання програми
			if custom_id == 'program_leave':
				member = inter.guild.get_member(author_id)
				overwrites = channel.overwrites
				if inter.author not in overwrites:
					return await error(inter, "<:cross:1127281507430576219> **Ви не учасник цієї програми!**")
				owner = get_program_owner(inter, member)
				if owner != None and channel_id == owner.id:
					return await error(inter, "<:cross:1127281507430576219> **Ви не можете покинути свою програму!**")
				overwrites.pop(inter.author)
				await channel.edit(overwrites=overwrites)
				await success(inter, f"<:check:1127281505153069136> **Ви успішно покинули програму {channel.mention}!**")
				self.edit_cooldown[str(channel.id)] = curTime()+30

			#Назва
			elif custom_id == 'program_name':
				price = items['program_name']['price']
				money = eco_db.find(f"{inter.author.id}.money")
				if money < price:
					return await error(inter, f"<:cross:1127281507430576219> **У вас не вистачає грошей! {money}/{price}{CURRENCY}**")
				if channel.name[1] == "︱": value = channel.name[2:][:20]
				else: value = channel.name[:20]
				#Modal
				components = disnake.ui.TextInput(label="Нова назва програми", value=value, min_length=5, max_length=20, custom_id="name")
				modal = disnake.ui.Modal(title="Змінити назву програми", components=components, custom_id=f"program_name:{channel_id}")
				await inter.response.send_modal(modal)

			#Тема
			elif custom_id == 'program_topic':
				price = items['program_topic']['price']
				money = eco_db.find(f"{inter.author.id}.money")
				if money < price:
					return await error(inter, f"<:cross:1127281507430576219> **У вас не вистачає грошей! {money}/{price}{CURRENCY}**")
				#Modal
				components = disnake.ui.TextInput(label="Нова тема програми (опис)", value=channel.topic, max_length=150, custom_id="topic")
				modal = disnake.ui.Modal(title="Змінити тему програми", components=components, custom_id=f"program_topic:{channel_id}")
				await inter.response.send_modal(modal)

			#Емодзі
			elif custom_id == 'program_emoji':
				price = items['program_emoji']['price']
				money = eco_db.find(f"{inter.author.id}.money")
				if money < price:
					return await error(inter, f"<:cross:1127281507430576219> **У вас не вистачає грошей! {money}/{price}{CURRENCY}**")
				value = None
				if channel.name[1] == "︱": value = channel.name[0]
				#Modal
				components = disnake.ui.TextInput(label="Нова іконка програми (емодзі)", value=value, min_length=1, max_length=2, custom_id="emoji")
				modal = disnake.ui.Modal(title="Змінити іконку програми", components=components, custom_id=f"program_emoji:{channel_id}")
				await inter.response.send_modal(modal)

			#Підняття програм
			elif custom_id == 'program_up':
				money = eco_db.find(f"{inter.author.id}.money")
				uppos = len(channel.category.channels)-get_position(inter.guild, channel)+1
				price = 250+400*uppos
				if price > MAX_MONEY: price = MAX_MONEY
				if money < price:
					return await error(inter, f"<:cross:1127281507430576219> **У вас не вистачає грошей! {money}/{price}{CURRENCY}**")
				if get_position(inter.guild, channel) < 1:
					return await error(inter, f"<:cross:1127281507430576219> **Ваша програма знаходиться на максимальній позиції!**")

				#Перевірка на емодзі
				up_pos = channel.position-1
				if channel.name[1] != "︱":
					sorted_channels = sorted(channel.category.channels, key=lambda c: c.position)
					pos = sorted_channels.index(channel)
					c = sorted_channels[pos-1]
					if c.name[1] == "︱":
						return await error(inter, "<:cross:1127281507430576219> **Ви не можете підняти свою програму вище, бо у вас немає іконки!**")

				self.edit_cooldown[str(channel.id)] = curTime()+150
				await success(inter, "<:check:1127281505153069136> **Успішно піднято програму на 1 позицію вверх!**")
				await channel.edit(position=up_pos)
				eco_db.update(f"{inter.author.id}.money", money-price)

			#Передача овнерки
			elif custom_id.startswith('program_transfer'):
				self.edit_cooldown[str(channel.id)] = curTime()+300
				overwrites = channel.overwrites
				member = inter.guild.get_member(int(custom_id.split('_')[2]))
				overwrites[member] = disnake.PermissionOverwrite(read_messages=True, send_messages=True, create_public_threads=True, create_private_threads=True, embed_links=True, attach_files=True, manage_messages=True, manage_threads=True, add_reactions=True)
				overwrites[inter.author] = disnake.PermissionOverwrite(read_messages=True, send_messages=True, create_public_threads=True, create_private_threads=True, embed_links=True, attach_files=True, add_reactions=True)
				await success(inter, f"<:check:1127281505153069136> **Успішно передано право власності програми користувачу {member.mention}!**")
				await channel.edit(overwrites=overwrites)

			#Приєднання до програми
			elif custom_id == 'program_join':
				member = inter.guild.get_member(author_id)
				members = 0
				for m in channel.overwrites:
					if channel.overwrites_for(m).send_messages == True and channel.overwrites_for(m).manage_messages == False:
						members += 1
				if members > 3: return await error(inter, '<:cross:1127281507430576219> **В цій програмі забагато людей!**')

				if get_program_member(inter.guild, member):
					return await error(inter, f"<:cross:1127281507430576219> **Ви вже є учасникиком/власником однієї з програм!**")
				overwrites = channel.overwrites
				overwrites[member] = disnake.PermissionOverwrite(read_messages=True, send_messages=True, create_public_threads=True, create_private_threads=True, embed_links=True, attach_files=True, add_reactions=True)
				await channel.edit(overwrites=overwrites)
				await success(inter, f"<:check:1127281505153069136> **Ви успішно приєдналися до програми {channel.mention}!**")
				self.edit_cooldown[str(channel.id)] = curTime()+30


	@commands.Cog.listener()
	async def on_modal_submit(self, inter:disnake.ModalInteraction):
		#Назва
		if inter.custom_id.startswith('program_'):
			#Перевірка
			items = items_db.full()
			text = list(inter.text_values.items())[0][1]
			custom_id = inter.custom_id.split(':')[0]
			channel_id = int(inter.custom_id.split(':')[1])
			if not get_program_owner(inter, inter.author):
				return await error(inter, "<:cross:1127281507430576219> **У вас немає програми! Купити її можна в </shop:1213168795728879702>**")
			channel = inter.guild.get_channel(channel_id)
			if channel == None:
				return await error(inter, "<:cross:1127281507430576219> **У вас немає програми! Купити її можна в </shop:1213168795728879702>**")

			#Затримка
			if str(channel.id) not in self.edit_cooldown: self.edit_cooldown[str(channel.id)] = 0
			if self.edit_cooldown[str(channel.id)] > time():
				return await cooldown_notice(inter, self.edit_cooldown[str(channel.id)])

			#Назва
			if custom_id == 'program_name':
				price = items['program_name']['price']
				money = eco_db.find(f"{inter.author.id}.money")
				if money < price:
					return await error(inter, f"<:cross:1127281507430576219> **У вас не вистачає грошей! {money}/{price}{CURRENCY}**")
				allowed = LETTER_LIST + LETTER_ENG_LIST + NUMBER_LIST + "_-"
				if channel.name[1] == "︱": new_name = channel.name[0]+'︱'
				else: new_name = ""
				for i in text.replace(' ', '-').lower():
					if i in allowed: new_name += i
				self.edit_cooldown[str(channel.id)] = curTime()+300
				await success(inter, f'**<:check:1127281505153069136> Успішно встановлено нову назву для програми!**')
				await channel.edit(name=new_name)
				eco_db.update(f"{inter.author.id}.money", money-price)

			#Тема
			elif custom_id == 'program_topic':
				price = items['program_topic']['price']
				money = eco_db.find(f"{inter.author.id}.money")
				if money < price:
					return await error(inter, f"<:cross:1127281507430576219> **У вас не вистачає грошей! {money}/{price}{CURRENCY}**")
				self.edit_cooldown[str(channel.id)] = curTime()+300
				await success(inter, f"**<:check:1127281505153069136> Успішно встановлено нову тему для програми!**\n```{text.replace('`','')}```")
				await channel.edit(topic=text)
				eco_db.update(f"{inter.author.id}.money", money-price)

			#Емодзі
			elif custom_id == 'program_emoji':
				price = items['program_emoji']['price']
				money = eco_db.find(f"{inter.author.id}.money")
				if money < price:
					return await error(inter, f"<:cross:1127281507430576219> **У вас не вистачає грошей! {money}/{price}{CURRENCY}**")
				if emj.is_emoji(text):
					pos = channel.position
					#Емодзі вже стоїть
					if channel.name[1] == "︱":
						new_name = text+'︱'+channel.name[2:]
					#Ще немає емодзі
					else:
						new_name = text+'︱'+channel.name
						for c in sorted(channel.category.channels, key=lambda c: c.position):
							if c.name[1] != "︱":
								if channel.position != c.position:
									pos = c.position
								break
					#Output
					await success(inter, f'**<:check:1127281505153069136> Успішно встановлено нову іконку для програми!**')
					await channel.edit(name=new_name,position=pos)
					eco_db.update(f"{inter.author.id}.money", money-price)
				else:
					return await error(inter, '<:cross:1127281507430576219> **Ви вказали не емодзі!**')


	@commands.Cog.listener()
	async def on_dropdown(self, inter:disnake.MessageInteraction):
		if inter.component.custom_id.startswith('program_edit'):
			#Перевірка
			channel_id = int(inter.component.custom_id.split(':')[1])
			author_id = int(inter.component.custom_id.split(':')[2])
			if inter.author.id != author_id:
				return await error(inter, "<:cross:1127281507430576219> **Керувати програмою може лише той учасник, що виконав команду!**")
			channel = inter.guild.get_channel(channel_id)
			if channel == None:
				return await error(inter, "<:cross:1127281507430576219> **У вас немає програми! Купити її можна в </shop:1213168795728879702>**")

			#Назва
			if inter.values[0] == "Змінити назву програми":
				await self.question(inter, channel, 'program_name')
			#Тема
			elif inter.values[0] == "Змінити тему програми":
				await self.question(inter, channel, 'program_topic')
			#Іконка
			elif inter.values[0] == "Змінити іконку програми":
				await self.question(inter, channel, 'program_emoji')
			#Підняти програму
			elif inter.values[0] == "Підняти програму":
				if get_position(inter.guild, channel) < 1:
					return await error(inter, f"<:cross:1127281507430576219> **Ваша програма знаходиться на максимальній позиції!**")
				await self.question(inter, channel, 'program_up', use_price=False)
			#Учасники програми
			elif inter.values[0] == "Додати/Прибрати учасника":
				members = 0
				for member in channel.overwrites:
					if channel.overwrites_for(member).send_messages == True and channel.overwrites_for(member).manage_messages == False:
						members += 1
				if members > 3: return await error(inter, '<:cross:1127281507430576219> **Ви не можете додати більше 3 людей в програму!**')
				select = disnake.ui.UserSelect(placeholder="Додати/Прибрати учасника до програми", custom_id=f'program_members:{channel_id}')
				await inter.response.send_message(components=[select], ephemeral=True)
			#Учасники програми
			elif inter.values[0] == "Передати право власності":
				select = disnake.ui.UserSelect(placeholder="Виберіть нового власника програми", custom_id=f'program_transfer:{channel_id}')
				await inter.response.send_message(components=[select], ephemeral=True)

		#Учасники програми
		elif inter.component.custom_id.startswith('program_members'):
			#Перевірка
			owner = get_program_owner(inter, inter.author)
			channel_id = int(inter.component.custom_id.split(':')[1])
			if owner == None:
				return await error(inter, "<:cross:1127281507430576219> **У вас немає програми! Купити її можна в </shop:1213168795728879702>**")
			channel = inter.guild.get_channel(channel_id)
			if channel == None:
				return await error(inter, "<:cross:1127281507430576219> **У вас немає програми! Купити її можна в </shop:1213168795728879702>**")

			#Код
			member = inter.guild.get_member(int(inter.values[0]))
			if member == None: return
			if member.id == inter.author.id:
				return await error(inter, "<:cross:1127281507430576219> **Ви не можете додавати себе до своєї програми!**")
			if member.bot:
				return await error(inter, "<:cross:1127281507430576219> **Ви не можете додавати ботів до своєї програми!**")
			#Прибирання
			if channel.overwrites_for(member).send_messages == True:
				overwrites = channel.overwrites
				overwrites.pop(member)
				await channel.edit(overwrites=overwrites)
				await success(inter, f"<:check:1127281505153069136> **Успішно вигнано користувача {member.mention} з вашої програми.**", ephemeral=True)
				self.edit_cooldown[str(channel.id)] = curTime()+30
			#Додавання
			else:
				if get_program_member(inter.guild, member):
					return await error(inter, f"<:cross:1127281507430576219> **Цей користувач вже є учасником/власником однієї з програм!**")
				await success(inter, '<:check:1127281505153069136> **Ви успішно надіслали запит на приєднання!**', ephemeral=True)

				emb = disnake.Embed(title="Запрошення до програми", description=f"{inter.author.mention} запрошує приєднатися вас до програми {channel.mention}. У вас є 3 хвилини, щоб прийняти запрошення.", color=GREEN)
				emb.set_thumbnail(url=inter.author.display_avatar)
				confirm = disnake.ui.Button(label="Прийняти", style=disnake.ButtonStyle.green, custom_id=f'program_join:{channel.id}:{member.id}')
				msg = await inter.channel.send(member.mention, embed=emb, components=[confirm])
				try: await msg.delete(delay=180)
				except: pass
				self.edit_cooldown[str(channel.id)] = curTime()+30

		#Передача власності
		elif inter.component.custom_id.startswith('program_transfer'):
			#Перевірка
			owner = get_program_owner(inter, inter.author)
			channel_id = int(inter.component.custom_id.split(':')[1])
			if owner == None:
				return await error(inter, "<:cross:1127281507430576219> **У вас немає програми! Купити її можна в </shop:1213168795728879702>**")
			channel = inter.guild.get_channel(channel_id)
			if channel == None:
				return await error(inter, "<:cross:1127281507430576219> **У вас немає програми! Купити її можна в </shop:1213168795728879702>**")

			#Код
			member = inter.guild.get_member(int(inter.values[0]))
			if member == None: return
			if member.id == inter.author.id:
				return await error(inter, "<:cross:1127281507430576219> **Ви вже власник програми!**")
			if get_program_member(inter.guild, member).id != channel.id or member.bot:
				return await error(inter, f"<:cross:1127281507430576219> **Цей користувач не є учасником вашої програми!**")
			await self.question(inter, channel, f'program_transfer_{member.id}', use_price=False)



	@commands.slash_command(name="program", description="📢 Налаштувати свою програму.", guild_ids=[GUILD_ID])
	@commands.cooldown(1, 2, commands.BucketType.user)
	async def program(self, inter:disnake.CommandInter):
		#Перевірка
		if inter.locale == disnake.Locale.ru:
			return await error(inter, "<:cross:1127281507430576219> **При ініціалізації мови сталася помилка!**")
		program_role = inter.guild.get_role(PROGRAM_ID)
		channel, program_owner = None, None
		#Перевірка на учасника програми
		owner = get_program_owner(inter, inter.author)
		if owner == None:
			check = get_program_member(inter.guild, inter.author)
			if check != None: channel = check
		else:
			channel = owner
			program_owner:disnake.Member = inter.author
		#Немає програми
		if channel == None:
			if program_role in inter.author.roles:
				try: await inter.author.remove_roles(program_role)
				except: pass
			return await error(inter, "<:cross:1127281507430576219> **У вас немає програми! Купити її можна в </shop:1213168795728879702>**")
		#Перевірка на архівованість
		if channel.overwrites_for(inter.guild.default_role).read_messages == False:
			return await error(inter, "<:cross:1127281507430576219> **Ваша програма була закрита через неактивність! Зверніться до адміністрації, щоб відновити її.**")
		#Преевірка на овнера
		if program_owner == None:
			for member in channel.overwrites:
				if channel.overwrites_for(member).manage_messages == True and channel.overwrites_for(member).send_messages == True:
					program_owner = member
		if program_owner == None:
			return await error(inter, "<:cross:1127281507430576219> **У вас немає програми! Купити її можна в </shop:1213168795728879702>**")

		#Перевірка на роль
		if program_role not in inter.author.roles:
			try: await inter.author.add_roles(program_role)
			except: pass

		#Учасники програми
		members = ""
		for member in channel.overwrites:
			if not isinstance(member, disnake.Member): continue
			if channel.overwrites_for(member).send_messages == True and member.id != program_owner.id:
				members += f"{member.mention} "
		if len(members) <= 0: members = "`Немає`"
		else: members += f"({len(members.split(' '))-1}/3)"

		#Embed
		options = []
		msg = 'Ви не є власником цієї програми, тому деякі дії можуть бути обмеженими.\n\n'
		position = get_position(inter.guild, channel)
		emb = disnake.Embed(title="Керування вашою програмою", description=(
			f"{msg if program_owner.id != inter.author.id else ''}"
			f"**📢 Ваша програма:** {channel.mention}\n"
			f"**📝 Тема:** `{'Немає' if channel.topic == None or len(channel.topic) <= 0 else channel.topic}`\n"
			f"**🔼 Позиція:** `#{position+1}`\n"
			f"**👑 Власник:** {program_owner.mention}\n"
			f"**<:people:1120347122835922984> Учасники:** {members}"
		), color=INVISIBLE)
		emb.set_footer(text=f'ID: {channel.id}')
		if program_owner.id == inter.author.id:
			options += [
				disnake.SelectOption(label='Змінити назву програми', emoji='📝'),
				disnake.SelectOption(label='Змінити тему програми', emoji='📝'),
				disnake.SelectOption(label='Змінити іконку програми', emoji='📢'),
				disnake.SelectOption(label='Додати/Прибрати учасника', emoji='<:people:1120347122835922984>'),
				disnake.SelectOption(label='Передати право власності', emoji='👑')
			]
		if position > 0:
			options += [disnake.SelectOption(label='Підняти програму', emoji='🔼')]
		dropdown = disnake.ui.StringSelect(
			options=(options if options != [] else ['123']),
			placeholder="Змінити програму...",
			custom_id=f'program_edit:{channel.id}:{inter.author.id}',
			disabled=bool(options == [])
		)
		components = [dropdown]
		if program_owner.id != inter.author.id:
			components.append(
				disnake.ui.Button(label="Покинути програму", style=disnake.ButtonStyle.red, custom_id=f'program_leave:{channel.id}:{inter.author.id}')
			)
		await inter.response.send_message(embed=emb, components=components)


def setup(bot:commands.Bot):
	bot.add_cog(Programs(bot))