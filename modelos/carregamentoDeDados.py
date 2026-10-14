import pandas as pd
from pathlib import Path
import requests

def carregarArquivo(file_path, selected_columns=None, filters=None, drop_duplicates_by=None, exclude_empty=None, column_data=None):
    # Garante que file_path seja string (caso seja um objeto Path)
    file_path = str(file_path)

    # Verifica se o arquivo é Excel ou CSV e carrega o DataFrame
    if file_path.endswith(('.xlsx', '.xls')):
        df = pd.read_excel(file_path, usecols=selected_columns)
    elif file_path.endswith('.csv'):
        df = pd.read_csv(file_path, sep=';', usecols=selected_columns)
    else:
        raise ValueError("O arquivo precisa ser no formato CSV ou Excel.")

    # Converter colunas para datetime, se solicitado
    if column_data:
        for column in column_data:
            if column in df.columns:
                df[column] = pd.to_datetime(df[column], format='%d/%m/%Y %H:%M:%S', errors='coerce')
                df[column] = pd.to_datetime(df[column], errors='coerce', dayfirst=True)

    # Aplicar filtros baseados nos valores fornecidos
    if filters:
        for column, filter_values in filters.items():
            if column in df.columns:
                df = df[df[column].isin(filter_values)]

    # Excluir valores vazios ou nulos, se solicitado
    if exclude_empty:
        for column in exclude_empty:
            if column in df.columns:
                df = df[df[column].notna() & (df[column] != '')]

    # Remover duplicatas com base em colunas específicas
    if drop_duplicates_by:
        df = df.drop_duplicates(subset=drop_duplicates_by)

    return df

def carregarPastaArquivos(file_path, selected_columns=None, column_data=None):

    # Buscar todos os arquivos .xls e .xlsx na pasta
    arquivos_excel = list(Path(file_path).glob('*.xlsx*'))

    # Lista para armazenar os DataFrames
    dfs = []

    # Ler cada arquivo e adicionar à lista
    for arquivo in arquivos_excel:
        df = pd.read_excel(arquivo, usecols=selected_columns)
        
        # Se uma coluna de data for especificada, converte a coluna de data
        if column_data:
            df[column_data] = pd.to_datetime(df[column_data], errors='coerce')

        dfs.append(df)

    # Concatenar todos os DataFrames
    df_final = pd.concat(dfs, ignore_index=True)

    return df_final



def carregaAPIFormacaoObrigatoria(url):
    resp = requests.get(url)
    resp.raise_for_status()
    data = resp.json()

    header = data[0]
    rows = data[1:]

    df = pd.DataFrame(rows, columns=header)

    df['InicioExclusivo'] = pd.to_datetime(df['InicioExclusivo'], errors='coerce')
    df['FimInclusivo'] = pd.to_datetime(df['FimInclusivo'], errors='coerce')
    df['CHNecessaria'] = pd.to_numeric(df['CHNecessaria'], errors='coerce')
    df['CHCumprida'] = pd.to_numeric(df['CHCumprida'], errors='coerce')
    df['CPF'] = df['CPF'].astype('int64')

    resultado = df.rename(columns={'InicioExclusivo': 'InicioPeriodo', 'FimInclusivo': 'FimPeriodo', 'CHNecessaria':'CHObrigatoria', 'CHCumprida': 'CHObrigatoriaRealizada'})

    for col in resultado.select_dtypes(include=["datetimetz"]).columns:
        resultado[col] = (
        resultado[col]
        .dt.tz_convert('America/Sao_Paulo')
        .dt.tz_localize(None)  # remove o fuso
        .dt.normalize()        # força hora 00:00:00
    )
    return resultado

def carregaAPIFormacaoEletiva(url):
    resp = requests.get(url)
    resp.raise_for_status()
    data = resp.json()

    header = data[0]
    rows = data[1:]

    df = pd.DataFrame(rows, columns=header)

    df['CH'] = pd.to_numeric(df['CH'], errors='coerce')
    df['CPF'] = df['CPF'].astype('int64')

    resultado = df.rename(columns={'CH': 'CHEletiva'})
    return resultado