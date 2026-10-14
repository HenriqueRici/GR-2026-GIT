"""Contratos de integração usando respostas simuladas, sem tráfego externo."""

import ast
import importlib
import subprocess
from unittest.mock import Mock, patch

import pandas as pd
from conftest import BASELINE, ROOT
from pandas.testing import assert_frame_equal

from configuracao import ABAS_GOOGLE, CONSULTAS_SIGABI
from modelos.carregamentoDeDados import carregarArquivo, carregarPastaArquivos


def test_consultas_preservadas():
    """Verifica todos os filtros, campos, tipos e ordem contra o Main original."""
    source = subprocess.check_output(["git", "show", f"{BASELINE}:Main.py"], cwd=ROOT, text=True)
    consultas = {}
    abas = {}
    for n in ast.parse(source).body:
        if not isinstance(n, ast.Assign) or not isinstance(n.value, ast.Call):
            continue
        f = n.value.func
        if isinstance(f, ast.Attribute) and f.attr == "consultar":
            consultas[n.targets[0].id] = {
                k.arg: ast.literal_eval(k.value) for k in n.value.keywords
            }
        elif isinstance(f, ast.Name) and f.id == "getGoogleSheets":
            abas[n.targets[0].id] = {k.arg: ast.literal_eval(k.value) for k in n.value.keywords}
    assert list(consultas.items()) == list(CONSULTAS_SIGABI.items())
    assert list(abas.items()) == list(ABAS_GOOGLE.items())


def test_importar_nao_autentica():
    """Importar Main/Sheets não deve iniciar o processamento ou exigir a chave."""
    import google_sheets.cliente as sheets
    import Main

    with patch("requests.post") as post, patch("gspread.authorize") as auth:
        importlib.reload(sheets)
        importlib.reload(Main)
    post.assert_not_called()
    auth.assert_not_called()


def test_sheets_conversoes_e_cache(legado):
    import google_sheets.cliente as novo

    antigo = legado("google_sheets/cliente.py")
    dados = [
        ["data", "inteiro", "decimal", "texto"],
        ["01/02/2026 12:34:56", "1", " 0,85 ", " a "],
        ["02/02/2026", "", "erro", ""],
        ["invalida", "2", "1.25", "x"],
    ]
    planilha = Mock()
    planilha.worksheet.return_value.get_all_values.return_value = dados
    antigo.planilha = planilha
    opcoes = dict(
        column_data=["data", "ausente"],
        column_int=["inteiro"],
        column_float=["decimal"],
        column_str=["texto"],
    )
    with patch.object(novo, "planilha", planilha):
        assert_frame_equal(
            antigo.getGoogleSheets("TESTE", **opcoes),
            novo.getGoogleSheets("TESTE", **opcoes),
            check_exact=True,
        )
    with (
        patch.object(novo, "planilha", None),
        patch.object(novo.Credentials, "from_service_account_file"),
        patch.object(novo.gspread, "authorize") as auth,
    ):
        novo.obter_planilha()
        novo.obter_planilha()
        assert auth.call_count == 1


def test_sigabi_autenticacao_renovacao(legado):
    from sigabi.cliente import Sigabi

    antigo = legado("sigabi/cliente.py")
    for classe in [antigo.Sigabi, Sigabi]:
        respostas = [
            Mock(status_code=200),
            Mock(status_code=200),
            Mock(status_code=401),
            Mock(status_code=200),
        ]
        respostas[0].json.return_value = {"access_token": "teste-a", "refresh_token": "teste-r"}
        respostas[1].json.return_value = {"access_token": "teste-b"}
        respostas[3].json.return_value = {"access_token": "teste-c", "refresh_token": "teste-s"}
        with patch("requests.post", side_effect=respostas) as post:
            cliente = classe("usuario-teste", "senha-ficticia")
            cliente.renovar_token()
            assert cliente.access_token == "teste-b" and cliente.refresh_token == "teste-r"
            cliente.renovar_token()
            assert cliente.headers["Authorization"] == "Bearer teste-c"
            assert post.call_count == 4


def test_menus_paginacao_e_tipos(legado):
    from sigabi.menus import Menus

    antigo = legado("sigabi/menus.py")
    cliente = Mock(base_url="https://exemplo.invalid", headers={})
    filtros = [
        {"field": "id", "operator": "in", "value": "1, 2, "},
        {"field": "nome", "operator": "eq", "value": "a"},
    ]
    resultados = []
    chamadas = []
    for classe in [antigo.Menus, Menus]:
        respostas = [Mock(status_code=200), Mock(status_code=200)]
        respostas[0].json.return_value = {
            "data": [{"id": "1", "data": "01/02/2026", "texto": "a"}],
            "pagination": {"total_pages": 2},
        }
        respostas[1].json.return_value = {
            "data": [
                {"id": "2", "data": "02/02/2026 12:00:00", "texto": "b"},
                {"id": "", "data": "invalida", "texto": ""},
            ],
            "pagination": {"total_pages": 2},
        }
        with patch("requests.post", side_effect=respostas) as post, patch("time.sleep"):
            resultado = classe(cliente).consultar(
                "teste",
                296,
                filtros=filtros,
                column_data=["data"],
                column_int=["id"],
                column_str=["texto"],
                exclude_empty=["id"],
            )
            resultados.append(resultado)
            chamadas.append(post.call_args_list)
    assert_frame_equal(*resultados, check_exact=True)
    assert chamadas[0] == chamadas[1]
    assert filtros[0]["value"] == "1, 2, "


def test_drive_conversoes(legado):
    import google_drive.cliente as novo

    antigo = legado("google_drive/cliente.py")
    tabela = pd.DataFrame(
        {
            "data": ["01/02/2026 00:00:00", "02/02/2026"],
            "hora": ["08:30:00", "invalida"],
            "inteiro": ["1", ""],
            "decimal": [".5", "x"],
            "texto": ["a", None],
        }
    )
    resultados = []
    for modulo in [antigo, novo]:
        drive = Mock()
        drive.files.return_value.list.return_value.execute.return_value = {
            "files": [{"id": "teste", "name": "teste.xlsx"}]
        }
        with (
            patch.object(modulo.service_account.Credentials, "from_service_account_file"),
            patch.object(modulo, "build", return_value=drive),
            patch.object(modulo, "MediaIoBaseDownload") as download,
            patch.object(modulo.pd, "read_excel", return_value=tabela.copy()),
        ):
            download.return_value.next_chunk.return_value = (None, True)
            resultados.append(
                modulo.lerDadoWebPonto(
                    column_data=["data"],
                    column_data_hora=["hora"],
                    column_int=["inteiro"],
                    column_float=["decimal"],
                    column_str=["texto"],
                    campos=list(tabela.columns),
                )
            )
    assert_frame_equal(*resultados, check_exact=True)


def test_leitores_locais_e_formacao(legado, tmp_path):
    import modelos.carregamentoDeDados as novo

    antigo = legado("modelos/carregamentoDeDados.py")
    tabela = pd.DataFrame(
        {"id": [1, 2, 2], "data": ["01/02/2026 00:00:00"] * 3, "texto": ["a", "b", "b"]}
    )
    arquivo = tmp_path / "base.csv"
    tabela.to_csv(arquivo, sep=";", index=False)
    opts = dict(
        column_data=["data"],
        drop_duplicates_by=["id"],
        filters={"id": [2]},
        exclude_empty=["texto"],
    )
    assert_frame_equal(antigo.carregarArquivo(arquivo, **opts), carregarArquivo(arquivo, **opts))
    tabela.to_excel(tmp_path / "base.xlsx", index=False)
    assert_frame_equal(antigo.carregarPastaArquivos(tmp_path), carregarPastaArquivos(tmp_path))
    for nome, dados in [
        ("carregaAPIFormacaoEletiva", [["CPF", "CH"], ["1", "25"], ["2", "erro"]]),
        (
            "carregaAPIFormacaoObrigatoria",
            [
                ["CPF", "InicioExclusivo", "FimInclusivo", "CHNecessaria", "CHCumprida"],
                ["1", "2026-02-01", "2026-03-01", "20", "10"],
            ],
        ),
    ]:
        resposta = Mock()
        resposta.json.return_value = dados
        with patch("requests.get", return_value=resposta):
            assert_frame_equal(
                getattr(antigo, nome)("https://exemplo.invalid"),
                getattr(novo, nome)("https://exemplo.invalid"),
            )


def test_pagamento_exportado(legado):
    import modelos.tratamentoPagamento as novo

    antigo = legado("modelos/tratamentoPagamento.py")
    base = pd.DataFrame(
        {
            "Func": [1, 2, 3],
            "Vinc": [1, 1, 1],
            "TipoVinculo": ["EFETIVO", "TEMPORÁRIO", "EFETIVO"],
            "EstimativaValorGR": [100.125, 200.0, 300.0],
        }
    )
    contratos = pd.DataFrame(
        {
            "Func": [2],
            "Vinc": [2],
            "TipoServidor": ["TAE"],
            "DataInicial": [pd.Timestamp("2025-01-01")],
            "DataFinal": [pd.Timestamp("2026-12-31")],
        }
    )
    vac = pd.DataFrame(
        {
            "Func": [3],
            "Vinc": [1],
            "Tipo": ["5017 - APOSENTADORIA"],
            "DataInicial": [pd.Timestamp("2026-01-01")],
            "DataFinal": [pd.Timestamp("1753-01-01")],
        }
    )
    resultados = []
    for modulo in [antigo, novo]:
        exportados = []

        def capturar(df, caminho, **kwargs):
            """Guarda nome, dados e opções que seriam enviados ao Excel."""
            exportados.append((str(caminho), df.copy(), kwargs))

        with patch.object(pd.DataFrame, "to_excel", capturar):
            modulo.defineVinc(
                base.copy(),
                contratos.copy(),
                vac.copy(),
                vac.iloc[:0].copy(),
                pd.Timestamp("2026-12-18"),
            )
        resultados.append(exportados)
    assert len(resultados[0]) == len(resultados[1])
    for (p1, d1, o1), (p2, d2, o2) in zip(*resultados):
        assert p1 == p2 and o1 == o2
        assert_frame_equal(d1, d2, check_exact=True)
