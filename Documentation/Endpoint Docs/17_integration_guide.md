# Doc 17 — Integration Guide

**numiVeda Astro Engine · Developer Reference · v1.0**

This is the practical glue between the 16 endpoint docs and your client code. The endpoint docs tell you *what each route returns*. This doc tells you *how to actually call them* — auth, errors, timeouts, retries, CORS, TypeScript types, deployment-specific concerns.

If you're integrating the engine into a web app, mobile app, WhatsApp bot, PDF report generator, or any client, read this first.

---

## 1. Base URLs

| Environment | URL |
|---|---|
| Production (internal) | `http://65.20.75.166:8001` |
| Production (public, when configured) | `https://api.numiveda.com` (TBD) |
| OpenAPI schema | `http://65.20.75.166:8001/openapi.json` |

All endpoint paths are prefixed `/astro/...` (e.g. `/astro/chart`). The `openapi.json` is the only route NOT under `/astro/` — FastAPI serves the schema at root.

**Important:** When fronted by nginx with SSL (recommended for production), the base URL becomes `https://your-domain.com`. The internal IP `65.20.75.166:8001` is for direct VPS-level calls; never expose it directly to browser clients.

---

## 2. Authentication

All requests require an API key in the `X-API-Key` header.

```
X-API-Key: numiveda-astro-secret-2026
```

**Read from environment variable in client code, never hardcode.**

### Example — JavaScript/Node.js (fetch)

```javascript
const response = await fetch('http://65.20.75.166:8001/astro/chart', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': process.env.ASTRO_API_KEY
  },
  body: JSON.stringify({
    dob: '1990-04-15',
    time: '14:30',
    lat: 28.6139,
    lon: 77.2090,
    timezone: 'Asia/Kolkata'
  })
});
const data = await response.json();
```

### Example — Python (requests)

```python
import os, requests

response = requests.post(
    'http://65.20.75.166:8001/astro/chart',
    headers={
        'Content-Type': 'application/json',
        'X-API-Key': os.getenv('ASTRO_API_KEY')
    },
    json={
        'dob': '1990-04-15',
        'time': '14:30',
        'lat': 28.6139, 'lon': 77.2090,
        'timezone': 'Asia/Kolkata'
    },
    timeout=30
)
data = response.json()
```

### Example — curl

```bash
curl -X POST http://65.20.75.166:8001/astro/chart \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $ASTRO_API_KEY" \
  -d '{"dob":"1990-04-15","time":"14:30","lat":28.6139,"lon":77.2090,"timezone":"Asia/Kolkata"}'
```

### Rotating the API key

If the key needs rotation (suspected leak, scheduled rotation):

1. SSH into the VPS
2. Set new value via `/etc/environment` or systemd service environment
3. Update all client integrations to use new key
4. `systemctl restart astro.service`
5. Verify all integrations work before retiring the old key

---

## 3. Standard Input Schema — BirthInput

Most endpoints accept the `BirthInput` schema:

### Required fields

| Field | Type | Format | Notes |
|---|---|---|---|
| `dob` | string | `YYYY-MM-DD` | 4-digit year |
| `time` | string | `HH:MM` | 24-hour, local time |
| `lat` | number | float | Decimal latitude |
| `lon` | number | float | Decimal longitude |
| `timezone` | string | IANA name | `Asia/Kolkata`, etc. |

### Optional fields (varies per endpoint)

| Field | Used by | Notes |
|---|---|---|
| `query_date` | predictive endpoints | `YYYY-MM-DD`, defaults to today |
| `name` | numerology endpoints | First+last name |
| `ayanamsha` | core endpoints | `Lahiri` (default), `Raman`, `Krishnamurti` |
| `gender` | health, compatibility | `male`/`female`/`other` |

### Common input gotchas

- **Time precision**: `HH:MM` is required. Don't send `HH:MM:SS`.
- **Timezone is mandatory**: Without `timezone`, engine defaults to UTC — wrong for almost all birth charts.
- **Latitude sign**: Southern hemisphere is **negative** (Sydney = `-33.8688`).
- **Longitude sign**: Western hemisphere is **negative** (New York = `-74.0060`).
- **Historical dates**: Acceptable post-1900. Pre-500 BCE not recommended due to ephemeris precision.

---

## 4. Response Patterns

### Successful response

HTTP `200 OK` with JSON body. Shape varies per endpoint (see Docs 01–15).

Newer endpoints (post-F4) tend to skip the `success` wrapper. Legacy endpoints (Doc 15) typically include it.

### Error response shapes

| HTTP code | Meaning | Body |
|---|---|---|
| `200 OK` | Success | Endpoint data |
| `400 Bad Request` | Invalid input | `{"detail": "validation message"}` |
| `401 Unauthorized` | Missing/wrong API key | `{"detail": "Invalid API Key"}` |
| `404 Not Found` | Wrong URL path | `{"detail": "Not Found"}` |
| `422 Unprocessable Entity` | Pydantic validation | `{"detail": [{"loc": [...], "msg": "...", "type": "..."}]}` |
| `500 Internal Server Error` | Engine bug | `{"detail": "Internal Server Error"}` |
| `503 Service Unavailable` | Engine restarting | Plain text |

### Example — 422 validation error

If you send `lat: "twenty-eight"`:
```json
{
  "detail": [{
    "loc": ["body", "lat"],
    "msg": "value is not a valid float",
    "type": "type_error.float"
  }]
}
```

### Defensive client wrapper

```javascript
async function callAstroEngine(endpoint, payload) {
  try {
    const response = await fetch(`${BASE_URL}${endpoint}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': process.env.ASTRO_API_KEY
      },
      body: JSON.stringify(payload),
      signal: AbortSignal.timeout(30000)
    });
    
    if (!response.ok) {
      const errorBody = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new AstroApiError(response.status, errorBody.detail, endpoint);
    }
    
    return await response.json();
  } catch (err) {
    if (err.name === 'TimeoutError' || err.name === 'AbortError') {
      throw new AstroApiError(408, 'Request timed out', endpoint);
    }
    throw err;
  }
}

class AstroApiError extends Error {
  constructor(status, detail, endpoint) {
    super(`Astro API ${status}: ${JSON.stringify(detail)} on ${endpoint}`);
    this.status = status;
    this.detail = detail;
    this.endpoint = endpoint;
  }
}
```

---

## 5. Timeouts & Retries

### Recommended timeouts per endpoint class

| Class | Timeout | Reason |
|---|---|---|
| Lightweight (chart, panchang) | 10s | <100ms typical |
| Medium (yogas, compatibility) | 15s | <500ms typical |
| Heavy (full reports) | 30s | <5s typical |
| **Rectification** | **60s** | `/rectification/master` ~1157ms, spike to 5-10s under load |

### Retry policy

- **Retry on:** 502, 503, 504 (transient infra)
- **Do NOT retry on:** 400, 401, 422 (client error)
- **Backoff:** Exponential (1s, 2s, 4s), capped at 3 attempts

```javascript
async function retryableCall(endpoint, payload, attempts = 3) {
  for (let i = 0; i < attempts; i++) {
    try {
      return await callAstroEngine(endpoint, payload);
    } catch (err) {
      if ([400, 401, 422].includes(err.status)) throw err;
      if (i === attempts - 1) throw err;
      await new Promise(r => setTimeout(r, 1000 * Math.pow(2, i)));
    }
  }
}
```

### Idempotency

All endpoints are idempotent — same input always returns same output (except predictive endpoints with `query_date` defaulting to today). Safe to retry.

---

## 6. Rate Limits & Capacity

The engine has **no application-level rate limits** currently. Single VPS / 2 uvicorn workers / 131 MB memory has practical capacity:

- Lightweight endpoints: ~100-200 req/s sustainable
- Medium endpoints: ~50 req/s sustainable
- Heavy endpoints: ~5-10 req/s sustainable

### Client-side rate limiting

For high-volume integrations:

```javascript
class RateLimiter {
  constructor(tokensPerSecond) {
    this.tokensPerSecond = tokensPerSecond;
    this.tokens = tokensPerSecond;
    this.lastRefill = Date.now();
  }
  async acquire() {
    while (this.tokens < 1) {
      const now = Date.now();
      const elapsed = (now - this.lastRefill) / 1000;
      this.tokens = Math.min(this.tokensPerSecond, this.tokens + elapsed * this.tokensPerSecond);
      this.lastRefill = now;
      if (this.tokens < 1) await new Promise(r => setTimeout(r, 100));
    }
    this.tokens--;
  }
}
```

For server-side limits when needed, nginx `limit_req_zone` is the cleanest add.

---

## 7. CORS — Browser Integration

The engine does NOT currently send CORS headers. Browser JS calls from a different origin will fail.

**Two paths:**

### Path A (recommended): Proxy through your backend

```
Browser → your-app.com/api/chart → astro engine (with API key)
```

API key stays server-side. This is the standard pattern.

### Path B: Enable CORS on the engine

In `main.py`:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://apps.numiveda.com",
        "https://reports.numiveda.com",
        # NEVER use "*" in production with auth
    ],
    allow_credentials=True,
    allow_methods=["POST", "GET"],
    allow_headers=["Content-Type", "X-API-Key"],
)
```

API key gets exposed to browsers. Generate per-client tokens with restricted access.

**Currently:** Engine ships with no CORS. All numiVeda apps proxy via backend.

---

## 8. TypeScript Type Templates

```typescript
export interface BirthInput {
  dob: string;            // YYYY-MM-DD
  time: string;           // HH:MM
  lat: number;
  lon: number;
  timezone: string;       // IANA
  query_date?: string;
  name?: string;
  ayanamsha?: 'Lahiri' | 'Raman' | 'Krishnamurti';
}

export interface Lagna {
  sign: string;
  degree: number;
  nakshatra: string;
  pada: number;
  d2_sign: string;
  d3_sign: string;
  d4_sign: string;
  d7_sign: string;
  d9_sign: string;
  d10_sign: string;
  d12_sign: string;
  d16_sign: string;
  d20_sign: string;
  d24_sign: string;
  d27_sign: string;
  d30_sign: string;
  d40_sign: string;
  d45_sign: string;
  d60_sign: string;
}

export interface PlanetState {
  sign: string;
  degree: number;
  house: number;
  nakshatra: string;
  pada: number;
  nakshatra_lord: string;
  is_retrograde: boolean;
  is_combust: boolean;
  dignity: 'exalted' | 'mooltrikona' | 'own_sign' | 'great_friend' 
        | 'friend' | 'neutral' | 'enemy' | 'great_enemy' | 'debilitated';
  has_digbala: boolean;
  // ...16 divisional sign fields
  aspects: PlanetAspect[];
}

export interface DashaPeriod {
  planet: string;
  start: string;
  end: string;
  years?: number;
  days: number;
}

export interface CurrentDasha {
  mahadasha: DashaPeriod;
  antardasha: DashaPeriod;
  pratyantar: DashaPeriod;
}

export interface AstroApiError {
  detail: string | Array<{ loc: string[]; msg: string; type: string }>;
}
```

Extend per-endpoint based on Doc 01–15 response shapes.

---

## 9. Common Integration Recipes

### Recipe 1: Generate chart on user signup

```javascript
async function generateChart(birthDetails) {
  const chart = await retryableCall('/astro/chart', birthDetails);
  await db.userCharts.insert({
    userId: currentUser.id,
    chart, generatedAt: new Date()
  });
  return chart;
}
```

Cache once, use many — every additional reading (yogas, transit, compatibility) starts with chart data.

### Recipe 2: Daily prediction WhatsApp bot

```javascript
async function sendDailyPrediction(user) {
  const userChart = await db.userCharts.findOne({ userId: user.id });
  const prediction = await retryableCall('/astro/transit/daily_predictions', {
    dob: userChart.dob, time: userChart.time,
    lat: userChart.lat, lon: userChart.lon,
    timezone: user.timezone
  });
  await whatsapp.sendMessage(user.phone, formatPrediction(prediction));
}
```

### Recipe 3: Multi-section PDF — parallel fan-out

```javascript
async function generateFullReport(birthInput) {
  const [chart, yogas, transit, dashas, remedies] = await Promise.all([
    retryableCall('/astro/chart', birthInput),
    retryableCall('/astro/yogas', birthInput),
    retryableCall('/astro/transit', birthInput),
    retryableCall('/astro/dasha/all', birthInput),
    retryableCall('/astro/remedies', birthInput)
  ]);
  return await pdfGenerator.render({ chart, yogas, transit, dashas, remedies });
}
```

5 parallel calls completes in ~max(individual) instead of sum. Typically 1-2s instead of 5-10s serial.

### Recipe 4: Heavy operation — rectification with progress UI

```javascript
async function rectifyBirthTime(birthInput, events) {
  setLoading(true, 'Calibrating birth time across 4 approaches...');
  try {
    const result = await retryableCall('/astro/rectification/master', {
      ...birthInput, events
    });
    await cache.set(rectifyCacheKey(birthInput, events), result, '30 days');
    return result;
  } finally {
    setLoading(false);
  }
}
```

### Recipe 5: Caching strategy

**Always cache (forever):** Natal charts, rectification results, yogas, divisional charts, numerology static numbers.

**Cache with TTL:** Transit predictions (1 hour), panchang (1 hour per location), sade sati state (1 day).

**Never cache:** Random-component endpoints (tarot, ramal, I-ching with RNG seeded by timestamp).

---

## 10. Environment & Deployment

### Local development against production engine

```bash
# .env.local
ASTRO_BASE_URL=http://65.20.75.166:8001
ASTRO_API_KEY=numiveda-astro-secret-2026
```

### Production deployment (Vercel, Railway, etc.)

Set env vars in platform settings UI. Never commit to git.

### Running engine locally for dev

```bash
git clone git@github.com:numiveda/astro-engine.git /opt/astro
cd /opt/astro
pip install fastapi uvicorn pyswisseph pytz
ASTRO_API_KEY=dev-key uvicorn main:app --host 0.0.0.0 --port 8001
```

Swiss Ephemeris data files aren't in git (too large). Get from `/opt/astro/` on production VPS or from Swiss Ephemeris official distribution.

---

## 11. Versioning & Backward Compatibility

### Current version

**v1.0-f11** — Post-F11 hotfix (2026-05-19). 327 endpoints. Git tag in repo.

### Breaking change policy (best-effort for internal use)

- Add fields freely (clients ignore unknown)
- Don't remove fields without notice
- Don't change semantics
- Add new endpoints rather than overloading

### Detect version from client

```bash
curl http://65.20.75.166:8001/openapi.json | jq '.info'
```

---

## 12. Debugging Integration Issues

### All calls return 401

API key wrong or missing. Check `echo $ASTRO_API_KEY` shows the right value. Header spelled `X-API-Key`.

### All calls return 422

Pydantic validation failing. Check `detail` array for which field. Common: `lat` as string, `time` as `HH:MM:SS`, `timezone` as numeric offset.

### Calls work in curl but fail in browser

CORS. Use proxy through your backend (Section 7 Path A).

### Random 500 errors

Engine bug for specific input. Save the input, check `journalctl -u astro.service | grep ERROR`, file an issue.

### Rectification timeouts

`/rectification/master` is genuinely slow. Set timeout to 60s, cache aggressively.

### Unexpected output

Verify input (timezone correct? lat/lon sign?). Compare with manual chart. Check journal warnings. Cross-reference Doc 01-15 for field meanings.

---

## 13. Where to Get Help

| Issue | Resource |
|---|---|
| Endpoint shape questions | Docs 01-15 (16 module-grouped docs) |
| Integration / client code | This doc (Doc 17) |
| Server operations / restore | `BACKUP_RECOVERY_OPERATIONS.md` |
| Architecture / deeper internals | Tech Handbook T1 |
| Debugging server-side | Tech Handbook T5 |
| Patch history | Tech Handbook T6 |
| Deployment / ops | Tech Handbook T7 |

---

**End of Doc 17.**
