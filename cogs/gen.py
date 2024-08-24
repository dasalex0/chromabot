from utils import *


class Gen(commands.Cog):
	def __init__(self, bot:commands.Bot):
		self.bot = bot


	@commands.slash_command(guild_ids=[GUILD_ID])
	async def gen(self, inter): pass

	@gen.sub_command_group()
	async def meme(self, inter): pass


	@gen.sub_command(name="caption", description="🤖 Зробити картинку з написом зверху.")
	@commands.cooldown(1, 2, commands.BucketType.user)
	async def caption(
		self, inter:disnake.CommandInter,
		зображення:disnake.Attachment,
		текст:str=commands.Param(max_length=150)
	):
		if inter.locale == disnake.Locale.ru:
			return await error(inter, "<:cross:1127281507430576219> **При ініціалізації мови сталася помилка!**")
		image = зображення
		text = текст
		check = await checkcooldown(inter.author, "gencommands")
		if check: return await cooldown_notice(inter, check)
		await inter.response.defer()

		#Зображення користувача
		try:
			data = BytesIO(await image.read())
			cimg = Image.open(data)
		except: return await error(inter, "<:cross:1127281507430576219> **Не вдалося згенерувати зображення!**")

		#Створення зображення
		if cimg.width > 920 or cimg.height > 920:
			cimg = cimg.resize((int(cimg.width/2), int(cimg.height/2)))
		if cimg.width > 920 or cimg.height > 920:
			cimg = cimg.resize((int(cimg.width/2), int(cimg.height/2)))
		cimg = cimg.convert("RGBA")
		#Створення тексту
		size = int((cimg.width + cimg.height) / 25)
		text = wrap(text, cimg.width/(size*0.8))
		#Зображення
		white = ((size+5)*len(text)) + 20
		img = Image.new("RGBA", (cimg.width,cimg.height+white))
		paste(img, cimg, (0,white))
		idraw = ImageDraw.Draw(img)
		idraw.rectangle([(0,0), (img.width,white)], width=3, fill="white")

		#Текст
		font = loadFont(size, 'arial.ttf')
		if len(text) < 2: y = int(white/2-size/2)-1
		else: y = int(white/2-size/2)/len(text)-1
		for t in text:
			w = idraw.textlength(t, font)
			x = int((img.width - w) / 2)
			idraw.text((x, y), t, font=font, fill="black")
			y += size+5

		#Збереження
		img.save("caption.png")
		await inter.send(file=disnake.File(fp="caption.png"))
		os.remove("caption.png")
		set_cooldown(inter.author, "gencommands", 15)


	@gen.sub_command(name="demotivator", description="🤖 Зробити демотиватор.")
	@commands.cooldown(1, 2, commands.BucketType.user)
	async def demotivator(
		self, inter:disnake.CommandInter,
		зображення:disnake.Attachment,
		заголовок:str=commands.Param(max_length=75),
		підзаголовок:str=commands.Param(default=None,max_length=125)
	):
		if inter.locale == disnake.Locale.ru:
			return await error(inter, "<:cross:1127281507430576219> **При ініціалізації мови сталася помилка!**")
		title, image, subtitle = заголовок, зображення, підзаголовок
		check = await checkcooldown(inter.author, "gencommands")
		if check: return await cooldown_notice(inter, check)
		await inter.response.defer()

		#Зображення користувача
		if not image.filename.lower().endswith(('.png', '.jpg', '.jpeg')):
			return await error(inter, "<:cross:1127281507430576219> **Файл повинен бути зображенням формату PNG чи JPEG!**")
		try:
			data = BytesIO(await image.read())
			cimg = Image.open(data).convert('RGBA')
			img = Image.new("RGBA", (49+cimg.width+49, 34+cimg.height+100), "black")
		except: return await error(inter, "<:cross:1127281507430576219> **Не вдалося згенерувати зображення!**")

		#Створення зображення
		while cimg.width > 640 or cimg.height > 640:
			cimg = cimg.resize((int(cimg.width/2), int(cimg.height/2)))
		while cimg.width <= 128 or cimg.height <= 128:
			cimg = cimg.resize((int(cimg.width*2), int(cimg.height*2)))
		size = int((cimg.width + cimg.height) / 20)
		size2 = int(size/1.5)
		#Заголовок
		title = wrap(title, (cimg.width)/(size/1.7))
		#Підзаголовок
		black = 76+((size+5)*len(title))
		if subtitle != None:
			subtitle = wrap(subtitle, (cimg.width)/(size2/2))
			black += ((size2+5)*len(subtitle))
		y = 34+cimg.height+black
		img = Image.new("RGBA", (49+cimg.width+49, y), "black")
		paste(img, cimg, (49,34))

		#хз
		idraw = ImageDraw.Draw(img)
		idraw.rectangle([(45,30), (49+cimg.width+3, 34+cimg.height+3)], width=2)
		w = idraw.textlength('dsc.gg/chromaua', loadFont(int(size/3), 'arial.ttf'))
		idraw.text((img.width-w-4, img.height-size/2-2), 'dsc.gg/chromaua', font=loadFont(int(size/3), 'arial.ttf'), fill="#cccccc")
		#Текст
		if len(title) <= 1: y = int(40+cimg.height+black/2-size)
		else: y = int(36+cimg.height+black/2-size*len(title)/2)
		if підзаголовок != None: y -= size2/2
		for t in title:
			font = loadFont(size, 'demotivator.ttf')
			w = idraw.textlength(t, font)
			x = int((img.width - w) / 2)
			idraw.text((x, y), t, font=font, fill="white")
			y += size+5
		#Другий текст
		if підзаголовок != None:
			y += 10
			for t in subtitle:
				font = loadFont(size2, 'demotivator.ttf')
				w = idraw.textlength(t, font)
				x = int((img.width - w) / 2)
				idraw.text((x, y), t, font=font, fill="white")
				y += size2+3

		#Збереження
		img.save("ai_demotivator.png")
		await inter.send(file=disnake.File(fp="ai_demotivator.png"))
		os.remove("ai_demotivator.png")
		set_cooldown(inter.author, "gencommands", 15)


	@gen.sub_command(name="speechbubble", description="🤖 Додати хмаринку з текстом до картинки.")
	@commands.cooldown(1, 2, commands.BucketType.user)
	async def speechbubble(self, inter:disnake.CommandInter, зображення:disnake.Attachment):
		if inter.locale == disnake.Locale.ru:
			return await error(inter, "<:cross:1127281507430576219> **При ініціалізації мови сталася помилка!**")
		image = зображення
		check = await checkcooldown(inter.author, "gencommands")
		if check: return await cooldown_notice(inter, check)

		if not image.filename.lower().endswith(('.png', '.jpg', '.jpeg')):
			return await error(inter, "<:cross:1127281507430576219> **Файл повинен бути зображенням формату PNG чи JPEG!**")
		await inter.response.defer()

		try:
			data = BytesIO(await image.read())
			cimg = Image.open(data).convert("RGBA")
			mask = Image.open('./img/misc/mask2.png').resize((cimg.width, cimg.height)).convert('L')
		except: return await error(inter, "<:cross:1127281507430576219> **Не вдалося згенерувати зображення!**")
		output = ImageOps.fit(cimg, mask.size, centering=(0.5, 0.5))
		output.putalpha(mask)

		output.save("gen_sb.gif")
		await inter.send(file=disnake.File(fp="gen_sb.gif"))
		os.remove("gen_sb.gif")
		set_cooldown(inter.author, "gencommands", 15)


def setup(bot:commands.Bot):
	bot.add_cog(Gen(bot))