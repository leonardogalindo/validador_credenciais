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
        """Valida uma única credencial via API do Bling com método otimizado.
        
        Este método implementa validação robusta com múltiplas verificações
        para garantir precisão na autenticação básica (sem 2FA).
        
        Args:
            username (str): Nome de usuário para validação.
            password (str): Senha para validação.
            
        Returns:
            bool: True se a credencial for válida, False caso contrário.
        """
        # Validação prévia dos dados de entrada
        if not self._validar_dados_entrada(username, password):
            return False
        
        try:
            logger.debug(f"🔍 Iniciando validação otimizada para usuário: {username}")
            
            # Realiza validação com método otimizado
            resultado_validacao = self._executar_validacao_otimizada(username, password)
            
            # Log do resultado
            if resultado_validacao['is_valid']:
                logger.info(f"✅ SUCESSO - Credenciais válidas para usuário: {username}")
                logger.debug(f"   📊 Detalhes: Status {resultado_validacao['status_code']}, "
                           f"Tempo: {resultado_validacao.get('response_time', 'N/A')}ms")
            else:
                logger.warning(f"❌ ERRO - Credenciais inválidas para usuário: {username} "
                             f"(HTTP {resultado_validacao['status_code']})")
                if resultado_validacao.get('error_details'):
                    logger.debug(f"   🔍 Detalhes do erro: {resultado_validacao['error_details']}")
            
            return resultado_validacao['is_valid']
            
        except requests.exceptions.Timeout:
            logger.warning(f"⏰ Timeout na validação para usuário: {username}")
            return False
        except requests.exceptions.ConnectionError:
            logger.error(f"🔌 Erro de conexão na validação para usuário: {username}")
            return False
        except Exception as e:
            logger.error(f"💥 Erro inesperado na validação para usuário {username}: {str(e)}")
            return False
    
    def _validar_dados_entrada(self, username: str, password: str) -> bool:
        """Valida os dados de entrada antes da requisição.
        
        Args:
            username (str): Nome de usuário.
            password (str): Senha.
            
        Returns:
            bool: True se os dados são válidos, False caso contrário.
        """
        # Verifica se username não está vazio
        if not username or not username.strip():
            logger.warning("❌ Username vazio ou inválido")
            return False
        
        # Verifica se password não está vazio
        if not password or not password.strip():
            logger.warning(f"❌ Password vazio para usuário: {username}")
            return False
        
        # Verifica comprimento mínimo do username (3 caracteres)
        if len(username.strip()) < 3:
            logger.warning(f"❌ Username muito curto para: {username}")
            return False
        
        # Verifica se não são placeholders conhecidos
        placeholders = ['[NOT_SAVED]', '[REDACTED]', '[HIDDEN]', 'N/A', 'NULL', 'undefined', 'null']
        if password.upper() in [p.upper() for p in placeholders]:
            logger.warning(f"❌ Password é placeholder para usuário: {username}")
            return False
        
        return True
    
    def _executar_validacao_otimizada(self, username: str, password: str) -> dict:
        """Executa validação otimizada com múltiplas verificações.
        
        Args:
            username (str): Nome de usuário.
            password (str): Senha.
            
        Returns:
            dict: Resultado da validação com detalhes.
        """
        import time
        start_time = time.time()
        
        # Headers otimizados para Bling
        headers = {
            'User-Agent': 'Bling-Security-Test/1.0 (Credential-Validation)',
            'X-Security-Test': 'security-tests-bling',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json, text/html, */*',
            'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        }
        
        # Dados de login otimizados
        data = {
            'username': username.strip(),
            'password': password,
            'remember': 'false',  # Não manter sessão
            'source': 'security-test'  # Identificar origem
        }
        
        # Configuração de sessão para melhor performance
        session = requests.Session()
        session.headers.update(headers)
        
        try:
            # Realiza requisição com configurações otimizadas
            response = session.post(
                self.login_url,
                data=data,
                timeout=self.timeout,
                allow_redirects=False,  # Não seguir redirects automaticamente
                verify=True  # Verificar SSL
            )
            
            # Calcula tempo de resposta
            response_time = round((time.time() - start_time) * 1000, 2)
            
            # Análise detalhada da resposta
            resultado = self._analisar_resposta_bling(response, response_time)
            
            return resultado
            
        finally:
            # Limpa a sessão
            session.close()
    
    def _analisar_resposta_bling(self, response: requests.Response, response_time: float) -> dict:
        """Analisa a resposta do Bling para determinar sucesso/falha.
        
        Args:
            response: Objeto de resposta do requests.
            response_time: Tempo de resposta em milissegundos.
            
        Returns:
            dict: Análise detalhada da resposta.
        """
        resultado = {
            'is_valid': False,
            'status_code': response.status_code,
            'response_time': response_time,
            'error_details': None
        }
        
        # Código 201 = Login bem-sucedido (conforme especificação)
        if response.status_code == 201:
            resultado['is_valid'] = True
            
            # Verificações adicionais de segurança
            if self._verificar_resposta_adicional(response):
                logger.debug("🔒 Verificações adicionais de segurança aprovadas")
            else:
                logger.debug("⚠️  Verificações adicionais apresentaram inconsistências")
        
        # Análise de códigos de erro específicos
        elif response.status_code == 401:
            resultado['error_details'] = "Credenciais inválidas"
        elif response.status_code == 403:
            resultado['error_details'] = "Acesso negado"
        elif response.status_code == 429:
            resultado['error_details'] = "Muitas tentativas - rate limit"
        elif response.status_code == 500:
            resultado['error_details'] = "Erro interno do servidor"
        elif response.status_code in [302, 303, 307, 308]:
            # Redirects podem indicar sucesso em alguns casos
            location = response.headers.get('Location', '')
            if 'dashboard' in location.lower() or 'home' in location.lower():
                resultado['is_valid'] = True
                resultado['error_details'] = f"Redirect para: {location}"
        else:
            resultado['error_details'] = f"Código não esperado: {response.status_code}"
        
        return resultado
    
    def _verificar_resposta_adicional(self, response: requests.Response) -> bool:
        """Verificações adicionais na resposta para maior precisão.
        
        Args:
            response: Objeto de resposta do requests.
            
        Returns:
            bool: True se as verificações passaram.
        """
        try:
            # Verifica headers de resposta
            content_type = response.headers.get('Content-Type', '').lower()
            
            # Verifica se não há indicadores de erro no conteúdo
            if hasattr(response, 'text') and response.text:
                content_lower = response.text.lower()
                
                # Indicadores de erro comuns
                error_indicators = [
                    'invalid credentials', 'login failed', 'authentication failed',
                    'credenciais inválidas', 'falha no login', 'erro de autenticação',
                    'access denied', 'unauthorized', 'forbidden'
                ]
                
                for indicator in error_indicators:
                    if indicator in content_lower:
                        logger.debug(f"🚨 Indicador de erro encontrado: {indicator}")
                        return False
                
                # Indicadores de sucesso
                success_indicators = [
                    'dashboard', 'welcome', 'bem-vindo', 'sucesso',
                    'authenticated', 'logged in', 'login successful'
                ]
                
                for indicator in success_indicators:
                    if indicator in content_lower:
                        logger.debug(f"✅ Indicador de sucesso encontrado: {indicator}")
                        return True
            
            return True  # Sem indicadores negativos
            
        except Exception as e:
            logger.debug(f"⚠️  Erro na verificação adicional: {str(e)}")
            return True  # Em caso de erro, assume que está ok
    
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
