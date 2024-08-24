from utils import *


class Logs(commands.Cog):
	def __init__(self, bot:commands.Bot):
		self.bot = bot

	#Повідомлення видалено
	@commands.Cog.listener()
	async def on_message_delete(self, message:disnake.Message):
		if not message.guild: return
		if message.guild.id != GUILD_ID: return
		if message.author.bot: return
		if message.channel.id in LOGS_IGNORE or message.channel.category_id in LOGS_IGNORE: return

		content = message.content.replace('`', '')
		if len(content) > 1000: content = f"{content[:1000]} ..."
		#Стікери
		if len(content) < 1 and len(message.stickers) > 0:
			content += f"[Sticker]\nName: {message.stickers[0].name} | ID: {message.stickers[0].id}\n\n"
		#Файли
		if len(content) < 1 and len(message.attachments) > 0:
			attach = 0
			for _ in message.attachments:
				attach += 1
				content += f"[File {attach}]\n{str(message.attachments[attach - 1].url)}\n\n"
		#Відсутнє
		if len(content) <= 0 and len(message.stickers) <= 0 and len(message.attachments) <= 0:
			content = 'Відсутнє'

		moderator = None
		async for entry in message.guild.audit_logs(action=disnake.AuditLogAction.message_delete, limit=1, after=datetime.fromtimestamp(time()-2)):
			moderator = entry.user
			break

		#Лог
		async with ClientSession() as session:
			webhook = Webhook.from_url(LOG_WEBHOOK, session=session)
			emb = disnake.Embed(description='Повідомлення було видалене', color=LOG_RED, timestamp=datetime.now())
			emb.set_thumbnail(url=message.author.display_avatar)
			if len(message.attachments) > 0:
				emb.set_image(url=str(message.attachments[0].url))
			emb.add_field(name='Видалене повідомлення', value=f"```{content}```", inline=False)
			emb.add_field(name='Автор', value=f"{message.author.mention} (**{message.author.display_name}**)")
			emb.add_field(name='Канал', value=f"<#{message.channel.id}> (**{message.channel}**)")
			if moderator != None and moderator != message.author:
				emb.add_field(name='Модератор', value=f"<@{moderator.id}> (**{moderator.display_name}**)")
			emb.set_footer(text=f"ID користувача: {message.author.id}")
			await webhook.send(embed=emb)


	#Повідомлення відредаговано
	@commands.Cog.listener()
	async def on_message_edit(self, before:disnake.Message, after:disnake.Message):
		if not after.guild: return
		if after.guild.id != GUILD_ID: return
		if after.author.bot: return
		if after.channel.id in LOGS_IGNORE or after.channel.category_id in LOGS_IGNORE: return

		beforecontent, aftercontent = before.content.replace('`', ''), after.content.replace('`', '')
		if aftercontent == beforecontent: return

		if len(beforecontent) > 1000: beforecontent = f"{beforecontent[:1000]} ..."
		else:
			if len(beforecontent) <= 0: beforecontent = 'Відсутнє'

		if len(aftercontent) > 1000: aftercontent = f"{aftercontent[:1000]} ..."
		else:
			if len(after.content) <= 0: aftercontent = 'Відсутнє'

		async with ClientSession() as session:
			webhook = Webhook.from_url(LOG_WEBHOOK, session=session)
			emb = disnake.Embed(description=f'[Повідомлення]({after.jump_url}) було відредаговано', color=LOG_BLUE, timestamp=datetime.now())
			emb.set_thumbnail(url=after.author.display_avatar)
			emb.add_field(name='Старий зміст', value=f"```{beforecontent}```",inline=False)
			emb.add_field(name='Новий зміст', value=f"```{aftercontent}```",inline=False)
			emb.add_field(name='Автор', value=f"{after.author.mention} (**{after.author.display_name}**)")
			emb.add_field(name='Канал', value=f"{after.channel.mention} (**{after.channel}**)")
			emb.set_footer(text=f"ID користувача {after.author.id}")
			await webhook.send(embed=emb)


	#Приєднався
	@commands.Cog.listener()
	async def on_member_join(self, member:disnake.Member):
		if member.guild.id != GUILD_ID: return
		async with ClientSession() as session:
			webhook = Webhook.from_url(LOG_WEBHOOK, session=session)
			emb = disnake.Embed(description=f"Приєднався новий користувач {member.mention} (**{member.display_name}**)", color=LOG_GREEN, timestamp=datetime.now())
			emb.add_field(name='Дата реєстрації', value=f"<t:{str(int(member.created_at.timestamp()))}:D> (<t:{str(int(member.created_at.timestamp()))}:R>)",inline=False)
			emb.set_thumbnail(url=member.display_avatar)
			emb.set_footer(text=f"ID користувача: {member.id}")
			await webhook.send(embed=emb)


	#Покинув сервер
	@commands.Cog.listener("on_member_remove")
	async def on_member_leave(self, member:disnake.Member):
		if member.guild.id != GUILD_ID: return
		roles = ""
		for role in member.roles:
			if role.id != member.guild.id:
				roles += f"{role.mention}\n"
		async with ClientSession() as session:
			webhook = Webhook.from_url(LOG_WEBHOOK, session=session)
			emb = disnake.Embed(description=f"Користувач покинув сервер {member.mention} (**{member.display_name}**)", color=LOG_RED, timestamp=datetime.now())
			emb.add_field(name="Приєднався на севрер", value=f"<t:{str(int(member.joined_at.timestamp()))}:D> (<t:{str(int(member.joined_at.timestamp()))}:R>)",inline=False)
			if len(roles) != 0: emb.add_field(name="Ролі", value=roles, inline=False)
			emb.set_thumbnail(url=member.display_avatar)
			emb.set_footer(text=f"ID користувача: {member.id}")
			await webhook.send(embed=emb)


	#Бан
	@commands.Cog.listener()
	async def on_member_ban(self, guild:disnake.Guild, member:disnake.User):
		if guild.id != GUILD_ID: return
		reason, moderator = None, None
		async for entry in guild.audit_logs(action=disnake.AuditLogAction.ban, limit=1, after=datetime.fromtimestamp(time()-2)):
			reason, moderator = entry.reason, entry.user
			break

		if reason == None: reason = "Не встановлена"
		async with ClientSession() as session:
			webhook = Webhook.from_url(LOG_WEBHOOK, session=session)
			emb = disnake.Embed(description=f"Користувача {member.mention} (**{member.display_name}**) було заблоковано!", color=LOG_RED, timestamp=datetime.now())
			emb.set_thumbnail(url=member.display_avatar)
			if moderator != None: emb.add_field(name="Модератор", value=f"<@{moderator.id}> (**{moderator.display_name}**)")
			emb.add_field(name="Причина", value=reason)
			emb.set_footer(text=f"ID користувача: {member.id}")
			await webhook.send(embed=emb)


	#Розбан
	@commands.Cog.listener()
	async def on_member_unban(self, guild:disnake.Guild, member:disnake.User):
		if guild.id != GUILD_ID: return
		async for entry in guild.audit_logs(action=disnake.AuditLogAction.unban, limit=1, after=datetime.fromtimestamp(time()-2)):
			moderator = entry.user
			break

		async with ClientSession() as session:
			webhook = Webhook.from_url(LOG_WEBHOOK, session=session)
			emb = disnake.Embed(description=f"Користувача {member.mention} (**{member.display_name}**) було розблоковано", color=LOG_GREEN, timestamp=datetime.now())
			emb.set_thumbnail(url=member.display_avatar)
			emb.add_field(name="Модератор", value=f"<@{moderator.id}> (**{moderator.display_name}**)")
			emb.set_footer(text=f"ID користувача: {member.id}")
			await webhook.send(embed=emb)


	#Кік
	@commands.Cog.listener("on_member_remove")
	async def on_member_kick(self, member:disnake.Member):
		if member.guild.id != GUILD_ID: return
		moderator, target, reason = None, None, None
		async for entry in member.guild.audit_logs(action=disnake.AuditLogAction.kick, limit=1, after=datetime.fromtimestamp(time()-2)):
			moderator, target, reason = entry.user, entry.target, entry.reason
			break

		if moderator == None or target == None: return
		if target.id != member.id: return
		if reason == None: reason = 'Не встановлена'
		async with ClientSession() as session:
			webhook = Webhook.from_url(LOG_WEBHOOK, session=session)
			emb = disnake.Embed(description=f"Користувача {member.mention} (**{member.display_name}**) було вигнано з серверу", color=LOG_RED, timestamp=datetime.now())
			emb.set_thumbnail(url=member.display_avatar)
			emb.add_field(name="Модератор", value=f"<@{moderator.id}> (**{moderator.display_name}**)")
			emb.add_field(name="Причина", value=reason)
			emb.set_footer(text=f"ID користувача: {member.id}")
			await webhook.send(embed=emb)


	#Зміна ніку
	@commands.Cog.listener("on_member_update")
	async def on_member_nickname(self, before:disnake.Member, after:disnake.Member):
		if after.guild.id != GUILD_ID: return
		if after.nick != before.nick:
			moderator = None
			async for entry in after.guild.audit_logs(action=disnake.AuditLogAction.member_update, limit=1, after=datetime.fromtimestamp(time()-2)):
				moderator = entry.user
				break

			async with ClientSession() as session:
				webhook = Webhook.from_url(LOG_WEBHOOK, session=session)
				emb = disnake.Embed(description=f"Нік користувача {after.mention} (**{after.display_name}**) було змінено", color=LOG_BLUE, timestamp=datetime.now())
				emb.set_thumbnail(url=after.display_avatar)
				emb.add_field(name="Старий нік", value=before.display_name)
				emb.add_field(name="Новий нік", value=after.display_name)
				if moderator != None and moderator != after: emb.add_field(name="Модератор", value=f"<@{moderator.id}> (**{moderator.display_name}**)", inline=False)
				emb.set_footer(text=f"ID користувача: {after.id}")
				await webhook.send(embed=emb)


	#Зміна ролей
	@commands.Cog.listener("on_member_update")
	async def on_member_roles(self, before:disnake.Member, after:disnake.Member):
		if after.guild.id != GUILD_ID: return
		if after.roles != before.roles:
			roles = []
			for role in after.roles:
				if role not in before.roles:
					if "everyone" not in role.name: roles.append(role)
			if len(roles) < 1:
				type = 1
				for role in before.roles:
					if role not in after.roles:
						roles.append(role)
			else: type = 0

			moderator = None
			async for entry in after.guild.audit_logs(action=disnake.AuditLogAction.member_role_update, limit=1, after=datetime.fromtimestamp(time()-2)):
				moderator = entry.user
				break

			name = {0: "Додано ролі", 1: "Прибрано ролі"}
			r = ""
			for role in roles: r += f"{role.mention}\n"

			async with ClientSession() as session:
				webhook = Webhook.from_url(LOG_WEBHOOK, session=session)
				emb = disnake.Embed(description=f"Ролі користувача {after.mention} (**{after.display_name}**) було змінено", color=LOG_BLUE, timestamp=datetime.now())
				emb.set_thumbnail(url=after.display_avatar)
				emb.add_field(name=f"{name[type]}",value=r)
				if moderator != None and moderator != after: emb.add_field(name="Модератор", value=f"<@{moderator.id}> (**{moderator.display_name}**)",inline=False)
				emb.set_footer(text=f"ID користувачів {after.id}")
				await webhook.send(embed=emb)


	#Войс
	@commands.Cog.listener()
	async def on_voice_state_update(self, member:disnake.Member, before:disnake.VoiceState, after:disnake.VoiceState):
		if member.guild.id != GUILD_ID: return
		if after.channel == before.channel: return
		if member.bot: return

		async with ClientSession() as session:
			if before.channel == None:
				webhook =  Webhook.from_url(LOG_WEBHOOK, session=session)
				emb = disnake.Embed(description=f"Користувач {member.mention} (**{member.display_name}**) зайшов у <#{after.channel.id}> (**{after.channel.name}**)", color=LOG_GREEN, timestamp=datetime.now())
				emb.set_thumbnail(url=member.display_avatar)
				emb.set_footer(text=f"ID користувача {member.id}")
				await webhook.send(embed=emb)

			elif after.channel == None:
				webhook = Webhook.from_url(LOG_WEBHOOK, session=session)
				emb = disnake.Embed(description=f"Користувач {member.mention} (**{member.display_name}**) покинув <#{before.channel.id}> (**{before.channel.name}**)", color=LOG_RED, timestamp=datetime.now())
				emb.set_thumbnail(url=member.display_avatar)
				emb.set_footer(text=f"ID користувача: {member.id}")
				await webhook.send(embed=emb)

			elif before.channel != None and after.channel != None:
				webhook =  Webhook.from_url(LOG_WEBHOOK, session=session)
				emb = disnake.Embed(description=f"Користувач {member.mention} (**{member.display_name}**) перейшов у інший голосовий канал", color=LOG_BLUE, timestamp=datetime.now())
				emb.set_thumbnail(url=member.display_avatar)
				emb.add_field(name="Старий канал", value=f"<#{before.channel.id}> (**{before.channel.name}**)")
				emb.add_field(name="Новий канал", value=f"<#{after.channel.id}> (**{after.channel.name}**)")
				emb.set_footer(text=f"ID користувача: {member.id}")
				await webhook.send(embed=emb)


	#Гілку створено
	@commands.Cog.listener()
	async def on_thread_create(self, thread: disnake.Thread):
		owner = self.bot.get_user(thread.owner_id)
		if owner == None: return
		channel = self.bot.get_channel(thread.parent_id)
		if channel == None: return
		if channel.guild.id != GUILD_ID: return

		async with ClientSession() as session:
			webhook = Webhook.from_url(LOG_WEBHOOK, session=session)
			emb = disnake.Embed(description="Нову гілку було створено", color=LOG_GREEN, timestamp=datetime.now())
			emb.add_field(name="Почав", value=f"{owner.mention} (**{owner.display_name}**)")
			emb.add_field(name="Канал", value=f"<#{channel.id}> (**{channel.name}**)")
			emb.add_field(name="Гілка", value=f"<#{thread.id}> (**{thread.name}**)")
			emb.set_footer(text=f"ID автора {owner.id}")
			await webhook.send(embed=emb)


	#Гілку видалено
	@commands.Cog.listener()
	async def on_thread_delete(self, thread: disnake.Thread):
		owner = self.bot.get_user(thread.owner_id)
		if owner == None: return
		channel = self.bot.get_channel(thread.parent_id)
		if channel == None: return
		if channel.guild.id != GUILD_ID: return

		async for entry in channel.guild.audit_logs(action=disnake.AuditLogAction.thread_delete, limit=1, after=datetime.fromtimestamp(time()-2)):
			moderator = entry.user
			break

		async with ClientSession() as session:
			webhook = Webhook.from_url(LOG_WEBHOOK, session=session)
			emb = disnake.Embed(description=f"Гілку **{thread.name}** було видалено", color=LOG_RED, timestamp=datetime.now())
			emb.add_field(name="Автор", value=f"{owner.mention} (**{owner.display_name}**)")
			emb.add_field(name="Канал", value=f"<#{channel.id}> (**{channel.name}**)")
			emb.add_field(name="Модератор", value=f"<@{moderator.id}> (**{moderator.display_name}**)", inline=False)
			emb.set_footer(text=f"ID автора: {owner.id}")
			await webhook.send(embed=emb)


	#Інвайт створено
	@commands.Cog.listener()
	async def on_invite_create(self, invite:disnake.Invite):
		if invite.guild.id != GUILD_ID: return
		inviter = invite.guild.get_member(invite.inviter.id)
		if not inviter: return

		async with ClientSession() as session:
			webhook = Webhook.from_url(LOG_WEBHOOK, session=session)
			emb = disnake.Embed(description=f"Нове запрошення з кодом **{invite.code}** було створено", color=LOG_GREEN, timestamp=datetime.now())
			emb.set_thumbnail(url=inviter.display_avatar)
			emb.add_field(name="Автор", value=f"{inviter.mention} (**{inviter.display_name}**)")
			emb.add_field(name="Канал", value=f"<#{invite.channel.id}> (**{invite.channel.name}**)")
			emb.set_footer(text=f"ID користувача: {invite.inviter.id}")
			await webhook.send(embed=emb)


def setup(bot:commands.Bot):
	bot.add_cog(Logs(bot))