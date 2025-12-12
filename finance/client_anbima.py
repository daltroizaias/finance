# %%

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, Literal, Optional
import logging
import base64
from settings import config
import pandas as pd
#%%
class AnbimaAuthClient:
    """
    Cliente de autenticação OAuth2 para API da ANBIMA
    """
    
    def __init__(self, client_id: str, client_secret: str, enviroment: Literal['sandbox', 'prod']):
        """
        Inicializa o cliente de autenticação
        
        Args:
            client_id: Client ID fornecido pela ANBIMA
            client_secret: Client Secret fornecido pela ANBIMA
            environment: Ambiente da API ("production" ou "sandbox")
        """
        self.enviroment = enviroment
        if enviroment == 'prod':
            self.base_url = "https://api.anbima.com.br"
        else:
            self.base_url = 'https://api-sandbox.anbima.com.br/mocks'

    
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_url = "https://api.anbima.com.br/oauth/access-token"

        # Armazena token atual
        self.access_token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None

        self.logger = logging.getLogger(__name__)

        
    def authenticate(self) -> Dict:
        """
        Autenticação da ANBIMA via OAuth2 Client Credentials
        """

        # Monta o Authorization Basic
        auth_str = f"{self.client_id}:{self.client_secret}"
        auth_base64 = base64.b64encode(auth_str.encode()).decode()

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {auth_base64}",
            "Accept": "application/json"
        }

        # Body obrigatoriamente x-www-form-urlencoded
        body = {
            "grant_type": "client_credentials"
        }

        self.logger.info("Autenticando na ANBIMA...")

        try:
            response = requests.post(
                self.token_url,
                data=body,   # <- OBRIGATORIAMENTE 'data', NÃO 'json'
                headers=headers,
                timeout=30
            )

            response.raise_for_status()

            token_data = response.json()

            # Armazena o token
            self.access_token = token_data["access_token"]
            self.token_expires_at = datetime.now() + timedelta(seconds=token_data.get("expires_in", 3600))

            return token_data

        except Exception as e:
            self.logger.error(f"Erro durante autenticação ANBIMA: {e}")
            raise

    def get_token(self) -> str:
        """
        Retorna um token válido (renova se estiver vencido).
        """
        if (
            self.access_token is None
            or self.token_expires_at is None
        ):
            self.logger.info("Token expirado ou inexistente. Renovando...")
            self.authenticate()

        return self.access_token

    def get(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
            """
            Faz um GET em qualquer endpoint da ANBIMA.
            
            Args:
                endpoint (str): Exemplo "/fundos/v2/fundos"
                params (dict): query params opcionais

            Returns:
                Dict com os dados retornados pela ANBIMA
            """
            token = self.get_token()
            
            headers = {
                'Content-Type': 'application/json',
                'client_id': self.client_id,
                "access_token": token,
            }

            url = f'{self.base_url}/{endpoint}'

            try:
                self.logger.info(f"GET {url}")
                response = requests.get(url, headers=headers, params=params, timeout=30)
                response.raise_for_status()

                return response.json()

            except Exception as e:
                self.logger.error(f"Erro ao acessar endpoint {url}: {e}")
                raise
#%%
# Exemplo de uso:
# if __name__ == "__main__":
# Configurar logging


logging.basicConfig(level=logging.INFO)

# Inicializar cliente (use variáveis de ambiente na prática)
client = AnbimaAuthClient(
    client_id=config.CLIENT_ID,
    client_secret=config.CLIENT_SECRET,
    enviroment='prod'
)

# %%

params = {
    'tipo-fundo': 'FIDC'
}
resp = client.get('feed/fundos/v2/fundos', params=params)

# %%
resp
# %%
df = pd.DataFrame(resp)
df
# %%
# %%
