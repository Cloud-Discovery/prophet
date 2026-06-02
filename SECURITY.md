# Security Policy

## Supported Versions

We actively support the following versions with security updates:

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take security vulnerabilities seriously. If you discover a security vulnerability, please follow these steps:

### 1. **Do NOT** open a public issue

Security vulnerabilities should be reported privately to protect users.

### 2. Email Security Team

Please email security details to: **security@oneprocloud.com**

Include the following information:

- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

### 3. Response Timeline

- **Initial Response**: Within 48 hours
- **Status Update**: Within 7 days
- **Fix Timeline**: Depends on severity, typically within 30 days

### 4. Disclosure Policy

- We will acknowledge receipt of your report
- We will keep you informed of the progress
- We will credit you in the security advisory (if desired)
- We will coordinate public disclosure after a fix is available

## Security Best Practices

When using Prophet, please follow these security best practices:

1. **Environment Variables**: Never commit `.env` files with real credentials
2. **Secret Keys**: Always change default secret keys in production
3. **Encryption Keys**: Generate strong encryption keys using the provided tool
4. **Database**: Use strong passwords for database connections
5. **Network**: Restrict network access to the application
6. **Updates**: Keep dependencies up to date
7. **Authentication**: Use strong passwords for user accounts
8. **HTTPS**: Always use HTTPS in production environments

## Known Security Considerations

- The application handles sensitive host credentials - ensure proper access control
- Collected data may contain sensitive information - ensure proper data protection
- API endpoints should be protected with authentication
- File uploads should be validated and sanitized

## Security Updates

Security updates will be announced through:

- GitHub Security Advisories
- Release notes in CHANGELOG.md
- Email notifications (for registered users)

Thank you for helping keep Prophet secure!
