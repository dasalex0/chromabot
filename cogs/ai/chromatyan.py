from utils import *

class ChromaTyan(commands.Cog):
	def __init__(self, bot:commands.Bot):
		self.bot = bot
		self.cooldown = 0
		self.api = os.getenv('API')
		self.api_key = os.getenv('API_KEY')
		self.blocked_users = []
		self.conversation_histories:dict[int, list] = {}


	async def ask_gpt(self, message:str, member:disnake.Member, conversation_history:dict={}, model:str="gpt-4-0125-preview"):
		#БАЗА ДАНИХ
		with open('data/ai/personality.txt', encoding='utf-8') as f:
			personality = f.read().replace('\n',' ')
		with open('data/ai/dataset.txt', encoding='utf-8') as f:
			dataset = f.read().replace('\n',' ')

		#JSON
		json = {
			"model": model,
			"max_tokens": 150,
			"messages": [
				{
					"role": "system",
					"content": personality
				},
				{
					"role": "system",
					"content": dataset
				},
				{
					"role": "system",
					"content": (
						f"You are currently speaking with person {member.display_name}, with nickname {member.name}. If you are asked with whom you speaking, answer {member.display_name} or {member.name}. "
						f"If they ask you about their id or айді, answer {member.id}. "
						f"If they ask you about when he joined server, answer {member.joined_at.day} {MONTHS[member.joined_at.month]} {member.joined_at.year} року. "
						f"If they ask you about when he registered in discord, answer {member.created_at.day} {MONTHS[member.created_at.month]} {member.created_at.year} року. "
					)
				},
				*conversation_history,
				{
					"role": "user",
					"content": message
				}
			]
		}

		try:
			async with ClientSession() as session:
				headers = {
					'Authorization': f'Bearer {self.api_key}',
					'Content-Type': 'application/json'
				}
				#Реквест на апі OpenAI
				async with session.post(self.api, json=json, headers=headers) as response:
					if response.status != 200:
						raise Exception(await response.text())
					#Отримання відповіді від AI
					chat_completion = await response.json()
					ai_response:list[str] = chat_completion["choices"][0]["message"]["content"].rstrip('.').split(' ')
					if random.randint(1,100) < 90: ai_response[0] = ai_response[0].lower()
					return ' '.join(ai_response)
		except Exception as e:
			print('Error during OpenAI API call:', e)
			return None


	@commands.Cog.listener()
	async def on_message(self, message:disnake.Message):
		if not message.guild: return
		if message.guild.id != GUILD_ID and message.channel.id not in CHROMATYAN_CHANNELS: return
		if message.author.bot: return
		if message.author.id in self.blocked_users: return
		if len(message.content) <= 0 and message.attachments == []: return

		if message.channel.id in CHROMATYAN_CHANNELS and self.cooldown < time() and self.bot.user in message.mentions:
			content = message.content.replace(self.bot.user.mention, "")
			#Перевірки
			if len(content) == 0 and message.attachments == [] and message.stickers == []:
				content = 'привіт'
			elif len(content) < 2 or len(content) > 90: return
			self.cooldown = int(time()) + 2

			#Повідомлення, на яке відповідає користувач
			ref_message = None
			if message.reference:
				try:
					channel = self.bot.get_channel(message.reference.channel_id)
					ref_message = await channel.fetch_message(message.reference.message_id)
				except: pass

			#Додавання канала в історію
			if message.author.id not in self.conversation_histories:
				self.conversation_histories[message.author.id] = []

			#Отримання контексту каналу
			conversation_history = self.conversation_histories[message.author.id]

			#Додавання контексту відповіді
			if ref_message:
				ref_message.content = ref_message.content.replace(self.bot.user.mention, "")
				if len(ref_message.content) > 2 and len(ref_message.content) < 250:
					if {"role": "user", "content": ref_message.content} not in conversation_history:
						conversation_history.append({
							"role": "user",
							"content": ref_message.content
						})

			#Відповідь від AI
			ai_response = await self.ask_gpt(content, message.author, conversation_history, model="gpt-3.5-turbo-0125")
			if not ai_response:
				return await message.channel.send("Sorry, I encountered an error while trying to respond.", reference=message)
			ai_response = ai_response[:150]
			#ХромаТян пише...
			if not emj.is_emoji(ai_response) and len(ai_response) > 2:
				self.cooldown = int(time()) + len(ai_response) * 0.1
				async with message.channel.typing():
					await asyncio.sleep(len(ai_response) * random.uniform(0.07,0.1))

			#Додавання контенту користувача
			conversation_history.append({
				"role": "user",
				"content": content
			})

			#Реакції
			if len(ai_response) == 1 and emj.is_emoji(ai_response):
				try: await message.add_reaction(ai_response)
				except: pass
			elif len(ai_response) == 2 and emj.is_emoji(ai_response[0]) and emj.is_emoji(ai_response[1]):
				try: await message.add_reaction(ai_response)
				except: pass
			else:
				#видалення всякої хуйні з повідомлення да
				if ai_response.endswith('😏') and random.randint(1,100) < 90:
					ai_response = ai_response[:-1]
				#іноді видаляти емодзі в кінці повідомлення
				if emj.is_emoji(ai_response[-1]) and random.randint(1,100) < 60:
					ai_response = ai_response[:-1]
					try: await message.add_reaction(ai_response[-1])
					except: pass

				#Додавання відповіді від AI
				conversation_history.append({
					"role": "assistant",
					"content": ai_response
				})
				#Надсилання
				try: await message.channel.send(ai_response, reference=message, allowed_mentions=disnake.AllowedMentions(everyone=False, users=False, roles=False, replied_user=True))
				except: pass
			#обрізання контексту, щоб у артема не закінчилися гроші (ну або не так швидко)
			if len(conversation_history) > 7:
				conversation_history = conversation_history[:-7]


def setup(bot:commands.Bot):
	bot.add_cog(ChromaTyan(bot))