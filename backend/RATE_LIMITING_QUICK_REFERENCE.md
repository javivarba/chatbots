# Rate Limiting - Quick Reference

## 🚀 Quick Start

### Run Tests

```bash
python test_rate_limiting_quick.py
```

---

## 📊 Límites Configurados

### Autenticación (Más Restrictivo)

| Endpoint | Límite |
|----------|--------|
| `POST /api/auth/login` | **5 por minuto** |
| `POST /api/auth/refresh` | **10 por minuto** |
| `POST /api/auth/change-password` | **3 por hora** |

### Dashboard - Escritura

| Endpoint | Límite |
|----------|--------|
| `POST /leads/<id>/update-status` | **30 por minuto** |
| `POST /leads/<id>/add-note` | **20 por minuto** |
| `POST /cache/clear` | **10 por hora** |
| `POST /cache/invalidate/*` | **60 por minuto** |

### Dashboard - Lectura

| Endpoint | Límite |
|----------|--------|
| `GET /api/stats` | Default |
| `GET /api/leads` | Default |
| `GET /api/leads/<id>` | Default |
| `GET /api/appointments` | Default |
| `GET /api/cache/stats` | Default |

**Default:** 50 por hora, 200 por día

---

## 🔒 Protección Activa

✅ **Brute Force Prevention** - Max 5 intentos de login por minuto
✅ **API Abuse Protection** - Límites en todas las operaciones
✅ **Sensitive Operations** - Límites estrictos en cache y passwords
✅ **Redis Storage** - Límites compartidos entre instancias

---

## 📡 Response Example

### Request Bloqueada (429)

```json
{
  "error": "Rate limit exceeded",
  "message": "Has excedido el límite de requests permitidos. 5 per 1 minute",
  "retry_after": 45
}
```

### Headers

```
HTTP/1.1 429 Too Many Requests
X-RateLimit-Limit: 5
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1732544400
```

---

## 💻 Frontend Handling

```javascript
const response = await fetch('/api/auth/login', {...});

if (response.status === 429) {
    const data = await response.json();
    const retryAfter = data.retry_after || 60;

    alert(`Demasiados intentos. Espera ${retryAfter} segundos.`);

    // Deshabilitar login por retryAfter segundos
    disableLoginButton(retryAfter);
}
```

---

## ⚙️ Configuration

### Environment Variables

```bash
# .env
REDIS_URL=redis://default:password@host:port/0
```

### Files Modified

- `app/__init__.py` - Limiter initialization + error handler
- `app/api/auth_routes.py` - Rate limits on auth endpoints
- `app/api/dashboard_routes.py` - Rate limits on dashboard

---

## 🧪 Testing

### Manual Test with curl

```bash
# Test rate limiting (6 requests, limit is 5)
for i in {1..6}; do
    echo "Request $i"
    curl -X POST http://localhost:5000/api/auth/login \
         -H "Content-Type: application/json" \
         -d '{"username":"test","password":"test"}'
    sleep 0.5
done
```

**Expected:** Requests 1-5 return 401, Request 6 returns 429

---

## 🐛 Troubleshooting

### Rate limiting not working

**Check Redis connection:**
```bash
redis-cli ping
# Should return: PONG
```

**Check environment variable:**
```bash
echo $REDIS_URL
```

### Too many 429 errors

**Increase limits in code:**
```python
@limiter.limit("10 per minute")  # Was "5 per minute"
```

---

## 📚 Full Documentation

For complete documentation, see:
- [RATE_LIMITING_GUIDE.md](RATE_LIMITING_GUIDE.md) - Full implementation guide
- [JWT_AUTHENTICATION_GUIDE.md](JWT_AUTHENTICATION_GUIDE.md) - Auth documentation
- [SECURITY_RECOMMENDATIONS.md](SECURITY_RECOMMENDATIONS.md) - Security overview

---

**Status:** ✅ Production Ready
**Last Updated:** 25 de noviembre de 2025
