"""Metas de aprendizagem por turma, unidade e vínculo."""

from datetime import datetime
from pathlib import Path

import pandas as pd

PONTOS_APRENDIZAGEM = {
    "TAE/AAE": (15, 30, 40, 50),
    "PROFESSOR EM REGÊNCIA": (180, 360, 405, 450),
    "PROFESSOR FORA DE REGÊNCIA": (180, 360, 405, 450),
    "GESTOR": (90, 180, 200, 225),
    "CIVIS E MILITARES LOTADOS NA SEDUC": (100, 200, 225, 300),
}


def metaAprendizagem(base, baseTurmas, baseMetaAprendizagemUnidades, baseMetaAprendizagemTurmas):
    """Pondera notas por dias × CH para regência e usa notas da unidade nos demais cargos.

    Exporta baseTurmasServidor.xlsx antes de ponderar e mantém notas com duas casas."""
    desktop_path = Path.home() / "Desktop" / "GR 2026"

    profRegencia = base[base["CargoGR"] == "PROFESSOR EM REGÊNCIA"].copy()
    profRegencia = profRegencia[["LotacaoGR", "Func", "Vinc"]]
    demaisCargos = base[base["CargoGR"] != "PROFESSOR EM REGÊNCIA"].copy()
    demaisCargos = demaisCargos[["LotacaoGR", "Func", "Vinc"]]

    baseTurmas = baseTurmas[baseTurmas["CodigoSEAP"].notna()]
    baseTurmas = baseTurmas[
        ["CodigoSEAP", "VinculoSEAP", "ChaveTurma", "CH", "DataInicial", "DataFinal"]
    ]
    baseTurmas = baseTurmas.rename(columns={"CodigoSEAP": "Func", "VinculoSEAP": "Vinc"})
    baseTurmas = (
        baseTurmas.groupby(["Func", "Vinc", "ChaveTurma", "DataInicial", "DataFinal"])
        .agg(CH=("CH", "sum"))
        .reset_index()
    )
    baseTurmas["Dias"] = (baseTurmas["DataFinal"] - baseTurmas["DataInicial"]).dt.days + 1

    baseTurmas["Peso"] = baseTurmas["Dias"] * baseTurmas["CH"]
    somaPeso = baseTurmas.groupby(["Func", "Vinc"]).agg(PesoTotal=("Peso", "sum")).reset_index()
    baseTurmas = pd.merge(baseTurmas, somaPeso, how="left", on=["Func", "Vinc"])
    baseTurmas["PercentualMetaAprendizagem"] = baseTurmas["Peso"] / baseTurmas["PesoTotal"]
    baseTurmas = (
        baseTurmas.groupby(["Func", "Vinc", "ChaveTurma"])
        .agg(PercentualMetaAprendizagem=("PercentualMetaAprendizagem", "sum"))
        .reset_index()
    )
    baseTurmas["ChaveTurma"] = baseTurmas["ChaveTurma"].str.replace('"', "", regex=False)

    baseTurmas = pd.merge(baseTurmas, baseMetaAprendizagemTurmas, how="left", on="ChaveTurma")

    colunas = ["NotaInicialAprendizagem", "MetaAprendizagem", "NotaFinalAprendizagem"]
    baseTurmas[colunas] = baseTurmas[colunas].fillna(0)
    baseTurmas.to_excel(desktop_path / "baseTurmasServidor.xlsx", index=False)

    baseTurmas["NotaInicialAprendizagem"] = (
        baseTurmas["NotaInicialAprendizagem"] * baseTurmas["PercentualMetaAprendizagem"]
    )
    baseTurmas["MetaAprendizagem"] = (
        baseTurmas["MetaAprendizagem"] * baseTurmas["PercentualMetaAprendizagem"]
    )
    baseTurmas["NotaFinalAprendizagem"] = (
        baseTurmas["NotaFinalAprendizagem"] * baseTurmas["PercentualMetaAprendizagem"]
    )
    baseTurmas = (
        baseTurmas.groupby(["Func", "Vinc"])
        .agg(
            NotaInicialAprendizagem=("NotaInicialAprendizagem", "sum"),
            MetaAprendizagem=("MetaAprendizagem", "sum"),
            NotaFinalAprendizagem=("NotaFinalAprendizagem", "sum"),
        )
        .reset_index()
    )

    baseTurmas["NotaInicialAprendizagem"] = baseTurmas["NotaInicialAprendizagem"].round(2)
    baseTurmas["MetaAprendizagem"] = baseTurmas["MetaAprendizagem"].round(2)
    baseTurmas["NotaFinalAprendizagem"] = baseTurmas["NotaFinalAprendizagem"].round(2)

    profRegencia = pd.merge(profRegencia, baseTurmas, how="left", on=["Func", "Vinc"])

    demaisCargos["LotacaoGR"] = demaisCargos["LotacaoGR"].astype(str)
    baseMetaAprendizagemUnidades["LotacaoGR"] = baseMetaAprendizagemUnidades["LotacaoGR"].astype(
        str
    )

    demaisCargos = pd.merge(
        demaisCargos, baseMetaAprendizagemUnidades, how="left", on=["LotacaoGR"]
    )
    metaPronta = pd.concat([demaisCargos, profRegencia])
    metaPronta = metaPronta.drop_duplicates(subset=["LotacaoGR", "Func", "Vinc"])
    base = pd.merge(base, metaPronta, how="left", on=["LotacaoGR", "Func", "Vinc"])

    base = base[
        [
            "Municipio",
            "LotacaoGR",
            "DescricaoLotacaoGR",
            "Nome",
            "CPF",
            "Func",
            "Vinc",
            "TipoVinculo",
            "CargoCarreira",
            "CargoGR",
            "DataInicio",
            "DataFinal",
            "CH",
            "PercentualGRVinculo",
            "ValorGRBaseVinculo",
            "Frequencia",
            "PontuacaoEvasao",
            "Meta administrativa - Alimentação Escolar",
            "Meta administrativa - Limpeza e Organização dos Ambientes Escolares",
            "Meta administrativa - Patrimônio Mobiliário e Imobiliário Escolar",
            "Meta administrativa - Manutenção e Conservação da Infraestrutura Escolar",
            "Meta administrativa - Gestão",
            "Meta administrativa - Resultados",
            "PontuacaoEixoPatrimonio",
            "PontuacaoEixoInfraestruturaEscolar",
            "PontuacaoEixoLimpeza",
            "PontuacaoEixoAlimentacao",
            "PontuacaoEixoResultados",
            "PontuacaoEixoGestao",
            "PontuacaoMetaAdiministrativa",
            "NotaInicialAprendizagem",
            "MetaAprendizagem",
            "NotaFinalAprendizagem",
        ]
    ]

    print(
        f"\033[92mMeta Aprendizagem pronto, concluído em "
        f"{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\033[0m"
    )
    return base


def pontuacaoMetaAprendizagem(row):
    """Aplica a faixa de evolução da aprendizagem e os pontos do cargo.

    Mantém a ordem de precedência original, inclusive quando meta e nota são zero.
    """
    pontos = PONTOS_APRENDIZAGEM.get(row["CargoGR"])
    if pontos is None:
        return 0
    inicial, final, meta = (
        row["NotaInicialAprendizagem"],
        row["NotaFinalAprendizagem"],
        row["MetaAprendizagem"],
    )
    if inicial <= final < meta:
        return pontos[0]
    if final == meta:
        return pontos[1]
    if meta < final <= meta * 1.2:
        return pontos[2]
    if final > meta * 1.2:
        return pontos[3]
    return 0
