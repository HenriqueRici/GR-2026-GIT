"""Consolidação e pontuação do absenteísmo com auditoria das ocorrências."""

import json

import pandas as pd


def absenteismoWebPonto(basePessoal, baseWebPonto):
    # Faz uma cópia real do DataFrame após o filtro para evitar SettingWithCopyWarning
    """Extrai atestados/doações sem horas trabalhadas e cruza com vínculos ativos."""
    baseWebPontoFrequencia = baseWebPonto[
        baseWebPonto["MF"].isin(
            [
                "01 - ATESTADO DE COMPARECIMENTO CONSULTA OU AFASTAMENTO MÉDICO ATÉ 03 DIAS",
                "14 - DOAÇÃO DE SANGUE",
            ]
        )
    ].copy()

    baseWebPontoFrequencia = baseWebPontoFrequencia[["LOGIN", "DataFrequencia", "MF"]]

    # Calcular horas por período
    baseWebPonto["HorasManha"] = (
        baseWebPonto["SaidaManha"] - baseWebPonto["EntradaManha"]
    ).dt.total_seconds() / 3600
    baseWebPonto["HorasTarde"] = (
        baseWebPonto["SaidaTarde"] - baseWebPonto["EntradaTarde"]
    ).dt.total_seconds() / 3600
    baseWebPonto["HorasNoite"] = (
        baseWebPonto["SaidaNoite"] - baseWebPonto["EntradaNoite"]
    ).dt.total_seconds() / 3600

    # Soma total de horas no dia
    baseWebPonto["TotalHorasDia"] = baseWebPonto[["HorasManha", "HorasTarde", "HorasNoite"]].sum(
        axis=1, skipna=True
    )
    baseWebPonto = (
        baseWebPonto.groupby(["LOGIN", "DataFrequencia"])
        .agg(TotalHorasDia=("TotalHorasDia", "sum"))
        .reset_index()
    )

    baseWebPonto = pd.merge(
        baseWebPontoFrequencia, baseWebPonto, on=["LOGIN", "DataFrequencia"], how="left"
    )

    # Renomear e filtrar por ausência de horas
    baseWebPonto = baseWebPonto[baseWebPonto["TotalHorasDia"] == 0]

    baseWebPonto = baseWebPonto.rename(columns={"LOGIN": "CPF", "MF": "TIPO"})
    baseWebPonto = baseWebPonto[["CPF", "DataFrequencia", "TIPO"]]

    # Aceita também o esquema Func/Vinc produzido por proporcaoVinculo.
    basePessoal = basePessoal.rename(
        columns={
            chave: destino
            for chave, destino in [("Func", "NumFunc"), ("Vinc", "NumVinc")]
            if destino not in basePessoal.columns
        }
    )
    baseWebPonto = pd.merge(baseWebPonto, basePessoal, on=["CPF"], how="left")
    baseWebPonto = baseWebPonto[
        (baseWebPonto["DataFrequencia"] >= baseWebPonto["DataInicio"])
        & (baseWebPonto["DataFrequencia"] <= baseWebPonto["DataFinal"])
    ].copy()
    baseWebPonto = baseWebPonto[["NumFunc", "NumVinc", "DataFrequencia", "TIPO"]]
    baseWebPonto = baseWebPonto.rename(
        columns={
            "NumFunc": "Func",
            "NumVinc": "Vinc",
            "DataFrequencia": "DataInicial",
            "TIPO": "Tipo",
        }
    )
    baseWebPonto["DataFinal"] = baseWebPonto["DataInicial"]

    return baseWebPonto


def absenteismoLicencasAfastamentos(baseLicencasAfastamentos, dataInicioGR, dataFimGR):
    """Recorta licenças à vigência da GR e descarta períodos sem dias positivos."""
    baseLicencasAfastamentos.loc[
        baseLicencasAfastamentos["DataFinal"] == pd.Timestamp("1753-01-01"), "DataFinal"
    ] = dataFimGR

    baseLicencasAfastamentos = baseLicencasAfastamentos[
        baseLicencasAfastamentos["DataFinal"] >= dataInicioGR
    ].copy()
    baseLicencasAfastamentos["DataInicial"] = baseLicencasAfastamentos["DataInicial"].mask(
        baseLicencasAfastamentos["DataInicial"] < dataInicioGR, dataInicioGR
    )
    baseLicencasAfastamentos["DataFinal"] = baseLicencasAfastamentos["DataFinal"].mask(
        baseLicencasAfastamentos["DataFinal"] > dataFimGR, dataFimGR
    )

    baseLicencasAfastamentos["DiasAfastamentoGR"] = (
        baseLicencasAfastamentos["DataFinal"] - baseLicencasAfastamentos["DataInicial"]
    ).dt.days + 1
    baseLicencasAfastamentos = baseLicencasAfastamentos[
        baseLicencasAfastamentos["DiasAfastamentoGR"] > 0
    ]
    baseLicencasAfastamentos = baseLicencasAfastamentos[
        ["Func", "Vinc", "DataInicial", "DataFinal", "Tipo"]
    ]

    return baseLicencasAfastamentos


def absenteismoFrequencias(baseWebPonto, baseFrequencias):
    """Cruza faltas SEAP com dias do WebPonto sem horas registradas."""
    for col in [
        "EntradaManha",
        "SaidaManha",
        "EntradaTarde",
        "SaidaTarde",
        "EntradaNoite",
        "SaidaNoite",
    ]:
        baseWebPonto[col] = pd.to_datetime(baseWebPonto[col], format="%H:%M:%S", errors="coerce")

    # Calcular horas por período
    baseWebPonto["HorasManha"] = (
        baseWebPonto["SaidaManha"] - baseWebPonto["EntradaManha"]
    ).dt.total_seconds() / 3600
    baseWebPonto["HorasTarde"] = (
        baseWebPonto["SaidaTarde"] - baseWebPonto["EntradaTarde"]
    ).dt.total_seconds() / 3600
    baseWebPonto["HorasNoite"] = (
        baseWebPonto["SaidaNoite"] - baseWebPonto["EntradaNoite"]
    ).dt.total_seconds() / 3600

    # Soma total de horas no dia
    baseWebPonto["TotalHorasDia"] = baseWebPonto[["HorasManha", "HorasTarde", "HorasNoite"]].sum(
        axis=1, skipna=True
    )
    baseWebPonto = (
        baseWebPonto.groupby(["LOGIN", "DataFrequencia"])["TotalHorasDia"].sum().reset_index()
    )

    baseWebPonto = pd.merge(
        baseWebPonto,
        baseFrequencias,
        left_on=["LOGIN", "DataFrequencia"],
        right_on=["CPF", "DataInicial"],
        how="left",
    )

    baseWebPonto = baseWebPonto[baseWebPonto["TotalHorasDia"] == 0].copy()
    baseWebPonto = baseWebPonto[baseWebPonto["Tipo"].notna()].copy()
    baseWebPonto = baseWebPonto[["Func", "Vinc", "DataInicial", "DataFinal", "Tipo"]]

    return baseWebPonto


def absenteismoGeral(grupoEleitos, absenteismoWebPonto, baseLicencas, baseFrequencia):
    """Consolida ocorrências, conta dias únicos e anexa JSON de auditoria por vínculo."""
    baseAbs = pd.concat([absenteismoWebPonto, baseLicencas, baseFrequencia])

    baseAbs = baseAbs.drop_duplicates(subset=["Func", "Vinc", "Tipo", "DataInicial", "DataFinal"])
    baseAbs["Tipo"] = baseAbs["Tipo"].str.replace(r"^\d+\s*-\s*", "", regex=True)

    def manter_licencas_validas(df):
        """Exclui atestados/doações integralmente contidos em outra licença do vínculo."""
        resultado = []
        for _, group in df.groupby(["Func", "Vinc"]):
            # Separar as licenças do tipo específico "01"
            licencas_tipo_01 = group[
                group["Tipo"].isin(
                    [
                        "ATESTADO DE COMPARECIMENTO CONSULTA OU AFASTAMENTO MÉDICO ATÉ 03 DIAS",
                        "DOAÇÃO DE SANGUE",
                    ]
                )
            ]

            # Separar as licenças de outros tipos
            licencas_outras = group[
                ~group["Tipo"].isin(
                    [
                        "ATESTADO DE COMPARECIMENTO CONSULTA OU AFASTAMENTO MÉDICO ATÉ 03 DIAS",
                        "DOAÇÃO DE SANGUE",
                    ]
                )
            ]

            # Manter todas as licenças que não são do tipo 01
            resultado.extend(licencas_outras.to_dict(orient="records"))

            # Verificar se cada licença do tipo 01 não está completamente dentro de outra
            for _, row in licencas_tipo_01.iterrows():
                if not any(
                    (row["DataInicial"] >= licenca["DataInicial"])
                    and (row["DataFinal"] <= licenca["DataFinal"])
                    for _, licenca in licencas_outras.iterrows()
                ):
                    resultado.append(row.to_dict())

        return pd.DataFrame(resultado)

    baseAbs = manter_licencas_validas(baseAbs)
    eleitos = grupoEleitos.rename(columns={"NumFunc": "Func", "NumVinc": "Vinc"})

    eleitosParaAbs = eleitos[["Func", "Vinc", "DataInicio", "DataFinal"]]
    eleitosParaAbs = eleitosParaAbs.rename(
        columns={"DataInicio": "DataInicioAtribuicao", "DataFinal": "DataFinalAtribuicao"}
    )

    baseAbs = pd.merge(baseAbs, eleitosParaAbs, on=["Func", "Vinc"], how="left")
    baseAbs = baseAbs[
        (
            (baseAbs["Tipo"] == "ARC - AGUARDANDO REGULARIZAÇÃO DO CARGO")
            & (baseAbs["DataInicial"] >= baseAbs["DataInicioAtribuicao"])
            & (baseAbs["DataFinal"] <= baseAbs["DataFinalAtribuicao"])
        )
        | (baseAbs["Tipo"] != "ARC - AGUARDANDO REGULARIZAÇÃO DO CARGO")
    ]

    baseAbs = baseAbs[["Func", "Vinc", "Tipo", "DataInicial", "DataFinal"]]
    baseAbs = baseAbs.drop_duplicates(subset=["Func", "Vinc", "Tipo", "DataInicial", "DataFinal"])

    absenteismo_por_vinculo = {}
    for item in baseAbs.to_dict(orient="records"):
        chave = (item["Func"], item["Vinc"])
        absenteismo_por_vinculo.setdefault(chave, []).append(item)

    def calcular_dias_ausentes(df):
        # Ordenar as datas para facilitar a junção de períodos sobrepostos
        """Conta datas únicas após unir períodos sobrepostos de afastamento."""
        df = df.sort_values(by=["DataInicial", "DataInicial"])

        # Lista para armazenar os períodos consolidados
        periodos_consolidados = []

        # Variáveis para rastrear o início e o fim do período atual
        inicio_periodo = None
        fim_periodo = None

        # Iterar pelas linhas e consolidar os períodos
        for i, row in df.iterrows():
            if inicio_periodo is None:
                # Definir o primeiro período
                inicio_periodo = row["DataInicial"]
                fim_periodo = row["DataFinal"]
            else:
                # Se o período atual se sobrepõe ao anterior, estenda o período
                if row["DataInicial"] <= fim_periodo:
                    fim_periodo = max(fim_periodo, row["DataFinal"])
                else:
                    # Se não houver sobreposição, finalize o período anterior e inicie um novo
                    periodos_consolidados.append((inicio_periodo, fim_periodo))
                    inicio_periodo = row["DataInicial"]
                    fim_periodo = row["DataFinal"]

        # Adicionar o último período
        if inicio_periodo is not None:
            periodos_consolidados.append((inicio_periodo, fim_periodo))

        # Criar um conjunto para armazenar os dias únicos consolidados
        dias_unicos = set()

        # Adicionar os dias de cada período consolidado ao conjunto
        for inicio, fim in periodos_consolidados:
            dias_unicos.update(pd.date_range(inicio, fim))

        return len(dias_unicos)

    absenteismoCompilado = (
        baseAbs.groupby(["Func", "Vinc"])
        .apply(calcular_dias_ausentes, include_groups=False)
        .reset_index(name="DiasAbsenteismo")
    )

    eleitos = grupoEleitos.rename(columns={"NumFunc": "Func", "NumVinc": "Vinc"})
    eleitos = pd.merge(eleitos, absenteismoCompilado, on=["Func", "Vinc"], how="left")

    eleitos["DiasAbsenteismo"] = eleitos["DiasAbsenteismo"].fillna(0)

    def encontrar_json_por_func_vinc(num_func, num_vinc):
        """Obtém as ocorrências previamente indexadas por servidor e vínculo."""
        return absenteismo_por_vinculo.get((num_func, num_vinc), [])

    eleitos["ListaAbsenteismo"] = eleitos.apply(
        lambda row: encontrar_json_por_func_vinc(row["Func"], row["Vinc"]), axis=1
    )

    def remover_informacao_dos_jsons(json_list, chave_para_remover):
        """Remove uma chave dos registros de auditoria in-place."""
        for item in json_list:
            item.pop(chave_para_remover, None)  # Remove a chave, se existir
        return json_list

    eleitos["ListaAbsenteismo"] = eleitos["ListaAbsenteismo"].apply(
        lambda x: remover_informacao_dos_jsons(x, "Func")
    )
    eleitos["ListaAbsenteismo"] = eleitos["ListaAbsenteismo"].apply(
        lambda x: remover_informacao_dos_jsons(x, "Vinc")
    )

    eleitos["ListaAbsenteismo"] = eleitos["ListaAbsenteismo"].apply(
        lambda lista: json.dumps(
            [
                {
                    **d,
                    "DataInicial": d["DataInicial"].strftime("%Y-%m-%d %H:%M:%S"),
                    "DataFinal": d["DataFinal"].strftime("%Y-%m-%d %H:%M:%S"),
                }
                for d in lista
            ],
            ensure_ascii=False,
        )
    )

    return eleitos


def pontuacaoAbsenteismo(row):
    """Pontua dias inteiros em faixas de dois; preserva -150 fora das faixas."""
    dias = row["DiasAbsenteismo"]
    teto = maxAbsenteismo(row)
    if dias == 0:
        return teto
    for faixa in range(1, 16):
        if dias in (2 * faixa - 1, 2 * faixa):
            return teto - faixa * (teto // 10) if faixa <= 10 else -(faixa - 10) * 30
    return -150


def maxAbsenteismo(row):
    """Retorna 300 para professores/gestores e 450 para os demais cargos."""
    if row["CargoGR"] in ["PROFESSOR EM REGÊNCIA", "GESTOR", "PROFESSOR FORA DE REGÊNCIA"]:
        return 300
    else:
        return 450
