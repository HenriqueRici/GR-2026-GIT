"""Fluxo integrado sintético, sem bases pessoais ou chamadas remotas."""

import copy
import subprocess
from unittest.mock import patch

import pandas as pd
from conftest import BASELINE, ROOT
from pandas.testing import assert_frame_equal
from test_regressao import comparar

from Main import calcular_gr
from modelos import grupoEleitos, metaAdm


def bases_sinteticas():
    """Inclui gestão por DE, designação e DGA, regência, TAE e civil."""
    inicio, fim = pd.Timestamp("2026-02-02"), pd.Timestamp("2026-11-30")
    linhas = []
    for numero in range(1, 7):
        linhas.append(
            dict(
                Ano=2026,
                DRE="DRE TESTE",
                Municipio="TESTE",
                SerieLotacao=100,
                Lotacao="ESCOLA TESTE",
                TipoLotacao="ESCOLA",
                Nome=f"SERVIDOR {numero}",
                CPF=str(numero),
                DataInicio=inicio,
                DataFinal=fim,
                CodFunc=1,
                Funcao="DIRETOR DESIGNADO/PROFESSOR" if numero == 2 else "PROFESSOR",
                TipoProcesso="TESTE",
                Processo=numero,
                NumFunc=numero,
                NumVinc=1,
                CargoCarreira="TECNICO ADMINISTRATIVO EDUCACIONAL"
                if numero == 5
                else "ANALISTA FUNDIARIO E AGRARIO L 10042"
                if numero == 6
                else "PROFESSOR EDUC. BASICA/30 HORAS",
                TotalCH=20,
                AdmCH=0,
                TipoServidor="PROFESSOR",
                TipoVinculo="EFETIVO",
                AtividadeSeap=60,
            )
        )
    atrib = pd.DataFrame(linhas)
    vac = pd.DataFrame(
        dict(
            Func=[4],
            Vinc=[1],
            Tipo=["LICENÇA"],
            DataInicial=[pd.Timestamp("2026-03-01")],
            DataFinal=[pd.Timestamp("2026-03-10")],
        )
    )
    aulas = pd.DataFrame(
        dict(
            CodigoSEAP=[4],
            VinculoSEAP=[1],
            ChaveTurma=["T1"],
            CH=[30],
            DataInicial=[inicio],
            DataFinal=[fim],
        )
    )
    adm = pd.DataFrame({"LotacaoGR": ["100"], "Municipio": ["TESTE"]})
    for col, _ in metaAdm.EIXOS.values():
        adm[col] = 75.0
    web = pd.DataFrame(
        {
            "LOGIN": list(range(1, 7)),
            "DataFrequencia": [pd.Timestamp("2026-04-01")] * 6,
            "MF": ["14 - DOAÇÃO DE SANGUE"] * 6,
        }
    )
    for turno in ["Manha", "Tarde", "Noite"]:
        web["Entrada" + turno] = pd.NaT
        web["Saida" + turno] = pd.NaT
    lic = vac.rename(columns={"Func": "Func"}).assign(Tipo="4020 - LICENÇA")
    freq = lic.assign(CPF=4.0)
    return dict(
        baseAtribuicao=atrib,
        baseHoraAtividade=pd.DataFrame(
            {"Func": [4], "Vinc": [1], "Tipo": ["2002 - HORA ATIVIDADE"]}
        ),
        baseVacancia=vac,
        baseAtribuicaoEmAula=aulas,
        baseDE=pd.DataFrame({"Func": [1], "DataInicial": [inicio], "DataFinal": [fim]}),
        baseSEAP=pd.DataFrame(
            {"numfunc": [3], "descr_cargo": ["DGA-1"], "dtini": [inicio], "dtfim": [fim]}
        ),
        baseEvasao=pd.DataFrame({"LotacaoGR": ["100"], "Frequencia": [0.91]}),
        baseAdm=adm,
        baseMetaAprendizagemUnidades=pd.DataFrame(
            {
                "LotacaoGR": ["100"],
                "NotaInicialAprendizagem": [4.0],
                "MetaAprendizagem": [5.0],
                "NotaFinalAprendizagem": [6.0],
            }
        ),
        baseMetaAprendizagemTurmas=pd.DataFrame(
            {
                "ChaveTurma": ["T1"],
                "NotaInicialAprendizagem": [4.0],
                "MetaAprendizagem": [5.0],
                "NotaFinalAprendizagem": [6.0],
            }
        ),
        baseWebPonto=web,
        baseLicencasAfastamentos=lic,
        baseFrequencias=freq,
    )


def test_atribuicao_classificacao_proporcao(legado):
    antigo = legado("modelos/grupoEleitos.py")
    b = bases_sinteticas()
    datas = (pd.Timestamp("2026-02-02"), pd.Timestamp("2026-11-30"))
    comparar(
        antigo.trataAtribuicao,
        grupoEleitos.trataAtribuicao,
        b["baseAtribuicao"],
        b["baseHoraAtividade"],
        b["baseVacancia"],
        *datas,
    )
    atribuicao = antigo.trataAtribuicao(
        b["baseAtribuicao"], b["baseHoraAtividade"], b["baseVacancia"], *datas
    )
    comparar(
        antigo.definirCargoGR,
        grupoEleitos.definirCargoGR,
        atribuicao,
        b["baseAtribuicaoEmAula"],
        b["baseDE"],
        b["baseSEAP"],
        *datas,
    )
    cargo = antigo.definirCargoGR(
        atribuicao, b["baseAtribuicaoEmAula"], b["baseDE"], b["baseSEAP"], *datas
    )
    cargo = cargo.merge(antigo.tetoGr(cargo), on="CPF", how="left")
    comparar(antigo.proporcaoVinculo, grupoEleitos.proporcaoVinculo, cargo)


def test_fluxo_com_adaptador_do_erro_legado(legado):
    """Compara o fluxo com a única adaptação de aliases necessária no original.

    O original falhava no WebPonto após proporcaoVinculo renomear NumFunc/NumVinc.
    O adaptador abaixo explicita essa correção; nenhuma regra de cálculo é trocada.
    """
    b = bases_sinteticas()
    inicio = pd.Timestamp("2026-02-02")
    fim = pd.Timestamp("2026-11-30")
    ns = {"pd": pd, "inicioGR": inicio, "fimGR": fim, **copy.deepcopy(b)}
    for modulo in [
        "grupoEleitos",
        "evasaoEscolar",
        "metaAdm",
        "metaAprendizagem",
        "absenteismo",
        "formacao",
        "pontuacao",
    ]:
        ns.update(
            {k: v for k, v in vars(legado(f"modelos/{modulo}.py")).items() if not k.startswith("_")}
        )
    original_web = ns["absenteismoWebPonto"]
    ns["absenteismoWebPonto"] = lambda base, web: original_web(
        base.rename(columns={"Func": "NumFunc", "Vinc": "NumVinc"}), web
    )
    source = subprocess.check_output(["git", "show", f"{BASELINE}:Main.py"], cwd=ROOT, text=True)
    trecho = source[
        source.index("atribuicao = trataAtribuicao") : source.index("eleitosGR.to_excel")
    ]
    saidas_antigas = []
    saidas_novas = []

    def capturar(lista):
        """Captura os DataFrames de auditoria exportados pelo cálculo."""
        return lambda frame, *a, **k: lista.append(frame.copy(deep=True))

    with patch.object(pd.DataFrame, "to_excel", capturar(saidas_antigas)):
        exec(compile(trecho, "fluxo_legado", "exec"), ns)
    with patch.object(pd.DataFrame, "to_excel", capturar(saidas_novas)):
        atual = calcular_gr(copy.deepcopy(b), inicio, fim)
    assert_frame_equal(ns["eleitosGR"], atual, check_exact=True)
    assert len(saidas_antigas) == len(saidas_novas) == 1
    assert_frame_equal(saidas_antigas[0], saidas_novas[0], check_exact=True)
