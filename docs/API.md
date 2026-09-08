# EduPredict 3.0 API Reference

The application exposes JSON endpoints for health, prediction, what-if analysis, student updates, trends, student listing and the EduPredict Assistant. Authentication/CSRF requirements depend on the endpoint and session state.

## Health

`GET /api/health`

Returns application/model/database status and feature metadata.

## Prediction

`POST /api/predict`

Accepts a validated feature payload and returns a prediction response. The endpoint is protected and should be used with the application's authentication and CSRF rules.

## What-if analysis

`POST /api/what-if`

Returns a baseline prediction and one-factor what-if score changes without saving the hypothetical values.

## Assistant

`POST /api/assistant`

Example request:

```json
{"message":"What features does EduPredict have?"}
```

Returns JSON containing the assistant answer and, where applicable, student-specific context.

## Student update

`POST /api/student/update`

Updates the logged-in student's supported profile/performance information subject to validation and authorization.

## Students

`GET /api/students`

Returns student information available to an authorized teacher context.

## Student trend

`GET /api/student/<student_id>/trend`

Returns trend/history information for an authorized student record.

## Response and error handling

Clients should handle standard HTTP status codes such as 200, 400, 403 and 404. Do not expose secrets or internal exception details in production.
