"""
security/middleware.py
======================
PRODUCTION - Security Headers and Session Management
"""
import streamlit as st
from datetime import datetime
import secrets

class SecurityHeaders:
    """Add security headers to Streamlit app"""

    @staticmethod
    def inject_headers():
        """Inject security headers via meta tags"""

        headers = """
        <script>
        (function() {
            function addMetaTag(httpEquiv, content) {
                var meta = document.createElement('meta');
                meta.httpEquiv = httpEquiv;
                meta.content = content;
                document.head.appendChild(meta);
            }
            
            if (window.location.protocol !== 'https:' && 
                !window.location.hostname.includes('localhost') && 
                !window.location.hostname.includes('127.0.0.1')) {
                window.location.href = 'https://' + window.location.host + window.location.pathname;
            }
            
            addMetaTag('Content-Security-Policy', 
                "default-src 'self'; " +
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' cdn.jsdelivr.net cdnjs.cloudflare.com; " +
                "style-src 'self' 'unsafe-inline' cdn.jsdelivr.net cdnjs.cloudflare.com fonts.googleapis.com; " +
                "font-src 'self' fonts.gstatic.com; " +
                "img-src 'self' data:; " +
                "connect-src 'self';"
            );
            
            addMetaTag('X-Content-Type-Options', 'nosniff');
            addMetaTag('X-Frame-Options', 'DENY');
            addMetaTag('X-XSS-Protection', '1; mode=block');
            addMetaTag('Referrer-Policy', 'strict-origin-when-cross-origin');
            addMetaTag('Strict-Transport-Security', 'max-age=31536000; includeSubDomains');
        })();
        </script>
        """

        st.markdown(headers, unsafe_allow_html=True)

    @staticmethod
    def initialize_session():
        """Initialize secure session"""

        if 'csrf_token' not in st.session_state:
            st.session_state.csrf_token = secrets.token_urlsafe(32)

        if 'session_start' not in st.session_state:
            st.session_state.session_start = datetime.now().isoformat()

        if 'session_id' not in st.session_state:
            st.session_state.session_id = secrets.token_urlsafe(16)

security_headers = SecurityHeaders()