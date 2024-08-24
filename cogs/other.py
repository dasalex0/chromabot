from cogs.level import Level
from utils import *


class Other(commands.Cog):
	def __init__(self, bot:commands.Bot):
		self.bot = bot


	###
	### Розіграші (таск)
	###
	@tasks.loop(seconds=15)
	async def giveaways(self):
		giveaways = giveaways_db.full()
		if list(giveaways) != []:
			guild = self.bot.get_guild(GUILD_ID)
			for msg in list(giveaways):
				#Отримання інформації
				giv = giveaways[msg]
				if not giv['time'] <= curTime() or giv['ended'] == True: continue
				channel = self.bot.get_channel(int(giv['channel']))
				prize = giv['prize']
				message = await channel.fetch_message(int(msg))

				#Користувачі
				users = await message.reactions[0].users().flatten()
				users.pop(users.index(self.bot.user))

				#Переможці
				winners = ""
				if giv['winners'] > 1:
					for _ in range(giv['winners']):
						winner = random.choice(users)
						users.pop(users.index(winner))
						winners += f"{winner.mention} "
				else:
					winner = random.choice(users)
					winners += f"{winner.mention}"
				if giv['winners'] <= 1:
					await channel.send(f"🎉 Вітаємо, {winners}, ви виграли приз: **{prize}**!")
					t = "Переможець"
				else:
					await channel.send(f"🎉 Вітаємо, {winners} ви виграли приз: **{prize}**!")
					t = "Переможці"

				#Embed
				emb = disnake.Embed(description=message.embeds[0].description, color=EMBEDCOLOR)
				emb.add_field(name=t, value=winners)
				emb.set_thumbnail(url=guild.icon)
				emb.set_footer(text="Розіграш закінчено!")
				await message.edit("**РОЗІГРАШ ЗАКІНЧЕНО! 🎉**", embed=emb)
				#БД
				giv["ended"] = True
				giveaways_db.update(msg, giv)

	@commands.Cog.listener()
	async def on_ready(self):
		if not self.giveaways.is_running():
			self.giveaways.start()


	###
	### Розіграші
	###
	@commands.slash_command(name="giveaway", description="👑 Почати розіграш.", guild_ids=[GUILD_ID])
	@commands.cooldown(1, 2, commands.BucketType.user)
	async def giveaway(self, inter:disnake.CommandInter, channel:disnake.TextChannel|disnake.NewsChannel=commands.Param(description="В якому каналі буде розіграш?"), duration:str=commands.Param(description="Скільки буде йти розіграш? (s|m|h|d)"), winners:int=commands.Param(description="Скільки людей зможуть виграти в розіграші?"), prize:str=commands.Param(description="Який приз буде розігруватись?")):
		if inter.author.id != ALEX: return
		gtime = convert_time(duration)
		if gtime == -1: return await inter.send(f"❌ **Ви не відповіли правильною одиницею! Використовуйте (s|m|h|d) наступного разу.**", ephemeral=True)
		elif gtime == -2: return await inter.send(f"❌ **Час має бути цілим числом! Наступного разу введіть ціле число.**", ephemeral=True)

		await inter.send(f"Розіграш надіслано в {channel.mention} і закінчиться <t:{curTime()+gtime}:R> (<t:{curTime()+gtime}:R>)", ephemeral=True)

		emb = disnake.Embed(description=f"**{prize}**", color=EMBEDCOLOR)
		emb.add_field(name="Закінчиться", value=f"<t:{curTime()+gtime}:R>")
		emb.add_field(name="Переможців", value=f"` {winners} `")
		emb.set_thumbnail(url=inter.guild.icon)
		emb.set_footer(text=f"Натисніть на реакцію 🎉, щоб прийняти участь.")
		msg = await channel.send("**РОЗІГРАШ 🎉**",embed=emb)
		await msg.add_reaction("🎉")

		update = {}
		update["ended"] = False
		update["channel"] = int(channel.id)
		update["time"] = curTime()+gtime
		update["winners"] = int(winners)
		update["prize"] = str(prize)
		giveaways_db.update(str(msg.id), update)

	@commands.message_command(name="Перезапустити розіграш", guild_ids=[GUILD_ID])
	async def reroll(self, inter:disnake.MessageCommandInteraction):
		if inter.author.id != ALEX: return
		message = inter.target
		giveaways = giveaways_db.full()
		if str(message.id) not in giveaways:
			return await error(inter, "<:cross:1127281507430576219> **Вказаного опитування не існує!**")

		#Користувачі
		users = await message.reactions[0].users().flatten()
		users.pop(users.index(self.bot.user))

		#Переможці
		winners = ""
		winnersc = giveaways[str(message.id)]["winners"]
		if winnersc > 1:
			t = "Переможці"
			for _ in range(winnersc):
				winner = random.choice(users)
				users.pop(users.index(winner))
				winners += f"{winner.mention} "
		else:
			t = "Переможець"
			winner = random.choice(users)
			winners += f"{winner.mention}"

		#Відповідь
		await inter.send(f"✅ Розіграш перезапущено!", ephemeral=True)
		await message.channel.send(f"🔄 Розіграш перезапущено. Новий переможець: {winners}")
		#Embed
		emb = disnake.Embed(description=message.embeds[0].description, color=EMBEDCOLOR)
		emb.add_field(name=t, value=f"{winners}")
		emb.set_thumbnail(url=inter.guild.icon)
		emb.set_footer(text="Розіграш закінчено!")
		await message.edit("**РОЗІГРАШ (рерол) 🎉**", embed=emb)
		giveaways_db.update(f'{id}.ended', True)



	###
	### Таблиця лідерів
	###
	@commands.Cog.listener("on_button_click")
	async def on_top_button(self, inter:disnake.MessageInteraction):
		if inter.component.custom_id.startswith("top:"):
			custom_id = inter.component.custom_id.split(':')
			type = custom_id[1]
			author_id = inter.message.interaction.author.id
			if inter.author.id != author_id:
				return await error(inter, "<:cross:1127281507430576219> **Ви не автор повідомлення!**")
			page = int(inter.message.embeds[0].footer.text.replace("Сторінка: ","").split("/")[0])
			if custom_id[2] == "prev": page -= 1
			elif custom_id[2] == "next": page += 1
			await self.top_func(inter, type, page, edit=True)

	@commands.slash_command(name="top", description="📋 Таблиця лідерів.", guild_ids=[GUILD_ID])
	@commands.cooldown(1, 2, commands.BucketType.user)
	async def top(self, inter:disnake.CommandInter, тип:str=commands.Param(description="Тип таблиці", choices=[
		OptionChoice("🚀 Рівень", "level"),
		OptionChoice("🎤 Войс", "voice"),
		OptionChoice("💸 Гроші", "money"),
		OptionChoice("🐖 Свині", "pig"),
		OptionChoice("📨 Запрошення", "invites")
	])):
		if inter.locale == disnake.Locale.ru:
			return await error(inter, "<:cross:1127281507430576219> **При ініціалізації мови сталася помилка!**")
		await self.top_func(inter, тип, 1)

	async def top_func(self, inter:disnake.CommandInter, type:str, page:int, edit:bool=False):
		#БД
		register(inter.author)
		level = level_db.full()
		eco = eco_db.full()
		pig = pigs_db.full()
		invdb = invites_db.full()
		#Embed
		emb = disnake.Embed(title="Таблиця лідерів", color=EMBEDCOLOR)
		emb.set_thumbnail(url=inter.guild.icon)

		#Рівень
		toppos = 0
		if type == "level":
			sorted_top = sorted(level, key=lambda k: -(Level.get_full_level(int(k))*50000 + level[k]["xp"]))
			for k in sorted_top:
				t = level[k]['type']
				toppos += 1
				owner = inter.guild.get_member(int(k))
				if not owner or (level[k]["type"] == 'bronze' and level[k]["xp"] <= 50):
					toppos -= 1;continue
				if toppos > page*10-10 and toppos <= page*10:
					voicemsg = ""
					if level[k]["voice"] >= 15:
						voicemsg = f" | **`{voicelevel(level[k]['voice'])}` 🎤**"
					emb.add_field(name=f"{set_rank(toppos)}#{toppos}. {owner.display_name}", value=f"**Рівень:** `{LEVELS[t]['name']} {str(level[k]['level'])}` | **XP:** `{level[k]['xp']}`{voicemsg}", inline=False)

		#Голосова активність
		elif type == "voice":
			sorted_top = sorted(level, key=lambda k: -level[k]["voice"])
			for k in sorted_top:
				toppos += 1
				owner = inter.guild.get_member(int(k))
				if not owner or level[k]["voice"] < 60:
					toppos -= 1;continue
				if toppos > page*10-10 and toppos <= page*10:
					voiceactive = voicelevel(level[k]['voice'])
					emb.add_field(name=f"{set_rank(toppos)}#{toppos}. {owner.display_name}", value=f"**`{voiceactive}` 🎤**", inline=False)

		#Гроші
		elif type == "money":
			sorted_top = {}
			for m in eco:
				money = eco[m]['money']
				if m in pig:
					money += pig[m]['balance']
				sorted_top[m] = money
			sorted_top = sorted(sorted_top, key=lambda k: -sorted_top[k])
			for k in sorted_top:
				toppos += 1
				owner = inter.guild.get_member(int(k))
				if not owner or eco[k]["money"] == 0:
					toppos -= 1;continue
				if toppos > page*10-10 and toppos <= page*10:
					money = eco[k]['money']
					pig_money = 0
					if k in pig:
						pig_money = pig[k]['balance']
					emb.add_field(name=f"{set_rank(toppos)}#{toppos}. {owner.display_name}", value=f"**Гроші: `{hf(money+pig_money)}`{CURRENCY}**", inline=False)

		#Свині
		elif type == "pig":
			sorted_top = sorted(pig, key=lambda k: -(pig[k]["mass"]+pig[k]["power"]*3))
			for k in sorted_top:
				toppos += 1
				owner = inter.guild.get_member(int(k))
				if not owner: toppos -= 1;continue
				if toppos > page*10-10 and toppos <= page*10:
					emb.add_field(name=f"{set_rank(toppos)}#{toppos}. {pig[k]['name']}", value=f"**Статистика: `{round(pig[k]['mass'], 2)} кг.` | `{pig[k]['power']}`💪\nВласник: {owner.mention}**", inline=False)

		#Запрошення
		elif type == "invites":
			sorted_top = sorted(invdb, key=lambda k: -(len(invdb[k]['join']) - len(invdb[k]['leave'])))
			emb.description = "📊 - Реальні інвайти (ті, хто залишились на сервері)\n✅ - Приєдналися\n❌ - Покинули сервер"
			for k in sorted_top:
				toppos += 1
				total = (len(invdb[k]['join']) - len(invdb[k]['leave']))
				owner = inter.guild.get_member(int(k))
				if not owner or total <= 0:
					toppos -= 1;continue
				if toppos > page*10-10 and toppos <= page*10:
					emb.add_field(name=f"{set_rank(toppos)}#{toppos}. {owner.display_name}",value=f"**📊 `{total}` | ✅ `{len(invdb[k]['join'])}` | ❌ `{len(invdb[k]['leave'])}`**", inline=False)

		#Сторінки
		final_page = int(toppos/10)
		if toppos % 10 != 0:
			final_page += 1
		emb.set_footer(text=f"Сторінка: {page}/{final_page}")

		#Відправка
		prev = disnake.ui.Button(emoji="<:1_:1074946080858460201>", custom_id=f"top:{type}:prev", disabled=bool(page <= 1))
		next = disnake.ui.Button(emoji="<:2_:1074946078618685520>", custom_id=f"top:{type}:next", disabled=bool(page >= final_page))
		if edit:
			return await inter.response.edit_message(embed=emb, components=[prev,next])
		await inter.send(embed=emb, components=[prev,next])


	###
	### Аватар
	###
	@commands.slash_command(name="avatar", description="📋 Подивитися аватар учасника.", guild_ids=[GUILD_ID])
	@commands.cooldown(1, 2, commands.BucketType.user)
	async def avatar(self, inter:disnake.CommandInter, учасник:disnake.Member=None):
		member = учасник
		if not member: member = inter.author
		avatar = member.display_avatar
		#Кнопки
		components = []
		components.append(disnake.ui.Button(label="PNG", url=f"{avatar.with_format('png').with_size(1024)}"))
		components.append(disnake.ui.Button(label="JPEG", url=f"{avatar.with_format('jpg').with_size(1024)}"))
		components.append(disnake.ui.Button(label="WEBP", url=f"{avatar.with_format('webp').with_size(1024)}"))
		if avatar._animated:
			components.append(disnake.ui.Button(label="GIF", url=f"{avatar.with_format('gif').with_size(1024)}"))
		#Embed
		emb = disnake.Embed(title=f"Аватар користувача @{member}", color=EMBEDCOLOR)
		emb.set_image(url=avatar.with_size(512))
		await inter.send(embed=emb, components=components)


def setup(bot:commands.Bot):
	bot.add_cog(Other(bot))