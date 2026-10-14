import pandas as pd
import json

def absenteismoWebPonto(basePessoal , baseWebPonto):
    # Faz uma cópia real do DataFrame após o filtro para evitar SettingWithCopyWarning
    baseWebPontoFrequencia = baseWebPonto[
        baseWebPonto['MF'].isin([
            '01 - ATESTADO DE COMPARECIMENTO CONSULTA OU AFASTAMENTO MÉDICO ATÉ 03 DIAS',
            '14 - DOAÇÃO DE SANGUE'
        ])
    ].copy()

    baseWebPontoFrequencia = baseWebPontoFrequencia[['LOGIN', 'DataFrequencia', 'MF']]

    # Calcular horas por período
    baseWebPonto['HorasManha'] = (baseWebPonto['SaidaManha'] - baseWebPonto['EntradaManha']).dt.total_seconds() / 3600
    baseWebPonto['HorasTarde'] = (baseWebPonto['SaidaTarde'] - baseWebPonto['EntradaTarde']).dt.total_seconds() / 3600
    baseWebPonto['HorasNoite'] = (baseWebPonto['SaidaNoite'] - baseWebPonto['EntradaNoite']).dt.total_seconds() / 3600

    # Soma total de horas no dia
    baseWebPonto['TotalHorasDia'] = baseWebPonto[['HorasManha', 'HorasTarde', 'HorasNoite']].sum(axis=1, skipna=True)
    baseWebPonto = baseWebPonto.groupby(['LOGIN', 'DataFrequencia']).agg(TotalHorasDia=('TotalHorasDia', 'sum')).reset_index()


    baseWebPonto = pd.merge(baseWebPontoFrequencia, baseWebPonto, on=['LOGIN', 'DataFrequencia'], how='left')

    # Renomear e filtrar por ausência de horas
    baseWebPonto = baseWebPonto[baseWebPonto['TotalHorasDia'] == 0]
    
    baseWebPonto = baseWebPonto.rename(columns={'LOGIN': 'CPF', 'MF': 'TIPO'})
    baseWebPonto = baseWebPonto[['CPF', 'DataFrequencia', 'TIPO']]

    baseWebPonto = pd.merge(baseWebPonto, basePessoal, on=['CPF'], how='left')
    baseWebPonto = baseWebPonto[(baseWebPonto['DataFrequencia'] >= baseWebPonto['DataInicio']) & (baseWebPonto['DataFrequencia'] <= baseWebPonto['DataFinal'])].copy()
    baseWebPonto = baseWebPonto[['NumFunc', 'NumVinc', 'DataFrequencia', 'TIPO']]
    baseWebPonto = baseWebPonto.rename(columns={'NumFunc': 'Func', 'NumVinc': 'Vinc', 'DataFrequencia':'DataInicial', 'TIPO':'Tipo'})
    baseWebPonto['DataFinal'] = baseWebPonto['DataInicial']

    return baseWebPonto



def absenteismoLicencasAfastamentos(baseLicencasAfastamentos, dataInicioGR, dataFimGR):
    baseLicencasAfastamentos.loc[baseLicencasAfastamentos['DataFinal'] == pd.Timestamp('1753-01-01'), 'DataFinal'] = dataFimGR

    baseLicencasAfastamentos = baseLicencasAfastamentos[baseLicencasAfastamentos['DataFinal'] >= dataInicioGR].copy()
    baseLicencasAfastamentos['DataInicial'] = baseLicencasAfastamentos.apply(lambda row: dataInicioGR if row['DataInicial'] < dataInicioGR else row['DataInicial'], axis=1)
    baseLicencasAfastamentos['DataFinal'] = baseLicencasAfastamentos.apply(lambda row: dataFimGR if row['DataFinal'] > dataFimGR else row['DataFinal'], axis=1)

    baseLicencasAfastamentos['DiasAfastamentoGR'] =  (baseLicencasAfastamentos['DataFinal'] - baseLicencasAfastamentos['DataInicial']).dt.days + 1
    baseLicencasAfastamentos = baseLicencasAfastamentos[baseLicencasAfastamentos['DiasAfastamentoGR'] > 0]
    baseLicencasAfastamentos = baseLicencasAfastamentos[['Func', 'Vinc', 'DataInicial', 'DataFinal', 'Tipo']]

    return baseLicencasAfastamentos


def absenteismoFrequencias(baseWebPonto, baseFrequencias):

    for col in ['EntradaManha', 'SaidaManha', 'EntradaTarde', 'SaidaTarde', 'EntradaNoite', 'SaidaNoite']:
        baseWebPonto[col] = pd.to_datetime(baseWebPonto[col], format='%H:%M:%S', errors='coerce')

    # Calcular horas por período
    baseWebPonto['HorasManha'] = (baseWebPonto['SaidaManha'] - baseWebPonto['EntradaManha']).dt.total_seconds() / 3600
    baseWebPonto['HorasTarde'] = (baseWebPonto['SaidaTarde'] - baseWebPonto['EntradaTarde']).dt.total_seconds() / 3600
    baseWebPonto['HorasNoite'] = (baseWebPonto['SaidaNoite'] - baseWebPonto['EntradaNoite']).dt.total_seconds() / 3600

    # Soma total de horas no dia
    baseWebPonto['TotalHorasDia'] = baseWebPonto[['HorasManha', 'HorasTarde', 'HorasNoite']].sum(axis=1, skipna=True)
    baseWebPonto = baseWebPonto.groupby(['LOGIN', 'DataFrequencia'])['TotalHorasDia'].sum().reset_index()

    baseWebPonto = pd.merge(baseWebPonto, baseFrequencias, left_on=['LOGIN', 'DataFrequencia'], right_on=['CPF', 'DataInicial'], how='left')

    baseWebPonto = baseWebPonto[baseWebPonto['TotalHorasDia'] == 0].copy()
    baseWebPonto = baseWebPonto[baseWebPonto['Tipo'].notna()].copy()
    baseWebPonto = baseWebPonto[['Func', 'Vinc', 'DataInicial', 'DataFinal', 'Tipo']]

    return baseWebPonto


def absenteismoGeral(grupoEleitos, absenteismoWebPonto, baseLicencas, baseFrequencia): 
    baseAbs = pd.concat([absenteismoWebPonto, baseLicencas, baseFrequencia])

    baseAbs = baseAbs.drop_duplicates(subset=['Func', 'Vinc', 'Tipo', 'DataInicial', 'DataFinal'])
    baseAbs['Tipo'] = baseAbs['Tipo'].str.replace(r'^\d+\s*-\s*', '', regex=True)


    def manter_licencas_validas(df):
        resultado = []
        for _, group in df.groupby(['Func', 'Vinc']):
            # Separar as licenças do tipo específico "01"
            licencas_tipo_01 = group[group['Tipo'].isin([
                'ATESTADO DE COMPARECIMENTO CONSULTA OU AFASTAMENTO MÉDICO ATÉ 03 DIAS', 'DOAÇÃO DE SANGUE'])]

            # Separar as licenças de outros tipos
            licencas_outras = group[~group['Tipo'].isin([
            'ATESTADO DE COMPARECIMENTO CONSULTA OU AFASTAMENTO MÉDICO ATÉ 03 DIAS','DOAÇÃO DE SANGUE'])]

            # Manter todas as licenças que não são do tipo 01
            resultado.extend(licencas_outras.to_dict(orient='records'))

            # Verificar se cada licença do tipo 01 não está completamente dentro de outra
            for _, row in licencas_tipo_01.iterrows():
                if not any((row['DataInicial'] >= l['DataInicial']) and (row['DataFinal'] <= l['DataFinal']) for _, l in licencas_outras.iterrows()):
                    resultado.append(row.to_dict())

        return pd.DataFrame(resultado)
    
    baseAbs = manter_licencas_validas(baseAbs)
    eleitos = grupoEleitos.rename(columns={'NumFunc': 'Func', 'NumVinc':'Vinc'})

    eleitosParaAbs = eleitos[['Func', 'Vinc', 'DataInicio', 'DataFinal']]
    eleitosParaAbs = eleitosParaAbs.rename(columns={'DataInicio': 'DataInicioAtribuicao', 'DataFinal':'DataFinalAtribuicao'})

    baseAbs = pd.merge(baseAbs, eleitosParaAbs, on=['Func', 'Vinc'], how='left')
    baseAbs = baseAbs[((baseAbs['Tipo'] == 'ARC - AGUARDANDO REGULARIZAÇÃO DO CARGO') & 
                       (baseAbs['DataInicial'] >= baseAbs['DataInicioAtribuicao']) & 
                       (baseAbs['DataFinal'] <= baseAbs['DataFinalAtribuicao'])) | 
                       (baseAbs['Tipo'] != 'ARC - AGUARDANDO REGULARIZAÇÃO DO CARGO')]

    baseAbs = baseAbs[['Func', 'Vinc', 'Tipo', 'DataInicial', 'DataFinal']]
    baseAbs = baseAbs.drop_duplicates(subset=['Func', 'Vinc', 'Tipo', 'DataInicial', 'DataFinal'])
    
    absenteismoJson = baseAbs.to_dict(orient='records')

    def calcular_dias_ausentes(df):
        # Ordenar as datas para facilitar a junção de períodos sobrepostos
        df = df.sort_values(by=['DataInicial', 'DataInicial'])

        # Lista para armazenar os períodos consolidados
        periodos_consolidados = []

        # Variáveis para rastrear o início e o fim do período atual
        inicio_periodo = None
        fim_periodo = None

        # Iterar pelas linhas e consolidar os períodos
        for i, row in df.iterrows():
            if inicio_periodo is None:
                # Definir o primeiro período
                inicio_periodo = row['DataInicial']
                fim_periodo = row['DataFinal']
            else:
                # Se o período atual se sobrepõe ao anterior, estenda o período
                if row['DataInicial'] <= fim_periodo:
                    fim_periodo = max(fim_periodo, row['DataFinal'])
                else:
                    # Se não houver sobreposição, finalize o período anterior e inicie um novo
                    periodos_consolidados.append((inicio_periodo, fim_periodo))
                    inicio_periodo = row['DataInicial']
                    fim_periodo = row['DataFinal']

        # Adicionar o último período
        if inicio_periodo is not None:
            periodos_consolidados.append((inicio_periodo, fim_periodo))

        # Criar um conjunto para armazenar os dias únicos consolidados
        dias_unicos = set()

        # Adicionar os dias de cada período consolidado ao conjunto
        for inicio, fim in periodos_consolidados:
            dias_unicos.update(pd.date_range(inicio, fim))

        return len(dias_unicos)

    absenteismoCompilado = baseAbs.groupby(['Func', 'Vinc']).apply(calcular_dias_ausentes, include_groups=False).reset_index(name='DiasAbsenteismo')

    eleitos = grupoEleitos.rename(columns={'NumFunc': 'Func', 'NumVinc':'Vinc'})
    eleitos = pd.merge(eleitos, absenteismoCompilado, on=['Func', 'Vinc'], how='left')
    
    eleitos['DiasAbsenteismo'] = eleitos['DiasAbsenteismo'].fillna(0)

    def encontrar_json_por_func_vinc(num_func, num_vinc):
        return [item for item in absenteismoJson if item['Func'] == num_func and item['Vinc'] == num_vinc]
    
    eleitos['ListaAbsenteismo'] = eleitos.apply(lambda row: encontrar_json_por_func_vinc(row['Func'], row['Vinc']), axis=1)

    def remover_informacao_dos_jsons(json_list, chave_para_remover):
        for item in json_list:
            item.pop(chave_para_remover, None)  # Remove a chave, se existir
        return json_list

    eleitos['ListaAbsenteismo'] = eleitos['ListaAbsenteismo'].apply(lambda x: remover_informacao_dos_jsons(x, "Func"))
    eleitos['ListaAbsenteismo'] = eleitos['ListaAbsenteismo'].apply(lambda x: remover_informacao_dos_jsons(x, "Vinc"))

    eleitos["ListaAbsenteismo"] = eleitos["ListaAbsenteismo"].apply(
    lambda lista: json.dumps([
        {
            **d,
            "DataInicial": d["DataInicial"].strftime("%Y-%m-%d %H:%M:%S"),
            "DataFinal": d["DataFinal"].strftime("%Y-%m-%d %H:%M:%S")
        }
        for d in lista
    ], ensure_ascii=False))

    return eleitos


def pontuacaoAbsenteismo(row):
    if row['CargoGR'] in ['PROFESSOR EM REGÊNCIA', 'GESTOR', 'PROFESSOR FORA DE REGÊNCIA']:
        if row['DiasAbsenteismo'] == 0:
            return 300
        elif row['DiasAbsenteismo'] in [1, 2]:
            return 270
        elif row['DiasAbsenteismo'] in [3, 4]:
            return 240
        elif row['DiasAbsenteismo'] in [5, 6]:
            return 210
        elif row['DiasAbsenteismo'] in [7, 8]:
            return 180
        elif row['DiasAbsenteismo'] in [9, 10]:
            return 150
        elif row['DiasAbsenteismo'] in [11, 12]:
            return 120
        elif row['DiasAbsenteismo'] in [13, 14]:
            return 90
        elif row['DiasAbsenteismo'] in [15, 16]:
            return 60
        elif row['DiasAbsenteismo'] in [17, 18]:
            return 30
        elif row['DiasAbsenteismo'] in [19, 20]:
            return 0
        elif row['DiasAbsenteismo'] in [21, 22]:
            return -30
        elif row['DiasAbsenteismo'] in [23, 24]:
            return -60
        elif row['DiasAbsenteismo'] in [25, 26]:
            return -90
        elif row['DiasAbsenteismo'] in [27, 28]:
            return -120
        elif row['DiasAbsenteismo'] in [29, 30]:
            return -150
        else:
            return -150
    else:
        if row['DiasAbsenteismo'] == 0:
            return 450
        elif row['DiasAbsenteismo'] in [1, 2]:
            return 405
        elif row['DiasAbsenteismo'] in [3, 4]:
            return 360
        elif row['DiasAbsenteismo'] in [5, 6]:
            return 315
        elif row['DiasAbsenteismo'] in [7, 8]:
            return 270
        elif row['DiasAbsenteismo'] in [9, 10]:
            return 225
        elif row['DiasAbsenteismo'] in [11, 12]:
            return 180
        elif row['DiasAbsenteismo'] in [13, 14]:
            return 135
        elif row['DiasAbsenteismo'] in [15, 16]:
            return 90
        elif row['DiasAbsenteismo'] in [17, 18]:
            return 45
        elif row['DiasAbsenteismo'] in [19, 20]:
            return 0
        elif row['DiasAbsenteismo'] in [21, 22]:
            return -30
        elif row['DiasAbsenteismo'] in [23, 24]:
            return -60
        elif row['DiasAbsenteismo'] in [25, 26]:
            return -90
        elif row['DiasAbsenteismo'] in [27, 28]:
            return -120
        elif row['DiasAbsenteismo'] in [29, 30]:
            return -150
        else:
            return -150
                
def maxAbsenteismo(row):
    if row['CargoGR'] in ['PROFESSOR EM REGÊNCIA', 'GESTOR', 'PROFESSOR FORA DE REGÊNCIA']:
        return 300
    else:
        return 450