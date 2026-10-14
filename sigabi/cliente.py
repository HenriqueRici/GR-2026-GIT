"""Autenticação e renovação de tokens da API SIGABI."""

import requests


class Sigabi:
    """Cliente de autenticação SIGABI."""

    def __init__(self, login, senha, base_url="https://apisigabi.seduc.mt.gov.br"):
        """Inicializa o cliente e suas dependências."""
        self.base_url = base_url
        self.login = login
        self.senha = senha

        self.access_token = None
        self.refresh_token = None
        self.headers = {}

        self.autenticar()

    def autenticar(self):
        """Obtém tokens usando login/senha e prepara os cabeçalhos das consultas."""
        r = requests.post(
            f"{self.base_url}/auth/login",
            headers={
                "Accept": "application/json",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={"grant_type": "password", "username": self.login, "password": self.senha},
        )

        r.raise_for_status()

        dados = r.json()

        self.access_token = dados["access_token"]
        self.refresh_token = dados.get("refresh_token")

        self._atualizar_headers()

    def renovar_token(self):
        """Renova o token; autentica novamente se o refresh estiver ausente ou inválido."""
        if not self.refresh_token:
            self.autenticar()
            return

        r = requests.post(
            f"{self.base_url}/auth/refresh",
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            json={"refresh_token": self.refresh_token},
        )

        # Se o refresh_token estiver inválido ou expirado,
        # realiza uma nova autenticação com login e senha.
        if r.status_code in (401, 403):
            self.autenticar()
            return

        r.raise_for_status()

        dados = r.json()

        self.access_token = dados["access_token"]

        if dados.get("refresh_token"):
            self.refresh_token = dados["refresh_token"]

        self._atualizar_headers()

    def menus(self):
        """Retorna o cliente de consultas paginadas associado a esta autenticação."""
        from .menus import Menus

        return Menus(self)

    def _atualizar_headers(self):
        """Reconstrói os cabeçalhos após autenticação ou renovação do token."""
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
