"""Composição dos pontos e cálculo do valor final da GR."""


def pontuacaoGeral(base):
    """Soma eixos aplicáveis ao cargo; mais de 30 dias de ausência zera a GR."""
    if not base["DiasAbsenteismo"] <= 30:
        return 0
    cargo = base["CargoGR"]
    if cargo not in (
        "GESTOR",
        "TAE/AAE",
        "PROFESSOR EM REGÊNCIA",
        "PROFESSOR FORA DE REGÊNCIA",
        "CIVIS E MILITARES LOTADOS NA SEDUC",
    ):
        return 0
    pontos = (
        base["PontuacaoAbsenteismo"]
        + base["PontuacaoEvasao"]
        + base["PontuacaoFormacao"]
        + base["PontuacaoMetaAprendizagem"]
    )
    if cargo in ("GESTOR", "TAE/AAE"):
        pontos += base["PontuacaoMetaAdiministrativa"]
    return pontos


def valorFinalGR(base):
    """Converte a pontuação em valor: base do vínculo dividida por 1000 vezes os pontos."""
    return base["ValorGRBaseVinculo"] / 1000 * base["PontuacaoGeral"]
