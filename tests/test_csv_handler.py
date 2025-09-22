"""Testes unitários para o módulo csv_handler.

Este módulo testa todas as funcionalidades do CSVHandler,
incluindo leitura, escrita e validação de arquivos CSV.
"""

import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open

from src.csv_handler import CSVHandler, criar_csv_handler


class TestCSVHandler:
    """Testes para a classe CSVHandler."""
    
    def setup_method(self):
        """Configuração executada antes de cada teste."""
        self.csv_handler = criar_csv_handler()
        self.temp_dir = Path(tempfile.mkdtemp())
    
    def teardown_method(self):
        """Limpeza executada após cada teste."""
        # Remove arquivos temporários
        import shutil
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_criar_csv_handler(self):
        """Testa a criação do CSVHandler."""
        handler = criar_csv_handler()
        assert isinstance(handler, CSVHandler)
        assert handler.encoding == 'utf-8'
        
        # Testa com encoding personalizado
        handler_custom = criar_csv_handler('latin-1')
        assert handler_custom.encoding == 'latin-1'
    
    def test_ler_credenciais_arquivo_valido(self):
        """Testa leitura de credenciais de arquivo válido."""
        # Cria arquivo CSV temporário
        csv_content = """username,password
user1@test.com,senha123
user2@test.com,senha456
user3@test.com,senha789"""
        
        csv_file = self.temp_dir / "credenciais.csv"
        csv_file.write_text(csv_content, encoding='utf-8')
        
        # Testa leitura
        credenciais = self.csv_handler.ler_credenciais(str(csv_file))
        
        assert len(credenciais) == 3
        assert credenciais[0]['username'] == 'user1@test.com'
        assert credenciais[0]['password'] == 'senha123'
        assert credenciais[1]['username'] == 'user2@test.com'
        assert credenciais[1]['password'] == 'senha456'
        assert credenciais[2]['username'] == 'user3@test.com'
        assert credenciais[2]['password'] == 'senha789'
    
    def test_ler_credenciais_formato_locaweb(self):
        """Testa leitura de credenciais no formato Locaweb (com colunas extras)."""
        # Cria arquivo CSV no formato Locaweb - o sistema deve extrair apenas username e password
        csv_content = """name,username,email,mail_domain,cpf,rg,rg_or_ie,password,password_hash,url,internal,gender,address,phone,occupation,mother_name,company_name,cnpj,stealer_family,infection_date,hardware_id,hostname,malware_installation_path,ip,user_agent,brand,source,threat_id,breach_date
,jonas.jesus@locaweb.com.br,jonas.jesus@locaweb.com.br,,,,,9hCAYCRx@zrK8HS,,,,,,,,,,,,,,,,,,LOCAWEB,Telegram,DRP-3187,2025-09-15
,vitor.paixao@locaweb.com.br,vitor.paixao@locaweb.com.br,,,,,locavideo08,,,,,,,,,,,,,,,,,,LOCAWEB,Telegram,DRP-3187,2025-09-15"""
        
        csv_file = self.temp_dir / "locaweb.csv"
        csv_file.write_text(csv_content, encoding='utf-8')
        
        # Testa leitura
        credenciais = self.csv_handler.ler_credenciais(str(csv_file))
        
        assert len(credenciais) == 2
        assert credenciais[0]['username'] == 'jonas.jesus@locaweb.com.br'
        assert credenciais[0]['password'] == '9hCAYCRx@zrK8HS'
        assert credenciais[1]['username'] == 'vitor.paixao@locaweb.com.br'
        assert credenciais[1]['password'] == 'locavideo08'
    
    def test_ler_credenciais_arquivo_inexistente(self):
        """Testa leitura de arquivo inexistente."""
        with pytest.raises(FileNotFoundError):
            self.csv_handler.ler_credenciais("arquivo_inexistente.csv")
    
    def test_ler_credenciais_colunas_faltantes(self):
        """Testa leitura de arquivo sem colunas necessárias."""
        csv_content = """nome,email
João,joao@test.com
Maria,maria@test.com"""
        
        csv_file = self.temp_dir / "sem_colunas.csv"
        csv_file.write_text(csv_content, encoding='utf-8')
        
        with pytest.raises(ValueError, match="Coluna 'username' não encontrada"):
            self.csv_handler.ler_credenciais(str(csv_file))
    
    def test_ler_credenciais_arquivo_vazio(self):
        """Testa leitura de arquivo vazio."""
        csv_file = self.temp_dir / "vazio.csv"
        csv_file.write_text("", encoding='utf-8')
        
        with pytest.raises(ValueError, match="Arquivo CSV está vazio"):
            self.csv_handler.ler_credenciais(str(csv_file))
    
    def test_ler_credenciais_linhas_vazias(self):
        """Testa leitura de arquivo com linhas vazias."""
        csv_content = """username,password
user1@test.com,senha123
,
user2@test.com,
,senha456
user3@test.com,senha789"""
        
        csv_file = self.temp_dir / "com_vazias.csv"
        csv_file.write_text(csv_content, encoding='utf-8')
        
        credenciais = self.csv_handler.ler_credenciais(str(csv_file))
        
        # Deve ignorar linhas com campos vazios
        assert len(credenciais) == 2
        assert credenciais[0]['username'] == 'user1@test.com'
        assert credenciais[1]['username'] == 'user3@test.com'
    
    def test_ler_credenciais_username_muito_curto(self):
        """Testa leitura de arquivo com username muito curto."""
        csv_content = """username,password
user1@test.com,senha123
ab,senha456
x,senha789
user4@test.com,senha_valida"""
        
        csv_file = self.temp_dir / "username_curto.csv"
        csv_file.write_text(csv_content, encoding='utf-8')
        
        credenciais = self.csv_handler.ler_credenciais(str(csv_file))
        
        # Deve ignorar usernames com menos de 3 caracteres
        assert len(credenciais) == 2
        assert credenciais[0]['username'] == 'user1@test.com'
        assert credenciais[1]['username'] == 'user4@test.com'
    
    def test_ler_credenciais_password_placeholder(self):
        """Testa leitura de arquivo com passwords placeholder."""
        csv_content = """username,password
user1@test.com,senha123
user2@test.com,[NOT_SAVED]
user3@test.com,[REDACTED]
user4@test.com,senha_valida
user5@test.com,[HIDDEN]
user6@test.com,N/A"""
        
        csv_file = self.temp_dir / "password_placeholder.csv"
        csv_file.write_text(csv_content, encoding='utf-8')
        
        credenciais = self.csv_handler.ler_credenciais(str(csv_file))
        
        # Deve ignorar passwords que são placeholders
        assert len(credenciais) == 2
        assert credenciais[0]['username'] == 'user1@test.com'
        assert credenciais[0]['password'] == 'senha123'
        assert credenciais[1]['username'] == 'user4@test.com'
        assert credenciais[1]['password'] == 'senha_valida'
    
    def test_remover_arquivo_csv_sucesso(self):
        """Testa remoção bem-sucedida de arquivo CSV."""
        # Cria arquivo temporário
        arquivo_teste = self.temp_dir / "teste_remocao.csv"
        arquivo_teste.write_text("username,password\nuser@test.com,senha123", encoding='utf-8')
        
        # Verifica se existe
        assert arquivo_teste.exists()
        
        # Remove o arquivo
        resultado = self.csv_handler.remover_arquivo_csv(str(arquivo_teste))
        
        # Verifica resultado
        assert resultado is True
        assert not arquivo_teste.exists()
    
    def test_remover_arquivo_csv_inexistente(self):
        """Testa remoção de arquivo que não existe."""
        arquivo_inexistente = self.temp_dir / "inexistente.csv"
        
        # Tenta remover arquivo que não existe
        resultado = self.csv_handler.remover_arquivo_csv(str(arquivo_inexistente))
        
        # Deve retornar False
        assert resultado is False
    
    def test_salvar_resultados_csv(self):
        """Testa salvamento de resultados em CSV."""
        resultados = [
            {'username': 'user1@test.com', 'is_valid': True, 'error': ''},
            {'username': 'user2@test.com', 'is_valid': False, 'error': 'Credenciais inválidas'}
        ]
        
        csv_file = self.temp_dir / "resultados.csv"
        self.csv_handler.salvar_resultados(resultados, str(csv_file))
        
        # Verifica se arquivo foi criado
        assert csv_file.exists()
        
        # Verifica conteúdo
        content = csv_file.read_text(encoding='utf-8')
        assert 'username,is_valid,error' in content
        assert 'user1@test.com,True,' in content
        assert 'user2@test.com,False,Credenciais inválidas' in content
    
    def test_salvar_resultados_csv_com_senha(self):
        """Testa salvamento de resultados CSV incluindo senhas."""
        resultados = [
            {'username': 'user1@test.com', 'password': 'senha123', 'is_valid': True, 'error': ''},
            {'username': 'user2@test.com', 'password': 'senha456', 'is_valid': False, 'error': 'Erro'}
        ]
        
        csv_file = self.temp_dir / "resultados_com_senha.csv"
        self.csv_handler.salvar_resultados(resultados, str(csv_file), incluir_senha=True)
        
        content = csv_file.read_text(encoding='utf-8')
        assert 'username,password,is_valid,error' in content
        assert 'senha123' in content
        assert 'senha456' in content
    
    def test_salvar_resultados_json(self):
        """Testa salvamento de resultados em JSON."""
        resultados = [
            {'username': 'user1@test.com', 'password': 'senha123', 'is_valid': True, 'error': '', 'linha_original': 2},
            {'username': 'user2@test.com', 'password': 'senha456', 'is_valid': False, 'error': 'Erro', 'linha_original': 3}
        ]
        
        json_file = self.temp_dir / "resultados.json"
        self.csv_handler.salvar_resultados_json(resultados, str(json_file), "teste.csv")
        
        # Verifica se arquivo foi criado
        assert json_file.exists()
        
        # Verifica estrutura JSON
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert 'metadata' in data
        assert 'resultados' in data
        assert data['metadata']['arquivo_origem'] == 'teste.csv'
        assert data['metadata']['total_processados'] == 2
        assert data['metadata']['total_validos'] == 1
        assert data['metadata']['total_invalidos'] == 1
        
        assert len(data['resultados']['validados_com_sucesso']) == 1
        assert len(data['resultados']['validados_com_erro']) == 1
        
        sucesso = data['resultados']['validados_com_sucesso'][0]
        assert sucesso['username'] == 'user1@test.com'
        assert sucesso['password'] == 'senha123'
        
        erro = data['resultados']['validados_com_erro'][0]
        assert erro['username'] == 'user2@test.com'
        assert erro['password'] == 'senha456'
        assert erro['erro'] == 'Erro'
    
    def test_salvar_resultados_lista_vazia(self):
        """Testa salvamento com lista vazia."""
        with pytest.raises(ValueError, match="Lista de resultados não pode estar vazia"):
            self.csv_handler.salvar_resultados([], "arquivo.csv")
        
        with pytest.raises(ValueError, match="Lista de resultados não pode estar vazia"):
            self.csv_handler.salvar_resultados_json([], "arquivo.json", "origem.csv")
    
    def test_validar_estrutura_csv_valida(self):
        """Testa validação de estrutura CSV válida."""
        csv_content = """username,password,email
user1@test.com,senha123,user1@test.com
user2@test.com,senha456,user2@test.com"""
        
        csv_file = self.temp_dir / "estrutura_valida.csv"
        csv_file.write_text(csv_content, encoding='utf-8')
        
        resultado = self.csv_handler.validar_estrutura_csv(str(csv_file))
        
        assert resultado['valido'] is True
        assert 'username' in resultado['colunas_encontradas']
        assert 'password' in resultado['colunas_encontradas']
        assert len(resultado['colunas_faltantes']) == 0
        assert resultado['total_linhas'] == 2
        assert resultado['erro'] is None
    
    def test_validar_estrutura_csv_invalida(self):
        """Testa validação de estrutura CSV inválida."""
        csv_content = """nome,email
João,joao@test.com"""
        
        csv_file = self.temp_dir / "estrutura_invalida.csv"
        csv_file.write_text(csv_content, encoding='utf-8')
        
        resultado = self.csv_handler.validar_estrutura_csv(str(csv_file))
        
        assert resultado['valido'] is False
        assert 'username' in resultado['colunas_faltantes']
        assert 'password' in resultado['colunas_faltantes']
        assert resultado['erro'] is not None
    
    def test_criar_template_csv(self):
        """Testa criação de template CSV."""
        template_file = self.temp_dir / "template.csv"
        
        colunas = ['username', 'password', 'email']
        dados_exemplo = [
            {'username': 'user1@test.com', 'password': 'senha123', 'email': 'user1@test.com'},
            {'username': 'user2@test.com', 'password': 'senha456', 'email': 'user2@test.com'}
        ]
        
        self.csv_handler.criar_template_csv(str(template_file), colunas, dados_exemplo)
        
        # Verifica se arquivo foi criado
        assert template_file.exists()
        
        # Verifica conteúdo
        content = template_file.read_text(encoding='utf-8')
        assert 'username,password,email' in content
        assert 'user1@test.com,senha123,user1@test.com' in content
        assert 'user2@test.com,senha456,user2@test.com' in content
    
    def test_criar_template_csv_sem_dados(self):
        """Testa criação de template CSV sem dados de exemplo."""
        template_file = self.temp_dir / "template_vazio.csv"
        
        self.csv_handler.criar_template_csv(str(template_file))
        
        # Verifica se arquivo foi criado apenas com cabeçalho
        assert template_file.exists()
        content = template_file.read_text(encoding='utf-8')
        lines = content.strip().split('\n')
        assert len(lines) == 1  # Apenas cabeçalho
        assert lines[0] == 'username,password'


class TestCSVHandlerIntegration:
    """Testes de integração para CSVHandler."""
    
    def setup_method(self):
        """Configuração para testes de integração."""
        self.csv_handler = criar_csv_handler()
        self.temp_dir = Path(tempfile.mkdtemp())
    
    def teardown_method(self):
        """Limpeza após testes de integração."""
        import shutil
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_fluxo_completo_csv_para_json(self):
        """Testa fluxo completo: CSV -> processamento -> JSON."""
        # 1. Cria arquivo CSV de entrada
        csv_content = """username,password
user1@test.com,senha123
user2@test.com,senha456
user3@test.com,senha789"""
        
        csv_file = self.temp_dir / "entrada.csv"
        csv_file.write_text(csv_content, encoding='utf-8')
        
        # 2. Lê credenciais
        credenciais = self.csv_handler.ler_credenciais(str(csv_file))
        assert len(credenciais) == 3
        
        # 3. Simula processamento (resultados fictícios)
        resultados = []
        for i, cred in enumerate(credenciais):
            resultado = {
                'username': cred['username'],
                'password': cred['password'],
                'is_valid': i % 2 == 0,  # Alterna entre válido/inválido
                'error': '' if i % 2 == 0 else 'Erro simulado',
                'linha_original': i + 2
            }
            resultados.append(resultado)
        
        # 4. Salva em JSON
        json_file = self.temp_dir / "saida.json"
        self.csv_handler.salvar_resultados_json(resultados, str(json_file), "entrada.csv")
        
        # 5. Verifica resultado final
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert data['metadata']['total_processados'] == 3
        assert data['metadata']['total_validos'] == 2  # user1 e user3
        assert data['metadata']['total_invalidos'] == 1  # user2
        assert len(data['resultados']['validados_com_sucesso']) == 2
        assert len(data['resultados']['validados_com_erro']) == 1
