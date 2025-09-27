"""Testes de integração para o sistema completo.

Este módulo testa a integração entre todos os componentes do sistema,
simulando fluxos completos de validação de credenciais.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import requests

from src import criar_csv_handler, criar_validador_locaweb
from src.settings import (AppConfig, LoggingConfig, initialize_app,
                          setup_logging)


class TestIntegracaoCompleta:
    """Testes de integração do sistema completo."""

    # Headers esperados em todas as requisições
    EXPECTED_HEADERS = {
        "Content-Type": "application/x-www-form-urlencoded",
        "X-Security-Test": "security-tests-lwsa",
        "User-Agent": "Locaweb-Security-Credential-Validator/1.0",
    }

    def setup_method(self):
        """Configuração para cada teste de integração."""
        self.temp_dir = Path(tempfile.mkdtemp())

        # Configura diretórios temporários
        self.original_data_dir = AppConfig.DATA_DIR
        self.original_log_dir = LoggingConfig.LOG_DIR

        AppConfig.DATA_DIR = self.temp_dir / "data"
        AppConfig.CSV_INPUT_DIR = AppConfig.DATA_DIR / "csv"
        AppConfig.TXT_OUTPUT_DIR = AppConfig.DATA_DIR / "txt"
        AppConfig.JSON_OUTPUT_DIR = AppConfig.DATA_DIR / "json"
        LoggingConfig.LOG_DIR = self.temp_dir / "logs"

    def teardown_method(self):
        """Limpeza após cada teste."""
        import shutil

        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

        # Restaura configurações originais
        AppConfig.DATA_DIR = self.original_data_dir
        LoggingConfig.LOG_DIR = self.original_log_dir

    def _verify_headers_in_calls(self, mock_post):
        """Verifica se todas as chamadas incluem os headers de segurança."""
        for call in mock_post.call_args_list:
            call_kwargs = call[1]  # kwargs da chamada
            assert "headers" in call_kwargs, "Headers não encontrados na chamada"
            headers = call_kwargs["headers"]
            assert headers == self.EXPECTED_HEADERS, f"Headers incorretos: {headers}"

    @patch("requests.post")
    def test_fluxo_completo_formato_simples(self, mock_post):
        """Testa fluxo completo com formato CSV simples."""
        # 1. Inicializa aplicação
        with patch.object(AppConfig, "LOCAWEB_LOGIN_URL", "https://test.com"):
            initialize_app()
            setup_logging("INFO")

        # 2. Cria arquivo CSV de entrada
        csv_content = """username,password
user1@test.com,senha123
user2@test.com,senha456
user3@test.com,senha789"""

        csv_file = AppConfig.CSV_INPUT_DIR / "credenciais.csv"
        csv_file.write_text(csv_content, encoding="utf-8")

        # 3. Mock das respostas HTTP (2 sucessos, 1 falha)
        def mock_post_side_effect(url, data, **kwargs):
            mock_response = Mock()
            if data["username"] == "user2@test.com":
                mock_response.status_code = 401  # Falha
            else:
                mock_response.status_code = 200  # Sucesso
            return mock_response

        mock_post.side_effect = mock_post_side_effect

        # 4. Executa validação
        validador = criar_validador_locaweb("https://test.com")
        resultados = validador.validar_credenciais_em_lote(
            str(csv_file), incluir_senha_resultado=True
        )

        # 5. Salva resultados
        csv_output = AppConfig.TXT_OUTPUT_DIR / "resultados.csv"
        json_output = AppConfig.JSON_OUTPUT_DIR / "relatorio.json"

        validador.salvar_resultados_csv(resultados, str(csv_output))
        validador.salvar_resultados_json(
            resultados, str(json_output), "credenciais.csv"
        )

        # 6. Verifica resultados
        assert len(resultados) == 3
        assert sum(1 for r in resultados if r["is_valid"]) == 2
        assert sum(1 for r in resultados if not r["is_valid"]) == 1

        # 7. Verifica arquivos de saída
        assert csv_output.exists()
        assert json_output.exists()

        # 8. Verifica conteúdo do JSON
        with open(json_output, "r", encoding="utf-8") as f:
            json_data = json.load(f)

        assert json_data["metadata"]["total_processados"] == 3
        assert json_data["metadata"]["total_validos"] == 2
        assert json_data["metadata"]["total_invalidos"] == 1
        assert len(json_data["resultados"]["validados_com_sucesso"]) == 2
        assert len(json_data["resultados"]["validados_com_erro"]) == 1

        # 9. Verifica se senhas estão incluídas no JSON
        sucesso = json_data["resultados"]["validados_com_sucesso"][0]
        assert "password" in sucesso
        assert sucesso["password"] in ["senha123", "senha789"]

        erro = json_data["resultados"]["validados_com_erro"][0]
        assert "password" in erro
        assert erro["password"] == "senha456"

        # 10. Verifica headers de segurança em todas as chamadas
        assert mock_post.call_count == 3
        self._verify_headers_in_calls(mock_post)

    @patch("requests.post")
    def test_fluxo_completo_formato_locaweb(self, mock_post):
        """Testa fluxo completo com formato Locaweb."""
        # 1. Inicializa aplicação
        with patch.object(AppConfig, "LOCAWEB_LOGIN_URL", "https://test.com"):
            initialize_app()

        # 2. Cria arquivo CSV no formato Locaweb
        csv_content = """name,username,email,mail_domain,cpf,rg,rg_or_ie,password,password_hash,url,internal,gender,address,phone,occupation,mother_name,company_name,cnpj,stealer_family,infection_date,hardware_id,hostname,malware_installation_path,ip,user_agent,brand,source,threat_id,breach_date
,jonas.jesus@locaweb.com.br,jonas.jesus@locaweb.com.br,,,,,9hCAYCRx@zrK8HS,,,,,,,,,,,,,,,,,,LOCAWEB,Telegram,DRP-3187,2025-09-15
,vitor.paixao@locaweb.com.br,vitor.paixao@locaweb.com.br,,,,,locavideo08,,,,,,,,,,,,,,,,,,LOCAWEB,Telegram,DRP-3187,2025-09-15
,emailmarketing@locaweb.com.br,emailmarketing@locaweb.com.br,,,,,Paralela09,,,,,,,,,,,,,,,,,,LOCAWEB,Telegram,DRP-3187,2025-09-15"""

        csv_file = AppConfig.CSV_INPUT_DIR / "locaweb.csv"
        csv_file.write_text(csv_content, encoding="utf-8")

        # 3. Mock das respostas HTTP
        def mock_post_side_effect(url, data, **kwargs):
            mock_response = Mock()
            # Simula falha para emailmarketing
            if "emailmarketing" in data["username"]:
                mock_response.status_code = 403
            else:
                mock_response.status_code = 200
            return mock_response

        mock_post.side_effect = mock_post_side_effect

        # 4. Executa validação
        validador = criar_validador_locaweb("https://test.com")
        resultados = validador.validar_credenciais_em_lote(
            str(csv_file), incluir_senha_resultado=True
        )

        # 5. Verifica extração correta dos dados
        assert len(resultados) == 3

        usernames = [r["username"] for r in resultados]
        passwords = [r["password"] for r in resultados]

        assert "jonas.jesus@locaweb.com.br" in usernames
        assert "vitor.paixao@locaweb.com.br" in usernames
        assert "emailmarketing@locaweb.com.br" in usernames

        assert "9hCAYCRx@zrK8HS" in passwords
        assert "locavideo08" in passwords
        assert "Paralela09" in passwords

        # 6. Verifica resultados de validação
        validos = [r for r in resultados if r["is_valid"]]
        invalidos = [r for r in resultados if not r["is_valid"]]

        assert len(validos) == 2
        assert len(invalidos) == 1
        assert invalidos[0]["username"] == "emailmarketing@locaweb.com.br"

        # 7. Verifica headers de segurança
        assert mock_post.call_count == 3
        self._verify_headers_in_calls(mock_post)

    @patch("requests.post")
    def test_tratamento_erros_rede(self, mock_post):
        """Testa tratamento de erros de rede durante validação."""
        # 1. Inicializa aplicação
        with patch.object(AppConfig, "LOCAWEB_LOGIN_URL", "https://test.com"):
            initialize_app()

        # 2. Cria arquivo CSV
        csv_content = """username,password
user1@test.com,senha123
user2@test.com,senha456
user3@test.com,senha789"""

        csv_file = AppConfig.CSV_INPUT_DIR / "credenciais.csv"
        csv_file.write_text(csv_content, encoding="utf-8")

        # 3. Mock que simula diferentes tipos de erro
        def mock_post_side_effect(url, data, **kwargs):
            username = data["username"]
            if username == "user1@test.com":
                # Sucesso
                mock_response = Mock()
                mock_response.status_code = 200
                return mock_response
            elif username == "user2@test.com":
                # Timeout
                raise requests.Timeout("Timeout na requisição")
            else:
                # Erro de conexão
                raise requests.ConnectionError("Erro de conexão")

        mock_post.side_effect = mock_post_side_effect

        # 4. Executa validação
        validador = criar_validador_locaweb("https://test.com")
        resultados = validador.validar_credenciais_em_lote(str(csv_file))

        # 5. Verifica tratamento de erros
        assert len(resultados) == 3

        # Primeiro usuário: sucesso
        assert resultados[0]["is_valid"] is True
        assert resultados[0]["error"] is None

        # Segundo usuário: timeout
        assert resultados[1]["is_valid"] is False
        assert "Timeout" in resultados[1]["error"]

        # Terceiro usuário: erro de conexão
        assert resultados[2]["is_valid"] is False
        assert "conexão" in resultados[2]["error"].lower()

        # 6. Verifica headers de segurança (todas as 3 chamadas foram feitas)
        assert mock_post.call_count == 3
        self._verify_headers_in_calls(mock_post)

    def test_validacao_estrutura_csv(self):
        """Testa validação de estrutura de arquivos CSV."""
        # 1. Inicializa aplicação
        with patch.object(AppConfig, "LOCAWEB_LOGIN_URL", "https://test.com"):
            initialize_app()

        csv_handler = criar_csv_handler()

        # 2. Testa arquivo válido
        csv_valido = """username,password,email
user1@test.com,senha123,user1@test.com"""

        csv_file = AppConfig.CSV_INPUT_DIR / "valido.csv"
        csv_file.write_text(csv_valido, encoding="utf-8")

        resultado = csv_handler.validar_estrutura_csv(
            str(csv_file), ["username", "password"]
        )

        assert resultado["valido"] is True
        assert len(resultado["colunas_faltantes"]) == 0

        # 3. Testa arquivo inválido
        csv_invalido = """nome,email
João,joao@test.com"""

        csv_file_invalido = AppConfig.CSV_INPUT_DIR / "invalido.csv"
        csv_file_invalido.write_text(csv_invalido, encoding="utf-8")

        resultado = csv_handler.validar_estrutura_csv(
            str(csv_file_invalido), ["username", "password"]
        )

        assert resultado["valido"] is False
        assert "username" in resultado["colunas_faltantes"]
        assert "password" in resultado["colunas_faltantes"]

    def test_criacao_template_automatica(self):
        """Testa criação automática de template."""
        # 1. Inicializa aplicação
        with patch.object(AppConfig, "LOCAWEB_LOGIN_URL", "https://test.com"):
            initialize_app()

        csv_handler = criar_csv_handler()

        # 2. Cria template no formato Locaweb
        template_file = AppConfig.CSV_INPUT_DIR / "template.csv"

        colunas = [
            "name",
            "username",
            "email",
            "mail_domain",
            "cpf",
            "rg",
            "rg_or_ie",
            "password",
            "password_hash",
            "url",
            "internal",
            "gender",
            "address",
            "phone",
            "occupation",
            "mother_name",
            "company_name",
            "cnpj",
            "stealer_family",
            "infection_date",
            "hardware_id",
            "hostname",
            "malware_installation_path",
            "ip",
            "user_agent",
            "brand",
            "source",
            "threat_id",
            "breach_date",
        ]

        dados_exemplo = [
            {
                col: (
                    f"exemplo_{col}"
                    if col not in ["username", "password"]
                    else f"user@test.com" if col == "username" else "senha123"
                )
                for col in colunas
            }
        ]

        csv_handler.criar_template_csv(str(template_file), colunas, dados_exemplo)

        # 3. Verifica se template foi criado corretamente
        assert template_file.exists()

        # 4. Verifica se pode ler o template criado
        credenciais = csv_handler.ler_credenciais(str(template_file))
        assert len(credenciais) == 1
        assert credenciais[0]["username"] == "user@test.com"
        assert credenciais[0]["password"] == "senha123"

    def test_logs_sistema_completo(self):
        """Testa sistema de logs durante operação completa."""
        # 1. Inicializa aplicação com logging
        with patch.object(AppConfig, "LOCAWEB_LOGIN_URL", "https://test.com"):
            initialize_app()
            setup_logging("DEBUG")

        # 2. Verifica se arquivos de log foram criados
        assert LoggingConfig.LOG_DIR.exists()

        # 3. Testa logs específicos
        import logging

        # Log geral
        logger = logging.getLogger("test_integration")
        logger.info("Teste de log de integração")

        # Log de auditoria
        audit_logger = logging.getLogger("audit")
        audit_logger.info("INTEGRATION_TEST - teste de auditoria")

        # Log de configurações
        settings_logger = logging.getLogger("settings")
        settings_logger.debug("Teste de log de configurações")

        # 4. Verifica se logs não geram exceções
        # (os arquivos de log devem ser criados automaticamente)
        debug_log = LoggingConfig.get_log_file_path("debug")
        error_log = LoggingConfig.get_log_file_path("error")
        audit_log = LoggingConfig.get_log_file_path("audit")
        settings_log = LoggingConfig.get_log_file_path("settings")

        # Os arquivos podem não existir ainda se não houve logs suficientes,
        # mas o sistema deve estar configurado para criá-los
        assert debug_log.parent.exists()  # Diretório deve existir
        assert error_log.parent.exists()
        assert audit_log.parent.exists()
        assert settings_log.parent.exists()


class TestIntegracaoModulos:
    """Testes de integração entre módulos específicos."""

    def setup_method(self):
        """Configuração para testes de integração de módulos."""
        self.temp_dir = Path(tempfile.mkdtemp())

    def teardown_method(self):
        """Limpeza após testes."""
        import shutil

        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_integracao_csv_handler_com_locaweb(self):
        """Testa integração entre CSVHandler e LocawebCredentialValidator."""
        # 1. Cria CSV handler
        csv_handler = criar_csv_handler()

        # 2. Cria arquivo CSV
        csv_content = """username,password
user1@test.com,senha123
user2@test.com,senha456"""

        csv_file = self.temp_dir / "test.csv"
        csv_file.write_text(csv_content, encoding="utf-8")

        # 3. Lê credenciais via CSV handler
        credenciais = csv_handler.ler_credenciais(str(csv_file))

        # 4. Simula validação (sem fazer requisições HTTP reais)
        resultados = []
        for i, cred in enumerate(credenciais):
            resultado = {
                "username": cred["username"],
                "password": cred["password"],
                "is_valid": i % 2 == 0,  # Alterna válido/inválido
                "error": None if i % 2 == 0 else "Erro simulado",
                "linha_original": i + 2,
            }
            resultados.append(resultado)

        # 5. Salva resultados via CSV handler
        json_file = self.temp_dir / "resultados.json"
        csv_handler.salvar_resultados_json(resultados, str(json_file), "test.csv")

        # 6. Verifica integração
        assert json_file.exists()

        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert data["metadata"]["arquivo_origem"] == "test.csv"
        assert data["metadata"]["total_processados"] == 2
        assert len(data["resultados"]["validados_com_sucesso"]) == 1
        assert len(data["resultados"]["validados_com_erro"]) == 1

    def test_integracao_settings_com_aplicacao(self):
        """Testa integração das configurações com a aplicação."""
        # 1. Configura variáveis de ambiente
        with patch.dict(
            "os.environ",
            {
                "LOCAWEB_LOGIN_URL": "https://integration.test.com",
                "REQUEST_TIMEOUT": "45",
                "CSV_ENCODING": "utf-8",
            },
        ):
            # 2. Recarrega configurações
            import importlib

            import src.settings

            importlib.reload(src.settings)
            from src.settings import AppConfig, get_app_settings

            # 3. Verifica se configurações foram aplicadas
            assert AppConfig.LOCAWEB_LOGIN_URL == "https://integration.test.com"
            assert AppConfig.REQUEST_TIMEOUT == 45

            # 4. Cria validador com configurações
            validador = criar_validador_locaweb()
            assert validador.login_url == "https://integration.test.com"
            assert validador.timeout == 45

            # 5. Verifica settings completas
            settings = get_app_settings()
            assert (
                settings["api"]["locaweb_login_url"] == "https://integration.test.com"
            )
            assert settings["api"]["request_timeout"] == 45

    @patch("requests.post")
    def test_pipeline_completo_dados_reais(self, mock_post):
        """Testa pipeline completo com dados similares aos reais."""
        # 1. Simula dados reais da Locaweb
        csv_real = """name,username,email,mail_domain,cpf,rg,rg_or_ie,password,password_hash,url,internal,gender,address,phone,occupation,mother_name,company_name,cnpj,stealer_family,infection_date,hardware_id,hostname,malware_installation_path,ip,user_agent,brand,source,threat_id,breach_date
,admin@empresa.com.br,admin@empresa.com.br,,,,,admin123,,,,,,,,,,,,,,,,,,LOCAWEB,DataBreach,DRP-001,2025-01-15
,user@empresa.com.br,user@empresa.com.br,,,,,user456,,,,,,,,,,,,,,,,,,LOCAWEB,DataBreach,DRP-002,2025-01-15
,test@empresa.com.br,test@empresa.com.br,,,,,test789,,,,,,,,,,,,,,,,,,LOCAWEB,DataBreach,DRP-003,2025-01-15"""

        csv_file = self.temp_dir / "dados_reais.csv"
        csv_file.write_text(csv_real, encoding="utf-8")

        # 2. Mock de respostas HTTP realistas
        def mock_post_side_effect(url, data, **kwargs):
            mock_response = Mock()
            username = data["username"]

            if username == "admin@empresa.com.br":
                mock_response.status_code = 200  # Admin válido
            elif username == "user@empresa.com.br":
                mock_response.status_code = 401  # Usuário inválido
            else:
                mock_response.status_code = 403  # Test bloqueado

            return mock_response

        mock_post.side_effect = mock_post_side_effect

        # 3. Executa pipeline completo
        validador = criar_validador_locaweb("https://test.com")
        resultados = validador.validar_credenciais_em_lote(
            str(csv_file), incluir_senha_resultado=True
        )

        # 4. Salva em JSON
        json_file = self.temp_dir / "relatorio_real.json"
        validador.salvar_resultados_json(resultados, str(json_file), "dados_reais.csv")

        # 5. Verifica resultados finais
        with open(json_file, "r", encoding="utf-8") as f:
            relatorio = json.load(f)

        # Verifica metadados
        assert relatorio["metadata"]["arquivo_origem"] == "dados_reais.csv"
        assert relatorio["metadata"]["total_processados"] == 3
        assert relatorio["metadata"]["total_validos"] == 1
        assert relatorio["metadata"]["total_invalidos"] == 2
        assert relatorio["metadata"]["taxa_sucesso"] == "33.3%"

        # Verifica sucessos
        sucessos = relatorio["resultados"]["validados_com_sucesso"]
        assert len(sucessos) == 1
        assert sucessos[0]["username"] == "admin@empresa.com.br"
        assert sucessos[0]["password"] == "admin123"

        # Verifica erros
        erros = relatorio["resultados"]["validados_com_erro"]
        assert len(erros) == 2
        usernames_erro = [e["username"] for e in erros]
        assert "user@empresa.com.br" in usernames_erro
        assert "test@empresa.com.br" in usernames_erro

        # 6. Verifica headers de segurança
        assert mock_post.call_count == 3
        self._verify_headers_in_calls(mock_post)
