import requests
from django.conf import settings

class AuthService:
    BASE_URL = 'http://dataidea.pythonanywhere.com/'  # dataideaorg-backend URL

    @staticmethod
    def authenticate_with_main_backend(username: str, password: str) -> dict:
        """
        Authenticates user against the main backend (dataideaorg-backend)
        Returns dict with tokens and user info if successful, or None if failed
        """

        print(f"Authenticating with main backend: {username} {password}")
        try:
            response = requests.post(
                f"{AuthService.BASE_URL}/accounts/login/",
                json={"username": username, "password": password}
            )
            
            if response.status_code == 200:
                return response.json()
            return None
        except requests.RequestException:
            return None

    @staticmethod
    def register_with_main_backend(user_data: dict) -> dict:
        """
        Registers a new user with the main backend (dataideaorg-backend)
        Returns dict with user info if successful, raises exception if failed
        """
        try:
            response = requests.post(
                f"{AuthService.BASE_URL}/accounts/register/",
                json={
                    "username": user_data['username'],
                    "password": user_data['password'],
                    "first_name": user_data['first_name'],
                    "last_name": user_data['last_name'],
                    "email": user_data.get('email', ''),
                    "gender": user_data.get('gender', 'N')
                }
            )
            
            if response.status_code == 201:
                return response.json()
            
            # If registration failed, raise the error message
            response.raise_for_status()
            return None
        except requests.RequestException as e:
            if e.response is not None:
                raise Exception(e.response.json().get('message', str(e)))
            raise Exception(str(e)) 