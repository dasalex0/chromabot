import pytz
from disnake import PermissionOverwrite
from chrdb import ChrDB

#хз
VERSION = "3.1"
LOG_WEBHOOK = "https://discord.com/api/webhooks/канал/да"
TIMEZONE = pytz.timezone('Europe/Kiev')
YOUNG_TIME = 86400*7
MONTHS = {
	1: "січня", 2: "лютого", 3: "березня", 4: "квітня", 5: "травня", 6: "червня",
	7: "липня", 8: "серпня", 9: "вересня", 10: "жовтня", 11: "листопада", 12: "грудня"
}
LETTER_LIST = "абвгґдеєжзиійїклмнопрстуфхцчшщьюя"
LETTER_ENG_LIST = "abcdefghijklmnopqrstuvwxyz"
NUMBER_LIST = "0123456789-"
LOGS_IGNORE = [] #канали, що ігноруються в логах


#Кольори
EMBEDCOLOR = 0x5865F2
INVISIBLE = 0x2B2D31
RED = 0xE53D2D
GREEN = 0x2BD873
LOG_RED = 0xBF4242
LOG_BLUE = 0x6C85D8
LOG_GREEN = 0x39BF39


#ID ролей для карточки
BOY_ID = 1091070507866132520
GIRL_ID = 1091070577328013392
STAFF_ID = 954271417799692288
PROGRAM_ID = 955015212799504386
DONATER_ID = 985459656749113365
BOOSTER_ID = 944902959018434561
ACTIVE_ID = 944886145538469908
MEMBER_ROLE_ID = 942714660069707806

#Інші ID
GUILD_ID = 942713932634808340 #ID хроми
ALEX = 1050301564310528021 #ID розробника, треба для сєкрєтних команд
KATCAP = 1116033722496585729 #Роль кацапа, для свинарника
UG_IGNORE = 1104866997658976450 #щоб бот не бив за суржик


#Ролі, що даються при заході на сервер
JOIN_ROLES = (
	MEMBER_ROLE_ID,
	944886784041558057,
	952855531339522091,
	1077297827639734403,
	953322942249451570
)


#Рівні
BRONZE_ID = 970934587125555230
SILVER_ID = 953322813111013386
PLATINUM_ID = 953329331353026660
GOLD_ID = 1186341274899456181
DIAMOND_ID = 953330170201247854
SAPPHIRE_ID = 1189940853209317528
CHROMIUM_ID = 1189941622503395429
ELITE_ID = 953330332390793226
ARCANA_ID = 1186341598401937459


#Інфо
INFO_CHANNEL = 1112770569889382520
NEWS_CHANNEL = 942722621303304242
VOTE_CHANNEL = 942727689352146944
#Комунікація
CHAT_CHANNEL = 943122899210997770
MEDIA_CHANNEL = 963099838755532840
SVINARNYK = 1055023457378770985
BOTS_CHANNEL = 943134988201775134
#Войс
VOICE_CATEGORY_ID = 981904733927272469
VOICE_CREATE_ID = 981899306648891462
#Інше
SUGGESTIONS_CHANNEL = 1164427321734864937
ECONOMY_CHANNEL = 1213166998742237275
BUMPREMINDER_CHANNEL = 1200164631419830396
SELFADV_CHANNEL = 1111286974406459462
#Міні-ігри
WORDS_MINIGAME = 1218310811169067068
COUNT_MINIGAME = 1218310922863382558
#Адмін. зона
INVITES_CHANNEL = 1077281528750551111
ADMIN_TRASH = 943063887383781376

#Канали в яких працює хроматян
CHROMATYAN_CHANNELS = [CHAT_CHANNEL]


#Рівень
LVL_CHANNELS = [CHAT_CHANNEL, MEDIA_CHANNEL, ECONOMY_CHANNEL, BUMPREMINDER_CHANNEL] #канали в яких накопичується досвід
XP_PER_LEVEL = 415 #скільки треба досвіду для апу наступного рівня
MONEY_PER_LEVEL = 50 #кількість грошей за ап рівня
LEVELS = {
	"bronze": {
		"name": "Бронза",
		"color": "AF6B2B",
		"role": BRONZE_ID,
		"multiple": 1,
		"levels": 3
	},
	"silver": {
		"name": "Срібло",
		"color": "7F7F7F",
		"role": SILVER_ID,
		"multiple": 1.4,
		"levels": 3
	},
	"platinum": {
		"name": "Платина",
		"color": "697F64",
		"role": PLATINUM_ID,
		"multiple": 1.8,
		"levels": 3
	},
	"gold": {
		"name": "Золото",
		"color": "DD9F0D",
		"role": GOLD_ID,
		"multiple": 2.2,
		"levels": 3
	},
	"diamond": {
		"name": "Діамант",
		"color": "3C87B9",
		"role": DIAMOND_ID,
		"multiple": 2.6,
		"levels": 3
	},
	"sapphire": {
		"name": "Сапфір",
		"color": "355BA7",
		"role": SAPPHIRE_ID,
		"multiple": 3,
		"levels": 3
	},
	"chromium": {
		"name": "Хроміум",
		"color": "8B5BD4",
		"role": CHROMIUM_ID,
		"multiple": 4.5,
		"levels": 3
	},
	"elite": {
		"name": "Еліта",
		"color": "D64B06",
		"role": ELITE_ID,
		"multiple": 5.5,
		"levels": 3
	},
	"arcana": {
		"name": "Аркана",
		"color": "A01609",
		"role": ARCANA_ID,
		"multiple": 10,
		"levels": 1
	}
}



#Іконки
CURRENCY = "<:chr_money:1213150977486753812>"
BOOLSTATUS = {
	True: "<:check:1127281505153069136>",
	False: "<:cross:1127281507430576219>"
}



#/crime
CRIME_CHANCE = 40
CRIME_REPLIES = (
	"🕵️‍♂️ Ви пограбували невеликий магазинчик пончиків, з цього магазину вам вдалося вкрасти {amount}",
	"🕵️‍♂️ Ви вкрали гаманець у людини, яка проходила повз. Там було {amount}",
	"🕵️‍♂️ Ви знайшли гаманець на дорозі. Там було {amount}",
	"🕵️‍♂️ Ви непомітно вкрали {amount} з кишені у людини в магазині.",
	"🕵️‍♂️ Ви надурили кацапа в інтернеті. Вам вдалося вкрасти {amount} з його балансу.",
	"🕵️‍♂️ Ви розбили скло в машини і вкрали чиюсь сумку звідти. Там було {amount}",
	"🕵️‍♂️ Ви надурили людину в інтернеті. Вам вдалося заробити {amount}",
    "🕵️‍♂️ Ви вкрали іграшки з дитячого будинку, і продали їх за {amount}",
	"🥶 Ви приїхали в росію, і стали іноагентом. Таким чином вам вдалося вкрасти {amount} із рускага бюджета, і повернутися додому."
)
FAIL_CRIME_REPLIES = (
	"Ви спробували пізданути блендер, але прийшов артьом газобетонщік і вас спіймав. Лікування коштувало {amount}",
	"Ви спробували пограбувати невеликий магазинчик, але продавець дістав пістолет і вимагав штраф у розмірі {amount}",
	"Ви спробували пограбувати магазин пончиків, але продавець дістав дробовик і вимагав штраф у розмірі {amount}",
	"При спробі пограбування магазину, його закрили і ви залишилися в пастці. Вам довелося заплатити {amount}, щоб вас випустили.",
	"При спробі пограбування піцерії, її закрили і ви залишилися в пастці. Вам довелося заплатити {amount}, щоб вас випустили.",
	"Ви вкрали телефон у дівчини, але вона виявилася донькою мафіозі. Щоб врятувати своє життя, вам довелося віддати {amount}",
	"При спробі вкрасти гаманець у людини, вона сильно вас побила і зателефонувала в поліцію. Вам довелося віддати {amount}",
	"При спробі вкрасти гаманець у чоловіка, він вас побив. Лікування коштувало вам {amount}",
	"Ви спробували викрасти машину, але спрацювала сигналізація і вас спіймала поліція. Вам довелося віддати {amount}",
	"При спробі взлому онлайн-сервісу, вас вичіслили і за вами приїхала поліція. Вам довелося заплатити {amount}",
	"Ви ходили під час коменданської години. Вас спіймали і виписали штраф в розмірі {amount}",
	"Ви ходили по вулиці під час коменданської години. Вас спіймали і виписали вам повістку. Ви якимось чином просрали {amount}",
	"Ви приїхали в росію, стали іноагентом і спробували вкрасти гроші з бюджету. Але вас спіймали, і посадили в камеру до навального. Ви віддали {amount} і вас випустили, бо карупції нєт!",
	"Ви намагалися вкрасти іграшки з дитячого будинку, але вас спіймав охоронець. Вам довелося виплатити штраф в розмірі {amount}",
	"Вас спіймали і мобілізували в магазині. Стати не придатним коштувало {amount}"
)

#/mine
MINE_ROCKS = (4,7)
MINE_IRON = (1,6)
MINE_GOLD = (1,4)
MINE_DIAMOND = (1,2)
MINE_EMERALD = (1,2)
MINE_COOLDOWN = 60*60

#/blackjack
BJ_LIMIT = (100, 1000)
BJ_MAX = 1500
BJ_COOLDOWN = 3600*2
BJ_MAX_SKIPS = 2
def BJ_TABLE() -> dict[str, int|str]:
	return {
		#Маленькі карти
		"<:S3:1201978742692655186>": 3, "<:S4:1127904591342731324>": 4, "<:S5:1127904594014519346>": 5, "<:S6:1127904595843219516>": 6,
		"<:C3:1201978671410462730>": 3, "<:C4:1127904432407986187>": 4, "<:C5:1127904435411099688>": 5, "<:C6:1127904436853936170>": 6,
		"<:H3:1201978720621961316>": 3, "<:H4:1127904532635070605>": 4, "<:H5:1127904535298457670>": 5, "<:H6:1127904537248813156>": 6,
		"<:D3:1201978698509860904>": 3, "<:D4:1127904487193981028>": 4, "<:D5:1127904489748320306>": 5, "<:D6:1127904491254071317>": 6,
		#Великі карти
		"<:S7:1127904598380781609>": 7, "<:S8:1127904600150790226>": 8, "<:S9:1127904602579292230>": 9, "<:S10:1127904604198277220>": 10,
		"<:C7:1127904440104534016>": 7, "<:C8:1127904441996148767>": 8, "<:C9:1127904444261072897>": 9, "<:C10:1127904446190461039>": 10,
		"<:H7:1127904539907997699>": 7, "<:H8:1127904542776897536>": 8, "<:H9:1127904546992164864>": 9, "<:H10:1127904549672329316>": 10,
		"<:D7:1127904492965347368>": 7, "<:D8:1127904495922331788>": 8, "<:D9:1127904497608425553>": 9, "<:D10:1127904500271829072>": 10,
		#Спеціальні карти
		"<:Sa:1127904607520174163>": "rnd", "<:Sk:1127904612473647114>": 10,
		"<:Ca:1127904448681881641>": "rnd", "<:Cq:1127904454767824896>": 10,
		"<:Ha:1127904551207448656>": "rnd", "<:Hk:1127904555510808596>": 10,
		"<:Da:1127904503295901807>": "rnd", "<:Dj:1127904504575184908>": 10
	}

#Економіка
MAX_MONEY = 15000
PAY_LIMIT = 7500
PAY_COOLDOWN = 60
TRADE_COOLDOWN = 30
PICK_DURABILITY = {
	"pick7": 40,
	"pick6": 40,
	"pick5": 90,
	"pick4": 65,
	"pick3": 55,
	"pick2": 35,
	"pick": 18
}


#Економічні БД
eco_db = ChrDB('data/economy/economy.chr')
jobs_db = ChrDB('data/economy/jobs.json')
items_db = ChrDB('data/economy/items.json')
pigs_db = ChrDB('data/economy/pigs.chr')
temp_db = ChrDB('data/economy/temp.chr')
#БД
card_db = ChrDB('data/card.chr')
cooldown_db = ChrDB('data/cooldown.chr')
giveaways_db = ChrDB('data/giveaways.chr')
invites_db = ChrDB('data/invites.chr')
level_db = ChrDB('data/level.chr')
other_db = ChrDB('data/other.chr')
stats_db = ChrDB('data/stats.chr')
sug_db = ChrDB('data/suggestions.chr')
voice_db = ChrDB('data/voice.chr')


#Приватки
def get_voice_perms():
	return PermissionOverwrite(
		read_messages=True, manage_channels=False,
		manage_permissions=False, manage_webhooks=False,
		create_instant_invite=False,
		connect=True, speak=True, stream=True,
		use_embedded_activities=True, use_soundboard=True,
		use_external_sounds=True, use_voice_activation=True,
		priority_speaker=False, mute_members=False,
		deafen_members=False, move_members=False,
		send_messages=True, embed_links=True,
		attach_files=True, add_reactions=True,
		use_external_emojis=True, use_external_stickers=True,
		mention_everyone=False, manage_messages=False,
		read_message_history=True, send_tts_messages=False,
		use_slash_commands=False
	)
voice_owner = PermissionOverwrite(read_messages=True, connect=True, speak=True, move_members=True, send_messages=True)
voice_member_allow = PermissionOverwrite(read_messages=True, connect=True, speak=True, send_messages=True)
voice_member_block = PermissionOverwrite(read_messages=True, connect=False, speak=False, send_messages=False)