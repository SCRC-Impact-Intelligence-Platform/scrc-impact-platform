"""Google Forms API adapter. OAuth is authorized separately using google_auth.py."""
from pathlib import Path
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SECRET_DIR = Path(__file__).resolve().parents[2] / ".secrets"
TOKEN_PATH = SECRET_DIR / "google_token.json"
SCOPES = [
    "https://www.googleapis.com/auth/forms.body",
    "https://www.googleapis.com/auth/forms.responses.readonly",
]


def get_forms_service():
    if not TOKEN_PATH.exists():
        raise RuntimeError("Run: python -m app.google_auth first")
    creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
    if not creds.valid:
        if not creds.expired or not creds.refresh_token:
            raise RuntimeError("Google OAuth expired; run google_auth again")
        creds.refresh(Request())
        TOKEN_PATH.write_text(creds.to_json())
    return build("forms", "v1", credentials=creds, cache_discovery=False)


def create_google_form(items: list[dict]) -> tuple[str, str, list[tuple[str, str]]]:
    """Returns Google form ID, responder URL, and question-ID pairs per publication."""
    service = get_forms_service()
    created = service.forms().create(body={"info": {"title": "SCRC Publication Attribution Verification (PoC)"}}).execute()
    form_id = created["formId"]
    requests = []
    for item in items:
        title = f"PMID {item['pmid']}: {item['title'][:180]}"
        requests.append({"createItem": {"item": {"title": f"{title} — Were any listed SCRC resources used?", "questionItem": {"question": {"required": True, "choiceQuestion": {"type": "RADIO", "options": [{"value": "Yes"}, {"value": "No"}], "shuffle": False}}}}, "location": {"index": len(requests)}}})
        requests.append({"createItem": {"item": {"title": f"{title} — If Yes, select resources used (otherwise leave empty)", "questionItem": {"question": {"required": False, "choiceQuestion": {"type": "CHECKBOX", "options": [{"value": f"{r['id']}: {r['name']}"} for r in item['resources']], "shuffle": False}}}}, "location": {"index": len(requests)}}})
    if not requests:
        raise ValueError("No publications selected")
    result = service.forms().batchUpdate(formId=form_id, body={"requests": requests}).execute()
    pairs = []
    replies = result["replies"]
    for index in range(0, len(replies), 2):
        pairs.append((replies[index]["createItem"]["questionId"][0], replies[index+1]["createItem"]["questionId"][0]))
    service.forms().setPublishSettings(
        formId=form_id,
        body={"publishSettings": {"publishState": {"isPublished": True, "isAcceptingResponses": True}}, "updateMask": "publishState"},
    ).execute()
    form = service.forms().get(formId=form_id).execute()
    return form_id, form["responderUri"], pairs


def get_responses(form_id: str) -> list[dict]:
    service = get_forms_service()
    records = []
    token = None
    while True:
        kwargs = {"formId": form_id, "pageSize": 500}
        if token:
            kwargs["pageToken"] = token
        response = service.forms().responses().list(**kwargs).execute()
        records.extend(response.get("responses", []))
        token = response.get("nextPageToken")
        if not token:
            return records
