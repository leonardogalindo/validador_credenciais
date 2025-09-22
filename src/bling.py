"""Módulo para validação de credenciais via API do Bling.

Este módulo fornece funcionalidades para validar credenciais em lote
a partir de arquivos CSV, utilizando a API de login do Bling.
Segue as diretrizes estabelecidas no GEMINI.md.
"""

import logging
import requests
from typing import Dict, Any, Optional, List
from datetime import datetime

try:
    from .csv_handler import criar_csv_handler
except ImportError:
    from csv_handler import criar_csv_handler


# Configuração do logger para este módulo
logger = logging.getLogger(__name__)


class BlingCredentialValidator:
    """Validador de credenciais via API do Bling.
    
    Esta classe encapsula as operações necessárias para validar credenciais
    em lote a partir de arquivos CSV, utilizando a API de login do Bling.
    """
    
    def __init__(self, 
                 login_url: str = "https://www.bling.com.br/login", 
                 timeout: int = 30) -> None:
        """Inicializa o validador de credenciais Bling.
        
        Args:
            login_url (str): URL da API de login do Bling.
            timeout (int): Timeout para requisições HTTP em segundos.
        """
        self.login_url = login_url
        self.timeout = timeout
        self.csv_handler = criar_csv_handler()
        
        logger.debug(f"BlingCredentialValidator inicializado com login_url: {self.login_url}")
    
    def validar_credencial_unica(self, 
                                 username: str, 
                                 password: str) -> bool:
        """Valida uma única credencial via API do Bling.
        
        Args:
            username (str): Nome de usuário para validação.
            password (str): Senha para validação.
            
        Returns:
            bool: True se a credencial for válida, False caso contrário.
        """
        try:
            # Headers para identificar testes de segurança
            headers = {
                'User-Agent': 'Bling-Security-Test/1.0 (Credential-Validation)',
                'X-Security-Test': 'security-tests-bling',
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            # Dados para o POST
            data = {
                'username': username,
                'password': password
            }
            
            logger.debug(f"🔍 Validando credencial para usuário: {username}")
            
            # Realiza a requisição POST
            response = requests.post(
                self.login_url,
                data=data,
                headers=headers,
                timeout=self.timeout,
                allow_redirects=False
            )
            
            # Verifica se o código de resposta é 201 (sucesso)
            is_valid = response.status_code == 201
            
            if is_valid:
                logger.info(f"✅ SUCESSO - Credenciais válidas para usuário: {username}")
            else:
                logger.warning(f"❌ ERRO - Credenciais inválidas para usuário: {username} (HTTP {response.status_code})")
            
            return is_valid
            
        except requests.exceptions.Timeout:
            logger.warning(f"⏰ Timeout na validação para usuário: {username}")
            return False
        except requests.exceptions.ConnectionError:
            logger.error(f"🔌 Erro de conexão na validação para usuário: {username}")
            return False
        except Exception as e:
            logger.error(f"💥 Erro inesperado na validação para usuário {username}: {str(e)}")
            return False
    
    def validar_credenciais_lote(self, 
                                 credenciais: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Valida múltiplas credenciais em lote.
        
        Args:
            credenciais (List[Dict[str, Any]]): Lista de credenciais para validar.
                Cada item deve conter 'username' e 'password'.
                
        Returns:
            List[Dict[str, Any]]: Lista de resultados da validação.
        """
        if not credenciais:
            logger.warning("⚠️  Lista de credenciais vazia")
            return []
        
        logger.info(f"🚀 Iniciando validação em lote de {len(credenciais)} credenciais Bling")
        
        resultados = []
        total = len(credenciais)
        
        for i, credencial in enumerate(credenciais, 1):
            username = credencial.get('username', '')
            password = credencial.get('password', '')
            linha_original = credencial.get('linha_original', i - 1)
            
            logger.debug(f"📊 Progresso: {i}/{total} ({(i/total)*100:.1f}%)")
            
            try:
                is_valid = self.validar_credencial_unica(username, password)
                
                resultado = {
                    'username': username,
                    'password': password,
                    'is_valid': is_valid,
                    'timestamp': datetime.now().isoformat(),
                    'linha_original': linha_original,
                    'error': '' if is_valid else 'Credencial inválida'
                }
                
                resultados.append(resultado)
                
                if is_valid:
                    logger.info(f"✅ [{i}/{total}] SUCESSO: {username}")
                else:
                    logger.warning(f"❌ [{i}/{total}] ERRO: {username}")
                    
            except Exception as e:
                logger.error(f"💥 Erro ao processar credencial {i}: {str(e)}")
                resultado = {
                    'username': username,
                    'password': password,
                    'is_valid': False,
                    'timestamp': datetime.now().isoformat(),
                    'linha_original': linha_original,
                    'error': f'Erro no processamento: {str(e)}'
                }
                resultados.append(resultado)
        
        # Estatísticas finais
        validas = sum(1 for r in resultados if r['is_valid'])
        invalidas = len(resultados) - validas
        taxa_sucesso = (validas / len(resultados) * 100) if resultados else 0
        
        logger.info(f"📈 Validação concluída - Total: {len(resultados)}, "
                   f"Válidas: {validas}, Inválidas: {invalidas}, "
                   f"Taxa de sucesso: {taxa_sucesso:.1f}%")
        
        return resultados
    
    def processar_arquivo_csv(self, caminho_arquivo: str) -> List[Dict[str, Any]]:
        """Processa um arquivo CSV e valida as credenciais.
        
        Args:
            caminho_arquivo (str): Caminho para o arquivo CSV.
            
        Returns:
            List[Dict[str, Any]]: Lista de resultados da validação.
        """
        logger.info(f"📂 Processando arquivo CSV: {caminho_arquivo}")
        
        try:
            # Lê as credenciais do arquivo CSV
            credenciais = self.csv_handler.ler_credenciais(caminho_arquivo)
            
            if not credenciais:
                logger.warning(f"⚠️  Nenhuma credencial válida encontrada no arquivo: {caminho_arquivo}")
                return []
            
            logger.info(f"📋 Encontradas {len(credenciais)} credenciais para validação")
            
            # Valida as credenciais
            resultados = self.validar_credenciais_lote(credenciais)
            
            return resultados
            
        except Exception as e:
            logger.error(f"💥 Erro ao processar arquivo CSV {caminho_arquivo}: {str(e)}")
            raise


def criar_validador_bling(login_url: str = "https://www.bling.com.br/login", 
                          timeout: int = 30) -> BlingCredentialValidator:
    """Factory function para criar uma instância do validador Bling.
    
    Args:
        login_url (str): URL da API de login do Bling.
        timeout (int): Timeout para requisições HTTP em segundos.
        
    Returns:
        BlingCredentialValidator: Instância configurada do validador.
    """
    return BlingCredentialValidator(login_url=login_url, timeout=timeout)
