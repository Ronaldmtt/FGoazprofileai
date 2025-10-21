import logging
from config import Config

logger = logging.getLogger(__name__)

class EmailService:
    """
    Email service for sending magic links.
    MVP: Console logging only (no actual email sending).
    Future: integrate with SendGrid or similar.
    """
    
    def __init__(self):
        self.sendgrid_key = Config.SENDGRID_API_KEY
        self.enabled = bool(self.sendgrid_key)
    
    def send_magic_link(self, email: str, magic_url: str) -> bool:
        """
        Send magic link email.
        In MVP, just log to console.
        """
        if not self.enabled:
            logger.info(f"[EMAIL] Magic link for {email}: {magic_url}")
            print(f"\n{'='*60}")
            print(f"MAGIC LINK EMAIL")
            print(f"To: {email}")
            print(f"Link: {magic_url}")
            print(f"{'='*60}\n")
            return True
        
        try:
            logger.info(f"Sent magic link to {email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            return False
