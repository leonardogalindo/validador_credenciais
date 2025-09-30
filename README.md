# 🔐 Validador de Credenciais Locaweb

[![Python Version](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-passing-green.svg)](tests/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Sistema de validação de credenciais em lote via API da Locaweb, desenvolvido em Python seguindo diretrizes de código limpo e modular.

---

## 📖 Índice

- [Sobre](#-sobre-o-projeto)
- [Funcionalidades](#-funcionalidades)
- [Instalação](#-instalação)
- [Como Usar](#-como-usar)
- [Documentação Completa](#-documentação-completa)
- [Licença](#-licença)

---

## 🎯 Sobre o Projeto

Este projeto automatiza a verificação de credenciais de usuário (login e senha) em lote, utilizando a API da Locaweb. Ele foi projetado para processar grandes volumes de dados a partir de arquivos CSV e gerar relatórios detalhados em formato JSON.

## ✨ Funcionalidades

-   ✅ **Validação em Lote**: Processa múltiplos arquivos CSV de uma só vez.
-   📊 **Relatórios Detalhados**: Gera arquivos JSON com o status de cada credencial.
-   🔒 **Segurança**: Utiliza headers de segurança e timeouts configuráveis.
-   📝 **Logging Estruturado**: Registra logs de auditoria, erros e debug.
-   ⚙️ **Interface de Comando**: Menu interativo para fácil utilização.

## 🚀 Instalação

Recomenda-se o uso de um ambiente virtual.

1.  **Clone o repositório:**
    ```bash
    git clone https://github.com/seu-usuario/validador_credenciais.git
    cd validador_credenciais
    ```

2.  **Crie e ative o ambiente virtual:**
    ```bash
    python -m venv .venv
    source .venv/bin/activate
    ```

3.  **Instale as dependências:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure as variáveis de ambiente:**
    Crie um arquivo `.env` a partir do `.env.example` e preencha as variáveis necessárias.

## 🛠️ Como Usar

Para iniciar a validação, execute o `main.py`:

```bash
python main.py
```

1.  **Prepare os arquivos**: Coloque os arquivos `.csv` a serem validados no diretório `data/csv/`.
2.  **Execute o programa**: O menu principal será exibido.
3.  **Acompanhe o resultado**: Os relatórios em `.json` serão salvos em `data/json/`.

## 📚 Documentação Completa

A documentação detalhada do projeto está localizada no diretório `doc/`:

-   **[Estrutura do Projeto (`doc/STRUCTURE.md`)](./doc/STRUCTURE.md)**: Uma visão geral da arquitetura e organização dos arquivos.
-   **[Guia de Dados (`doc/README_data.md`)](./doc/README_data.md)**: Convenções e uso do diretório `data/`.
-   **[Guia de Contribuição (`doc/CONTRIBUTING.md`)](./doc/CONTRIBUTING.md)**: Instruções para quem deseja contribuir com o projeto.

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.