from pathlib import Path

import pandas as pd
import os

def defineVinc(base, baseContrato, baseVacancia, licencasCalcVacancia, dtPagamento):
    desktop_path = Path.home() / 'Desktop' / 'GR 2025'

    baseEfetivo = base.drop_duplicates(subset=['Func', 'Vinc', 'TipoVinculo'])
    baseEfetivo = baseEfetivo[baseEfetivo['TipoVinculo'] == 'EFETIVO'].copy()
    
    valorGRTotal = base.groupby(['Func', 'TipoVinculo']).agg(ValorGR=('EstimativaValorGR', 'sum')).reset_index()
    valorGRTotal = valorGRTotal[valorGRTotal['ValorGR'] > 0].copy()

    contratos = valorGRTotal[valorGRTotal['TipoVinculo'] == 'TEMPORÁRIO'].copy()
    
    baseContrato = baseContrato[baseContrato['TipoServidor'] != "PROFESSOR"].copy()
    baseContrato = baseContrato.groupby(['Func', 'Vinc']).agg(DataInicioVinculo=('DataInicial', 'min'), DataFinalVinculo=('DataFinal', 'max')).reset_index()
    baseContrato = baseContrato[['Func', 'Vinc', 'DataInicioVinculo', 'DataFinalVinculo']]
    baseContrato = baseContrato[baseContrato['DataFinalVinculo'] >= pd.to_datetime('2025-01-01')].copy()
    
    ativos = baseContrato[(baseContrato['DataInicioVinculo'] <= dtPagamento) & (baseContrato['DataFinalVinculo'] >= dtPagamento)].copy()
    ativos['STATUS'] = 'CONTRATO-EFETIVO ATIVO'
    melhor_vinc_ativos = ativos.sort_values(['Func', 'DataInicioVinculo'], ascending=[True, False]).drop_duplicates('Func', keep='first')

    nao_ativos = baseContrato[~baseContrato['Func'].isin(melhor_vinc_ativos['Func'])]
    antes = nao_ativos[nao_ativos['DataFinalVinculo'] <= dtPagamento].copy()
    antes['STATUS'] = 'CONTRATO INATIVO'
    melhor_vinc_nao_ativo = antes.sort_values(['Func', 'DataFinalVinculo'], ascending=[True, False]).drop_duplicates('Func', keep='first')

    melhorVincContrato = pd.concat([melhor_vinc_ativos, melhor_vinc_nao_ativo], ignore_index=True)
    melhorVincContrato = melhorVincContrato[['Func', 'Vinc', 'STATUS']]

    contratos = pd.merge(contratos, melhorVincContrato, on=['Func'], how='left')
    contratos = contratos[['Func', 'Vinc', 'ValorGR', 'STATUS']] ## CONTRATOS TRATADOS
    
    lipLac = licencasCalcVacancia[licencasCalcVacancia['Tipo'].isin(['4010 - LICENCA PARA TRATAMENTO DE INTERESSE PARTICULAR', '4011 - LICENCA PARA ACOMPANHAMENTO DO CONJUGE'])]
    baseVacancia = pd.concat([baseVacancia, lipLac], ignore_index=True)
    
    baseVacancia.loc[baseVacancia['DataFinal'] == pd.Timestamp('1753-01-01'), 'DataFinal'] = dtPagamento
    baseVacancia = baseVacancia[baseVacancia['DataFinal'] >= dtPagamento].copy()
    baseVacancia = baseVacancia[['Func', 'Vinc', 'Tipo']]
    baseVacancia = baseVacancia.drop_duplicates(subset=['Func', 'Vinc', 'Tipo'])

    efetivos = pd.merge(baseEfetivo, baseVacancia, on=['Func', 'Vinc'], how='left')

    efetivos['STATUS'] = efetivos['Tipo'].apply(
    lambda x: 'CONTRATO-EFETIVO ATIVO' if x == '4025 - DESIGNAÇÃO/REGIME DE COLABORAÇÃO (ESTADO/MUNICIPIO)'
    else 'FALECIDO' if x == '5019 - FALECIMENTO'
    else 'APOSENTADO' if x == '5017 - APOSENTADORIA'
    else 'POSSE EM OUTRO CARGO' if x == '4032 - POSSE EM OUTRO CARGO INACUMULAVEL'
    else 'EXONERADO' if x == '5018 - EXONERACAO'
    else 'CONTRATO-EFETIVO ATIVO' if x == '4028 - PERMUTA (ESTADO/ESTADO)'
    else 'CONTRATO-EFETIVO ATIVO' if x == '4029 - CEDENCIA PARA OUTRO ORGAO OU PODER - COM ONUS C/ RESSARC'
    else 'CEDIDO' if x == '4035 - CEDÊNCIA PARA OUTRO ÓRGÃO OU PODER - SEM ONUS'
    else 'CEDIDO' if x == '4026 - CEDÊNCIA PARA OUTRO ÓRGÃO OU PODER - COM ONUS S/ RESSARC'
    else 'LIP/LAC' if x == '4010 - LICENCA PARA TRATAMENTO DE INTERESSE PARTICULAR'
    else 'LIP/LAC' if x == '4011 - LICENCA PARA ACOMPANHAMENTO DO CONJUGE'
    else 'CONTRATO-EFETIVO ATIVO')

    efetivos = pd.merge(efetivos, valorGRTotal, on=['Func'], how='left')
    efetivos = efetivos[['Func', 'Vinc', 'ValorGR', 'STATUS']]

    concat = pd.concat([contratos, efetivos], ignore_index=True)
    concat = concat[concat['ValorGR'] > 0].copy()

    ordem_status = [
    'FALECIDO',
    'CONTRATO-EFETIVO ATIVO',
    'APOSENTADO',
    'POSSE EM OUTRO CARGO',
    'LIP/LAC',
    'EXONERADO',
    'CEDIDO',
    'CONTRATO INATIVO',
    'INDEFINIDO']

    concat['STATUS'] = pd.Categorical(concat['STATUS'], categories=ordem_status, ordered=True)
    melhorVinc = concat.sort_values(['Func', 'STATUS']).groupby('Func').first().reset_index()
    
    melhorVinc['STATUS'] = melhorVinc['STATUS'].fillna("INDEFINIDO")

    pasta = desktop_path / "BASE PAGAMENTO"

    melhorVinc['ValorGR'] = melhorVinc['ValorGR'].round(2)
    
    for status, grupo in melhorVinc.groupby('STATUS', observed=False):
        nome_arquivo = f"{status}.xlsx".replace("/", "-")  # evita erro com barras
        caminho_completo = os.path.join(pasta, nome_arquivo)
        grupo = grupo.drop(columns=['STATUS']) # Remove a coluna STATUS
        grupo.to_excel(caminho_completo, index=False)

    return