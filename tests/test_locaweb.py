"""Testes unitários para o módulo locaweb.

Este módulo testa todas as funcionalidades do LocawebCredentialValidator,
incluindo validação de credenciais e integração com CSV.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import requests

from src.locaweb import LocawebCredentialValidator, criar_validador_locaweb


class TestLocawebCredentialValidator:
    """Testes para a classe LocawebCredentialValidator."""
    
    # Headers esperados em todas as requisições
    EXPECTED_HEADERS = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-Security-Test': 'security-tests-lwsa',
        'User-Agent': 'Locaweb-Security-Credential-Validator/1.0 (Teste de Segurança - Credenciais Vazadas)'
    }
    
    def setup_method(self):
        """Configuração executada antes de cada teste."""
        self.login_url = "https://api.test.com/login"
        self.validator = LocawebCredentialValidator(login_url=self.login_url)
        self.temp_dir = Path(tempfile.mkdtemp())
    
    def teardown_method(self):
        """Limpeza executada após cada teste."""
        import shutil
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def _verify_headers_in_calls(self, mock_post):
        """Verifica se todas as chamadas incluem os headers de segurança."""
        for call in mock_post.call_args_list:
            call_kwargs = call[1]  # kwargs da chamada
            assert 'headers' in call_kwargs, "Headers não encontrados na chamada"
            headers = call_kwargs['headers']
            assert headers == self.EXPECTED_HEADERS, f"Headers incorretos: {headers}"
    
    def test_init_com_url(self):
        """Testa inicialização com URL fornecida."""
        validator = LocawebCredentialValidator(login_url="https://test.com")
        assert validator.login_url == "https://test.com"
        assert validator.timeout == 30  # valor padrão
        assert validator.csv_handler is not None
    
    def test_init_com_timeout_customizado(self):
        """Testa inicialização com timeout customizado."""
        validator = LocawebCredentialValidator(
            login_url="https://test.com", 
            timeout=60
        )
        assert validator.timeout == 60
    
    @patch.dict('os.environ', {'LOCAWEB_LOGIN_URL': 'https://env.test.com'})
    def test_init_com_env_var(self):
        """Testa inicialização com URL da variável de ambiente."""
        validator = LocawebCredentialValidator()
        assert validator.login_url == "https://env.test.com"
    
    def test_init_sem_url(self):
        """Testa inicialização sem URL (deve falhar)."""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="URL de login deve ser fornecida"):
                LocawebCredentialValidator()
    
    @patch('requests.post')
    def test_validar_credencial_unica_sucesso(self, mock_post):
        """Testa validação de credencial única com sucesso."""
        # Mock da resposta HTTP
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        resultado = self.validator.validar_credencial_unica("user@test.com", "senha123")
        
        assert resultado is True
        mock_post.assert_called_once_with(
            self.login_url,
            data={'username': 'user@test.com', 'password': 'senha123'},
            timeout=30,
            headers=self.EXPECTED_HEADERS
        )
    
    @patch('requests.post')
    def test_validar_credencial_unica_falha(self, mock_post):
        """Testa validação de credencial única com falha."""
        # Mock da resposta HTTP com erro
        mock_response = Mock()
        mock_response.status_code = 401
        mock_post.return_value = mock_response
        
        resultado = self.validator.validar_credencial_unica("user@test.com", "senha_errada")
        
        assert resultado is False
    
    @patch('requests.post')
    def test_validar_credencial_unica_erro_rede(self, mock_post):
        """Testa validação com erro de rede."""
        mock_post.side_effect = requests.RequestException("Erro de conexão")
        
        with pytest.raises(requests.RequestException):
            self.validator.validar_credencial_unica("user@test.com", "senha123")
    
    def test_validar_credencial_unica_parametros_vazios(self):
        """Testa validação com parâmetros vazios."""
        with pytest.raises(ValueError, match="Username e password não podem estar vazios"):
            self.validator.validar_credencial_unica("", "senha123")
        
        with pytest.raises(ValueError, match="Username e password não podem estar vazios"):
            self.validator.validar_credencial_unica("user@test.com", "")
        
        with pytest.raises(ValueError, match="Username e password não podem estar vazios"):
            self.validator.validar_credencial_unica("", "")
    
    @patch('requests.post')
    def test_validar_credencial_unica_diferentes_status_codes(self, mock_post):
        """Testa validação com diferentes códigos de status HTTP."""
        test_cases = [
            (200, True),   # Sucesso
            (401, False),  # Não autorizado
            (403, False),  # Proibido
            (404, False),  # Não encontrado
            (500, False),  # Erro interno
        ]
        
        for status_code, expected_result in test_cases:
            mock_response = Mock()
            mock_response.status_code = status_code
            mock_post.return_value = mock_response
            
            resultado = self.validator.validar_credencial_unica("user@test.com", "senha123")
            assert resultado == expected_result
    
    def test_validar_credenciais_em_lote_arquivo_inexistente(self):
        """Testa validação em lote com arquivo inexistente."""
        with pytest.raises(FileNotFoundError):
            self.validator.validar_credenciais_em_lote("arquivo_inexistente.csv")
    
    @patch('requests.post')
    def test_validar_credenciais_em_lote_sucesso(self, mock_post):
        """Testa validação em lote com sucesso."""
        # Cria arquivo CSV temporário
        csv_content = """username,password
user1@test.com,senha123
user2@test.com,senha456
user3@test.com,senha789"""
        
        csv_file = self.temp_dir / "credenciais.csv"
        csv_file.write_text(csv_content, encoding='utf-8')
        
        # Mock das respostas HTTP (alternando sucesso/falha)
        def mock_post_side_effect(url, data, **kwargs):
            mock_response = Mock()
            if data['username'] == 'user2@test.com':
                mock_response.status_code = 401  # Falha
            else:
                mock_response.status_code = 200  # Sucesso
            return mock_response
        
        mock_post.side_effect = mock_post_side_effect
        
        # Executa validação
        resultados = self.validator.validar_credenciais_em_lote(str(csv_file))
        
        # Verifica resultados
        assert len(resultados) == 3
        assert resultados[0]['username'] == 'user1@test.com'
        assert resultados[0]['is_valid'] is True
        assert resultados[1]['username'] == 'user2@test.com'
        assert resultados[1]['is_valid'] is False
        assert resultados[2]['username'] == 'user3@test.com'
        assert resultados[2]['is_valid'] is True
        
        # Verifica se as chamadas HTTP foram feitas
        assert mock_post.call_count == 3
        
        # Verifica se todas as chamadas incluem headers de segurança
        self._verify_headers_in_calls(mock_post)
    
    @patch('requests.post')
    def test_validar_credenciais_em_lote_com_senha_resultado(self, mock_post):
        """Testa validação em lote incluindo senhas no resultado."""
        csv_content = """username,password
user1@test.com,senha123"""
        
        csv_file = self.temp_dir / "credenciais.csv"
        csv_file.write_text(csv_content, encoding='utf-8')
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        # Testa com senha incluída
        resultados = self.validator.validar_credenciais_em_lote(
            str(csv_file), 
            incluir_senha_resultado=True
        )
        
        assert len(resultados) == 1
        assert 'password' in resultados[0]
        assert resultados[0]['password'] == 'senha123'
        
        # Testa sem senha incluída
        resultados = self.validator.validar_credenciais_em_lote(
            str(csv_file), 
            incluir_senha_resultado=False
        )
        
        assert len(resultados) == 1
        assert 'password' not in resultados[0]
        
        # Verifica headers de segurança
        self._verify_headers_in_calls(mock_post)
    
    @patch('requests.post')
    def test_validar_credenciais_em_lote_com_erros(self, mock_post):
        """Testa validação em lote com erros de rede."""
        csv_content = """username,password
user1@test.com,senha123
user2@test.com,senha456"""
        
        csv_file = self.temp_dir / "credenciais.csv"
        csv_file.write_text(csv_content, encoding='utf-8')
        
        # Mock que falha na segunda chamada
        def mock_post_side_effect(url, data, **kwargs):
            if data['username'] == 'user2@test.com':
                raise requests.RequestException("Erro de rede")
            mock_response = Mock()
            mock_response.status_code = 200
            return mock_response
        
        mock_post.side_effect = mock_post_side_effect
        
        resultados = self.validator.validar_credenciais_em_lote(str(csv_file))
        
        assert len(resultados) == 2
        assert resultados[0]['is_valid'] is True
        assert resultados[0]['error'] is None
        assert resultados[1]['is_valid'] is False
        assert 'Erro de rede' in resultados[1]['error']
        
        # Verifica headers de segurança (apenas na primeira chamada que teve sucesso)
        assert mock_post.call_count == 2
        self._verify_headers_in_calls(mock_post)
    
    
    def test_salvar_resultados_json(self):
        """Testa salvamento de resultados em JSON."""
        resultados = [
            {'username': 'user1@test.com', 'is_valid': True, 'error': None}
        ]
        
        json_file = self.temp_dir / "resultados.json"
        
        # Mock do csv_handler
        with patch.object(self.validator.csv_handler, 'salvar_resultados_json') as mock_salvar:
            self.validator.salvar_resultados_json(resultados, str(json_file), "origem.csv")
            mock_salvar.assert_called_once_with(resultados, str(json_file), "origem.csv")


class TestCriarValidadorLocaweb:
    """Testes para a função criar_validador_locaweb."""
    
    def test_criar_validador_sem_parametros(self):
        """Testa criação do validador sem parâmetros."""
        with patch.dict('os.environ', {'LOCAWEB_LOGIN_URL': 'https://test.com'}):
            validator = criar_validador_locaweb()
            assert isinstance(validator, LocawebCredentialValidator)
            assert validator.login_url == "https://test.com"
    
    def test_criar_validador_com_url(self):
        """Testa criação do validador com URL específica."""
        validator = criar_validador_locaweb("https://custom.com")
        assert isinstance(validator, LocawebCredentialValidator)
        assert validator.login_url == "https://custom.com"


class TestLocawebIntegration:
    """Testes de integração para o módulo locaweb."""
    
    def setup_method(self):
        """Configuração para testes de integração."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.validator = LocawebCredentialValidator(login_url="https://test.com")
    
    def teardown_method(self):
        """Limpeza após testes de integração."""
        import shutil
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    @patch('requests.post')
    def test_fluxo_completo_validacao(self, mock_post):
        """Testa fluxo completo: CSV -> validação -> JSON."""
        # 1. Cria arquivo CSV
        csv_content = """username,password
user1@test.com,senha123
user2@test.com,senha456"""
        
        csv_file = self.temp_dir / "entrada.csv"
        csv_file.write_text(csv_content, encoding='utf-8')
        
        # 2. Mock das respostas HTTP
        def mock_post_side_effect(url, data, **kwargs):
            mock_response = Mock()
            mock_response.status_code = 200 if data['username'] == 'user1@test.com' else 401
            return mock_response
        
        mock_post.side_effect = mock_post_side_effect
        
        # 3. Executa validação
        resultados = self.validator.validar_credenciais_em_lote(
            str(csv_file), 
            incluir_senha_resultado=True
        )
        
        # 4. Salva em JSON
        json_file = self.temp_dir / "saida.json"
        self.validator.salvar_resultados_json(resultados, str(json_file), "entrada.csv")
        
        # 5. Verifica se arquivo JSON foi criado
        assert json_file.exists()
        
        # 6. Verifica conteúdo do JSON
        import json
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert data['metadata']['total_processados'] == 2
        assert data['metadata']['total_validos'] == 1
        assert data['metadata']['total_invalidos'] == 1
        assert len(data['resultados']['validados_com_sucesso']) == 1
        assert len(data['resultados']['validados_com_erro']) == 1
    
    @patch('requests.post')
    def test_tratamento_erro_timeout(self, mock_post):
        """Testa tratamento de erro de timeout."""
        csv_content = """username,password
user1@test.com,senha123"""
        
        csv_file = self.temp_dir / "entrada.csv"
        csv_file.write_text(csv_content, encoding='utf-8')
        
        # Mock que simula timeout
        mock_post.side_effect = requests.Timeout("Timeout na requisição")
        
        resultados = self.validator.validar_credenciais_em_lote(str(csv_file))
        
        assert len(resultados) == 1
        assert resultados[0]['is_valid'] is False
        assert 'Timeout' in resultados[0]['error']
    
    @patch('requests.post')
    def test_validacao_formato_locaweb_completo(self, mock_post):
        """Testa validação com formato Locaweb completo."""
        # CSV no formato Locaweb
        csv_content = """name,username,email,mail_domain,cpf,rg,rg_or_ie,password,password_hash,url,internal,gender,address,phone,occupation,mother_name,company_name,cnpj,stealer_family,infection_date,hardware_id,hostname,malware_installation_path,ip,user_agent,brand,source,threat_id,breach_date
,jonas.jesus@locaweb.com.br,jonas.jesus@locaweb.com.br,,,,,9hCAYCRx@zrK8HS,,,,,,,,,,,,,,,,,,LOCAWEB,Telegram,DRP-3187,2025-09-15
,vitor.paixao@locaweb.com.br,vitor.paixao@locaweb.com.br,,,,,locavideo08,,,,,,,,,,,,,,,,,,LOCAWEB,Telegram,DRP-3187,2025-09-15"""
        
        csv_file = self.temp_dir / "locaweb.csv"
        csv_file.write_text(csv_content, encoding='utf-8')
        
        # Mock de resposta HTTP
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        resultados = self.validator.validar_credenciais_em_lote(str(csv_file))
        
        assert len(resultados) == 2
        assert resultados[0]['username'] == 'jonas.jesus@locaweb.com.br'
        assert resultados[1]['username'] == 'vitor.paixao@locaweb.com.br'
        assert all(r['is_valid'] for r in resultados)
        
        # Verifica se as chamadas HTTP foram feitas com os dados corretos
        assert mock_post.call_count == 2
        calls = mock_post.call_args_list
        assert calls[0][1]['data']['username'] == 'jonas.jesus@locaweb.com.br'
        assert calls[0][1]['data']['password'] == '9hCAYCRx@zrK8HS'
        assert calls[1][1]['data']['username'] == 'vitor.paixao@locaweb.com.br'
        assert calls[1][1]['data']['password'] == 'locavideo08'
