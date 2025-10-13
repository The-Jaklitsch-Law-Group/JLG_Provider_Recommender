"""Tests for S3 data client functionality."""

"""Tests for S3 data client functionality."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def mock_s3_config():
    """Mock S3 configuration."""
    return {
        "aws_access_key_id": "test_key",
        "aws_secret_access_key": "test_secret",
        "bucket_name": "test-bucket",
        "region_name": "us-east-1",
        "referrals_folder": "referrals",
        "preferred_providers_folder": "preferred_providers",
        "use_latest_file": True,
    }


@pytest.fixture
def mock_boto3_client():
    """Mock boto3 S3 client."""
    client = MagicMock()
    return client


class TestS3DataClient:
    """Test cases for S3DataClient."""

    @patch("src.utils.config.get_api_config")
    @patch("src.utils.config.is_api_enabled")
    def test_client_initialization(self, mock_is_enabled, mock_get_config, mock_s3_config):
        """Test S3 client initialization."""
        from src.utils.s3_client_optimized import S3DataClient

        mock_is_enabled.return_value = True
        mock_get_config.return_value = mock_s3_config

        client = S3DataClient(folder_map={})

        assert client.is_configured() is True
        mock_get_config.assert_called_once_with("s3")

    @patch("src.utils.config.get_api_config")
    @patch("src.utils.config.is_api_enabled")
    def test_client_not_configured(self, mock_is_enabled, mock_get_config, mock_s3_config):
        """Test S3 client when not configured."""
        from src.utils.s3_client_optimized import S3DataClient

        mock_is_enabled.return_value = False
        mock_get_config.return_value = mock_s3_config

        client = S3DataClient(folder_map={})

        assert client.is_configured() is False

    @patch("boto3.Session")
    @patch("src.utils.config.get_api_config")
    @patch("src.utils.config.is_api_enabled")
    def test_list_files_in_folder(self, mock_is_enabled, mock_get_config, mock_boto3_session, mock_s3_config):
        """Test listing files in S3 folder."""
        from src.utils.s3_client_optimized import S3DataClient

        mock_is_enabled.return_value = True
        mock_get_config.return_value = mock_s3_config

        # Mock S3 client and session
        mock_client = MagicMock()
        mock_session = MagicMock()
        mock_session.client.return_value = mock_client
        mock_boto3_session.return_value = mock_session

        # Mock paginator for list_objects_v2
        mock_paginator = MagicMock()
        mock_client.get_paginator.return_value = mock_paginator
        mock_page_iterator = [
            {
                "Contents": [
                    {"Key": "referrals/file1.csv", "LastModified": datetime(2024, 1, 1, 12, 0, 0)},
                    {"Key": "referrals/file2.csv", "LastModified": datetime(2024, 1, 2, 12, 0, 0)},
                ]
            }
        ]
        mock_paginator.paginate.return_value = mock_page_iterator

        client = S3DataClient(folder_map={})
        files = client.list_files_in_folder("referrals")

        assert len(files) == 2
        # Should be sorted by date descending
        assert files[0][0] == "file2.csv"
        assert files[1][0] == "file1.csv"

    @patch("boto3.Session")
    @patch("src.utils.config.get_api_config")
    @patch("src.utils.config.is_api_enabled")
    def test_download_file(self, mock_is_enabled, mock_get_config, mock_boto3_session, mock_s3_config):
        """Test downloading a file from S3."""
        from src.utils.s3_client_optimized import S3DataClient

        mock_is_enabled.return_value = True
        mock_get_config.return_value = mock_s3_config

        # Mock S3 client and session
        mock_client = MagicMock()
        mock_session = MagicMock()
        mock_session.client.return_value = mock_client
        mock_boto3_session.return_value = mock_session

        # Mock file download
        test_data = b"test file content"

        def mock_download_fileobj(bucket, key, buffer):
            buffer.write(test_data)

        mock_client.download_fileobj.side_effect = mock_download_fileobj

        client = S3DataClient(folder_map={})
        result = client.download_file("referrals", "test.csv")

        assert result == test_data

    @patch("boto3.Session")
    @patch("src.utils.config.get_api_config")
    @patch("src.utils.config.is_api_enabled")
    def test_download_latest_file(self, mock_is_enabled, mock_get_config, mock_boto3_session, mock_s3_config):
        """Test downloading the latest file from S3."""
        from src.utils.s3_client_optimized import S3DataClient

        mock_is_enabled.return_value = True
        mock_get_config.return_value = mock_s3_config

        # Mock S3 client and session
        mock_client = MagicMock()
        mock_session = MagicMock()
        mock_session.client.return_value = mock_client
        mock_boto3_session.return_value = mock_session

        # Mock paginator for list_objects_v2
        mock_paginator = MagicMock()
        mock_client.get_paginator.return_value = mock_paginator
        mock_page_iterator = [
            {
                "Contents": [
                    {"Key": "referrals/old_file.csv", "LastModified": datetime(2024, 1, 1, 12, 0, 0)},
                    {"Key": "referrals/latest_file.csv", "LastModified": datetime(2024, 1, 2, 12, 0, 0)},
                ]
            }
        ]
        mock_paginator.paginate.return_value = mock_page_iterator

        # Mock file download
        test_data = b"latest file content"

        def mock_download_fileobj(bucket, key, buffer):
            buffer.write(test_data)

        mock_client.download_fileobj.side_effect = mock_download_fileobj

        client = S3DataClient(folder_map={})
        result = client.download_latest_file("referrals")

        assert result is not None
        file_bytes, filename = result
        assert file_bytes == test_data
        assert filename == "latest_file.csv"

    @patch("boto3.client")
    @patch("src.utils.config.get_api_config")
    @patch("src.utils.config.is_api_enabled")
    def test_download_latest_file_no_files(self, mock_is_enabled, mock_get_config, mock_boto3_client, mock_s3_config):
        """Test downloading latest file when no files exist."""
        from src.utils.s3_client_optimized import S3DataClient

        mock_is_enabled.return_value = True
        mock_get_config.return_value = mock_s3_config

        # Mock S3 client
        mock_client = MagicMock()
        mock_boto3_client.return_value = mock_client

        # Mock empty list response
        mock_client.list_objects_v2.return_value = {}

        client = S3DataClient(folder_map={})
        result = client.download_latest_file("referrals")

        assert result is None

    @patch("src.utils.config.get_api_config")
    @patch("src.utils.config.is_api_enabled")
    def test_client_not_configured_returns_empty(self, mock_is_enabled, mock_get_config, mock_s3_config):
        """Test that disabled client returns empty results."""
        from src.utils.s3_client_optimized import S3DataClient

        mock_is_enabled.return_value = False
        mock_get_config.return_value = mock_s3_config

        client = S3DataClient(folder_map={})

        # Should return empty/None for all operations
        assert client.list_files_in_folder("referrals") == []
        assert client.download_file("referrals", "test.csv") is None
        assert client.download_latest_file("referrals") is None

    @patch("src.utils.config.get_api_config")
    @patch("src.utils.config.is_api_enabled")
    def test_validate_configuration_reports_missing(self, mock_is_enabled, mock_get_config, mock_s3_config):
        """validate_configuration should return messages for missing keys."""
        from src.utils.s3_client_optimized import S3DataClient

        # Provide an incomplete config (missing bucket and secret)
        incomplete = mock_s3_config.copy()
        incomplete.pop("bucket_name", None)
        incomplete.pop("aws_secret_access_key", None)

        mock_is_enabled.return_value = True
        mock_get_config.return_value = incomplete

        client = S3DataClient(folder_map={"top_folder": ""})
        issues = client.validate_configuration()

        assert "bucket_name" in issues
        assert "aws_secret_access_key" in issues

    @patch("src.utils.config.get_api_config")
    @patch("src.utils.config.is_api_enabled")
    def test_validate_configuration_no_issues_when_present(self, mock_is_enabled, mock_get_config, mock_s3_config):
        """validate_configuration returns empty dict when all keys present."""
        from src.utils.s3_client_optimized import S3DataClient

        mock_is_enabled.return_value = True
        mock_get_config.return_value = mock_s3_config

        client = S3DataClient(folder_map={"top_folder": ""})
        issues = client.validate_configuration()

        assert issues == {}
