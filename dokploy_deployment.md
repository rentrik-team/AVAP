# Deploying AVAP on Dokploy

Covers the Dokploy/Traefik deployment only. For a plain single machine
(`http://localhost:3000`) use `docker-compose.yml` instead — see the comments
at the top of that file.

## Why the stock compose file 404s

The application and its environment variables were never the problem. The
failure was one layer below, in networking.

Traefik's Docker provider only discovers containers attached to the
`dokploy-network` bridge. `docker-compose.yml` declares no networks, so
Compose puts the stack on its own default network where Traefik cannot see
it. Every request for the domain then falls through to Traefik's catch-all,
which answers `404 page not found` — and because no router ever existed, no
Let's Encrypt certificate was requested either, so the site is served under
Traefik's self-signed fallback certificate.

Confirming the symptom from any machine:

```
curl -sk -o /dev/null -w '%{http_code}\n' https://<your-domain>/
openssl s_client -connect <your-domain>:443 -servername <your-domain> </dev/null 2>/dev/null \
  | openssl x509 -noout -issuer
```

`404` plus `issuer=CN=TRAEFIK DEFAULT CERT` means no router matched — the
container never joined `dokploy-network`. Distinguish it from:

| Symptom                              | Meaning                                    |
| ------------------------------------ | ------------------------------------------ |
| 404 + `TRAEFIK DEFAULT CERT`         | no router — container off `dokploy-network` |
| 404 + valid cert, Next.js 404 page   | router fine, the app returned the 404       |
| 502 / Bad Gateway                    | router fine, container unreachable/unhealthy |

`docker-compose.dokploy.yml` fixes this by joining the external network.

## Two hostnames are required

The browser calls the API directly — the frontend never proxies it. So the
backend needs its own public HTTPS hostname:

| Service  | Hostname                | Container port |
| -------- | ----------------------- | -------------- |
| frontend | `avap.rentrik.in`       | 3000           |
| backend  | `api-avap.rentrik.in`   | 8000           |
| db       | not exposed             | —              |

A single hostname is not enough. With only the frontend exposed, the UI loads
and every API call fails: the bundle would point at `http://localhost:8000`,
and any plain-`http` API URL is blocked as mixed content on an https page.

Note the flat `api-avap` naming rather than `api.avap`. `rentrik.in` uses a
single-level wildcard record, so `api.avap.rentrik.in` does not resolve.
Check any new hostname with `dig +short <hostname>` before deploying —
Let's Encrypt's HTTP-01 challenge fails if it does not resolve.

## Configuration split

Routing is owned by the **Dokploy UI (Domains tab)**. The compose file
deliberately carries no `traefik.http.*` labels: two routers matching the
same `Host()` rule is ambiguous. It contributes only the network wiring plus
one `traefik.docker.network` hint on `backend`, which is attached to two
networks and would otherwise risk Traefik picking the wrong container IP.

| Concern                    | Owned by                        |
| -------------------------- | ------------------------------- |
| Hostname, port, TLS/cert   | Dokploy UI, Domains tab         |
| Network attachment         | `docker-compose.dokploy.yml`    |
| App config (CORS, API URL) | Dokploy UI, Environment tab     |

## Setup

1. **DNS.** A records for both hostnames pointing at the Dokploy host.
   Verify with `dig +short <hostname>`.

2. **Compose path.** In the Dokploy service, set the Compose Path to
   `docker-compose.dokploy.yml`.

3. **Domains tab.** One entry per exposed service:

   | Service  | Host                  | Path | Port | HTTPS | Cert        |
   | -------- | --------------------- | ---- | ---- | ----- | ----------- |
   | frontend | `avap.rentrik.in`     | `/`  | 3000 | on    | letsencrypt |
   | backend  | `api-avap.rentrik.in` | `/`  | 8000 | on    | letsencrypt |

4. **Environment tab.** These configure the application, not the routing, and
   are required even though the domains are managed in the UI:

   ```
   POSTGRES_PASSWORD=<strong-password>
   FRONTEND_DOMAIN=avap.rentrik.in
   BACKEND_DOMAIN=api-avap.rentrik.in
   OPENROUTER_API_KEY=<key, or leave blank>
   ```

   Hostnames only — no scheme, no trailing slash; the compose file adds
   `https://`. `FRONTEND_DOMAIN` becomes the backend's allowed CORS origin;
   `BACKEND_DOMAIN` becomes the API URL compiled into the browser bundle.

   Leaving `OPENROUTER_API_KEY` blank is supported: scans, risk scoring and
   reports work; AI remediation fails gracefully and is recorded in the audit
   log.

5. **Deploy.** Use Redeploy, not Restart — `BACKEND_DOMAIN` is compiled into
   the bundle at image build time.

## Verifying

```
curl -s https://api-avap.rentrik.in/health                          # {"status":"healthy",...}
curl -s -o /dev/null -w '%{http_code}\n' https://avap.rentrik.in/   # 200
```

Then open the UI and confirm the dashboard loads data rather than showing
error states — that exercises the browser -> API -> CORS path end to end.

## The frontend lock file

`frontend/Dockerfile` runs `npm ci`, which hard-fails if `package-lock.json`
is out of sync with `package.json` rather than silently resolving. The lock
must be generated by the same npm major as the build image (`node:24-alpine`),
otherwise optional/peer transitive entries differ and the build breaks with
`Missing: ... from lock file`.

To regenerate it with the exact npm the build uses, rather than whatever is
installed locally:

```
docker run --rm -v "$PWD/frontend:/w" -w /w node:24-alpine \
  npm install --package-lock-only
```

Commit the result. Verify before pushing with:

```
docker build --build-arg NEXT_PUBLIC_API_BASE_URL=https://api-avap.rentrik.in \
  -t avap-frontend-verify ./frontend
```

## Notes

- No host ports are published; Traefik reaches the containers over
  `dokploy-network`, so nothing collides with other stacks on the host.
- The database is on the private `internal` network only.
- Serving the UI from a hostname other than `FRONTEND_DOMAIN` will be
  rejected by the browser — CORS is pinned to exactly that origin.
- Migrations run automatically on backend start via
  `backend/docker-entrypoint.sh` (`alembic upgrade head`), gated on a healthy
  database.
