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
def get_youtube_url(track_name, track_singer):
    ydl_opts = {'format': 'bestaudio', 'noplaylist': 'True'}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            results = ydl.extract_info(f"ytsearch:{track_name} {track_singer}", download=False)['entries'][0]
            return results['url']
        except Exception as e:
            print(f"Erro ao buscar {track_name}: {e}")
            return None
        
# Função para obter nomes dos artistas de uma playlist
def get_artists_from_playlist(playlist_id):
    # Obtenha informações da playlist
    playlist_tracks = sp.playlist_tracks(playlist_id)

    # Lista para armazenar os nomes dos artistas
    artist_names = []

    # Iterar pelas faixas da playlist
    for item in playlist_tracks['items']:
        track = item['track']
        if track:
            # Iterar pelos artistas da faixa
            for artist in track['artists']:
                artist_names.append(artist['name'])

    return artist_names