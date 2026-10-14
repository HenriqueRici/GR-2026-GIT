import pandas as pd
import numpy as np
from datetime import datetime

def metaAdministrativa(base, baseAdm):

    base = pd.merge(base, baseAdm, on='LotacaoGR', how='left')

    colunas_metas = [
        'Meta administrativa - Patrimônio Mobiliário e Imobiliário Escolar',
        'Meta administrativa - Manutenção e Conservação da Infraestrutura Escolar',
        'Meta administrativa - Limpeza e Organização dos Ambientes Escolares',
        'Meta administrativa - Alimentação Escolar',
        'Meta administrativa - Resultados',
        'Meta administrativa - Gestão']

    base[colunas_metas] = base[colunas_metas].fillna(0)

    base['PontuacaoEixoPatrimonio'] = base.apply(pontosEixoPatrimonio, axis=1)
    base['PontuacaoEixoInfraestruturaEscolar'] = base.apply(pontosEixoInfraestruturaEscolar, axis=1)
    base['PontuacaoEixoLimpeza'] = base.apply(pontosEixoLimpeza, axis=1)
    base['PontuacaoEixoAlimentacao'] = base.apply(pontosEixoAlimentacao, axis=1)
    base['PontuacaoEixoResultados'] = base.apply(pontosEixoResultados, axis=1)
    base['PontuacaoEixoGestao'] = base.apply(pontosEixoGestao, axis=1)

    colunas_pontuacao = [
        'PontuacaoEixoPatrimonio',
        'PontuacaoEixoInfraestruturaEscolar',
        'PontuacaoEixoLimpeza',
        'PontuacaoEixoAlimentacao',
        'PontuacaoEixoResultados',
        'PontuacaoEixoGestao'
    ]

    base['PontuacaoMetaAdiministrativa'] = np.ceil(base[colunas_pontuacao].sum(axis=1))

    base = base[['Municipio', 'LotacaoGR', 'DescricaoLotacaoGR', 'Nome', 'CPF', 'Func', 'Vinc', 'TipoVinculo', 'CargoCarreira', 
                 'CargoGR', 'DataInicio', 'DataFinal', 'CH', 'PercentualGRVinculo', 'ValorGRBaseVinculo', 'Frequencia', 'PontuacaoEvasao', 
                 'Meta administrativa - Alimentação Escolar', 'Meta administrativa - Limpeza e Organização dos Ambientes Escolares',
                 'Meta administrativa - Patrimônio Mobiliário e Imobiliário Escolar', 'Meta administrativa - Manutenção e Conservação da Infraestrutura Escolar',
                 'Meta administrativa - Gestão', 'Meta administrativa - Resultados', 'PontuacaoEixoPatrimonio', 'PontuacaoEixoInfraestruturaEscolar',
                 'PontuacaoEixoLimpeza', 'PontuacaoEixoAlimentacao', 'PontuacaoEixoResultados', 'PontuacaoEixoGestao', 'PontuacaoMetaAdiministrativa']]

    print(f'\033[92mMeta Administrativa pronto, concluído em ' f'{datetime.now().strftime("%d/%m/%Y %H:%M:%S")}\033[0m')
    return base


def pontosEixoPatrimonio(row):
    nota_maxima = 75
    tamanho_faixa = 0.25 * nota_maxima  
    if row['CargoGR'] == 'GESTOR':
        valor_faixa = 9.375
        faixas_completas = int(row['Meta administrativa - Patrimônio Mobiliário e Imobiliário Escolar'] // tamanho_faixa)
        return (faixas_completas * valor_faixa)/2
    elif row['CargoGR'] == 'TAE/AAE':
        valor_faixa = 15.625
        faixas_completas = int(row['Meta administrativa - Patrimônio Mobiliário e Imobiliário Escolar'] // tamanho_faixa)
        return (faixas_completas * valor_faixa)/2
    else:
        return 0



def pontosEixoInfraestruturaEscolar(row):
    nota_maxima = 75
    tamanho_faixa = 0.25 * nota_maxima  
    if row['CargoGR'] == 'GESTOR':
        valor_faixa = 9.375
        faixas_completas = int(row['Meta administrativa - Manutenção e Conservação da Infraestrutura Escolar'] // tamanho_faixa)
        return (faixas_completas * valor_faixa)/2
    elif row['CargoGR'] == 'TAE/AAE':
        valor_faixa = 15.625
        faixas_completas = int(row['Meta administrativa - Manutenção e Conservação da Infraestrutura Escolar' \
        ''] // tamanho_faixa)
        return (faixas_completas * valor_faixa)/2
    else:
        return 0

def pontosEixoLimpeza(row):
    nota_maxima = 75
    tamanho_faixa = 0.25 * nota_maxima 
    if row['CargoGR'] == 'GESTOR':
        valor_faixa = 9.375
        faixas_completas = int(row['Meta administrativa - Limpeza e Organização dos Ambientes Escolares'] // tamanho_faixa)
        return faixas_completas * valor_faixa
    elif row['CargoGR'] == 'TAE/AAE':
        valor_faixa = 15.625
        faixas_completas = int(row['Meta administrativa - Limpeza e Organização dos Ambientes Escolares'] // tamanho_faixa)
        return faixas_completas * valor_faixa
    else:
        return 0
    
def pontosEixoAlimentacao(row):
    nota_maxima = 75
    tamanho_faixa = 0.25 * nota_maxima  
    if row['CargoGR'] == 'GESTOR':
        valor_faixa = 9.375
        faixas_completas = int(row['Meta administrativa - Alimentação Escolar'] // tamanho_faixa)
        return faixas_completas * valor_faixa
    elif row['CargoGR'] == 'TAE/AAE':
        valor_faixa = 15.625
        faixas_completas = int(row['Meta administrativa - Alimentação Escolar'] // tamanho_faixa)
        return faixas_completas * valor_faixa
    else:
        return 0


def pontosEixoResultados(row):
    nota_maxima = 600
     
    if row['CargoGR'] == 'GESTOR':
        tamanho_faixa = 0.125 * nota_maxima 
        valor_faixa = 7.031
        faixas_completas = int(row['Meta administrativa - Resultados'] // tamanho_faixa)
        return faixas_completas * valor_faixa
    elif row['CargoGR'] == 'TAE/AAE':
        tamanho_faixa = 0.0625 * nota_maxima  
        valor_faixa = 3.90625
        faixas_completas = int(row['Meta administrativa - Resultados'] // tamanho_faixa)
        return faixas_completas * valor_faixa
    else:
        return 0
    

def pontosEixoGestao(row):
    nota_maxima = 100
    if row['CargoGR'] == 'GESTOR':
        tamanho_faixa = 0.125 * nota_maxima 
        valor_faixa = 7.031
        faixas_completas = int(row['Meta administrativa - Gestão'] // tamanho_faixa)
        return faixas_completas * valor_faixa
    else:
        return 0