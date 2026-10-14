import pandas as pd
import numpy as np
from datetime import datetime

def trataAtribuicao(baseAtribuicao, baseHoraAtividade, baseVacancia, dataInicioGR, dataFimGR):
    
    baseAtribuicao['E_GESTOR'] = baseAtribuicao['Funcao'].isin(['PROFESSOR/DRE', 'COORDENADOR PEDAGÓGICO', 'COORDENADOR PEDAGÓGICO - SALA ANEXA', 'COORDENADOR PEDAGÓGICO - 2º VÍNCULO', 'DIRETOR', 'DIRETOR - 2º VÍNCULO'])

    duplicados = (
    baseAtribuicao.groupby(['NumFunc', 'NumVinc', 'DataInicio', 'DataFinal'])
    .filter(lambda g: any(g['E_GESTOR']) and any(g['Funcao'] == 'PROFESSOR')))

    cond_remover = (
    (baseAtribuicao['Funcao'] == 'PROFESSOR') &
    baseAtribuicao[['NumFunc', 'NumVinc', 'DataInicio', 'DataFinal']].apply(tuple, axis=1).isin(
        duplicados[['NumFunc', 'NumVinc', 'DataInicio', 'DataFinal']].apply(tuple, axis=1)
    ))

    baseAtribuicao = baseAtribuicao[~cond_remover].copy()

    baseAtribuicao = baseAtribuicao.apply(lambda col: col.str.strip() if col.dtype == 'object' else col)
    baseAtribuicao.loc[baseAtribuicao['DataFinal'] == pd.Timestamp('1753-01-01'), 'DataFinal'] = dataFimGR
    
    baseHoraAtividade = baseHoraAtividade.drop_duplicates(subset=['Func', 'Vinc'])
    baseHoraAtividade = baseHoraAtividade[['Func','Vinc','Tipo']] 
    baseHoraAtividade = baseHoraAtividade.rename(columns={'Func': 'NumFunc', 'Vinc': 'NumVinc', 'Tipo':'HoraAtividade'})

    baseAtribuicao = pd.merge(baseAtribuicao, baseHoraAtividade, on=['NumFunc', 'NumVinc'], how='left')

    baseAtribuicao['CH'] = np.where(
    baseAtribuicao['HoraAtividade'].eq('2002 - HORA ATIVIDADE').fillna(False),
    (baseAtribuicao['TotalCH'] + baseAtribuicao['AdmCH']) * 1.5,
    baseAtribuicao['TotalCH'] + baseAtribuicao['AdmCH'])

    baseAtribuicao.loc[baseAtribuicao['TipoVinculo'].isin(['EFETIVO']),'AtividadeSeap'] = 60
    baseAtribuicao['CH'] = (baseAtribuicao['CH'])/60*baseAtribuicao['AtividadeSeap']
    baseAtribuicao.loc[baseAtribuicao['CargoCarreira'].isin(['PROFESSOR EDUC. BASICA/20 HORAS']),'CH'] = 20
    baseAtribuicao.loc[baseAtribuicao['CargoCarreira'].isin(['PROFESSOR EDUC. BASICA/30 HORAS']),'CH'] = 30
    baseAtribuicao.loc[baseAtribuicao['CargoCarreira'].isin(['PROFESSOR EDUC. BASICA/40 HORAS']),'CH'] = 40
    baseAtribuicao.loc[baseAtribuicao['CargoCarreira'].isin(['PROF. 30 HORAS ANEXO VI LC50/98']),'CH'] = 30

    baseAtribuicao = baseAtribuicao[baseAtribuicao['CargoCarreira'] != 'PERMUTADOS'].copy()

    baseAtribuicao = baseAtribuicao[baseAtribuicao['DataFinal'] >= dataInicioGR].copy()
    baseAtribuicao['DataInicio'] = baseAtribuicao.apply(lambda row: dataInicioGR if row['DataInicio'] < dataInicioGR else row['DataInicio'], axis=1)
    baseAtribuicao['DataFinal'] = baseAtribuicao.apply(lambda row: dataFimGR if row['DataFinal'] > dataFimGR else row['DataFinal'], axis=1)
        
    vacancia = trataVacancia(baseVacancia, dataInicioGR, dataFimGR)
    baseAtribuicao = pd.merge(baseAtribuicao, vacancia, on=['NumFunc', 'NumVinc'], how='left')
       
    baseAtribuicao['DiasVinculo'] =  (baseAtribuicao['DataFinal'] - baseAtribuicao['DataInicio']).dt.days + 1

    vincEfetivos = baseAtribuicao[baseAtribuicao['TipoVinculo']=='EFETIVO']
    vincEfetivos = vincEfetivos.groupby(['NumFunc', 'NumVinc']).agg(DataInicio=('DataInicio', 'min'), DataFinal=('DataFinal', 'max')).reset_index()
    vincEfetivos['DiasVinculoEfetivo'] =  (vincEfetivos['DataFinal'] - vincEfetivos['DataInicio']).dt.days + 1
    vincEfetivos = vincEfetivos[vincEfetivos['DiasVinculoEfetivo'] >= 15].copy()
    vincEfetivos = vincEfetivos[['NumFunc', 'NumVinc', 'DiasVinculoEfetivo']]
    baseAtribuicao = pd.merge(baseAtribuicao, vincEfetivos, on=['NumFunc', 'NumVinc'], how='left')

    vincContratos = baseAtribuicao[baseAtribuicao['TipoVinculo']=='TEMPORÁRIO']
    vincContratos = vincContratos.groupby(['NumFunc', 'NumVinc']).agg(DataInicio=('DataInicio', 'min'), DataFinal=('DataFinal', 'max')).reset_index()
    vincContratos['DiasVinculoContrato'] =  (vincContratos['DataFinal'] - vincContratos['DataInicio']).dt.days + 1
    vincContratos = vincContratos[vincContratos['DiasVinculoContrato'] >= 15].copy()
    vincContratos = vincContratos[['NumFunc', 'NumVinc', 'DiasVinculoContrato']]
    baseAtribuicao = pd.merge(baseAtribuicao, vincContratos, on=['NumFunc', 'NumVinc'], how='left')


    filtro = (
    ((baseAtribuicao['TipoVinculo'] == 'EFETIVO') & (baseAtribuicao['DiasVinculoEfetivo'].notnull())) |
    ((baseAtribuicao['TipoVinculo'] == 'TEMPORÁRIO') & (baseAtribuicao['DiasVinculoContrato'].notnull())))

    baseAtribuicao = baseAtribuicao[filtro]


    baseAtribuicao = baseAtribuicao[baseAtribuicao['DiasVinculo'] > 0].copy()

    def ajustar_periodos(df_periodos, df_vacancias):
        linhas = []

        for _, row in df_periodos.iterrows():

            numfunc = row['NumFunc']
            numvinc = row['NumVinc']
            inicio = row['DataInicio']
            fim = row['DataFinal']

            # Filtra vacâncias do mesmo servidor e vínculo
            vacs = df_vacancias[
                (df_vacancias['NumFunc'] == numfunc) &
                (df_vacancias['NumVinc'] == numvinc) &
                (df_vacancias['DataInicioVacancia'] <= fim) &
                (df_vacancias['DataFinalVacancia'] >= inicio)
            ].sort_values('DataInicioVacancia')

            # Sem vacância → mantém a linha original
            if vacs.empty:
                linhas.append(row.copy())
                continue

            atual_inicio = inicio

            for _, v in vacs.iterrows():

                v_ini = v['DataInicioVacancia']
                v_fim = v['DataFinalVacancia']

                # Vacância cobre todo o período
                if v_ini <= inicio and v_fim >= fim:
                    atual_inicio = None
                    break

                # Existe período antes da vacância
                if v_ini > atual_inicio:

                    novo_fim = min(
                        v_ini - pd.Timedelta(days=1),
                        fim
                    )

                    if novo_fim >= atual_inicio:

                        nova_linha = row.copy()

                        nova_linha['DataInicio'] = atual_inicio
                        nova_linha['DataFinal'] = novo_fim

                        linhas.append(nova_linha)

                # Avança para depois da vacância
                if v_fim + pd.Timedelta(days=1) <= fim:

                    atual_inicio = v_fim + pd.Timedelta(days=1)

                else:

                    atual_inicio = None
                    break

            # Existe período depois da última vacância
            if atual_inicio is not None and atual_inicio <= fim:

                nova_linha = row.copy()

                nova_linha['DataInicio'] = atual_inicio
                nova_linha['DataFinal'] = fim

                linhas.append(nova_linha)

        return pd.DataFrame(linhas).reset_index(drop=True)

    baseAtribuicao = ajustar_periodos(baseAtribuicao, vacancia)
    baseAtribuicao = baseAtribuicao.drop_duplicates(subset=['NumFunc', 'NumVinc', 'DataInicio', 'DataFinal'])

    baseAtribuicao = baseAtribuicao[['DRE', 'Municipio', 'SerieLotacao', 'Lotacao', 'TipoLotacao', 'Nome', 'CPF', 'CodFunc', 'Funcao', 'TipoProcesso', 
                                            'Processo', 'TipoServidor', 'TipoVinculo', 'NumFunc', 'NumVinc', 'CargoCarreira', 'CH', 'DataInicio', 'DataFinal']]
    
    baseAtribuicao['DiasVinculo'] =  (baseAtribuicao['DataFinal'] - baseAtribuicao['DataInicio']).dt.days + 1

    def dias_unicos(grupo):
        periodos = (
            grupo[['DataInicio', 'DataFinal']]
            .dropna()
            .sort_values('DataInicio')
            .itertuples(index=False, name=None)
        )

        total = 0
        inicio_atual = None
        fim_atual = None

        for inicio, fim in periodos:
            if inicio_atual is None:
                inicio_atual = inicio
                fim_atual = fim

            elif inicio <= fim_atual + pd.Timedelta(days=1):
                # Períodos sobrepostos ou consecutivos
                fim_atual = max(fim_atual, fim)

            else:
                # Fecha o período anterior
                total += (fim_atual - inicio_atual).days + 1

                inicio_atual = inicio
                fim_atual = fim

        # Fecha o último período
        if inicio_atual is not None:
            total += (fim_atual - inicio_atual).days + 1

        return total
    
    vinc15Dias = (baseAtribuicao.groupby(['NumFunc', 'NumVinc']).apply(dias_unicos, include_groups=False).rename('DiasVinculoManter').reset_index())
    vinc15Dias = vinc15Dias[vinc15Dias['DiasVinculoManter'] >= 15].copy()
    vinc15Dias['MANTER'] = 'SIM'

    baseAtribuicao = pd.merge(baseAtribuicao, vinc15Dias, how='left', on=['NumFunc', 'NumVinc'])
    baseAtribuicao = baseAtribuicao[baseAtribuicao['MANTER'] == 'SIM']
    baseAtribuicao = baseAtribuicao[baseAtribuicao['CargoCarreira'] != 'MEMBRO DE CONSELHO']

    print(f'\033[92mAtribuição tratada, concluído em ' f'{datetime.now().strftime("%d/%m/%Y %H:%M:%S")}\033[0m')

    return baseAtribuicao

def trataVacancia(baseVancania, dataInicioGR, dataFimGR):
    vacancia = baseVancania.copy()
    vacancia.loc[vacancia['DataFinal'] == pd.Timestamp('1753-01-01'), 'DataFinal'] = dataFimGR
    vacancia = vacancia[vacancia['DataFinal'] >= dataInicioGR].copy()

    vacancia['DataInicial'] = vacancia.apply(lambda row: dataInicioGR if row['DataInicial'] < dataInicioGR else row['DataInicial'], axis=1)
    vacancia['DataFinal'] = vacancia.apply(lambda row: dataFimGR if row['DataFinal'] > dataFimGR else row['DataFinal'], axis=1)
    resultado = vacancia.rename(columns={'Func': 'NumFunc', 'Vinc': 'NumVinc', 'DataInicial':'DataInicioVacancia', 'DataFinal': 'DataFinalVacancia'})
    resultado = resultado[['NumFunc', 'NumVinc', 'DataInicioVacancia', 'DataFinalVacancia','Tipo']]

    resultado = resultado.sort_values(['NumFunc', 'NumVinc', 'Tipo', 'DataInicioVacancia'])



    def unir_periodos(grupo):
        grupo = grupo.sort_values('DataInicioVacancia').reset_index(drop=True)
        grupos_unidos = []
        inicio = grupo.loc[0, 'DataInicioVacancia']
        fim = grupo.loc[0, 'DataFinalVacancia']
        
        for _, linha in grupo.iloc[1:].iterrows():
            if (linha['DataInicioVacancia'] - fim).days <= 1:
                fim = max(fim, linha['DataFinalVacancia'])
            else:
                grupos_unidos.append([inicio, fim])
                inicio = linha['DataInicioVacancia']
                fim = linha['DataFinalVacancia']
        
        grupos_unidos.append([inicio, fim])
        return pd.DataFrame(grupos_unidos, columns=['DataInicioVacancia', 'DataFinalVacancia'])
    
    cols = [c for c in resultado.columns if c not in ['NumFunc', 'NumVinc', 'Tipo']]

    resultado = (resultado.groupby(['NumFunc', 'NumVinc', 'Tipo'], group_keys=False).apply(lambda g: unir_periodos(g[cols]).assign(NumFunc=g.name[0], 
                                                                                                                                   NumVinc=g.name[1],
                                                                                                                                   Tipo=g.name[2]), include_groups=False)
                                                                                                                                   .reset_index(drop=True))
    
    resultado['DiasVacancia'] =  (resultado['DataFinalVacancia'] - resultado['DataInicioVacancia']).dt.days + 1
    
    return resultado 

def tetoGr(baseAtribuicao):
     # Criar um dicionário para armazenar os contratos por CPF
    contratos_cpf = {}
    for _, row in baseAtribuicao.iterrows():
        cpf = str(row["CPF"])  # Garantir que CPF seja tratado como string
        if cpf not in contratos_cpf:
            contratos_cpf[cpf] = []
        contratos_cpf[cpf].append((row["DataInicio"], row["DataFinal"], row["CH"]))

    # Lista para armazenar os resultados finais
    resultados_cpf = []

    # Processar cada CPF separadamente
    for cpf, contratos in contratos_cpf.items():
        # Obter todas as datas únicas relevantes
        datas_unicas = sorted(set([ini for ini, _, _ in contratos] + [fim + pd.Timedelta(days=1) for _, fim, _ in contratos]))

        # Criar os intervalos únicos corretamente
        periodos = [(datas_unicas[i], datas_unicas[i+1] - pd.Timedelta(days=1)) for i in range(len(datas_unicas)-1)]

        # Calcular a carga horária para cada período único
        for inicio, fim in periodos:
            carga_total = sum(ch for ini, f, ch in contratos if ini <= inicio and f >= fim)
            resultados_cpf.append((cpf, inicio, fim, carga_total))

    # Criar um DataFrame com os resultados organizados
    df_resultado = pd.DataFrame(resultados_cpf, columns=["CPF", "DataInicio", "DataFinal", "CH"])
    df_resultado['Dias'] =  (df_resultado['DataFinal'] - df_resultado['DataInicio']).dt.days + 1
    df_resultado["CH"] = df_resultado["CH"].apply(lambda x: 30 if x > 30 else x)
    df_resultado['Percentual'] = (df_resultado['Dias']/302)*(df_resultado['CH']/30)
    
    df_resultado = df_resultado.groupby(['CPF']).agg(PercentualGRServidor=('Percentual', 'sum')).reset_index()
    df_resultado['CPF'] = df_resultado['CPF'].astype(float)

    print(f'\033[92mTeto GR definido, concluído em ' f'{datetime.now().strftime("%d/%m/%Y %H:%M:%S")}\033[0m')
    return df_resultado

def proporcaoVinculo(grupo):
    grupo = grupo.copy()
    grupo['Peso'] = grupo['DiasVinculo'] * grupo['CH']
    somaPeso = grupo.groupby(['NumFunc']).agg(PesoTotal=('Peso', 'sum')).reset_index()
    grupo = pd.merge(grupo, somaPeso, how='left', on='NumFunc')
    grupo['PercentualGRVinculo'] = grupo['Peso']/grupo['PesoTotal']*grupo['PercentualGRServidor']

    grupo = grupo[['DRE', 'Municipio', 'SerieLotacao', 'Lotacao', 'TipoLotacao', 'Nome', 'CPF', 'TipoVinculo', 'DataInicio', 'DataFinal', 
                                     'NumFunc', 'NumVinc', 'CargoCarreira', 'CH', 'DiasVinculo', 'CargoGR', 'PercentualGRVinculo']]
    
 
    grupo['LotacaoGR'] = np.select([grupo['TipoLotacao'] == 'ÓRGÃO CENTRAL', grupo['TipoLotacao'] == 'DRE'], 
                                   [        'ÓRGÃO CENTRAL', grupo['DRE']], default=grupo['SerieLotacao'].astype(str))
   
    grupo['LotacaoGR'] = grupo['LotacaoGR'].replace('DRE TANGARA DA SERRA', 'DRE TANGARÁ DA SERRA')
    grupo['LotacaoGR'] = grupo['LotacaoGR'].replace('DRE JUINA', 'DRE JUÍNA')
    grupo['LotacaoGR'] = grupo['LotacaoGR'].replace('DRE CACERES', 'DRE CÁCERES')
    grupo['LotacaoGR'] = grupo['LotacaoGR'].replace('DRE BARRA DO GARCAS', 'DRE BARRA DO GARÇAS')

    grupo['DescricaoLotacaoGR'] = np.select([grupo['TipoLotacao'] == 'ÓRGÃO CENTRAL', grupo['TipoLotacao'] == 'DRE', grupo['TipoLotacao'].isin(['EDUCAÇÃO ESPECIAL', 'ESCOLA INDÍGENA'])], 
                                   [        'ÓRGÃO CENTRAL', grupo['DRE'], grupo['DRE']], default=grupo['Lotacao'].astype(str))


    grupo = grupo.groupby(['LotacaoGR', 'DescricaoLotacaoGR', 'Nome', 'CPF', 'NumFunc', 'NumVinc', 'TipoVinculo', 'CargoCarreira', 'CargoGR', 'DataInicio', 'DataFinal', 'CH']).agg(
        PercentualGRVinculo=('PercentualGRVinculo', 'sum')).reset_index()

    
    grupo = grupo.rename(columns={'NumFunc': 'Func', 'NumVinc': 'Vinc'})
    print(f'\033[92mDistribuição % GR nos vínculos feito, concluído em ' f'{datetime.now().strftime("%d/%m/%Y %H:%M:%S")}\033[0m')
    return grupo

def calcular_periodo_unico(df, col_data_ini=None, col_data_fim=None):

    # Ordena as datas
    grupo = df.sort_values(by=col_data_ini).reset_index(drop=True)

    # Lista para armazenar intervalos fundidos
    intervalos = []

    for _, linha in grupo.iterrows():
        ini, fim = linha[col_data_ini], linha[col_data_fim]
        if pd.isna(ini) or pd.isna(fim):
            continue  # Ignora linhas com datas nulas

        if not intervalos:
            intervalos.append([ini, fim])
        else:
            ult_ini, ult_fim = intervalos[-1]
            if ini <= ult_fim:  # sobreposição
                intervalos[-1][1] = max(ult_fim, fim)
            else:
                intervalos.append([ini, fim])

    # Soma os dias únicos
    total_dias = sum((fim - ini).days + 1 for ini, fim in intervalos)
    return total_dias


def definirCargoGR(baseAtribuicao, aula, baseDE, baseSEAP, dataInicioGR, dataFimGR):

    baseDE.loc[baseDE['DataFinal'] == pd.Timestamp('1753-01-01'), 'DataFinal'] = dataFimGR
    baseDE['DataInicial'] = baseDE.apply(lambda row: dataInicioGR if row['DataInicial'] < dataInicioGR else row['DataInicial'], axis=1)
    baseDE['DataFinal'] = baseDE.apply(lambda row: dataFimGR if row['DataFinal'] > dataFimGR else row['DataFinal'], axis=1)
    baseDE = baseDE[baseDE['DataFinal'] >= dataInicioGR].copy()
    resultadoDE = baseDE.groupby('Func', group_keys=False).apply(calcular_periodo_unico, col_data_ini='DataInicial', col_data_fim='DataFinal', include_groups=False).reset_index().rename(columns={0: 'DiasGestao'})
     
    baseSEAP = baseSEAP[baseSEAP['descr_cargo'].str.contains('DGA', na=False)]
    baseSEAP.loc[baseSEAP['dtfim'].isna(), 'dtfim'] = dataFimGR
    baseSEAP.loc[baseSEAP['dtini'] < dataInicioGR, 'dtini'] = dataInicioGR
    baseSEAP.loc[baseSEAP['dtfim'] > dataFimGR, 'dtfim'] = dataFimGR
    baseSEAP = baseSEAP[baseSEAP['dtfim'] >= dataInicioGR].copy()
    resultadoSEAP = baseSEAP.groupby('numfunc').apply(calcular_periodo_unico, col_data_ini='dtini', col_data_fim='dtfim', include_groups=False).reset_index().rename(columns={0: 'DiasGestao'})
    resultadoSEAP = resultadoSEAP.rename(columns={'numfunc': 'Func'})
    
   
    gestaoContrato = baseAtribuicao[baseAtribuicao['Funcao'].isin(['COORDENADOR/DESIGNADO', 'DIRETOR DESIGNADO/PROFESSOR', 'SECRETÁRIO/DESIGNADO'])]
    gestaoContrato = gestaoContrato.groupby('NumFunc').apply(calcular_periodo_unico, col_data_ini='DataInicio', col_data_fim='DataFinal', include_groups=False).reset_index().rename(columns={0: 'DiasGestao'})
    gestaoContrato = gestaoContrato.rename(columns={'NumFunc': 'Func'})
    
    resultadoGestao = pd.concat([resultadoDE, resultadoSEAP, gestaoContrato])
    resultadoGestao = (resultadoGestao.groupby('Func', as_index=False)['DiasGestao'].sum())

    resultadoGestao = resultadoGestao[resultadoGestao['DiasGestao'] >= 180]

    baseAtribuicao = pd.merge(baseAtribuicao, resultadoGestao, how='left', left_on='NumFunc', right_on='Func')
   
    substituicoes = {
    'DGA-1': 'CIVIS E MILITARES LOTADOS NA SEDUC',
    'DGA-2': 'CIVIS E MILITARES LOTADOS NA SEDUC',
    'DGA-3': 'CIVIS E MILITARES LOTADOS NA SEDUC',
    'DGA-4': 'CIVIS E MILITARES LOTADOS NA SEDUC',
    'DGA-5': 'CIVIS E MILITARES LOTADOS NA SEDUC',
    'DGA-6': 'CIVIS E MILITARES LOTADOS NA SEDUC',
    'PRESIDENTE CONSELHO ESTADUAL DE EDUCAÇÃO': 'GESTOR',
    '15019 - APOIO TECNICO ESP CIVICO MILITAR 01': 'CIVIS E MILITARES LOTADOS NA SEDUC',
    '15020 - APOIO TECNICO ESP CIVICO MILITAR 02': 'CIVIS E MILITARES LOTADOS NA SEDUC',
    '15021 - INSPETOR TECNICO CIVICO MILITAR': 'CIVIS E MILITARES LOTADOS NA SEDUC',
    'AGENTE UNIVERSITARIO LC 321/2008 - UNEMAT': 'CIVIS E MILITARES LOTADOS NA SEDUC',
    'AGES - AGENTE DESENVOLV. ECON. E SOCIAL': 'CIVIS E MILITARES LOTADOS NA SEDUC',
    'ANALISTA ADMINISTRATIVO': 'CIVIS E MILITARES LOTADOS NA SEDUC',
    'ANALISTA DE DESENVOLVIMENTO ECONÔMICO E SOCIAL': 'CIVIS E MILITARES LOTADOS NA SEDUC',
    'APOIO TÉCNICO ESP CÍVICO MILITAR 01': 'CIVIS E MILITARES LOTADOS NA SEDUC',
    'APOIO TÉCNICO ESP CÍVICO MILITAR 02': 'CIVIS E MILITARES LOTADOS NA SEDUC',
    'FUNCAO DGA 5 LC/266': 'CIVIS E MILITARES LOTADOS NA SEDUC',
    'GESTOR GOVERNAMENTAL': 'CIVIS E MILITARES LOTADOS NA SEDUC',
    'PROC. DO ESTADO EM ESTAGIO PROBAT': 'CIVIS E MILITARES LOTADOS NA SEDUC',
    'INSPETOR CIVICO MILITAR - NÍVEL SUPORTE E APOIO': 'CIVIS E MILITARES LOTADOS NA SEDUC',
    'MEMBRO DE CONSELHO': 'CIVIS E MILITARES LOTADOS NA SEDUC',
    'PERMUTADOS': 'CIVIS E MILITARES LOTADOS NA SEDUC',
    'PROFESSOR UNEMAT LC 534/2014': 'CIVIS E MILITARES LOTADOS NA SEDUC',
    'TEC. DESENVOL. ECON. SOCIAL  40 HRS': 'CIVIS E MILITARES LOTADOS NA SEDUC',
    'TECNICO AREA INSTR. - 40H': 'CIVIS E MILITARES LOTADOS NA SEDUC',
    'TÉCNICO ADMINISTRATIVO L 10052': 'CIVIS E MILITARES LOTADOS NA SEDUC',
    'TÉCNICO DESENV.ECO.SOC L 10177/14': 'CIVIS E MILITARES LOTADOS NA SEDUC',
    'ANALISTA FUNDIARIO E AGRARIO L 10042': 'CIVIS E MILITARES LOTADOS NA SEDUC',
    'ANALISTA DE TECNOLOGIA DA INFORMACAO JUNIOR': 'CIVIS E MILITARES LOTADOS NA SEDUC',
    'ASSESSOR JURIDICO(A)': 'CIVIS E MILITARES LOTADOS NA SEDUC',
    'CONTR.TEMP.FUNCAO PROF. HABILITADO': 'PROFESSOR',
    'CONTR.TEMP.FUNCAO PROF. NAO HABILIT': 'PROFESSOR',
    'ESPECIALISTA': 'PROFESSOR',
    'PROF. 30 HORAS ANEXO VI LC50/98': 'PROFESSOR',
    'PROFESSOR EDUC. BASICA/20 HORAS': 'PROFESSOR',
    'PROFESSOR EDUC. BASICA/30 HORAS': 'PROFESSOR',
    'PROFESSOR EDUC. BASICA/40 HORAS': 'PROFESSOR',
    'APOIO ADM. EDUCACIONAL-ELEMENTAR': 'TAE/AAE',
    'APOIO ADMIN PROFISSIONALIZADO': 'TAE/AAE',
    'AUXILIAR DE ADMINISTRAÇÃO': 'TAE/AAE',
    'AUXILIAR DE SERVIÇOS GERAIS I': 'TAE/AAE',
    'PORTEIRO': 'TAE/AAE',
    'VIGIA': 'TAE/AAE',
    'TECNICO ADMIN PROFISSIONALIZADO': 'TAE/AAE',
    'TECNICO ADMINISTRATIVO EDUCACIONAL': 'TAE/AAE',
    'AGENTE ADMINISTRAÇÃO':'TAE/AAE',
    'OFICIAL DE GESTAO CIVICO-MILITAR': 'CIVIS E MILITARES LOTADOS NA SEDUC',
    'OFICIAL DE GESTAO EDUCACIONAL MILITAR': 'CIVIS E MILITARES LOTADOS NA SEDUC',
    'MOTORISTA': 'CIVIS E MILITARES LOTADOS NA SEDUC',
    'ANALISTA DE TECNOLOGIA DA INFORMAÇÃO SENIOR - INTERINO': 'CIVIS E MILITARES LOTADOS NA SEDUC',
    'MONITOR': 'CIVIS E MILITARES LOTADOS NA SEDUC',
    'TENENTE CORONEL LC 541/2014': 'CIVIS E MILITARES LOTADOS NA SEDUC',
    }

    baseAtribuicao['CargoCarreira'] = baseAtribuicao['CargoCarreira'].str.strip()
    baseAtribuicao['CargoGR'] = np.where(baseAtribuicao['DiasGestao'].notna(),'GESTOR', baseAtribuicao['CargoCarreira'].map(substituicoes))

    professorEmAula = baseAtribuicao[baseAtribuicao['CargoGR'] == 'PROFESSOR']

    aula = aula[aula['DataFinal'] >= dataInicioGR]
    aula.loc[aula['DataInicial'] < dataInicioGR, 'DataInicial'] = dataInicioGR
    aula.loc[aula['DataFinal'] > dataFimGR, 'DataFinal'] = dataFimGR
    
    emAula = aula.drop_duplicates(subset=['CodigoSEAP', 'VinculoSEAP', 'DataInicial', 'DataFinal'])
    emAula = emAula[['CodigoSEAP', 'VinculoSEAP', 'DataInicial', 'DataFinal']]
    emAula = emAula.rename(columns={'DataInicial': 'DataInicialAula', 'DataFinal': 'DataFinalAula'})

    professorEmAula = pd.merge(professorEmAula, emAula, how='left', left_on=['NumFunc', 'NumVinc'], right_on=['CodigoSEAP', 'VinculoSEAP'])

    professorEmAula.loc[(professorEmAula['DataInicialAula'] <= professorEmAula['DataInicio']) & (professorEmAula['DataFinalAula'] >= professorEmAula['DataFinal']), 'Em Sala'] = 'SIM'
    professorEmAula = professorEmAula[['NumFunc', 'NumVinc', 'DataInicio', 'DataFinal', 'Em Sala']]
    professorEmAula = professorEmAula.drop_duplicates(subset=['NumFunc', 'NumVinc', 'DataInicio', 'DataFinal'])
    
    baseAtribuicao = pd.merge(baseAtribuicao, professorEmAula, how='left', on=['NumFunc', 'NumVinc', 'DataInicio', 'DataFinal'])

    baseAtribuicao.loc[(baseAtribuicao['CargoGR'] == 'PROFESSOR') & (baseAtribuicao['Em Sala'] == 'SIM'), 'CargoGR'] = 'PROFESSOR EM REGÊNCIA'
    baseAtribuicao.loc[(baseAtribuicao['CargoGR'] == 'PROFESSOR') & (baseAtribuicao['Em Sala'].isna()), 'CargoGR'] = 'PROFESSOR FORA DE REGÊNCIA'
    baseAtribuicao = baseAtribuicao[[ 'DRE', 'Municipio', 'SerieLotacao', 'Lotacao', 'TipoLotacao', 'Nome', 'CPF', 'TipoVinculo', 'DataInicio', 'DataFinal',
                                     'NumFunc', 'NumVinc', 'CargoCarreira', 'CH', 'DiasVinculo', 'CargoGR']]
    
    baseAtribuicao["CH"] = baseAtribuicao["CH"].apply(lambda x: 30 if x > 30 else x)  
    baseAtribuicao['CPF'] = baseAtribuicao['CPF'].astype(float)

    print(f'\033[92mCargo GR definido, concluído em ' f'{datetime.now().strftime("%d/%m/%Y %H:%M:%S")}\033[0m')
    return baseAtribuicao


def valorGRBase(row):

    if row['CargoGR'] in ['PROFESSOR EM REGÊNCIA', 'GESTOR', 'PROFESSOR FORA DE REGÊNCIA']:

        return 11015.44 * row['PercentualGRVinculo'] * 1.054

    elif row['CargoGR'] == 'TAE/AAE':

        return 5507.72 * row['PercentualGRVinculo'] * 1.054

    elif row['CargoGR'] == 'CIVIS E MILITARES LOTADOS NA SEDUC':

        if row['CargoCarreira'] == 'ANALISTA DE DESENVOLVIMENTO ECONÔMICO E SOCIAL':
            return 7845.50 / 2 * row['PercentualGRVinculo'] * 1.054

        elif row['CargoCarreira'] == 'TEC. DESENVOL. ECON. SOCIAL  40 HRS':
            return 4134.55 / 2 * row['PercentualGRVinculo'] * 1.054

        elif row['CargoCarreira'] == 'TÉCNICO DESENV.ECO.SOC L 10177/14':
            return 4134.55 / 2 * row['PercentualGRVinculo'] * 1.054

        elif row['CargoCarreira'] == '15021 - INSPETOR TECNICO CIVICO MILITAR':
            return 6421.62 / 2 * row['PercentualGRVinculo'] * 1.054

        elif row['CargoCarreira'] == 'INSPETOR CIVICO MILITAR - NÍVEL SUPORTE E APOIO':
            return 3944.05 / 2 * row['PercentualGRVinculo'] * 1.054

        elif row['CargoCarreira'] == '15019 - APOIO TECNICO ESP CIVICO MILITAR 01':
            return 8934.43 / 2 * row['PercentualGRVinculo'] * 1.054

        elif row['CargoCarreira'] == 'APOIO TÉCNICO ESP CÍVICO MILITAR 01':
            return 8934.43 / 2 * row['PercentualGRVinculo'] * 1.054

        elif row['CargoCarreira'] == '15020 - APOIO TECNICO ESP CIVICO MILITAR 02':
            return 8934.43 / 2 * row['PercentualGRVinculo'] * 1.054

        elif row['CargoCarreira'] == 'APOIO TÉCNICO ESP CÍVICO MILITAR 02':
            return 8934.43 / 2 * row['PercentualGRVinculo'] * 1.054

        elif row['CargoCarreira'] == 'AGENTE UNIVERSITARIO LC 321/2008 - UNEMAT':
            return 8388.38 / 2 * row['PercentualGRVinculo'] * 1.054

        elif row['CargoCarreira'] == 'ANALISTA ADMINISTRATIVO':
            return 7845.50 / 2 * row['PercentualGRVinculo'] * 1.054

        elif row['CargoCarreira'] == 'ANALISTA FUNDIARIO E AGRARIO L 10042':
            return 9956.16 / 2 * row['PercentualGRVinculo'] * 1.054

        elif row['CargoCarreira'] == 'ANALISTA DE TECNOLOGIA DA INFORMACAO JUNIOR':
            return 7845.50 / 2 * row['PercentualGRVinculo'] * 1.054

        elif row['CargoCarreira'] == 'ASSESSOR JURIDICO(A)':
            return 8934.44 / 2 * row['PercentualGRVinculo'] * 1.054

        elif row['CargoCarreira'] == 'DGA-1':
            return 29118.13 / 2 * row['PercentualGRVinculo'] * 1.054

        elif row['CargoCarreira'] == 'DGA-2':
            return 14957.21 / 2 * row['PercentualGRVinculo'] * 1.054

        elif row['CargoCarreira'] == 'DGA-3':
            return 10948.67 / 2 * row['PercentualGRVinculo'] * 1.054

        elif row['CargoCarreira'] == 'DGA-4':
            return 8934.44 / 2 * row['PercentualGRVinculo'] * 1.054

        elif row['CargoCarreira'] == 'DGA-5':
            return 6421.63 / 2 * row['PercentualGRVinculo'] * 1.054

        elif row['CargoCarreira'] == 'DGA-6':
            return 4957.81 / 2 * row['PercentualGRVinculo'] * 1.054

        elif row['CargoCarreira'] == 'PROC. DO ESTADO EM ESTAGIO PROBAT':
            return 37745.52 / 2 * row['PercentualGRVinculo'] * 1.054

        elif row['CargoCarreira'] == 'OFICIAL DE GESTAO EDUCACIONAL MILITAR':
            return 9416.89 / 2 * row['PercentualGRVinculo']

        elif row['CargoCarreira'] == 'MONITOR':
            return 6768.39 / 2 * row['PercentualGRVinculo']
        
        elif row['CargoCarreira'] == 'OFICIAL DE GESTAO CIVICO-MILITAR':
            return 9416.89 / 2 * row['PercentualGRVinculo']

        elif row['CargoCarreira'] == 'TENENTE CORONEL LC 541/2014':
            return  10188.64 / 2 * row['PercentualGRVinculo']

        elif row['CargoCarreira'] == 'ANALISTA DE TECNOLOGIA DA INFORMAÇÃO SENIOR - INTERINO':
            return  19588.82 / 2 * row['PercentualGRVinculo']

    return 0