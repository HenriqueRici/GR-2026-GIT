from modelos.carregamentoDeDados import *
from modelos.tratamentoPagamento import *
from modelos.grupoEleitos import *
from modelos.absenteismo import *
from modelos.evasaoEscolar import *
from modelos.metaAdm import *
from modelos.formacao import *
from modelos.metaAprendizagem import *
from modelos.pontuacao import *
from google_sheets.cliente import *
from google_drive.cliente import *

from pathlib import Path
import time
from datetime import timedelta, datetime
import numpy as np
from sigabi import Sigabi
import os

print(f'\033[93mInício Execução: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}\033[0m')
inicioTempoReproducao = time.perf_counter()
inicioGR = pd.to_datetime('2026-02-02')
fimGR = pd.to_datetime('2026-11-30')
fimFormacao = pd.to_datetime('2026-11-19')
dataPagamento = pd.to_datetime('2026-12-18')
desktop_path = Path.home() / 'Desktop' / 'GR 2026'

api = Sigabi(
    login="06465533138",
    senha="123456"
)

baseVacancia = api.menus().consultar(
    menu=296,
    nomeBase= "Base Vacância",
    filtros=[
        {
            "field": "Acao_ID",
            "operator": "in",
            'value': [1, 2, 3]
        },
        {
            "field": "Cod_Situacao",
            "operator": "in",
            'value': [12, 18]
        },
        {
            "field": "Tipo",
            "operator": "in",
            'value': ['5017 - APOSENTADORIA', '5018 - EXONERACAO', '5019 - FALECIMENTO', '4032 - POSSE EM OUTRO CARGO INACUMULAVEL', 
                      '4035 - CEDÊNCIA PARA OUTRO ÓRGÃO OU PODER - SEM ONUS', '4029 - CEDENCIA PARA OUTRO ORGAO OU PODER - COM ONUS C/ RESSARC',
                      '4026 - CEDÊNCIA PARA OUTRO ÓRGÃO OU PODER - COM ONUS S/ RESSARC', '4025 - DESIGNAÇÃO/REGIME DE COLABORAÇÃO (ESTADO/MUNICIPIO)',
                      '4040 - DESIGNAÇÃO/REGIME DE COLABORAÇÃO (ESTADO/ESTADO)', '4028 - PERMUTA (ESTADO/ESTADO)',
                      '4023 - DESIG/REG DE COLABORACAO (ENT FILANT/OUTRAS INST)', '5032 - DEMISSÃO']
                }
    ],
     exclude_empty=[
        "Vinc"
    ],
    campos= ["Ano", "Grupo", "Tipo", "Cod_Situacao", "Servidor", "CPF", "Func", "Vinc", "DataInicial", "DataFinal",  "Acao_ID"],
    column_data=["DataInicial", "DataFinal"],
    column_int=["Ano", "Cod_Situacao", "Func", "Vinc", "Acao_ID"],
    column_str=["Grupo", "Tipo", "Servidor", "CPF"]
)

baseAtribuicao = api.menus().consultar(
    menu=330,
    nomeBase= "Base Atribuição",
    filtros=[
        {
            "field": "Ano",
            "operator": "in",
            'value': [2024, 2025, 2026]
        }
    ],
     exclude_empty=[
        "NumVinc"
    ],
    campos= ["Ano", "DRE", "Municipio", "SerieLotacao", "Lotacao", "TipoLotacao", "Nome", "CPF", "DataInicio", "DataFinal",  "CodFunc", "Funcao", 
             "TipoProcesso", "Processo", "NumFunc", "NumVinc", "CargoCarreira", "TotalCH", "AdmCH", "TipoServidor", "TipoVinculo", "AtividadeSeap"],
    column_data=["DataInicio", "DataFinal"],
    column_int=["Ano", "SerieLotacao", "CodFunc", "Processo", "NumFunc", "NumVinc", "TotalCH", "AdmCH", "AtividadeSeap"],
    column_str=["DRE", "Municipio", "Lotacao", "TipoLotacao", "Nome", "CPF", "Funcao", "TipoProcesso", "CargoCarreira", "TipoServidor", "TipoVinculo"]
)

baseHoraAtividade = api.menus().consultar(
    menu=296,
    nomeBase= "Base Hora Atividade",
    filtros=[
        {
            "field": "Ano",
            "operator": "in",
            'value': [2024, 2025, 2026]
        },
        {
             "field": "Tipo",
            "operator": "eq",
            'value': "2002 - HORA ATIVIDADE"
        },
        {
            "field": "Acao_ID",
            "operator": "in",
            'value': [1, 2, 3]
        },
        {
            "field": "Cod_Situacao",
            "operator": "in",
            'value': [12, 18]
        }
    ],
     exclude_empty=[
        "Vinc"
    ],
    campos= ["Tipo", "Cod_Situacao", "Servidor", "CPF", "Func", "Vinc", "Acao_ID"],
    column_data=["DataInicial", "DataFinal"],
    column_int=["Cod_Situacao", "Func", "Vinc", "Acao_ID"],
    column_str=["Tipo", "Servidor", "CPF"]
)


baseDE = api.menus().consultar(
    menu=296,
    nomeBase= "Base D.E.",
    filtros=[
        {
            "field": "Ano",
            "operator": "in",
            'value': [2023, 2024, 2025, 2026]
        },
        {
             "field": "Tipo",
            "operator": "in",
            'value': ['2010 - DEDICACAO EXCLUSIVA (COORDENADOR PEDAGOGICO)', '2011 - DEDICACAO EXCLUSIVA (DIRETOR)', 
                      '2012 - DEDICACAO EXCLUSIVA (SECRETARIO)', '2014 - DEDICACAO EXCLUSIVA (COORDENADOR PEDAGOGICO) / PEB', 
                      '2015 - DEDICACAO EXCLUSIVA (DIRETOR) / PEB']
        },
        {
            "field": "Acao_ID",
            "operator": "in",
            'value': [1, 2, 3]
        },
        {
            "field": "Cod_Situacao",
            "operator": "in",
            'value': [12, 18]
        }
    ],
    exclude_empty=[
        "Vinc"
    ],
    campos= ["Ano", "Tipo", "Cod_Situacao", "Processo", "Servidor", "CPF", "Func", "Vinc", "DataInicial", "DataFinal", "Acao_ID"],
    column_data=["DataInicial", "DataFinal"],
    column_int=["Ano", "Cod_Situacao", "Processo", "Func", "Vinc", "Acao_ID"],
    column_str=["Tipo", "Servidor", "CPF"]
)


baseAtribuicaoEmAula = api.menus().consultar(
    menu=723,
    nomeBase= "Base Atribuição em Aula",
    filtros=[
        {
            "field": "Ano",
            "operator": "eq",
            'value': 2026
        }
    ],
    exclude_empty=[
        "CodigoSEAP"
    ],
    campos= ["ChaveTurma", "LotacaoID", "CPF", "Motivo", "CH", "DataInicial", "DataFinal", "Tipo", "CodigoSEAP", "VinculoSEAP"],
    column_data=["DataInicial", "DataFinal"],
    column_int=["LotacaoID", "CH", "CodigoSEAP", "VinculoSEAP"],
    column_str=["ChaveTurma", "CPF", "Motivo", "Tipo"]
)


baseLicencasAfastamentos = api.menus().consultar(
    menu=296,
    nomeBase= "Base Licenças e Afastamentos",
    filtros=[
        {
             "field": "Tipo",
            "operator": "in",
            'value':  ['4020 - LICENCA PARA TRATAMENTO DE SAUDE (EFETIVO)', '4021 - LICENCA PARA TRATAMENTO DE SAUDE EM PESSOA DA FAMILIA', 
                       '5020 - LICENÇA PARA QUALIFICAÇÃO PROFISSIONAL', '4013 - LICENCA PARA TRATAMENTO DE SAUDE (CONTRATADO)', '5012 - PROCESSO ADMINISTRATIVO DISCIPLINAR', 
                       '4027 - LICENÇA PARA DESEMPENHO DO MANDATO CLASSISTA', '5010 - AFASTAMENTO PARA EXERCÍCIO DE MANDATO ELETIVO S/ ONUS', '5025 - AFASTAMENTO PRISÃO / FLAGRANTE OU PREVENTIVA', 
                       '5016 - AGUARDANDO APOSENTADORIA POR INVALIDEZ', '4033 - LICENCA POR MOTIVO DE CASAMENTO', '5028 - ARC - AGUARDANDO REGULARIZAÇÃO DO CARGO', '5031 - AFASTAMENTO PREVENTIVO', 
                       '5023 - LICENÇA PARA ATIVIDADE POLITICA', '5030 - P.A.D - AGUARDANDO REGULARIZAÇÃO CARGO','5009 - AFASTAMENTO PARA EXERCÍCIO DE MANDATO ELETIVO C/ ONUS', 
                       '5011 - AFASTAMENTO PARA ESTUDO OU MISSÃO NO EXTERIOR', '4005 - LICENCA PARA TRATAMENTO DE SAUDE (COMISSIONADO)', '5015 - AFASTAMENTO POR MOTIVO DE CONDENAÇÃO POR SENT. DEFINITIVA', 
                       '5026 - PROCESSO DE SINDICÂNCIA', '5021 - AFASTAMENTO/DECISÃO JUDICIAL', '5013 - AFASTAMENTO PARA ESTUDO OU MISSÃO NO EXTERIOR - COM ÔNUS', 
                       '5049 - TCAC - TERMO DE COMPROMISSO DE AJUSTAMENTO DE CONDUTA']
        },
        {
            "field": "Acao_ID",
            "operator": "in",
            'value': [1, 2,3]
        },
        {
            "field": "Cod_Situacao",
            "operator": "in",
            'value': [12, 18]
        }
    ],
    exclude_empty=[
        "Vinc"
    ],
    campos= ["Grupo", "Tipo", "Cod_Situacao", "Servidor", "CPF", "Func", "Vinc", "DataInicial", "DataFinal", "Acao_ID"],
    column_data=["DataInicial", "DataFinal"],
    column_int=["Cod_Situacao", "Func", "Vinc", "Acao_ID"],
    column_str=["Grupo", "Tipo", "Servidor", "CPF"]
)


licencasCalcVacancia = api.menus().consultar(
    menu=296,
    nomeBase= "Base Licenças Proporcionais",
    filtros=[
        {
             "field": "Tipo",
            "operator": "in",
            'value':  ['4015 - LICENCA A GESTANTE (CONTRATADO)', '4019 - LICENÇA A GESTANTE/COMPLEMENTO (CONTRATADO)', '4022 - LICENCA GESTANTE (SERVIDORA EFETIVA)', '4011 - LICENCA PARA ACOMPANHAMENTO DO CONJUGE', 
                       '4010 - LICENCA PARA TRATAMENTO DE INTERESSE PARTICULAR', '4014 - LICENCA A ADOTANTE EFETIVO', 
                       '4034 - LICENCA POR LUTO', '4024 - LICENÇA PATERNIDADE', '4017 - LICENCA A ADOTANTE INTERINO', '4078 - LICENÇA MATERNIDADE']
        },
        {
            "field": "Acao_ID",
            "operator": "in",
            'value': [1, 2,3]
        },
        {
            "field": "Cod_Situacao",
            "operator": "in",
            'value': [12, 18]
        }
    ],
    exclude_empty=[
        "Vinc"
    ],
    campos= ["Grupo", "Tipo", "Cod_Situacao", "Servidor", "CPF", "Func", "Vinc", "DataInicial", "DataFinal", "Acao_ID"],
    column_data=["DataInicial", "DataFinal"],
    column_int=["Cod_Situacao", "Func", "Vinc", "Acao_ID"],
    column_str=["Grupo", "Tipo", "Servidor", "CPF"]
)

baseVacancia = pd.concat([baseVacancia, licencasCalcVacancia])


baseFrequencias = api.menus().consultar(
    menu=296,
    nomeBase= "Base Frequência",
    filtros=[
        {
            "field": "Ano",
            "operator": "eq",
            'value':  2026
        },
        {
             "field": "Tipo",
            "operator": "in",
            'value':  ['30010 - FALTAS NÃO JUSTIFICADAS ( SEM ANUÊNCIA )', '10099 - FALTAS NÃO JUSTIFICADAS ( SEM ANUÊNCIA ) - PROPORCIONAL']
        },
        {
            "field": "Acao_ID",
            "operator": "in",
            'value': [1, 2,3]
        },
        {
            "field": "Cod_Situacao",
            "operator": "in",
            'value': [12, 18]
        }
    ],
    exclude_empty=[
        "Vinc"
    ],
    campos= ["Grupo", "Tipo", "Cod_Situacao", "Servidor", "CPF", "Func", "Vinc", "DataInicial", "DataFinal", "Acao_ID"],
    column_data=["DataInicial", "DataFinal"],
    column_int=["Cod_Situacao", "Func", "Vinc", "Acao_ID"],
    column_str=["Grupo", "Tipo", "Servidor", "CPF"]
)

'''
baseContratos = api.menus().consultar(
    menu=296,
    nomeBase= "Base Contratos",
    filtros=[
        {
            "field": "Grupo",
            "operator": "eq",
            'value':  "CONTRATO"
        },
        {
            "field": "Ano",
            "operator": "in",
            'value':  [2024, 2025, 2026]
        },
        {
            "field": "Acao_ID",
            "operator": "in",
            'value': [1, 2,3]
        },
        {
            "field": "Cod_Situacao",
            "operator": "in",
            'value': [12, 18]
        }
    ],
    column_data=[
        "DataInicial",
        "DataFinal"
    ],
     exclude_empty=[
        "Vinc"
    ],
    campos= ["Grupo", "Tipo", "Cod_Situacao", "Servidor", "CPF", "Func", "Vinc", "DataInicial", "DataFinal", "Acao_ID"]
)

'''

baseAdm = getGoogleSheets(
    nome_aba = "Meta Administrativa",
    column_float=["Meta administrativa - Alimentação Escolar", "Meta administrativa - Limpeza e Organização dos Ambientes Escolares", 
                  "Meta administrativa - Patrimônio Mobiliário e Imobiliário Escolar", "Meta administrativa - Manutenção e Conservação da Infraestrutura Escolar", 
                  "Meta administrativa - Gestão", "Meta administrativa - Resultados"],
    column_str=["LotacaoGR", "Municipio", "NomeEscola", "TipoEscola"])



baseMetaAprendizagemTurmas = getGoogleSheets(
    nome_aba = "Meta de Aprendizagem (Turmas)",
    column_float=["NotaInicialAprendizagem", "MetaAprendizagem", "NotaFinalAprendizagem"],
    column_str=["LotacaoGR", "NomeEscola", "TipoEscola"])

baseMetaAprendizagemUnidades = getGoogleSheets(
    nome_aba = "Meta de Aprendizagem (Unidades)",
    column_float=["NotaInicialAprendizagem", "MetaAprendizagem", "NotaFinalAprendizagem"],
    column_str=["LotacaoGR", "NomeEscola", "TipoEscola", "DescriçãoTurma", "ModalidadeTurma"])


baseEvasao = getGoogleSheets(
    nome_aba = "Evasão Escolar",
    column_float=["Frequencia"],
    column_str=["LotacaoGR", "NomeEscola", "TipoEscola"])

baseFuncaoConfianca = getGoogleSheets(
    nome_aba = "Função de Confiança",
    column_data=["dtini", "dtfim", "dtinirem", "dtfimrem", "dtexerc", "dtaposent", "dtvac"],
    column_int=["numfunc", "numvinc", "cargo", "setor", "numfunc_tit", "numvinc_tit", "numero_vaga"],
    column_str=["ident_vinc", "nome", "orgao", "regime_jur", "formaprov", "categoria", "subcategoria", "referencia", "tipoevento", 
                "obs", "cargo_aglut", "descr_cargo", "descr_setor", "ident_func_tit", "descr_cargo_aglut", "tipo_vinc", "FLEX_CAMPO_01", "jornada", "especialidade"])

baseCargoConfianca = getGoogleSheets(
    nome_aba = "Cargos em Comissão",
    column_data=["dtini", "dtfim", "dtinirem", "dtfimrem", "dtexerc", "dtaposent", "dtvac"],
    column_int=["numfunc", "numvinc", "cargo", "setor", "numfunc_tit", "numvinc_tit", "numero_vaga"],
    column_str=["ident_vinc", "nome", "orgao", "regime_jur", "formaprov", "categoria", "subcategoria", "referencia", "tipoevento", 
                    "obs", "cargo_aglut", "descr_cargo", "descr_setor", "ident_func_tit", "descr_cargo_aglut", "tipo_vinc", "FLEX_CAMPO_01", "jornada", "especialidade"])

baseInclusaoManual = getGoogleSheets(
    nome_aba = "Inclusão Manual",
    column_data=["DataInicio", "DataFinal"],
    column_int=["SerieLotacao", "NumFunc", "NumVinc", "TotalCH", "AdmCH", "AtividadeSeap"],
    column_str=["DRE", "Lotacao", "TipoLotacao", "Nome", "CPF", "Funcao", "CargoCarreira", "TipoServidor", "TipoVinculo"])

baseSEAP = pd.concat([baseFuncaoConfianca, baseCargoConfianca])
baseAtribuicao = pd.concat([baseAtribuicao, baseInclusaoManual])


baseWebPonto = lerDadoWebPonto(campos= ['NOME', 'LOGIN', 'MF', 'DataFrequencia', 'EntradaManha', 'SaidaManha', 'EntradaTarde', 'SaidaTarde', 'EntradaNoite', 'SaidaNoite'],
                               column_data=["DataFrequencia"], 
                               column_data_hora=['EntradaManha', 'SaidaManha', 'EntradaTarde', 'SaidaTarde', 'EntradaNoite', 'SaidaNoite'], 
                               column_int=["LOGIN"], 
                               column_str=["NOME", "MF"])

                            

'''
#ATUALIZAR BASES DE FORMAÇÃO
baseFormacaoObgrigatoria = carregaAPIFormacaoObrigatoria("https://script.google.com/a/edu.mt.gov.br/macros/s/AKfycbzx5VeUgOQBQgDBDNGRb7NcvkNNYs5DNOmzqKFmthyT2TDF7M2Zr9GRk2Mdefc9GTlkiw/exec?sheetid=1ednabjk66kBZ_b5odUJ5HQEPagwWMwTE7itzNYOCIh0&gid=0&format=json")
baseFormacaoEletivaRealizada = carregaAPIFormacaoEletiva("https://script.google.com/a/edu.mt.gov.br/macros/s/AKfycbzx5VeUgOQBQgDBDNGRb7NcvkNNYs5DNOmzqKFmthyT2TDF7M2Zr9GRk2Mdefc9GTlkiw/exec?sheetid=1ednabjk66kBZ_b5odUJ5HQEPagwWMwTE7itzNYOCIh0&gid=1333313896&format=json")
print(f'\033[92mBase Formação concluído em {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}\033[0m')
'''
print(f'\033[93mBases Carregadas: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}\033[0m')
####################################################################################################################################################

atribuicao = trataAtribuicao(baseAtribuicao, baseHoraAtividade, baseVacancia, inicioGR, fimGR)
cargoGR = definirCargoGR(atribuicao, baseAtribuicaoEmAula, baseDE, baseSEAP, inicioGR, fimGR)
teto = tetoGr(cargoGR)
eleitosGR = pd.merge(cargoGR, teto, how='left', on='CPF')
eleitosGR = proporcaoVinculo(eleitosGR)
eleitosGR['ValorGRBaseVinculo'] = eleitosGR.apply(valorGRBase, axis=1)

eleitosGR = evasao(eleitosGR, baseEvasao)
eleitosGR['PontuacaoEvasao'] = eleitosGR.apply(pontuacaoEvasao, axis=1)

eleitosGR = metaAdministrativa(eleitosGR, baseAdm)

eleitosGR = metaAprendizagem(eleitosGR, baseAtribuicaoEmAula, baseMetaAprendizagemUnidades, baseMetaAprendizagemTurmas) 
eleitosGR['PontuacaoMetaAprendizagem'] = eleitosGR.apply(pontuacaoMetaAprendizagem, axis=1)

#temporario
eleitosGR['CHObrigatoria'] = 0
eleitosGR['CHObrigatoriaRealizada'] = 0
eleitosGR['CHEletiva'] = 0
eleitosGR['PontuacaoFormacao'] = 0

# eleitosGR = formacaoObrigatoria(eleitosGR, baseFormacaoObgrigatoria, inicioGR, colFormacao='CHObrigatoria')
# eleitosGR = formacaoObrigatoria(eleitosGR, baseFormacaoObgrigatoria, inicioGR, colFormacao='CHObrigatoriaRealizada')
# eleitosGR = formacaoEletivaRealizada(eleitosGR, baseFormacaoEletivaRealizada)
# eleitosGR['PontuacaoFormacao'] = eleitosGR.apply(pontuacaoFormacao, axis=1)

eleitosGR = absenteismoGeral(eleitosGR, absenteismoWebPonto(eleitosGR, baseWebPonto), 
                             absenteismoLicencasAfastamentos(baseLicencasAfastamentos, inicioGR, fimGR), 
                             absenteismoFrequencias(baseWebPonto, baseFrequencias))
         
eleitosGR['PontuacaoAbsenteismo'] = eleitosGR.apply(pontuacaoAbsenteismo, axis=1)
eleitosGR['MaxAbsenteismo'] = eleitosGR.apply(maxAbsenteismo, axis=1)

eleitosGR['PontuacaoGeral'] = eleitosGR.apply(pontuacaoGeral, axis=1)
eleitosGR['EstimativaValorGR'] = eleitosGR.apply(valorFinalGR, axis=1)
eleitosGR['EstimativaValorGR'] = eleitosGR['EstimativaValorGR'].clip(lower=0)
eleitosGR.to_excel(desktop_path / 'PreviaGR.xlsx', index=True)


# vinc = defineVinc(eleitosGR,baseContratos, baseVacancia, licencasCalcVacancia, dataPagamento)
fimTempoReproducao = time.perf_counter()
duracao = fimTempoReproducao - inicioTempoReproducao
tempo_formatado = str(timedelta(seconds=int(duracao)))
print(f'\033[93mTempo decorrido: {tempo_formatado}\033[0m')