# Dynamic Email Setup for AssetVault

This project now sends dynamic emails for:

- Welcome email after registration
- Password reset email from `/forgot-password`
- File upload confirmation
- Permission granted / file shared notification
- Public share link notification

## Render Environment Variables

Add these in Render → Your Web Service → Environment:

```env
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_gmail_app_password
MAIL_DEFAULT_SENDER=your_email@gmail.com
```

For Gmail, do **not** use your normal Gmail password. Use a Gmail App Password.

## Local Development

Create a `.env` file locally with the same variables. The app will still run if email variables are missing; it will skip emails and show a local reset link for forgot password testing.

## Changed Files

- `config/config.py`
- `routes/auth_routes.py`
- `routes/asset_routes.py`
- `routes/permission_routes.py`
- `service/email_service.py`
- `templates/login.html`
- `templates/forgot_password.html`
- `templates/reset_password.html`
- `requirements.txt`
