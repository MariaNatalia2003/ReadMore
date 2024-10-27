import discord
import asyncio
from googleapiclient.discovery import build
from dotenv import load_dotenv # dotenv: ferramenta que permite carregar variáveis de ambiente
import os

load_dotenv() #Carrega as variáveis de ambiente e disponibiliza no código

# Integração com a API Google Books
API_KEY = os.getenv("API_key")

books_service = build('books', 'v1', developerKey=API_KEY) # Primeiro parâmetro é o service name, o nome da API sendo usada