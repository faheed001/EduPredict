# Security Policy

## Scope
EduPredict 3.0 is an academic prototype. Security controls are included for demonstration and development, but a production deployment requires additional review.

## Included protections
- Password hashing with Werkzeug.
- Session-based authentication.
- Student/teacher role checks.
- CSRF protection for state-changing requests.
- HTTP security headers.
- Input validation and request-size limits.
- Environment-based secret configuration.

## Do not commit
Never commit passwords, API keys, `.env` files, production databases, real student records, or other confidential information.

## Production recommendations
- Set a strong `EDUPREDICT_SECRET`.
- Run behind HTTPS.
- Use a production WSGI server and reverse proxy.
- Restrict database/file permissions.
- Add centralized monitoring and audit retention controls.
- Perform dependency and penetration testing before real deployment.

## Reporting
For a security issue, do not publish sensitive exploit details in a public issue. Contact the project maintainer privately first.
