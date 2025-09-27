# 🔐 Validador de Credenciais Locaweb

Sistema de validação de credenciais em lote via API da Locaweb, desenvolvido em Python seguindo as diretrizes do GEMINI.md.

## 📋 Funcionalidades

- ✅ Validação de credenciais via API da Locaweb
- 📊 Processamento em lote de arquivos CSV
- 📄 Geração de relatórios em formato JSON
- 🔒 Headers de segurança configurados
- 📝 Sistema de logging completo (debug, error, audit, settings)
- 🎯 Interface de linha de comando intuitiva

## 🚀 Instalação

### Instalação via pip (Recomendado)

```bash
# Instalar o pacote
pip install validador-credenciais

# Ou instalar em modo de desenvolvimento
git clone <repository-url>
cd validador_credenciais
pip install -e .
```

### Instalação Manual

```bash
# Clonar o repositório
git clone <repository-url>
cd validador_credenciais

# Criar ambiente virtual
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# ou
.venv\Scripts\activate     # Windows

# Instalar dependências
pip install -r requirements.txt
```

## 🎯 Uso

### Comando de Console (Após instalação via pip)

```bash
# Executar o validador
validar-credenciais
```

### Execução Manual

```bash
# Executar diretamente
python main.py
```

### Fluxo de Uso

1. **Preparar arquivo CSV**: Coloque seus arquivos CSV no diretório `data/csv/`
2. **Executar o comando**: `validar-credenciais`
3. **Selecionar Locaweb**: Escolha a opção 1 no menu
4. **Aguardar processamento**: O sistema processará todos os arquivos CSV encontrados
5. **Verificar resultados**: Os relatórios JSON serão salvos em `data/json/`

## 📁 Estrutura de Arquivos

```
validador_credenciais/
├── src/                    # Código fonte principal
│   ├── __init__.py
│   ├── locaweb.py         # Validador Locaweb
│   ├── csv_handler.py     # Manipulação de CSV
│   ├── menu.py            # Interface do menu
│   └── settings.py        # Configurações
├── tests/                 # Testes unitários
├── data/                  # Diretórios de dados
│   ├── csv/              # Arquivos CSV de entrada
│   └── json/             # Relatórios JSON de saída
├── logs/                  # Arquivos de log
├── main.py               # Ponto de entrada
├── setup.py              # Configuração do pacote
├── requirements.txt      # Dependências
├── GEMINI.md            # Diretrizes do projeto
└── README.md            # Este arquivo
```

## 📊 Formato dos Arquivos CSV

### Formato Simples
```csv
username,password
usuario1@exemplo.com,senha123
usuario2@exemplo.com,senha456
```

### Formato Locaweb Completo
```csv
name,username,email,mail_domain,cpf,rg,rg_or_ie,password,password_hash,url,internal,gender,address,phone,occupation,mother_name,company_name,cnpj,stealer_family,infection_date,hardware_id,hostname,malware_installation_path,ip,user_agent,brand,source,threat_id,breach_date
,usuario@locaweb.com.br,usuario@locaweb.com.br,,,,,senha123,,,,,,,,,,,,,,,,,,LOCAWEB,DataBreach,DRP-001,2025-01-15
```

## ⚙️ Configuração

### Variáveis de Ambiente

Crie um arquivo `.env` baseado no `.env.example`:

```bash
# URL da API de login da Locaweb
LOCAWEB_LOGIN_URL=https://login.locaweb.com.br/v1/tickets

# Timeout para requisições HTTP (segundos)
REQUEST_TIMEOUT=30

# Encoding dos arquivos CSV
CSV_ENCODING=utf-8
```

### Configurações de Logging

O sistema gera logs em diferentes níveis:
- `logs/debug.log` - Debug detalhado (DEV)
- `logs/error.log` - Erros e falhas (DEV/PROD)
- `logs/audit.log` - Auditoria crítica (PROD)
- `logs/settings.log` - Compatibilidade histórica (DEV)

## 🧪 Testes

```bash
# Executar todos os testes
pytest

# Executar com cobertura
pytest --cov=src

# Executar testes específicos
pytest tests/test_menu.py -v
```

## 🔧 Desenvolvimento

### Formatação de Código

```bash
# Formatação automática
black src/ tests/ main.py

# Organização de imports
isort src/ tests/ main.py

# Análise estática
flake8 src/ tests/ main.py
```

### Estrutura de Desenvolvimento

O projeto segue as diretrizes do GEMINI.md:
- **PEP 8** para estilo de código
- **Tipagem estática** com `typing`
- **Docstrings** em todas as funções
- **Logging estruturado** para auditoria
- **Testes unitários** abrangentes

## 📈 Exemplo de Relatório JSON

```json
{
  "metadata": {
    "arquivo_origem": "credenciais.csv",
    "data_processamento": "2025-09-27T00:12:30.123456",
    "total_processados": 3,
    "total_validos": 2,
    "total_invalidos": 1,
    "taxa_sucesso": "66.7%"
  },
  "resultados": {
    "validados_com_sucesso": [
      {
        "username": "usuario1@exemplo.com",
        "password": "senha123",
        "is_valid": true,
        "linha_original": 2
      }
    ],
    "validados_com_erro": [
      {
        "username": "usuario2@exemplo.com",
        "password": "senha456",
        "is_valid": false,
        "error": "Credenciais inválidas",
        "linha_original": 3
      }
    ]
  }
}
```

## 🔒 Segurança

- Headers de segurança configurados automaticamente
- Senhas incluídas nos relatórios JSON (mantenha-os seguros!)
- Logs de auditoria para rastreabilidade
- Timeout configurável para requisições HTTP

## 📝 Licença

MIT License - veja o arquivo LICENSE para detalhes.

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'feat: Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📞 Suporte

Para suporte e dúvidas:
- Abra uma issue no GitHub
- Verifique os logs em `logs/` para diagnóstico
