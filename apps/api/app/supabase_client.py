import os

from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

_url = os.environ.get("SUPABASE_URL")
_service_role_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

supabase: Client | None = (
    create_client(_url, _service_role_key) if _url and _service_role_key else None
)
