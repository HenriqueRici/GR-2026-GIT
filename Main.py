"""Entrada da GR 2026: carregamento, cálculo e exportação da prévia."""

import os
import time
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

from configuracao import ABAS_GOOGLE, CONSULTAS_SIGABI
from modelos.absenteismo import (
    absenteismoFrequencias,
    absenteismoGeral,
    absenteismoLicencasAfastamentos,
    absenteismoWebPonto,
    maxAbsenteismo,
    pontuacaoAbsenteismo,
)
from modelos.evasaoEscolar import evasao, pontuacaoEvasao
from modelos.grupoEleitos import (
    definirCargoGR,
    proporcaoVinculo,
    tetoGr,
    trataAtribuicao,
    valorGRBase,
)
from modelos.metaAdm import metaAdministrativa
from modelos.metaAprendizagem import metaAprendizagem, pontuacaoMetaAprendizagem
from modelos.pontuacao import pontuacaoGeral


def carregar_bases(api):
    """Lê as bases na ordem original e reúne inclusões, licenças e cargos SEAP.

    Realiza somente leituras remotas. As importações Google são adiadas para
    permitir testar o cálculo sem credenciais ou dependências de integração.
    """
    from google_drive.cliente import lerDadoWebPonto
    from google_sheets.cliente import getGoogleSheets

    bases = {nome: api.menus().consultar(**opcoes) for nome, opcoes in CONSULTAS_SIGABI.items()}
    bases.update({nome: getGoogleSheets(**opcoes) for nome, opcoes in ABAS_GOOGLE.items()})
    bases["baseVacancia"] = pd.concat([bases["baseVacancia"], bases["licencasCalcVacancia"]])
    bases["baseSEAP"] = pd.concat([bases["baseFuncaoConfianca"], bases["baseCargoConfianca"]])
    bases["baseAtribuicao"] = pd.concat([bases["baseAtribuicao"], bases["baseInclusaoManual"]])
    baseWebPonto = lerDadoWebPonto(
        campos=[
            "NOME",
            "LOGIN",
            "MF",
            "DataFrequencia",
            "EntradaManha",
            "SaidaManha",
            "EntradaTarde",
            "SaidaTarde",
            "EntradaNoite",
            "SaidaNoite",
        ],
        column_data=["DataFrequencia"],
        column_data_hora=[
            "EntradaManha",
            "SaidaManha",
            "EntradaTarde",
            "SaidaTarde",
            "EntradaNoite",
            "SaidaNoite",
        ],
        column_int=["LOGIN"],
        column_str=["NOME", "MF"],
    )
    bases["baseWebPonto"] = baseWebPonto
    return bases


def calcular_gr(bases, inicioGR, fimGR):
    """Executa as regras existentes e retorna a prévia por vínculo.

    Mantém formação zerada, como no fluxo original. A etapa de aprendizagem
    também exporta baseTurmasServidor.xlsx, preservando a saída de auditoria.
    As funções de domínio podem alterar as bases recebidas.
    """
    baseAtribuicao = bases["baseAtribuicao"]
    baseHoraAtividade = bases["baseHoraAtividade"]
    baseVacancia = bases["baseVacancia"]
    baseAtribuicaoEmAula = bases["baseAtribuicaoEmAula"]
    baseDE = bases["baseDE"]
    baseSEAP = bases["baseSEAP"]
    baseEvasao = bases["baseEvasao"]
    baseAdm = bases["baseAdm"]
    baseMetaAprendizagemUnidades = bases["baseMetaAprendizagemUnidades"]
    baseMetaAprendizagemTurmas = bases["baseMetaAprendizagemTurmas"]
    baseWebPonto = bases["baseWebPonto"]
    baseLicencasAfastamentos = bases["baseLicencasAfastamentos"]
    baseFrequencias = bases["baseFrequencias"]

    atribuicao = trataAtribuicao(baseAtribuicao, baseHoraAtividade, baseVacancia, inicioGR, fimGR)
    cargoGR = definirCargoGR(atribuicao, baseAtribuicaoEmAula, baseDE, baseSEAP, inicioGR, fimGR)
    teto = tetoGr(cargoGR)
    eleitosGR = pd.merge(cargoGR, teto, how="left", on="CPF")
    eleitosGR = proporcaoVinculo(eleitosGR)
    eleitosGR["ValorGRBaseVinculo"] = eleitosGR.apply(valorGRBase, axis=1)

    eleitosGR = evasao(eleitosGR, baseEvasao)
    eleitosGR["PontuacaoEvasao"] = eleitosGR.apply(pontuacaoEvasao, axis=1)

    eleitosGR = metaAdministrativa(eleitosGR, baseAdm)

    eleitosGR = metaAprendizagem(
        eleitosGR, baseAtribuicaoEmAula, baseMetaAprendizagemUnidades, baseMetaAprendizagemTurmas
    )
    eleitosGR["PontuacaoMetaAprendizagem"] = eleitosGR.apply(pontuacaoMetaAprendizagem, axis=1)

    # temporario
    eleitosGR["CHObrigatoria"] = 0
    eleitosGR["CHObrigatoriaRealizada"] = 0
    eleitosGR["CHEletiva"] = 0
    eleitosGR["PontuacaoFormacao"] = 0

    # eleitosGR = formacaoObrigatoria(eleitosGR, baseFormacaoObgrigatoria, inicioGR, colFormacao='CHObrigatoria')
    # eleitosGR = formacaoObrigatoria(eleitosGR, baseFormacaoObgrigatoria, inicioGR, colFormacao='CHObrigatoriaRealizada')
    # eleitosGR = formacaoEletivaRealizada(eleitosGR, baseFormacaoEletivaRealizada)
    # eleitosGR['PontuacaoFormacao'] = eleitosGR.apply(pontuacaoFormacao, axis=1)

    eleitosGR = absenteismoGeral(
        eleitosGR,
        absenteismoWebPonto(eleitosGR, baseWebPonto),
        absenteismoLicencasAfastamentos(baseLicencasAfastamentos, inicioGR, fimGR),
        absenteismoFrequencias(baseWebPonto, baseFrequencias),
    )

    eleitosGR["PontuacaoAbsenteismo"] = eleitosGR.apply(pontuacaoAbsenteismo, axis=1)
    eleitosGR["MaxAbsenteismo"] = eleitosGR.apply(maxAbsenteismo, axis=1)

    eleitosGR["PontuacaoGeral"] = eleitosGR.apply(pontuacaoGeral, axis=1)
    eleitosGR["EstimativaValorGR"] = (
        eleitosGR["ValorGRBaseVinculo"] / 1000 * eleitosGR["PontuacaoGeral"]
    )
    eleitosGR["EstimativaValorGR"] = eleitosGR["EstimativaValorGR"].clip(lower=0)
    return eleitosGR


def main():
    """Autentica, carrega, calcula e grava PreviaGR.xlsx na pasta original."""
    from sigabi import Sigabi

    login = os.environ.get("SIGABI_LOGIN")
    senha = os.environ.get("SIGABI_SENHA")
    if not login or not senha:
        raise RuntimeError("Configure SIGABI_LOGIN e SIGABI_SENHA antes de executar.")
    print(f"\033[93mInício Execução: {datetime.now():%d/%m/%Y %H:%M:%S}\033[0m")
    inicio = time.perf_counter()
    api = Sigabi(login=login, senha=senha)
    bases = carregar_bases(api)
    print(f"\033[93mBases Carregadas: {datetime.now():%d/%m/%Y %H:%M:%S}\033[0m")
    previa = calcular_gr(bases, pd.Timestamp("2026-02-02"), pd.Timestamp("2026-11-30"))
    pasta = Path.home() / "Desktop" / "GR 2026"
    previa.to_excel(pasta / "PreviaGR.xlsx", index=True)
    duracao = timedelta(seconds=int(time.perf_counter() - inicio))
    print(f"\033[92mExecução concluída em {duracao}\033[0m")
    return previa


if __name__ == "__main__":
    main()
