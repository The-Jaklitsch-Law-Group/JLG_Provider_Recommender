"""
Optimized AWS S3 client utilities for improved performance.

This module provides performance-optimized utilities for accessing S3 with:
- Connection pooling and reuse
- Parallel operations
- Better caching strategies
- Reduced API calls
"""

import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from io import BytesIO
from typing import Dict, List, Optional, Tuple

import streamlit as st

logger = logging.getLogger(__name__)


class OptimizedS3DataClient:
    """Performance-optimized client for accessing data files from AWS S3."""

    def __init__(self, folder_map: Optional[Dict[str, str]] = None):
        """Initialize the optimized S3 client with connection pooling."""
        from src.utils.config import get_api_config, is_api_enabled

        self.config = get_api_config("s3")
        self.enabled = is_api_enabled("s3")
        self._client = None
        self._session = None

        # Default folder configuration
        defaults = {
            "referrals_folder": "990046944",
            "preferred_providers_folder": "990047553",
        }

        # Merge configurations
        merged = defaults.copy()
        if isinstance(self.config, dict):
            cfg_ref = self.config.get("referrals_folder")
            cfg_pref = self.config.get("preferred_providers_folder")
            if cfg_ref:
                merged["referrals_folder"] = cfg_ref
            if cfg_pref:
                merged["preferred_providers_folder"] = cfg_pref

        # Apply caller overrides
        if folder_map:
            for k, v in folder_map.items():
                if k in merged and v:
                    merged[k] = v

        self.folder_map = merged

    def is_configured(self) -> bool:
        """Check if S3 is properly configured."""
        return self.enabled and isinstance(self.config, dict) and self.config.get("bucket_name")

    def _get_session(self):
        """Get cached boto3 session for connection reuse."""
        if self._session is None and self.enabled:
            try:
                import boto3
                from botocore.config import Config

                # Optimize connection pooling
                config = Config(
                    region_name=self.config.get("region_name", "us-east-1"),
                    retries={"max_attempts": 3, "mode": "adaptive"},
                    max_pool_connections=10,
                )

                session_kwargs = {"config": config}
                if isinstance(self.config, dict):
                    access_key = self.config.get("aws_access_key_id")
                    secret_key = self.config.get("aws_secret_access_key")
                    if access_key and secret_key:
                        session_kwargs.update({"aws_access_key_id": access_key, "aws_secret_access_key": secret_key})

                self._session = boto3.Session(**session_kwargs)
            except Exception as e:
                logger.error(f"Failed to initialize S3 session: {e}")
                self.enabled = False
        return self._session

    def _get_client(self):
        """Get S3 client from cached session."""
        if self._client is None:
            session = self._get_session()
            if session:
                try:
                    self._client = session.client("s3")
                except Exception as e:
                    logger.error(f"Failed to create S3 client: {e}")
                    self.enabled = False
        return self._client

    def _resolve_folder(self, folder_type: str) -> Optional[str]:
        """Resolve S3 folder prefix for the given folder type."""
        if folder_type == "referrals":
            sub = self.folder_map.get("referrals_folder")
        elif folder_type == "preferred_providers":
            sub = self.folder_map.get("preferred_providers_folder")
        else:
            logger.error(f"Unknown folder type: {folder_type}")
            return None

        if not sub:
            return None

        # Normalize folder path
        folder = sub.rstrip("/")
        if not folder.endswith("/"):
            folder += "/"

        # Remove any leading bucket name if accidentally included
        if isinstance(self.config, dict):
            bucket = self.config.get("bucket_name")
            if bucket and folder.startswith(f"{bucket}/"):
                folder = folder[len(bucket) + 1 :]

        return folder.lstrip("/")

    def list_files_batch(self, folder_types: List[str]) -> Dict[str, List[Tuple[str, datetime]]]:
        """List files for multiple folder types in parallel."""
        client = self._get_client()
        if not client or not isinstance(self.config, dict):
            return {ft: [] for ft in folder_types}

        bucket_name = self.config["bucket_name"]
        results = {}

        # Prepare operations for parallel execution
        operations = []
        for folder_type in folder_types:
            folder = self._resolve_folder(folder_type)
            if folder:
                operations.append((folder_type, folder))

        # Execute in parallel
        with ThreadPoolExecutor(max_workers=min(len(operations), 4)) as executor:
            future_to_folder = {
                executor.submit(self._list_folder_files, client, bucket_name, folder): folder_type
                for folder_type, folder in operations
            }

            for future in as_completed(future_to_folder):
                folder_type = future_to_folder[future]
                try:
                    results[folder_type] = future.result()
                except Exception as e:
                    logger.error(f"Failed to list files for {folder_type}: {e}")
                    results[folder_type] = []

        # Ensure all requested folder types have entries
        for folder_type in folder_types:
            if folder_type not in results:
                results[folder_type] = []

        return results

    def _list_folder_files(self, client, bucket_name: str, folder: str) -> List[Tuple[str, datetime]]:
        """List files in a single folder."""
        try:
            paginator = client.get_paginator("list_objects_v2")
            page_iterator = paginator.paginate(Bucket=bucket_name, Prefix=folder, PaginationConfig={"PageSize": 100})

            files = []
            for page in page_iterator:
                if "Contents" in page:
                    for obj in page["Contents"]:
                        # Skip the folder itself
                        if obj["Key"] == folder:
                            continue
                        # Include Excel and CSV files
                        if obj["Key"].lower().endswith((".xlsx", ".xls", ".csv")):
                            filename = obj["Key"].split("/")[-1]
                            files.append((filename, obj["LastModified"]))

            return sorted(files, key=lambda x: x[1], reverse=True)

        except Exception as e:
            logger.error(f"Failed to list files in folder '{folder}': {e}")
            return []

    def download_files_batch(self, downloads: List[Tuple[str, str]]) -> Dict[str, Optional[bytes]]:
        """Download multiple files in parallel.

        Args:
            downloads: List of (folder_type, filename) tuples

        Returns:
            Dict mapping "{folder_type}:{filename}" to file bytes or None
        """
        client = self._get_client()
        if not client or not isinstance(self.config, dict):
            return {f"{ft}:{fn}": None for ft, fn in downloads}

        bucket_name = self.config["bucket_name"]
        results = {}

        # Prepare download operations
        operations = []
        for folder_type, filename in downloads:
            folder = self._resolve_folder(folder_type)
            if folder:
                s3_key = f"{folder}{filename}"
                key = f"{folder_type}:{filename}"
                operations.append((key, s3_key))

        # Execute downloads in parallel
        with ThreadPoolExecutor(max_workers=min(len(operations), 3)) as executor:
            future_to_key = {
                executor.submit(self._download_single_file, client, bucket_name, s3_key): key
                for key, s3_key in operations
            }

            for future in as_completed(future_to_key):
                key = future_to_key[future]
                try:
                    results[key] = future.result()
                except Exception as e:
                    logger.error(f"Failed to download {key}: {e}")
                    results[key] = None

        return results

    def _download_single_file(self, client, bucket_name: str, s3_key: str) -> Optional[bytes]:
        """Download a single file from S3."""
        try:
            buffer = BytesIO()
            client.download_fileobj(bucket_name, s3_key, buffer)
            buffer.seek(0)
            return buffer.getvalue()
        except Exception as e:
            logger.error(f"Failed to download file '{s3_key}': {e}")
            return None

    def download_file(self, folder_type: str, filename: str) -> Optional[bytes]:
        """Download a specific file from S3."""
        client = self._get_client()
        if not client or not isinstance(self.config, dict):
            return None

        folder = self._resolve_folder(folder_type)
        if not folder:
            return None

        s3_key = f"{folder}{filename}"
        return self._download_single_file(client, self.config["bucket_name"], s3_key)

    def download_latest_files_batch(self, folder_types: List[str]) -> Dict[str, Optional[Tuple[bytes, str]]]:
        """Download the latest file from multiple folders in parallel."""
        # First get file listings
        file_listings = self.list_files_batch(folder_types)

        # Prepare downloads for latest files
        downloads = []
        for folder_type in folder_types:
            files = file_listings.get(folder_type, [])
            if files:
                latest_filename = files[0][0]  # Files are already sorted by date desc
                downloads.append((folder_type, latest_filename))

        if not downloads:
            return {ft: None for ft in folder_types}

        # Download files
        download_results = self.download_files_batch(downloads)

        # Format results
        results = {}
        for folder_type, filename in downloads:
            key = f"{folder_type}:{filename}"
            file_bytes = download_results.get(key)
            if file_bytes:
                results[folder_type] = (file_bytes, filename)
            else:
                results[folder_type] = None

        # Ensure all requested folder types have entries
        for folder_type in folder_types:
            if folder_type not in results:
                results[folder_type] = None

        return results


# Cached instances and functions for Streamlit
@st.cache_resource
def get_optimized_s3_client(folder_map_key: Optional[str] = None) -> OptimizedS3DataClient:
    """Get cached optimized S3 client instance."""
    folder_map = None
    if folder_map_key and folder_map_key in st.session_state:
        folder_map = st.session_state[folder_map_key]
    return OptimizedS3DataClient(folder_map=folder_map)


@st.cache_data(ttl=300, show_spinner=False)
def get_s3_files_optimized(
    folder_types: List[str], folder_map_key: Optional[str] = None
) -> Dict[str, List[Tuple[str, datetime]]]:
    """Cached function to get file listings for multiple folder types."""
    client = get_optimized_s3_client(folder_map_key)
    if not client.is_configured():
        return {ft: [] for ft in folder_types}

    return client.list_files_batch(folder_types)


@st.cache_data(ttl=60, show_spinner=False)  # Shorter TTL for latest files
def get_latest_s3_files_optimized(
    folder_types: List[str], folder_map_key: Optional[str] = None
) -> Dict[str, Optional[Tuple[bytes, str]]]:
    """Cached function to download latest files from multiple folders."""
    client = get_optimized_s3_client(folder_map_key)
    if not client.is_configured():
        return {ft: None for ft in folder_types}

    return client.download_latest_files_batch(folder_types)
