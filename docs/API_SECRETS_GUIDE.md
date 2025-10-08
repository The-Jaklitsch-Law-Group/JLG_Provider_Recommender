# API Settings and Secrets Management Guide

This guide demonstrates how to properly add and manage API settings and credentials in your JLG Provider Recommender Streamlit application.

## 🔐 Secrets Management Overview

Streamlit provides a secure way to manage sensitive information like API keys, database credentials, and other secrets through the `secrets.toml` file and Streamlit Cloud's secrets management.

## 📁 File Structure

```
.streamlit/
├── secrets.toml          # Local secrets (DO NOT COMMIT)
└── config.toml          # Public configuration

src/utils/
├── config.py            # Configuration management utilities
└── enhanced_geocoding.py # Example API integration

pages/
└── 40_🔧_Configuration.py # Configuration dashboard
```

## 🛠️ Setting Up Secrets

### 1. Local Development (.streamlit/secrets.toml)

The `secrets.toml` file should contain all your sensitive configuration:

```toml
# Geocoding APIs
[geocoding]
google_maps_api_key = "your_google_maps_api_key_here"
google_maps_enabled = true
nominatim_user_agent = "jlg_provider_recommender"
request_timeout = 10
rate_limit_delay = 1.0
max_retries = 3

# Database connection
[database]
url = "postgresql://username:password@localhost:5432/dbname"
username = "your_db_username"
password = "your_db_password"
host = "localhost"
port = 5432
database_name = "jlg_provider_db"
ssl_mode = "require"

# External APIs
[apis]
filevine_api_key = "your_filevine_api_key"
filevine_base_url = "https://api.filevine.com"
filevine_org_id = "your_organization_id"

# AWS S3 Configuration
[s3]
aws_access_key_id = "your_aws_access_key_id"
aws_secret_access_key = "your_aws_secret_access_key"
bucket_name = "your-s3-bucket-name"
region_name = "us-east-1"
referrals_folder = "referrals"
preferred_providers_folder = "preferred_providers"
use_latest_file = true

# Email configuration
smtp_server = "smtp.gmail.com"
smtp_port = 587
smtp_username = "your_email@company.com"
smtp_password = "your_app_password"
from_email = "noreply@company.com"

# Analytics
google_analytics_id = "GA_MEASUREMENT_ID"
sentry_dsn = "your_sentry_dsn"

# Application settings
[app]
environment = "development"
debug_mode = true
log_level = "DEBUG"

# Security settings
[security]
allowed_hosts = ["localhost", "127.0.0.1", "*.streamlit.app"]
max_requests_per_hour = 1000
max_geocoding_requests_per_day = 2500
session_timeout_minutes = 60

# Caching configuration
[cache]
ttl_hours = 24
max_size_mb = 100
redis_url = ""
enable_redis = false
```

### 2. Streamlit Cloud Configuration

When deploying to Streamlit Cloud:

1. Go to your app's settings in Streamlit Cloud
2. Navigate to the "Secrets" section
3. Paste your `secrets.toml` content (without the actual secret values)
4. Fill in the real API keys and credentials

## 💻 Using Secrets in Code

### Basic Secret Access

```python
import streamlit as st
from src.utils.config import get_secret, get_api_config

# Simple secret access
api_key = get_secret('geocoding.google_maps_api_key', '')
debug_mode = get_secret('app.debug_mode', False)

# Structured configuration access
geocoding_config = get_api_config('geocoding')
google_api_key = geocoding_config['google_maps_api_key']
timeout = geocoding_config['request_timeout']
```

### API Integration Example

```python
from src.utils.config import get_api_config, is_api_enabled

def make_api_request():
    # Check if API is enabled and configured
    if not is_api_enabled('google_maps'):
        st.warning("Google Maps API not configured")
        return None
    
    # Get API configuration
    config = get_api_config('geocoding')
    api_key = config['google_maps_api_key']
    timeout = config['request_timeout']
    
    # Make the API request
    # ... your API code here
```

### Environment-Aware Configuration

```python
from src.utils.config import get_app_config

app_config = get_app_config()

if app_config['environment'] == 'production':
    # Production settings
    st.set_page_config(
        page_title="JLG Provider Recommender",
        page_icon="🏥"
    )
else:
    # Development settings
    st.set_page_config(
        page_title="[DEV] JLG Provider Recommender",
        page_icon="🛠️"
    )
    
    if app_config['debug_mode']:
        st.sidebar.info("Debug mode enabled")
```

## 🔑 API Key Setup Instructions

### Google Maps Geocoding API

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable the "Geocoding API"
4. Create credentials (API key)
5. Restrict the API key to your domain/IPs
6. Add to secrets:

```toml
[geocoding]
google_maps_api_key = "AIza..."
google_maps_enabled = true
```

### Filevine API

1. Log into your Filevine account
2. Go to Settings → API Keys
3. Generate a new API key
4. Note your Organization ID
5. Add to secrets:

```toml
[apis]
filevine_api_key = "your_api_key"
filevine_org_id = "your_org_id"
```

### Database Connection

For PostgreSQL:

```toml
[database]
url = "postgresql://username:password@host:port/database"
# OR individual components:
host = "your_db_host"
port = 5432
database_name = "your_db_name"
username = "your_username"
password = "your_password"
```

### Email (SMTP)

For Gmail with App Passwords:

```toml
[apis]
smtp_server = "smtp.gmail.com"
smtp_port = 587
smtp_username = "your_email@gmail.com"
smtp_password = "your_16_char_app_password"
from_email = "noreply@yourcompany.com"
```

### AWS S3 for Data Storage

To enable automatic data pulls from S3:

1. **Create AWS IAM User**:
   - Go to [AWS IAM Console](https://console.aws.amazon.com/iam/)
   - Create a new IAM user for the application
   - Attach policy: `AmazonS3ReadOnlyAccess` (or create custom policy)
   - Generate access keys

2. **Configure S3 Bucket**:
   - Create an S3 bucket (or use existing)
   - Create folders: `referrals/` and `preferred_providers/`
   - Upload Excel files to these folders
   - Set appropriate bucket policies

3. **Add to secrets**:

```toml
[s3]
aws_access_key_id = "AKIA..."
aws_secret_access_key = "your_secret_key"
bucket_name = "jlg-provider-data"
region_name = "us-east-1"
referrals_folder = "referrals"
preferred_providers_folder = "preferred_providers"
use_latest_file = true
```

4. **Custom S3 Policy (Optional)**:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::jlg-provider-data",
        "arn:aws:s3:::jlg-provider-data/*"
      ]
    }
  ]
}
```

## 🛡️ Security Best Practices

### 1. Never Commit Secrets
- Add `.streamlit/secrets.toml` to `.gitignore`
- Use placeholder values in version control
- Rotate API keys regularly

### 2. Environment Separation
```toml
[app]
environment = "production"  # or "development", "staging"
```

### 3. Rate Limiting
```toml
[security]
max_requests_per_hour = 1000
max_geocoding_requests_per_day = 2500
```

### 4. Input Validation
```python
from src.utils.config import validate_configuration

issues = validate_configuration()
if issues:
    for component, issue in issues.items():
        st.error(f"{component}: {issue}")
```

## 📊 Configuration Monitoring

### Built-in Dashboard

Visit `/Configuration` page in your app to:
- View API status and configuration
- Test API connections
- Monitor rate limits
- Validate security settings

### Programmatic Monitoring

```python
from src.utils.enhanced_geocoding import test_all_apis

# Test all APIs
results = test_all_apis()
for api, status in results.items():
    if not status.get('working'):
        st.error(f"API {api} is not working!")
```

## 🚀 Deployment Checklist

### Before Deploying to Production:

1. **Environment Settings**
   - [ ] Set `app.environment = "production"`
   - [ ] Set `app.debug_mode = false`
   - [ ] Set appropriate `app.log_level`

2. **Security Review**
   - [ ] API keys configured in Streamlit Cloud secrets
   - [ ] Rate limits appropriate for production
   - [ ] Allowed hosts configured correctly
   - [ ] No secrets in git repository

3. **API Configuration**
   - [ ] All required APIs enabled and tested
   - [ ] Fallback services configured
   - [ ] Error handling implemented

4. **Performance**
   - [ ] Cache TTL values optimized
   - [ ] Rate limiting in place
   - [ ] Monitoring configured

## 🔧 Troubleshooting

### Common Issues

1. **"KeyError" when accessing secrets**
   ```python
   # Wrong:
   api_key = st.secrets['api']['key']
   
   # Right:
   api_key = get_secret('api.key', '')
   ```

2. **Secrets not updating in Streamlit Cloud**
   - Clear browser cache
   - Restart the app
   - Check secrets format in Cloud console

3. **API authentication failing**
   - Verify API keys in configuration dashboard
   - Check API key restrictions (IP/domain)
   - Monitor rate limits

### Debug Mode

Enable debug logging in development:

```toml
[app]
debug_mode = true
log_level = "DEBUG"
```

Then use:

```python
import logging
logger = logging.getLogger(__name__)

if get_app_config()['debug_mode']:
    logger.debug("API request details: %s", request_data)
```

## 📚 Additional Resources

- [Streamlit Secrets Management](https://docs.streamlit.io/streamlit-community-cloud/deploy-an-app/connect-to-data-sources/secrets-management)
- [Google Maps API Documentation](https://developers.google.com/maps/documentation/geocoding)
- [Filevine API Documentation](https://developer.filevine.com/)
- [PostgreSQL Connection Strings](https://www.postgresql.org/docs/current/libpq-connect.html#LIBPQ-CONNSTRING)

---

This configuration system provides a robust, secure, and maintainable way to manage all your API credentials and application settings across different environments.