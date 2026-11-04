## SMTP Configuration (Local Development)

The backend supports sending Google Forms verification invitations through the UCI SMTP relay.

### Setup

From the `backend/` directory:

**1. Install dependencies**

```bash
python -m pip install -e ".[dev]"
```

**2. Create a local environment file**

```bash
cp .env.example .env
```

**3. Configure `.env`**

```dotenv
SMTP_HOST=mta.service.uci.edu
SMTP_PORT=587
SMTP_FROM=DoNotReply@uci.edu
SMTP_ENABLE_SEND=true
SMTP_ALLOWED_RECIPIENTS=your-email@uci.edu
```

Replace `your-email@uci.edu` with an email address you control. Only enable sending when authorized to use the UCI SMTP relay.

**4. Start the backend**

```bash
python -m uvicorn app.main:app --reload
```

The backend automatically loads `.env` at startup. No manual `export` commands are required.

### Testing Email Invitations

1. Start the frontend with `npm run dev`.
2. Open `/forms` and select a researcher with a test email address.
3. Select publications and resources, then generate a Google Form.
4. Click **Compose invitation**, review the email, and click **Send invitation**.
5. Verify that the email arrives in your inbox and the Form Batch and Publications are marked `SENT`.

### Notes

- `.env` is Git-ignored and must not be committed.
- `.env.example` is committed as a configuration template.
- SMTP credentials are optional and should only be configured if required by UCI IT.
- `SMTP_ALLOWED_RECIPIENTS` restricts outgoing email to approved test recipients.
- SMTP acceptance does not guarantee inbox delivery.