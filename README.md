## API documentation (Swagger)

I used **drf-spectacular** to generate OpenAPI docs and a Swagger UI.

- Swagger UI (interactive): `http://127.0.0.1:8000/api/docs/swagger/`
- OpenAPI JSON: `http://127.0.0.1:8000/api/schema/`

Authentication: Token Authentication (`Authorization: Token <token>`). Obtain a token with `POST /api/login/`.

Examples:
- I added request & response examples in the Swagger UI for the following actions:
  - `POST /api/announcements/{id}/request_job/` — contractor request (example request & created ContractorRequest response).
  - `POST /api/announcements/{id}/assign/` — owner assigns contractor (example request & announcement response).
  - `POST /api/announcements/{id}/mark_done/` and `confirm_done/` — examples showing status transitions.
  - `POST /api/tickets/{id}/post_message/` — message request & response examples.
  - `POST /api/comments/` — example request & response (only allowed after confirmation).
