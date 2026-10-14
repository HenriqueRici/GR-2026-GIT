import pandas as pd
from pathlib import Path
from datetime import datetime

def metaAprendizagem(base, baseTurmas, baseMetaAprendizagemUnidades, baseMetaAprendizagemTurmas ):
    desktop_path = Path.home() / 'Desktop' / 'GR 2026'

    profRegencia =  base[base["CargoGR"] == "PROFESSOR EM REGÊNCIA"].copy()
    profRegencia = profRegencia[['LotacaoGR', 'Func', 'Vinc']]
    demaisCargos = base[base["CargoGR"] != "PROFESSOR EM REGÊNCIA"].copy()
    demaisCargos = demaisCargos[['LotacaoGR', 'Func', 'Vinc']]
    
    baseTurmas = baseTurmas[baseTurmas['CodigoSEAP'].notna()]
    baseTurmas = baseTurmas[['CodigoSEAP', 'VinculoSEAP', 'ChaveTurma', 'CH', 'DataInicial', 'DataFinal']]
    baseTurmas = baseTurmas.rename(columns={'CodigoSEAP': 'Func', 'VinculoSEAP': 'Vinc'})
    baseTurmas = baseTurmas.groupby(['Func', 'Vinc', 'ChaveTurma', 'DataInicial', 'DataFinal']).agg(CH=('CH', 'sum')).reset_index()
    baseTurmas['Dias'] =  (baseTurmas['DataFinal'] - baseTurmas['DataInicial']).dt.days + 1

    baseTurmas['Peso'] = baseTurmas['Dias'] * baseTurmas['CH']
    somaPeso = baseTurmas.groupby(['Func', 'Vinc']).agg(PesoTotal=('Peso', 'sum')).reset_index()
    baseTurmas = pd.merge(baseTurmas, somaPeso, how='left', on=['Func', 'Vinc'])
    baseTurmas['PercentualMetaAprendizagem'] = baseTurmas['Peso']/baseTurmas['PesoTotal']
    baseTurmas = baseTurmas.groupby(['Func', 'Vinc', 'ChaveTurma']).agg(PercentualMetaAprendizagem=('PercentualMetaAprendizagem', 'sum')).reset_index()
    baseTurmas['ChaveTurma'] = baseTurmas['ChaveTurma'].str.replace('"', '', regex=False)

    baseTurmas = pd.merge(baseTurmas, baseMetaAprendizagemTurmas, how='left', on='ChaveTurma')
    
    colunas = ['NotaInicialAprendizagem', 'MetaAprendizagem', 'NotaFinalAprendizagem']
    baseTurmas[colunas] = baseTurmas[colunas].fillna(0)
    baseTurmas.to_excel(desktop_path / 'baseTurmasServidor.xlsx', index=False)

    baseTurmas['NotaInicialAprendizagem'] = baseTurmas['NotaInicialAprendizagem']*baseTurmas['PercentualMetaAprendizagem']
    baseTurmas['MetaAprendizagem'] = baseTurmas['MetaAprendizagem']*baseTurmas['PercentualMetaAprendizagem']
    baseTurmas['NotaFinalAprendizagem'] = baseTurmas['NotaFinalAprendizagem']*baseTurmas['PercentualMetaAprendizagem']
    baseTurmas = baseTurmas.groupby(['Func', 'Vinc']).agg(NotaInicialAprendizagem=('NotaInicialAprendizagem', 'sum'), 
                                                          MetaAprendizagem=('MetaAprendizagem', 'sum'), 
                                                          NotaFinalAprendizagem=('NotaFinalAprendizagem', 'sum')).reset_index()


    baseTurmas['NotaInicialAprendizagem'] = baseTurmas['NotaInicialAprendizagem'].round(2)
    baseTurmas['MetaAprendizagem'] = baseTurmas['MetaAprendizagem'].round(2)
    baseTurmas['NotaFinalAprendizagem'] = baseTurmas['NotaFinalAprendizagem'].round(2)
   
    profRegencia = pd.merge(profRegencia, baseTurmas, how='left', on=['Func', 'Vinc'])

    demaisCargos["LotacaoGR"] = demaisCargos["LotacaoGR"].astype(str)
    baseMetaAprendizagemUnidades["LotacaoGR"] = baseMetaAprendizagemUnidades["LotacaoGR"].astype(str)

    demaisCargos = pd.merge(demaisCargos, baseMetaAprendizagemUnidades, how='left', on=['LotacaoGR'])
    metaPronta = pd.concat([demaisCargos, profRegencia])
    metaPronta = metaPronta.drop_duplicates(subset=['LotacaoGR', 'Func', 'Vinc'])
    base = pd.merge(base, metaPronta, how='left', on=['LotacaoGR', 'Func', 'Vinc'])

    base = base[['Municipio', 'LotacaoGR', 'DescricaoLotacaoGR', 'Nome', 'CPF', 'Func', 'Vinc', 'TipoVinculo', 'CargoCarreira', 
                     'CargoGR', 'DataInicio', 'DataFinal', 'CH', 'PercentualGRVinculo', 'ValorGRBaseVinculo', 'Frequencia', 'PontuacaoEvasao', 
                     'Meta administrativa - Alimentação Escolar', 'Meta administrativa - Limpeza e Organização dos Ambientes Escolares',
                     'Meta administrativa - Patrimônio Mobiliário e Imobiliário Escolar', 'Meta administrativa - Manutenção e Conservação da Infraestrutura Escolar',
                     'Meta administrativa - Gestão', 'Meta administrativa - Resultados', 'PontuacaoEixoPatrimonio', 'PontuacaoEixoInfraestruturaEscolar',
                     'PontuacaoEixoLimpeza', 'PontuacaoEixoAlimentacao', 'PontuacaoEixoResultados', 'PontuacaoEixoGestao', 'PontuacaoMetaAdiministrativa', 
                     'NotaInicialAprendizagem', 'MetaAprendizagem', 'NotaFinalAprendizagem']]


    print(f'\033[92mMeta Aprendizagem pronto, concluído em ' f'{datetime.now().strftime("%d/%m/%Y %H:%M:%S")}\033[0m')
    return base


def pontuacaoMetaAprendizagem(row):
    if row['CargoGR'] == "TAE/AAE":
        if row['NotaInicialAprendizagem'] <= row['NotaFinalAprendizagem'] < row['MetaAprendizagem']:
            return 15
        elif row['NotaFinalAprendizagem'] == row['MetaAprendizagem']:
            return 30
        elif row['MetaAprendizagem'] < row['NotaFinalAprendizagem'] <= row['MetaAprendizagem'] * 1.2:
            return 40
        elif row['NotaFinalAprendizagem'] > row['MetaAprendizagem'] * 1.2:
            return 50
        else:
            return 0
    elif row['CargoGR'] == "PROFESSOR EM REGÊNCIA":
        if row['NotaInicialAprendizagem'] <= row['NotaFinalAprendizagem'] < row['MetaAprendizagem']:
            return 180
        elif row['NotaFinalAprendizagem'] == row['MetaAprendizagem']:
            return 360
        elif row['MetaAprendizagem'] < row['NotaFinalAprendizagem'] <= row['MetaAprendizagem'] * 1.2:
            return 405
        elif row['NotaFinalAprendizagem'] > row['MetaAprendizagem'] * 1.2:
            return 450
        else:
            return 0
    elif row['CargoGR'] == "GESTOR":
        if row['NotaInicialAprendizagem'] <= row['NotaFinalAprendizagem'] < row['MetaAprendizagem']:
            return 90
        elif row['NotaFinalAprendizagem'] == row['MetaAprendizagem']:
            return 180
        elif row['MetaAprendizagem'] < row['NotaFinalAprendizagem'] <= row['MetaAprendizagem'] * 1.2:
            return 200
        elif row['NotaFinalAprendizagem'] > row['MetaAprendizagem'] * 1.2:
            return 225
        else:
            return 0
    elif row['CargoGR'] == "PROFESSOR FORA DE REGÊNCIA":
        if row['NotaInicialAprendizagem'] <= row['NotaFinalAprendizagem'] < row['MetaAprendizagem']:
            return 180
        elif row['NotaFinalAprendizagem'] == row['MetaAprendizagem']:
            return 360
        elif row['MetaAprendizagem'] < row['NotaFinalAprendizagem'] <= row['MetaAprendizagem'] * 1.2:
            return 405
        elif row['NotaFinalAprendizagem'] > row['MetaAprendizagem'] * 1.2:
            return 450
        else:
            return 0
    elif row['CargoGR'] == "CIVIS E MILITARES LOTADOS NA SEDUC":
        if row['NotaInicialAprendizagem'] <= row['NotaFinalAprendizagem'] < row['MetaAprendizagem']:
            return 100
        elif row['NotaFinalAprendizagem'] == row['MetaAprendizagem']:
            return 200
        elif row['MetaAprendizagem'] < row['NotaFinalAprendizagem'] <= row['MetaAprendizagem'] * 1.2:
            return 225
        elif row['NotaFinalAprendizagem'] > row['MetaAprendizagem'] * 1.2:
            return 300
        else:
            return 0
    else:
        return 0

