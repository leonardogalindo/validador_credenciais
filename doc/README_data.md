# Documentação do Diretório `data/`

Este documento detalha a estrutura e as convenções utilizadas no diretório `data/`, garantindo a consistência e a rastreabilidade dos dados manipulados pelo projeto.

---

## Estrutura de Subdiretórios

O diretório `data/` é organizado da seguinte forma:

-   `data/csv/`: Armazena os arquivos de dados brutos em formato CSV. Estes arquivos são a fonte primária de informações para as rotinas de processamento e não devem ser modificados manualmente.
-   `data/json/`: Contém dados processados, limpos ou transformados, salvos em formato JSON. Estes arquivos são o resultado das operações de tratamento realizadas pela aplicação.

## Política de Versionamento

-   **Dados Brutos (`csv/`)**: Arquivos nesta pasta são considerados imutáveis. Uma vez adicionados, não devem ser alterados.
-   **Dados Processados (`json/`)**: Arquivos nesta pasta podem ser atualizados ou recriados a cada execução do sistema. Eles não são versionados no Git e devem ser gerados pela aplicação.

## Manutenção de Diretórios Vazios com `.gitkeep`

O arquivo `.gitkeep` presente nos subdiretórios (`csv/` e `json/`) é um marcador utilizado para garantir que o Git versione essas pastas mesmo quando estiverem vazias. Isso é importante para manter a estrutura de diretórios do projeto consistente em todos os ambientes.
