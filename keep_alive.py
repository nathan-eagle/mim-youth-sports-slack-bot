#!/usr/bin/env python3
"""
Keep-alive service to prevent Flask app from sleeping
"""

import requests
import time
import threading
import logging
import os

logger = logging.getLogger(__name__)

class KeepAlive:
    def __init__(self, app_url: str, interval_minutes: int = 10):
        self.app_url = app_url.rstrip('/')
        self.interval_seconds = interval_minutes * 60
        self.running = False
        self.thread = None
    
    def start(self):
        """Start keep-alive service"""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._keep_alive_loop, daemon=True)
        self.thread.start()
        logger.info(f"Keep-alive service started, pinging {self.app_url} every {self.interval_seconds//60} minutes")
    
    def stop(self):
        """Stop keep-alive service"""
        self.running = False
        if self.thread:
            self.thread.join()
        logger.info("Keep-alive service stopped")
    
    def _keep_alive_loop(self):
        """Main keep-alive loop"""
        while self.running:
            try:
                # Ping health endpoint
                health_url = f"{self.app_url}/health"
                response = requests.get(health_url, timeout=30)
                if response.status_code == 200:
                    logger.info("Keep-alive ping successful")
                else:
                    logger.warning(f"Keep-alive ping returned {response.status_code}")
            
            except Exception as e:
                logger.error(f"Keep-alive ping failed: {e}")
            
            # Wait for next ping
            time.sleep(self.interval_seconds)

# Global keep-alive instance
keep_alive = None

def start_keep_alive():
    """Start keep-alive service if URL is configured"""
    global keep_alive
    
    app_url = os.getenv('APP_URL')  # Set this to your deployed app URL
    if app_url and not keep_alive:
        keep_alive = KeepAlive(app_url, interval_minutes=10)
        keep_alive.start()

if __name__ == "__main__":
    # Test keep-alive
    test_url = "https://your-app.herokuapp.com"  # Replace with your URL
    ka = KeepAlive(test_url, interval_minutes=1)
    ka.start()
    
    try:
        time.sleep(300)  # Run for 5 minutes
    except KeyboardInterrupt:
        ka.stop()