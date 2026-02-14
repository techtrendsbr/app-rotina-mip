import gspread
import pandas as pd
import json
import os
from typing import Optional, Dict, Any


class SheetManager:
    """Gerencia conexões e operações com o Google Sheets.

    Suporta múltiplos métodos de autenticação com fallback automático:
    1. Streamlit Secrets (JSON Payload como string) - PRIORIDADE
    2. Arquivo local (Desenvolvimento)
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

    def _connect(self):
        """Estabelece conexão com o Google Sheets."""
        print(f"\n{'='*60}")
        print(f"🔧 Iniciando conexão com Google Sheets...")
        print(f"📋 Planilha alvo: '{self.sheet_name}'")
        print(f"{'='*60}\n")

        # Tentar 1: Streamlit Secrets (Cloud) - PRIORIDADE
        try:
            import streamlit as st

            st.write("🔍 DEBUG: Buscando 'service_account_file_content' em st.secrets...")
            secret_value = st.secrets.get('service_account_file_content')

            if secret_value is None:
                st.error("⚠️ Chave 'service_account_file_content' não encontrada em st.secrets")
                raise Exception("Secret não encontrado")

            st.write(f"✅ DEBUG: Secret encontrado! Tipo: {type(secret_value)}, Tamanho: {len(secret_value)} caracteres")

            # Se for uma string (JSON como texto), fazer parse
            if isinstance(secret_value, str):
                try:
                    credentials_dict = json.loads(secret_value)
                    st.write(f"✅ DEBUG: Parseado JSON string com sucesso ({len(credentials_dict)} campos)")
                except json.JSONDecodeError as e:
                    st.error(f"❌ DEBUG: Falha ao fazer parse JSON: {e}")
                    raise Exception(f"Erro ao fazer parse JSON: {e}")
            elif isinstance(secret_value, dict):
                # Se for um dict (AttrDict), converter
                credentials_dict = dict(secret_value)
                st.write(f"✅ DEBUG: Convertido de dict para dict Python ({len(credentials_dict)} campos)")
            else:
                st.error(f"❌ DEBUG: Tipo de secret não suportado: {type(secret_value)}")
                raise Exception(f"Tipo de secret não suportado: {type(secret_value)}")

            # Verificar campos essenciais
            required_fields = ['type', 'project_id', 'private_key_id', 'private_key', 'client_email', 'client_id']
            missing_fields = [f for f in required_fields if f not in credentials_dict]

            if missing_fields:
                st.error(f"❌ DEBUG: Campos faltando no JSON: {missing_fields}")
                raise Exception(f"Campos faltando no JSON: {missing_fields}")

            st.write(f"✅ DEBUG: Todos os campos essenciais presentes")

            # Conectar usando o dict
            try:
                self.gc = gspread.service_account_from_dict(credentials_dict)
                self.credentials_source = "Streamlit Secrets (JSON Payload)"
                st.write(f"✅ DEBUG: gspread.service_account_from_dict() bem-sucedido")
            except Exception as e:
                st.error(f"❌ DEBUG: Erro ao conectar com gspread: {str(e)}")
                raise Exception(f"Erro ao conectar com gspread: {str(e)}")

            try:
                self.sheet = self.gc.open(self.sheet_name).sheet1
                st.write("")
                st.success(f"✅ CONECTADO via {self.credentials_source}")
                st.info(f"📊 Planilha: '{self.sheet_name}'")
                st.write(f"{'='*60}\n")
                return
            except Exception as e:
                st.error(f"❌ DEBUG: Erro ao abrir planilha: {str(e)}")
                raise Exception(f"Erro ao abrir planilha: {str(e)}")

        # Tentar 2: Arquivo Local (Desenvolvimento)
        try:
            credentials_files = ['service_account.json', 'service-account.json']

            for cred_file in credentials_files:
                if os.path.exists(cred_file):
                    st.write(f"✅ DEBUG: Arquivo local encontrado: {cred_file}")
                    try:
                        self.gc = gspread.service_account(filename=cred_file)
                        self.credentials_source = f"Arquivo local ({cred_file})"
                        st.write(f"✅ DEBUG: gspread.service_account() bem-sucedido")

                        try:
                            self.sheet = self.gc.open(self.sheet_name).sheet1
                            st.write("")
                            st.success(f"✅ CONECTADO via {self.credentials_source}")
                            st.info(f"📊 Planilha: '{self.sheet_name}'")
                            st.write(f"{'='*60}\n")
                            return
                        except Exception as e:
                            st.error(f"❌ DEBUG: Erro ao abrir planilha: {str(e)}")
                            raise Exception(f"Erro ao abrir planilha: {str(e)}")
                    except Exception as e:
                        st.error(f"❌ DEBUG: Erro ao usar arquivo local: {str(e)}")
                        continue

        # Se chegou aqui, nenhum método funcionou
        st.write(f"\n{'='*60}")
        st.error("❌ ERRO CRÍTICO: Não foi possível estabelecer conexão")
        st.write(f"{'='*60}\n")
        st.write("\n🔍 O que foi tentado (em ordem):\n")
        st.write("1. Streamlit Secrets (service_account_file_content)")
        st.write("2. Arquivo local (service_account.json ou service-account.json)")
        st.write("\n💡 SOLUÇÕES:\n")
        st.write("🌤️ Ambiente Cloud (Streamlit Cloud):")
        st.write("   1. Acesse: https://cloud.streamlit.io/")
        st.write("   2. Vá em: Seu app → Settings → Secrets")
        st.write("   3. Adicione um secret com nome: service_account_file_content")
        st.write("   4. Cole TODO o conteúdo do seu service_account.json (como string)")
        st.write("\n💻 Ambiente Local (Desenvolvimento):")
        st.write("   - Certifique-se de que 'service_account.json' ou 'service-account.json' existe na raiz do projeto")
        st.write("\n📖 Documentação detalhada: Veja DEPLOYMENT.md")
        st.write(f"{'='*60}\n")

        raise Exception(
            "❌ Erro Crítico: Não foi possível encontrar credenciais válidas do Google Service Account.\n\n"
            "Tentado: Streamlit Secrets, Arquivo local\n\n"
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
            import streamlit as st
            st.write("🔍 DEBUG: Obtendo dados da planilha...")

            # Obter todos os dados da planilha
            records = self.sheet.get_all_records()
            st.write(f"✅ DEBUG: {len(records)} registros encontrados")

            if not records:
                # Retornar DataFrame vazio com as colunas esperadas
                st.write("⚠️  DEBUG: Planilha vazia, retornando DataFrame vazio")
                return pd.DataFrame(columns=['Data', 'Mensagem Crua', 'Resposta'])

            df = pd.DataFrame(records)
            st.write(f"✅ DEBUG: DataFrame criado com {len(df)} linhas e {len(df.columns)} colunas")
            return df
        except Exception as e:
            st.error(f"❌ DEBUG: Erro ao obter dados: {type(e).__name__}: {str(e)}")
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
            import streamlit as st

            # Encontrar a próxima linha vazia
            next_row = len(self.sheet.get_all_values()) + 1
            st.write(f"🔍 DEBUG: Adicionando dados na linha {next_row}")

            # Adicionar data, mensagem e resposta vazia
            self.sheet.update_cell(next_row, 1, date)
            self.sheet.update_cell(next_row, 2, text)
            self.sheet.update_cell(next_row, 3, "")  # Resposta vazia inicialmente

            st.write(f"✅ Dados adicionados: {date}")
            return True
        except Exception as e:
            st.error(f"❌ DEBUG: Erro ao adicionar dados: {type(e).__name__}: {str(e)}")
            raise Exception(f"Erro ao adicionar dados: {str(e)}")

    def update_cell(self, row: int, col: int, value: str) -> bool:
        """
        Atualiza uma célula específica da planilha.

        Args:
            row: Número da linha (1-indexado, incluindo cabeçalho)
            col: Número da coluna (1=A, 2=B, 3=C)
            value: Novo valor para a célula

        Returns:
            True se bem-sucedido
        """
        try:
            import streamlit as st

            # Ajustar row para considerar o cabeçalho (row 1 é o cabeçalho)
            # Se o usuário passa row=1, queremos a primeira linha de dados (row 2 na planilha)
            actual_row = row + 1

            st.write(f"🔍 DEBUG: Atualizando célula: linha {actual_row}, coluna {col}")
            self.sheet.update_cell(actual_row, col, value)
            st.write(f"✅ Célula atualizada: linha {row}, coluna {col}")
            return True
        except Exception as e:
            st.error(f"❌ DEBUG: Erro ao atualizar célula: {type(e).__name__}: {str(e)}")
            raise Exception(f"Erro ao atualizar célula: {str(e)}")

    def delete_row(self, row: int) -> bool:
        """
        Deleta uma linha específica da planilha.

        Args:
            row: Número da linha (1-indexado, excluindo cabeçalho)

        Returns:
            True se bem-sucedido
        """
        try:
            import streamlit as st

            # Ajustar row para considerar o cabeçalho
            actual_row = row + 1
            st.write(f"🔍 DEBUG: Deletando linha {actual_row}")
            self.sheet.delete_rows(actual_row)
            st.write(f"✅ Linha deletada: {row}")
            return True
        except Exception as e:
            st.error(f"❌ DEBUG: Erro ao deletar linha: {type(e).__name__}: {str(e)}")
            raise Exception(f"Erro ao deletar linha: {str(e)}")

    def get_all_values(self) -> list:
        """
        Retorna todos os valores da planilha como lista de listas.

        Returns:
            Lista de listas com todos os valores
        """
        try:
            import streamlit as st
            st.write("🔍 DEBUG: Obtendo todos os valores...")
            values = self.sheet.get_all_values()
            st.write(f"✅ DEBUG: {len(values)} linhas obtidas")
            return values
        except Exception as e:
            st.error(f"❌ DEBUG: Erro ao obter valores: {type(e).__name__}: {str(e)}")
            raise Exception(f"Erro ao obter valores: {str(e)}")
