from pathlib import Path
import io
from datetime import datetime
import pandas as pd

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload


def lerDadoWebPonto(
    column_data=None,
    column_data_hora=None,
    column_int=None,
    column_float=None,
    column_str=None,
    campos=None
):

    # ==========================================================
    # LOCALIZA O ARQUIVO DE CREDENCIAL
    # ==========================================================

    pasta_script = Path(__file__).resolve().parent
    arquivo_credencial = pasta_script / "credenciais.json"

    # ==========================================================
    # AUTENTICAÇÃO
    # ==========================================================

    scopes = [
        "https://www.googleapis.com/auth/drive.readonly"
    ]

    credenciais = service_account.Credentials.from_service_account_file(
        arquivo_credencial,
        scopes=scopes
    )

    drive = build(
        "drive",
        "v3",
        credentials=credenciais
    )

    # ==========================================================
    # PROCURA OS ARQUIVOS EXCEL
    # ==========================================================

    id_pasta = "1EUfbEuEpEQb6fEdmSpzpT6s_Ql4-SMGE"

    query = f"""
        '{id_pasta}' in parents
        and trashed = false
        and (
            mimeType = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            or mimeType = 'application/vnd.ms-excel'
        )
    """

    resultado = drive.files().list(
        q=query,
        fields="files(id, name, mimeType)",
        pageSize=1000
    ).execute()

    arquivos = resultado.get("files", [])

    print(f"\tArquivos WebPonto encontrados: {len(arquivos)}")

    # ==========================================================
    # LER OS ARQUIVOS
    # ==========================================================

    dataframes = []

    for arquivo in arquivos:

        print(f"\tLendo: {arquivo['name']}")

        try:

            request = drive.files().get_media(
                fileId=arquivo["id"]
            )

            arquivo_bytes = io.BytesIO()

            downloader = MediaIoBaseDownload(
                arquivo_bytes,
                request
            )

            concluido = False

            while not concluido:
                status, concluido = downloader.next_chunk()

            arquivo_bytes.seek(0)

            # Lê o Excel
            df = pd.read_excel(arquivo_bytes)

            # Guarda o nome do arquivo
            df["Arquivo_Origem"] = arquivo["name"]

            dataframes.append(df)

        except Exception as erro:

            print(f"ERRO ao ler {arquivo['name']}: {erro}")

    # ==========================================================
    # JUNTA TODOS OS ARQUIVOS
    # ==========================================================

    if not dataframes:

        print("Nenhum arquivo Excel foi lido.")

        return pd.DataFrame()

    df_final = pd.concat(
        dataframes,
        ignore_index=True
    )

    print(f"\tArquivos lidos: {len(dataframes)}")
    print(f"\tRegistros: {len(df_final)}")

    # ==========================================================
    # TRATAMENTO DAS COLUNAS
    # ==========================================================

    # Datas: DD/MM/AAAA HH:MM:SS
    if column_data:

        for col in column_data:

            if col not in df_final.columns:
                continue

            df_final[col] = pd.to_datetime(
                df_final[col],
                format="%d/%m/%Y %H:%M:%S",
                errors="coerce"
            )

            # Tenta interpretar os valores que não foram convertidos
            nulos = df_final[col].isna()

            if nulos.any():

                df_final.loc[nulos, col] = pd.to_datetime(
                    df_final.loc[nulos, col],
                    errors="coerce",
                    dayfirst=True
                )

    # Horários: HH:MM:SS
    if column_data_hora:

        for col in column_data_hora:

            if col not in df_final.columns:
                continue

            df_final[col] = pd.to_datetime(
                df_final[col].astype("string"),
                format="%H:%M:%S",
                errors="coerce"
            )

    # Números inteiros, permitindo valores nulos
    if column_int:

        for col in column_int:

            if col not in df_final.columns:
                continue

            df_final[col] = pd.to_numeric(
                df_final[col],
                errors="coerce"
            ).astype("Int64")

    # Números decimais
    if column_float:

        for col in column_float:

            if col not in df_final.columns:
                continue

            df_final[col] = pd.to_numeric(
                df_final[col],
                errors="coerce"
            ).astype("Float64")

    # Textos
    if column_str:

        for col in column_str:

            if col not in df_final.columns:
                continue

            df_final[col] = df_final[col].astype("string")

    # ==========================================================
    # SELECIONA AS COLUNAS
    # ==========================================================

    if campos:
        df_final = df_final[
            [col for col in campos if col in df_final.columns]
        ]

    print(
        f'\033[92mBase WebPonto concluído em '
        f'{datetime.now().strftime("%d/%m/%Y %H:%M:%S")}\033[0m'
    )

    return df_final