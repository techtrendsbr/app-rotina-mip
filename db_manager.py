import gspread
import pandas as pd
from datetime import datetime
from typing import Optional, Dict, Any


class SheetManager:
    """Gerencia conexões e operações com o Google Sheets."""

    def __init__(self, credentials_file: str = 'service_account.json', sheet_name: str = 'Journal Database'):
        """
        Inicializa o gerenciador de planilhas.

        Args:
            credentials_file: Caminho para o arquivo de credenciais do Google Service Account
            sheet_name: Nome da planilha no Google Drive
        """
        self.credentials_file = credentials_file
        self.sheet_name = sheet_name
        self.gc = None
        self.sheet = None
        self._connect()

    def _connect(self):
        """Estabelece conexão com o Google Sheets."""
        try:
            self.gc = gspread.service_account(filename=self.credentials_file)
            self.sheet = self.gc.open(self.sheet_name).sheet1
            print(f"✅ Conectado à planilha: {self.sheet_name}")
        except Exception as e:
            raise Exception(f"Erro ao conectar ao Google Sheets: {str(e)}")

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
