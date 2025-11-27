# JWT Authentication - Quick Reference

## 🚀 Quick Start

### Login
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"Admin123456"}'
```

### Use Protected Route
```bash
curl http://localhost:5000/api/stats \
  -H "Authorization: Bearer <your_access_token>"
```

---

## 👤 Default Credentials

```
Username: admin
Password: Admin123456
Email:    admin@bjjacademy.com
Role:     admin
```

⚠️ **Cambiar en producción**

---

## 📡 API Endpoints

### Authentication

| Method | Endpoint | Auth Required | Description |
|--------|----------|---------------|-------------|
| POST | `/api/auth/login` | ❌ | Login and get tokens |
| POST | `/api/auth/refresh` | ✅ (Refresh) | Renew access token |
| GET | `/api/auth/me` | ✅ | Get current user |
| POST | `/api/auth/change-password` | ✅ | Change password |

### Protected Dashboard Routes

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/stats` | Get dashboard stats |
| GET | `/api/leads` | Get leads list |
| GET | `/api/leads/<id>` | Get lead detail |
| POST | `/api/leads/<id>/update-status` | Update lead status |
| POST | `/api/leads/<id>/add-note` | Add note to lead |
| GET | `/api/appointments` | Get appointments |
| GET | `/api/cache/stats` | Get cache stats |
| POST | `/api/cache/clear` | Clear cache |
| POST | `/api/cache/invalidate/lead/<id>` | Invalidate lead cache |
| POST | `/api/cache/invalidate/conversation/<id>` | Invalidate conv cache |

---

## 🛠️ User Management

### Create Admin User (Interactive)
```bash
python create_admin_user.py
```

### Create Admin User (CLI)
```bash
python create_admin_quick.py <username> <email> <password>
```

### Example
```bash
python create_admin_quick.py javi javi@academy.com MySecurePass123
```

---

## 🧪 Testing

### Run Auth Tests
```bash
python test_auth_flow.py
```

**Expected:** 8 tests pass ✓

---

## 🔑 Token Lifetimes

| Token Type | Lifetime | Usage |
|------------|----------|-------|
| **Access Token** | 1 hour | API requests |
| **Refresh Token** | 30 days | Renew access token |

---

## 🔒 Security Config

### Environment Variables (.env)
```bash
JWT_SECRET_KEY=FD4Q5Ysktm9auEF1hQSAAcLHzTVZYV2fkRDBjTy8nf8
JWT_ACCESS_TOKEN_EXPIRES=3600      # 1 hour
JWT_REFRESH_TOKEN_EXPIRES=2592000  # 30 days
```

### Generate New Secret Key
```python
import secrets
print(secrets.token_urlsafe(32))
```

---

## 🐛 Troubleshooting

### "Missing Authorization Header"
**Problema:** No se envió el token
**Solución:** Agregar header `Authorization: Bearer <token>`

### "Signature verification failed"
**Problema:** Token inválido o JWT_SECRET_KEY cambió
**Solución:** Login nuevamente para obtener nuevo token

### "Token has expired"
**Problema:** Access token expiró (>1 hora)
**Solución:** Usar refresh token para obtener nuevo access token

### "Credenciales inválidas"
**Problema:** Username o password incorrectos
**Solución:** Verificar credenciales o crear nuevo usuario

---

## 📝 Request Examples

### Login Request
```json
POST /api/auth/login
Content-Type: application/json

{
    "username": "admin",
    "password": "Admin123456"
}
```

### Login Response (Success)
```json
{
    "access_token": "eyJhbGci...",
    "refresh_token": "eyJhbGci...",
    "user": {
        "id": 1,
        "username": "admin",
        "email": "admin@bjjacademy.com",
        "role": "admin",
        "is_active": true
    }
}
```

### Protected Request
```bash
GET /api/stats
Authorization: Bearer eyJhbGci...
```

### Refresh Token Request
```bash
POST /api/auth/refresh
Authorization: Bearer <refresh_token>
```

### Change Password Request
```json
POST /api/auth/change-password
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "current_password": "OldPassword123",
    "new_password": "NewPassword123"
}
```

---

## 💻 Frontend Integration

### Save Tokens (JavaScript)
```javascript
const response = await fetch('/api/auth/login', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({username, password})
});

const data = await response.json();
localStorage.setItem('access_token', data.access_token);
localStorage.setItem('refresh_token', data.refresh_token);
```

### Authenticated Request
```javascript
const token = localStorage.getItem('access_token');

const response = await fetch('/api/stats', {
    headers: {'Authorization': `Bearer ${token}`}
});

const stats = await response.json();
```

### Handle Token Expiration
```javascript
if (response.status === 401) {
    await refreshToken();
    return retry();
}
```

---

## 📋 User Roles

| Role | Permissions |
|------|-------------|
| **admin** | Full access, user management |
| **staff** | Dashboard access, lead management |
| **readonly** | View-only access |

---

## ✅ Implementation Checklist

- [x] flask-jwt-extended installed
- [x] User model created
- [x] JWT configured in Flask
- [x] Auth endpoints created
- [x] Users table created in PostgreSQL
- [x] Admin user created
- [x] Dashboard routes protected
- [x] Tests passing
- [x] Documentation complete

---

## 🔗 Related Files

- `app/models/user.py` - User model
- `app/api/auth_routes.py` - Auth endpoints
- `app/api/dashboard_routes.py` - Protected routes
- `create_admin_user.py` - User creation script
- `test_auth_flow.py` - Test suite
- `JWT_AUTHENTICATION_GUIDE.md` - Full documentation

---

## 📞 Common Commands

```bash
# Create admin user
python create_admin_quick.py admin admin@academy.com Admin123456

# Test authentication
python test_auth_flow.py

# Start Flask server
python run.py

# Check PostgreSQL users table
psql -U postgres -d bjj_academy -c "SELECT * FROM users;"
```

---

**Last Updated:** 25 de noviembre de 2025
**Status:** ✅ Production Ready (cambiar credenciales por defecto)
