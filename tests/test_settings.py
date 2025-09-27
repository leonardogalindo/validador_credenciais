"""Testes unitários para o módulo settings.

Este módulo testa todas as funcionalidades de configuração,
incluindo logging, configurações da aplicação e inicialização.
"""

import logging
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.settings import (AppConfig, LoggingConfig, get_app_settings,
                          initialize_app, setup_logging)


class TestLoggingConfig:
    """Testes para a classe LoggingConfig."""

    def test_get_log_level_default(self):
        """Testa obtenção do nível de log padrão."""
        with patch.dict("os.environ", {}, clear=True):
            level = LoggingConfig.get_log_level()
            assert level == logging.INFO

    def test_get_log_level_from_env(self):
        """Testa obtenção do nível de log da variável de ambiente."""
        with patch.dict("os.environ", {"LOG_LEVEL": "DEBUG"}):
            level = LoggingConfig.get_log_level()
            assert level == logging.DEBUG

        with patch.dict("os.environ", {"LOG_LEVEL": "ERROR"}):
            level = LoggingConfig.get_log_level()
            assert level == logging.ERROR

    def test_get_log_level_invalid(self):
        """Testa obtenção do nível de log com valor inválido."""
        level = LoggingConfig.get_log_level("INVALID")
        assert level == logging.INFO  # Deve retornar padrão

    def test_get_log_level_parameter(self):
        """Testa obtenção do nível de log por parâmetro."""
        level = LoggingConfig.get_log_level("WARNING")
        assert level == logging.WARNING

    def test_create_log_directory(self):
        """Testa criação do diretório de logs."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Muda temporariamente o diretório de logs
            original_log_dir = LoggingConfig.LOG_DIR
            LoggingConfig.LOG_DIR = Path(temp_dir) / "test_logs"

            try:
                LoggingConfig.create_log_directory()
                assert LoggingConfig.LOG_DIR.exists()
                assert LoggingConfig.LOG_DIR.is_dir()
            finally:
                LoggingConfig.LOG_DIR = original_log_dir

    def test_get_log_file_path(self):
        """Testa obtenção do caminho do arquivo de log."""
        path = LoggingConfig.get_log_file_path("debug")
        assert path.name == "debug.log"
        assert path.parent == LoggingConfig.LOG_DIR

        path = LoggingConfig.get_log_file_path("custom")
        assert path.name == "custom.log"

    def test_create_file_handler(self):
        """Testa criação de handler de arquivo."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_log_dir = LoggingConfig.LOG_DIR
            LoggingConfig.LOG_DIR = Path(temp_dir)

            try:
                handler = LoggingConfig.create_file_handler("test", logging.DEBUG)
                assert isinstance(handler, logging.FileHandler)
                assert handler.level == logging.DEBUG
            finally:
                LoggingConfig.LOG_DIR = original_log_dir

    def test_create_console_handler(self):
        """Testa criação de handler de console."""
        handler = LoggingConfig.create_console_handler(logging.INFO)
        assert isinstance(handler, logging.StreamHandler)
        assert handler.level == logging.INFO


class TestAppConfig:
    """Testes para a classe AppConfig."""

    def test_locaweb_login_url_from_env(self):
        """Testa obtenção da URL da variável de ambiente."""
        with patch.dict("os.environ", {"LOCAWEB_LOGIN_URL": "https://test.com"}):
            # Recarrega a classe para pegar nova variável
            import importlib

            import src.settings

            importlib.reload(src.settings)
            from src.settings import AppConfig

            assert AppConfig.LOCAWEB_LOGIN_URL == "https://test.com"

    def test_request_timeout_default(self):
        """Testa timeout padrão."""
        with patch.dict("os.environ", {}, clear=True):
            import importlib

            import src.settings

            importlib.reload(src.settings)
            from src.settings import AppConfig

            assert AppConfig.REQUEST_TIMEOUT == 30

    def test_request_timeout_from_env(self):
        """Testa timeout da variável de ambiente."""
        with patch.dict("os.environ", {"REQUEST_TIMEOUT": "60"}):
            import importlib

            import src.settings

            importlib.reload(src.settings)
            from src.settings import AppConfig

            assert AppConfig.REQUEST_TIMEOUT == 60

    def test_csv_encoding_default(self):
        """Testa encoding padrão do CSV."""
        with patch.dict("os.environ", {}, clear=True):
            import importlib

            import src.settings

            importlib.reload(src.settings)
            from src.settings import AppConfig

            assert AppConfig.CSV_ENCODING == "utf-8"

    def test_create_directories(self):
        """Testa criação dos diretórios da aplicação."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_data_dir = AppConfig.DATA_DIR
            AppConfig.DATA_DIR = Path(temp_dir) / "test_data"
            AppConfig.CSV_INPUT_DIR = AppConfig.DATA_DIR / "csv"
            AppConfig.TXT_OUTPUT_DIR = AppConfig.DATA_DIR / "txt"
            AppConfig.JSON_OUTPUT_DIR = AppConfig.DATA_DIR / "json"

            try:
                AppConfig.create_directories()

                assert AppConfig.DATA_DIR.exists()
                assert AppConfig.CSV_INPUT_DIR.exists()
                assert AppConfig.TXT_OUTPUT_DIR.exists()
                assert AppConfig.JSON_OUTPUT_DIR.exists()
            finally:
                AppConfig.DATA_DIR = original_data_dir

    def test_validate_required_settings_success(self):
        """Testa validação de configurações obrigatórias com sucesso."""
        with patch.object(AppConfig, "LOCAWEB_LOGIN_URL", "https://test.com"):
            # Não deve lançar exceção
            AppConfig.validate_required_settings()

    def test_validate_required_settings_failure(self):
        """Testa validação de configurações obrigatórias com falha."""
        with patch.object(AppConfig, "LOCAWEB_LOGIN_URL", None):
            with pytest.raises(ValueError, match="LOCAWEB_LOGIN_URL deve ser definida"):
                AppConfig.validate_required_settings()

        with patch.object(AppConfig, "LOCAWEB_LOGIN_URL", ""):
            with pytest.raises(ValueError, match="LOCAWEB_LOGIN_URL deve ser definida"):
                AppConfig.validate_required_settings()

    def test_get_default_output_path(self):
        """Testa geração de caminho padrão de saída."""
        path = AppConfig.get_default_output_path("credenciais.csv")
        expected = AppConfig.TXT_OUTPUT_DIR / "resultados_credenciais.csv"
        assert path == expected

        path = AppConfig.get_default_output_path("test_file.csv")
        expected = AppConfig.TXT_OUTPUT_DIR / "resultados_test_file.csv"
        assert path == expected


class TestSetupLogging:
    """Testes para a função setup_logging."""

    def setup_method(self):
        """Configuração antes de cada teste."""
        # Limpa handlers existentes
        root_logger = logging.getLogger()
        root_logger.handlers.clear()

        # Limpa loggers específicos
        for logger_name in ["audit", "settings"]:
            logger = logging.getLogger(logger_name)
            logger.handlers.clear()

    def teardown_method(self):
        """Limpeza após cada teste."""
        # Limpa handlers
        root_logger = logging.getLogger()
        root_logger.handlers.clear()

        for logger_name in ["audit", "settings"]:
            logger = logging.getLogger(logger_name)
            logger.handlers.clear()

    @patch.object(LoggingConfig, "create_log_directory")
    @patch.object(LoggingConfig, "create_console_handler")
    @patch.object(LoggingConfig, "create_file_handler")
    def test_setup_logging_basic(
        self, mock_file_handler, mock_console_handler, mock_create_dir
    ):
        """Testa configuração básica de logging."""
        # Mock dos handlers
        mock_console_handler.return_value = MagicMock()
        mock_file_handler.return_value = MagicMock()

        setup_logging()

        # Verifica se diretório foi criado
        mock_create_dir.assert_called_once()

        # Verifica se handlers foram criados
        mock_console_handler.assert_called_once()
        assert mock_file_handler.call_count >= 2  # debug e error handlers

    @patch.object(LoggingConfig, "create_log_directory")
    def test_setup_logging_with_file(self, mock_create_dir):
        """Testa configuração de logging com arquivo adicional."""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file_path = temp_file.name

        try:
            setup_logging(log_file=temp_file_path)

            # Verifica se arquivo foi configurado
            root_logger = logging.getLogger()
            file_handlers = [
                h for h in root_logger.handlers if isinstance(h, logging.FileHandler)
            ]
            assert len(file_handlers) >= 1
        finally:
            os.unlink(temp_file_path)

    def test_setup_logging_levels(self):
        """Testa configuração com diferentes níveis."""
        for level in ["DEBUG", "INFO", "WARNING", "ERROR"]:
            # Limpa handlers antes de cada teste
            root_logger = logging.getLogger()
            root_logger.handlers.clear()

            with tempfile.TemporaryDirectory() as temp_dir:
                original_log_dir = LoggingConfig.LOG_DIR
                LoggingConfig.LOG_DIR = Path(temp_dir)

                try:
                    setup_logging(level)

                    # Verifica se loggers específicos foram configurados
                    audit_logger = logging.getLogger("audit")
                    settings_logger = logging.getLogger("settings")

                    assert len(audit_logger.handlers) > 0
                    assert len(settings_logger.handlers) > 0
                    assert not audit_logger.propagate
                    assert not settings_logger.propagate
                finally:
                    LoggingConfig.LOG_DIR = original_log_dir


class TestInitializeApp:
    """Testes para a função initialize_app."""

    @patch.object(AppConfig, "validate_required_settings")
    @patch.object(AppConfig, "create_directories")
    @patch.object(LoggingConfig, "create_log_directory")
    def test_initialize_app(self, mock_log_dir, mock_app_dirs, mock_validate):
        """Testa inicialização da aplicação."""
        initialize_app()

        mock_validate.assert_called_once()
        mock_app_dirs.assert_called_once()
        mock_log_dir.assert_called_once()

    @patch.object(AppConfig, "validate_required_settings")
    def test_initialize_app_validation_failure(self, mock_validate):
        """Testa inicialização com falha na validação."""
        mock_validate.side_effect = ValueError("Configuração inválida")

        with pytest.raises(ValueError, match="Configuração inválida"):
            initialize_app()


class TestGetAppSettings:
    """Testes para a função get_app_settings."""

    def test_get_app_settings_structure(self):
        """Testa estrutura das configurações retornadas."""
        settings = get_app_settings()

        # Verifica estrutura principal
        assert "api" in settings
        assert "csv" in settings
        assert "directories" in settings
        assert "security" in settings
        assert "logging" in settings

        # Verifica seção API
        assert "locaweb_login_url" in settings["api"]
        assert "request_timeout" in settings["api"]

        # Verifica seção CSV
        assert "encoding" in settings["csv"]
        assert "default_columns" in settings["csv"]

        # Verifica seção de diretórios
        assert "data_dir" in settings["directories"]
        assert "csv_input_dir" in settings["directories"]
        assert "txt_output_dir" in settings["directories"]
        assert "json_output_dir" in settings["directories"]

        # Verifica seção de segurança
        assert "include_passwords_in_output" in settings["security"]

        # Verifica seção de logging
        assert "log_dir" in settings["logging"]
        assert "log_files" in settings["logging"]
        assert "available_levels" in settings["logging"]

    def test_get_app_settings_types(self):
        """Testa tipos dos valores nas configurações."""
        settings = get_app_settings()

        # Verifica tipos
        assert isinstance(settings["api"]["request_timeout"], int)
        assert isinstance(settings["csv"]["encoding"], str)
        assert isinstance(settings["csv"]["default_columns"], list)
        assert isinstance(settings["security"]["include_passwords_in_output"], bool)
        assert isinstance(settings["logging"]["available_levels"], list)


class TestSettingsIntegration:
    """Testes de integração para o módulo settings."""

    def test_configuracao_completa_aplicacao(self):
        """Testa configuração completa da aplicação."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Configura diretórios temporários
            original_data_dir = AppConfig.DATA_DIR
            original_log_dir = LoggingConfig.LOG_DIR

            AppConfig.DATA_DIR = Path(temp_dir) / "data"
            LoggingConfig.LOG_DIR = Path(temp_dir) / "logs"

            # Atualiza outros diretórios
            AppConfig.CSV_INPUT_DIR = AppConfig.DATA_DIR / "csv"
            AppConfig.TXT_OUTPUT_DIR = AppConfig.DATA_DIR / "txt"
            AppConfig.JSON_OUTPUT_DIR = AppConfig.DATA_DIR / "json"

            try:
                with patch.object(AppConfig, "LOCAWEB_LOGIN_URL", "https://test.com"):
                    # Inicializa aplicação
                    initialize_app()

                    # Configura logging
                    setup_logging("INFO")

                    # Verifica se diretórios foram criados
                    assert AppConfig.DATA_DIR.exists()
                    assert AppConfig.CSV_INPUT_DIR.exists()
                    assert AppConfig.TXT_OUTPUT_DIR.exists()
                    assert AppConfig.JSON_OUTPUT_DIR.exists()
                    assert LoggingConfig.LOG_DIR.exists()

                    # Verifica se loggers estão funcionando
                    logger = logging.getLogger("test")
                    audit_logger = logging.getLogger("audit")
                    settings_logger = logging.getLogger("settings")

                    # Testa logs (não deve gerar exceção)
                    logger.info("Teste de log")
                    audit_logger.info("Teste de auditoria")
                    settings_logger.debug("Teste de configurações")

            finally:
                # Restaura configurações originais
                AppConfig.DATA_DIR = original_data_dir
                LoggingConfig.LOG_DIR = original_log_dir

    @patch.dict(
        "os.environ",
        {
            "LOCAWEB_LOGIN_URL": "https://env.test.com",
            "REQUEST_TIMEOUT": "45",
            "LOG_LEVEL": "DEBUG",
            "CSV_ENCODING": "latin-1",
            "INCLUDE_PASSWORDS_IN_OUTPUT": "true",
        },
    )
    def test_configuracao_via_variaveis_ambiente(self):
        """Testa configuração via variáveis de ambiente."""
        # Recarrega módulo para pegar novas variáveis
        import importlib

        import src.settings

        importlib.reload(src.settings)
        from src.settings import AppConfig, LoggingConfig, get_app_settings

        # Verifica se configurações foram carregadas
        assert AppConfig.LOCAWEB_LOGIN_URL == "https://env.test.com"
        assert AppConfig.REQUEST_TIMEOUT == 45
        assert AppConfig.CSV_ENCODING == "latin-1"
        assert AppConfig.INCLUDE_PASSWORDS_IN_OUTPUT is True

        # Verifica nível de log
        level = LoggingConfig.get_log_level()
        assert level == logging.DEBUG

        # Verifica se settings refletem as configurações
        settings = get_app_settings()
        assert settings["api"]["locaweb_login_url"] == "https://env.test.com"
        assert settings["api"]["request_timeout"] == 45
        assert settings["csv"]["encoding"] == "latin-1"
        assert settings["security"]["include_passwords_in_output"] is True
