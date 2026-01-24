import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional

class EmailSender:
    """
    Handles sending transactional emails via SMTP.
    """
    def __init__(self):
        self.smtp_host = self._get_config("SMTP_HOST")
        self.smtp_port = int(self._get_config("SMTP_PORT", 587))
        self.smtp_user = self._get_config("SMTP_USER")
        self.smtp_password = self._get_config("SMTP_PASSWORD")
        self.from_email = self._get_config("SMTP_FROM_EMAIL") or self.smtp_user

    def _get_config(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get config from env vars or streamlit secrets."""
        # 1. Try environment variable
        val = os.environ.get(key)
        if val is not None:
            return val
        
        # 2. Try Streamlit secrets
        try:
            import streamlit as st
            # Check root level
            if key in st.secrets:
                return str(st.secrets[key])
            # Check [env] section
            if "env" in st.secrets and key in st.secrets["env"]:
                return str(st.secrets["env"][key])
        except Exception:
            pass
            
        return default

    def send_email(self, to_email: str, subject: str, html_content: str) -> bool:
        """
        Send an HTML email.
        Returns True on success, False on failure.
        """
        if not all([self.smtp_host, self.smtp_user, self.smtp_password]):
            print("EmailSender Error: Missing SMTP credentials in .env")
            return False

        try:
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = to_email
            msg['Subject'] = subject

            msg.attach(MIMEText(html_content, 'html'))

            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            return True
        except Exception as e:
            print(f"Email Sending Failed: {e}")
            return False
