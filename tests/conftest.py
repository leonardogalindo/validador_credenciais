"""Configurações compartilhadas para todos os testes.

Este arquivo contém fixtures e configurações que são compartilhadas
entre todos os testes do projeto.
"""

import logging
import os
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch

from src.settings import AppConfig, LoggingConfig


@pytest.fixture(scope="session")
def disable_logging():
    """Desabilita logging durante os testes para evitar poluição da saída."""
    logging.disable(logging.CRITICAL)
    yield
    logging.disable(logging.NOTSET)


@pytest.fixture
def temp_directory():
    """Cria um diretório temporário para testes."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def mock_env_vars():
    """Fixture para mockar variáveis de ambiente."""
    def _mock_env(**kwargs):
        return patch.dict('os.environ', kwargs, clear=True)
    return _mock_env


@pytest.fixture
def sample_csv_simple():
    """Retorna conteúdo de CSV simples para testes."""
    return """username,password
user1@test.com,senha123
user2@test.com,senha456
user3@test.com,senha789"""


@pytest.fixture
def sample_csv_locaweb():
    """Retorna conteúdo de CSV no formato Locaweb para testes."""
    return """name,username,email,mail_domain,cpf,rg,rg_or_ie,password,password_hash,url,internal,gender,address,phone,occupation,mother_name,company_name,cnpj,stealer_family,infection_date,hardware_id,hostname,malware_installation_path,ip,user_agent,brand,source,threat_id,breach_date
,jonas.jesus@locaweb.com.br,jonas.jesus@locaweb.com.br,,,,,9hCAYCRx@zrK8HS,,,,,,,,,,,,,,,,,,LOCAWEB,Telegram,DRP-3187,2025-09-15
,vitor.paixao@locaweb.com.br,vitor.paixao@locaweb.com.br,,,,,locavideo08,,,,,,,,,,,,,,,,,,LOCAWEB,Telegram,DRP-3187,2025-09-15
,emailmarketing@locaweb.com.br,emailmarketing@locaweb.com.br,,,,,Paralela09,,,,,,,,,,,,,,,,,,LOCAWEB,Telegram,DRP-3187,2025-09-15"""


@pytest.fixture
def sample_validation_results():
    """Retorna resultados de validação de exemplo para testes."""
    return [
        {
            'username': 'user1@test.com',
            'password': 'senha123',
            'is_valid': True,
            'error': None,
            'linha_original': 2
        },
        {
            'username': 'user2@test.com',
            'password': 'senha456',
            'is_valid': False,
            'error': 'Credenciais inválidas',
            'linha_original': 3
        },
        {
            'username': 'user3@test.com',
            'password': 'senha789',
            'is_valid': True,
            'error': None,
            'linha_original': 4
        }
    ]


@pytest.fixture
def isolated_app_config(temp_directory):
    """Isola configurações da aplicação para testes."""
    # Salva configurações originais
    original_data_dir = AppConfig.DATA_DIR
    original_csv_dir = AppConfig.CSV_INPUT_DIR
    original_txt_dir = AppConfig.TXT_OUTPUT_DIR
    original_json_dir = AppConfig.JSON_OUTPUT_DIR
    original_log_dir = LoggingConfig.LOG_DIR
    
    # Configura diretórios temporários
    AppConfig.DATA_DIR = temp_directory / "data"
    AppConfig.CSV_INPUT_DIR = AppConfig.DATA_DIR / 'csv'
    AppConfig.TXT_OUTPUT_DIR = AppConfig.DATA_DIR / 'txt'
    AppConfig.JSON_OUTPUT_DIR = AppConfig.DATA_DIR / 'json'
    LoggingConfig.LOG_DIR = temp_directory / "logs"
    
    # Cria diretórios
    AppConfig.create_directories()
    LoggingConfig.create_log_directory()
    
    yield {
        'data_dir': AppConfig.DATA_DIR,
        'csv_dir': AppConfig.CSV_INPUT_DIR,
        'txt_dir': AppConfig.TXT_OUTPUT_DIR,
        'json_dir': AppConfig.JSON_OUTPUT_DIR,
        'log_dir': LoggingConfig.LOG_DIR
    }
    
    # Restaura configurações originais
    AppConfig.DATA_DIR = original_data_dir
    AppConfig.CSV_INPUT_DIR = original_csv_dir
    AppConfig.TXT_OUTPUT_DIR = original_txt_dir
    AppConfig.JSON_OUTPUT_DIR = original_json_dir
    LoggingConfig.LOG_DIR = original_log_dir


@pytest.fixture
def mock_locaweb_api():
    """Mock para API da Locaweb."""
    def _create_mock(success_users=None, fail_users=None, error_users=None):
        """
        Cria mock da API com comportamentos específicos.
        
        Args:
            success_users: Lista de usuários que devem retornar sucesso (200)
            fail_users: Lista de usuários que devem retornar falha (401)
            error_users: Lista de usuários que devem gerar exceção
        """
        success_users = success_users or []
        fail_users = fail_users or []
        error_users = error_users or []
        
        def mock_post_side_effect(url, data, **kwargs):
            from unittest.mock import Mock
            import requests
            
            username = data.get('username', '')
            
            if username in error_users:
                raise requests.RequestException(f"Erro simulado para {username}")
            
            mock_response = Mock()
            if username in success_users:
                mock_response.status_code = 200
            elif username in fail_users:
                mock_response.status_code = 401
            else:
                # Comportamento padrão: alterna entre sucesso e falha
                mock_response.status_code = 200 if hash(username) % 2 == 0 else 401
            
            return mock_response
        
        return patch('requests.post', side_effect=mock_post_side_effect)
    
    return _create_mock


@pytest.fixture(autouse=True)
def clean_loggers():
    """Limpa handlers de logging antes e depois de cada teste."""
    # Limpa antes do teste
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    
    for logger_name in ['audit', 'settings']:
        logger = logging.getLogger(logger_name)
        logger.handlers.clear()
    
    yield
    
    # Limpa depois do teste
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    
    for logger_name in ['audit', 'settings']:
        logger = logging.getLogger(logger_name)
        logger.handlers.clear()


@pytest.fixture
def valid_env_config():
    """Configuração válida de variáveis de ambiente para testes."""
    return {
        'LOCAWEB_LOGIN_URL': 'https://test.locaweb.com/api',
        'REQUEST_TIMEOUT': '30',
        'LOG_LEVEL': 'INFO',
        'CSV_ENCODING': 'utf-8',
        'INCLUDE_PASSWORDS_IN_OUTPUT': 'false'
    }


# Marcadores para categorizar testes
def pytest_configure(config):
    """Configuração adicional do pytest."""
    config.addinivalue_line(
        "markers", "unit: marca testes unitários"
    )
    config.addinivalue_line(
        "markers", "integration: marca testes de integração"
    )
    config.addinivalue_line(
        "markers", "slow: marca testes que demoram para executar"
    )
    config.addinivalue_line(
        "markers", "network: marca testes que fazem requisições de rede"
    )


# Hook para personalizar coleta de testes
def pytest_collection_modifyitems(config, items):
    """Modifica itens coletados para adicionar marcadores automáticos."""
    for item in items:
        # Adiciona marcador 'unit' para testes que não são de integração
        if "test_integration" not in item.nodeid:
            item.add_marker(pytest.mark.unit)
        else:
            item.add_marker(pytest.mark.integration)
        
        # Adiciona marcador 'network' para testes que fazem requisições
        if "requests" in str(item.function.__code__.co_names):
            item.add_marker(pytest.mark.network)


# Hook para relatório personalizado
def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """Adiciona resumo personalizado ao final dos testes."""
    if hasattr(terminalreporter, 'stats'):
        passed = len(terminalreporter.stats.get('passed', []))
        failed = len(terminalreporter.stats.get('failed', []))
        skipped = len(terminalreporter.stats.get('skipped', []))
        
        terminalreporter.write_sep("=", "RESUMO DOS TESTES")
        terminalreporter.write_line(f"✅ Passou: {passed}")
        terminalreporter.write_line(f"❌ Falhou: {failed}")
        terminalreporter.write_line(f"⏭️  Pulou: {skipped}")
        
        if failed == 0:
            terminalreporter.write_line("🎉 Todos os testes passaram!")
        else:
            terminalreporter.write_line("⚠️  Alguns testes falharam. Verifique os detalhes acima.")


# Configuração para testes lentos
def pytest_runtest_setup(item):
    """Configuração executada antes de cada teste."""
    # Pula testes marcados como 'slow' se não for explicitamente solicitado
    if "slow" in item.keywords and not item.config.getoption("--runslow", default=False):
        pytest.skip("Teste lento pulado (use --runslow para executar)")


def pytest_addoption(parser):
    """Adiciona opções personalizadas ao pytest."""
    parser.addoption(
        "--runslow", 
        action="store_true", 
        default=False, 
        help="Executa testes marcados como lentos"
    )
