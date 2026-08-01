# Deploying AVAP on Dokploy

Covers the Dokploy/Traefik deployment only. For a plain single machine
(`http://localhost:3000`) use `docker-compose.yml` instead — see the comments
at the top of that file.

## Why the stock compose file 404s

Traefik's Docker provider only discovers containers attached to the
`dokploy-network` bridge. `docker-compose.yml` declares no networks, so
Compose puts the stack on its own default network where Traefik cannot see
it. Every request for the domain then falls through to Traefik's catch-all,
which answers `404 page not found` and serves its self-signed
`TRAEFIK DEFAULT CERT` because no Let's Encrypt certificate was ever
requested.

Confirming the symptom from any machine:

```
curl -sk -o /dev/null -w '%{http_code}\n' https://<your-domain>/
openssl s_client -connect <your-domain>:443 -servername <your-domain> </dev/null 2>/dev/null \
  | openssl x509 -noout -issuer
```

`404` plus `issuer=CN=TRAEFIK DEFAULT CERT` means no router matched — the
container never joined `dokploy-network`. This is distinct from a `502`
(router matched, container unreachable or unhealthy) and from a Next.js 404
page (router matched, app returned it).

`docker-compose.dokploy.yml` fixes this by joining the external network and
declaring the Traefik routers explicitly.

## Two hostnames are required

The browser calls the API directly — the frontend never proxies it. So the
backend needs its own public HTTPS hostname:

| Service  | Hostname               | Container port |
| -------- | ---------------------- | -------------- |
| frontend | `avap.example.com`     | 3000           |
| backend  | `api.avap.example.com` | 8000           |
| db       | not exposed            | —              |

A single hostname is not enough. With only the frontend exposed, the UI
loads and every API call fails: the bundle would point at
`http://localhost:8000`, and any plain-`http` API URL is blocked as mixed
content on an https page.

## Steps

1. **DNS.** Create A records for both hostnames pointing at the Dokploy
   host, and let them resolve before deploying — Let's Encrypt's HTTP-01
   challenge fails otherwise. Verify with `dig +short <hostname>`.

2. **Compose path.** In the Dokploy service, set the Compose Path to
   `docker-compose.dokploy.yml`.

3. **Remove UI domains.** Delete any entries under the Dokploy **Domains**
   tab for these hostnames. Routing now comes from the labels in the compose
   file; two routers matching the same `Host()` rule is ambiguous.

4. **Environment.** In the Dokploy **Environment** tab:

   ```
   POSTGRES_PASSWORD=<strong-password>
   FRONTEND_DOMAIN=avap.example.com
   BACKEND_DOMAIN=api.avap.example.com
   OPENROUTER_API_KEY=<key, or leave blank>
   ```

   Hostnames only — no scheme, no trailing slash. The compose file adds
   `https://` where it is needed.

   Leaving `OPENROUTER_API_KEY` blank is supported: scans, risk scoring and
   reports work; AI remediation fails gracefully and is recorded in the
   audit log.

5. **Deploy.** Use Redeploy, not Restart — `BACKEND_DOMAIN` is compiled into
   the browser bundle by `NEXT_PUBLIC_API_BASE_URL` at image build time.
   Changing it later requires another rebuild.

## Verifying

```
curl -s https://api.avap.example.com/health                          # {"status":"healthy",...}
curl -s -o /dev/null -w '%{http_code}\n' https://avap.example.com/   # 200
```

Then open the UI and confirm the dashboard loads data rather than showing
error states — that exercises the browser -> API -> CORS path end to end.

## Notes

- `docker-compose.dokploy.yml` publishes no host ports. Traefik reaches the
  containers over `dokploy-network`, so nothing can collide with other
  stacks on the same host.
- The database is on the private `internal` network only and is labelled
  `traefik.enable=false`; it is not reachable from outside the stack.
- Backend CORS is pinned to `https://$FRONTEND_DOMAIN`. Serving the UI from
  a different hostname than the one in `FRONTEND_DOMAIN` will be rejected by
  the browser.
- Migrations run automatically on backend start via
  `backend/docker-entrypoint.sh` (`alembic upgrade head`), gated on a healthy
  database.
