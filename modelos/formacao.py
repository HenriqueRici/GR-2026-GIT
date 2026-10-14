import pandas as pd

def formacaoObrigatoria(vinculos, formacao, inicioGR, colFormacao=None):

    formacao['InicioPeriodo'] = formacao.apply(lambda row: inicioGR if row['InicioPeriodo'] < inicioGR else row['InicioPeriodo'], axis=1)
    formacao['FimPeriodo'] = formacao.apply(lambda row: inicioGR if row['FimPeriodo'] < inicioGR else row['FimPeriodo'], axis=1)

    vinculosRegencia = vinculos[vinculos["CargoGR"] == "PROFESSOR EM REGÊNCIA"].copy()
    formacao["CPF"] = formacao["CPF"].astype("int64")

    resultados = []
    
    # Percorre períodos de formação
    for _, f in formacao.iterrows():
        # Seleciona vínculos que INTERSECTAM o período da formação
        ativos = vinculosRegencia[(vinculosRegencia["CPF"] == f["CPF"]) &
                          (vinculosRegencia["DataInicio"] <= f["FimPeriodo"]) &
                          (vinculosRegencia["DataFinal"] >= f["InicioPeriodo"])]
        if ativos.empty:
            continue
        
        total_ch = ativos["CH"].sum()
        
        for _, v in ativos.iterrows():
            proporcao = v["CH"] / total_ch if total_ch > 0 else 0
            ch_distribuida = f[colFormacao] * proporcao
            resultados.append({
                "CPF": f["CPF"],
                "NumVinc": v["NumVinc"],
                colFormacao: ch_distribuida
            })
            
    
    df_resultados = pd.DataFrame(resultados)
    df_resultados = df_resultados.groupby(['CPF', 'NumVinc']).agg(**{colFormacao: (colFormacao, 'sum')}).reset_index()
    df_resultados = pd.merge(vinculos, df_resultados, how='left', on=['CPF', 'NumVinc'])

    df_resultados.loc[df_resultados['CargoGR'] != 'PROFESSOR EM REGÊNCIA', colFormacao] = 0
    df_resultados[colFormacao] = df_resultados[colFormacao].fillna(0)

    return df_resultados

def formacaoEletivaRealizada(vinculos, formacaoEletiva):
    formacaoEletiva["CPF"] = formacaoEletiva["CPF"].astype("int64")
    formacaoEletiva = formacaoEletiva.groupby(['CPF']).agg(CHEletiva=('CHEletiva', 'sum')).reset_index()

    vinculos = pd.merge(vinculos, formacaoEletiva, how='left', on='CPF')
    vinculos["CHEletiva"] = vinculos["CHEletiva"].fillna(0)
    return vinculos


def pontuacaoFormacao(row):
    if row['CHObrigatoriaRealizada'] >= row['CHObrigatoria']:
        if 100 <= row['CHEletiva'] <= 130:
            return 54
        elif 131 <= row['CHEletiva'] <= 180:
            return 90
        elif 181 <= row['CHEletiva'] <= 199:
            return 126
        elif 200 <= row['CHEletiva']:
            return 150
        else:
            return 0
    else:
        return 0