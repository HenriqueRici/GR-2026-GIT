"""Indicadores e pontuação de frequência escolar."""

from datetime import datetime

import pandas as pd


def evasao(base, baseEvasao):
    """Anexa indicadores de frequência à lotação após limpar a chave da base."""
    base["LotacaoGR"] = base["LotacaoGR"].astype(str).str.strip()
    base = pd.merge(base, baseEvasao, on=["LotacaoGR"], how="left")
    print(
        f"\033[92mEvasão pronto, concluído em {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\033[0m"
    )
    return base


def pontuacaoEvasao(row):
    """Aplica os limites de frequência específicos para regência/gestão ou demais cargos."""
    if row["CargoGR"] in ["PROFESSOR EM REGÊNCIA", "GESTOR"]:
        if row["Frequencia"] > 0.9:
            return 100
        elif 0.8 <= row["Frequencia"] <= 0.9:
            return 30
    else:
        if row["Frequencia"] > 0.85:
            return 100
        elif 0.8 <= row["Frequencia"] <= 0.85:
            return 30

    return 0
