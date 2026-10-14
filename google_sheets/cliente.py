import gspread
import pandas as pd
from datetime import datetime
from pathlib import Path
from google.oauth2.service_account import Credentials


SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]


# Caminho do arquivo JSON
CAMINHO_CREDENCIAIS = Path(__file__).parent / "credenciais.json"


# Autenticação
credenciais = Credentials.from_service_account_file(
    CAMINHO_CREDENCIAIS,
    scopes=SCOPES
)

cliente = gspread.authorize(credenciais)


# Abre a planilha
planilha = cliente.open("BASES GR 2026")


def getGoogleSheets(
    nome_aba,
    column_data=None,
    column_int=None,
    column_float=None,
    column_str=None
):

    aba = planilha.worksheet(nome_aba)

    # ================================================================
    # RETORNA TUDO COMO TEXTO
    # ================================================================

    dados = aba.get_all_values()

    # Primeira linha = cabeçalho
    df = pd.DataFrame(
        dados[1:],
        columns=dados[0]
    )

    # ================================================================
    # TRATAMENTO DAS COLUNAS DE DATA
    # ================================================================

    if column_data:

        for column in column_data:

            if column not in df.columns:
                continue

            # --------------------------------------------------------
            # 1. Formato:
            # 01/06/2025 00:00:00
            # --------------------------------------------------------

            convertido = pd.to_datetime(
                df[column],
                format="%d/%m/%Y %H:%M:%S",
                errors="coerce"
            )

            # --------------------------------------------------------
            # 2. Tenta outros formatos
            # --------------------------------------------------------

            valores_nulos = convertido.isna()

            if valores_nulos.any():

                convertido.loc[valores_nulos] = pd.to_datetime(
                    df.loc[valores_nulos, column],
                    errors="coerce",
                    dayfirst=True
                )

            df[column] = convertido

    # ================================================================
    # TRATAMENTO DAS COLUNAS INTEIRAS
    # ================================================================

    if column_int:

        for column in column_int:

            if column not in df.columns:
                continue

            df[column] = pd.to_numeric(
                df[column],
                errors="coerce"
            ).astype("Int64")

    # ================================================================
    # TRATAMENTO DAS COLUNAS DECIMAIS
    # ================================================================
    if column_float:

        for column in column_float:

            if column not in df.columns:
                continue

            df[column] = (
                df[column]
                .astype(str)
                .str.strip()
                .str.replace(",", ".", regex=False)
            )

            df[column] = pd.to_numeric(
                df[column],
                errors="coerce"
            ).astype("Float64")

    # ================================================================
    # TRATAMENTO DAS COLUNAS DE TEXTO
    # ================================================================

    if column_str:

        for column in column_str:

            if column not in df.columns:
                continue

            df[column] = df[column].astype("string")

    # ================================================================
    # LOG
    # ================================================================

    print(
        f'\033[92mBase {nome_aba} concluído em '
        f'{datetime.now().strftime("%d/%m/%Y %H:%M:%S")}\033[0m'
    )

    return df


def set_df(df, nome_aba):

    aba = planilha.worksheet(nome_aba)

    aba.clear()

    dados = [df.columns.tolist()] + df.fillna("").values.tolist()

    aba.update(dados, "A1")