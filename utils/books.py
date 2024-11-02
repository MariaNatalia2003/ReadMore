# Importação de bibliotecas
import requests
from googleapiclient.discovery import build
from dotenv import load_dotenv # dotenv: ferramenta que permite carregar variáveis de ambiente
import os
import random
from urllib.parse import quote # Biblioteca para codificar o gênero da busca por gênero

# Importação de arquivos do projeto
from db import database

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
        return data['items']
    else:
        return []
    
# Função auxiliar para mostrar as informações de um livro
async def mostrar_livros(data, index):
    livro = data[index]
    titulo = livro['volumeInfo'].get('title', 'Título não encontrado')
    autores = livro['volumeInfo'].get('authors', ['Autor desconhecido'])
    numero_paginas = livro['volumeInfo'].get('pageCount', 'Número de páginas não disponível')
    generos = livro['volumeInfo'].get('categories', ['Gênero não disponível'])

    return titulo, autores, numero_paginas, generos

# Função para get na leitura atual do usuário no banco de dados    
async def checar_leituraAtual(usuario):
    await database.novo_usuario(usuario) #roda a função novo_usuario para checar se a pessoa tem uma conta, se não tiver cria uma

    filtro = {"discord_id":usuario.id} #filtra o usuário pelo id do discord para identificar qual é o usuário
    resultado = database.usuarios.find(filtro)

    resultado = list(database.usuarios.find(filtro)) # Converte para lista para facilitar a busca

    if resultado: # Checa se o resultado tem dados
        leituraAtual = resultado[0].get("leituraAtual", "nenhum")  # Obtém leituraAtual ou usa "nenhum" como padrão

        # Se a leituraAtual do usuário não existir, cria na conta do usuário no MongoDB
        if leituraAtual is None:
            relacao = { "$set": { # $set é uma função pra mudar algo no banco de dados
                "leituraAtual":"nenhum"
            }}
            database.usuarios.update_one(filtro,relacao) #funcao pra alterar um usuario do banco

            return "nenhum"
        else:
            return leituraAtual
    else:
        # Lógica adicional, caso o resultado esteja vazio
        relacao = { "$set": { # $set é uma função pra mudar algo no banco de dados
            "leituraAtual":"nenhum"
        }}
        database.usuarios.update_one(filtro,relacao) #funcao pra alterar um usuario do banco

        return "nenhum"
    
# Função para get na leitura atual do usuário no banco de dados    
async def checar_livrosLidos(usuario):
    await database.novo_usuario(usuario) #roda a função novo_usuario para checar se a pessoa tem uma conta, se não tiver cria uma

    filtro = {"discord_id":usuario.id} #filtra o usuário pelo id do discord para identificar qual é o usuário
    resultado = database.usuarios.find(filtro)

    resultado = list(database.usuarios.find(filtro)) # Converte para lista para facilitar a busca

    if resultado: # Checa se o resultado tem dados
        livrosLidos = resultado[0].get("livrosLidos", 0)  # Obtém leituraAtual ou usa "nenhum" como padrão

        # Se a leituraAtual do usuário não existir, cria na conta do usuário no MongoDB
        if livrosLidos is None:
            relacao = { "$set": { # $set é uma função pra mudar algo no banco de dados
                "livrosLidos":0
            }}
            database.usuarios.update_one(filtro,relacao) #funcao pra alterar um usuario do banco

            return 0
        else:
            return livrosLidos
    else:
        # Lógica adicional, caso o resultado esteja vazio
        relacao = { "$set": { # $set é uma função pra mudar algo no banco de dados
            "livrosLidos":0
        }}
        database.usuarios.update_one(filtro,relacao) #funcao pra alterar um usuario do banco

        return 0
    
async def terminar_livro(usuario):
    await database.novo_usuario(usuario) # Cria uma conta para o usuário no banco de dados

    livrosLidosAtuais = await checar_livrosLidos(usuario)

    filtro = {"discord_id":usuario.id}
    relacao = { "$set": { # $set é uma função pra mudar algo no banco de dados
        "livrosLidos": livrosLidosAtuais+1
    }}
    relacao2 = { "$set": { # $set é uma função pra mudar algo no banco de dados
        "leituraAtual": "nenhum"
    }}

    database.usuarios.update_one(filtro,relacao) #funcao pra alterar um usuario do banco
    database.usuarios.update_one(filtro,relacao2)

# Função de busca de livros por gênero
async def buscar_livros_por_genero(genero):
    # Codificação do gênero
    genero_codificado = quote(genero)

    # Define o endpoint da API do Google Books e os parâmetros
    url = "https://www.googleapis.com/books/v1/volumes"
    parametros = {
        'q': f'subject:{genero_codificado}',  # Filtro pela categoria/gênero
        #'maxResults': 50,  # Limita o número de resultados - causou erro de parâmetro inválido
        'printType': 'books',  # Especifica que quer apenas livros
        'langRestrict': 'pt'       # Restrição de idioma para português
    }

    resposta = requests.get(url, params=parametros)
    print(resposta)
    print(resposta.text)

    if resposta.status_code == 200:
        dados = resposta.json()
        livros_generos = {}

        
        # Verifica se há itens suficientes para selecionar aleatoriamente
        itens = dados.get('items', [])
        if len(itens) >= 5:
            livros_aleatorios = random.sample(itens, k=5)
            print(livros_aleatorios)
        else:
            livros_aleatorios = itens  # Se houver menos de 5, utiliza todos os disponíveis
            print(livros_aleatorios)
        

        # Itera sobre os livros retornados e adiciona ao dicionário
        for dado in livros_aleatorios:
            titulo = dado['volumeInfo'].get('title', 'Título não encontrado')
            autores = dado['volumeInfo'].get('authors', ['Autor desconhecido'])
            livros_generos[titulo] = ", ".join(autores)

        return livros_generos
    else:
        return 400
