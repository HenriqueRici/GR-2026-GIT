"""Mede os seis eixos administrativos em dados sintéticos e confere equivalência."""

import subprocess
import sys
import time
import types
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from modelos.metaAdm import EIXOS, _pontuar_coluna  # noqa: E402

BASELINE = "948ebdaba9bccf955f7dad2a252697d6ccc8c4c9"


def main():
    """Compara medianas de três execuções para 40 mil registros fictícios."""
    codigo = subprocess.check_output(
        ["git", "show", f"{BASELINE}:modelos/metaAdm.py"], cwd=ROOT, text=True
    )
    antigo = types.ModuleType("meta_anterior")
    exec(compile(codigo, "meta_anterior", "exec"), antigo.__dict__)
    rng = np.random.default_rng(2026)
    base = pd.DataFrame(
        {"CargoGR": rng.choice(["GESTOR", "TAE/AAE", "PROFESSOR EM REGÊNCIA"], 40000)}
    )
    for coluna, _ in EIXOS.values():
        base[coluna] = rng.uniform(0, 75, len(base))
    tempos = {"original": [], "refatorado": []}
    for _ in range(3):
        inicio = time.perf_counter()
        esperado = pd.DataFrame({nome: base.apply(getattr(antigo, nome), axis=1) for nome in EIXOS})
        tempos["original"].append(time.perf_counter() - inicio)
        inicio = time.perf_counter()
        atual = pd.DataFrame({nome: _pontuar_coluna(base, nome) for nome in EIXOS})
        tempos["refatorado"].append(time.perf_counter() - inicio)
        pd.testing.assert_frame_equal(esperado, atual, check_exact=True)
    original = float(np.median(tempos["original"]))
    refatorado = float(np.median(tempos["refatorado"]))
    print("40.000 linhas; seis eixos; mediana de três execuções")
    print(
        f"Original: {original:.4f}s; refatorado: {refatorado:.4f}s; razão: {original / refatorado:.1f}x"
    )
    print("DataFrames idênticos, inclusive tipos e ordem. Medição isolada, sem I/O.")


if __name__ == "__main__":
    main()
