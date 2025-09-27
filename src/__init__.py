"""Pacote principal do validador de credenciais.

Este pacote contém módulos para validação de credenciais via API da Locaweb,
manipulação de arquivos CSV e configurações centralizadas.
"""

from .csv_handler import CSVHandler, criar_csv_handler
from .locaweb import LocawebCredentialValidator, criar_validador_locaweb
from .settings import AppConfig, LoggingConfig, initialize_app, setup_logging

__version__ = "1.0.0"
__author__ = "Validador de Credenciais"

__all__ = [
    "criar_validador_locaweb",
    "LocawebCredentialValidator",
    "criar_csv_handler",
    "CSVHandler",
    "setup_logging",
    "initialize_app",
    "AppConfig",
    "LoggingConfig",
]
