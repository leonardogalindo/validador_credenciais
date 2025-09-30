# Estrutura do Projeto

Este documento descreve a organização dos diretórios e arquivos do projeto, fornecendo uma visão geral de sua arquitetura.

---

## Visão Geral

O projeto segue uma estrutura modular para separar responsabilidades e facilitar a manutenção.

-   `/.github/workflows/`: Contém os pipelines de Integração Contínua e Deploy Contínuo (CI/CD).
-   `/build/`: Armazena arquivos temporários gerados durante o processo de build do pacote.
-   `/data/`: Contém os dados brutos e processados. (Veja `README_data.md` para mais detalhes).
-   `/dist/`: Guarda os pacotes distribuíveis da aplicação.
-   `/doc/`: Armazena a documentação do projeto.
-   `/logs/`: Contém os arquivos de log gerados pela aplicação.
-   `/src/`: Inclui o código-fonte principal da aplicação.
-   `/tests/`: Contém os testes unitários e de integração.
-   `/validador_credenciais.egg-info/`: Metadados do pacote gerados pelo `setuptools`.
-   `main.py`: Ponto de entrada da aplicação.
-   `requirements.txt`: Lista de dependências do projeto.
-   `setup.py`: Script de configuração para distribuição do pacote.

## O Propósito do `.gitkeep`

O Git, por padrão, não rastreia diretórios vazios. O arquivo `.gitkeep` é um marcador, sem conteúdo, colocado em um diretório que precisa ser mantido no repositório mesmo quando vazio.

Isso garante que a estrutura de pastas do projeto seja consistente em todos os ambientes de desenvolvimento, evitando erros de "diretório não encontrado" em scripts ou na execução da aplicação.
