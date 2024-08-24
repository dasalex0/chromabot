from utils import *


class InviteLogger(commands.Cog):
	def __init__(self, bot:commands.Bot):
		self.bot = bot
		self.invites_list = {}


	@tasks.loop(seconds=12)
	async def checkinvite(self):
		try: self.invites_list = await self.bot.get_guild(GUILD_ID).invites()
		except: pass

	@commands.Cog.listener()
	async def on_ready(self):
		if not self.checkinvite.is_running():
			self.checkinvite.start()

	@commands.Cog.listener()
	async def on_invite_create(self, invite):
		try: self.invites_list = await self.bot.get_guild(GUILD_ID).invites()
		except: pass


	def get_code(self, invite_list:list[disnake.Invite], code:str):
		for inv in invite_list:
			if inv.code == code:
				return inv


	@commands.slash_command(name="invites", description="📋 Подивитися свою кількість запрошень.", guild_ids=[GUILD_ID])
	@commands.cooldown(1, 2, commands.BucketType.user)
	async def invites(self, inter:disnake.CommandInter, учасник:disnake.Member=None):
		if inter.locale == disnake.Locale.ru:
			return await error(inter, "<:cross:1127281507430576219> **При ініціалізації мови сталася помилка!**")
		member = учасник
		if member == None: member = inter.author
		invdb = invites_db.full()
		member_joins, member_leaves, last, emoji = [], [], "", "<:chr_smileHz:1139909888596783195>"
		total = 0
		#Отримання інвайтів
		if str(member.id) in invdb:
			member_joins = list(invdb[str(member.id)]['join'])
			member_leaves = list(invdb[str(member.id)]['leave'])

		#Запрошення
		if len(member_joins) > 0 or len(member_leaves) > 0:
			total = len(member_joins) - len(member_leaves)
			#Останні запрошені
			member_joins.reverse()
			index = 0
			for member_id in member_joins:
				if index > 5: break
				if member_id in member_leaves: continue
				last += f"<@{member_id}> "
				index += 1

		#Іконки для запрошень
		emojies = {
			70: '🤯', 50: '💪', 35: '<:chr_catHPizdec:1161289664582385774>👍', 20: '<:chr_otherSigma:1130429248889421844>',
			10: '<:chr_memeLike:1207661822103265280>', 5: '<:chr_catELike:1161290345296969761>', 1: '👍'
		}
		for i in emojies:
			if total >= i:
				emoji = emojies[i]
				break

		#Embed
		emb = disnake.Embed(description=(
			f"**Кількість запрошень:**\n"
			f"> ✅ **{len(member_joins)}** приєдналися\n"
			f"> ❌ **{len(member_leaves)}** покинули сервер\n\n"
			f"> Ви запросили **{total}** людей! {emoji}"
		),color=EMBEDCOLOR, timestamp=inter.created_at)
		emb.set_author(name=f"@{member}", icon_url=member.display_avatar)
		emb.set_thumbnail(url=member.display_avatar)
		if total > 0: emb.add_field(name=f"Список останніх запрошених людей:", value=f"> {last}")
		await inter.send(embed=emb)


	@commands.Cog.listener()
	async def on_member_join(self, member: disnake.Member):
		if member.guild.id != GUILD_ID: return
		invdb = invites_db.full()
		IBJ = self.invites_list
		try: self.invites_list = await member.guild.invites()
		except: pass
		if curTime() - member.created_at.timestamp() < YOUNG_TIME: return

		channel = self.bot.get_channel(INVITES_CHANNEL)
		#Перебирання посилань
		for invite in IBJ:
			if not invite.uses < self.get_code(self.invites_list, invite.code).uses: continue
			inviter = int(invite.inviter.id)

			#База даних
			if str(inviter) not in invdb:
				new_invite = {"join": {}, "leave": []}
			else:
				new_invite = invdb[str(inviter)]
			if str(member.id) not in new_invite['join']:
				new_invite['join'][member.id] = invite.code
			if str(member.id) in list(new_invite['join']) and str(member.id) in list(new_invite['leave']):
				new_invite['join'].pop(str(member.id))
				new_invite['leave'].remove(str(member.id))
				new_invite['join'][str(member.id)] = invite.code
			invites_db.update(f'{inviter}', new_invite)
			
			#Отримання кількості
			invdb = invites_db.full()
			member_joins = list(invdb[str(inviter)]['join'])
			member_leaves = list(invdb[str(inviter)]['leave'])
			total = len(member_joins) - len(member_leaves)
			if total < 0: total = 0
			return await channel.send(f"💚 {member.mention} приєднався. Його запросив <@{inviter}>, тепер запрошення має **{total}** використань. (Код запрошення: `{invite.code}`)\nВін **{len(member.guild.members)}**-ий учасник серверу\nЗареєструвався: <t:{int(member.created_at.timestamp())}:R>")
		
		await channel.send(f"💚 {member.mention} зайшов через невідоме запрошення.\nВін **{len(member.guild.members)}**-ий учасник серверу\nЗареєструвався: <t:{int(member.created_at.timestamp())}:R>")


	@commands.Cog.listener()
	async def on_member_remove(self, member: disnake.Member):
		if member.guild.id != GUILD_ID: return
		invdb = invites_db.full()
		self.invites_list = await member.guild.invites()
		#База даних
		if curTime() - member.created_at.timestamp() < YOUNG_TIME: return
		for m in invdb:
			if str(member.id) not in list(invdb[m]['leave']) and str(member.id) in list(invdb[m]['join']):
				invdb[m]['leave'].append(str(member.id))
				invites_db.update(f"{m}", invdb[m])
				break

		#Отримання кількості
		invdb = invites_db.full()
		member_joins = list(invdb[m]['join'])
		member_leaves = list(invdb[m]['leave'])
		total = len(member_joins) - len(member_leaves)
		if total < 0: total = 0

		#Повідомлення
		channel = self.bot.get_channel(INVITES_CHANNEL)
		try: inviter = f"**{member.guild.get_member(m).name}** (<@{m}>)"
		except: inviter = f"<@{m}>"
		await channel.send(f"💔 **{member.name}** ({member.mention}) покинув сервер. Його запросив {inviter}, тепер запрошення має **{total}** використань.\nПриєднався на сервер: <t:{int(member.joined_at.timestamp())}:R>", allowed_mentions=disnake.AllowedMentions(everyone=False, users=False, roles=False))


def setup(bot:commands.Bot):
	bot.add_cog(InviteLogger(bot))