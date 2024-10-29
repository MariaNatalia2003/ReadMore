# Importação de bibliotecas
import pymongo.mongo_client
import pymongo
from dotenv import load_dotenv # dotenv: ferramenta que permite carregar variáveis de ambiente

# Importação de arquivos do projeto
from db import database
from utils import cash

load_dotenv()

# Get que retorna a meta de leitura diária do usuário
async def get_metaDiaria(usuario):
    await database.novo_usuario(usuario) #roda a função novo_usuario para checar se a pessoa tem uma conta, se não tiver cria uma

    filtro = {"discord_id":usuario.id} #filtra o usuário pelo id do discord para identificar qual é o usuário
    resultado = list(database.usuarios.find(filtro)) # Converte para lista para facilitar a busca

    if resultado: # Checa se o resultado tem dados
        metaDiaria = resultado[0].get("metaDiaria", 0)  # Obtém metaDiaria ou usa 0 como padrão

        # Se a metaDiaria diaria do usuário não existir, cria na conta do usuário no MongoDB
        if metaDiaria is None:
            relacao = { "$set": { # $set é uma função pra mudar algo no banco de dados
                "metaDiaria":0
            }}
            database.usuarios.update_one(filtro,relacao) #funcao pra alterar um usuario do banco

            return 0
        else:
            return metaDiaria
    else:
        # Lógica adicional, caso o resultado esteja vazio
        relacao = { "$set": { # $set é uma função pra mudar algo no banco de dados
            "metaDiaria":0
        }}
        database.usuarios.update_one(filtro,relacao) #funcao pra alterar um usuario do banco

        return 0

# Função para alterar a meta diária de leitura
async def alterar_metaDiaria(usuario, novaMeta):
    await database.novo_usuario(usuario) # Cria uma conta para o usuário no banco de dados

    filtro = {"discord_id":usuario.id}
    relacao = { "$set": { # $set é uma função pra mudar algo no banco de dados
        "metaDiaria": novaMeta
    }}

    database.usuarios.update_one(filtro,relacao) #funcao pra alterar um usuario do banco

# Função para checar se o usuário bateu a meta diária de leitura
async def checar_metaDiaria(usuario, pgsLidas):
    await database.novo_usuario(usuario) # Cria uma conta para o usuário no banco de dados

    filtro = {"discord_id":usuario.id}
    metaDiaria = await get_metaDiaria(usuario)

    relacao = { "$set": { # $set é uma função pra mudar algo no banco de dados
        "pgsLidasDia": pgsLidas
    }}

    database.usuarios.update_one(filtro,relacao) #funcao pra alterar um usuario do banco

    # Checagem se o usuário bateu a meta diária
    if pgsLidas >= metaDiaria:
        return 1
    else:
        return 0
