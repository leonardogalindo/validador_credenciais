#!/usr/bin/env python3
"""Ponto de entrada principal do validador de credenciais.

Este módulo serve como ponto de entrada principal da aplicação,
processando automaticamente arquivos CSV do diretório data/csv
utilizando o validador Locaweb.
Segue as diretrizes estabelecidas no GEMINI.md.
"""

import logging
import sys
from pathlib import Path
from typing import Any, List

from src import criar_csv_handler, criar_validador_locaweb
from src.menu import executar_selecao_empresa
from src.settings import AppConfig, initialize_app, setup_logging


def descobrir_arquivos_csv() -> List[Path]:
    """Descobre arquivos CSV no diretório data/csv.

    Returns:
        List[Path]: Lista de arquivos CSV encontrados.
    """
    logger = logging.getLogger(__name__)

    csv_dir = AppConfig.CSV_INPUT_DIR
    if not csv_dir.exists():
        logger.warning(f"Diretório {csv_dir} não existe")
        return []

    # Busca por arquivos .csv
    arquivos_csv = list(csv_dir.glob("*.csv"))

    if not arquivos_csv:
        logger.warning(f"Nenhum arquivo CSV encontrado em {csv_dir}")
        return []

    logger.info(
        f"Encontrados {len(arquivos_csv)} arquivo(s) CSV: {[f.name for f in arquivos_csv]}"
    )
    return arquivos_csv


def processar_arquivo_csv(arquivo_entrada: Path, validador: Any) -> None:
    """Processa um arquivo CSV com credenciais.

    Args:
        arquivo_entrada (Path): Caminho para arquivo CSV com credenciais.
        validador (Any): Instância do validador Locaweb.
    """
    logger = logging.getLogger(__name__)
    audit_logger = logging.getLogger("audit")

    try:
        if not arquivo_entrada.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {arquivo_entrada}")

        logger.info(f"📁 Processando arquivo: {arquivo_entrada.name}")
        audit_logger.info(f"BATCH_VALIDATION_START - file: {arquivo_entrada.name}")

        # Processa com o validador Locaweb
        resultados = validador.validar_credenciais_em_lote(
            str(arquivo_entrada),
            incluir_senha_resultado=True,  # Inclui senhas para o JSON
        )

        # Estatísticas
        total = len(resultados)
        validas = sum(1 for r in resultados if r["is_valid"])
        invalidas = total - validas
        erros = sum(1 for r in resultados if r.get("error"))

        print(f"\n=== 📊 Resultados: {arquivo_entrada.name} ===")
        print(f"📋 Total processadas: {total}")
        print(f"✅ Credenciais válidas: {validas}")
        print(f"❌ Credenciais inválidas: {invalidas}")
        print(f"🚨 Erros de conexão: {erros}")
        print(f"📈 Taxa de sucesso: {(validas/total*100):.1f}%" if total > 0 else "N/A")

        # Log detalhado dos resultados
        logger.info(f"📊 PROCESSAMENTO CONCLUÍDO - {arquivo_entrada.name}")
        logger.info(f"   📋 Total: {total} credenciais")
        logger.info(f"   ✅ Válidas: {validas}")
        logger.info(f"   ❌ Inválidas: {invalidas}")
        logger.info(f"   🚨 Erros: {erros}")
        logger.info(f"   📈 Taxa de sucesso: {(validas/total*100):.1f}%")

        # Gera caminho de saída JSON
        arquivo_json = (
            AppConfig.JSON_OUTPUT_DIR / f"relatorio_{arquivo_entrada.stem}.json"
        )

        # Salva em JSON (formato principal)
        csv_handler = criar_csv_handler()
        csv_handler.salvar_resultados_json(
            resultados, str(arquivo_json), arquivo_entrada.name
        )
        print(f"📄 Relatório JSON salvo em: {arquivo_json}")
        logger.info(f"📄 Relatório JSON gerado: {arquivo_json}")

        # Remove arquivo CSV após processamento
        if csv_handler.remover_arquivo_csv(str(arquivo_entrada)):
            print(f"🗑️  Arquivo CSV removido: {arquivo_entrada.name}")
        else:
            logger.warning(f"⚠️  Não foi possível remover: {arquivo_entrada.name}")

        audit_logger.info(
            f"BATCH_VALIDATION_END - file: {arquivo_entrada.name}, "
            f"total: {total}, valid: {validas}, invalid: {invalidas}, errors: {erros}"
        )

    except Exception as e:
        logger.error(f"Erro ao processar {arquivo_entrada.name}: {str(e)}")
        audit_logger.error(
            f"BATCH_VALIDATION_ERROR - file: {arquivo_entrada.name}, error: {str(e)}"
        )
        print(f"Erro ao processar {arquivo_entrada.name}: {e}")
        raise


def criar_template_se_necessario() -> None:
    """Cria um template CSV se o diretório estiver vazio."""
    logger = logging.getLogger(__name__)

    csv_dir = AppConfig.CSV_INPUT_DIR
    if not csv_dir.exists() or not any(csv_dir.glob("*.csv")):
        logger.info("Nenhum arquivo CSV encontrado, criando template de exemplo")

        try:
            csv_handler = criar_csv_handler()
            template_path = csv_dir / "template_credenciais.csv"

            # Formato simplificado: apenas username e password
            colunas = ["username", "password"]

            dados_exemplo = [
                {"username": "usuario1@exemplo.com", "password": "senha123"},
                {"username": "usuario2@exemplo.com", "password": "senha456"},
                {"username": "usuario3@exemplo.com", "password": "senha789"},
            ]

            csv_handler.criar_template_csv(str(template_path), colunas, dados_exemplo)

            print(f"✅ Template criado: {template_path}")
            print("   Formato: username,password")
            print("   Edite o arquivo com suas credenciais e execute novamente.")
            logger.info(f"Template CSV criado: {template_path}")

        except Exception as e:
            logger.error(f"Erro ao criar template: {str(e)}")
            print(f"Erro ao criar template: {e}")


def main() -> int:
    """Função principal da aplicação.

    Processa automaticamente todos os arquivos CSV encontrados no diretório
    data/csv usando o validador Locaweb.

    Returns:
        int: Código de saída (0 = sucesso, 1 = erro).
    """
    try:
        # Inicializa a aplicação (cria diretórios e valida configurações)
        initialize_app()

        # Configura logging usando settings.py (nível INFO por padrão)
        setup_logging()

        logger = logging.getLogger(__name__)
        settings_logger = logging.getLogger("settings")
        audit_logger = logging.getLogger("audit")

        # Log das configurações iniciais
        settings_logger.debug("Aplicação iniciada - modo interativo")
        settings_logger.debug(f"Timeout: {AppConfig.REQUEST_TIMEOUT}s")
        settings_logger.debug(f"Diretório CSV: {AppConfig.CSV_INPUT_DIR}")
        settings_logger.debug(f"Diretório saída JSON: {AppConfig.JSON_OUTPUT_DIR}")
        settings_logger.debug("Modo: Apenas JSON (CSV removido após processamento)")

        audit_logger.info("APPLICATION_START - modo interativo")

        # Executa menu de seleção de empresa
        validador = executar_selecao_empresa()

        if validador is None:
            print("\n👋 Operação cancelada pelo usuário.")
            logger.info("Aplicação cancelada pelo usuário no menu")
            return 0

        print(f"\nBuscando arquivos CSV em: {AppConfig.CSV_INPUT_DIR}")

        # Descobre arquivos CSV
        arquivos_csv = descobrir_arquivos_csv()

        if not arquivos_csv:
            print("Nenhum arquivo CSV encontrado.")
            criar_template_se_necessario()
            return 0

        # Processa cada arquivo encontrado
        arquivos_processados = 0
        arquivos_com_erro = 0

        for arquivo_csv in arquivos_csv:
            try:
                print(f"\n--- Processando: {arquivo_csv.name} ---")
                processar_arquivo_csv(arquivo_csv, validador)
                arquivos_processados += 1

            except Exception as e:
                logger.error(f"Falha ao processar {arquivo_csv.name}: {str(e)}")
                print(f"Erro: {e}")
                arquivos_com_erro += 1
                continue

        # Resumo final
        print(f"\n=== Resumo da Execução ===")
        print(f"Arquivos encontrados: {len(arquivos_csv)}")
        print(f"Arquivos processados: {arquivos_processados}")
        print(f"Arquivos com erro: {arquivos_com_erro}")

        audit_logger.info(
            f"APPLICATION_END - processados: {arquivos_processados}, "
            f"erros: {arquivos_com_erro}"
        )

        logger.info("Aplicação finalizada com sucesso")

        # Retorna erro se houve falhas
        return 1 if arquivos_com_erro > 0 else 0

    except KeyboardInterrupt:
        logger = logging.getLogger(__name__)
        logger.warning("Aplicação interrompida pelo usuário")
        print("\nOperação cancelada pelo usuário.")
        return 1

    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Erro inesperado na aplicação: {str(e)}")
        print(f"Erro inesperado: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
