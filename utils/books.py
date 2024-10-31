import discord
import asyncio
import requests
from googleapiclient.discovery import build
from dotenv import load_dotenv # dotenv: ferramenta que permite carregar variáveis de ambiente
import os

load_dotenv() #Carrega as variáveis de ambiente e disponibiliza no código

# Integração com a API Google Books
API_KEY = os.getenv("API_key")

books_service = build('books', 'v1', developerKey=API_KEY) # Primeiro parâmetro é o service name, o nome da API sendo usada

# Função para buscar o livro na API do Google Books
async def buscar_livro(nome_do_livro):
    url = f"https://www.googleapis.com/books/v1/volumes?q={nome_do_livro}"
    response = requests.get(url)
    data = response.json()

    if 'items' in data:
        # Pegando o primeiro livro da lista de resultados
        livro = data['items'][0]
        titulo = livro['volumeInfo'].get('title', 'Título não encontrado')
        autores = livro['volumeInfo'].get('authors', ['Autor desconhecido'])
        numero_paginas = livro['volumeInfo'].get('pageCount', 'Número de páginas não disponível')
        generos = livro['volumeInfo'].get('categories', ['Gênero não disponível'])

        return titulo, autores, numero_paginas, generos
    else:
        return None, None, None, None