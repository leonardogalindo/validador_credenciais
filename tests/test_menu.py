"""Testes unitários para o módulo menu.py.

Este módulo contém testes abrangentes para o sistema de menu
de seleção de empresas/serviços, seguindo as diretrizes do GEMINI.md.
"""

from io import StringIO
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.menu import (MenuValidador, TipoEmpresa, criar_menu,
                      executar_selecao_empresa)


class TestTipoEmpresa:
    """Testes para a enumeração TipoEmpresa."""

    @pytest.mark.unit
    def test_valores_enum(self):
        """Testa se os valores do enum estão corretos."""
        assert TipoEmpresa.LOCAWEB.value == "locaweb"


class TestMenuValidador:
    """Testes para a classe MenuValidador."""

    def setup_method(self):
        """Configuração executada antes de cada teste."""
        self.menu = MenuValidador()

    @pytest.mark.unit
    def test_inicializacao(self):
        """Testa inicialização do menu."""
        assert self.menu.opcoes is not None
        assert len(self.menu.opcoes) == 1
        assert "1" in self.menu.opcoes

        # Verifica estrutura das opções
        opcao_locaweb = self.menu.opcoes["1"]
        assert opcao_locaweb["nome"] == "Locaweb"
        assert opcao_locaweb["tipo"] == TipoEmpresa.LOCAWEB
        assert "descricao" in opcao_locaweb
        assert "factory" in opcao_locaweb

    @pytest.mark.unit
    @patch("sys.stdout", new_callable=StringIO)
    def test_exibir_menu(self, mock_stdout):
        """Testa exibição do menu."""
        self.menu.exibir_menu()

        output = mock_stdout.getvalue()
        assert "VALIDADOR DE CREDENCIAIS" in output
        assert "1. Locaweb" in output
        assert "0. Sair" in output

    @pytest.mark.unit
    @patch("builtins.input", return_value="1")
    def test_obter_escolha_usuario_opcao_valida(self, mock_input):
        """Testa obtenção de escolha válida do usuário."""
        escolha = self.menu.obter_escolha_usuario()
        assert escolha == "1"

    @pytest.mark.unit
    @patch("builtins.input", return_value="0")
    def test_obter_escolha_usuario_sair(self, mock_input):
        """Testa quando usuário escolhe sair."""
        escolha = self.menu.obter_escolha_usuario()
        assert escolha is None

    @pytest.mark.unit
    @patch("builtins.input", side_effect=["9", "1"])
    @patch("builtins.print")
    def test_obter_escolha_usuario_opcao_invalida(self, mock_print, mock_input):
        """Testa tratamento de opção inválida."""
        escolha = self.menu.obter_escolha_usuario()
        assert escolha == "1"

        # Verifica se mensagem de erro foi exibida
        mock_print.assert_any_call(
            "❌ Opção inválida! Por favor, escolha uma opção válida."
        )

    @pytest.mark.unit
    @patch("builtins.input", side_effect=KeyboardInterrupt())
    @patch("builtins.print")
    def test_obter_escolha_usuario_keyboard_interrupt(self, mock_print, mock_input):
        """Testa tratamento de interrupção por teclado."""
        escolha = self.menu.obter_escolha_usuario()
        assert escolha is None

    @pytest.mark.unit
    @patch("src.menu.criar_validador_locaweb")
    def test_criar_validador_locaweb(self, mock_criar_validador):
        """Testa criação de validador Locaweb."""
        mock_validador = Mock()
        mock_criar_validador.return_value = mock_validador

        validador = self.menu.criar_validador("1")

        assert validador == mock_validador
        mock_criar_validador.assert_called_once()

    @pytest.mark.unit
    def test_criar_validador_opcao_invalida(self):
        """Testa criação de validador com opção inválida."""
        with pytest.raises(ValueError, match="Opção inválida: 2"):
            self.menu.criar_validador("2")

    @pytest.mark.unit
    @patch("src.menu.criar_validador_locaweb", side_effect=Exception("Erro de criação"))
    def test_criar_validador_erro(self, mock_criar_validador):
        """Testa tratamento de erro na criação do validador."""
        with pytest.raises(Exception, match="Erro de criação"):
            self.menu.criar_validador("1")

    @pytest.mark.unit
    def test_obter_info_opcao_valida(self):
        """Testa obtenção de informações de opção válida."""
        info = self.menu.obter_info_opcao("1")

        assert info["nome"] == "Locaweb"
        assert info["tipo"] == TipoEmpresa.LOCAWEB
        assert "descricao" in info
        assert "factory" in info

    @pytest.mark.unit
    def test_obter_info_opcao_invalida(self):
        """Testa obtenção de informações de opção inválida."""
        with pytest.raises(ValueError, match="Opção inválida: 9"):
            self.menu.obter_info_opcao("9")

    @pytest.mark.unit
    def test_listar_opcoes_disponiveis(self):
        """Testa listagem de opções disponíveis."""
        opcoes = self.menu.listar_opcoes_disponiveis()

        assert opcoes == {"1": "Locaweb"}

    @pytest.mark.unit
    @patch.object(MenuValidador, "exibir_menu")
    @patch.object(MenuValidador, "obter_escolha_usuario", return_value="1")
    @patch.object(MenuValidador, "criar_validador")
    @patch("builtins.print")
    def test_executar_menu_interativo_sucesso(
        self, mock_print, mock_criar_validador, mock_obter_escolha, mock_exibir_menu
    ):
        """Testa execução bem-sucedida do menu interativo."""
        mock_validador = Mock()
        mock_criar_validador.return_value = mock_validador

        resultado = self.menu.executar_menu_interativo()

        assert resultado == mock_validador
        mock_exibir_menu.assert_called_once()
        mock_obter_escolha.assert_called_once()
        mock_criar_validador.assert_called_once_with("1")

    @pytest.mark.unit
    @patch.object(MenuValidador, "exibir_menu")
    @patch.object(MenuValidador, "obter_escolha_usuario", return_value=None)
    def test_executar_menu_interativo_cancelado(
        self, mock_obter_escolha, mock_exibir_menu
    ):
        """Testa execução do menu quando usuário cancela."""
        resultado = self.menu.executar_menu_interativo()

        assert resultado is None
        mock_exibir_menu.assert_called_once()
        mock_obter_escolha.assert_called_once()

    @pytest.mark.unit
    @patch.object(MenuValidador, "exibir_menu")
    @patch.object(
        MenuValidador, "obter_escolha_usuario", side_effect=Exception("Erro no menu")
    )
    @patch("builtins.print")
    def test_executar_menu_interativo_erro(
        self, mock_print, mock_obter_escolha, mock_exibir_menu
    ):
        """Testa tratamento de erro no menu interativo."""
        resultado = self.menu.executar_menu_interativo()

        assert resultado is None
        mock_print.assert_any_call("\n❌ Erro: Erro no menu")


class TestFactoryFunctions:
    """Testes para as funções factory."""

    @pytest.mark.unit
    def test_criar_menu(self):
        """Testa criação de menu via factory."""
        menu = criar_menu()

        assert isinstance(menu, MenuValidador)
        assert menu.opcoes is not None

    @pytest.mark.unit
    @patch("src.menu.criar_menu")
    @patch.object(MenuValidador, "executar_menu_interativo")
    def test_executar_selecao_empresa(self, mock_executar_menu, mock_criar_menu):
        """Testa função de conveniência para seleção de empresa."""
        mock_menu = Mock()
        mock_validador = Mock()
        mock_menu.executar_menu_interativo.return_value = mock_validador
        mock_criar_menu.return_value = mock_menu

        resultado = executar_selecao_empresa()

        assert resultado == mock_validador
        mock_criar_menu.assert_called_once()
        mock_menu.executar_menu_interativo.assert_called_once()


@pytest.mark.integration
class TestMenuIntegration:
    """Testes de integração para o sistema de menu."""

    @pytest.mark.unit
    @patch("builtins.input", return_value="1")
    @patch("builtins.print")
    @patch("src.menu.criar_validador_locaweb")
    def test_fluxo_completo_selecao_locaweb(
        self, mock_criar_validador, mock_print, mock_input
    ):
        """Testa fluxo completo de seleção do Locaweb."""
        mock_validador = Mock()
        mock_criar_validador.return_value = mock_validador

        menu = MenuValidador()
        resultado = menu.executar_menu_interativo()

        assert resultado == mock_validador
        mock_criar_validador.assert_called_once()
