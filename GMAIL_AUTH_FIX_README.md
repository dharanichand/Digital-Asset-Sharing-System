# Gmail SMTP authentication fix

The error:

SMTPAuthenticationError: Username and Password not accepted

means Gmail rejected the sender login.

Required fix:
1. Revoke the old exposed Google App Password.
2. Create a new Google App Password.
3. Paste it into .env and Render MAIL_PASSWORD without spaces.
4. Restart Flask or redeploy Render.

Local .env example:

SECRET_KEY=digital-asset-system-secret-key-render-2026-vu241fa04444
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USE_SSL=False
MAIL_USERNAME=vu.241fa04444@gmail.com
MAIL_PASSWORD=yournewgoogleapppasswordwithoutspaces
MAIL_DEFAULT_SENDER=vu.241fa04444@gmail.com
DATABASE_URL=sqlite:///database.db

Test locally:
python scripts/test_email.py receiver@example.com
