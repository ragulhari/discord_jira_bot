import os
import sys
import unittest
from unittest.mock import patch, MagicMock
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.bot import get_jira_auth, jira_request, get_NAME_tasks, get_task_details, get_tasks_by_status, find_similar_tasks

class TestJiraFunctions(unittest.TestCase):
    
    @patch('src.bot.JIRA_USERNAME', 'test_user')
    @patch('src.bot.JIRA_API_TOKEN', 'test_token')
    def test_get_jira_auth(self):
        auth = get_jira_auth()
        self.assertEqual(auth, ('test_user', 'test_token'))
    
    @patch('src.bot.requests.get')
    @patch('src.bot.get_jira_auth', return_value=('test_user', 'test_token'))
    def test_jira_request_get(self, mock_auth, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {'key': 'value'}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = jira_request('test_endpoint')
        
        mock_get.assert_called_once()
        self.assertEqual(result, {'key': 'value'})
    
    @patch('src.bot.requests.post')
    @patch('src.bot.get_jira_auth', return_value=('test_user', 'test_token'))
    def test_jira_request_post(self, mock_auth, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {'key': 'value'}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        result = jira_request('test_endpoint', method='POST', data={'test': 'data'})
        
        mock_post.assert_called_once()
        self.assertEqual(result, {'key': 'value'})
    
    @patch('src.bot.jira_request')
    @patch('src.bot.JIRA_PROJECT', 'NAME')
    def test_get_NAME_tasks(self, mock_jira_request):
        mock_jira_request.return_value = {'issues': [{'key': 'NAME-1'}]}
        
        result = get_NAME_tasks(10)
        
        mock_jira_request.assert_called_once()
        self.assertEqual(result, {'issues': [{'key': 'NAME-1'}]})
    
    @patch('src.bot.jira_request')
    def test_get_task_details(self, mock_jira_request):
        mock_jira_request.return_value = {'key': 'NAME-1', 'fields': {'summary': 'Test Task'}}
        
        result = get_task_details('NAME-1')
        
        mock_jira_request.assert_called_once()
        self.assertEqual(result, {'key': 'NAME-1', 'fields': {'summary': 'Test Task'}})
    
    @patch('src.bot.jira_request')
    @patch('src.bot.JIRA_PROJECT', 'NAME')
    def test_get_tasks_by_status(self, mock_jira_request):
        mock_jira_request.return_value = {'issues': [{'key': 'NAME-1'}]}
        
        result = get_tasks_by_status('Em Andamento', 10)
        
        mock_jira_request.assert_called_once()
        self.assertEqual(result, {'issues': [{'key': 'NAME-1'}]})
    
    @patch('src.bot.get_task_details')
    @patch('src.bot.get_NAME_tasks')
    def test_find_similar_tasks(self, mock_get_NAME_tasks, mock_get_task_details):
        # Configurar mock para a tarefa de referência
        mock_get_task_details.return_value = {
            'key': 'NAME-1',
            'fields': {
                'summary': 'Tarefa de teste',
                'description': 'Descrição da tarefa de teste'
            }
        }
        
        # Configurar mock para todas as tarefas
        mock_get_NAME_tasks.return_value = {
            'issues': [
                {
                    'key': 'NAME-1',
                    'fields': {
                        'summary': 'Tarefa de teste',
                        'description': 'Descrição da tarefa de teste'
                    }
                },
                {
                    'key': 'NAME-2',
                    'fields': {
                        'summary': 'Tarefa de teste similar',
                        'description': 'Descrição similar da tarefa de teste'
                    }
                },
                {
                    'key': 'NAME-3',
                    'fields': {
                        'summary': 'Tarefa completamente diferente',
                        'description': 'Descrição totalmente diferente'
                    }
                }
            ]
        }
        
        result = find_similar_tasks('NAME-1', 0.5, 10)
        
        # Verificar se as funções mock foram chamadas
        mock_get_task_details.assert_called_once()
        mock_get_NAME_tasks.assert_called_once()
        
        # Verificar se o resultado contém a tarefa similar
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['key'], 'NAME-2')

if __name__ == '__main__':
    unittest.main()
