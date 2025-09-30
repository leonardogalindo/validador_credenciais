# Guia de Contribuição

Agradecemos o seu interesse em contribuir com o projeto! Para garantir a qualidade e a consistência do código, siga as diretrizes abaixo.

---

## Fluxo de Trabalho

1.  **Fork e Clone**: Faça um fork do repositório e clone-o para sua máquina local.
2.  **Crie uma Branch**: Crie uma branch específica para sua feature ou correção (`git checkout -b feature/nome-da-feature` ou `fix/descricao-do-fix`).
3.  **Desenvolva**: Implemente suas alterações, seguindo os padrões de código do projeto.
4.  **Teste**: Adicione testes unitários para suas novas funcionalidades e garanta que todos os testes existentes continuem passando.
5.  **Documente**: Atualize a documentação, se necessário.
6.  **Commit**: Faça commits claros e concisos, seguindo o padrão de [Commits Convencionais](https.conventionalcommits.org/en/v1.0.0/).
    -   **Exemplos**:
        -   `feat: Adiciona nova funcionalidade de exportação`
        -   `fix: Corrige cálculo de imposto na fatura`
        -   `docs: Atualiza o README com novas instruções`
7.  **Push e Pull Request**: Envie suas alterações para o seu fork e abra um Pull Request (PR) para a branch `main` do repositório original.

## Padrões de Código

-   **Estilo**: Siga o guia de estilo PEP 8.
-   **Formatação**: Utilize `black` para formatação automática e `isort` para ordenação de imports.
-   **Tipagem**: Adote tipagem estática (PEP 484) em todas as funções e métodos.
-   **Docstrings**: Documente todas as funções e classes com docstrings no estilo Google.

## Relatório de Bugs e Sugestões

-   Para relatar bugs, use a seção "Issues" do GitHub, fornecendo o máximo de detalhes possível.
-   Para sugerir novas funcionalidades, crie uma "Issue" descrevendo a proposta e sua motivação.
