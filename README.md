# TinRate API

A comprehensive Django REST API implementation for the TinRate platform - a marketplace connecting experts with clients for consultations and meetings.

## 🚀 Features

- **User Authentication**: JWT-based authentication with email verification
- **Expert Profiles**: Complete expert listing and profile management
- **Meeting System**: Booking, scheduling, and management of expert consultations
- **Review System**: Rating and review system for experts
- **Availability Management**: Flexible scheduling system for experts
- **Notifications**: Real-time notification system
- **Search & Discovery**: Advanced search and filtering capabilities
- **Dashboard**: Comprehensive dashboard with analytics

## 📋 API Specification

This API follows the detailed specification outlined in `API_SPECIFICATION.md`, implementing all endpoints exactly as specified.

## 🛠 Tech Stack

- **Backend**: Django 5.2.1 + Django REST Framework 3.16.0
- **Authentication**: JWT with djangorestframework-simplejwt
- **Database**: PostgreSQL (with SQLite fallback for development)
- **Caching**: Django's built-in caching framework
- **CORS**: django-cors-headers for cross-origin requests

## 📦 Installation

### Prerequisites

- Python 3.8+
- PostgreSQL (optional, SQLite used by default)

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd django-tinrate-api
   ```

2. **Create virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Configuration**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Database Setup**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Create Superuser** (optional)
   ```bash
   python manage.py createsuperuser
   ```

7. **Run the server**
   ```bash
   python manage.py runserver
   ```

The API will be available at `http://localhost:8000/v1/`

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database Settings (PostgreSQL)
DB_NAME=tinrate_db
DB_USER=postgres
DB_PASSWORD=password
DB_HOST=localhost
DB_PORT=5432

# Use SQLite for development (set to True if PostgreSQL is not available)
USE_SQLITE=True

# Email Settings
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=localhost
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
DEFAULT_FROM_EMAIL=noreply@tinrate.com

# TinRate API Settings
TINRATE_BASE_URL=https://api.tinrate.com

# LinkedIn OAuth Settings
LINKEDIN_CLIENT_ID=
LINKEDIN_CLIENT_SECRET=
```

## 📚 API Documentation

### Base URL
```
http://localhost:8000/v1/
```

### Authentication
All authenticated endpoints require a Bearer token:
```
Authorization: Bearer <jwt_token>
```

### Main Endpoints

#### 🔐 Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - User login
- `POST /auth/logout` - User logout
- `POST /auth/verify-email` - Verify email address
- `POST /auth/resend-verification` - Resend verification code
- `POST /auth/linkedin` - LinkedIn OAuth

#### 👤 User Management
- `GET /users/me` - Get current user profile
- `PUT /users/me` - Update user profile
- `POST /users/me/complete-profile` - Complete profile setup

#### 🎯 Expert Listings
- `GET /experts` - List experts with filtering
- `GET /experts/featured` - Get featured experts
- `GET /experts/{profileUrl}` - Get expert profile
- `POST /experts/me/listing` - Create/update expert listing
- `PUT /experts/me/listing/publish` - Publish expert listing

#### 📅 Meetings
- `GET /meetings` - Get user's meetings
- `POST /meetings/invitations/create` - Create meeting invitation
- `POST /meetings/invitations/{id}/accept` - Accept meeting invitation
- `POST /meetings/{id}/cancel` - Cancel meeting

#### 📝 Reviews
- `GET /experts/{id}/reviews` - Get expert reviews
- `POST /meetings/{id}/review` - Submit review
- `GET /reviews/received` - Get received reviews (experts)

#### 📱 Notifications
- `GET /notifications` - Get notifications
- `PUT /notifications/{id}/read` - Mark as read
- `GET /notifications/preferences` - Get preferences

#### 📊 Dashboard
- `GET /dashboard` - Get dashboard data

#### 🔍 Search
- `GET /search?q={query}` - Global search

#### 🔧 System
- `GET /health` - Health check
- `GET /config` - Client configuration

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test authentication
python manage.py test users
python manage.py test experts

# Run with verbose output
python manage.py test -v 2

# Run specific test case
python manage.py test users.tests.UserModelTestCase.test_create_user
```

### Test Coverage

The project includes comprehensive test coverage for:
- User authentication and registration
- Expert profile management
- Meeting system functionality
- Review and rating system
- API endpoint validation
- Model methods and properties

## 📁 Project Structure

```
django-tinrate-api/
├── tinrate_api/           # Main project settings
│   ├── settings.py        # Django settings
│   ├── urls.py           # Main URL configuration
│   └── utils.py          # Utility functions
├── authentication/       # Authentication app
│   ├── models.py         # Auth-related models
│   ├── views.py          # Auth endpoints
│   ├── serializers.py    # Auth serializers
│   └── tests.py          # Auth tests
├── users/                # User management app
│   ├── models.py         # User model
│   ├── views.py          # User endpoints
│   ├── serializers.py    # User serializers
│   └── tests.py          # User tests
├── experts/              # Expert management app
│   ├── models.py         # Expert and availability models
│   ├── views.py          # Expert endpoints
│   ├── serializers.py    # Expert serializers
│   └── tests.py          # Expert tests
├── meetings/             # Meeting system app
│   ├── models.py         # Meeting models
│   ├── views.py          # Meeting endpoints
│   ├── serializers.py    # Meeting serializers
│   └── tests.py          # Meeting tests
├── reviews/              # Review system app
│   ├── models.py         # Review models
│   ├── views.py          # Review endpoints
│   ├── serializers.py    # Review serializers
│   └── tests.py          # Review tests
├── notifications/        # Notification system app
│   ├── models.py         # Notification models
│   ├── views.py          # Notification endpoints
│   ├── serializers.py    # Notification serializers
│   └── tests.py          # Notification tests
├── requirements.txt      # Python dependencies
├── .env                  # Environment variables
└── README.md            # This file
```

## 🔒 Security Features

- JWT token authentication with refresh tokens
- Email verification for new accounts
- Rate limiting on authentication endpoints
- Input validation and sanitization
- CORS configuration for cross-origin requests
- Password validation and hashing
- SQL injection protection via Django ORM

## 🚀 Performance Optimizations

- Database query optimization
- Caching strategy for frequently accessed data
- Pagination for large datasets
- Bulk operations for efficiency
- Optimized serializers for minimal data transfer

## 📈 Monitoring & Logging

- Comprehensive logging configuration
- Health check endpoint for monitoring
- Error tracking and reporting
- Performance metrics collection

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Check the API specification in `API_SPECIFICATION.md`
- Review the test files for usage examples

## 🔄 API Versioning

The API uses URL versioning with `/v1/` prefix. Future versions will maintain backward compatibility where possible.

## 📊 Rate Limiting

Default rate limits:
- Authentication endpoints: 5 requests/minute
- Search endpoints: 30 requests/minute
- General API: 100 requests/minute
- Dashboard endpoint: 10 requests/minute

## 🌐 CORS Configuration

CORS is configured to allow requests from:
- `http://localhost:3000` (development)
- `http://127.0.0.1:3000` (development)
- `https://app.tinrate.com` (production)

## 📝 Changelog

### v1.0.0 (Initial Release)
- Complete API implementation matching specification
- User authentication and management
- Expert profile system
- Meeting booking and management
- Review and rating system
- Notification system
- Search and discovery features
- Comprehensive test coverage