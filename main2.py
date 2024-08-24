from utils import *
import chrdb

class ChromaTyan(commands.Bot):
	def __init__(self):
		cmd = commands.CommandSyncFlags.default()
		cmd.sync_commands = True
		super().__init__(command_prefix=["cet!"], intents=disnake.Intents.all(), command_sync_flags=cmd, help_command=None)

	def reload_cogs(self, folder:str):
		folder = folder.replace("\\","/").replace(".","").strip("/")
		for file in os.listdir(folder):
			if file.endswith(".py") and not file.startswith("_"):
				try: self.unload_extension(f"{folder.replace('/','.')}.{file[:-3]}")
				except: pass
				try: self.load_extension(f"{folder.replace('/','.')}.{file[:-3]}")
				except: pass
				print("Successfully loaded cog: "+file)

	async def on_ready(self):
		print("\n" * 25)
		print(f"#################################\n")
		print(f"Бот {self.user} був запущений!")
		print(f"ID: {self.user.id}")
		print(f"Disnake: {disnake.__version__}")
		print(f"ChrDB: {chrdb.__version__}\n")
		print(f"#################################\n")
		await self.change_presence(activity=disnake.Streaming(name="Хрома", url="https://www.twitch.tv/dasalex_ua"))

	async def on_message(self, message:disnake.Message):
		await self.process_commands(message)


if __name__ == "__main__":
	bot = ChromaTyan()
	bot.reload_cogs("cogs/ai")
	bot.run(os.getenv('TOKEN_CHROMATYAN'))