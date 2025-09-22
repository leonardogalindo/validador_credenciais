"""Pacote principal do validador de credenciais.

Este pacote contém módulos para validação de credenciais via API da Locaweb,
manipulação de arquivos CSV e configurações centralizadas.
"""

from .locaweb import criar_validador_locaweb, LocawebCredentialValidator
from .csv_handler import criar_csv_handler, CSVHandler
from .settings import setup_logging, initialize_app, AppConfig, LoggingConfig

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
    "LoggingConfig"
]
