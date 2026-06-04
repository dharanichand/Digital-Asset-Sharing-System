from __future__ import annotations

import smtplib
from email.message import EmailMessage
from typing import Iterable, Optional
from flask import current_app, url_for


def email_enabled() -> bool:
    return bool(
        current_app.config.get("MAIL_USERNAME")
        and current_app.config.get("MAIL_PASSWORD")
        and current_app.config.get("MAIL_SERVER")
    )


def _clean_app_password(password: str | None) -> str:
    """Remove spaces accidentally copied from Google App Password display."""
    return (password or "").replace(" ", "").strip()


def send_email(to: str | Iterable[str], subject: str, body: str, html: Optional[str] = None) -> bool:
    if not email_enabled():
        current_app.logger.error(
            "Email disabled: MAIL_USERNAME, MAIL_PASSWORD, or MAIL_SERVER is missing."
        )
        return False

    recipients = [to] if isinstance(to, str) else list(to)
    recipients = [r.strip() for r in recipients if r and r.strip()]
    if not recipients:
        current_app.logger.error("Email not sent: recipient list is empty.")
        return False

    sender = current_app.config.get("MAIL_DEFAULT_SENDER") or current_app.config["MAIL_USERNAME"]

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = ", ".join(recipients)
    msg.set_content(body)
    if html:
        msg.add_alternative(html, subtype="html")

    server = current_app.config.get("MAIL_SERVER", "smtp.gmail.com")
    port = int(current_app.config.get("MAIL_PORT", 587))
    use_tls = str(current_app.config.get("MAIL_USE_TLS", "true")).lower() in ["1", "true", "yes", "on"]
    use_ssl = str(current_app.config.get("MAIL_USE_SSL", "false")).lower() in ["1", "true", "yes", "on"]

    username = (current_app.config.get("MAIL_USERNAME") or "").strip()
    password = _clean_app_password(current_app.config.get("MAIL_PASSWORD"))

    try:
        smtp_class = smtplib.SMTP_SSL if use_ssl else smtplib.SMTP
        with smtp_class(server, port, timeout=20) as smtp:
            smtp.ehlo()
            if use_tls and not use_ssl:
                smtp.starttls()
                smtp.ehlo()
            smtp.login(username, password)
            smtp.send_message(msg)

        current_app.logger.info("Email sent successfully to %s", ", ".join(recipients))
        return True

    except smtplib.SMTPAuthenticationError:
        current_app.logger.exception(
            "Gmail rejected MAIL_USERNAME/MAIL_PASSWORD. "
            "Create a NEW Google App Password, remove spaces, and update MAIL_PASSWORD."
        )
        return False

    except Exception:
        current_app.logger.exception(
            "Email sending failed. Check MAIL_SERVER, MAIL_PORT, TLS/SSL settings, and internet access."
        )
        return False


def send_welcome_email(user) -> bool:
    subject = "Welcome to AssetVault"
    body = f"""Hi {user.username},

Your AssetVault account was created successfully.

Account details:
Email: {user.email}
Role: {user.role}
Group: {user.group_name}

You can now sign in and start managing your digital assets.
"""
    html = f"""
    <h2>Welcome to AssetVault, {user.username}!</h2>
    <p>Your account was created successfully.</p>
    <ul>
      <li><strong>Email:</strong> {user.email}</li>
      <li><strong>Role:</strong> {user.role}</li>
      <li><strong>Group:</strong> {user.group_name}</li>
    </ul>
    <p>You can now sign in and start managing your digital assets.</p>
    """
    return send_email(user.email, subject, body, html)


def send_password_reset_email(user, token: str) -> bool:
    reset_url = url_for("auth.reset_password", token=token, _external=True)
    subject = "Reset your AssetVault password"
    body = f"""Hi {user.username},

Use this link to reset your AssetVault password:
{reset_url}

This link expires in 30 minutes. If you did not request this, you can ignore this email.
"""
    html = f"""
    <h2>Password reset request</h2>
    <p>Hi {user.username},</p>
    <p>Click the button below to reset your password. This link expires in 30 minutes.</p>
    <p>
      <a href="{reset_url}" style="display:inline-block;padding:12px 18px;background:#2563eb;color:#fff;text-decoration:none;border-radius:8px;">
        Reset Password
      </a>
    </p>
    <p>If the button does not work, copy this link:</p>
    <p>{reset_url}</p>
    """
    return send_email(user.email, subject, body, html)


def send_file_uploaded_email(user, asset) -> bool:
    subject = "File uploaded successfully"
    expiry = asset.expiry_date.strftime("%Y-%m-%d") if asset.expiry_date else "No expiry date"
    body = f"""Hi {user.username},

Your file was uploaded successfully.

File: {asset.original_name}
Category: {asset.category}
Expiry: {expiry}
Public: {'Yes' if asset.is_public else 'No'}
Download allowed: {'Yes' if asset.allow_download else 'No'}
"""
    html = f"""
    <h2>File uploaded successfully</h2>
    <p>Hi {user.username}, your file was uploaded successfully.</p>
    <ul>
      <li><strong>File:</strong> {asset.original_name}</li>
      <li><strong>Category:</strong> {asset.category}</li>
      <li><strong>Expiry:</strong> {expiry}</li>
      <li><strong>Public:</strong> {'Yes' if asset.is_public else 'No'}</li>
      <li><strong>Download allowed:</strong> {'Yes' if asset.allow_download else 'No'}</li>
    </ul>
    """
    return send_email(user.email, subject, body, html)


def send_permission_granted_email(recipient, owner, asset, permission_type: str) -> bool:
    files_url = url_for("asset.files", _external=True)
    subject = "A file was shared with you"
    owner_name = owner.username if owner else "An administrator"
    body = f"""Hi {recipient.username},

{owner_name} shared a file with you on AssetVault.

File: {asset.original_name}
Permission: {permission_type}

Open your files page:
{files_url}
"""
    html = f"""
    <h2>A file was shared with you</h2>
    <p>Hi {recipient.username},</p>
    <p><strong>{owner_name}</strong> shared a file with you on AssetVault.</p>
    <ul>
      <li><strong>File:</strong> {asset.original_name}</li>
      <li><strong>Permission:</strong> {permission_type}</li>
    </ul>
    <p><a href="{files_url}">Open your files page</a></p>
    """
    return send_email(recipient.email, subject, body, html)


def send_public_link_email(owner, asset) -> bool:
    if not asset.share_token:
        return False

    share_url = url_for("asset.public_share", token=asset.share_token, _external=True)
    subject = "Public sharing enabled"
    body = f"""Hi {owner.username},

Public sharing is now enabled for this file:
{asset.original_name}

Public link:
{share_url}
"""
    html = f"""
    <h2>Public sharing enabled</h2>
    <p>Hi {owner.username}, public sharing is now enabled for <strong>{asset.original_name}</strong>.</p>
    <p><a href="{share_url}">Open public share link</a></p>
    <p>{share_url}</p>
    """
    return send_email(owner.email, subject, body, html)
