"""Regressões de pontuação, intervalos, distribuição e tipos de dados."""

import ast
import copy
import importlib
import inspect
import itertools

import numpy as np
import pandas as pd
import pytest
from pandas.testing import assert_frame_equal, assert_series_equal

from modelos import absenteismo, formacao, grupoEleitos, metaAdm, metaAprendizagem

CARGOS = [
    "GESTOR",
    "TAE/AAE",
    "PROFESSOR EM REGÊNCIA",
    "PROFESSOR FORA DE REGÊNCIA",
    "CIVIS E MILITARES LOTADOS NA SEDUC",
    "DESCONHECIDO",
]


def comparar(antiga, nova, *args, **kwargs):
    """Compara retorno e mutações, incluindo tipos, ordem e índices."""
    a, b = copy.deepcopy(args), copy.deepcopy(args)
    esperado, obtido = antiga(*a, **kwargs), nova(*b, **kwargs)
    if isinstance(esperado, pd.DataFrame):
        assert_frame_equal(esperado, obtido, check_exact=True)
    else:
        assert esperado == obtido
    for antes, depois in zip(a, b):
        if isinstance(antes, pd.DataFrame):
            assert_frame_equal(antes, depois, check_exact=True)


@pytest.mark.parametrize(
    "modulo,funcoes",
    [
        ("absenteismo", ["pontuacaoAbsenteismo", "maxAbsenteismo"]),
        ("evasaoEscolar", ["pontuacaoEvasao"]),
        ("formacao", ["pontuacaoFormacao"]),
        ("metaAprendizagem", ["pontuacaoMetaAprendizagem"]),
        ("pontuacao", ["pontuacaoGeral", "valorFinalGR"]),
    ],
)
def test_regras_escalares(legado, modulo, funcoes):
    antigo = legado(f"modelos/{modulo}.py")
    novo = importlib.import_module(f"modelos.{modulo}")
    for cargo, v in itertools.product(CARGOS, list(range(-2, 42)) + [0.5, 1.5, np.nan]):
        row = dict(
            CargoGR=cargo,
            DiasAbsenteismo=v,
            Frequencia=v / 40,
            CHObrigatoria=20,
            CHObrigatoriaRealizada=v,
            CHEletiva=v * 6,
            NotaInicialAprendizagem=2,
            NotaFinalAprendizagem=v / 5,
            MetaAprendizagem=5,
            PontuacaoAbsenteismo=300,
            PontuacaoEvasao=100,
            PontuacaoFormacao=150,
            PontuacaoMetaAprendizagem=225,
            PontuacaoMetaAdiministrativa=225,
            PontuacaoGeral=1000,
            ValorGRBaseVinculo=10000,
        )
        for nome in funcoes:
            assert getattr(novo, nome)(row) == getattr(antigo, nome)(row)


def test_limites(legado):
    antigo = legado("modelos/formacao.py")
    for obrigatoria, horas in itertools.product(
        [0, 19, 20, 21], [99, 100, 130, 130.5, 131, 180, 180.5, 181, 199, 199.5, 200, 201]
    ):
        row = dict(CHObrigatoria=20, CHObrigatoriaRealizada=obrigatoria, CHEletiva=horas)
        assert formacao.pontuacaoFormacao(row) == antigo.pontuacaoFormacao(row)
    antigo = legado("modelos/metaAprendizagem.py")
    for cargo, inicial, meta, final in itertools.product(
        CARGOS, [0, 4, 6], [0, 5], [0, 3, 4, 4.999, 5, 5.001, 6, 6.001, np.nan]
    ):
        row = dict(
            CargoGR=cargo,
            NotaInicialAprendizagem=inicial,
            MetaAprendizagem=meta,
            NotaFinalAprendizagem=final,
        )
        assert metaAprendizagem.pontuacaoMetaAprendizagem(row) == antigo.pontuacaoMetaAprendizagem(
            row
        )


def test_valores_base(legado):
    antigo = legado("modelos/grupoEleitos.py")
    nomes = [
        n.value
        for n in ast.walk(ast.parse(inspect.getsource(grupoEleitos.valorGRBase)))
        if isinstance(n, ast.Constant) and isinstance(n.value, str)
    ]
    for cargo, carreira, proporcao in itertools.product(CARGOS, nomes, [0, 0.123456789, 1, 1.25]):
        row = dict(CargoGR=cargo, CargoCarreira=carreira, PercentualGRVinculo=proporcao)
        assert grupoEleitos.valorGRBase(row) == antigo.valorGRBase(row)


def test_eixos_vetorizados(legado):
    antigo = legado("modelos/metaAdm.py")
    for nome, (coluna, _) in metaAdm.EIXOS.items():
        base = pd.DataFrame(
            list(
                itertools.product(
                    CARGOS, [-1, 0, 0.1, 12.49, 12.5, 18.74, 18.75, 37.5, 75, 100, 599, 600, 900]
                )
            ),
            columns=["CargoGR", coluna],
        )
        esperado = base.apply(getattr(antigo, nome), axis=1)
        assert_series_equal(metaAdm._pontuar_coluna(base, nome), esperado, check_exact=True)
        assert_series_equal(base.apply(getattr(metaAdm, nome), axis=1), esperado, check_exact=True)


def test_teto_e_periodos(legado):
    antigo = legado("modelos/grupoEleitos.py")
    rng = np.random.default_rng(42)
    inicio = pd.Timestamp("2026-02-02")
    base = pd.DataFrame(
        {
            "CPF": rng.integers(1, 12, 150).astype(float),
            "DataInicio": inicio + pd.to_timedelta(rng.integers(0, 80, 150), unit="D"),
            "DataFinal": inicio + pd.to_timedelta(rng.integers(80, 302, 150), unit="D"),
            "CH": rng.choice([10.0, 20.0, 30.0, 40.0], 150),
        }
    )
    comparar(antigo.tetoGr, grupoEleitos.tetoGr, base)
    comparar(
        antigo.calcular_periodo_unico,
        grupoEleitos.calcular_periodo_unico,
        base,
        col_data_ini="DataInicio",
        col_data_fim="DataFinal",
    )
    vac = base.rename(columns={"CPF": "Func", "DataInicio": "DataInicial"}).assign(
        Vinc=1, Tipo="LICENÇA"
    )
    comparar(
        antigo.trataVacancia,
        grupoEleitos.trataVacancia,
        vac,
        inicio,
        inicio + pd.Timedelta(days=301),
    )


def test_formacao(legado):
    antigo = legado("modelos/formacao.py")
    vinc = pd.DataFrame(
        {
            "CPF": [1, 1, 2, 3],
            "NumVinc": [1, 2, 1, 1],
            "CH": [20, 10, 30, 30],
            "CargoGR": [CARGOS[2]] * 3 + [CARGOS[0]],
            "DataInicio": pd.to_datetime(["2026-02-01"] * 4),
            "DataFinal": pd.to_datetime(["2026-11-30"] * 4),
        }
    )
    cursos = pd.DataFrame(
        {
            "CPF": ["1", "2", "4"],
            "InicioPeriodo": pd.to_datetime(["2026-01-01", "2026-05-01", "2026-06-01"]),
            "FimPeriodo": pd.to_datetime(["2026-03-01", "2026-06-01", "2026-08-01"]),
            "CHObrigatoria": [30, 20, 10],
        }
    )
    comparar(
        antigo.formacaoObrigatoria,
        formacao.formacaoObrigatoria,
        vinc,
        cursos,
        pd.Timestamp("2026-02-02"),
        colFormacao="CHObrigatoria",
    )
    comparar(
        antigo.formacaoEletivaRealizada,
        formacao.formacaoEletivaRealizada,
        vinc,
        pd.DataFrame({"CPF": ["1", "1", "2"], "CHEletiva": [20, 30, 50]}),
    )


def test_absenteismo(legado):
    antigo = legado("modelos/absenteismo.py")
    base = pd.DataFrame(
        {
            "Func": [1, 1, 2, 2, 3],
            "Vinc": [1, 1, 1, 2, 1],
            "DataInicio": pd.to_datetime(["2026-02-02"] * 5),
            "DataFinal": pd.to_datetime(["2026-11-30"] * 5),
        }
    )
    lic = pd.DataFrame(
        {
            "Func": [1, 1, 1, 2, 2],
            "Vinc": [1, 1, 1, 1, 2],
            "Tipo": [
                "4020 - LICENÇA",
                "4020 - LICENÇA",
                "01 - ATESTADO DE COMPARECIMENTO CONSULTA OU AFASTAMENTO MÉDICO ATÉ 03 DIAS",
                "30010 - FALTA",
                "30010 - FALTA",
            ],
            "DataInicial": pd.to_datetime(
                ["2026-03-01", "2026-03-04", "2026-03-02", "2026-04-01", "2026-04-01"]
            ),
            "DataFinal": pd.to_datetime(
                ["2026-03-05", "2026-03-06", "2026-03-02", "2026-04-02", "2026-04-03"]
            ),
        }
    )
    comparar(
        antigo.absenteismoGeral, absenteismo.absenteismoGeral, base, lic.iloc[:0], lic, lic.iloc[:0]
    )
    comparar(
        antigo.absenteismoLicencasAfastamentos,
        absenteismo.absenteismoLicencasAfastamentos,
        lic,
        pd.Timestamp("2026-03-03"),
        pd.Timestamp("2026-04-02"),
    )


def test_webponto_aliases(legado):
    antigo = legado("modelos/absenteismo.py")
    base = pd.DataFrame(
        {
            "CPF": [1],
            "NumFunc": [1],
            "NumVinc": [1],
            "DataInicio": [pd.Timestamp("2026-02-02")],
            "DataFinal": [pd.Timestamp("2026-11-30")],
        }
    )
    web = pd.DataFrame(
        {
            "LOGIN": [1],
            "DataFrequencia": [pd.Timestamp("2026-04-01")],
            "MF": ["14 - DOAÇÃO DE SANGUE"],
        }
    )
    for turno in ["Manha", "Tarde", "Noite"]:
        web["Entrada" + turno] = pd.NaT
        web["Saida" + turno] = pd.NaT
    esperado = antigo.absenteismoWebPonto(base.copy(), web.copy())
    assert_frame_equal(
        absenteismo.absenteismoWebPonto(
            base.rename(columns={"NumFunc": "Func", "NumVinc": "Vinc"}), web.copy()
        ),
        esperado,
    )
    comparar(antigo.absenteismoWebPonto, absenteismo.absenteismoWebPonto, base, web)


def test_meta_administrativa_completa(legado):
    antigo = legado("modelos/metaAdm.py")
    tree = ast.parse(inspect.getsource(metaAdm.metaAdministrativa))
    selecao = next(
        n.value.slice
        for n in ast.walk(tree)
        if isinstance(n, ast.Assign)
        and isinstance(n.value, ast.Subscript)
        and isinstance(n.value.slice, ast.List)
    )
    colunas = ast.literal_eval(selecao)
    base = pd.DataFrame(
        {
            c: [0] * len(CARGOS)
            for c in colunas
            if not c.startswith("Meta administrativa")
            and not c.startswith("PontuacaoEixo")
            and c != "PontuacaoMetaAdiministrativa"
        }
    )
    base["CargoGR"] = CARGOS
    base["LotacaoGR"] = [str(i) for i in range(len(CARGOS))]
    adm = pd.DataFrame({"LotacaoGR": base["LotacaoGR"]})
    for coluna, _ in metaAdm.EIXOS.values():
        adm[coluna] = pd.Series([75, 37.5, None, 0, 100, 600], dtype="Float64")
    comparar(antigo.metaAdministrativa, metaAdm.metaAdministrativa, base, adm)
