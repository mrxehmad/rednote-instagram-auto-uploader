#!/usr/bin/env python3
"""
Authentication module for Instagram
"""
import os
import logging
import time
from instagrapi import Client
from instagrapi.exceptions import (
    LoginRequired,
    ChallengeRequired,
    ClientError,
    ClientConnectionError
)
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_client(debug=False, max_retries=3):
    """
    Create an authenticated Instagram client with retry logic
    
    Args:
        debug (bool): Enable debug mode
        max_retries (int): Maximum number of retry attempts
    
    Returns:
        Client/None: Authenticated client if successful, None otherwise
    """
    try:
        # Get credentials from environment variables
        username = os.getenv('INSTAGRAM_USERNAME')
        password = os.getenv('INSTAGRAM_PASSWORD')
        
        if not username or not password:
            logging.error("Instagram credentials not found in environment variables")
            return None
        
        # Create client
        client = Client()
        
        # Configure client settings
        client.delay_range = [1, 3]  # Add random delay between requests
        client.request_timeout = 30  # Increase timeout
        
        # Try to load session first
        if os.path.exists('session.pkl'):
            try:
                client.load_settings('session.pkl')
                # Test if session is still valid
                try:
                    client.get_timeline_feed()
                    logging.info("Session loaded and validated successfully")
                    return client
                except (LoginRequired, ClientError):
                    logging.warning("Session expired, attempting new login")
                    if os.path.exists('session.pkl'):
                        os.remove('session.pkl')
            except Exception as e:
                logging.warning(f"Failed to load session: {e}")
                if os.path.exists('session.pkl'):
                    os.remove('session.pkl')
        
        # Login with retry logic
        for attempt in range(max_retries):
            try:
                logging.info(f"Login attempt {attempt + 1}/{max_retries}")
                client.login(username, password)
                
                # Save session for future use
                client.dump_settings('session.pkl')
                logging.info("Login successful")
                return client
                
            except ChallengeRequired as e:
                logging.info("Challenge required, handling verification...")
                try:
                    # Get challenge info from the exception
                    challenge_url = e.challenge_url
                    logging.info(f"Challenge URL: {challenge_url}")
                    
                    # Get verification code from user
                    code = input(f"Enter verification code for {username}: ")
                    
                    # Send verification code
                    client.private_request(
                        "challenge/",
                        data={
                            "choice": "1",  # Email verification
                            "_uuid": client.uuid,
                            "_uid": client.user_id,
                            "_csrftoken": client.token,
                            "code": code
                        }
                    )
                    logging.info("Verification code sent")
                    
                    # Save session after successful verification
                    client.dump_settings('session.pkl')
                    return client
                    
                except Exception as challenge_error:
                    logging.error(f"Challenge handling failed: {challenge_error}")
                    if attempt == max_retries - 1:
                        raise
                    time.sleep(5)  # Wait before retry
                    
            except (ClientConnectionError, ClientError) as e:
                logging.error(f"Connection error on attempt {attempt + 1}: {e}")
                if attempt == max_retries - 1:
                    raise
                time.sleep(5)  # Wait before retry
                
            except Exception as e:
                logging.error(f"Login failed on attempt {attempt + 1}: {e}")
                if attempt == max_retries - 1:
                    raise
                time.sleep(5)  # Wait before retry
        
        return None
        
    except Exception as e:
        logging.error(f"Failed to create client: {e}")
        return None