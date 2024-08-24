from utils import *


class Voice(commands.Cog):
	def __init__(self, bot:commands.Bot):
		self.bot = bot
		self.cooldown = {}

	#Embed
	@commands.command()
	async def voicepanel(self, ctx:commands.Context):
		if ctx.author.id != ALEX: return
		emb = disnake.Embed(title="🔧 Керування приватними кімнатами", description=(
			"Ви можете керувати своєю кімнатою кнопками нижче.\n\n"
			"👑 — Передати права іншому користувачу.\n"
			"📝 — Перейменувати приватку.\n"
			"⛔ — Встановити ліміт користувачів.\n"
			"🔒 — Закрити/Відкрити приватку.\n"
			"👥 — Дозволити/Заборонити користувачу заходити в приватку.\n"
			"💾 — Зберегти налаштування приватки.\n"
			"📥 — Завантажити налаштування приватки."
		), color=INVISIBLE)
		await ctx.send(embed=emb, components=[
			disnake.ui.Button(emoji="👑", custom_id="voice_transfer"),
			disnake.ui.Button(emoji="📝", custom_id="voice_rename"),
			disnake.ui.Button(emoji="⛔", custom_id="voice_limit"),
			disnake.ui.Button(emoji="🔒", custom_id="voice_lock"),
			disnake.ui.Button(emoji="👥", custom_id="voice_member"),
			disnake.ui.Button(emoji="<:empty:1229687771019481129>", custom_id="voice_none", disabled=True),
			disnake.ui.Button(emoji="💾", custom_id="voice_save"),
			disnake.ui.Button(emoji="<:empty:1229687771019481129>", custom_id="voice_none2", disabled=True),
			disnake.ui.Button(emoji="📥", custom_id="voice_load"),
			disnake.ui.Button(emoji="<:empty:1229687771019481129>", custom_id="voice_none3", disabled=True)
		])
		await ctx.message.delete()


	#Перевірка
	def check(self, member: disnake.Member) -> str | disnake.VoiceChannel:
		if not member.voice:
			return "<:cross:1127281507430576219> **Ви не знаходитесь у войсі!**"
		channel = member.voice.channel
		if channel.category_id != VOICE_CATEGORY_ID or channel.id == VOICE_CREATE_ID:
			return "<:cross:1127281507430576219> **Ви не знаходитесь у войсі!**"
		if channel.overwrites_for(member).move_members != True:
			return "<:cross:1127281507430576219> **Ви не є творцем войсу!**"
		return channel


	###
	### Модал
	###
	@commands.Cog.listener()
	async def on_modal_submit(self, inter: disnake.ModalInteraction):
		if not inter.custom_id.startswith("voice_"): return
		#Назва
		if inter.custom_id == "voice_name":
			#Перевірки
			if str(inter.author.id) not in self.cooldown:
				self.cooldown[str(inter.author.id)] = {}
			if 'name' not in self.cooldown[str(inter.author.id)]:
				self.cooldown[str(inter.author.id)]['name'] = [0,0]
			#Затримка
			self.cooldown[str(inter.author.id)]['name'][1] += 1
			if self.cooldown[str(inter.author.id)]['name'][1] == 2:
				self.cooldown[str(inter.author.id)]['name'][1] = 0
				self.cooldown[str(inter.author.id)]['name'][0] = time()+600
			channel = self.check(inter.author)
			if not isinstance(channel, disnake.VoiceChannel):
				return await error(inter, channel)
			#Відповідь
			text = inter.text_values['name']
			await inter.send(f"<:check:1127281505153069136> **Успішно змінено назву приватки на `{text}`!**", ephemeral=True)
			await channel.edit(name=text)

		#Ліміт
		elif inter.custom_id == "voice_limit":
			#Перевірки
			if str(inter.author.id) not in self.cooldown:
				self.cooldown[str(inter.author.id)] = {}
			if 'limit' not in self.cooldown[str(inter.author.id)]:
				self.cooldown[str(inter.author.id)]['limit'] = 0
			self.cooldown[str(inter.author.id)]['limit'] = time()+15
			channel = self.check(inter.author)
			if not isinstance(channel, disnake.VoiceChannel):
				return await error(inter, channel)
			#Відповідь
			try: limit = int(inter.text_values['limit'])
			except: limit = 0
			await inter.send(f"<:check:1127281505153069136> **Успішно змінено ліміт користувачів приватки на `{limit}`!**", ephemeral=True)
			await channel.edit(user_limit=limit)


	###
	### Кнопка
	###
	@commands.Cog.listener()
	async def on_button_click(self, inter: disnake.MessageInteraction):
		if not inter.component.custom_id.startswith("voice_"): return
		member = inter.author
		channel = self.check(inter.author)
		if not isinstance(channel, disnake.VoiceChannel):
			return await error(inter, channel)

		#Перейменувати
		if inter.component.custom_id == "voice_rename":
			#Затримка
			if str(inter.author.id) not in self.cooldown:
				self.cooldown[str(inter.author.id)] = {}
			if 'name' not in self.cooldown[str(inter.author.id)]:
				self.cooldown[str(inter.author.id)]['name'] = [0,0]
			if self.cooldown[str(inter.author.id)]['name'][0] > time():
				return await cooldown_notice(inter, self.cooldown[str(inter.author.id)]['name'][0])
			#Модал
			components = disnake.ui.TextInput(label="Назва", placeholder="Введіть назву вашого каналу тут", custom_id="name", min_length=2, max_length=20)
			modal = disnake.ui.Modal(title="Змінити назву приватки", custom_id="voice_name", components=components)
			await inter.response.send_modal(modal)

		#Ліміт
		elif inter.component.custom_id == "voice_limit":
			#Затримка
			if str(inter.author.id) not in self.cooldown:
				self.cooldown[str(inter.author.id)] = {}
			if 'limit' not in self.cooldown[str(inter.author.id)]:
				self.cooldown[str(inter.author.id)]['limit'] = 0
			if self.cooldown[str(inter.author.id)]['limit'] > time():
				return await cooldown_notice(inter, self.cooldown[str(inter.author.id)]['limit'])
			#Модал
			components = disnake.ui.TextInput(label="Ліміт", placeholder="Введіть обмеження на кількість користувачів", custom_id="limit", min_length=1, max_length=2)
			modal = disnake.ui.Modal(title="Змінити ліміт приватки", custom_id="voice_limit", components=components)
			await inter.response.send_modal(modal)

		#Закрити/Відкрити
		elif inter.component.custom_id == "voice_lock":
			#Затримка
			if str(inter.author.id) not in self.cooldown:
				self.cooldown[str(inter.author.id)] = {}
			if 'status' not in self.cooldown[str(inter.author.id)]:
				self.cooldown[str(inter.author.id)]['status'] = 0
			if self.cooldown[str(inter.author.id)]['status'] > time():
				return await cooldown_notice(inter, self.cooldown[str(inter.author.id)]['status'])
			overwrites = channel.overwrites
			#Відкриття войсу
			if not channel.overwrites[member.guild.default_role].connect:
				overwrites[member.guild.default_role] = get_voice_perms()
				await success(inter, "<:check:1127281505153069136> **Успішно відкрито приватку!**", ephemeral=True)
			#Закриття войсу
			else:
				voice_close = get_voice_perms()
				voice_close.send_messages = False
				voice_close.connect = False
				overwrites[member.guild.default_role] = voice_close
				await success(inter, "<:check:1127281505153069136> **Успішно закрито приватку!**", ephemeral=True)
			await channel.edit(overwrites=overwrites)
			self.cooldown[str(inter.author.id)]['status'] = curTime()+15

		#Передати овнерку
		elif inter.component.custom_id == "voice_transfer":
			self.cooldown[str(inter.author.id)]['members'] = time()+5
			dropdown = disnake.ui.UserSelect(custom_id="voice_transfer")
			await inter.send("**👑 Передати права на власність приваткою.**", components=[dropdown], ephemeral=True)

		#Дозволити/заборонити користувачу заходити
		elif inter.component.custom_id == "voice_member":
			dropdown = disnake.ui.UserSelect(custom_id="voice_member")
			if not channel.overwrites_for(inter.guild.default_role).connect:
				await inter.send("**🟢 Дозволити користувачу заходити в приватку.**", components=[dropdown], ephemeral=True)
			elif channel.overwrites_for(inter.guild.default_role).connect:
				await inter.send("**⛔ Заборонити користувачу заходити в приватку.**", components=[dropdown], ephemeral=True)

		#Зберегти
		elif inter.component.custom_id == "voice_save":
			#Затримка
			if str(inter.author.id) not in self.cooldown:
				self.cooldown[str(inter.author.id)] = {}
			if 'saveload' not in self.cooldown[str(inter.author.id)]:
				self.cooldown[str(inter.author.id)]['saveload'] = 0
			if self.cooldown[str(inter.author.id)]['saveload'] > time():
				return await cooldown_notice(inter, self.cooldown[str(inter.author.id)]['saveload'])
			self.cooldown[str(inter.author.id)]['saveload'] = time()+10
			overwrites = channel.overwrites

			#Учасники
			amembers, dmembers = [], []
			for m in overwrites:
				if m != member.guild.default_role and m.id not in (KATCAP, member.id):
					if overwrites[m].connect:
						amembers.append(m.id)
					elif not overwrites[m].connect:
						dmembers.append(m.id)
			#Закриття
			locked = bool(not overwrites[member.guild.default_role].connect)

			#БД
			update = {}
			update["name"] = channel.name
			update["limit"] = channel.user_limit
			update["allow_members"] = amembers
			update["deny_members"] = dmembers
			update["locked"] = locked
			voice_db.update(f"{member.id}", update)

			#Форматування учасників
			amembers_str, dmembers_str = "",""
			if amembers == []: amembers_str = "`Немає`"
			if dmembers == []: dmembers_str = "`Немає`"
			for m in amembers:
				amembers_str += f"{member.guild.get_member(m).mention} "
			for m in dmembers:
				dmembers_str += f"{member.guild.get_member(m).mention} "

			await inter.response.send_message((
				"<:check:1127281505153069136> **Успішно збережено налаштування приватки!**\n"
				f"> **Назва:** `{channel.name}`\n"
				f"> **Ліміт:** `{channel.user_limit}`\n"
				f"> **Закритий:** {BOOLSTATUS[locked]}\n"
				f"> **Дозволені користувачі:** {amembers_str}\n"
				f"> **Заборонені користувачі:** {dmembers_str}\n"
			), ephemeral=True)

		#Завантаження
		elif inter.component.custom_id == "voice_load":
			#Перевірка наявності в БД
			if str(inter.author.id) not in self.cooldown:
				self.cooldown[str(inter.author.id)] = {}
			if 'saveload' not in self.cooldown[str(inter.author.id)]:
				self.cooldown[str(inter.author.id)]['saveload'] = 0
			if 'name' not in self.cooldown[str(inter.author.id)]:
				self.cooldown[str(inter.author.id)]['name'] = [0,0]
			if self.cooldown[str(inter.author.id)]['saveload'] > time():
				return await cooldown_notice(inter, self.cooldown[str(inter.author.id)]['saveload'])
			#Затримка
			self.cooldown[str(inter.author.id)]['name'][1] += 1
			self.cooldown[str(inter.author.id)]['saveload'] = time()+10
			if self.cooldown[str(inter.author.id)]['name'][1] == 2:
				self.cooldown[str(inter.author.id)]['name'][1] = 0
				self.cooldown[str(inter.author.id)]['name'][0] = time()+600
			#БД
			overwrites = channel.overwrites
			voice = voice_db.full()
			if str(member.id) not in voice: return await error(inter, "<:cross:1127281507430576219> **У вас ще немає збережених налаштувань приватки!**")
			voice = voice[str(member.id)]

			#Закриття
			if voice["locked"]:
				voice_close = get_voice_perms()
				voice_close.send_messages = False
				voice_close.connect = False
				overwrites[member.guild.default_role] = voice_close
			overwrites[member] = voice_owner

			#Дозволені користувачі
			allow_members = ""
			if voice['allow_members'] != []:
				for m in voice["allow_members"]:
					mem = member.guild.get_member(m)
					if mem == None: continue
					overwrites[mem] = voice_member_allow
					allow_members += f"{mem.mention} "
			else:
				allow_members = "`Немає`"
			#Заборонені користувачі
			deny_members = ""
			if voice['deny_members'] != []:
				for m in voice["deny_members"]:
					mem = member.guild.get_member(m)
					if mem == None: continue
					overwrites[mem] = voice_member_block
					deny_members += f"{mem.mention} "
			else:
				deny_members = "`Немає`"

			await inter.send((
				"<:check:1127281505153069136> **Успішно завантажено налаштування приватки!**\n"
				f"> **Назва:** `{voice['name']}`\n"
				f"> **Ліміт:** `{voice['limit']}`\n"
				f"> **Закритий:** {BOOLSTATUS[voice['locked']]}\n"
				f"> **Дозволені користувачі:** {allow_members}\n"
				f"> **Заборонені користувачі:** {deny_members}\n"
			), ephemeral=True)
			#Затримка
			if self.cooldown[str(inter.author.id)]['name'][0] < time():
				await channel.edit(name=voice["name"], user_limit=voice["limit"], overwrites=overwrites)


	###
	### Селект меню
	###
	@commands.Cog.listener()
	async def on_dropdown(self, inter: disnake.MessageInteraction):
		if not inter.component.custom_id.startswith("voice_"): return
		member = inter.author
		channel = self.check(inter.author)
		if not isinstance(channel, disnake.VoiceChannel):
			return await error(inter, channel)
		###
		### Користувачі
		###
		if inter.component.custom_id == "voice_member":
			#Затримка
			if str(inter.author.id) not in self.cooldown:
				self.cooldown[str(inter.author.id)] = {}
			if 'members' not in self.cooldown[str(inter.author.id)]:
				self.cooldown[str(inter.author.id)]['members'] = 0
			if self.cooldown[str(inter.author.id)]['members'] > time():
				return await cooldown_notice(inter, self.cooldown[str(inter.author.id)]['members'])
			self.cooldown[str(inter.author.id)]['members'] = time()+5
			overwrites = channel.overwrites

			#Отримання користувача
			newmember = member.guild.get_member(int(inter.values[0]))
			if newmember not in member.guild.members:
				return await error(inter, "<:cross:1127281507430576219> **Користувача не знайдено!**", ephemeral=True)

			#Дозволити доступ
			if not channel.overwrites_for(inter.guild.default_role).connect:
				if newmember in overwrites:
					overwrites.pop(newmember)
					await success(inter, f"<:check:1127281505153069136> **Успішно прибрано користувача {newmember.mention} з приватки!**",ephemeral=True)
				else:
					overwrites[newmember] = voice_member_allow
					await success(inter, f"<:check:1127281505153069136> **Успішно дозволено заходити користувачу {newmember.mention} до приватки!**",ephemeral=True)
			#Заборонити доступ
			elif channel.overwrites_for(inter.guild.default_role).connect:
				if newmember in overwrites:
					overwrites.pop(newmember)
					await success(inter, f"<:check:1127281505153069136> **Успішно дозволено користувачу {newmember.mention} заходи до приватки!**",ephemeral=True)
				else:
					overwrites[newmember] = voice_member_block
					await success(inter, f"<:check:1127281505153069136> **Успішно заборонено користувачу {newmember.mention} заходити до приватки!**",ephemeral=True)
			await channel.edit(overwrites=overwrites)
		
		###
		### Передача овнерки
		###
		elif inter.component.custom_id == "voice_transfer":
			#Перевірки
			if str(inter.author.id) not in self.cooldown:
				self.cooldown[str(inter.author.id)] = {}
			if 'members' not in self.cooldown[str(inter.author.id)]:
				self.cooldown[str(inter.author.id)]['members'] = 0
			if self.cooldown[str(inter.author.id)]['members'] > time():
				return await cooldown_notice(inter, self.cooldown[str(inter.author.id)]['members'])
			channel = self.check(inter.author)
			if not isinstance(channel, disnake.VoiceChannel):
				return await error(inter, channel)

			#Отримання нового власника каналу
			newowner = inter.guild.get_member(int(inter.values[0]))
			if not newowner:
				return await error(inter, "<:cross:1127281507430576219> **Користувача не знайдено!**")

			#Права каналу
			overwrites = channel.overwrites
			overwrites.pop(inter.author)
			overwrites[newowner] = voice_owner
			#Відповідь
			self.cooldown[str(inter.author.id)]['members'] = time()+5
			await success(inter, f"<:check:1127281505153069136> **Успішно передано права на приватку користувачу {newowner.mention}!**", ephemeral=True)
			await channel.edit(overwrites=overwrites)


	@commands.Cog.listener()
	async def on_voice_state_update(self, member:disnake.Member, before:disnake.VoiceState, after:disnake.VoiceState):
		if member.guild.id != GUILD_ID: return
		guild = member.guild
		#Видалення приватки
		if before.channel:
			if len(before.channel.members) < 1 and before.channel.id != VOICE_CREATE_ID:
				if before.channel.category_id == VOICE_CATEGORY_ID:
					try: await before.channel.delete()
					except: pass
		#Створення приватки
		if not after.channel: return
		if after.channel.id == VOICE_CREATE_ID:
			#Створення каналу
			overwrites = {
				guild.default_role: get_voice_perms(),
				member: voice_owner,
				guild.get_role(STAFF_ID): disnake.PermissionOverwrite(deafen_members=True, mute_members=True),
				guild.get_role(KATCAP): disnake.PermissionOverwrite(read_messages=False)
			}
			category = self.bot.get_channel(VOICE_CATEGORY_ID)
			channel = await guild.create_voice_channel(member.display_name, overwrites=overwrites, category=category)
			try: await member.move_to(channel)
			except: return await channel.delete()

			#Затримка
			self.cooldown[str(member.id)] = {}
			self.cooldown[str(member.id)]['name'] = [0,0]
			self.cooldown[str(member.id)]['limit'] = 0
			self.cooldown[str(member.id)]['status'] = 0
			self.cooldown[str(member.id)]['members'] = 0
			self.cooldown[str(member.id)]['saveload'] = 0


def setup(bot:commands.Bot):
	bot.add_cog(Voice(bot))