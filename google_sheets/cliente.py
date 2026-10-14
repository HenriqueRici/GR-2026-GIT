"""Leitura e escrita explícita de planilhas Google com autenticação sob demanda."""

import os
from datetime import datetime
from pathlib import Path

import gspread
import pandas as pd
from google.oauth2.service_account import Credentials

from modelos.conversoes import converter_numeros_textos

SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]


# Caminho do arquivo JSON
CAMINHO_CREDENCIAIS = Path(
    os.environ.get("GOOGLE_SHEETS_CREDENTIALS", Path(__file__).parent / "credenciais.json")
)


planilha = None


def obter_planilha():
    """Autentica no primeiro uso e reutiliza a planilha durante a execução."""
    global planilha
    if planilha is None:
        credenciais = Credentials.from_service_account_file(CAMINHO_CREDENCIAIS, scopes=SCOPES)
        cliente = gspread.authorize(credenciais)
        planilha = cliente.open("BASES GR 2026")
    return planilha


def getGoogleSheets(
    nome_aba, column_data=None, column_int=None, column_float=None, column_str=None
):
    """Lê a aba e converte datas, inteiros anuláveis, decimais brasileiros e textos."""
    aba = obter_planilha().worksheet(nome_aba)
    # RETORNA TUDO COMO TEXTO

    dados = aba.get_all_values()

    # Primeira linha = cabeçalho
    df = pd.DataFrame(dados[1:], columns=dados[0])
    # TRATAMENTO DAS COLUNAS DE DATA

    if column_data:
        for column in column_data:
            if column not in df.columns:
                continue
            # 1. Formato:
            # 01/06/2025 00:00:00

            convertido = pd.to_datetime(df[column], format="%d/%m/%Y %H:%M:%S", errors="coerce")
            # 2. Tenta outros formatos

            valores_nulos = convertido.isna()

            if valores_nulos.any():
                convertido.loc[valores_nulos] = pd.to_datetime(
                    df.loc[valores_nulos, column], errors="coerce", dayfirst=True
                )

            df[column] = convertido
    # TRATAMENTO DAS COLUNAS INTEIRAS

    converter_numeros_textos(df, column_int, column_float, column_str, decimal_brasileiro=True)
    # TRATAMENTO DAS COLUNAS DECIMAIS
    # TRATAMENTO DAS COLUNAS DE TEXTO
    # LOG

    print(
        f"\033[92mBase {nome_aba} concluído em "
        f"{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\033[0m"
    )

    return df


def set_df(df, nome_aba):
    """Substitui todo o conteúdo da aba pelo DataFrame (operação de escrita explícita)."""
    aba = obter_planilha().worksheet(nome_aba)

    aba.clear()

    dados = [df.columns.tolist()] + df.fillna("").values.tolist()

    aba.update(dados, "A1")
