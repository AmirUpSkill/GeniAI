# Geni Auth Layer PRD

## 1. Purpose

The Auth Layer lets users enter Geni through Google OAuth and keeps their browser authenticated with a secure server-side session. It is the first production-style layer in the application because every chat, profile, and future AI workflow depends on knowing the current user and enforcing ownership.

For this learning project, the Auth Layer is also a testing target. It demonstrates how to test third-party OAuth integration, cookie-based sessions, database-backed authentication, protected endpoints, and negative authentication cases.

## 2. Current Scope

The current implementation supports:

- Google OAuth sign-in.
- First-login user creation.
- Reuse of existing Google users on later login.
- HTTP-only session cookies.
- Hashed session tokens stored in PostgreSQL.
- Current-user lookup through `/api/auth/me`.
- Logout with server-side session deletion and browser cookie clearing.
- Structured authentication errors.

The current implementation does not include:

- Email/password login.
- Refresh tokens.
- Multiple OAuth providers.
- Role-based permissions.
- Redirecting back to arbitrary post-login URLs from the callback.

## 3. User Stories

### Start Google Sign-In

As a visitor, I can click "Continue with Google" from the frontend so that I can start the Google OAuth login flow.

Acceptance criteria:

- The frontend builds a login URL using `/api/auth/google/login`.
- The request includes a `redirectUri` query parameter pointing to the frontend chat page.
- The backend redirects the browser to Google's OAuth authorization URL.

### Complete Google Login

As a Google user with a verified email, I can complete OAuth so that I am signed in and sent to the chat app.

Acceptance criteria:

- The backend exchanges the Google callback `code` for Google user information.
- Login is rejected if Google reports that the email is not verified.
- A new local user is created when the Google user has not signed in before.
- An existing local user is reused when the Google `provider_user_id` already exists.
- A new server-side auth session is created.
- The browser receives a session cookie.
- The user is redirected to `{FRONTEND_URL}/chat`.

### Load Current User

As a returning authenticated user, I can load my current profile/session through `/api/auth/me` so that the frontend can determine whether I am signed in.

Acceptance criteria:

- The frontend sends credentials with the request.
- The backend reads the configured session cookie.
- The backend hashes the raw cookie token and looks up a non-expired session.
- The endpoint returns the authenticated user's public fields.
- Missing, empty, invalid, or expired sessions return `401`.

### Logout

As an authenticated user, I can log out so that my server-side session is invalidated and my browser cookie is cleared.

Acceptance criteria:

- The frontend sends `POST /api/auth/logout`.
- The backend deletes the matching auth session if a cookie is present.
- The backend returns a successful logout response even if no cookie is present.
- The response clears the configured session cookie.

### Reject Unauthenticated Access

As an unauthenticated user, protected endpoints reject me with a structured `401` error so that the frontend can handle auth failures consistently.

Acceptance criteria:

- Authenticated dependencies reject missing or empty cookies.
- Invalid or expired session tokens are rejected.
- Error responses use the shared application error shape.

## 4. User Flow

1. The visitor opens the frontend auth page.
2. The frontend calls `GET /api/auth/me` to check for an existing session.
3. If the session exists, the frontend sends the user to `/chat`.
4. If the session check fails, the user stays on the auth page.
5. The user clicks "Continue with Google".
6. The frontend navigates to `/api/auth/google/login?redirectUri={frontendChatUrl}`.
7. The backend builds a Google OAuth URL and redirects to Google.
8. Google redirects back to `/api/auth/google/callback?code={code}&state={state}`.
9. The backend exchanges the code with Google, validates the email, creates or reuses the user, creates an auth session, sets the session cookie, and redirects to `{FRONTEND_URL}/chat`.
10. Later API calls include the session cookie with `credentials: "include"`.
11. Logout deletes the server-side session and clears the browser cookie.

## 5. API Contract

The backend mounts auth routes under the global API prefix, so the public paths below use `/api`.

| Method | Endpoint | Behavior |
| --- | --- | --- |
| `GET` | `/api/auth/google/login` | Builds a Google OAuth URL and redirects with `302`. Accepts optional `redirectUri` query parameter. |
| `GET` | `/api/auth/google/callback` | Exchanges Google `code`, creates or reuses user, creates server session, sets cookie, redirects to `{FRONTEND_URL}/chat`. |
| `GET` | `/api/auth/me` | Returns the authenticated user from the session cookie. |
| `POST` | `/api/auth/logout` | Deletes the current session if present and clears the session cookie. |

### `GET /api/auth/google/login`

Query parameters:

| Name | Type | Required | Description |
| --- | --- | --- | --- |
| `redirectUri` | string | No | Frontend URL that the caller wants to return to after login. Currently stored as OAuth `state`. |

Response:

- Status: `302 Found`
- `Location`: Google OAuth authorization URL.

Google authorization parameters currently include:

- `client_id`
- `redirect_uri`
- `response_type=code`
- `scope=openid email profile`
- `access_type=offline`
- `prompt=consent`
- `state`, when provided

### `GET /api/auth/google/callback`

Query parameters:

| Name | Type | Required | Description |
| --- | --- | --- | --- |
| `code` | string | Yes | OAuth authorization code returned by Google. |
| `state` | string | No | OAuth state value. Currently accepted but ignored by the callback implementation. |

Success response:

- Status: `302 Found`
- `Location`: `{FRONTEND_URL}/chat`
- Sets the configured session cookie.

Failure response:

```json
{
  "success": false,
  "error": {
    "code": "AUTH_PROVIDER_FAILED",
    "message": "Google authentication failed."
  }
}
```

When Google returns an unverified email, the service raises:

```json
{
  "success": false,
  "error": {
    "code": "AUTH_EMAIL_NOT_VERIFIED",
    "message": "Google email is not verified."
  }
}
```

Both provider failures are currently returned with HTTP `401`.

### `GET /api/auth/me`

Request:

- No body.
- Requires the configured session cookie.

Success response:

```json
{
  "success": true,
  "data": {
    "id": "usr_...",
    "email": "user@example.com",
    "fullName": "User Name",
    "avatarUrl": "https://example.com/avatar.png",
    "provider": "google",
    "createdAt": "2026-07-06T00:00:00Z",
    "updatedAt": "2026-07-06T00:00:00Z"
  }
}
```

Notes:

- `avatarUrl` can be `null`.
- Dates are serialized by Pydantic from backend `datetime` values.

Unauthorized response:

```json
{
  "success": false,
  "error": {
    "code": "AUTH_UNAUTHORIZED",
    "message": "User is not authenticated."
  }
}
```

### `POST /api/auth/logout`

Request:

- No body.
- Session cookie is optional.

Success response:

```json
{
  "success": true,
  "message": "User logged out successfully."
}
```

Response cookie behavior:

- Clears the configured session cookie.
- Uses the same path, secure, SameSite, and HttpOnly settings as session cookie configuration.

## 6. Session and Cookie Behavior

The browser stores the raw session token in a cookie. The backend never stores that raw token in the database. Instead, it computes an HMAC-SHA256 hash using `SESSION_SECRET_KEY` and stores the hash in `auth_sessions.session_token_hash`.

Configured defaults:

| Setting | Default | Purpose |
| --- | --- | --- |
| `SESSION_COOKIE_NAME` | `geni_session` | Browser cookie name. |
| `SESSION_SECRET_KEY` | `change-me-in-production` | Secret used to hash raw session tokens. |
| `SESSION_TTL_DAYS` | `7` | Session lifetime and cookie max age. |
| `SESSION_COOKIE_SECURE` | `false` | Whether the browser requires HTTPS for the cookie. |
| `SESSION_COOKIE_SAMESITE` | `lax` | Cookie SameSite policy. |

Cookie attributes:

- `HttpOnly`
- `path=/`
- `max_age = SESSION_TTL_DAYS * 24 * 60 * 60`
- Configurable `Secure`
- Configurable `SameSite`

Session lookup:

1. Read the raw token from the configured cookie.
2. Reject missing or empty tokens.
3. Hash the token with `SESSION_SECRET_KEY`.
4. Query `auth_sessions` for the hash.
5. Require `expires_at` to be greater than the current time.
6. Return the joined `users` record.

Logout:

1. Read the raw token from the configured cookie.
2. If present, hash the token.
3. Delete the matching `auth_sessions` row.
4. Commit the transaction.
5. Clear the browser cookie.

## 7. Data Model

### `users`

Stores local user records created from Google profile data.

| Column | Purpose |
| --- | --- |
| `id` | Primary key, generated with `usr_` prefix. |
| `email` | Unique Google email address. |
| `full_name` | User display name from Google. |
| `avatar_url` | Optional Google profile picture URL. |
| `provider` | OAuth provider name, currently `google`. |
| `provider_user_id` | Unique Google subject identifier. |
| `created_at` | Creation timestamp. |
| `updated_at` | Update timestamp. |

Indexes and constraints:

- Primary key on `id`.
- Unique index on `email`.
- Unique index on `provider_user_id`.

### `auth_sessions`

Stores server-side authentication sessions.

| Column | Purpose |
| --- | --- |
| `id` | Primary key, generated with `ses_` prefix. |
| `user_id` | Foreign key to `users.id`. |
| `session_token_hash` | Unique HMAC-SHA256 hash of the raw browser token. |
| `expires_at` | Session expiry timestamp. |
| `created_at` | Creation timestamp. |
| `updated_at` | Update timestamp. |

Indexes and constraints:

- Primary key on `id`.
- Foreign key from `auth_sessions.user_id` to `users.id`.
- `auth_sessions.user_id` cascades on user delete.
- Unique index on `session_token_hash`.
- Index on `user_id`.
- Index on `expires_at`.

## 8. Frontend Integration

The frontend auth page currently:

- Checks the current session with `getCurrentUser()`.
- Redirects authenticated users to `/chat`.
- Keeps unauthenticated users on the auth page.
- Builds the Google login URL with `getGoogleLoginUrl()`.
- Sends API requests through the shared `apiClient`.

The shared API client:

- Uses `VITE_API_BASE_URL`.
- Sends `credentials: "include"` so cookies are included.
- Sends `Accept: application/json`.
- Throws on non-2xx responses.

Frontend schema validation:

- `/api/auth/me` is validated with `authenticatedUserResponseSchema`.
- `/api/auth/logout` is validated with `logoutResponseSchema`.

## 9. Error Handling

Auth errors use the shared application error response shape:

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable message."
  }
}
```

Current auth-related errors:

| Code | HTTP Status | Message |
| --- | --- | --- |
| `AUTH_UNAUTHORIZED` | `401` | `User is not authenticated.` |
| `AUTH_PROVIDER_FAILED` | `401` | `Google authentication failed.` |
| `AUTH_EMAIL_NOT_VERIFIED` | `401` | `Google email is not verified.` |

## 10. Existing Test Coverage

Current backend tests cover:

- Google OAuth authorization URL construction.
- Google callback redirect behavior.
- Google callback session cookie creation.
- New-user creation from Google profile data.
- Existing-user reuse by Google provider user ID.
- Rejection of unverified Google email.
- Session token generation.
- Session token hashing.
- Hash sensitivity to `SESSION_SECRET_KEY`.
- Current-user response from `/api/auth/me`.
- `401` response when current user is missing.
- Logout session deletion.
- Logout cookie clearing.

The tests use dependency overrides and fakes for auth service behavior where useful, keeping endpoint tests deterministic and avoiding real Google calls.

## 11. Known Current Limitations

- `redirectUri` is passed from the frontend to `/api/auth/google/login` and then placed in the OAuth `state` value, but `/api/auth/google/callback` currently ignores `state` and always redirects to `{FRONTEND_URL}/chat`.
- The OAuth `state` value is not currently validated as a CSRF protection token.
- The backend stores sessions but does not currently expose session management to users.
- Expired sessions are rejected during lookup, but there is no cleanup job documented or implemented for deleting old rows.
- The local default `SESSION_SECRET_KEY` is suitable only for development and must be changed in production.

## 12. Source References

Primary implementation files:

- `backend/app/auth/routes.py`
- `backend/app/auth/service.py`
- `backend/app/auth/repository.py`
- `backend/app/auth/google_oauth.py`
- `backend/app/auth/dependencies.py`
- `backend/app/auth/schemas.py`
- `backend/app/core/cookies.py`
- `backend/app/core/security.py`
- `backend/app/core/errors.py`
- `backend/app/models/user.py`
- `backend/app/models/auth_session.py`
- `backend/alembic/versions/20260704_0001_create_auth_tables.py`
- `frontend/src/features/auth/api.ts`
- `frontend/src/features/auth/schemas.ts`
- `frontend/src/features/auth/pages/auth-page.tsx`
