import os
import discord
from discord.ext import commands
import requests
import json
from dotenv import load_dotenv
import logging
from datetime import datetime
import difflib

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("discord_jira_bot")

# Carregar variáveis de ambiente
load_dotenv()

# Configurações do Discord
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')

# Configurações do Jira
JIRA_URL = os.getenv('JIRA_URL')
JIRA_USERNAME = os.getenv('JIRA_USERNAME')
JIRA_API_TOKEN = os.getenv('JIRA_API_TOKEN')
JIRA_PROJECT = 'NAME'  # Projeto específico mencionado pelo usuário

# Configuração do bot Discord
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Função para autenticação no Jira
def get_jira_auth():
    return (JIRA_USERNAME, JIRA_API_TOKEN)

# Função para fazer requisições à API do Jira
def jira_request(endpoint, method='GET', data=None):
    url = f"{JIRA_URL}/rest/api/2/{endpoint}"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    try:
        if method == 'GET':
            response = requests.get(url, auth=get_jira_auth(), headers=headers)
        elif method == 'POST':
            response = requests.post(url, auth=get_jira_auth(), headers=headers, json=data)
        
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Erro na requisição ao Jira: {e}")
        return None

# Função para buscar tarefas do projeto NAME
def get_NAME_tasks(max_results=50):
    jql_query = f'project = {JIRA_PROJECT} ORDER BY created DESC'
    endpoint = f"search?jql={jql_query}&maxResults={max_results}"
    return jira_request(endpoint)

# Função para buscar detalhes de uma tarefa específica
def get_task_details(issue_key):
    endpoint = f"issue/{issue_key}"
    return jira_request(endpoint)

# Função para buscar tarefas por status
def get_tasks_by_status(status, max_results=20):
    jql_query = f'project = {JIRA_PROJECT} AND status = "{status}" ORDER BY created DESC'
    endpoint = f"search?jql={jql_query}&maxResults={max_results}"
    return jira_request(endpoint)

# Função para encontrar tarefas similares com base no título e descrição
def find_similar_tasks(issue_key, similarity_threshold=0.6, max_results=10):
    # Obter detalhes da tarefa de referência
    reference_task = get_task_details(issue_key)
    if not reference_task:
        return None
    
    # Extrair título e descrição da tarefa de referência
    ref_summary = reference_task.get('fields', {}).get('summary', '')
    ref_description = reference_task.get('fields', {}).get('description', '') or ''
    ref_text = f"{ref_summary} {ref_description}"
    
    # Buscar todas as tarefas do projeto
    all_tasks = get_NAME_tasks(100)
    if not all_tasks or 'issues' not in all_tasks:
        return None
    
    similar_tasks = []
    
    # Comparar cada tarefa com a tarefa de referência
    for task in all_tasks['issues']:
        # Pular a própria tarefa
        if task['key'] == issue_key:
            continue
        
        task_summary = task.get('fields', {}).get('summary', '')
        task_description = task.get('fields', {}).get('description', '') or ''
        task_text = f"{task_summary} {task_description}"
        
        # Calcular similaridade usando difflib
        similarity = difflib.SequenceMatcher(None, ref_text, task_text).ratio()
        
        if similarity >= similarity_threshold:
            similar_tasks.append({
                'key': task['key'],
                'summary': task_summary,
                'similarity': similarity
            })
    
    # Ordenar por similaridade (mais similar primeiro)
    similar_tasks.sort(key=lambda x: x['similarity'], reverse=True)
    
    # Retornar apenas os top N resultados
    return similar_tasks[:max_results]

# Evento quando o bot está pronto
@bot.event
async def on_ready():
    logger.info(f'{bot.user.name} conectado ao Discord!')
    await bot.change_presence(activity=discord.Activity(
        type=discord.ActivityType.watching, 
        name="tarefas do Jira"
    ))

# Comando para listar tarefas do projeto NAME
@bot.command(name='tarefas', help='Lista as tarefas recentes do projeto NAME')
async def list_tasks(ctx, quantidade: int = 10):
    await ctx.send(f"🔍 Buscando as {quantidade} tarefas mais recentes do projeto NAME...")
    
    tasks = get_NAME_tasks(quantidade)
    
    if not tasks or 'issues' not in tasks or not tasks['issues']:
        await ctx.send("❌ Não foi possível encontrar tarefas ou ocorreu um erro na consulta.")
        return
    
    embed = discord.Embed(
        title=f"Tarefas do Projeto {JIRA_PROJECT}",
        description=f"Listando as {len(tasks['issues'])} tarefas mais recentes",
        color=discord.Color.blue(),
        timestamp=datetime.now()
    )
    
    for issue in tasks['issues']:
        issue_key = issue['key']
        summary = issue['fields']['summary']
        status = issue['fields']['status']['name']
        assignee = issue['fields'].get('assignee', {})
        assignee_name = assignee.get('displayName', 'Não atribuído') if assignee else 'Não atribuído'
        
        embed.add_field(
            name=f"{issue_key}: {summary}",
            value=f"**Status:** {status}\n**Responsável:** {assignee_name}",
            inline=False
        )
    
    embed.set_footer(text=f"Solicitado por {ctx.author.display_name}")
    await ctx.send(embed=embed)

# Comando para verificar o status de uma tarefa
@bot.command(name='status', help='Verifica o status de uma tarefa específica')
async def check_status(ctx, issue_key: str):
    if not issue_key.startswith(f"{JIRA_PROJECT}-"):
        issue_key = f"{JIRA_PROJECT}-{issue_key}"
    
    await ctx.send(f"🔍 Buscando informações da tarefa {issue_key}...")
    
    task = get_task_details(issue_key)
    
    if not task or 'fields' not in task:
        await ctx.send(f"❌ Não foi possível encontrar a tarefa {issue_key} ou ocorreu um erro na consulta.")
        return
    
    fields = task['fields']
    summary = fields['summary']
    status = fields['status']['name']
    description = fields.get('description', 'Sem descrição')
    assignee = fields.get('assignee', {})
    assignee_name = assignee.get('displayName', 'Não atribuído') if assignee else 'Não atribuído'
    created = fields.get('created', '').split('T')[0] if fields.get('created') else 'Data desconhecida'
    
    embed = discord.Embed(
        title=f"{issue_key}: {summary}",
        description=description[:2000] + ('...' if len(description) > 2000 else ''),
        color=discord.Color.green(),
        timestamp=datetime.now()
    )
    
    embed.add_field(name="Status", value=status, inline=True)
    embed.add_field(name="Responsável", value=assignee_name, inline=True)
    embed.add_field(name="Criado em", value=created, inline=True)
    
    # Adicionar link para a tarefa no Jira
    task_url = f"{JIRA_URL}/browse/{issue_key}"
    embed.add_field(name="Link", value=f"[Abrir no Jira]({task_url})", inline=False)
    
    embed.set_footer(text=f"Solicitado por {ctx.author.display_name}")
    await ctx.send(embed=embed)

# Comando para listar tarefas por status
@bot.command(name='por_status', help='Lista tarefas com um status específico')
async def tasks_by_status(ctx, status: str, quantidade: int = 10):
    await ctx.send(f"🔍 Buscando até {quantidade} tarefas com status '{status}'...")
    
    tasks = get_tasks_by_status(status, quantidade)
    
    if not tasks or 'issues' not in tasks or not tasks['issues']:
        await ctx.send(f"❌ Não foi possível encontrar tarefas com status '{status}' ou ocorreu um erro na consulta.")
        return
    
    embed = discord.Embed(
        title=f"Tarefas com Status: {status}",
        description=f"Encontradas {len(tasks['issues'])} tarefas",
        color=discord.Color.gold(),
        timestamp=datetime.now()
    )
    
    for issue in tasks['issues']:
        issue_key = issue['key']
        summary = issue['fields']['summary']
        assignee = issue['fields'].get('assignee', {})
        assignee_name = assignee.get('displayName', 'Não atribuído') if assignee else 'Não atribuído'
        
        embed.add_field(
            name=f"{issue_key}: {summary}",
            value=f"**Responsável:** {assignee_name}",
            inline=False
        )
    
    embed.set_footer(text=f"Solicitado por {ctx.author.display_name}")
    await ctx.send(embed=embed)

# Comando para encontrar tarefas similares
@bot.command(name='similares', help='Encontra tarefas similares a uma tarefa específica')
async def find_similar(ctx, issue_key: str, threshold: float = 0.6, quantidade: int = 5):
    if not issue_key.startswith(f"{JIRA_PROJECT}-"):
        issue_key = f"{JIRA_PROJECT}-{issue_key}"
    
    await ctx.send(f"🔍 Buscando tarefas similares a {issue_key}...")
    
    similar_tasks = find_similar_tasks(issue_key, threshold, quantidade)
    
    if not similar_tasks:
        await ctx.send(f"❌ Não foi possível encontrar tarefas similares a {issue_key} ou ocorreu um erro na consulta.")
        return
    
    # Obter detalhes da tarefa de referência
    reference_task = get_task_details(issue_key)
    ref_summary = reference_task.get('fields', {}).get('summary', 'Tarefa desconhecida')
    
    embed = discord.Embed(
        title=f"Tarefas Similares a {issue_key}",
        description=f"Tarefa de referência: **{ref_summary}**\nEncontradas {len(similar_tasks)} tarefas similares",
        color=discord.Color.purple(),
        timestamp=datetime.now()
    )
    
    for task in similar_tasks:
        similarity_percentage = int(task['similarity'] * 100)
        embed.add_field(
            name=f"{task['key']}: {task['summary']}",
            value=f"**Similaridade:** {similarity_percentage}%",
            inline=False
        )
    
    embed.set_footer(text=f"Solicitado por {ctx.author.display_name}")
    await ctx.send(embed=embed)

# Comando de ajuda personalizado
@bot.command(name='jira_ajuda', help='Mostra os comandos disponíveis para interação com o Jira')
async def jira_help(ctx):
    embed = discord.Embed(
        title="Comandos do Bot Jira",
        description="Lista de comandos disponíveis para interação com o Jira",
        color=discord.Color.blue(),
        timestamp=datetime.now()
    )
    
    embed.add_field(
        name="!tarefas [quantidade]",
        value="Lista as tarefas mais recentes do projeto NAME. Você pode especificar a quantidade (padrão: 10).",
        inline=False
    )
    
    embed.add_field(
        name="!status <número_tarefa>",
        value="Mostra detalhes de uma tarefa específica. Você pode usar apenas o número ou o código completo (ex: NAME-123).",
        inline=False
    )
    
    embed.add_field(
        name="!por_status <status> [quantidade]",
        value="Lista tarefas com um status específico. Exemplos de status: 'Em Andamento', 'Concluído', etc.",
        inline=False
    )
    
    embed.add_field(
        name="!similares <número_tarefa> [limiar] [quantidade]",
        value="Encontra tarefas similares a uma tarefa específica. O limiar (0.0-1.0) define o nível mínimo de similaridade (padrão: 0.6).",
        inline=False
    )
    
    embed.add_field(
        name="!jira_ajuda",
        value="Mostra esta mensagem de ajuda.",
        inline=False
    )
    
    embed.set_footer(text=f"Solicitado por {ctx.author.display_name}")
    await ctx.send(embed=embed)

# Tratamento de erros para comandos
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("❌ Comando não encontrado. Use `!jira_ajuda` para ver a lista de comandos disponíveis.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ Argumento obrigatório faltando: {error.param.name}. Use `!jira_ajuda` para mais informações.")
    else:
        logger.error(f"Erro ao executar comando: {error}")
        await ctx.send(f"❌ Ocorreu um erro ao executar o comando: {error}")

# Iniciar o bot
def main():
    logger.info("Iniciando o bot Discord-Jira...")
    bot.run(DISCORD_TOKEN)

if __name__ == "__main__":
    main()
