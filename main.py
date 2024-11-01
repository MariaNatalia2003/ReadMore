# Importação de bibliotecas do projeto
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv # dotenv: ferramenta que permite carregar variáveis de ambiente
import os
import asyncio
from typing import Optional # Biblioteca para deixar alguns parâmetros dos comando opicionais

# Importação de arquivos do projeto
from db import database
from utils import help, cash, checkdaily, music, books

"""
from utils import cash
from utils import checkdaily
from utils import music
from utils import books
"""

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

# Variáveis globais
# Controle de pausa das músicas do comando /rm-play
is_paused = False
is_playing = False

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

"""
@tree.command(name = 'teste', description='Testando') #Comando específico para seu servidor
async def slash2(interaction: discord.Interaction):
    await interaction.response.send_message(f"Estou funcionando!", ephemeral = True) 
"""

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
        # desc: descrição do comando
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

# Comando de barra para /rm-viewdailygoal
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

# Comando de barra para /rm-pause
@tree.command(name="rm-pause", description="Pausa a reprodução atual.")
async def pause(interaction: discord.Interaction):
    global is_paused

    # Verifique se o bot está conectado e tocando algo
    voice_client = interaction.guild.voice_client
    if voice_client and voice_client.is_playing():
        voice_client.pause()  # Pausa a música
        is_paused = True # aciona a flag de pause
        await interaction.response.send_message("Reprodução pausada. ⏸️")
    else:
        await interaction.response.send_message("Não há nenhuma música tocando no momento para pausar.", ephemeral=False)

# Comando de barra para /rm-stop
@tree.command(name="rm-stop", description="Interrompe a reprodução atual.")
async def stop(interaction: discord.Interaction):
    global is_playing

    is_playing = False # Atribui false na flag para interromper que o comando /rm-play continue sendo executado

    voice_client = interaction.guild.voice_client

    if voice_client and voice_client.is_connected():
        if voice_client and voice_client.is_playing():
            voice_client.stop()  # Para a reprodução
            await interaction.response.send_message("Música interrompida.")
        else:
            await interaction.response.send_message("Não há nenhuma música tocando no momento.")

        # Desconectar do canal de voz
        await voice_client.disconnect()
    else:
        await interaction.response.send_message("O bot não está conectado a um canal de voz.")

# Comando de barra para /rm-continue
@tree.command(name="rm-continue", description="Continua a reprodução de música.")
async def continue_playing(interaction: discord.Interaction):
    global is_paused

    voice_client = interaction.guild.voice_client
    if voice_client and voice_client.is_paused():
        voice_client.resume()  # Continua a reprodução
        is_paused = False # desaciona a flag de pause
        await interaction.response.send_message("Música retomada.")
    else:
        await interaction.response.send_message("Não há nenhuma música pausada.")

# Comando de barra para /rm-skip
@tree.command(name="rm-skip", description="Pula para a próxima música.")
async def skip(interaction: discord.Interaction):
    voice_client = interaction.guild.voice_client
    if voice_client and voice_client.is_playing():
        voice_client.stop()  # Para a música atual, permitindo que o loop continue para a próxima música
        await interaction.response.send_message("Música pulada.")
    else:
        await interaction.response.send_message("Não há nenhuma música tocando no momento.")

# Comando de barra para /rm-play <link da playlist>
@tree.command(name="rm-play", description="Toca uma playlist.")
@app_commands.describe(playlist_url="Link da playlist do Spotify")
async def play(interaction: discord.Interaction, playlist_url: Optional[str] = None):
    global is_paused, is_playing

    is_playing = True

    await interaction.response.defer()  # Adiar a resposta de 3 segundos do Discord

    if playlist_url is None:
        playlist_url = 'https://open.spotify.com/playlist/33uCDnCmt3gUhDC2niZvqn?si=7229822801254248'
    
    # Extraindo o ID da playlist do URL do Spotify
    playlist_id = playlist_url.split('/')[-1].split('?')[0]

    # Obtendo informações da playlist, e buscando pelo nome
    playlist_data = music.sp.playlist(playlist_id)
    playlist_name = playlist_data['name']

    results = music.sp.playlist_tracks(playlist_id)

    # Obter detalhes das faixas e dos artistas
    tracks_info = results['items']
    
    # Montar uma lista de faixas com seus artistas
    tracks_with_artists = []
    for item in tracks_info:
        track = item['track']
        if track:
            track_name = track['name']
            artists = ", ".join(artist['name'] for artist in track['artists'])  # Obter os nomes dos artistas da track
            tracks_with_artists.append((track_name, artists))

    # Verifique se o bot já está conectado
    if interaction.guild.voice_client and interaction.guild.voice_client.is_connected():
        await interaction.guild.voice_client.disconnect()

    # Conectar ao canal de voz
    if interaction.user.voice:
        channel = interaction.user.voice.channel
        voice_client = await channel.connect()

        # Responder ao usuário que o comando foi enviado
        await interaction.followup.send(f"Iniciando a reprodução da playlist **{playlist_name}**!", ephemeral=False)

        # Reprodução de cada track
        for track_name, artists in tracks_with_artists:
            if not is_playing: # Verifica se a conexão foi interrompida com o comando /rm-stop
                break

            # Buscar a URL do YouTube para a faixa
            url = music.get_youtube_url(track_name, artists)
            if url:
                voice_client.play(discord.FFmpegPCMAudio(executable=ffmpeg_path, source=url, **ffmpeg_options))
                await interaction.followup.send(f"Tocando: **{track_name}** por **{artists}**")
                
                while (voice_client.is_playing() or is_paused) and is_playing: # Verifica se a música está tocando ou pausada e se a flag is_playing ainda é True
                    await asyncio.sleep(1) # Suspende a execução do código por 1s antes de entrar na próxima iteração do loop
            else:
                await interaction.followup.send(f"Não foi possível encontrar {track} no YouTube.")
        await voice_client.disconnect()
        is_playing = False
    else:
        await interaction.followup.send("Você precisa estar em um canal de voz para usar este comando.")

# Comando para definir qual vai ser o canal para as mensagens de boas vindas
@tree.command(name="rm-welcomechannel", description="Define um canal de texto para as mensagens de boas-vindas.")
@commands.has_permissions(manage_guild=True)
async def set_canal_boasvindas(interaction: discord.Interaction, channel: discord.TextChannel):
    await database.cadastro_canal_boasvindas_id(channel)
    await interaction.response.send_message(f"Canal de boas-vindas definido para {channel.mention}.")

@aclient.event
async def on_member_join(member):
    print(f"{member.name} entrou no servidor.")  # Adicionado para debug
    guild_id = str(member.guild.id)
    channel_data = database.canais_de_texto.find_one({"_id": guild_id})

    if channel_data and "canal_boasvindas" in channel_data:
        channel_id = int(channel_data["canal_boasvindas"])
        channel = aclient.get_channel(channel_id)
        print(f"ID do canal de boas-vindas: {channel.id if channel else 'não encontrado'}")  # Para debug
        if channel:
            try:
                await channel.send(f"Bem-vindo(a), {member.mention}! Esperamos que você aproveite sua estadia!")
                print("Mensagem de boas-vindas enviada.")  # Para confirmar que a mensagem foi enviada
            except discord.Forbidden:
                print("O bot não tem permissão para enviar mensagens neste canal.")
            except discord.HTTPException as e:
                print(f"Erro ao enviar mensagem: {e}")

# Comando para iniciar a busca pelo livro
@tree.command(name="rm-startbook", description="Atualiza sua leitura atual.")
@app_commands.describe(nome_do_livro="Nome do livro que você deseja buscar.")
async def start_book(interaction: discord.Interaction, nome_do_livro: str):
    await interaction.response.defer()  # Adiar a resposta para evitar o timeout

    # Chama a função de busca
    titulo, autores, numero_paginas, generos = await books.buscar_livro(nome_do_livro)

    if titulo:
        mensagem = f"Você se refere a **{titulo}** de **{', '.join(autores)}**?\nNúmero de páginas: **{numero_paginas}**\nGêneros: **{', '.join(generos)}**?"
        
        # Enviar a mensagem para o usuário
        msg = await interaction.followup.send(mensagem)

        # Reagir com emojis
        await msg.add_reaction("✅")  # Emoji positivo
        await msg.add_reaction("❌")  # Emoji negativo

        # Função interna para verificar reações
        def check(reaction, user):
            return user == interaction.user and str(reaction.emoji) in ["✅", "❌"] and reaction.message.id == msg.id

        try:
            reaction, user = await aclient.wait_for("reaction_add", timeout=30.0, check=check)

            if str(reaction.emoji) == "✅":
                # Salvar informações do livro no MongoDB
                livro_info = {
                    'titulo': titulo,
                    'autores': autores,
                    'numero_paginas': numero_paginas,
                    'generos': generos,
                    'usuario_id': str(interaction.user.id),
                    'user_name': interaction.user.name
                }
                database.livros.insert_one(livro_info)

                # Salvar nome do livro na conta do usuário
                database.usuarios.update_one(
                    {'user_id': str(interaction.user.id)},
                    {'$set': {'leituraAtual': titulo}},
                    upsert=True
                )

                await interaction.followup.send(f"Livro **{titulo}** salvo como sua leitura atual!")
            elif str(reaction.emoji) == "❌":
                await interaction.followup.send("Buscando um livro diferente... Tente novamente.")
                # Chame a função novamente ou implemente a lógica de busca nova

        except asyncio.TimeoutError:
            await interaction.followup.send("Você não reagiu a tempo.")

    else:
        await interaction.followup.send("Nenhum livro encontrado com esse nome.")

aclient.run(os.getenv("DISCORD_TOKEN"))