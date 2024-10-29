# Importação de bibliotecas
import pymongo.mongo_client
import pymongo
from dotenv import load_dotenv # dotenv: ferramenta que permite carregar variáveis de ambiente

# Importação de arquivos do projeto
from db import database

load_dotenv()

async def checar_saldo(usuario):
    await database.novo_usuario(usuario) #roda a função novo_usuario para checar se a pessoa tem uma conta, se não tiver cria uma

    filtro = {"discord_id":usuario.id} #filtra o usuário pelo id do discord para identificar qual é o usuário
    resultado = database.usuarios.find(filtro)

    return resultado.__getitem__(0)["moedas"]

async def alterar_saldo(usuario, quantidade):
    await database.novo_usuario(usuario) # Cria uma conta para o usuário no banco de dados

    moedas_atuais = await checar_saldo(usuario)

    filtro = {"discord_id":usuario.id}
    relacao = { "$set": { # $set é uma função pra mudar algo no banco de dados
        "moedas": moedas_atuais+quantidade
    }}

    database.usuarios.update_one(filtro,relacao) #funcao pra alterar um usuario do banco
