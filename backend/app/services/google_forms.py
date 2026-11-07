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


def _radio_item(title: str, values: list[str], *, required: bool) -> dict:
    return {
        "title": title,
        "questionItem": {"question": {
            "required": required,
            "choiceQuestion": {
                "type": "RADIO",
                "options": [{"value": value} for value in values],
                "shuffle": False,
            },
        }},
    }


def create_google_form(
    items: list[dict], *, batch_id: int | None = None, researcher_name: str | None = None
) -> tuple[str, str, list[tuple[str, str, str]]]:
    """Create a respondent-name prompt plus three questions per publication.

    The respondent name stays in Google Forms only; it is not returned in
    the publication question-ID triples or persisted by response sync.
    """
    if not items:
        raise ValueError("No publications selected")
    service = get_forms_service()
    title = "SCRC Publication Attribution Verification"
    # documentTitle controls the file name shown in Google Forms / Drive.
    # Keep the responder-facing title short, but distinguish owner-side batches.
    parts = ["SCRC Verification"]
    if batch_id is not None:
        parts.append(f"Batch #{batch_id}")
    if researcher_name:
        parts.append(researcher_name.strip()[:80])
    parts.append(f"{len(items)} publication(s)")
    document_title = " | ".join(parts)
    created = service.forms().create(
        body={"info": {"title": title, "documentTitle": document_title}}
    ).execute()
    form_id = created["formId"]
    # One form-level question, unrelated to any specific publication.
    # We intentionally do not store or interpret this answer in our DB.
    name_question = {
        "title": "Your full name",
        "questionItem": {"question": {
            "required": True,
            "textQuestion": {"paragraph": False},
        }},
    }
    requests = [{"createItem": {"item": name_question, "location": {"index": 0}}}]
    for item in items:
        title = f"PMID {item['pmid']}: {item['title'][:180]}"
        equipment_options = [
            {"value": f"{r['id']}: {r['name']}"} for r in item["resources"]
        ]
        # Plain checkbox option: respondents select it without typing free text.
        equipment_options.append({"value": "Other (not listed)"})
        questions = [
            _radio_item(
                f"{title} — Were any SCRC resources used?",
                ["Yes", "No", "Unsure"],
                required=True,
            ),
            {
                "title": f"{title} — If Yes, which SCRC resources were used? (Other if not listed)",
                "questionItem": {"question": {
                    "required": False,
                    "choiceQuestion": {
                        "type": "CHECKBOX",
                        "options": equipment_options,
                        "shuffle": False,
                    },
                }},
            },
            _radio_item(
                f"{title} — If Yes, how critical were the selected resources overall?",
                ["Critical", "Significant", "Minor"],
                required=False,
            ),
        ]
        for question in questions:
            requests.append({"createItem": {
                "item": question,
                "location": {"index": len(requests)},
            }})
    result = service.forms().batchUpdate(
        formId=form_id, body={"requests": requests}
    ).execute()
    replies = result["replies"]
    triples = []
    # First reply belongs to the standalone name question, not to a paper.
    for index in range(1, len(replies), 3):
        triples.append(tuple(
            replies[index + offset]["createItem"]["questionId"][0]
            for offset in range(3)
        ))
    service.forms().setPublishSettings(
        formId=form_id,
        body={"publishSettings": {"publishState": {
            "isPublished": True, "isAcceptingResponses": True,
        }}, "updateMask": "publishState"},
    ).execute()
    form = service.forms().get(formId=form_id).execute()
    return form_id, form["responderUri"], triples


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
