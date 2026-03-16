# ADR-001: JWT Authentication Architecture with RBAC

**Date**: 2026-03-16 | **Status**: Accepted

---

## Context

The system needs authenticated access to session data and analytics. We must choose between:

1. Session-based auth (cookies + server-side sessions)
2. JWT stateless tokens
3. OAuth2 with external provider

## Decision

**JWT HS256 with access + refresh token rotation and database-backed refresh token revocation.**

### Rationale

| Criteria       | JWT (chosen)         | Sessions         | OAuth2 external |
| -------------- | -------------------- | ---------------- | --------------- |
| Stateless API  |  Yes               |  No            |  Yes          |
| Revocation     |  DB-backed refresh |  Native        | ️ Provider-dep |
| Self-contained |  Yes               |  Yes           |  External dep |
| RBAC           |  Claims in token   |  Session store | ️ Complex      |
| Complexity     | Medium               | Low              | High            |

### Token Strategy

- **Access token**: short-lived (30 min), HS256, carries `sub` (user_id) and `roles[]`
- **Refresh token**: long-lived (7 days), persisted in `refresh_tokens` table
- **Rotation**: every refresh call revokes the old token and issues a new one
- **Logout**: marks refresh token as `revoked = True`

## Consequences

-  Stateless access token verification (no DB hit on every request)
-  Revocation possible via refresh token table
- ️ Access tokens cannot be instantly revoked (must wait for expiry)
- ️ Refresh token table needs periodic cleanup of expired tokens
