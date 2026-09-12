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

Returns structured JSON containing:
- `answer`: Markdown-formatted explanation, rich tabular breakdown, or pedagogical action plan.
- `suggestions`: Array of contextually relevant follow-up questions tailored to the query and role.
- `role`: Current user authentication context (`"student"` or `"teacher"`).

Example response:

```json
{
  "answer": "### 🎯 Your Real-Time Academic Scorecard\n\n- **Predicted Score:** `78.4 / 100`...",
  "suggestions": ["Why am I at risk?", "Generate 14-day study plan", "What if I study 5 more hours?"],
  "role": "student"
}
```

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
