---
inclusion: fileMatch
fileMatchPattern: "backend/**/*.py"
---

# WorkOS Token Verification — Get The Issuer Right

Every Parashell backend that validates a WorkOS user-management access token MUST verify it the same way the working services do. Copying the pattern wrong causes a silent `401 Unauthorized` on every request even though the token is valid everywhere else. This is mandatory.

## The Rule That Bites: Issuer Is Per-Client

WorkOS user-management access tokens carry:

```
iss = https://api.workos.com/user_management/{client_id}
```

NOT `https://api.workos.com`. If you verify against the plain host, `jwt.decode` raises on issuer mismatch and the endpoint returns `401` for tokens that the completions API and every other service accept. The failure is silent from the caller's side — the request just 401s and any fallback path hides it.

The canonical, correct implementation lives in `backend/API/custom_auth.py`:

```python
_WORKOS_API_BASE = "https://api.workos.com"

def _default_workos_issuer(client_id: str) -> str:
    return f"{_WORKOS_API_BASE}/user_management/{client_id}"
```

## Required Settings For Any New Backend Verifier

Resolve `client_id` from HostControl service `wos` (`extra_data.client_id`) — never hardcode it. Then:

```python
self.workos_client_id = _workos_client_id()  # from HostControl wos extra_data
self.workos_jwks_url = (
    os.environ.get("WORKOS_JWKS_URL", "").strip()
    or f"https://api.workos.com/sso/jwks/{self.workos_client_id}"
)
self.workos_issuer = (
    os.environ.get("WORKOS_JWT_ISSUER", "").strip()
    or f"https://api.workos.com/user_management/{self.workos_client_id}"
)
self.workos_audience = (os.environ.get("WORKOS_JWT_AUDIENCE", "") or "").strip()
```

`jwt.decode` must use `algorithms=["RS256"]`, `issuer=self.workos_issuer`, `audience=audience or None`, and `options={"require": ["exp", "sub"], "verify_aud": bool(audience)}`, then reject when `claims.get("client_id") != self.workos_client_id`.

## What NOT To Do

- Do NOT default the issuer to `"https://api.workos.com"`. That is the bug. If you copy `backend/Cortex/main.py`, fix the issuer default — Cortex's plain-host default only survives if its Vercel env sets `WORKOS_JWT_ISSUER`, and relying on that is how new services ship broken.
- Do NOT hardcode the client id, jwks url, or issuer with a literal client id.
- Do NOT let a 401 fall through silently. Log the resolved issuer/jwks and the decode failure reason so an issuer mismatch is obvious, not a mystery.

## Verification

Before shipping a new backend that authenticates WorkOS tokens, confirm:

1. The issuer default is `https://api.workos.com/user_management/{client_id}`, matching `backend/API/custom_auth.py`.
2. `client_id`, `jwks_url`, and `issuer` are all derived from the HostControl-resolved client id (or explicit env overrides), never hardcoded.
3. A real signed-in token that the completions API accepts is accepted by the new service (no 401).

If any check fails, the work is not done. Fix the issuer before reporting completion.
