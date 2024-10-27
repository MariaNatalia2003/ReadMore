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

# Função para criar uma conta para o usuário
async def novo_usuario(usuario):
    filtro = {"discord_id":usuario.id}
    # Checagem se não existe usuário com esse id do discord
    if usuarios.count_documents(filtro) == 0:
        # Criação da conta para o usuário
        conta = {
            "discord_id":usuario.id,
            "moedas":0
        }
        # Inserção no banco de dados
        usuarios.insert_one(conta)
        return conta
    else:
        return False
    
async def checar_saldo(usuario):
    await novo_usuario(usuario) #roda a função novo_usuario para checar se a pessoa tem uma conta, se não tiver cria uma

    filtro = {"discord_id":usuario.id} #filtra o usuário pelo id do discord para identificar qual é o usuário
    resultado = usuarios.find(filtro)

    return resultado.__getitem__(0)["moedas"]

async def alterar_saldo(usuario, quantidade):
    await novo_usuario(usuario)

    moedas_atuais = await checar_saldo(usuario)

    filtro = {"discord_id":usuario.id}
    relacao = { "$set": { # $set é uma função pra mudar algo no banco de dados
        "moedas": moedas_atuais+quantidade
    }}

    usuarios.update_one(filtro,relacao) #funcao pra alterar um usuario do banco
