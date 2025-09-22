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
    @patch('src.bling.logger')
    def test_validar_credencial_unica_sucesso(self, mock_logger):
        """Testa validação bem-sucedida de credencial única com método otimizado."""
        # Mock do método otimizado
        with patch.object(self.validator, '_executar_validacao_otimizada') as mock_exec:
            mock_exec.return_value = {
                'is_valid': True,
                'status_code': 201,
                'response_time': 150.5,
                'error_details': None
            }
            
            resultado = self.validator.validar_credencial_unica("user@test.com", "senha123")
            
            assert resultado is True
            mock_exec.assert_called_once_with("user@test.com", "senha123")
            
            # Verifica se o log de sucesso foi chamado
            mock_logger.info.assert_called_with("✅ SUCESSO - Credenciais válidas para usuário: user@test.com")
    
    @pytest.mark.unit
    @patch('src.bling.logger')
    def test_validar_credencial_unica_falha(self, mock_logger):
        """Testa validação com falha de credencial única com método otimizado."""
        # Mock do método otimizado
        with patch.object(self.validator, '_executar_validacao_otimizada') as mock_exec:
            mock_exec.return_value = {
                'is_valid': False,
                'status_code': 401,
                'response_time': 89.7,
                'error_details': 'Credenciais inválidas'
            }
            
            resultado = self.validator.validar_credencial_unica("user@test.com", "senha_errada")
            
            assert resultado is False
            mock_exec.assert_called_once_with("user@test.com", "senha_errada")
            
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
    
    @pytest.mark.unit
    def test_validar_dados_entrada_validos(self):
        """Testa validação de dados de entrada válidos."""
        resultado = self.validator._validar_dados_entrada("user@test.com", "senha123")
        assert resultado is True
    
    @pytest.mark.unit
    def test_validar_dados_entrada_username_vazio(self):
        """Testa validação com username vazio."""
        resultado = self.validator._validar_dados_entrada("", "senha123")
        assert resultado is False
        
        resultado = self.validator._validar_dados_entrada("   ", "senha123")
        assert resultado is False
    
    @pytest.mark.unit
    def test_validar_dados_entrada_password_vazio(self):
        """Testa validação com password vazio."""
        resultado = self.validator._validar_dados_entrada("user@test.com", "")
        assert resultado is False
        
        resultado = self.validator._validar_dados_entrada("user@test.com", "   ")
        assert resultado is False
    
    @pytest.mark.unit
    def test_validar_dados_entrada_username_curto(self):
        """Testa validação com username muito curto."""
        resultado = self.validator._validar_dados_entrada("ab", "senha123")
        assert resultado is False
    
    @pytest.mark.unit
    def test_validar_dados_entrada_password_placeholder(self):
        """Testa validação com password placeholder."""
        placeholders = ['[NOT_SAVED]', '[REDACTED]', '[HIDDEN]', 'N/A', 'NULL', 'undefined', 'null']
        
        for placeholder in placeholders:
            resultado = self.validator._validar_dados_entrada("user@test.com", placeholder)
            assert resultado is False
    
    @pytest.mark.unit
    def test_analisar_resposta_bling_sucesso_201(self):
        """Testa análise de resposta com código 201."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.headers = {'Content-Type': 'application/json'}
        mock_response.text = '{"status": "success"}'
        
        resultado = self.validator._analisar_resposta_bling(mock_response, 150.5)
        
        assert resultado['is_valid'] is True
        assert resultado['status_code'] == 201
        assert resultado['response_time'] == 150.5
        assert resultado['error_details'] is None
    
    @pytest.mark.unit
    def test_analisar_resposta_bling_erro_401(self):
        """Testa análise de resposta com código 401."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.headers = {'Content-Type': 'application/json'}
        mock_response.text = '{"error": "Invalid credentials"}'
        
        resultado = self.validator._analisar_resposta_bling(mock_response, 95.2)
        
        assert resultado['is_valid'] is False
        assert resultado['status_code'] == 401
        assert resultado['error_details'] == "Credenciais inválidas"
    
    @pytest.mark.unit
    def test_analisar_resposta_bling_redirect_sucesso(self):
        """Testa análise de resposta com redirect para dashboard."""
        mock_response = Mock()
        mock_response.status_code = 302
        mock_response.headers = {'Location': 'https://bling.com.br/dashboard'}
        mock_response.text = ''
        
        resultado = self.validator._analisar_resposta_bling(mock_response, 200.0)
        
        assert resultado['is_valid'] is True
        assert resultado['status_code'] == 302
        assert 'dashboard' in resultado['error_details'].lower()
    
    @pytest.mark.unit
    def test_verificar_resposta_adicional_sucesso(self):
        """Testa verificação adicional com indicadores de sucesso."""
        mock_response = Mock()
        mock_response.headers = {'Content-Type': 'text/html'}
        mock_response.text = '<html><body>Welcome to dashboard</body></html>'
        
        resultado = self.validator._verificar_resposta_adicional(mock_response)
        assert resultado is True
    
    @pytest.mark.unit
    def test_verificar_resposta_adicional_erro(self):
        """Testa verificação adicional com indicadores de erro."""
        mock_response = Mock()
        mock_response.headers = {'Content-Type': 'text/html'}
        mock_response.text = '<html><body>Invalid credentials</body></html>'
        
        resultado = self.validator._verificar_resposta_adicional(mock_response)
        assert resultado is False
    
    @pytest.mark.unit
    def test_validar_credencial_dados_invalidos(self):
        """Testa validação com dados inválidos (falha na validação prévia)."""
        resultado = self.validator.validar_credencial_unica("", "senha123")
        assert resultado is False
        
        resultado = self.validator.validar_credencial_unica("user@test.com", "[NOT_SAVED]")
        assert resultado is False


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
