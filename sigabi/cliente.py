import requests


class Sigabi:

    def __init__(
        self,
        login,
        senha,
        base_url="https://apisigabi.seduc.mt.gov.br"
    ):
        self.base_url = base_url
        self.login = login
        self.senha = senha

        self.access_token = None
        self.refresh_token = None
        self.headers = {}

        self.autenticar()

    def autenticar(self):

        r = requests.post(
            f"{self.base_url}/auth/login",
            headers={
                "Accept": "application/json",
                "Content-Type": "application/x-www-form-urlencoded"
            },
            data={
                "grant_type": "password",
                "username": self.login,
                "password": self.senha
            }
        )

        r.raise_for_status()

        dados = r.json()

        self.access_token = dados["access_token"]
        self.refresh_token = dados.get("refresh_token")

        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

    def renovar_token(self):

        if not self.refresh_token:
            self.autenticar()
            return

        r = requests.post(
            f"{self.base_url}/auth/refresh",
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json"
            },
            json={
                "refresh_token": self.refresh_token
            }
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

        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

    def menus(self):
        from .menus import Menus
        return Menus(self)