"""
Notification service for SMS and WhatsApp messages
"""
import logging
from twilio.rest import Client
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import Config

logging.basicConfig(level=getattr(logging, Config.LOG_LEVEL))
logger = logging.getLogger(__name__)

class NotificationService:
    """Handle SMS, WhatsApp, and Email notifications"""
    
    def __init__(self):
        self.twilio_client = None
        self.twilio_phone = Config.TWILIO_PHONE_NUMBER
        self.user_phone = Config.USER_PHONE_NUMBER
        self.whatsapp_number = Config.WHATSAPP_NUMBER
        
        # Initialize Twilio if credentials are available
        if Config.TWILIO_ACCOUNT_SID and Config.TWILIO_AUTH_TOKEN:
            try:
                self.twilio_client = Client(
                    Config.TWILIO_ACCOUNT_SID,
                    Config.TWILIO_AUTH_TOKEN
                )
            except Exception as e:
                logger.warning(f"Twilio initialization failed: {str(e)}")
    
    def send_sms(self, message):
        """
        Send SMS notification
        """
        if not self.twilio_client:
            logger.warning("Twilio not configured. SMS not sent.")
            return False
        
        try:
            message = self.twilio_client.messages.create(
                body=message,
                from_=self.twilio_phone,
                to=self.user_phone
            )
            logger.info(f"SMS sent successfully. SID: {message.sid}")
            return True
        except Exception as e:
            logger.error(f"Failed to send SMS: {str(e)}")
            return False
    
    def send_whatsapp(self, message):
        """
        Send WhatsApp notification via Twilio
        """
        if not self.twilio_client:
            logger.warning("Twilio not configured. WhatsApp not sent.")
            return False
        
        try:
            # Twilio WhatsApp format: whatsapp:+1234567890
            from_whatsapp = f"whatsapp:{self.twilio_phone}"
            to_whatsapp = f"whatsapp:{self.user_phone}"
            
            message = self.twilio_client.messages.create(
                body=message,
                from_=from_whatsapp,
                to=to_whatsapp
            )
            logger.info(f"WhatsApp message sent successfully. SID: {message.sid}")
            return True
        except Exception as e:
            logger.error(f"Failed to send WhatsApp: {str(e)}")
            return False
    
    def send_email(self, subject, body):
        """
        Send email notification
        """
        if not Config.EMAIL_USER or not Config.EMAIL_PASSWORD:
            logger.warning("Email not configured. Email not sent.")
            return False
        
        try:
            msg = MIMEMultipart()
            msg['From'] = Config.EMAIL_USER
            msg['To'] = Config.NOTIFICATION_EMAIL
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(Config.SMTP_SERVER, Config.SMTP_PORT)
            server.starttls()
            server.login(Config.EMAIL_USER, Config.EMAIL_PASSWORD)
            text = msg.as_string()
            server.sendmail(Config.EMAIL_USER, Config.NOTIFICATION_EMAIL, text)
            server.quit()
            
            logger.info("Email sent successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            return False
    
    def notify_slot_purchase(self, order_details):
        """
        Send notification about slot purchase
        """
        symbol = order_details.get('tradingsymbol', 'N/A')
        quantity = order_details.get('quantity', 'N/A')
        price = order_details.get('average_price', 'N/A')
        order_id = order_details.get('order_id', 'N/A')
        status = order_details.get('status', 'N/A')
        
        message = f"""
🚀 Automated Slot Purchase Executed

Symbol: {symbol}
Quantity: {quantity}
Price: ₹{price}
Order ID: {order_id}
Status: {status}

This is an automated trade executed by your trading agent.
        """.strip()
        
        # Send via all channels
        self.send_sms(message)
        self.send_whatsapp(message)
        self.send_email(
            subject=f"Slot Purchase: {symbol}",
            body=message
        )
    
    def notify_error(self, error_message):
        """
        Send error notification
        """
        message = f"""
⚠️ Trading Agent Error

{error_message}

Please check your trading agent configuration.
        """.strip()
        
        self.send_sms(message)
        self.send_whatsapp(message)
        self.send_email(
            subject="Trading Agent Error",
            body=message
        )
    
    def notify_daily_reminder(self):
        """
        Send daily reminder about automated trading
        """
        message = """
📊 Daily Trading Reminder

Your automated trading agent is active and will execute slot purchases as configured.

No action required from your side.
        """.strip()
        
        self.send_sms(message)
        self.send_whatsapp(message)
