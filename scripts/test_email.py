import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import app
from service.email_service import send_email

if len(sys.argv) < 2:
    print("Usage: python scripts/test_email.py receiver@example.com")
    raise SystemExit(1)

receiver = sys.argv[1]

with app.app_context():
    print("MAIL_SERVER:", app.config.get("MAIL_SERVER"))
    print("MAIL_PORT:", app.config.get("MAIL_PORT"))
    print("MAIL_USE_TLS:", app.config.get("MAIL_USE_TLS"))
    print("MAIL_USE_SSL:", app.config.get("MAIL_USE_SSL"))
    print("MAIL_USERNAME:", app.config.get("MAIL_USERNAME"))
    print("MAIL_DEFAULT_SENDER:", app.config.get("MAIL_DEFAULT_SENDER"))
    print("MAIL_PASSWORD EXISTS:", bool(app.config.get("MAIL_PASSWORD")))

    ok = send_email(
        receiver,
        "AssetVault SMTP Test",
        "This is a test email from your AssetVault Flask project."
    )

    if ok:
        print("SUCCESS: Test email sent. Check Inbox/Spam/Sent folder.")
    else:
        print("FAILED: Email not sent. Check the error printed above.")
