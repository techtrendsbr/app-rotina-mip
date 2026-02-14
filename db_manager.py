import gspread
import pandas as pd
import json
from datetime import datetime
from typing import Optional, Dict, Any
import os

class SheetManager:
    """Gerencia conexões e operações com o Google Sheets.

    Suporta autenticação via:
    1. Streamlit Secrets (Cloud) - st.secrets["gcp_service_account"]
    2. Arquivo local (Desenvolvimento) - service_account.json
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
        """Estabelece conexão com o Google Sheets.

        Tenta autenticar na seguinte ordem:
        1. Streamlit Secrets (ambiente cloud)
        2. Arquivo local service_account.json (desenvolvimento)
        """
        try:
            # Tentar 1: Arquivo local (Desenvolvimento local) - PRIORIDADE LOCAL
            credentials_files = ['service_account.json', 'service-account.json']

            for cred_file in credentials_files:
                if os.path.exists(cred_file):
                    self.gc = gspread.service_account(filename=cred_file)
                    self.credentials_source = f"Arquivo local ({cred_file})"
                    print(f"✅ Conectado via arquivo local à planilha: {self.sheet_name}")
                    self.sheet = self.gc.open(self.sheet_name).sheet1
                    return

            # Tentar 2: Streamlit Secrets (Cloud) - SOMENTE se não tiver arquivo local
            try:
                import streamlit as st
                # Usar get() para evitar erros de chave não existente
                credentials_json = st.secrets.get('gcp_service_account', None)
                if credentials_json:
                    credentials_dict = json.loads(credentials_json)
                    self.gc = gspread.service_account_from_dict(credentials_dict)
                    self.credentials_source = "Streamlit Secrets (Cloud)"
                    print(f"✅ Conectado via Streamlit Secrets à planilha: {self.sheet_name}")
                    self.sheet = self.gc.open(self.sheet_name).sheet1
                    return
            except (ImportError, KeyError, AttributeError, json.JSONDecodeError):
                pass  # Streamlit não disponível ou secret inválida, continuar para erro

            # Se nenhum método funcionou
            raise Exception(
                "Não foi possível encontrar credenciais do Google Service Account.\n\n"
                "**Ambiente Cloud (Streamlit Cloud):**\n"
                "1. Abra: https://cloud.streamlit.io/\n"
                "2. Vá em: Settings → Secrets\n"
                "3. Adicione: `gcp_service_account` com TODO o JSON do service account\n\n"
                "**Ambiente Local (Desenvolvimento):**\n"
                "- Certifique-se de que 'service_account.json' ou 'service-account.json' existe na raiz do projeto.\n"
                "- Veja .streamlit/secrets.toml.example para configuração local com secrets."
            )

        except Exception as e:
            raise Exception(f"Erro ao conectar ao Google Sheets: {str(e)}")

    def get_connection_info(self) -> Dict[str, str]:
        """
        Retorna informações sobre a conexão atual.
        Útil para debugging e verificação do ambiente.
        """
        return {
            'sheet_name': self.sheet_name,
            'credentials_source': self.credentials_source,
            'connection_status': '✅ Conectado' if self.sheet else '❌ Desconectado'
        }

    def get_data(self) -> pd.DataFrame:
        """
        Retorna todos os dados da planilha como um DataFrame.

        Returns:
            DataFrame com os dados da planilha (colunas: Data, Mensagem Crua, Resposta)
        """
        try:
            # Obter todos os dados da planilha
            records = self.sheet.get_all_records()

            if not records:
                # Retornar DataFrame vazio com as colunas esperadas
                return pd.DataFrame(columns=['Data', 'Mensagem Crua', 'Resposta'])

            df = pd.DataFrame(records)
            return df
        except Exception as e:
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

            # Adicionar data, mensagem e resposta vazia
            self.sheet.update_cell(next_row, 1, date)
            self.sheet.update_cell(next_row, 2, text)
            self.sheet.update_cell(next_row, 3, "")  # Resposta vazia inicialmente

            print(f"✅ Dados adicionados: {date}")
            return True
        except Exception as e:
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

            self.sheet.update_cell(actual_row, col, value)
            print(f"✅ Célula atualizada: linha {row}, coluna {col}")
            return True
        except Exception as e:
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
            self.sheet.delete_rows(actual_row)
            print(f"✅ Linha deletada: {row}")
            return True
        except Exception as e:
            raise Exception(f"Erro ao deletar linha: {str(e)}")

    def get_all_values(self) -> list:
        """
        Retorna todos os valores da planilha como lista de listas.

        Returns:
            Lista de listas com todos os valores
        """
        try:
            return self.sheet.get_all_values()
        except Exception as e:
            raise Exception(f"Erro ao obter valores: {str(e)}")
