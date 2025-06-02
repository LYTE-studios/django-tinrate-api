# TinRate API Specification

## Overview
This document outlines the REST API endpoints required for the TinRate platform. The API is designed to minimize requests and optimize loading times through efficient data structures and strategic endpoint design.

## Base URL
```
https://api.tinrate.com/v1
```

## Authentication
All authenticated endpoints require a Bearer token in the Authorization header:
```
Authorization: Bearer <jwt_token>
```

---

## 🔐 Authentication Endpoints

### POST /auth/register
Register a new user account.

**Request Body:**
```json
{
  "email": "john@example.com",
  "password": "securePassword123",
  "firstName": "John",
  "lastName": "Smith",
  "country": "US"
}
```

**Response (201):**
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "user_123",
      "email": "john@example.com",
      "firstName": "John",
      "lastName": "Smith",
      "country": "US",
      "isEmailVerified": false,
      "createdAt": "2025-01-01T00:00:00Z"
    },
    "requiresEmailVerification": true
  }
}
```

### POST /auth/login
Authenticate user and return access token.

**Request Body:**
```json
{
  "email": "john@example.com",
  "password": "securePassword123"
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "accessToken": "jwt_token_here",
    "refreshToken": "refresh_token_here",
    "user": {
      "id": "user_123",
      "email": "john@example.com",
      "firstName": "John",
      "lastName": "Smith",
      "country": "US",
      "isEmailVerified": true,
      "profileComplete": true,
      "isExpert": false
    }
  }
}
```

### POST /auth/verify-email
Verify user's email address with verification code.

**Request Body:**
```json
{
  "email": "john@example.com",
  "verificationCode": "123456"
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "message": "Email verified successfully"
  }
}
```

### POST /auth/resend-verification
Resend email verification code.

**Request Body:**
```json
{
  "email": "john@example.com"
}
```

### POST /auth/logout
Logout user and invalidate tokens.

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "success": true,
  "data": {
    "message": "Logged out successfully"
  }
}
```

### POST /auth/linkedin
Authenticate with LinkedIn OAuth.

**Request Body:**
```json
{
  "code": "linkedin_oauth_code",
  "redirectUri": "https://app.tinrate.com/auth/callback"
}
```

---

## 👤 User Profile Endpoints

### GET /users/me
Get current user's profile information.

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "user_123",
      "email": "john@example.com",
      "firstName": "John",
      "lastName": "Smith",
      "country": "US",
      "profileImageUrl": "https://cdn.tinrate.com/profiles/user_123.jpg",
      "isEmailVerified": true,
      "profileComplete": true,
      "isExpert": true,
      "expertProfile": {
        "id": "expert_456",
        "title": "UI/UX Designer",
        "company": "Coding Studios",
        "bio": "Creative UI/UX designer...",
        "hourlyRate": 20,
        "isListed": true,
        "profileUrl": "johnsmith",
        "totalMeetings": 23,
        "totalMeetingTime": "17:25",
        "rating": 4.8,
        "reviewCount": 6
      }
    }
  }
}
```

### PUT /users/me
Update current user's profile.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "firstName": "John",
  "lastName": "Smith",
  "country": "US",
  "profileImageUrl": "https://cdn.tinrate.com/profiles/user_123.jpg"
}
```

### POST /users/me/complete-profile
Complete user profile setup.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "firstName": "John",
  "lastName": "Smith",
  "country": "US"
}
```

---

## 🎯 Expert Listings Endpoints

### GET /experts
Get list of experts with filtering and pagination.

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `limit` (optional): Items per page (default: 20)
- `search` (optional): Search query
- `skills` (optional): Comma-separated skill filters
- `minRating` (optional): Minimum rating filter
- `maxPrice` (optional): Maximum hourly rate filter

**Response (200):**
```json
{
  "success": true,
  "data": {
    "experts": [
      {
        "id": "expert_456",
        "userId": "user_123",
        "name": "John Smith",
        "title": "UI/UX Designer",
        "company": "Coding Studios",
        "profileImageUrl": "https://cdn.tinrate.com/profiles/user_123.jpg",
        "hourlyRate": 20,
        "rating": 4.8,
        "reviewCount": 44,
        "totalHours": 140,
        "skills": ["DESIGN", "PROGRAMMING"],
        "isAvailableSoon": true,
        "isTopRated": false,
        "isFeatured": true,
        "profileUrl": "johnsmith"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 150,
      "totalPages": 8
    }
  }
}
```

### GET /experts/featured
Get featured experts for homepage (optimized for minimal requests).

**Response (200):**
```json
{
  "success": true,
  "data": {
    "experts": [
      {
        "id": "expert_456",
        "name": "John Smith",
        "title": "UI/UX Designer",
        "company": "Coding Studios",
        "profileImageUrl": "https://cdn.tinrate.com/profiles/user_123.jpg",
        "hourlyRate": 20,
        "rating": 4.8,
        "reviewCount": 44,
        "skills": ["DESIGN", "PROGRAMMING"],
        "isAvailableSoon": true,
        "profileUrl": "johnsmith"
      }
    ]
  }
}
```

### GET /experts/:profileUrl
Get expert's public profile by profile URL.

**Response (200):**
```json
{
  "success": true,
  "data": {
    "expert": {
      "id": "expert_456",
      "name": "John Smith",
      "title": "UI/UX Designer",
      "company": "Coding Studios",
      "bio": "Creative UI/UX designer at Coding Studios...",
      "profileImageUrl": "https://cdn.tinrate.com/profiles/user_123.jpg",
      "hourlyRate": 20,
      "rating": 4.8,
      "reviewCount": 6,
      "totalMeetings": 23,
      "totalMeetingTime": "17:25",
      "skills": ["DESIGN", "PROGRAMMING"],
      "isListed": true,
      "profileUrl": "johnsmith",
      "companyLogo": "https://cdn.tinrate.com/companies/coding_studios.jpg"
    },
    "reviews": [
      {
        "id": "review_789",
        "reviewerName": "Janice Doe",
        "reviewerType": "Expert",
        "reviewerImageUrl": "https://cdn.tinrate.com/profiles/reviewer.jpg",
        "rating": 5,
        "comment": "John gave clear, actionable UX advice in just 30 minutes...",
        "createdAt": "2025-01-01T00:00:00Z"
      }
    ],
    "upcomingMeetings": [
      {
        "id": "meeting_101",
        "date": "2025-01-19",
        "time": "09:00",
        "clientName": "Janice Smith"
      }
    ]
  }
}
```

---

## 📅 Calendar & Availability Endpoints

### GET /experts/me/availability
Get current user's availability schedule.

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `month` (optional): Month in YYYY-MM format (default: current month)
- `timezone` (optional): Timezone (default: user's timezone)

**Response (200):**
```json
{
  "success": true,
  "data": {
    "availability": {
      "timezone": "Europe/Brussels",
      "schedule": [
        {
          "date": "2025-03-24",
          "timeSlots": [
            {
              "startTime": "09:00",
              "endTime": "17:00",
              "isAvailable": true
            }
          ]
        }
      ],
      "weeklyDefaults": {
        "monday": [
          {
            "startTime": "09:00",
            "endTime": "17:00",
            "isEnabled": true
          }
        ]
      }
    }
  }
}
```

### PUT /experts/me/availability
Update availability schedule.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "timezone": "Europe/Brussels",
  "weeklyDefaults": {
    "monday": [
      {
        "startTime": "09:00",
        "endTime": "16:00",
        "isEnabled": true
      },
      {
        "startTime": "16:00",
        "endTime": "20:00",
        "isEnabled": true
      }
    ],
    "tuesday": [
      {
        "startTime": "09:00",
        "endTime": "16:00",
        "isEnabled": true
      }
    ],
    "wednesday": [
      {
        "startTime": "09:00",
        "endTime": "16:00",
        "isEnabled": false
      }
    ]
  },
  "specificDates": [
    {
      "date": "2025-03-18",
      "timeSlots": [
        {
          "startTime": "09:00",
          "endTime": "16:00",
          "isAvailable": true
        }
      ]
    }
  ]
}
```

### POST /experts/me/availability/bulk-update
Update availability for multiple dates at once.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "dates": ["2025-03-18", "2025-03-25"],
  "timeSlots": [
    {
      "startTime": "09:00",
      "endTime": "16:00"
    }
  ],
  "timezone": "Europe/Brussels"
}
```

### GET /meetings
Get user's meetings (both as expert and client).

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `type` (optional): "upcoming", "past", "all" (default: "upcoming")
- `limit` (optional): Number of meetings to return (default: 10)

**Response (200):**
```json
{
  "success": true,
  "data": {
    "meetings": [
      {
        "id": "meeting_101",
        "expertId": "expert_456",
        "expertName": "John Smith",
        "clientId": "user_789",
        "clientName": "Janice Smith",
        "scheduledAt": "2025-01-19T09:00:00Z",
        "duration": 60,
        "status": "scheduled",
        "meetingUrl": "https://meet.tinrate.com/meeting_101",
        "type": "expert" // or "client"
      }
    ]
  }
}
```

---

## 🎯 Expert Profile Management

### POST /experts/me/listing
Create or update expert listing.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "title": "UI/UX Designer",
  "company": "Coding Studios",
  "bio": "Creative UI/UX designer at LYTE Studios...",
  "hourlyRate": 20,
  "skills": ["DESIGN", "PROGRAMMING"],
  "profileUrl": "johnsmith"
}
```

**Response (201):**
```json
{
  "success": true,
  "data": {
    "expert": {
      "id": "expert_456",
      "title": "UI/UX Designer",
      "company": "Coding Studios",
      "bio": "Creative UI/UX designer...",
      "hourlyRate": 20,
      "skills": ["DESIGN", "PROGRAMMING"],
      "profileUrl": "johnsmith",
      "isListed": false,
      "createdAt": "2025-01-01T00:00:00Z"
    }
  }
}
```

### PUT /experts/me/listing/publish
Publish expert listing to marketplace.

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "success": true,
  "data": {
    "expert": {
      "id": "expert_456",
      "isListed": true,
      "profileUrl": "johnsmith",
      "listingUrl": "https://tinrate.com/johnsmith"
    }
  }
}
```

### PUT /experts/me/listing/unpublish
Remove expert listing from marketplace.

**Headers:** `Authorization: Bearer <token>`

---

## 📝 Reviews & Ratings

### GET /experts/:expertId/reviews
Get reviews for a specific expert.

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `limit` (optional): Items per page (default: 10)

**Response (200):**
```json
{
  "success": true,
  "data": {
    "reviews": [
      {
        "id": "review_789",
        "reviewerId": "user_101",
        "reviewerName": "Janice Doe",
        "reviewerType": "Expert",
        "reviewerImageUrl": "https://cdn.tinrate.com/profiles/reviewer.jpg",
        "rating": 5,
        "comment": "John gave clear, actionable UX advice...",
        "meetingId": "meeting_456",
        "createdAt": "2025-01-01T00:00:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 10,
      "total": 6,
      "totalPages": 1
    },
    "summary": {
      "averageRating": 4.8,
      "totalReviews": 6,
      "ratingDistribution": {
        "5": 4,
        "4": 2,
        "3": 0,
        "2": 0,
        "1": 0
      }
    }
  }
}
```

### POST /meetings/:meetingId/review
Submit a review after a meeting.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "rating": 5,
  "comment": "Great session! Very helpful insights."
}
```

---

## 🔗 Profile Sharing

### GET /experts/me/profile-link
Get shareable profile link information.

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "success": true,
  "data": {
    "profileUrl": "johnsmith",
    "fullUrl": "https://tinrate.com/johnsmith",
    "isPublic": true
  }
}
```

### PUT /experts/me/profile-url
Update custom profile URL.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "profileUrl": "johnsmith"
}
```

---

## 📊 Dashboard Data

### GET /dashboard
Get comprehensive dashboard data (optimized single request).

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "user_123",
      "firstName": "John",
      "lastName": "Smith",
      "isExpert": true
    },
    "expertStats": {
      "totalMeetings": 23,
      "totalMeetingTime": "17:25",
      "rating": 4.8,
      "reviewCount": 6,
      "isListed": true
    },
    "upcomingMeetings": [
      {
        "id": "meeting_101",
        "date": "2025-01-19",
        "time": "09:00",
        "clientName": "Janice Smith",
        "type": "expert"
      }
    ],
    "recentActivity": [
      {
        "type": "meeting_completed",
        "description": "Meeting with John Doe completed",
        "timestamp": "2025-01-01T00:00:00Z"
      }
    ]
  }
}
```

---

## 🔍 Search & Discovery

### GET /search
Global search across experts and content.

**Query Parameters:**
- `q`: Search query (required)
- `type` (optional): "experts", "all" (default: "all")
- `limit` (optional): Results limit (default: 20)

**Response (200):**
```json
{
  "success": true,
  "data": {
    "experts": [
      {
        "id": "expert_456",
        "name": "John Smith",
        "title": "UI/UX Designer",
        "company": "Coding Studios",
        "profileImageUrl": "https://cdn.tinrate.com/profiles/user_123.jpg",
        "rating": 4.8,
        "hourlyRate": 20,
        "profileUrl": "johnsmith"
      }
    ],
    "totalResults": 15
  }
}
```

---

## 💳 Billing & Payments

### GET /billing/overview
Get billing overview and payment history.

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "success": true,
  "data": {
    "currentBalance": 150.00,
    "pendingPayouts": 75.00,
    "totalEarnings": 2340.00,
    "recentTransactions": [
      {
        "id": "txn_123",
        "type": "earning",
        "amount": 20.00,
        "description": "Meeting with Janice Smith",
        "date": "2025-01-01T00:00:00Z",
        "status": "completed"
      }
    ],
    "paymentMethods": [
      {
        "id": "pm_123",
        "type": "bank_account",
        "last4": "1234",
        "isDefault": true
      }
    ]
  }
}
```

---

## 📱 Notifications

### GET /notifications
Get user notifications.

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `unread` (optional): "true" to get only unread notifications
- `limit` (optional): Number of notifications (default: 20)

**Response (200):**
```json
{
  "success": true,
  "data": {
    "notifications": [
      {
        "id": "notif_123",
        "type": "meeting_reminder",
        "title": "Meeting in 1 hour",
        "message": "Your meeting with Janice Smith starts in 1 hour",
        "isRead": false,
        "createdAt": "2025-01-01T00:00:00Z",
        "actionUrl": "/meetings/meeting_101"
      }
    ],
    "unreadCount": 3
  }
}
```

### PUT /notifications/:id/read
Mark notification as read.

**Headers:** `Authorization: Bearer <token>`

---

## 🔧 System Endpoints

### GET /health
Health check endpoint.

**Response (200):**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-01T00:00:00Z"
}
```

### GET /config
Get client configuration.

**Response (200):**
```json
{
  "success": true,
  "data": {
    "features": {
      "linkedinAuth": true,
      "videoMeetings": true
    },
    "limits": {
      "maxBioLength": 500,
      "maxProfileUrlLength": 50
    }
  }
}
```

---

## 📋 Data Models

### User
```typescript
interface User {
  id: string;
  email: string;
  firstName?: string;
  lastName?: string;
  country?: string;
  profileImageUrl?: string;
  isEmailVerified: boolean;
  profileComplete: boolean;
  isExpert: boolean;
  createdAt: string;
  updatedAt?: string;
}
```

### Expert
```typescript
interface Expert {
  id: string;
  userId: string;
  title: string;
  company: string;
  bio: string;
  hourlyRate: number;
  skills: string[];
  profileUrl: string;
  isListed: boolean;
  rating: number;
  reviewCount: number;
  totalMeetings: number;
  totalMeetingTime: string;
  profileImageUrl: string;
  companyLogo?: string;
}
```

### Meeting
```typescript
interface Meeting {
  id: string;
  expertId: string;
  clientId: string;
  scheduledAt: string;
  duration: number; // in minutes
  status: 'scheduled' | 'completed' | 'cancelled';
  meetingUrl?: string;
  notes?: string;
}
```

---

## 🚀 Performance Optimizations

### Caching Strategy
- **Expert listings**: Cache for 5 minutes
- **User profiles**: Cache for 15 minutes  
- **Reviews**: Cache for 30 minutes
- **Availability**: Cache for 2 minutes

### Pagination
- Default page size: 20 items
- Maximum page size: 100 items
- Use cursor-based pagination for real-time data

### Rate Limiting
- Authentication endpoints: 5 requests/minute
- Search endpoints: 30 requests/minute
- General API: 100 requests/minute
- Dashboard endpoint: 10 requests/minute

### Bulk Operations
- Use `/dashboard` for initial page load (single request)
- Use `/experts/featured` for homepage (optimized payload)
- Batch availability updates with `/availability/bulk-update`

---

## 🔒 Security Considerations

### Authentication
- JWT tokens with 1-hour expiration
- Refresh tokens with 30-day expiration
- Rate limiting on auth endpoints

### Data Validation
- Input sanitization on all endpoints
- Email format validation
- Profile URL uniqueness validation
- File upload size limits (5MB for profile images)

### Privacy
- Profile visibility controls
- Email verification required for listing
- Review moderation system