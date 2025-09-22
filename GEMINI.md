# Gemini.md: guia de colaboração AI

Este documento fornece contexto essencial para modelos de IA que interagem com este projeto. Seguir estas diretrizes garante consistência e preserva a qualidade do código.

---

## 1. Visão geral do projeto e propósito

**Objetivo Primário:**
Este projeto é um sistema em **Python**, estruturado para organizar código-fonte, documentação, dados e testes de maneira modular. A finalidade exata deve ser confirmada pelo desenvolvedor humano, mas o formato sugere que se trata de uma aplicação de automação ou processamento de dados.

**Domínio de negócio:**
Inferido como **automação**. (Confiança: média; recomenda-se validação humana.)

---

## 2. Tecnologias e pilha principal

* **Linguagem:** Python (versão inferida >=3.12).
* **Frameworks & Runtimes:** Dependem do `requirements.txt`.
* **Bibliotecas/Dependências-chave:** Listadas em `requirements.txt`.
* **Gerenciador de pacotes:** `pip`.

---

## 3. Padrões arquitetônicos

**Arquitetura geral:** Aplicação monolítica modularizada em diretórios.

* `README.md`: localizado na raiz, contém visão geral e instruções básicas.
* `src`: código-fonte principal.
* `tests`: testes unitários e de integração.
* `data`: repositório de datasets, estruturado conforme convenções abaixo.
* `doc`: documentação complementar.
* `logs`: saídas de logging configuradas no projeto.

**Diretório `data/`: convenções de uso**

* `data/csv/` → dados brutos.
* `data/txt/` → dados limpos e transformados.

> Boa prática: incluir um `README.md` dentro de `data/` explicando cada subpasta e política de versionamento.

---

## 4. Guia de Convenções e Estilo de Codificação

**Formatação:**

* Seguir PEP 8.
* Indentação: 4 espaços.
* Ferramentas recomendadas:

  * `black` → formatação automática.
  * `isort` → organização automática de imports.
  * `flake8` ou `pylint` → análise estática.

**Convenções de nomeação:**

* Variáveis e funções: snake\_case (`minha_funcao`).
* Classes: PascalCase (`MinhaClasse`).
* Arquivos: snake\_case (`meu_modulo.py`).

**Design da API:** Não aplicável até verificação de frameworks (ex.: Flask, FastAPI).

**Tratamento de erros:**

* Uso de `try/except` para captura de exceções.
* Classes de erro personalizadas devem residir em `src/exceptions.py`.

**Docstrings e Tipagem:**

* Utilizar tipagem estática (PEP 484) com `typing`.
* Todas as funções e classes devem conter **docstrings** (Google ou NumPy style).
* Exemplo:

  ```python
  def calcular_media(valores: list[float]) -> float:
      """Calcula a média de uma lista de valores numéricos.

      Args:
          valores (list[float]): Lista de números de entrada.

      Returns:
          float: Média aritmética dos valores.
      """
      return sum(valores) / len(valores)
  ```

---

## 5. Arquivos-chave e pontos de entrada

* **Ponto de entrada principal:** `main.py` na raiz.
* **Configuração:**

  * `requirements.txt` → dependências.
  * `src/settings.py` → configuração obrigatória de **logging**.
* **CI/CD Pipeline:** `.github/workflows/*.yml` ou similares (a confirmar).

**Logging (obrigatório):**

* **Arquivos de log:**

  * `logs/debug.log` → debug detalhado (DEV, nível DEBUG).
  * `logs/error.log` → erros e falhas (DEV/PROD, nível ERROR).
  * `logs/audit.log` → auditoria crítica (PROD, nível INFO).
  * `logs/settings.log` → compatibilidade histórica (DEV, nível DEBUG).

* **Política de retenção:**

  * Local: **ilimitada** (sem rotação automática).
 
* **Boas práticas:**

  * Formato estruturado em produção recomendado (JSON ou chave=valor).
  * Não logar dados sensíveis (tokens, senhas, PII).
  * Incluir sempre: `timestamp`, `nível`, `logger`, `função`, `linha` e `mensagem`.
  * Auditoria deve incluir `user_id`, `session_id` ou equivalente.

---

## 6. Fluxo de trabalho de desenvolvimento e teste

**Ambiente de desenvolvimento local:**

1. Criar ambiente virtual: `python -m venv .venv`.
2. Ativar ambiente virtual.
3. Instalar dependências: `pip install -r requirements.txt`.

**Teste:**

* Localizado em `tests/`.
* Execução via `pytest`.

**CI/CD Processo:**

* Alterações acionam pipelines (lint + testes + build/deploy).

---

## 7. Instruções específicas para colaboração de IA

**Diretrizes de contribuição:**

* Confirmar `CONTRIBUTING.md`.
* PRs pequenos, documentados e revisados.

**Infraestrutura (IaC):** Nenhum diretório detectado; se adicionado, revisar com cautela.

**Segurança:**

* Nunca inserir segredos em código.
* Variáveis sensíveis via `.env`.

**Dependências:**

```bash
pip install <pacote>
pip freeze > requirements.txt
```

**Mensagens de commit:**

* `feat:`, `fix:`, `docs:`, `test:` (Conventional Commits).

---

# 🔎 Análise crítica e recomendações

1. Diretório `data/` estruturado → facilita rastreabilidade e versionamento.
2. Logging consolidado em arquivos distintos, com política ilimitada + backup anual → atende auditoria e compliance.
3. Tipagem + docstrings padronizadas → consistência para IA e humanos.
4. CI/CD e pipelines ainda precisam ser detalhados.
5. Sugestão: criar `doc/CONTRIBUTING.md` e `doc/README_data.md` para formalizar convenções.
