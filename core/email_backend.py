import ssl
import smtplib
from django.core.mail.backends.smtp import EmailBackend as BaseEmailBackend

class CustomEmailBackend(BaseEmailBackend):
    def open(self):
        """
        Override open method to handle SSL certificate issues
        """
        if self.connection:
            return False
        connection_params = self._get_connection_params()
        
        try:
            self.connection = smtplib.SMTP(
                self.host, 
                self.port, 
                timeout=connection_params.get('timeout'),
                local_hostname=connection_params.get('local_hostname')
            )
            
            if self.use_tls:    
                self.connection.ehlo()
                
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                
                self.connection.starttls(context=context)
                self.connection.ehlo()
            
            if self.username and self.password:
                self.connection.login(self.username, self.password)
                
            return True
            
        except (smtplib.SMTPException, OSError) as e:
            if not self.fail_silently:
                raise
            return False
    
    def _get_connection_params(self):
        params = {}
        
        if hasattr(self, 'timeout') and self.timeout is not None:
            params['timeout'] = self.timeout
        
        if hasattr(self, 'local_hostname') and self.local_hostname is not None:
            params['local_hostname'] = self.local_hostname
        
        return params