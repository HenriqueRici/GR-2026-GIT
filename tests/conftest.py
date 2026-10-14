"""Referência de comportamento carregada do commit anterior à refatoração."""

import subprocess
import types
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

BASELINE = "948ebdaba9bccf955f7dad2a252697d6ccc8c4c9"
ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def legado():
    """Importa a referência sem autenticar em serviços externos."""

    def carregar(caminho):
        codigo = subprocess.check_output(
            ["git", "show", f"{BASELINE}:{caminho}"], cwd=ROOT, text=True
        )
        modulo = types.ModuleType("legado")
        modulo.__file__ = str(ROOT / caminho)
        with (
            patch(
                "google.oauth2.service_account.Credentials.from_service_account_file",
                return_value=Mock(),
            ),
            patch("gspread.authorize", return_value=Mock()),
        ):
            exec(compile(codigo, caminho, "exec"), modulo.__dict__)
        return modulo

    return carregar
