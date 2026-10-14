"""Confere duas prévias Excel produzidas a partir das mesmas bases de entrada."""

import argparse

import pandas as pd


def main():
    """Retorna erro se nomes, ordem ou valores das células forem diferentes."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("anterior", help="Prévia de referência, preservada antes da execução nova.")
    parser.add_argument("atual", help="Prévia produzida pela versão refatorada.")
    args = parser.parse_args()
    anterior = pd.read_excel(args.anterior)
    atual = pd.read_excel(args.atual)
    pd.testing.assert_frame_equal(anterior, atual, check_exact=True)
    print(f"Prévias idênticas: {len(atual)} linhas e {len(atual.columns)} colunas.")


if __name__ == "__main__":
    main()
