"""Pontuação dos seis eixos administrativos por cargo."""

from datetime import datetime

import numpy as np
import pandas as pd


def metaAdministrativa(base, baseAdm):
    """Anexa metas, substitui nulos por zero e soma os seis eixos com arredondamento para cima."""
    base = pd.merge(base, baseAdm, on="LotacaoGR", how="left")

    colunas_metas = [
        "Meta administrativa - Patrimônio Mobiliário e Imobiliário Escolar",
        "Meta administrativa - Manutenção e Conservação da Infraestrutura Escolar",
        "Meta administrativa - Limpeza e Organização dos Ambientes Escolares",
        "Meta administrativa - Alimentação Escolar",
        "Meta administrativa - Resultados",
        "Meta administrativa - Gestão",
    ]

    base[colunas_metas] = base[colunas_metas].fillna(0)

    base["PontuacaoEixoPatrimonio"] = _pontuar_coluna(base, "pontosEixoPatrimonio")
    base["PontuacaoEixoInfraestruturaEscolar"] = _pontuar_coluna(
        base, "pontosEixoInfraestruturaEscolar"
    )
    base["PontuacaoEixoLimpeza"] = _pontuar_coluna(base, "pontosEixoLimpeza")
    base["PontuacaoEixoAlimentacao"] = _pontuar_coluna(base, "pontosEixoAlimentacao")
    base["PontuacaoEixoResultados"] = _pontuar_coluna(base, "pontosEixoResultados")
    base["PontuacaoEixoGestao"] = _pontuar_coluna(base, "pontosEixoGestao")

    colunas_pontuacao = [
        "PontuacaoEixoPatrimonio",
        "PontuacaoEixoInfraestruturaEscolar",
        "PontuacaoEixoLimpeza",
        "PontuacaoEixoAlimentacao",
        "PontuacaoEixoResultados",
        "PontuacaoEixoGestao",
    ]

    base["PontuacaoMetaAdiministrativa"] = np.ceil(base[colunas_pontuacao].sum(axis=1))

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
        ]
    ]

    print(
        f"\033[92mMeta Administrativa pronto, concluído em "
        f"{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\033[0m"
    )
    return base


def pontosEixoPatrimonio(row):
    """Calcula o eixo Patrimônio Mobiliário e Imobiliário Escolar para uma linha."""
    return _pontos_eixo(row, "pontosEixoPatrimonio")


def pontosEixoInfraestruturaEscolar(row):
    """Calcula o eixo Manutenção e Conservação da Infraestrutura Escolar para uma linha."""
    return _pontos_eixo(row, "pontosEixoInfraestruturaEscolar")


def pontosEixoLimpeza(row):
    """Calcula o eixo Limpeza e Organização dos Ambientes Escolares para uma linha."""
    return _pontos_eixo(row, "pontosEixoLimpeza")


def pontosEixoAlimentacao(row):
    """Calcula o eixo Alimentação Escolar para uma linha."""
    return _pontos_eixo(row, "pontosEixoAlimentacao")


def pontosEixoResultados(row):
    """Calcula o eixo Resultados para uma linha."""
    return _pontos_eixo(row, "pontosEixoResultados")


def pontosEixoGestao(row):
    """Calcula o eixo Gestão para uma linha."""
    return _pontos_eixo(row, "pontosEixoGestao")


EIXOS = {
    "pontosEixoPatrimonio": (
        "Meta administrativa - Patrimônio Mobiliário e Imobiliário Escolar",
        {"GESTOR": (18.75, 9.375, 2), "TAE/AAE": (18.75, 15.625, 2)},
    ),
    "pontosEixoInfraestruturaEscolar": (
        "Meta administrativa - Manutenção e Conservação da Infraestrutura Escolar",
        {"GESTOR": (18.75, 9.375, 2), "TAE/AAE": (18.75, 15.625, 2)},
    ),
    "pontosEixoLimpeza": (
        "Meta administrativa - Limpeza e Organização dos Ambientes Escolares",
        {"GESTOR": (18.75, 9.375, 1), "TAE/AAE": (18.75, 15.625, 1)},
    ),
    "pontosEixoAlimentacao": (
        "Meta administrativa - Alimentação Escolar",
        {"GESTOR": (18.75, 9.375, 1), "TAE/AAE": (18.75, 15.625, 1)},
    ),
    "pontosEixoResultados": (
        "Meta administrativa - Resultados",
        {"GESTOR": (75, 7.031, 1), "TAE/AAE": (37.5, 3.90625, 1)},
    ),
    "pontosEixoGestao": ("Meta administrativa - Gestão", {"GESTOR": (12.5, 7.031, 1)}),
}


def _pontos_eixo(row, eixo):
    """Mantém divisão inteira e ordem de operações da regra escalar original."""
    coluna, regras = EIXOS[eixo]
    regra = regras.get(row["CargoGR"])
    if regra is None:
        return 0
    tamanho, valor, divisor = regra
    return int(row[coluna] // tamanho) * valor / divisor


def _pontuar_coluna(base, eixo):
    """Calcula cada cargo em bloco, sem executar Python para cada servidor."""
    coluna, regras = EIXOS[eixo]
    aplicaveis = base["CargoGR"].isin(regras)
    pontos = pd.Series(0, index=base.index, dtype=float if aplicaveis.any() else int)
    for cargo, (tamanho, valor, divisor) in regras.items():
        mascara = base["CargoGR"].eq(cargo).fillna(False)
        faixas = (base.loc[mascara, coluna] // tamanho).astype("int64")
        pontos.loc[mascara] = faixas * valor / divisor
    return pontos
