"""Módulo para validação de credenciais via API da Locaweb.

Este módulo fornece funcionalidades para validar credenciais em lote
a partir de arquivos CSV, utilizando a API de tickets da Locaweb.
Segue as diretrizes estabelecidas no GEMINI.md.
"""

import logging
import os
from typing import Any, Dict, List, Optional

import requests
from dotenv import load_dotenv

from .csv_handler import criar_csv_handler

# Carrega variáveis de ambiente
load_dotenv()

# Configuração do logger para este módulo
logger = logging.getLogger(__name__)


class LocawebCredentialValidator:
    """Validador de credenciais via API da Locaweb.

    Esta classe encapsula as operações necessárias para validar credenciais
    em lote a partir de arquivos CSV, utilizando a API de tickets da Locaweb.
    """

    def __init__(self, login_url: Optional[str] = None, timeout: int = 30) -> None:
        """Inicializa o validador de credenciais Locaweb.

        Args:
            login_url (Optional[str]): URL da API de login. Se não fornecida,
                será obtida da variável de ambiente LOCAWEB_LOGIN_URL.
            timeout (int): Timeout para requisições HTTP em segundos.
        """
        self.login_url = login_url or os.getenv("LOCAWEB_LOGIN_URL")
        self.timeout = timeout
        self.csv_handler = criar_csv_handler()

        if not self.login_url:
            raise ValueError(
                "URL de login deve ser fornecida via parâmetro ou variável de ambiente LOCAWEB_LOGIN_URL"
            )

        logger.debug(
            f"LocawebCredentialValidator inicializado com login_url: {self.login_url}"
        )

    def validar_credencial_unica(self, username: str, password: str) -> bool:
        """Valida uma única credencial via API da Locaweb.

        Args:
            username (str): Nome de usuário para validação.
            password (str): Senha para validação.

        Returns:
            bool: True se as credenciais são válidas, False caso contrário.

        Raises:
            ValueError: Se username ou password estão vazios.
            requests.RequestException: Se houve erro na requisição HTTP.
        """
        if not username or not password:
            raise ValueError("Username e password não podem estar vazios")

        logger.info(f"Validando credenciais para usuário: {username}")

        try:
            # Dados para a requisição POST
            data = {"username": username, "password": password}

            # Headers para identificar testes de segurança da Locaweb
            headers = {
                "Content-Type": "application/x-www-form-urlencoded",
                "X-Security-Test": "security-tests-lwsa",
                "User-Agent": "Locaweb-Security-Credential-Validator/1.0",
            }

            # Realiza a requisição POST para a API
            response = requests.post(
                self.login_url, data=data, timeout=self.timeout, headers=headers
            )

            # Considera credenciais válidas se status code for 200
            is_valid = response.status_code == 201

            if is_valid:
                logger.info(
                    f"✅ SUCESSO - Credenciais válidas para usuário: {username}"
                )
            else:
                logger.warning(
                    f"❌ ERRO - Credenciais inválidas para usuário: {username} (HTTP {response.status_code})"
                )

            return is_valid

        except requests.RequestException as e:
            logger.error(f"Erro na requisição HTTP para usuário {username}: {str(e)}")
            raise
        except Exception as e:
            logger.error(
                f"Erro inesperado durante validação para usuário {username}: {str(e)}"
            )
            raise

    def validar_credenciais_em_lote(
        self, caminho_csv: str, incluir_senha_resultado: bool = False
    ) -> List[Dict[str, Any]]:
        """Valida credenciais em lote a partir de um arquivo CSV.

        Args:
            caminho_csv (str): Caminho para o arquivo CSV com credenciais.
            incluir_senha_resultado (bool): Se True, inclui a senha nos resultados.
                ATENÇÃO: Não recomendado por questões de segurança.

        Returns:
            List[Dict[str, Any]]: Lista com resultados da validação.
                Cada item contém: username, is_valid, error (se houver).
                Se incluir_senha_resultado=True, também contém password.
        """
        logger.info(f"Iniciando validação em lote do arquivo: {caminho_csv}")

        # Usa o csv_handler para ler as credenciais
        credenciais = self.csv_handler.ler_credenciais(caminho_csv)
        resultados = []

        for i, credencial in enumerate(credenciais, 1):
            username = credencial["username"]
            password = credencial["password"]

            logger.info(f"🔍 Validando credencial {i}/{len(credenciais)}: {username}")

            resultado = {"username": username, "is_valid": False, "error": None}

            # Inclui senha apenas se solicitado (não recomendado)
            if incluir_senha_resultado:
                resultado["password"] = password

            try:
                resultado["is_valid"] = self.validar_credencial_unica(
                    username, password
                )
                if resultado["is_valid"]:
                    logger.info(
                        f"✅ SUCESSO {i}/{len(credenciais)} - {username}: Credenciais válidas"
                    )
                else:
                    logger.warning(
                        f"❌ FALHA {i}/{len(credenciais)} - {username}: Credenciais inválidas"
                    )
            except Exception as e:
                resultado["error"] = str(e)
                logger.error(f"🚨 ERRO {i}/{len(credenciais)} - {username}: {str(e)}")

            resultados.append(resultado)

        validas = sum(1 for r in resultados if r["is_valid"])
        invalidas = len(resultados) - validas
        erros = sum(1 for r in resultados if r.get("error"))

        logger.info(f"📊 RESUMO DA VALIDAÇÃO:")
        logger.info(f"   ✅ Válidas: {validas}")
        logger.info(f"   ❌ Inválidas: {invalidas}")
        logger.info(f"   🚨 Erros: {erros}")
        logger.info(f"   📈 Taxa de sucesso: {(validas/len(resultados)*100):.1f}%")

        return resultados

    def salvar_resultados_json(
        self,
        resultados: List[Dict[str, Any]],
        caminho_saida: str,
        nome_arquivo_origem: str,
    ) -> None:
        """Salva os resultados da validação em um arquivo JSON organizado.

        Args:
            resultados (List[Dict[str, Any]]): Resultados da validação.
            caminho_saida (str): Caminho para salvar o arquivo JSON.
            nome_arquivo_origem (str): Nome do arquivo CSV original.
        """
        # Delega para o csv_handler
        self.csv_handler.salvar_resultados_json(
            resultados, caminho_saida, nome_arquivo_origem
        )


def criar_validador_locaweb(
    login_url: Optional[str] = None,
) -> LocawebCredentialValidator:
    """Factory function para criar uma instância do validador Locaweb.

    Args:
        login_url (Optional[str]): URL da API de login. Se não fornecida,
            será obtida da variável de ambiente LOCAWEB_LOGIN_URL.

    Returns:
        LocawebCredentialValidator: Instância configurada do validador.
    """
    logger.debug("Criando nova instância do validador Locaweb")
    return LocawebCredentialValidator(login_url=login_url)
