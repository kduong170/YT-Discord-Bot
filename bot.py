import discord
import youtube_dl
import asyncio
from discord.ext import commands
import random

bot = commands.Bot(command_prefix='!', intents = discord.Intents.all())
discord.opus.load_opus('/opt/homebrew/Cellar/opus/1.3.1/lib/libopus.0.dylib')

# Reads bot token from text file
fileOpen = open('token.txt', 'r')
token = fileOpen.readline()
fileOpen.close()

# Suppress noise about console usage from errors
youtube_dl.utils.bug_reports_message = lambda: ''


ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',  # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'options': '-vn',
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename,executable = '/Library/Frameworks/Python.framework/Versions/3.11/bin/ffmpeg', **ffmpeg_options), data=data)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')

@bot.command(help = 'This is a test')
async def test(client):
    if client.channel.name == 'bot':
        await client.send('command gotten')

@bot.command(help = 'Have bot join vc')
async def join(client):
    if not client.message.author.voice:
        await client.send('{} is not in a voice chat. Please join a voice chat!'.format(client.message.author.name))
        return False
    else:
        channel = client.message.author.voice.channel
        await channel.connect()
        return True

@bot.command(help = 'Have bot leave vc')
async def leave(client):
    voice = client.message.guild.voice_client
    if voice.is_connected():
        await voice.disconnect()
    else:
        await client.send('ytvd is not connected to a voice chat')

@bot.command(help = 'Have bot pause music')
async def pause(client):
    voice = client.message.guild.voice_client
    if voice.is_playing():
        voice.pause()
    else:
        await client.send('ytvid has nothing to play!')

@bot.command(help = 'Have bot resume music')
async def play(client):
    voice = client.message.guild.voice_client
    if voice.is_paused():
        voice.resume()
    else:
        await client.send('ytvid has nothing to pause!')
        
@bot.command(help = 'Plays vid provided url')
async def str(client, url):
#Plays from a url (almost anything youtube_dl supports)
    async with client.typing():
        player = await YTDLSource.from_url(url, loop=client.bot.loop)
        client.voice_client.play(player, after=lambda e: print(f'Player error: {e}') if e else None)

    await client.send(f'Now playing: {player.title}')

@str.before_invoke
async def ensure_voice(client):
    voice = client.message.guild.voice_client
    if voice is None:
        if client.author.voice:
            await client.author.voice.channel.connect()
        else:
            await client.send("You are not connected to a voice channel.")
    elif voice.is_playing():
            await voice.disconnect()
            await client.message.author.voice.channel.connect()
            
@bot.command(help = 'Shutdowns bot')
@commands.is_owner()
async def shutdown(context):
    exit()

bot.run(token)


