import requests
import pandas as pd
from time import sleep
from datetime import datetime


class Menus:

    def __init__(self, cliente):
        self.cliente = cliente

    def _preparar_filtros(self, filtros):

        if not filtros:
            return filtros

        filtros_convertidos = []

        for filtro in filtros:

            # Garante que o filtro seja um dicionário
            if not isinstance(filtro, dict):
                raise TypeError(
                    "Cada filtro deve ser um dicionário."
                )

            filtro = filtro.copy()

            operador = filtro.get("operator")
            valor = filtro.get("value")

            # ============================================================
            # OPERADOR IN
            # ============================================================
            #
            # NÃO transformar [1, 2, 3] em "1,2,3".
            #
            # A API precisa receber a lista.
            #

            if operador == "in":

                if isinstance(valor, (tuple, set)):
                    valor = list(valor)

                elif not isinstance(valor, list):

                    # Permite também:
                    # "1,2,3"
                    # "1, 2, 3"

                    if isinstance(valor, str):

                        valor = [
                            item.strip()
                            for item in valor.split(",")
                            if item.strip() != ""
                        ]

                    else:
                        valor = [valor]

                filtro["value"] = valor

            # ============================================================
            # OUTROS OPERADORES
            # ============================================================
            #
            # Não altera o valor.
            #

            filtros_convertidos.append(filtro)

        return filtros_convertidos

    def consultar(
        self,
        nomeBase,
        menu,
        filtros=None,
        campos=None,
        ordenar=None,
        per_page=5000,
        column_data=None,
        column_int=None,
        column_str=None,
        exclude_empty=None
    ):

        url = f"{self.cliente.base_url}/menus/{menu}/execute"

        pagina = 1
        dados = []

        # ================================================================
        # PREPARAR FILTROS
        # ================================================================

        filtros = self._preparar_filtros(filtros)

        # ================================================================
        # CONSULTA API
        # ================================================================

        while True:

            body = {
                "pagination": {
                    "page": pagina,
                    "per_page": per_page
                }
            }

            if filtros:
                body["filters"] = filtros

            if campos:
                body["select_fields"] = campos

            if ordenar:
                body["order_by"] = ordenar

            try:

                r = requests.post(
                    url,
                    headers=self.cliente.headers,
                    json=body,
                    timeout=120
                )

            except requests.exceptions.RequestException as e:

                print()
                print("ERRO DE CONEXÃO COM A API:")
                print(e)

                raise

            # ============================================================
            # ERRO DA API
            # ============================================================

            if r.status_code != 200:

                print()
                print("RESPOSTA DA API:")
                print(r.text)

            r.raise_for_status()

            resposta = r.json()

            # ============================================================
            # DADOS
            # ============================================================

            registros = resposta.get("data", [])

            if not registros:

                print("Nenhum registro retornado.")
                break

            dados.extend(registros)

            # ============================================================
            # PAGINAÇÃO
            # ============================================================

            pagination = resposta.get("pagination", {})

            total_paginas = pagination.get(
                "total_pages",
                pagina
            )

            if pagina >= total_paginas:
                break

            pagina += 1

            sleep(0.1)

        # ================================================================
        # DATAFRAME
        # ================================================================

        df = pd.DataFrame(dados)

        # ================================================================
        # TRATAMENTO DAS COLUNAS DE DATA
        # ================================================================

        if column_data:

            for column in column_data:

                if column not in df.columns:
                    continue

                # Mantém os valores originais
                original = df[column].copy()

                # --------------------------------------------------------
                # 1. Formato brasileiro
                # 01/06/2025
                # --------------------------------------------------------

                convertido = pd.to_datetime(
                    original,
                    format="%d/%m/%Y",
                    errors="coerce"
                )

                # --------------------------------------------------------
                # 2. Formato brasileiro com hora
                # 01/06/2025 00:00:00
                # --------------------------------------------------------

                nulos = convertido.isna()

                if nulos.any():

                    convertido.loc[nulos] = pd.to_datetime(
                        original.loc[nulos],
                        format="%d/%m/%Y %H:%M:%S",
                        errors="coerce"
                    )

                # --------------------------------------------------------
                # 3. Formato ISO
                #
                # 2025-06-01
                # 2025-06-01T00:00:00
                # 2025-06-01T00:00:00.000
                # --------------------------------------------------------

                nulos = convertido.isna()

                if nulos.any():

                    convertido.loc[nulos] = pd.to_datetime(
                        original.loc[nulos],
                        errors="coerce"
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
        # TRATAMENTO DAS COLUNAS DE TEXTO
        # ================================================================

        if column_str:

            for column in column_str:

                if column not in df.columns:
                    continue

                df[column] = df[column].astype("string")

        # ================================================================
        # REMOVER LINHAS COM COLUNAS VAZIAS
        # ================================================================

        if exclude_empty:

            for column in exclude_empty:

                if column in df.columns:

                    df = df[
                        df[column].notna() &
                        (df[column].astype(str).str.strip() != '')
                    ]

        # ================================================================
        # LOG
        # ================================================================

        print(
            f'\033[92m{nomeBase} concluído em '
            f'{datetime.now().strftime("%d/%m/%Y %H:%M:%S")}'
            f'\033[0m'
        )

        return df