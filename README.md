# Bot Discord para Integração com Jira (Projeto NAME)

Este projeto implementa um bot do Discord que se conecta ao MCP da Atlassian para realizar consultas no Jira sobre tarefas do projeto NAME.

## Funcionalidades

- Listar tarefas do projeto NAME
- Consultar status de tarefas específicas
- Filtrar tarefas por status
- Identificar tarefas similares com base em conteúdo

## Requisitos

- Python 3.6+
- Token de bot do Discord
- Credenciais de API do Jira

## Instalação

1. Clone este repositório ou baixe os arquivos
2. Instale as dependências:

```bash
pip install discord.py python-dotenv requests
```

3. Configure as variáveis de ambiente:
   - Crie um arquivo `.env` baseado no `.env.example`
   - Preencha com suas credenciais do Discord e do Jira

## Configuração

### Obter Token do Discord

1. Acesse o [Portal de Desenvolvedores do Discord](https://discord.com/developers/applications)
2. Crie uma nova aplicação
3. Vá para a seção "Bot" e clique em "Add Bot"
4. Copie o token e adicione ao arquivo `.env`
5. Ative os intents necessários (Presence Intent, Server Members Intent, Message Content Intent)
6. Use o link de OAuth2 para adicionar o bot ao seu servidor

### Configurar Credenciais do Jira

1. Acesse as configurações da sua conta Atlassian
2. Crie um token de API
3. Adicione o token, URL do Jira e seu nome de usuário ao arquivo `.env`

## Uso

Execute o bot com:

```bash
python src/bot.py
```

### Comandos Disponíveis

- `!tarefas [quantidade]` - Lista as tarefas mais recentes do projeto NAME
- `!status <número_tarefa>` - Mostra detalhes de uma tarefa específica
- `!por_status <status> [quantidade]` - Lista tarefas com um status específico
- `!similares <número_tarefa> [limiar] [quantidade]` - Encontra tarefas similares
- `!jira_ajuda` - Mostra a lista de comandos disponíveis

## Estrutura do Projeto

```
discord_jira_bot/
├── src/
│   ├── bot.py           # Código principal do bot
│   └── test_bot.py      # Testes unitários (dentro de src)
├── tests/
│   └── test_bot.py      # Testes unitários (diretório separado)
├── .env.example         # Exemplo de configuração de variáveis de ambiente
└── README.md            # Este arquivo
```

## Testes

Execute os testes unitários com:

```bash
python -m unittest discover -s tests
```

## Referências

- [Documentação do discord.py](https://discordpy.readthedocs.io/)
- [API do Jira](https://developer.atlassian.com/server/jira/platform/jira-rest-api-examples/)
- [MCP Atlassian](https://pypi.org/project/mcp-atlassian/)
- [Atlassian Python API](https://github.com/atlassian-api/atlassian-python-api)

## Notas

- As credenciais são tratadas como variáveis de ambiente para segurança
- O bot está configurado para o projeto "NAME" conforme solicitado
- As respostas são formatadas de forma amigável usando embeds do Discord
- Criado 100% por IA utilizando manus.im
