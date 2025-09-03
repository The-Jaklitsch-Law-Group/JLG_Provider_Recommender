# Security Policy

## Supported Versions

We actively support the following versions with security updates:

| Version | Supported          |
| ------- | ------------------ |
| 2.0.x   | :white_check_mark: |
| 1.x.x   | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability, please follow these steps:

1. **DO NOT** open a public issue for security vulnerabilities
2. Email us directly at [info@jaklitschlawgroup.com](mailto:info@jaklitschlawgroup.com) with:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

## Security Considerations

### Data Privacy
- This application processes healthcare provider information
- No personally identifiable information (PII) should be included in datasets
- All sensitive data should be handled according to applicable privacy laws

### API Keys and Secrets
- Never commit API keys, passwords, or other secrets to version control
- Use environment variables or Streamlit Cloud secrets for sensitive configuration
- Regularly rotate API keys and credentials

### Deployment Security
- Production deployment includes security hardening configurations
- File watching and debug features are disabled in production
- CORS and XSRF protection are configured appropriately

## Best Practices

1. Keep dependencies updated and monitor for known vulnerabilities
2. Use the provided `.gitignore` to prevent accidental inclusion of sensitive files
3. Review all data files before public deployment
4. Enable appropriate access controls for production deployments

## Response Timeline

- We aim to respond to security reports within 48 hours
- Critical vulnerabilities will be addressed within 7 days
- Non-critical issues will be addressed in the next minor release

Thank you for helping keep this project secure!
