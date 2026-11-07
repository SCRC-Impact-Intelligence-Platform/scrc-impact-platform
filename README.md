# SCRC Impact Intelligence Platform

A UCI Stem Cell Research Center capstone platform for discovering research publications, verifying SCRC resource usage through Google Forms, and reporting confirmed publication–resource attributions.

## Documentation

- [Backend setup, PubMed discovery, and Google OAuth](backend/README.md)
- [Three-question verification, Criticality, Other, and Unsure](backend/FORM_CRITICALITY.md)
- [SMTP email invitations and local testing](backend/EMAIL_WORKFLOW.md)
- [Frontend development](frontend/README.md)

## Local development

Use two terminals after completing the backend and frontend setup instructions:

```bash
# From backend/ with the Python environment activated
python -m uvicorn app.main:app --reload

# From frontend/ in a separate terminal
npm run dev
```

Open the frontend at <http://127.0.0.1:5173> and the API docs at <http://127.0.0.1:8000/docs>.

