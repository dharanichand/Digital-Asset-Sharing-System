# Render Email Setup for AssetVault

Add these variables in Render -> your Web Service -> Environment.

Required for Gmail SMTP:

MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USE_SSL=False
MAIL_USERNAME=yourgmail@gmail.com
MAIL_PASSWORD=your_16_character_google_app_password
MAIL_DEFAULT_SENDER=yourgmail@gmail.com

Also keep:

SECRET_KEY=any_long_random_secret
DATABASE_URL=your_render_postgresql_internal_url

Important:
- MAIL_PASSWORD must be a Google App Password, not your normal Gmail password.
- Enable 2-Step Verification in Google Account before creating an App Password.
- After adding/changing variables, click Save Changes and then Manual Deploy -> Clear build cache & deploy or Deploy latest commit.
