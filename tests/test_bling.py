"""Testes unitários para o módulo bling.py.

Este módulo contém testes abrangentes para validação de credenciais
via API do Bling, seguindo as diretrizes do GEMINI.md.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import requests

from src.bling import BlingCredentialValidator, criar_validador_bling


class TestBlingCredentialValidator:
    """Testes para a classe BlingCredentialValidator."""
    
    def setup_method(self):
        """Configuração executada antes de cada teste."""
        self.validator = BlingCredentialValidator()
        self.temp_dir = Path(tempfile.mkdtemp())
    
    def teardown_method(self):
        """Limpeza executada após cada teste."""
        # Remove arquivos temporários
        for file in self.temp_dir.glob('*'):
            file.unlink()
        self.temp_dir.rmdir()
    
    @pytest.mark.unit
    def test_inicializacao_padrao(self):
        """Testa inicialização com parâmetros padrão."""
        validator = BlingCredentialValidator()
        assert validator.login_url == "https://www.bling.com.br/login"
        assert validator.timeout == 30
        assert validator.csv_handler is not None
    
    @pytest.mark.unit
    def test_inicializacao_customizada(self):
        """Testa inicialização com parâmetros customizados."""
        custom_url = "https://custom.bling.com.br/login"
        custom_timeout = 60
        
        validator = BlingCredentialValidator(login_url=custom_url, timeout=custom_timeout)
        assert validator.login_url == custom_url
        assert validator.timeout == custom_timeout
    
    @pytest.mark.unit
    @patch('src.bling.requests.post')
    @patch('src.bling.logger')
    def test_validar_credencial_unica_sucesso(self, mock_logger, mock_post):
        """Testa validação bem-sucedida de credencial única."""
        # Configura mock para retornar status 201
        mock_response = Mock()
        mock_response.status_code = 201
        mock_post.return_value = mock_response
        
        resultado = self.validator.validar_credencial_unica("user@test.com", "senha123")
        
        assert resultado is True
        mock_post.assert_called_once()
        
        # Verifica se os headers de segurança foram incluídos
        call_args = mock_post.call_args
        headers = call_args[1]['headers']
        assert headers['X-Security-Test'] == 'security-tests-bling'
        assert 'Bling-Security-Test' in headers['User-Agent']
        
        # Verifica se o log de sucesso foi chamado
        mock_logger.info.assert_called_with("✅ SUCESSO - Credenciais válidas para usuário: user@test.com")
    
    @pytest.mark.unit
    @patch('src.bling.requests.post')
    @patch('src.bling.logger')
    def test_validar_credencial_unica_falha(self, mock_logger, mock_post):
        """Testa validação com falha de credencial única."""
        # Configura mock para retornar status diferente de 201
        mock_response = Mock()
        mock_response.status_code = 401
        mock_post.return_value = mock_response
        
        resultado = self.validator.validar_credencial_unica("user@test.com", "senha_errada")
        
        assert resultado is False
        mock_post.assert_called_once()
        
        # Verifica se o log de erro foi chamado
        mock_logger.warning.assert_called_with("❌ ERRO - Credenciais inválidas para usuário: user@test.com (HTTP 401)")
    
    @pytest.mark.unit
    @patch('src.bling.requests.post')
    def test_validar_credencial_unica_timeout(self, mock_post):
        """Testa tratamento de timeout na validação."""
        mock_post.side_effect = requests.exceptions.Timeout()
        
        resultado = self.validator.validar_credencial_unica("user@test.com", "senha123")
        
        assert resultado is False
        mock_post.assert_called_once()
    
    @pytest.mark.unit
    @patch('src.bling.requests.post')
    def test_validar_credencial_unica_connection_error(self, mock_post):
        """Testa tratamento de erro de conexão."""
        mock_post.side_effect = requests.exceptions.ConnectionError()
        
        resultado = self.validator.validar_credencial_unica("user@test.com", "senha123")
        
        assert resultado is False
        mock_post.assert_called_once()
    
    @pytest.mark.unit
    @patch('src.bling.requests.post')
    def test_validar_credencial_unica_erro_generico(self, mock_post):
        """Testa tratamento de erro genérico."""
        mock_post.side_effect = Exception("Erro inesperado")
        
        resultado = self.validator.validar_credencial_unica("user@test.com", "senha123")
        
        assert resultado is False
        mock_post.assert_called_once()
    
    @pytest.mark.unit
    def test_validar_credenciais_lote_lista_vazia(self):
        """Testa validação em lote com lista vazia."""
        resultado = self.validator.validar_credenciais_lote([])
        assert resultado == []
    
    @pytest.mark.unit
    @patch('src.bling.BlingCredentialValidator.validar_credencial_unica')
    def test_validar_credenciais_lote_sucesso(self, mock_validar):
        """Testa validação em lote bem-sucedida."""
        # Configura mock para alternar entre True e False
        mock_validar.side_effect = [True, False, True]
        
        credenciais = [
            {'username': 'user1@test.com', 'password': 'senha1', 'linha_original': 0},
            {'username': 'user2@test.com', 'password': 'senha2', 'linha_original': 1},
            {'username': 'user3@test.com', 'password': 'senha3', 'linha_original': 2}
        ]
        
        resultados = self.validator.validar_credenciais_lote(credenciais)
        
        assert len(resultados) == 3
        assert resultados[0]['is_valid'] is True
        assert resultados[1]['is_valid'] is False
        assert resultados[2]['is_valid'] is True
        
        # Verifica se todos os resultados têm os campos necessários
        for resultado in resultados:
            assert 'username' in resultado
            assert 'password' in resultado
            assert 'is_valid' in resultado
            assert 'timestamp' in resultado
            assert 'linha_original' in resultado
            assert 'error' in resultado
    
    @pytest.mark.unit
    @patch('src.bling.BlingCredentialValidator.validar_credencial_unica')
    def test_validar_credenciais_lote_com_erro(self, mock_validar):
        """Testa validação em lote com erro durante processamento."""
        mock_validar.side_effect = Exception("Erro de validação")
        
        credenciais = [
            {'username': 'user@test.com', 'password': 'senha123', 'linha_original': 0}
        ]
        
        resultados = self.validator.validar_credenciais_lote(credenciais)
        
        assert len(resultados) == 1
        assert resultados[0]['is_valid'] is False
        assert 'Erro no processamento' in resultados[0]['error']
    
    @pytest.mark.unit
    @patch('src.bling.criar_csv_handler')
    def test_processar_arquivo_csv_sucesso(self, mock_criar_csv_handler):
        """Testa processamento bem-sucedido de arquivo CSV."""
        # Configura mock do CSV handler
        mock_csv_handler = Mock()
        mock_csv_handler.ler_credenciais.return_value = [
            {'username': 'user@test.com', 'password': 'senha123', 'linha_original': 0}
        ]
        mock_criar_csv_handler.return_value = mock_csv_handler
        
        # Mock da validação
        with patch.object(self.validator, 'validar_credenciais_lote') as mock_validar_lote:
            mock_validar_lote.return_value = [
                {'username': 'user@test.com', 'is_valid': True, 'error': ''}
            ]
            
            # Recria o validator para usar o mock
            validator = BlingCredentialValidator()
            
            resultado = validator.processar_arquivo_csv("teste.csv")
            
            assert len(resultado) == 1
            assert resultado[0]['is_valid'] is True
    
    @pytest.mark.unit
    @patch('src.bling.criar_csv_handler')
    def test_processar_arquivo_csv_vazio(self, mock_criar_csv_handler):
        """Testa processamento de arquivo CSV vazio."""
        mock_csv_handler = Mock()
        mock_csv_handler.ler_credenciais.return_value = []
        mock_criar_csv_handler.return_value = mock_csv_handler
        
        validator = BlingCredentialValidator()
        resultado = validator.processar_arquivo_csv("teste_vazio.csv")
        
        assert resultado == []
    
    @pytest.mark.unit
    @patch('src.bling.criar_csv_handler')
    def test_processar_arquivo_csv_erro(self, mock_criar_csv_handler):
        """Testa tratamento de erro no processamento de CSV."""
        mock_csv_handler = Mock()
        mock_csv_handler.ler_credenciais.side_effect = Exception("Erro ao ler CSV")
        mock_criar_csv_handler.return_value = mock_csv_handler
        
        validator = BlingCredentialValidator()
        
        with pytest.raises(Exception, match="Erro ao ler CSV"):
            validator.processar_arquivo_csv("teste_erro.csv")


class TestFactoryFunction:
    """Testes para a função factory criar_validador_bling."""
    
    @pytest.mark.unit
    def test_criar_validador_bling_padrao(self):
        """Testa criação de validador com parâmetros padrão."""
        validator = criar_validador_bling()
        
        assert isinstance(validator, BlingCredentialValidator)
        assert validator.login_url == "https://www.bling.com.br/login"
        assert validator.timeout == 30
    
    @pytest.mark.unit
    def test_criar_validador_bling_customizado(self):
        """Testa criação de validador com parâmetros customizados."""
        custom_url = "https://custom.bling.com.br/login"
        custom_timeout = 60
        
        validator = criar_validador_bling(login_url=custom_url, timeout=custom_timeout)
        
        assert isinstance(validator, BlingCredentialValidator)
        assert validator.login_url == custom_url
        assert validator.timeout == custom_timeout


@pytest.mark.integration
class TestBlingIntegration:
    """Testes de integração para o validador Bling."""
    
    def setup_method(self):
        """Configuração para testes de integração."""
        self.validator = BlingCredentialValidator()
        self.temp_dir = Path(tempfile.mkdtemp())
    
    def teardown_method(self):
        """Limpeza após testes de integração."""
        for file in self.temp_dir.glob('*'):
            file.unlink()
        self.temp_dir.rmdir()
    
    @patch('src.bling.requests.post')
    def test_fluxo_completo_validacao(self, mock_post):
        """Testa fluxo completo de validação com arquivo CSV."""
        # Configura mock para simular resposta da API
        mock_response = Mock()
        mock_response.status_code = 201
        mock_post.return_value = mock_response
        
        # Cria arquivo CSV temporário
        csv_file = self.temp_dir / "teste_bling.csv"
        csv_content = """username,password
user1@test.com,senha123
user2@test.com,senha456"""
        
        csv_file.write_text(csv_content, encoding='utf-8')
        
        # Processa o arquivo
        resultados = self.validator.processar_arquivo_csv(str(csv_file))
        
        # Verifica resultados
        assert len(resultados) == 2
        assert all(r['is_valid'] for r in resultados)
        assert mock_post.call_count == 2
        
        # Verifica se os headers de segurança foram incluídos em todas as chamadas
        for call in mock_post.call_args_list:
            headers = call[1]['headers']
            assert headers['X-Security-Test'] == 'security-tests-bling'
            assert 'Bling-Security-Test' in headers['User-Agent']
