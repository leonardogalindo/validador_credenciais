"""Configurações centralizadas da aplicação.

Este módulo contém todas as configurações da aplicação, incluindo
configuração obrigatória de logging conforme especificado no GEMINI.md.
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()


class LoggingConfig:
    """Configuração centralizada do sistema de logging.

    Implementa a política de logging obrigatória conforme GEMINI.md:
    - logs/debug.log → debug detalhado (DEV, nível DEBUG)
    - logs/error.log → erros e falhas (DEV/PROD, nível ERROR)
    - logs/audit.log → auditoria crítica (PROD, nível INFO)
    - logs/settings.log → compatibilidade histórica (DEV, nível DEBUG)
    """

    # Diretório base para logs
    LOG_DIR = Path("logs")

    # Configurações de arquivos de log
    LOG_FILES = {
        "debug": "debug.log",
        "error": "error.log",
        "audit": "audit.log",
        "settings": "settings.log",
    }

    # Formatos de log
    FORMATS = {
        "detailed": "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s",
        "simple": "%(asctime)s - %(levelname)s - %(message)s",
        "audit": "%(asctime)s - AUDIT - %(message)s",
        "settings": "%(asctime)s - SETTINGS - %(message)s",
    }

    # Níveis de log por ambiente
    LOG_LEVELS = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }

    @classmethod
    def get_log_level(cls, level_name: Optional[str] = None) -> int:
        """Obtém o nível de log configurado.

        Args:
            level_name (Optional[str]): Nome do nível. Se None, usa variável de ambiente.

        Returns:
            int: Nível de logging.
        """
        if level_name is None:
            level_name = os.getenv("LOG_LEVEL", "INFO")

        return cls.LOG_LEVELS.get(level_name.upper(), logging.INFO)

    @classmethod
    def create_log_directory(cls) -> None:
        """Cria o diretório de logs se não existir."""
        cls.LOG_DIR.mkdir(exist_ok=True)

    @classmethod
    def get_log_file_path(cls, log_type: str) -> Path:
        """Obtém o caminho completo para um arquivo de log.

        Args:
            log_type (str): Tipo do log (debug, error, audit, settings).

        Returns:
            Path: Caminho completo para o arquivo.
        """
        filename = cls.LOG_FILES.get(log_type, f"{log_type}.log")
        return cls.LOG_DIR / filename

    @classmethod
    def create_file_handler(
        cls, log_type: str, level: int, format_type: str = "detailed"
    ) -> logging.FileHandler:
        """Cria um handler de arquivo para logging.

        Args:
            log_type (str): Tipo do log (debug, error, audit, settings).
            level (int): Nível mínimo de logging.
            format_type (str): Tipo de formato a usar.

        Returns:
            logging.FileHandler: Handler configurado.
        """
        log_path = cls.get_log_file_path(log_type)
        handler = logging.FileHandler(log_path, encoding="utf-8")
        handler.setLevel(level)

        formatter = logging.Formatter(cls.FORMATS[format_type])
        handler.setFormatter(formatter)

        return handler

    @classmethod
    def create_console_handler(
        cls, level: int, format_type: str = "simple"
    ) -> logging.StreamHandler:
        """Cria um handler de console para logging.

        Args:
            level (int): Nível mínimo de logging.
            format_type (str): Tipo de formato a usar.

        Returns:
            logging.StreamHandler: Handler configurado.
        """
        handler = logging.StreamHandler()
        handler.setLevel(level)

        formatter = logging.Formatter(cls.FORMATS[format_type])
        handler.setFormatter(formatter)

        return handler


class AppConfig:
    """Configurações gerais da aplicação."""

    # Configurações da API Locaweb
    LOCAWEB_LOGIN_URL = os.getenv("LOCAWEB_LOGIN_URL")
    REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))

    # Configurações de CSV
    CSV_ENCODING = os.getenv("CSV_ENCODING", "utf-8")
    DEFAULT_CSV_COLUMNS = ["username", "password"]

    # Configurações de diretórios
    DATA_DIR = Path("data")
    CSV_INPUT_DIR = DATA_DIR / "csv"
    JSON_OUTPUT_DIR = DATA_DIR / "json"

    # Configurações de segurança
    INCLUDE_PASSWORDS_IN_OUTPUT = (
        os.getenv("INCLUDE_PASSWORDS_IN_OUTPUT", "false").lower() == "true"
    )

    @classmethod
    def create_directories(cls) -> None:
        """Cria os diretórios necessários da aplicação."""
        cls.DATA_DIR.mkdir(exist_ok=True)
        cls.CSV_INPUT_DIR.mkdir(exist_ok=True)
        cls.JSON_OUTPUT_DIR.mkdir(exist_ok=True)

    @classmethod
    def validate_required_settings(cls) -> None:
        """Valida se as configurações obrigatórias estão definidas.

        Raises:
            ValueError: Se alguma configuração obrigatória não estiver definida.
        """
        if not cls.LOCAWEB_LOGIN_URL:
            raise ValueError(
                "LOCAWEB_LOGIN_URL deve ser definida no arquivo .env. "
                "Exemplo: LOCAWEB_LOGIN_URL=https://sua-api.com/endpoint"
            )


def setup_logging(
    console_level: Optional[str] = None, log_file: Optional[str] = None
) -> None:
    """Configura o sistema de logging da aplicação.

    Implementa a configuração obrigatória de logging conforme GEMINI.md.

    Args:
        console_level (Optional[str]): Nível de log para console.
        log_file (Optional[str]): Arquivo adicional para logs.
    """
    # Cria diretório de logs
    LoggingConfig.create_log_directory()

    # Obtém nível de log
    base_level = LoggingConfig.get_log_level(console_level)

    # Limpa configurações anteriores
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(logging.DEBUG)  # Permite todos os níveis

    # Handler para console
    console_handler = LoggingConfig.create_console_handler(base_level)
    root_logger.addHandler(console_handler)

    # Handler para arquivo adicional se especificado
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(base_level)
        formatter = logging.Formatter(LoggingConfig.FORMATS["detailed"])
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # Handlers específicos conforme GEMINI.md

    # 1. Debug log - desenvolvimento (nível DEBUG)
    debug_handler = LoggingConfig.create_file_handler(
        "debug", logging.DEBUG, "detailed"
    )
    root_logger.addHandler(debug_handler)

    # 2. Error log - erros e falhas (nível ERROR)
    error_handler = LoggingConfig.create_file_handler(
        "error", logging.ERROR, "detailed"
    )
    root_logger.addHandler(error_handler)

    # 3. Audit log - auditoria crítica (nível INFO)
    audit_logger = logging.getLogger("audit")
    audit_handler = LoggingConfig.create_file_handler("audit", logging.INFO, "audit")
    audit_logger.addHandler(audit_handler)
    audit_logger.setLevel(logging.INFO)
    audit_logger.propagate = False  # Não propaga para root logger

    # 4. Settings log - compatibilidade histórica (nível DEBUG)
    settings_logger = logging.getLogger("settings")
    settings_handler = LoggingConfig.create_file_handler(
        "settings", logging.DEBUG, "settings"
    )
    settings_logger.addHandler(settings_handler)
    settings_logger.setLevel(logging.DEBUG)
    settings_logger.propagate = False  # Não propaga para root logger

    # Log inicial das configurações
    settings_logger = logging.getLogger("settings")
    settings_logger.debug("Sistema de logging inicializado")
    settings_logger.debug(f"Nível de console: {console_level or 'INFO'}")
    settings_logger.debug(f"Arquivo adicional: {log_file or 'Nenhum'}")
    settings_logger.debug(f"Diretório de logs: {LoggingConfig.LOG_DIR}")


def get_app_settings() -> Dict[str, Any]:
    """Retorna todas as configurações da aplicação.

    Returns:
        Dict[str, Any]: Dicionário com todas as configurações.
    """
    return {
        "api": {
            "locaweb_login_url": AppConfig.LOCAWEB_LOGIN_URL,
            "request_timeout": AppConfig.REQUEST_TIMEOUT,
        },
        "csv": {
            "encoding": AppConfig.CSV_ENCODING,
            "default_columns": AppConfig.DEFAULT_CSV_COLUMNS,
        },
        "directories": {
            "data_dir": str(AppConfig.DATA_DIR),
            "csv_input_dir": str(AppConfig.CSV_INPUT_DIR),
            "json_output_dir": str(AppConfig.JSON_OUTPUT_DIR),
        },
        "security": {
            "include_passwords_in_output": AppConfig.INCLUDE_PASSWORDS_IN_OUTPUT
        },
        "logging": {
            "log_dir": str(LoggingConfig.LOG_DIR),
            "log_files": LoggingConfig.LOG_FILES,
            "available_levels": list(LoggingConfig.LOG_LEVELS.keys()),
        },
    }


def initialize_app() -> None:
    """Inicializa a aplicação criando diretórios necessários e validando configurações."""
    # Valida configurações obrigatórias
    AppConfig.validate_required_settings()

    # Cria diretórios necessários
    AppConfig.create_directories()
    LoggingConfig.create_log_directory()

    # Log da inicialização
    settings_logger = logging.getLogger("settings")
    settings_logger.debug("Aplicação inicializada")
    settings_logger.debug(
        f"Diretórios criados: {AppConfig.DATA_DIR}, {LoggingConfig.LOG_DIR}"
    )
    settings_logger.debug(f"URL da API configurada: {AppConfig.LOCAWEB_LOGIN_URL}")


if __name__ == "__main__":
    # Exemplo de uso das configurações
    print("=== Configurações da Aplicação ===")

    # Inicializa a aplicação
    initialize_app()

    # Configura logging
    setup_logging("DEBUG")

    # Obtém e exibe configurações
    settings = get_app_settings()

    import json

    print(json.dumps(settings, indent=2, ensure_ascii=False))

    # Testa logging
    logger = logging.getLogger(__name__)
    audit_logger = logging.getLogger("audit")
    settings_logger = logging.getLogger("settings")

    logger.debug("Teste de log DEBUG")
    logger.info("Teste de log INFO")
    logger.warning("Teste de log WARNING")
    logger.error("Teste de log ERROR")

    audit_logger.info("Teste de auditoria")
    settings_logger.debug("Teste de configurações")

    print("\nLogs salvos em:")
    for log_type, filename in LoggingConfig.LOG_FILES.items():
        print(f"  {log_type}: {LoggingConfig.get_log_file_path(log_type)}")
