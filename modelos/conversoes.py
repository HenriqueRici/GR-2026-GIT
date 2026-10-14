"""Conversões compartilhadas pelas fontes de dados, sem alterar seus índices."""

import pandas as pd


def converter_numeros_textos(
    df, column_int=None, column_float=None, column_str=None, decimal_brasileiro=False
):
    """Converte colunas existentes in-place e retorna o mesmo DataFrame.

    Inválidos viram nulos. Usa Int64/Float64 anuláveis e string do pandas.
    Somente Sheets solicita substituição da vírgula decimal; não remove milhares.
    Colunas ausentes são ignoradas, como nos clientes originais.
    """
    for coluna in column_int or ():
        if coluna in df.columns:
            df[coluna] = pd.to_numeric(df[coluna], errors="coerce").astype("Int64")
    for coluna in column_float or ():
        if coluna in df.columns:
            valores = df[coluna]
            if decimal_brasileiro:
                valores = valores.astype(str).str.strip().str.replace(",", ".", regex=False)
            df[coluna] = pd.to_numeric(valores, errors="coerce").astype("Float64")
    for coluna in column_str or ():
        if coluna in df.columns:
            df[coluna] = df[coluna].astype("string")
    return df
