#!/usr/bin/env python3
"""
Authentication module for Instagram
"""
import os
import logging
from instagrapi import Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_client(debug=False):
    """
    Create an authenticated Instagram client
    
    Args:
        debug (bool): Enable debug mode
    
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
        
        # Load session if exists
        if os.path.exists('session.pkl'):
            try:
                client.load_settings('session.pkl')
                client.login(username, password)
                logging.info("Session loaded and login successful.")
                return client
            except Exception as e:
                logging.warning(f"Failed to load session: {e}")
        
        # If no session or load failed, login normally
        client.login(username, password)
        
        # Save session for future use
        client.dump_settings('session.pkl')
        
        logging.info("Login successful")
        return client
        
    except Exception as e:
        logging.error(f"Failed to create client: {e}")
        return None