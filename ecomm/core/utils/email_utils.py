# utils/email_utils.py
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags
from django.urls import reverse
import logging

logger = logging.getLogger(__name__)

class ReturnEmailService:
    """Handle all return-related email communications"""
    
    @staticmethod
    def get_tracking_url(return_request):
        """Generate tracking URL for return"""
        domain = getattr(settings, 'SITE_DOMAIN', 'localhost:8080')
        protocol = getattr(settings, 'SITE_PROTOCOL', 'http')
        
        # This line builds the full URL
        return f"{protocol}://{domain}{reverse('core:return-confirmation', args=[return_request.rma_number])}"
    
    @staticmethod
    def send_return_confirmation(return_request):
        """Send email when return request is created"""
        try:
            subject = f"Return Request Confirmation - #{return_request.rma_number}"
            tracking_url = ReturnEmailService.get_tracking_url(return_request)
            
            html_content = render_to_string(
                'core/emails/return_request_confirmation.html',
                {
                    'return': return_request,
                    'tracking_url': tracking_url
                }
            )
            text_content = strip_tags(html_content)
            
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[return_request.user.email]
            )
            email.attach_alternative(html_content, "text/html")
            email.send()
            
            logger.info(f"Return confirmation email sent for RMA: {return_request.rma_number}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send return confirmation email: {str(e)}")
            return False
    
    @staticmethod
    def send_return_approved(return_request):
        """Send email when return is approved"""
        try:
            subject = f"Return Request Approved - #{return_request.rma_number}"
            tracking_url = ReturnEmailService.get_tracking_url(return_request)
            
            html_content = render_to_string(
                'core/emails/return_approved.html',
                {
                    'return': return_request,
                    'tracking_url': tracking_url
                }
            )
            text_content = strip_tags(html_content)
            
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[return_request.user.email]
            )
            email.attach_alternative(html_content, "text/html")
            
            # If you have a return label, you could attach it here
            # if return_request.return_label:
            #     email.attach_file(return_request.return_label.path)
            
            email.send()
            
            logger.info(f"Return approved email sent for RMA: {return_request.rma_number}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send return approved email: {str(e)}")
            return False
    
    @staticmethod
    def send_return_rejected(return_request):
        """Send email when return is rejected"""
        try:
            subject = f"Update on Your Return Request - #{return_request.rma_number}"
            
            html_content = render_to_string(
                'core/emails/return_rejected.html',
                {'return': return_request}
            )
            text_content = strip_tags(html_content)
            
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[return_request.user.email]
            )
            email.attach_alternative(html_content, "text/html")
            email.send()
            
            logger.info(f"Return rejected email sent for RMA: {return_request.rma_number}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send return rejected email: {str(e)}")
            return False
    
    @staticmethod
    def send_return_received(return_request):
        """Send email when returned item is received"""
        try:
            subject = f"Return Item Received - #{return_request.rma_number}"
            
            html_content = render_to_string(
                'core/emails/return_received.html',
                {'return': return_request}
            )
            text_content = strip_tags(html_content)
            
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[return_request.user.email]
            )
            email.attach_alternative(html_content, "text/html")
            email.send()
            
            logger.info(f"Return received email sent for RMA: {return_request.rma_number}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send return received email: {str(e)}")
            return False
    
    @staticmethod
    def send_return_completed(return_request):
        """Send email when refund is processed"""
        try:
            subject = f"Refund Processed - #{return_request.rma_number}"
            
            html_content = render_to_string(
                'core/emails/return_completed.html',
                {'return': return_request}
            )
            text_content = strip_tags(html_content)
            
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[return_request.user.email]
            )
            email.attach_alternative(html_content, "text/html")
            email.send()
            
            logger.info(f"Return completed email sent for RMA: {return_request.rma_number}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send return completed email: {str(e)}")
            return False