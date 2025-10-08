"""
AWS S3 client utilities for JLG Provider Recommender.

This module provides utilities for accessing and downloading data from AWS S3
buckets, with proper error handling and integration with the app's configuration
system.

Usage:
    from src.utils.s3_client import S3DataClient, get_latest_s3_file
    
    client = S3DataClient()
    if client.is_configured():
        file_bytes = client.download_latest_file('referrals')
"""

import logging
from datetime import datetime
from io import BytesIO
from typing import Optional, List, Tuple

import streamlit as st

logger = logging.getLogger(__name__)


class S3DataClient:
    """Client for accessing data files from AWS S3."""
    
    def __init__(self):
        """Initialize the S3 client with configuration from secrets."""
        from src.utils.config import get_api_config, is_api_enabled
        
        self.config = get_api_config('s3')
        self.enabled = is_api_enabled('s3')
        self._client = None
        
    def is_configured(self) -> bool:
        """Check if S3 is properly configured."""
        return self.enabled
    
    def _get_client(self):
        """Lazy initialization of boto3 client."""
        if self._client is None and self.enabled:
            try:
                import boto3
                self._client = boto3.client(
                    's3',
                    aws_access_key_id=self.config['aws_access_key_id'],
                    aws_secret_access_key=self.config['aws_secret_access_key'],
                    region_name=self.config['region_name']
                )
            except Exception as e:
                logger.error(f"Failed to initialize S3 client: {e}")
                self.enabled = False
        return self._client
    
    def list_files_in_folder(self, folder_type: str) -> List[Tuple[str, datetime]]:
        """
        List all files in a specific S3 folder.
        
        Args:
            folder_type: Either 'referrals' or 'preferred_providers'
            
        Returns:
            List of tuples (filename, last_modified_datetime)
        """
        client = self._get_client()
        if not client:
            return []
        
        # Get folder path from config
        if folder_type == 'referrals':
            folder = self.config['referrals_folder']
        elif folder_type == 'preferred_providers':
            folder = self.config['preferred_providers_folder']
        else:
            logger.error(f"Unknown folder type: {folder_type}")
            return []
        
        # Ensure folder ends with /
        if not folder.endswith('/'):
            folder += '/'
        
        try:
            response = client.list_objects_v2(
                Bucket=self.config['bucket_name'],
                Prefix=folder
            )
            
            files = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    # Skip the folder itself
                    if obj['Key'] == folder:
                        continue
                    # Only include Excel files
                    if obj['Key'].lower().endswith(('.xlsx', '.xls')):
                        filename = obj['Key'].split('/')[-1]
                        files.append((filename, obj['LastModified']))
            
            return sorted(files, key=lambda x: x[1], reverse=True)
            
        except Exception as e:
            logger.error(f"Failed to list files in S3 folder '{folder}': {e}")
            return []
    
    def download_file(self, folder_type: str, filename: str) -> Optional[bytes]:
        """
        Download a specific file from S3.
        
        Args:
            folder_type: Either 'referrals' or 'preferred_providers'
            filename: Name of the file to download
            
        Returns:
            File bytes or None if download fails
        """
        client = self._get_client()
        if not client:
            return None
        
        # Get folder path from config
        if folder_type == 'referrals':
            folder = self.config['referrals_folder']
        elif folder_type == 'preferred_providers':
            folder = self.config['preferred_providers_folder']
        else:
            logger.error(f"Unknown folder type: {folder_type}")
            return None
        
        # Ensure folder ends with /
        if not folder.endswith('/'):
            folder += '/'
        
        s3_key = f"{folder}{filename}"
        
        try:
            buffer = BytesIO()
            client.download_fileobj(
                self.config['bucket_name'],
                s3_key,
                buffer
            )
            buffer.seek(0)
            return buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Failed to download file '{s3_key}' from S3: {e}")
            return None
    
    def download_latest_file(self, folder_type: str) -> Optional[Tuple[bytes, str]]:
        """
        Download the most recently modified file from an S3 folder.
        
        Args:
            folder_type: Either 'referrals' or 'preferred_providers'
            
        Returns:
            Tuple of (file_bytes, filename) or None if no files found
        """
        files = self.list_files_in_folder(folder_type)
        if not files:
            logger.warning(f"No files found in S3 folder '{folder_type}'")
            return None
        
        latest_filename, last_modified = files[0]
        logger.info(f"Downloading latest file '{latest_filename}' from S3 (modified: {last_modified})")
        
        file_bytes = self.download_file(folder_type, latest_filename)
        if file_bytes:
            return file_bytes, latest_filename
        return None


@st.cache_data(ttl=300, show_spinner=False)
def get_latest_s3_file(folder_type: str) -> Optional[Tuple[bytes, str]]:
    """
    Cached function to get the latest file from S3.
    
    Args:
        folder_type: Either 'referrals' or 'preferred_providers'
        
    Returns:
        Tuple of (file_bytes, filename) or None if download fails
    """
    client = S3DataClient()
    if not client.is_configured():
        return None
    
    return client.download_latest_file(folder_type)


@st.cache_data(ttl=300, show_spinner=False)
def list_s3_files(folder_type: str) -> List[Tuple[str, datetime]]:
    """
    Cached function to list files in an S3 folder.
    
    Args:
        folder_type: Either 'referrals' or 'preferred_providers'
        
    Returns:
        List of tuples (filename, last_modified_datetime)
    """
    client = S3DataClient()
    if not client.is_configured():
        return []
    
    return client.list_files_in_folder(folder_type)
