from __future__ import annotations

import smtplib
from email.message import EmailMessage
from typing import Iterable, Optional
from flask import current_app, url_for


def email_enabled() -> bool:
    """Return True only when SMTP settings are configured.

    The app must keep working locally even before you add email credentials.
    When credentials are missing, email functions simply return False instead
    of crashing the website.
    """
    return bool(
        current_app.config.get("MAIL_USERNAME")
        and current_app.config.get("MAIL_PASSWORD")
        and current_app.config.get("MAIL_SERVER")
    )


def send_email(to: str | Iterable[str], subject: str, body: str, html: Optional[str] = None) -> bool:
    """Send one dynamic email using SMTP.

    Required environment variables on Render:
      MAIL_USERNAME
      MAIL_PASSWORD

    Optional environment variables:
      MAIL_SERVER, MAIL_PORT, MAIL_USE_TLS, MAIL_DEFAULT_SENDER
    """
    if not email_enabled():
        current_app.logger.info("Email skipped because SMTP environment variables are not configured.")
        return False

    recipients = [to] if isinstance(to, str) else list(to)
    recipients = [r for r in recipients if r]
    if not recipients:
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

    try:
        with smtplib.SMTP(server, port, timeout=20) as smtp:
            if use_tls:
                smtp.starttls()
            smtp.login(current_app.config["MAIL_USERNAME"], current_app.config["MAIL_PASSWORD"])
            smtp.send_message(msg)
        return True
    except Exception as exc:
        current_app.logger.exception("Email sending failed: %s", exc)
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
    <p><a href="{reset_url}" style="display:inline-block;padding:12px 18px;background:#2563eb;color:#fff;text-decoration:none;border-radius:8px;">Reset Password</a></p>
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
