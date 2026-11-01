"""One-time interactive OAuth setup for a developer-owned Google Form PoC."""
from google_auth_oauthlib.flow import InstalledAppFlow
from app.services.google_forms import SCOPES, SECRET_DIR, TOKEN_PATH


def main():
    client_path = SECRET_DIR / "google_oauth_client.json"
    if not client_path.exists():
        raise SystemExit(f"Place Desktop OAuth client JSON at {client_path}")
    flow = InstalledAppFlow.from_client_secrets_file(str(client_path), SCOPES)
    creds = flow.run_local_server(port=0)
    SECRET_DIR.mkdir(parents=True, exist_ok=True)
    TOKEN_PATH.write_text(creds.to_json())
    print(f"Saved OAuth token at {TOKEN_PATH} (never commit it)")

if __name__ == "__main__":
    main()
