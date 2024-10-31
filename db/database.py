import pymongo.mongo_client
import pymongo
from dotenv import load_dotenv # dotenv: ferramenta que permite carregar variáveis de ambiente
import os

load_dotenv() #Carrega as variáveis de ambiente e disponibiliza no código
#os.getenv() busca os valores das variáveis

client = pymongo.MongoClient(os.getenv("DB_CONNECTION_STRING")) 

# Tenta se conectar com o banco de dados
try:
    client.admin.command("ping")
    print("Conexão bem-sucedida!")
except pymongo.errors.OperationFailure as e:
    print(f"Erro de autenticação: {e}")

bancodedados = client["readMore_database"]
usuarios = bancodedados["usuarios"]
canais_de_texto = bancodedados["canais_boasvindas"]
livros = bancodedados["livros"]

# Função para criar uma conta para o usuário
async def novo_usuario(usuario):
    filtro = {"discord_id":usuario.id}
    # Checagem se não existe usuário com esse id do discord
    if usuarios.count_documents(filtro) == 0:
        # Criação da conta para o usuário
        conta = {
            "discord_id":usuario.id,
            "moedas":0,
            "metaDiaria":0,
            "pgsLidasDia":0,
            "livrosLidos":0,
            "leituraAtual":"nenhum"
        }
        # Inserção no banco de dados
        usuarios.insert_one(conta)
        return conta
    else:
        return False

# Cadastro dos ids dos canais de texto para boas vindas   
async def cadastro_canal_boasvindas_id(channel_id):
    guild_id = str(channel_id.guild.id)
    canais_de_texto.update_one(
        {"_id": guild_id},
        {"$set": {"canal_boasvindas": str(channel_id.id)}},
        upsert=True
    )