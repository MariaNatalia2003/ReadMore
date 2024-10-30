# Importação de bibliotecas do projeto
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv # dotenv: ferramenta que permite carregar variáveis de ambiente
import os
import asyncio

# Importação de arquivos do projeto
from db import database
from utils import help
from utils import cash
from utils import checkdaily
from utils import music

#id_do_servidor = 1275253885333930077 # Usado no servidor de testes
"""
Para testes somente no servidor de teste, utilizar 
guild = discord.Object(id=id_do_servidor),
no início de cada tree.command
"""

# Configurações do ffmpeg
ffmpeg_path = r"C:\Users\55199\Downloads\ffmpeg-master-latest-win64-gpl\ffmpeg-master-latest-win64-gpl\bin\ffmpeg.exe"
ffmpeg_options = {
    'options': '-vn -buffer_size 512k'  # O 'buffer_size' ajuda em conexões instáveis ou streams de alta latência
}

load_dotenv()

class client(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.synced = False #Nós usamos isso para o bot não sincronizar os comandos mais de uma vez

    async def on_ready(self):
        await self.wait_until_ready()
        if not self.synced: #Checar se os comandos slash foram sincronizados 
            await tree.sync() # Você também pode deixar o id do servidor em branco para aplicar em todos servidores, mas isso fará com que demore de 1~24 horas para funcionar.
            self.synced = True
        print(f"Entramos como {self.user}.")

aclient = client()
tree = app_commands.CommandTree(aclient)

@tree.command(name = 'teste', description='Testando') #Comando específico para seu servidor
async def slash2(interaction: discord.Interaction):
    await interaction.response.send_message(f"Estou funcionando!", ephemeral = True) 

#Comando para checar saldo
@tree.command(name = 'rm-cash', description = 'Veja o seu saldo no bot')
async def saldo(interaction: discord.Interaction):
    moedas = await cash.checar_saldo(interaction.user)
    await interaction.response.send_message(f"Você tem {moedas} moedas.")

# Comando de barra para /rm-help
@tree.command(name="rm-help", description="Mostra todos os comandos ou detalhes sobre um comando específico.")
@app_commands.describe(command="Nome do comando para mais informações (opcional)")
async def rm_help(interaction: discord.Interaction, command: str = None):
    if command is None:
        # Exibir lista de todos os comandos
        help_message = "**Comandos Disponíveis:**\n"
        # cmd: comando
        #desc: descrição do comando
        for cmd, desc in help.comandos_info.items():
            help_message += f"**/{cmd}** - {desc}\n"
        await interaction.response.send_message(help_message, ephemeral=True)
    else:
        # Exibir detalhes sobre o comando especificado
        cmd_info = help.comandos_info.get(command.lower())
        if cmd_info:
            await interaction.response.send_message(f"**/{command}** - {cmd_info}", ephemeral=True)
        else:
            await interaction.response.send_message(f"O comando **/{command}** não foi encontrado.", ephemeral=True)

# Comando para ver a meta diária de leitura atual
#Comando para checar saldo
@tree.command(name = 'rm-viewdailygoal', description = 'Veja sua meta diária de leitura atual')
async def metaAtual(interaction: discord.Interaction):
    metaAtual = await checkdaily.get_metaDiaria(interaction.user)
    await interaction.response.send_message(f"Sua meta de leitura atual é {metaAtual} páginas.")

# Comando de barra para /rm-checkdaily
@tree.command(name="rm-checkdaily", description="Verifica se você bateu a meta de leitura diária e atualiza seu saldo.")
@app_commands.describe(paginas="Número de páginas lidas")
@app_commands.checks.cooldown(1, 86400, key=lambda i:(i.guild_id, i.user.id)) # Coloca um cooldown no comando e só permite uma execução a cada 24 horas.
async def meta(interaction: discord.Interaction, paginas: int):
    checagem = await checkdaily.checar_metaDiaria(interaction.user, paginas)

    await cash.alterar_saldo(interaction.user, paginas)

    if checagem == 1:
        await interaction.response.send_message(f"Parabéns, {interaction.user.mention} bateu a meta de leitura com {paginas} páginas! 🎉")
    else:
        await interaction.response.send_message(f"{interaction.user.mention} leu {paginas} páginas, mas não bateu a meta de leitura. 😓")

@meta.error
async def meta_error(interaction:discord.Interaction, error:app_commands.AppCommandError):
    # Checa se o erro do comando é devido ao tempo de recarga
    if isinstance(error, app_commands.CommandOnCooldown):
        tempoRestanteSegundos = error.cooldown.get_retry_after()

        await interaction.response.send_message(f"Você só pode dar 1 checkdaily por dia. Tente em `{round(tempoRestanteSegundos/3600, 2)}` horas.", ephemeral=True) # ephemeral=True significa que só próprio usuário verá a mensagem no chat
    else:
        raise(error)
    
# Comando de barra para /rm-checkdailyupdate
@tree.command(name="rm-checkdailyupdate", description="Atualiza sua meta diária de leitura.")
@app_commands.describe(paginas="Nova meta de leitura")
async def alterar_meta(interaction: discord.Interaction, paginas: int):
    await checkdaily.alterar_metaDiaria(interaction.user, paginas)

    await interaction.response.send_message(f"Sua meta diária foi alterada para {paginas} páginas por dia.")

# Comando de barra para /rm-play <link da playlist>
@tree.command(name="rm-play", description="Toca uma playlist.")
@app_commands.describe(playlist_url="Link da playlist do Spotify")
async def play(interaction: discord.Interaction, playlist_url: str):
    await interaction.response.defer()  # Adiar a resposta de 3 segundos do Discord

    # Extraindo o ID da playlist do URL do Spotify
    playlist_id = playlist_url.split('/')[-1].split('?')[0]

    # Obtendo informações da playlist, e buscando pelo nome
    playlist_data = music.sp.playlist(playlist_id)
    playlist_name = playlist_data['name']

    results = music.sp.playlist_tracks(playlist_id)

    # Obter nomes das faixas da playlist
    tracks = [track['track']['name'] for track in results['items']]

    # Verifique se o bot já está conectado
    if interaction.guild.voice_client and interaction.guild.voice_client.is_connected():
        await interaction.guild.voice_client.disconnect()

    # Conectar ao canal de voz
    if interaction.user.voice:
        channel = interaction.user.voice.channel
        voice_client = await channel.connect()

        # Responder ao usuário que o comando foi enviado
        await interaction.followup.send(f"Iniciando a reprodução da playlist **{playlist_name}**!", ephemeral=False)

        # Reproduzir cada faixa
        for track in tracks:
            # Buscar a URL do YouTube para a faixa
            url = music.get_youtube_url(track)
            if url:
                voice_client.play(discord.FFmpegPCMAudio(executable=ffmpeg_path, source=url, **ffmpeg_options))
                while voice_client.is_playing():
                    await asyncio.sleep(1)
            else:
                await interaction.followup.send(f"Não foi possível encontrar {track} no YouTube.")
        await voice_client.disconnect()
    else:
        await interaction.followup.send("Você precisa estar em um canal de voz para usar este comando.")

# Comando de barra para /rm-pause
@tree.command(name="rm-pause", description="Pausa a reprodução atual.")
async def pause(interaction: discord.Interaction):
    # Verifique se o bot está conectado e tocando algo
    voice_client = interaction.guild.voice_client
    if voice_client and voice_client.is_playing():
        voice_client.pause()  # Pausa a música
        await interaction.followup.send("Reprodução pausada. ⏸️")
    else:
        await interaction.followup.send("Não há nenhuma música tocando no momento para pausar.", ephemeral=False)

aclient.run(os.getenv("DISCORD_TOKEN"))