"""Módulo de menu para seleção de empresa/serviço.

Este módulo fornece uma interface de menu para o usuário escolher
entre diferentes serviços de validação de credenciais.
Segue as diretrizes estabelecidas no GEMINI.md.
"""

import logging
from enum import Enum
from typing import Any, Callable, Dict, Optional

try:
    from .locaweb import criar_validador_locaweb
except ImportError:
    from locaweb import criar_validador_locaweb


# Configuração do logger para este módulo
logger = logging.getLogger(__name__)


class TipoEmpresa(Enum):
    """Enumeração dos tipos de empresa disponíveis."""

    LOCAWEB = "locaweb"


class MenuValidador:
    """Classe responsável pelo menu de seleção de validadores."""

    def __init__(self) -> None:
        """Inicializa o menu de validadores."""
        self.opcoes = {
            "1": {
                "nome": "Locaweb",
                "tipo": TipoEmpresa.LOCAWEB,
                "descricao": "Validação de credenciais via API da Locaweb",
                "factory": criar_validador_locaweb,
            }
        }

        logger.debug("MenuValidador inicializado com opções disponíveis")

    def exibir_menu(self) -> None:
        """Exibe o menu de opções para o usuário."""
        print("\n" + "=" * 60)
        print("🔐 VALIDADOR DE CREDENCIAIS")
        print("=" * 60)
        print("\nEscolha o serviço para validação:")
        print()

        for opcao, dados in self.opcoes.items():
            print(f"  {opcao}. {dados['nome']}")
            print(f"     {dados['descricao']}")
            print()

        print("  0. Sair")
        print("\n" + "-" * 60)

    def obter_escolha_usuario(self) -> Optional[str]:
        """Obtém a escolha do usuário via input.

        Returns:
            Optional[str]: Opção escolhida pelo usuário ou None para sair.
        """
        while True:
            try:
                escolha = input("Digite sua opção: ").strip()

                if escolha == "0":
                    logger.info("👋 Usuário escolheu sair")
                    return None

                if escolha in self.opcoes:
                    opcao_selecionada = self.opcoes[escolha]
                    logger.info(f"✅ Usuário selecionou: {opcao_selecionada['nome']}")
                    return escolha

                print("❌ Opção inválida! Por favor, escolha uma opção válida.")

            except KeyboardInterrupt:
                print("\n\n👋 Saindo...")
                logger.info("🛑 Usuário interrompeu com Ctrl+C")
                return None
            except Exception as e:
                logger.error(f"💥 Erro ao obter escolha do usuário: {str(e)}")
                print("❌ Erro inesperado. Tente novamente.")

    def criar_validador(self, opcao: str) -> Any:
        """Cria uma instância do validador baseado na opção escolhida.

        Args:
            opcao (str): Opção escolhida pelo usuário.

        Returns:
            Any: Instância do validador correspondente.

        Raises:
            ValueError: Se a opção for inválida.
        """
        if opcao not in self.opcoes:
            raise ValueError(f"Opção inválida: {opcao}")

        dados_opcao = self.opcoes[opcao]
        factory_function = dados_opcao["factory"]

        logger.debug(f"🏭 Criando validador para: {dados_opcao['nome']}")

        try:
            validador = factory_function()
            logger.info(f"✅ Validador {dados_opcao['nome']} criado com sucesso")
            return validador
        except Exception as e:
            logger.error(f"💥 Erro ao criar validador {dados_opcao['nome']}: {str(e)}")
            raise

    def obter_info_opcao(self, opcao: str) -> Dict[str, Any]:
        """Obtém informações sobre uma opção específica.

        Args:
            opcao (str): Opção para obter informações.

        Returns:
            Dict[str, Any]: Informações da opção.

        Raises:
            ValueError: Se a opção for inválida.
        """
        if opcao not in self.opcoes:
            raise ValueError(f"Opção inválida: {opcao}")

        return self.opcoes[opcao].copy()

    def listar_opcoes_disponiveis(self) -> Dict[str, str]:
        """Lista todas as opções disponíveis.

        Returns:
            Dict[str, str]: Mapeamento de opção para nome da empresa.
        """
        return {opcao: dados["nome"] for opcao, dados in self.opcoes.items()}

    def executar_menu_interativo(self) -> Optional[Any]:
        """Executa o menu interativo e retorna o validador escolhido.

        Returns:
            Optional[Any]: Validador escolhido ou None se o usuário cancelar.
        """
        logger.info("🚀 Iniciando menu interativo")

        try:
            self.exibir_menu()
            escolha = self.obter_escolha_usuario()

            if escolha is None:
                logger.info("🚪 Menu encerrado pelo usuário")
                return None

            validador = self.criar_validador(escolha)
            info_opcao = self.obter_info_opcao(escolha)

            print(f"\n✅ {info_opcao['nome']} selecionado com sucesso!")
            print(f"📋 {info_opcao['descricao']}")

            return validador

        except Exception as e:
            logger.error(f"💥 Erro durante execução do menu: {str(e)}")
            print(f"\n❌ Erro: {str(e)}")
            return None


def criar_menu() -> MenuValidador:
    """Factory function para criar uma instância do menu.

    Returns:
        MenuValidador: Instância configurada do menu.
    """
    return MenuValidador()


def executar_selecao_empresa() -> Optional[Any]:
    """Função de conveniência para executar seleção de empresa.

    Returns:
        Optional[Any]: Validador escolhido ou None se cancelado.
    """
    menu = criar_menu()
    return menu.executar_menu_interativo()
