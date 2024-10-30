# Importação de bibliotecas
import discord
from discord.ext import commands
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import yt_dlp
import os
from dotenv import load_dotenv
import asyncio

load_dotenv()

client_credentials_manager = SpotifyClientCredentials(client_id=os.getenv("SPOTIFY_CLIENT_ID"), client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"))
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

# Função para buscar o URL do YouTube para cada faixa
def get_youtube_url(track_name):
    ydl_opts = {'format': 'bestaudio', 'noplaylist': 'True'}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            results = ydl.extract_info(f"ytsearch:{track_name}", download=False)['entries'][0]
            return results['url']
        except Exception as e:
            print(f"Erro ao buscar {track_name}: {e}")
            return None