"""Módulo para manipulação de arquivos CSV.

Este módulo fornece funcionalidades para leitura e escrita de arquivos CSV,
especificamente para credenciais e resultados de validação.
Segue as diretrizes estabelecidas no GEMINI.md.
"""

import csv
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Configuração do logger para este módulo
logger = logging.getLogger(__name__)


class CSVHandler:
    """Manipulador de arquivos CSV para credenciais e resultados.

    Esta classe encapsula todas as operações de leitura e escrita
    de arquivos CSV relacionados à validação de credenciais.
    """

    def __init__(self, encoding: str = "utf-8") -> None:
        """Inicializa o manipulador de CSV.

        Args:
            encoding (str): Codificação de caracteres para os arquivos CSV.
        """
        self.encoding = encoding
        logger.debug(f"CSVHandler inicializado com encoding: {encoding}")

    def ler_credenciais(self, caminho_arquivo: str) -> List[Dict[str, str]]:
        """Lê credenciais de um arquivo CSV.

        O arquivo deve conter as colunas 'username' e 'password'.

        Args:
            caminho_arquivo (str): Caminho para o arquivo CSV contendo as credenciais.

        Returns:
            List[Dict[str, str]]: Lista de dicionários com as credenciais.
                Cada dicionário contém 'username', 'password' e 'linha_original'.

        Raises:
            FileNotFoundError: Se o arquivo não foi encontrado.
            ValueError: Se o arquivo não possui as colunas 'username' e 'password'.
            PermissionError: Se não há permissão para ler o arquivo.
        """
        caminho = Path(caminho_arquivo)

        if not caminho.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {caminho_arquivo}")

        if not caminho.is_file():
            raise ValueError(f"Caminho não é um arquivo: {caminho_arquivo}")

        logger.info(f"Lendo credenciais do arquivo: {caminho_arquivo}")

        credenciais = []
        linhas_ignoradas = 0

        try:
            with open(caminho, "r", encoding=self.encoding, newline="") as arquivo:
                reader = csv.DictReader(arquivo)

                # Verifica se as colunas necessárias existem
                if not reader.fieldnames:
                    raise ValueError("Arquivo CSV está vazio ou não possui cabeçalho")

                if "username" not in reader.fieldnames:
                    raise ValueError(
                        f"Coluna 'username' não encontrada. "
                        f"Colunas disponíveis: {list(reader.fieldnames)}"
                    )

                if "password" not in reader.fieldnames:
                    raise ValueError(
                        f"Coluna 'password' não encontrada. "
                        f"Colunas disponíveis: {list(reader.fieldnames)}"
                    )

                # Lê as credenciais linha por linha
                for linha_num, linha in enumerate(
                    reader, start=2
                ):  # start=2 porque linha 1 é o cabeçalho
                    usuario = linha.get("username", "").strip()
                    senha = linha.get("password", "").strip()

                    # Valida apenas linhas com username E password preenchidos
                    if usuario and senha and usuario != "" and senha != "":
                        # Validações adicionais
                        if len(usuario) < 3:
                            linhas_ignoradas += 1
                            logger.warning(
                                f"⚠️  Linha {linha_num} ignorada: username muito curto (mínimo 3 caracteres)"
                            )
                            continue

                        if len(senha) < 1:
                            linhas_ignoradas += 1
                            logger.warning(
                                f"⚠️  Linha {linha_num} ignorada: password vazio"
                            )
                            continue

                        # Ignora passwords que são placeholders
                        if senha in [
                            "[NOT_SAVED]",
                            "[REDACTED]",
                            "[HIDDEN]",
                            "N/A",
                            "NULL",
                        ]:
                            linhas_ignoradas += 1
                            logger.warning(
                                f"⚠️  Linha {linha_num} ignorada: password é placeholder ({senha})"
                            )
                            continue

                        credenciais.append(
                            {
                                "username": usuario,
                                "password": senha,
                                "linha_original": linha_num,
                            }
                        )
                        logger.debug(
                            f"✅ Linha {linha_num}: {usuario} - credencial válida carregada"
                        )
                    else:
                        linhas_ignoradas += 1
                        motivos = []
                        if not usuario or usuario == "":
                            motivos.append("username vazio ou ausente")
                        if not senha or senha == "":
                            motivos.append("password vazio ou ausente")

                        logger.warning(
                            f"⚠️  Linha {linha_num} ignorada: {', '.join(motivos)}"
                        )

            logger.info(
                f"📊 Carregadas {len(credenciais)} credenciais válidas do arquivo"
            )
            if linhas_ignoradas > 0:
                logger.warning(
                    f"⚠️  Total de {linhas_ignoradas} linhas ignoradas por dados incompletos"
                )

            return credenciais

        except PermissionError as e:
            logger.error(f"Sem permissão para ler o arquivo: {caminho_arquivo}")
            raise
        except UnicodeDecodeError as e:
            logger.error(f"Erro de codificação ao ler arquivo: {str(e)}")
            raise ValueError(
                f"Erro de codificação no arquivo. Tente usar encoding diferente."
            )
        except Exception as e:
            logger.error(f"Erro inesperado ao ler arquivo CSV: {str(e)}")
            raise

    def salvar_resultados(
        self,
        resultados: List[Dict[str, Any]],
        caminho_saida: str,
        incluir_senha: bool = False,
    ) -> None:
        """Salva os resultados da validação em um arquivo CSV.

        Args:
            resultados (List[Dict[str, Any]]): Resultados da validação.
                Cada item deve conter pelo menos: username, is_valid.
            caminho_saida (str): Caminho para salvar o arquivo de resultados.
            incluir_senha (bool): Se True, inclui a senha no arquivo de saída.
                ATENÇÃO: Não recomendado por questões de segurança.

        Raises:
            ValueError: Se a lista de resultados está vazia.
            PermissionError: Se não há permissão para escrever no arquivo.
        """
        if not resultados:
            raise ValueError("Lista de resultados não pode estar vazia")

        # Cria o diretório pai se não existir
        caminho = Path(caminho_saida)
        caminho.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"Salvando {len(resultados)} resultados em: {caminho_saida}")

        try:
            with open(caminho, "w", encoding=self.encoding, newline="") as arquivo:
                # Define as colunas do arquivo de saída
                fieldnames = ["username", "is_valid", "error"]
                if incluir_senha:
                    fieldnames.insert(1, "password")  # Adiciona após username

                writer = csv.DictWriter(arquivo, fieldnames=fieldnames)
                writer.writeheader()

                for resultado in resultados:
                    linha_saida = {
                        "username": resultado.get("username", ""),
                        "is_valid": resultado.get("is_valid", False),
                        "error": resultado.get("error", ""),
                    }

                    if incluir_senha:
                        linha_saida["password"] = resultado.get("password", "")

                    writer.writerow(linha_saida)

            logger.info(f"Resultados salvos com sucesso em: {caminho_saida}")

            if incluir_senha:
                logger.warning(
                    "ATENÇÃO: Senhas foram incluídas no arquivo de saída. "
                    "Considere questões de segurança."
                )

        except PermissionError as e:
            logger.error(f"Sem permissão para escrever no arquivo: {caminho_saida}")
            raise
        except Exception as e:
            logger.error(f"Erro inesperado ao salvar resultados: {str(e)}")
            raise

    def validar_estrutura_csv(
        self, caminho_arquivo: str, colunas_obrigatorias: List[str] = None
    ) -> Dict[str, Any]:
        """Valida a estrutura de um arquivo CSV.

        Args:
            caminho_arquivo (str): Caminho para o arquivo CSV.
            colunas_obrigatorias (List[str], optional): Lista de colunas que devem existir.
                Se None, usa ['username', 'password'] como padrão.

        Returns:
            Dict[str, Any]: Informações sobre a estrutura do arquivo:
                - valido (bool): Se a estrutura é válida
                - colunas_encontradas (List[str]): Colunas encontradas no arquivo
                - colunas_faltantes (List[str]): Colunas obrigatórias não encontradas
                - total_linhas (int): Total de linhas no arquivo (excluindo cabeçalho)
                - erro (str): Mensagem de erro se houver
        """
        # Define colunas padrão se não fornecidas
        if colunas_obrigatorias is None:
            colunas_obrigatorias = ["username", "password"]

        resultado = {
            "valido": False,
            "colunas_encontradas": [],
            "colunas_faltantes": [],
            "total_linhas": 0,
            "erro": None,
        }

        try:
            caminho = Path(caminho_arquivo)

            if not caminho.exists():
                resultado["erro"] = f"Arquivo não encontrado: {caminho_arquivo}"
                return resultado

            with open(caminho, "r", encoding=self.encoding, newline="") as arquivo:
                reader = csv.DictReader(arquivo)

                if not reader.fieldnames:
                    resultado["erro"] = "Arquivo CSV está vazio ou não possui cabeçalho"
                    return resultado

                resultado["colunas_encontradas"] = list(reader.fieldnames)
                resultado["colunas_faltantes"] = [
                    col for col in colunas_obrigatorias if col not in reader.fieldnames
                ]

                # Conta o número de linhas
                resultado["total_linhas"] = sum(1 for _ in reader)

                # Arquivo é válido se não há colunas faltantes
                resultado["valido"] = len(resultado["colunas_faltantes"]) == 0

                if not resultado["valido"]:
                    resultado["erro"] = (
                        f"Colunas obrigatórias não encontradas: {resultado['colunas_faltantes']}"
                    )

        except Exception as e:
            resultado["erro"] = f"Erro ao validar estrutura: {str(e)}"
            logger.error(resultado["erro"])

        return resultado

    def criar_template_csv(
        self,
        caminho_arquivo: str,
        colunas: List[str] = None,
        dados_exemplo: Optional[List[Dict[str, str]]] = None,
    ) -> None:
        """Cria um arquivo CSV template com as colunas especificadas.

        Args:
            caminho_arquivo (str): Caminho onde criar o arquivo template.
            colunas (List[str], optional): Lista de nomes das colunas.
                Se None, usa ['username', 'password'] como padrão.
            dados_exemplo (Optional[List[Dict[str, str]]]): Dados de exemplo
                para incluir no template.
        """
        # Define colunas padrão se não fornecidas
        if colunas is None:
            colunas = ["username", "password"]

        caminho = Path(caminho_arquivo)
        caminho.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"Criando template CSV em: {caminho_arquivo}")

        try:
            with open(caminho, "w", encoding=self.encoding, newline="") as arquivo:
                writer = csv.DictWriter(arquivo, fieldnames=colunas)
                writer.writeheader()

                if dados_exemplo:
                    for linha in dados_exemplo:
                        writer.writerow(linha)

            logger.info(f"Template CSV criado com sucesso: {caminho_arquivo}")

        except Exception as e:
            logger.error(f"Erro ao criar template CSV: {str(e)}")
            raise

    def _remover_duplicatas(
        self, resultados: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Remove duplicatas baseado em username + password.

        Args:
            resultados: Lista de resultados com possíveis duplicatas

        Returns:
            Lista de resultados únicos (primeira ocorrência mantida)
        """
        vistos = set()
        resultados_unicos = []
        duplicatas_removidas = 0

        for resultado in resultados:
            username = resultado.get("username", "")
            password = resultado.get("password", "")
            chave_unica = (username, password)

            if chave_unica not in vistos:
                vistos.add(chave_unica)
                resultados_unicos.append(resultado)
            else:
                duplicatas_removidas += 1
                logger.debug(f"🔄 Duplicata removida: {username}")

        if duplicatas_removidas > 0:
            logger.info(f"🔄 Removidas {duplicatas_removidas} duplicatas")

        return resultados_unicos

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
        if not resultados:
            raise ValueError("Lista de resultados não pode estar vazia")

        # Cria o diretório pai se não existir
        caminho = Path(caminho_saida)
        caminho.parent.mkdir(parents=True, exist_ok=True)

        # Remove duplicatas baseado em username + password
        resultados_unicos = self._remover_duplicatas(resultados)

        logger.info(
            f"Salvando {len(resultados_unicos)} resultados únicos em JSON: {caminho_saida}"
        )

        # Separa resultados por status
        validados_sucesso = []
        validados_erro = []

        for resultado in resultados_unicos:
            item = {
                "username": resultado.get("username", ""),
                "password": resultado.get("password", ""),
                "timestamp": datetime.now().isoformat(),
                "linha_original": resultado.get("linha_original", 0),
            }

            if resultado.get("is_valid", False):
                validados_sucesso.append(item)
            else:
                item["erro"] = resultado.get("error", "Credenciais inválidas")
                validados_erro.append(item)

        # Estrutura do JSON final
        relatorio = {
            "metadata": {
                "arquivo_origem": nome_arquivo_origem,
                "data_processamento": datetime.now().isoformat(),
                "total_processados": len(resultados_unicos),
                "total_validos": len(validados_sucesso),
                "total_invalidos": len(validados_erro),
                "taxa_sucesso": (
                    f"{(len(validados_sucesso)/len(resultados_unicos)*100):.1f}%"
                    if resultados_unicos
                    else "0%"
                ),
            },
            "resultados": {
                "validados_com_sucesso": validados_sucesso,
                "validados_com_erro": validados_erro,
            },
        }

        try:
            with open(caminho, "w", encoding=self.encoding) as arquivo:
                json.dump(relatorio, arquivo, indent=2, ensure_ascii=False)

            logger.info(f"Relatório JSON salvo com sucesso: {caminho_saida}")
            logger.info(
                f"Resumo: {len(validados_sucesso)} sucessos, {len(validados_erro)} erros"
            )
            logger.warning(
                "ATENÇÃO: O arquivo JSON contém senhas em texto claro. Mantenha-o seguro!"
            )

        except Exception as e:
            logger.error(f"Erro inesperado ao salvar JSON: {str(e)}")
            raise

    def remover_arquivo_csv(self, caminho_arquivo: str) -> bool:
        """Remove arquivo CSV após processamento.

        Args:
            caminho_arquivo: Caminho do arquivo a ser removido

        Returns:
            bool: True se removido com sucesso, False caso contrário
        """
        try:
            arquivo_path = Path(caminho_arquivo)
            if arquivo_path.exists():
                arquivo_path.unlink()
                logger.info(f"🗑️  Arquivo CSV removido: {arquivo_path.name}")
                return True
            else:
                logger.warning(
                    f"⚠️  Arquivo não encontrado para remoção: {caminho_arquivo}"
                )
                return False
        except Exception as e:
            logger.error(f"❌ Erro ao remover arquivo CSV: {e}")
            return False


def criar_csv_handler(encoding: str = "utf-8") -> CSVHandler:
    """Factory function para criar uma instância do manipulador CSV.

    Args:
        encoding (str): Codificação de caracteres para os arquivos CSV.

    Returns:
        CSVHandler: Instância configurada do manipulador.
    """
    logger.debug("Criando nova instância do CSVHandler")
    return CSVHandler(encoding=encoding)
