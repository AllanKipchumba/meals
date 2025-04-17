import streamlit as st
import extra_streamlit_components as stx
from extra_streamlit_components.CookieManager import CookieManager
from datetime import datetime, timedelta
import json

# ✅ Typed function with CookieManager
def create_auth_token(email: str, user_id: str, cookie_manager: CookieManager) -> None:
    auth_token = {
        "user_id": user_id,
        "email": email,
        "exp": (datetime.now() + timedelta(days=30)).timestamp()
    }

    
    cookie_manager.set(
        "auth_token",
        json.dumps(auth_token),
        expires_at=(datetime.now() + timedelta(days=30))
    )
