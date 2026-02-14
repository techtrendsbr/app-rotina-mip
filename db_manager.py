import gspread
import pandas as pd
import json
import os
from typing import Optional, Dict, Any


class SheetManager:
    """Gerencia conexões e operações com o Google Sheets.

    Suporta múltiplos métodos de autenticação com fallback automático:
    1. Streamlit Secrets (chave específica)
    2. Streamlit Secrets (raiz)
    3. Arquivo local (service_account.json)
    """

    def __init__(self, sheet_name: str = 'Journal Database'):
        """
        Inicializa o gerenciador de planilhas.

        Args:
            sheet_name: Nome da planilha no Google Drive
        """
        self.sheet_name = sheet_name
        self.gc = None
        self.sheet = None
        self.credentials_source = None
        self._connect()

    def _normalize_private_key(self, key: str) -> str:
        """
        Normaliza a private_key substituindo escape sequences.

        Args:
            key: A chave privada (possivelmente com \\n)

        Returns:
            A chave normalizada com \n reais
        """
        if isinstance(key, str):
            # Substituir \\n por \n e \\t por \t
            return key.replace('\\n', '\n').replace('\\t', '\t')
        return key

    def _try_secrets_specific(self) -> Optional[gspread.Client]:
        """
        Tenta autenticar usando st.secrets['service_account_file_content'].

        Returns:
            gspread.Client ou None se falhar
        """
        try:
            import streamlit as st
            print(f"🔍 DEBUG: Tentando st.secrets['service_account_file_content']...")

            # Tentar ler o JSON completo como string (MÉTODO NOVO: JSON Payload)
            secret_value = st.secrets.get('service_account_file_content')

            if secret_value is None:
                print(f"⚠️  DEBUG: Chave 'service_account_file_content' não encontrada em st.secrets")
                return None

            print(f"✅ DEBUG: Secret encontrado! Tipo: {type(secret_value)}, Tamanho: {len(secret_value)} caracteres")

            # Se for uma string (JSON como texto), fazer parse
            if isinstance(secret_value, str):
                try:
                    credentials_dict = json.loads(secret_value)
                    print(f"✅ DEBUG: Parseado JSON string com sucesso ({len(credentials_dict)} campos)")
                except json.JSONDecodeError as e:
                    print(f"❌ DEBUG: Falha ao fazer parse JSON: {e}")
                    return None
            elif isinstance(secret_value, dict):
                # Se for um dict (AttrDict), converter
                credentials_dict = dict(secret_value)
                print(f"✅ DEBUG: Convertido de dict para dict Python ({len(credentials_dict)} campos)")
            else:
                print(f"❌ DEBUG: Tipo de secret não suportado: {type(secret_value)}")
                return None

            # Verificar campos essenciais
            required_fields = ['type', 'project_id', 'private_key_id', 'private_key', 'client_email', 'client_id']
            missing_fields = [f for f in required_fields if f not in credentials_dict]

            if missing_fields:
                print(f"❌ DEBUG: Campos faltando no JSON: {missing_fields}")
                return None

            print(f"✅ DEBUG: Todos os campos essenciais presentes")

            # Conectar usando o dict
            gc = gspread.service_account_from_dict(credentials_dict)
            self.credentials_source = "Streamlit Secrets (JSON Payload)"
            print(f"✅ DEBUG: gspread.service_account_from_dict() bem-sucedido")
            return gc

        except ImportError:
            print(f"⚠️  DEBUG: Streamlit não disponível (ImportError)")
            return None
        except AttributeError as e:
            print(f"⚠️  DEBUG: st.secrets não disponível: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"❌ DEBUG: Erro ao fazer parse JSON: {e}")
            return None
        except Exception as e:
            print(f"❌ DEBUG: Erro em st.secrets['service_account_file_content']: {type(e).__name__}: {e}")
            return None

    def _try_secrets_root(self) -> Optional[gspread.Client]:
        """
        Tenta autenticar usando st.secrets (raiz) para chaves soltas.

        Às vezes o usuário cola as chaves direto sem wrapper.
        Ex: project_id, private_key, etc. na raiz de st.secrets

        Returns:
            gspread.Client ou None se falhar
        """
        try:
            import streamlit as st
            print(f"🔍 DEBUG: Tentando st.secrets (raiz) para chaves soltas...")

            # Verificar se chaves essenciais existem na raiz
            essential_keys = ['project_id', 'private_key_id', 'private_key',
                           'client_email', 'client_id']

            # Tentar montar dict da raiz
            credentials_dict = {}
            missing_keys = []

            for key in essential_keys:
                value = st.secrets.get(key)
                if value is not None:
                    credentials_dict[key] = value
                    print(f"✅ DEBUG: Chave '{key}' encontrada na raiz")
                else:
                    missing_keys.append(key)

            if len(missing_keys) == len(essential_keys):
                # Nenhuma chave encontrada
                print(f"⚠️  DEBUG: Nenhuma chave essencial encontrada na raiz de st.secrets")
                return None

            if len(missing_keys) > 0:
                print(f"⚠️  DEBUG: Algumas chaves faltando na raiz: {missing_keys}")
                return None

            # Adicionar campos opcionais se existirem
            optional_keys = ['auth_uri', 'token_uri',
                           'auth_provider_x509_cert_url', 'client_x509_cert_url']

            for key in optional_keys:
                value = st.secrets.get(key)
                if value is not None:
                    credentials_dict[key] = value
                    print(f"✅ DEBUG: Chave opcional '{key}' encontrada")

            # Normalizar private_key
            if 'private_key' in credentials_dict:
                credentials_dict['private_key'] = self._normalize_private_key(credentials_dict['private_key'])
                print(f"✅ DEBUG: private_key normalizada")

            # Conectar
            gc = gspread.service_account_from_dict(credentials_dict)
            self.credentials_source = "Streamlit Secrets (raiz)"
            print(f"✅ DEBUG: gspread.service_account_from_dict() bem-sucedido")
            return gc

        except ImportError:
            print(f"⚠️  DEBUG: Streamlit não disponível (ImportError)")
            return None
        except AttributeError as e:
            print(f"⚠️  DEBUG: st.secrets não disponível: {e}")
            return None
        except Exception as e:
            print(f"❌ DEBUG: Erro em st.secrets (raiz): {type(e).__name__}: {e}")
            return None

    def _try_local_file(self) -> Optional[gspread.Client]:
        """
        Tenta autenticar usando arquivos locais.

        Returns:
            gspread.Client ou None se falhar
        """
        print(f"🔍 DEBUG: Tentando arquivos locais...")

        credentials_files = [
            'service_account.json',
            'service-account.json',
            'service_account',
            'service-account'
        ]

        for cred_file in credentials_files:
            if os.path.exists(cred_file):
                print(f"✅ DEBUG: Arquivo encontrado: {cred_file}")
                try:
                    gc = gspread.service_account(filename=cred_file)
                    self.credentials_source = f"Arquivo local ({cred_file})"
                    print(f"✅ DEBUG: gspread.service_account() bem-sucedido")
                    return gc
                except Exception as e:
                    print(f"❌ DEBUG: Erro ao ler {cred_file}: {type(e).__name__}: {e}")
                    continue
            else:
                print(f"⚠️  DEBUG: Arquivo não encontrado: {cred_file}")

        print(f"⚠️  DEBUG: Nenhum arquivo local encontrado")
        return None

    def _connect(self):
        """Estabelece conexão com o Google Sheets.

        Tenta múltiplos métodos em ordem:
        1. Streamlit Secrets (chave específica)
        2. Streamlit Secrets (raiz)
        3. Arquivo local
        """
        print(f"\n{'='*60}")
        print(f"🔧 Iniciando conexão com Google Sheets...")
        print(f"📋 Planilha alvo: '{self.sheet_name}'")
        print(f"{'='*60}\n")

        # Tentar 1: Streamlit Secrets (JSON Payload) - PRIORIDADE NOVA
        gc = self._try_secrets_specific_json()
        if gc:
            try:
                self.gc = gc
                self.sheet = self.gc.open(self.sheet_name).sheet1
                print(f"\n✅ CONECTADO via {self.credentials_source}")
                print(f"📊 Planilha: '{self.sheet_name}'")
                print(f"{'='*60}\n")
                return
            except Exception as e:
                print(f"\n❌ DEBUG: Erro ao aber planilha com secrets específico: {type(e).__name__}: {e}\n")
                # Continuar para próxima tentativa

        # Tentar 2: Streamlit Secrets (raiz)
        gc = self._try_secrets_root()
        if gc:
            try:
                self.gc = gc
                self.sheet = self.gc.open(self.sheet_name).sheet1
                print(f"\n✅ CONECTADO via {self.credentials_source}")
                print(f"📊 Planilha: '{self.sheet_name}'")
                print(f"{'='*60}\n")
                return
            except Exception as e:
                print(f"\n❌ DEBUG: Erro ao aber planilha com secrets raiz: {type(e).__name__}: {e}\n")
                # Continuar para próxima tentativa

        # Tentar 3: Arquivo local
        gc = self._try_local_file()
        if gc:
            try:
                self.gc = gc
                self.sheet = self.gc.open(self.sheet_name).sheet1
                print(f"\n✅ CONECTADO via {self.credentials_source}")
                print(f"📊 Planilha: '{self.sheet_name}'")
                print(f"{'='*60}\n")
                return
            except Exception as e:
                print(f"\n❌ DEBUG: Erro ao aber planilha com arquivo local: {type(e).__name__}: {e}\n")
                # Não há mais fallbacks

        # Se chegou aqui, todos os métodos falharam
        print(f"\n{'='*60}")
        print(f"❌ ERRO CRÍTICO: Não foi possível estabelecer conexão")
        print(f"{'='*60}")
        print(f"\n🔍 O que foi tentado (em ordem):\n")
        print(f"1. Streamlit Secrets (chave específica): st.secrets['gcp_service_account']")
        print(f"2. Streamlit Secrets (raiz): Chaves na raiz (project_id, private_key, etc.)")
        print(f"3. Arquivo local: service_account.json ou service-account.json")
        print(f"\n💡 SOLUÇÕES:\n")
        print(f"🌤️ Ambiente Cloud (Streamlit Cloud):")
        print(f"   1. Acesse: https://cloud.streamlit.io/")
        print(f"   2. Vá em: Seu app → Settings → Secrets")
        print(f"   3. Adicione um secret com nome: gcp_service_account")
        print(f"   4. Cole TODO o conteúdo do seu service_account.json (não apenas o caminho)")
        print(f"\n💻 Ambiente Local (Desenvolvimento):")
        print(f"   - Certifique-se de que 'service_account.json' existe na raiz do projeto")
        print(f"   - Ou renomeie para 'service-account.json' se preferir")
        print(f"\n📖 Documentação detalhada: Veja DEPLOYMENT.md")
        print(f"{'='*60}\n")

        raise Exception(
            "❌ Erro Crítico: Não foi possível encontrar credenciais válidas do Google Service Account.\n\n"
            f"Tentado: Secrets específico, Secrets raiz, Arquivo local\n\n"
            "Consulte os logs de debug acima para detalhes."
        )

    def get_connection_info(self) -> Dict[str, str]:
        """
        Retorna informações sobre a conexão atual.
        Útil para debugging e verificação do ambiente.
        """
        return {
            'sheet_name': self.sheet_name,
            'credentials_source': self.credentials_source or 'Não conectado',
            'connection_status': '✅ Conectado' if self.sheet else '❌ Desconectado'
        }

    def get_data(self) -> pd.DataFrame:
        """
        Retorna todos os dados da planilha como um DataFrame.

        Returns:
            DataFrame com os dados da planilha (colunas: Data, Mensagem Crua, Resposta)
        """
        try:
            print(f"🔍 DEBUG: Obtendo dados da planilha...")
            # Obter todos os dados da planilha
            records = self.sheet.get_all_records()
            print(f"✅ DEBUG: {len(records)} registros encontrados")

            if not records:
                # Retornar DataFrame vazio com as colunas esperadas
                print(f"⚠️  DEBUG: Planilha vazia, retornando DataFrame vazio")
                return pd.DataFrame(columns=['Data', 'Mensagem Crua', 'Resposta'])

            df = pd.DataFrame(records)
            print(f"✅ DEBUG: DataFrame criado com {len(df)} linhas e {len(df.columns)} colunas")
            return df
        except Exception as e:
            print(f"❌ DEBUG: Erro ao obter dados: {type(e).__name__}: {e}")
            raise Exception(f"Erro ao obter dados: {str(e)}")

    def append_data(self, date: str, text: str) -> bool:
        """
        Adiciona uma nova linha à planilha.

        Args:
            date: Data no formato DD/MM/YYYY ou string
            text: Texto narrativo da mensagem

        Returns:
            True se bem-sucedido
        """
        try:
            # Encontrar a próxima linha vazia
            next_row = len(self.sheet.get_all_values()) + 1
            print(f"🔍 DEBUG: Adicionando dados na linha {next_row}")

            # Adicionar data, mensagem e resposta vazia
            self.sheet.update_cell(next_row, 1, date)
            self.sheet.update_cell(next_row, 2, text)
            self.sheet.update_cell(next_row, 3, "")  # Resposta vazia inicialmente

            print(f"✅ Dados adicionados: {date}")
            return True
        except Exception as e:
            print(f"❌ DEBUG: Erro ao adicionar dados: {type(e).__name__}: {e}")
            raise Exception(f"Erro ao adicionar dados: {str(e)}")

    def update_cell(self, row: int, col: int, value: str) -> bool:
        """
        Atualiza uma célula específica da planilha.

        Args:
            row: Número da linha (1-indexed, incluindo cabeçalho)
            col: Número da coluna (1=A, 2=B, 3=C)
            value: Novo valor para a célula

        Returns:
            True se bem-sucedido
        """
        try:
            # Ajustar row para considerar o cabeçalho (row 1 é o cabeçalho)
            # Se o usuário passa row=1, queremos a primeira linha de dados (row 2 na planilha)
            actual_row = row + 1

            print(f"🔍 DEBUG: Atualizando célula: linha {actual_row}, coluna {col}")
            self.sheet.update_cell(actual_row, col, value)
            print(f"✅ Célula atualizada: linha {row}, coluna {col}")
            return True
        except Exception as e:
            print(f"❌ DEBUG: Erro ao atualizar célula: {type(e).__name__}: {e}")
            raise Exception(f"Erro ao atualizar célula: {str(e)}")

    def delete_row(self, row: int) -> bool:
        """
        Deleta uma linha específica da planilha.

        Args:
            row: Número da linha (1-indexed, excluindo cabeçalho)

        Returns:
            True se bem-sucedido
        """
        try:
            # Ajustar row para considerar o cabeçalho
            actual_row = row + 1
            print(f"🔍 DEBUG: Deletando linha {actual_row}")
            self.sheet.delete_rows(actual_row)
            print(f"✅ Linha deletada: {row}")
            return True
        except Exception as e:
            print(f"❌ DEBUG: Erro ao deletar linha: {type(e).__name__}: {e}")
            raise Exception(f"Erro ao deletar linha: {str(e)}")

    def get_all_values(self) -> list:
        """
        Retorna todos os valores da planilha como lista de listas.

        Returns:
            Lista de listas com todos os valores
        """
        try:
            print(f"🔍 DEBUG: Obtendo todos os valores...")
            values = self.sheet.get_all_values()
            print(f"✅ DEBUG: {len(values)} linhas obtidas")
            return values
        except Exception as e:
            print(f"❌ DEBUG: Erro ao obter valores: {type(e).__name__}: {e}")
            raise Exception(f"Erro ao obter valores: {str(e)}")
