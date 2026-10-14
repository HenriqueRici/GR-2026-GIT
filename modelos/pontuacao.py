def pontuacaoGeral(base):
    if base['DiasAbsenteismo'] <= 30:
        if base['CargoGR'] == 'GESTOR':
            return base['PontuacaoAbsenteismo'] + base['PontuacaoEvasao'] + base['PontuacaoFormacao'] + base['PontuacaoMetaAprendizagem'] + base['PontuacaoMetaAdiministrativa']   
        elif base['CargoGR'] == 'PROFESSOR FORA DE REGÊNCIA':
            return base['PontuacaoAbsenteismo'] + base['PontuacaoEvasao'] + base['PontuacaoFormacao'] + base['PontuacaoMetaAprendizagem']
        elif base['CargoGR'] == 'PROFESSOR EM REGÊNCIA':
            return base['PontuacaoAbsenteismo'] + base['PontuacaoEvasao'] + base['PontuacaoFormacao'] + base['PontuacaoMetaAprendizagem']
        elif base['CargoGR'] == 'TAE/AAE':
            return base['PontuacaoAbsenteismo'] + base['PontuacaoEvasao'] + base['PontuacaoFormacao'] + base['PontuacaoMetaAprendizagem'] + base['PontuacaoMetaAdiministrativa']   
        elif base['CargoGR'] == 'CIVIS E MILITARES LOTADOS NA SEDUC':
            return base['PontuacaoAbsenteismo'] + base['PontuacaoEvasao'] + base['PontuacaoFormacao'] + base['PontuacaoMetaAprendizagem']
        else: 
            return 0
    else: 
        return 0

    
def valorFinalGR(base):
    return base['ValorGRBaseVinculo']/1000*base['PontuacaoGeral']
 
