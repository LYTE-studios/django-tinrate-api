# CORS Troubleshooting Guide for TinRate API

## 🔗 CORS Configuration Overview

The TinRate API has been configured with comprehensive CORS settings to allow cross-origin requests from your frontend applications.

## ⚙️ Current CORS Settings

### Development Mode (DEBUG=True)
- **CORS_ALLOW_ALL_ORIGINS**: `True` (allows all origins)
- **CORS_ALLOW_CREDENTIALS**: `True`
- **CSRF_TRUSTED_ORIGINS**: `['http://*', 'https://*']`

### Production Mode (DEBUG=False)
- **Allowed Origins**:
  - `http://localhost:3000`
  - `http://127.0.0.1:3000`
  - `http://localhost:3001`
  - `http://127.0.0.1:3001`
  - `http://localhost:8080`
  - `http://127.0.0.1:8080`
  - `https://app.tinrate.com`
  - `https://tinrate.lytestudios.be`
  - `https://api.tinrate.lytestudios.be`

### Allowed Methods
- `DELETE`, `GET`, `OPTIONS`, `PATCH`, `POST`, `PUT`

### Allowed Headers
- `accept`, `accept-encoding`, `authorization`, `content-type`
- `dnt`, `origin`, `user-agent`, `x-csrftoken`, `x-requested-with`
- `x-forwarded-for`, `x-forwarded-proto`

## 🧪 Testing CORS

### 1. Use the CORS Test Page
Open `test_cors.html` in your browser and test the API endpoints:

```bash
# Serve the test page locally
python -m http.server 3000
# Then open: http://localhost:3000/test_cors.html
```

### 2. Test with curl
```bash
# Test preflight request
curl -X OPTIONS \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type,Authorization" \
  http://localhost:8000/v1/cors-test/

# Test actual request
curl -X GET \
  -H "Origin: http://localhost:3000" \
  http://localhost:8000/v1/cors-test/
```

### 3. Test with JavaScript
```javascript
// Test from browser console
fetch('http://localhost:8000/v1/cors-test/', {
  method: 'GET',
  headers: {
    'Content-Type': 'application/json',
  }
})
.then(response => response.json())
.then(data => console.log('Success:', data))
.catch(error => console.error('Error:', error));
```

## 🔧 Common CORS Issues & Solutions

### Issue 1: "Access to fetch at '...' from origin '...' has been blocked by CORS policy"

**Solution**: Check if your frontend origin is in the allowed origins list.

```python
# Add your frontend URL to settings.py
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",  # React default
    "http://localhost:3001",  # Alternative port
    "http://localhost:8080",  # Vue.js default
    "https://your-frontend-domain.com",  # Your production domain
]
```

### Issue 2: "CORS policy: Request header field authorization is not allowed"

**Solution**: Ensure `authorization` is in the allowed headers (already configured).

### Issue 3: "CORS policy: The request client is not a secure context"

**Solution**: Use HTTPS in production or ensure your development server supports HTTPS.

### Issue 4: Preflight requests failing

**Solution**: Check that OPTIONS method is allowed and the endpoint handles preflight requests.

### Issue 5: Credentials not being sent

**Solution**: Ensure both frontend and backend are configured for credentials:

**Frontend (JavaScript)**:
```javascript
fetch('http://localhost:8000/v1/api-endpoint/', {
  method: 'POST',
  credentials: 'include',  // Important!
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer your-jwt-token'
  }
});
```

**Backend**: Already configured with `CORS_ALLOW_CREDENTIALS = True`

## 🛠️ Frontend Configuration Examples

### React/Next.js
```javascript
// api.js
const API_BASE_URL = 'http://localhost:8000/v1';

export const apiCall = async (endpoint, options = {}) => {
  const url = `${API_BASE_URL}${endpoint}`;
  
  const config = {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    credentials: 'include',
    ...options,
  };

  const response = await fetch(url, config);
  
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }
  
  return response.json();
};
```

### Vue.js with Axios
```javascript
// api.js
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000/v1',
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor for auth token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default api;
```

### Angular
```typescript
// api.service.ts
import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private baseUrl = 'http://localhost:8000/v1';

  constructor(private http: HttpClient) {}

  private getHeaders(): HttpHeaders {
    return new HttpHeaders({
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${localStorage.getItem('access_token')}`
    });
  }

  get(endpoint: string) {
    return this.http.get(`${this.baseUrl}${endpoint}`, {
      headers: this.getHeaders(),
      withCredentials: true
    });
  }
}
```

## 🔍 Debugging CORS Issues

### 1. Check Browser Developer Tools
- Open Network tab
- Look for preflight OPTIONS requests
- Check response headers for CORS headers
- Look for error messages in Console tab

### 2. Check Django Logs
```bash
# Run Django with verbose logging
python manage.py runserver --verbosity=2
```

### 3. Test with Different Browsers
- Chrome: Strict CORS enforcement
- Firefox: Good debugging tools
- Safari: Different CORS behavior

### 4. Use Browser Extensions
- CORS Unblock (for testing only)
- Postman Interceptor

## 📋 CORS Headers Checklist

When debugging, ensure these headers are present in responses:

✅ `Access-Control-Allow-Origin`
✅ `Access-Control-Allow-Methods`
✅ `Access-Control-Allow-Headers`
✅ `Access-Control-Allow-Credentials` (if using credentials)
✅ `Access-Control-Max-Age` (for preflight caching)

## 🚀 Production Deployment

### 1. Update Allowed Origins
```python
# In production settings
CORS_ALLOWED_ORIGINS = [
    "https://app.tinrate.com",
    "https://tinrate.lytestudios.be",
    # Add your production domains
]

# Remove CORS_ALLOW_ALL_ORIGINS in production
CORS_ALLOW_ALL_ORIGINS = False
```

### 2. Use HTTPS
Ensure both frontend and backend use HTTPS in production.

### 3. Configure Reverse Proxy
If using Nginx, ensure CORS headers are not duplicated:

```nginx
# nginx.conf
location /v1/ {
    proxy_pass http://django;
    # Don't add CORS headers here if Django handles them
}
```

## 🆘 Still Having Issues?

1. **Check the CORS test endpoint**: `GET /v1/cors-test/`
2. **Verify your frontend origin** is in the allowed list
3. **Check browser console** for specific error messages
4. **Test with curl** to isolate frontend vs backend issues
5. **Review Django logs** for any server-side errors

## 📞 Quick Test Commands

```bash
# Test CORS endpoint
curl -H "Origin: http://localhost:3000" http://localhost:8000/v1/cors-test/

# Test with preflight
curl -X OPTIONS \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: POST" \
  http://localhost:8000/v1/cors-test/

# Test health endpoint
curl -H "Origin: http://localhost:3000" http://localhost:8000/v1/health/
```

The TinRate API is now configured with comprehensive CORS support. If you're still experiencing issues, the problem is likely in the frontend configuration or network setup.