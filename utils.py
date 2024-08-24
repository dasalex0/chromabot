import disnake
import random
import re
import os
import pytz
import json
import asyncio
import requests
import emoji as emj
from config import *
from time import time
from io import BytesIO
from aiohttp import ClientSession
from disnake.ext import commands, tasks
from datetime import timedelta, datetime
from disnake import Webhook, OptionChoice
from PIL import Image, ImageDraw, ImageOps, ImageFont, ImageEnhance
from dotenv import load_dotenv
load_dotenv()


###
### Маленькі функції
###
def curTime():
	return int(time())

def hf(num:int):
	return '{0:,}'.format(num)

def percent(num:int, percent:int):
	num = num / 100
	num = num * percent
	return num

def loadFont(size:int, name:str="eukraine.otf"):
	return ImageFont.truetype(f'img/fonts/{name}', size=size)

def paste(one:Image.Image, two:Image.Image, pos:tuple[int, int]):
	padded = Image.new('RGBA', one.size, (0, 0, 0, 0))
	padded.paste(two, pos)
	result = Image.alpha_composite(one, padded)
	one.paste(result, (0, 0))

def get_xp_goal(member:disnake.Member):
	typnm = 0
	level = level_db.find(f"{member.id}")
	lvl = level['level']
	type = level['type']
	if type == list(LEVELS)[0]: typnm = 1
	for i in LEVELS:
		if i == type: break
		typnm += LEVELS[i]['levels']
	return int((lvl + typnm) * XP_PER_LEVEL * LEVELS[type]['multiple'])

def str_to_hex(string:str):
	base16INT = int(string.replace('#',''), 16)
	hex_value = hex(base16INT)
	return int(hex_value,0)

def wrap(content:str, max:int=25):
	wrapped, line = [], ""
	#Word Wrap
	for word in content.split(' '):
		line += f"{word} "
		if len(line) >= max:
			wrapped.append(line)
			line = ""
	if line != "": wrapped.append(line)
	#Regular Wrap
	if len(wrapped) == 1 and len(wrapped[0]) > max:
		wrapped = []
		step = int(max)-1
		for i in range(0, len(content), step):
			wrapped.append(content[int(i):step])
			step += int(max)
	return wrapped


###
### Функції з
### Повідомленнями
###
async def error(inter:disnake.Interaction, msg:str, ephemeral:bool=True, components:list=None, footer:str=None):
	emb = disnake.Embed(description=msg, color=RED)
	emb.set_author(name=f"@{inter.author}", icon_url=inter.author.display_avatar)
	#Футер
	if footer:
		emb.set_footer(text=footer)
	else:
		emb.timestamp = datetime.now()
	#Компоненти
	if components:
		return await inter.send(embed=emb, ephemeral=ephemeral, components=components)
	else:
		return await inter.send(embed=emb, ephemeral=ephemeral)

async def success(inter:disnake.Interaction, msg:str, ephemeral:bool=False, components:list=None, footer:str=None):
	emb = disnake.Embed(description=msg, color=GREEN)
	emb.set_author(name=f"@{inter.author}", icon_url=inter.author.display_avatar)
	#Футер
	if footer:
		emb.set_footer(text=footer)
	else:
		emb.timestamp = datetime.now()
	#Компоненти
	if components:
		return await inter.send(embed=emb, ephemeral=ephemeral, components=components)
	else:
		return await inter.send(embed=emb, ephemeral=ephemeral)

def loadJsonEmbed(options:dict) -> tuple[str, list[disnake.Embed]]:
	content = ""
	embeds = []
	for emb_info in options['embeds']:
		emb = disnake.Embed()
		#Заголовок
		if "title" in emb_info:
			emb.title = emb_info["title"]
		#Опис
		if "description" in emb_info:
			emb.description = emb_info["description"]
		#Посилання
		if "url" in emb_info:
			emb.url = emb_info["url"]
		#Колір
		if "color" in emb_info:
			if isinstance(emb_info["color"], str):
				emb.set_default_colour(str_to_hex(emb_info["color"]))
			elif isinstance(emb_info["color"], int):
				emb.set_default_colour(emb_info["color"])
		#Автор
		if "author" in emb_info:
			if "name" in emb_info["author"]:
				emb.author.name = emb_info["author"]["name"]
			elif "icon_url" in emb_info["author"]:
				emb.author.icon_url = emb_info["author"]["icon_url"]
			if "url" in emb_info["author"]:
				emb.author.url = emb_info["author"]["url"]
		#Футер
		if "footer" in emb_info:
			if "text" in emb_info["footer"]:
				emb.set_footer(text=emb_info["footer"]["text"])
			if "icon_url" in emb_info["footer"]:
				emb.set_footer(text=emb_info["footer"]["text"], icon_url=emb_info["footer"]["icon_url"])
		#Зображення
		if "image" in emb_info and "url" and emb_info["image"]:
			emb.set_image(emb_info["image"]["url"])
		#Маленьке зображення
		if "thumbnail" in emb_info and "url" and emb_info["thumbnail"]:
			emb.set_thumbnail(emb_info["thumbnail"]["url"])
		#Поля
		if "fields" in emb_info:
			for field in emb_info["fields"]:
				name = None
				if "name" in field:
					name = field["name"]
				value = None
				if "value" in field:
					value = field["value"]
				inline = False
				if "inline" in field:
					inline = field["inline"]
				emb.add_field(name=name, value=value, inline=inline)
		embeds.append(emb)
	return content, embeds


###
### Інші
### Функції
###
def convert_time(time:str):
	time_dict = {"s" : 1, "m" : 60, "h" : 3600, "d": 3600*24}
	unit = time[-1]
	if unit not in time_dict: return -1
	try: val = int(time[:-1])
	except: return -2
	return val * time_dict[unit]

async def zakacap(member:disnake.Member):
	#Додавання ролі кацапа
	try: await member.add_roles(member.guild.get_role(KATCAP))
	except: pass
	#Учасник
	try: await member.remove_roles(member.guild.get_role(MEMBER_ROLE_ID))
	except: pass
	channel = member.guild.get_channel(SVINARNYK)
	await channel.send(
		f"🐖 Вітаємо, дорогий кацап {member.mention}, в **сVинарник**. Ось невеликий гайд по цьому воістину прекрасному місцю:\n"
		"- Тут вас будуть принижувати. (Але ви повинні терпіти, це ваше призначення в цьому житті)\n"
		"- Ви обмежені в правах. Ви не зможете прикріпити сюди картинку, гіфку чи навіть якийсь емодзі. Ужас!\n"
		"- Вас в будь-який момент можуть замутити, обісрати вам нік чи просто забанити, але не забувайте: \"Русский - Терпеть\".\n"
	)

def image_bar(idraw, x:int, y:int, width:int, height:int, progress:float, bg:str="black", fg:str="red"):
	idraw.ellipse((x+width, y, x+height+width, y+height), fill=bg)
	idraw.ellipse((x, y, x+height, y+height), fill=bg)
	idraw.rectangle((x+(height/2), y, x+width+(height/2), y+height), fill=bg)
	width *= progress
	if progress > 0:
		idraw.ellipse((x+width, y, x+height+width, y+height), fill=fg)
		idraw.ellipse((x, y, x+height, y+height), fill=fg)
		idraw.rectangle((x+(height/2), y, x+width+(height/2), y+height), fill=fg)
	return idraw


###
### Функції
### Реєстрації
###
def register(member:disnake.Member):
	if member.bot: return
	#Рівень
	if str(member.id) not in level_db.full():
		update = {}
		update['type'] = "bronze"
		update['messages'] = 0
		update['messages_today'] = 0
		update['messages_week'] = 0
		update['level'] = 1
		update['xp'] = 0
		update['voice'] = 0
		update['last_activity'] = curTime()
		level_db.update(f"{member.id}", update)
	#Затримка
	if str(member.id) not in cooldown_db.full():
		cooldown_db.update(f"{member.id}", {})
	#Економіка
	if str(member.id) not in eco_db.full():
		update = {}
		update['money'] = 0
		update['job'] = 0
		eco_db.update(f"{member.id}", update)
	#Картка
	if str(member.id) not in card_db.full():
		update = {}
		update['background'] = 0
		update['backgrounds'] = [0]
		update['frame'] = 0
		update['frames'] = [0]
		update['deco'] = 0
		update['decos'] = [0]
		update['color'] = "999999"
		card_db.update(f"{member.id}", update)

def register_pig(member:disnake.Member):
	pigs = pigs_db.full()
	if str(member.id) not in pigs:
		update = {}
		update["name"] = f"Безіменна Свиня #{len(pigs)}"
		update["balance"] = 0
		update["balance_eaten"] = 0
		update["mass"] = 1
		update["power"] = 1
		update["wins"] = 0
		update["loses"] = 0
		update["created"] = curTime()
		update['image'] = "https://cdn.discordapp.com/attachments/1202307855743733811/1205250828269523034/default.png?ex=65fc9a4d&is=65ea254d&hm=123f66a4ce66c868d1b3345c3bcf313f31e96f3b339c8936f4575e3a872b6415&"
		update['image_id'] = None
		update['skin'] = 0
		update['skins'] = [0]
		update['eye'] = 0
		update['eyes'] = [0]
		update['deco'] = 0
		update['decos'] = [0]
		update['face'] = 0
		update['faces'] = [0]
		update['hat'] = 0
		update['hats'] = [0]
		pigs_db.update(f"{member.id}", update)


###
### Економіка
### Серверу
###
def pick_color(progress:float):
	color_list = {
		0.9: '#4EB256', 0.8: '#74B54F', 0.7: '#77BF54', 0.6: '#AACC47', 0.5: '#D8CC41',
		0.4: '#D6A22A', 0.3: '#D38723', 0.2: '#D16B23', 0.1: '#DB4325', 0.0: '#AF201D'
	}
	for i in color_list:
		if progress >= i:
			return color_list[i]
	return color_list[-1]

def get_program_owner(inter:disnake.Interaction, member:disnake.Member|int):
	if isinstance(member, int): member = inter.guild.get_member(member)
	if not member: return None
	category = inter.guild.get_channel(956898075144769556)
	for channel in category.channels:
		channel:disnake.TextChannel
		if channel.overwrites_for(member).send_messages == True and channel.overwrites_for(member).manage_messages == True:
			return channel
	return None

def get_program_member(guild:disnake.Guild, member:disnake.Member|int):
	if isinstance(member, int): member = guild.get_member(member)
	category = guild.get_channel(956898075144769556)
	for channel in category.channels:
		channel:disnake.TextChannel
		if channel.overwrites_for(member).send_messages == True:
			return channel
	return None

def get_position(guild:disnake.Guild, channel:disnake.TextChannel|int):
	if isinstance(channel, int): channel:disnake.TextChannel = guild.get_channel(channel)
	if channel and channel.category:
		sorted_channels = sorted(channel.category.channels, key=lambda c: c.position)
		category_position = sorted_channels.index(channel)
		return category_position
	return 0

async def run_script(scriptname:str, member:disnake.Member) -> str|bool:
	### pick Script
	if scriptname.startswith("pick"):
		eco = eco_db.find(f"{member.id}")
		if any(x in eco for x in list(PICK_DURABILITY)):
			return f"<:cross:1127281507430576219> **Ви вже маєте кайло!**"
		eco["pick_durability"] = PICK_DURABILITY[scriptname]
		eco_db.update(f"{member.id}", eco)
		return True

	### Бустер
	elif scriptname.startswith("booster_"):
		register(member)
		boost = scriptname.split("_")
		level = level_db.find(f"{member.id}")
		if 'booster' in level:
			if level['booster'] >= int(boost[1]):
				return "<:cross:1127281507430576219> **Ви вже маєте активний бустер!**"
		level['booster'] = int(boost[1])
		level['booster_expire'] = curTime()+(86400*7)
		level_db.update(f"{member.id}", level)
		return True

	### Свиня
	elif scriptname == "pig":
		try: eco_db.delete(f"{member.id}.pig")
		except: pass
		try: pigs_db.delete(f"{member.id}")
		except: pass
		register_pig(member)
		set_cooldown(member, 'pig-feed', 0)
		set_cooldown(member, 'pig-fight', 0)
		return True

	### Створення програми
	elif scriptname == "create_program":
		if get_program_member(member.guild, member) != None:
			return "<:cross:1127281507430576219> **Ви вже є власником/учасником однієї з програм!**"
		guild = member.guild
		overwrites = {
			guild.default_role: disnake.PermissionOverwrite(read_messages=True,manage_channels=False,manage_permissions=False,manage_webhooks=False,create_instant_invite=False,send_messages=False,send_messages_in_threads=True,create_private_threads=False,create_public_threads=False,embed_links=False,attach_files=False,add_reactions=False,use_external_emojis=True,use_external_stickers=True,mention_everyone=False,manage_messages=False,manage_threads=False,read_message_history=True,send_tts_messages=False,use_slash_commands=False,send_voice_messages=True),
			member: disnake.PermissionOverwrite(read_messages=True,send_messages=True,create_public_threads=True,create_private_threads=True,embed_links=True,attach_files=True,add_reactions=True,manage_messages=True,manage_threads=True),
			guild.get_role(KATCAP): disnake.PermissionOverwrite(read_messages=False), #кацап
			guild.get_role(ACTIVE_ID): disnake.PermissionOverwrite(add_reactions=True), #актив
		}
		pc = member.guild.get_channel(956898075144769556)
		await guild.create_text_channel(f"{member.name[:15]}-program", slowmode_delay=30, overwrites=overwrites, category=pc)
		try: await member.add_roles(guild.get_role(PROGRAM_ID))
		except: pass
		return True


###
### Функції із
### Затримкою
###
async def cooldown_notice(inter:disnake.Interaction, wait:int):
	emb = disnake.Embed(description=f"⏱ **Затримка! Повертайтеся <t:{int(wait)}:R>**", color=RED, timestamp=datetime.now())
	emb.set_author(name=inter.author, icon_url=inter.author.display_avatar)
	return await inter.send(embed=emb, ephemeral=True)

def set_cooldown(member:disnake.Member, type:str, time:int|float):
	cooldown = cooldown_db.find(f"{member.id}")
	cooldown[type] = curTime() + time
	cooldown_db.update(f"{member.id}", cooldown)

async def checkcooldown(member:disnake.Member, type:str):
	register(member)
	cooldown = cooldown_db.find(f"{member.id}")
	if not type in cooldown:
		cooldown[type] = 0
		cooldown_db.update(f"{member.id}", cooldown)
		return None
	cd = cooldown[type]
	if int(cd) > curTime(): return cd
	else: return None


###
### Рівень
###
def set_rank(toppos:int):
	ranks = {1: '🥇', 2: '🥈', 3: '🥉'}
	for r in ranks:
		if toppos == r: return ranks[r]+' '
	return ''

def voicelevel(num:int|float):
	if num <= 60:
		return f"{str(num)} сек."
	elif num > 60 and num <= 3600:
		return f"{str(round(num/60, 1))} хв."
	elif num > 3600 and num <= 129600:
		return f"{str(round(num/60/60, 1))} год."
	elif num > 129600:
		return f"{str(round(num/60/60/24, 1))} днів"

def check_active(member_id:int):
	db = level_db.full()
	if str(member_id) not in db:
		return False
	level = db[str(member_id)]['level']
	type = db[str(member_id)]['type']
	if level > 1 and type == 'bronze':
		return True
	elif type != 'bronze':
		return True
	return False


###
### БД
###
def open_banwords():
	f = open("./data/banwords.txt", encoding="utf-8")
	ruwords = [s.replace("\n", "").replace("\r", "") for s in f.readlines()]
	return ruwords