from utils import *


class Info(commands.Cog):
	def __init__(self, bot:commands.Bot):
		self.bot = bot


	@commands.Cog.listener()
	async def on_dropdown(self, inter:disnake.MessageInteraction):
		if inter.component.custom_id != 'info': return
		values = inter.values[0]
		options = ChrDB(f"data/info/{values}.json").full()
		content, embeds = loadJsonEmbed(options)
		await inter.response.send_message(content, embeds=embeds, ephemeral=True)


	@commands.command()
	async def info(self, ctx:commands.Context):
		if ctx.author.id == ALEX:
			#Embed
			db = ChrDB('data/info/_main.json').full()
			content, embeds = loadJsonEmbed(db)
			
			#Опції
			db = ChrDB('data/info/_options.json').full()
			options = []
			for option in db:
				options.append(disnake.SelectOption(label=db[option]['title'], emoji=db[option]['emoji'], value=option))
			dropdown = disnake.ui.StringSelect(placeholder="Виберіть категорію інформації", custom_id="info", options=options)

			#Відправка
			btn = disnake.ui.Button(label="Запрошення на сервер", emoji="🔗", url="https://discord.gg/6UpZ4gVcud")
			btn2 = disnake.ui.Button(label="Донат", emoji="💸", url="https://donatello.to/dasalex")
			await ctx.send(content, embeds=embeds, components=[dropdown,btn,btn2])
			await ctx.message.delete()


def setup(bot:commands.Bot):
	bot.add_cog(Info(bot))