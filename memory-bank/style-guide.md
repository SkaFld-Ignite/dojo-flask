# STYLE GUIDE - CODING STANDARDS & CONVENTIONS

> **Coding standards, conventions, and best practices for the dojo-flask project**

## 🎨 FRONTEND STYLE GUIDE (Next.js/React/TypeScript)

### TypeScript Standards
```typescript
// Use explicit typing for components
interface Props {
  title: string;
  isVisible?: boolean;
}

export default function Component({ title, isVisible = true }: Props) {
  return <div>{title}</div>;
}

// Use proper type exports
export type { Props as ComponentProps };
```

### React Component Patterns
```typescript
// Functional components with TypeScript
import { useState, useEffect } from 'react';

// Props interface naming: ComponentNameProps
interface ButtonProps {
  variant: 'primary' | 'secondary';
  onClick: () => void;
  children: React.ReactNode;
}

// Component naming: PascalCase
export default function Button({ variant, onClick, children }: ButtonProps) {
  return (
    <button 
      className={`btn btn-${variant}`}
      onClick={onClick}
    >
      {children}
    </button>
  );
}
```

### Tailwind CSS Conventions
```tsx
// Responsive design patterns
<div className="flex flex-col md:flex-row lg:grid lg:grid-cols-3">
  
// Dark mode support
<div className="bg-white dark:bg-gray-800 text-gray-900 dark:text-white">
  
// Hover and focus states
<button className="bg-blue-500 hover:bg-blue-600 focus:ring-2 focus:ring-blue-300">
```

### File Organization
```
app/
├── components/           # Reusable UI components
│   ├── ui/              # Basic UI elements (Button, Input, etc.)
│   └── features/        # Feature-specific components
├── hooks/               # Custom React hooks
├── utils/               # Utility functions
└── types/               # TypeScript type definitions
```

## 🔧 BACKEND STYLE GUIDE (Flask/Python)

### Flask Route Patterns
```python
from flask import Flask, jsonify, request
from typing import Dict, Any

app = Flask(__name__)

# Route naming: snake_case with descriptive names
@app.route("/api/users", methods=["GET"])
def get_users() -> Dict[str, Any]:
    """Get all users with proper JSON response."""
    return jsonify({
        "success": True,
        "data": [],
        "message": "Users retrieved successfully"
    })

# Error handling pattern
@app.route("/api/users/<int:user_id>", methods=["GET"])
def get_user(user_id: int) -> Dict[str, Any]:
    try:
        # Business logic here
        return jsonify({"success": True, "data": user_data})
    except Exception as e:
        return jsonify({
            "success": False, 
            "error": str(e)
        }), 500
```

### Python Code Standards
```python
# Type hints for all functions
def process_user_data(user_id: int, data: Dict[str, Any]) -> bool:
    """Process user data with proper type hints."""
    pass

# Class naming: PascalCase
class UserService:
    def __init__(self, database_url: str) -> None:
        self.db_url = database_url
    
    def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new user with validation."""
        pass
```

## 📁 PROJECT STRUCTURE STANDARDS

### Directory Conventions
```
dojo-flask/
├── api/                 # Flask backend
│   ├── routes/         # Route handlers
│   ├── models/         # Data models
│   ├── services/       # Business logic
│   └── utils/          # Utility functions
├── app/                # Next.js frontend
│   ├── components/     # React components
│   ├── hooks/          # Custom hooks
│   ├── utils/          # Frontend utilities
│   └── types/          # TypeScript types
└── shared/             # Shared types/utilities
```

### File Naming Conventions
- **Components:** PascalCase (`UserProfile.tsx`)
- **Hooks:** camelCase with "use" prefix (`useUserData.ts`)
- **Utilities:** camelCase (`formatDate.ts`)
- **Types:** PascalCase (`UserData.ts`)
- **Routes:** snake_case (`user_routes.py`)

## 🔄 API DESIGN STANDARDS

### REST API Conventions
```python
# Endpoint structure: /api/version/resource
GET    /api/v1/users          # Get all users
GET    /api/v1/users/123      # Get specific user
POST   /api/v1/users          # Create new user
PUT    /api/v1/users/123      # Update user
DELETE /api/v1/users/123      # Delete user
```

### Response Format Standards
```json
{
  "success": true,
  "data": {
    "id": 123,
    "name": "John Doe"
  },
  "message": "User retrieved successfully",
  "timestamp": "2024-01-01T00:00:00Z"
}

// Error responses
{
  "success": false,
  "error": "User not found",
  "code": "USER_NOT_FOUND",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

## 🧪 TESTING STANDARDS

### Frontend Testing (Jest/Testing Library)
```typescript
import { render, screen } from '@testing-library/react';
import Button from './Button';

describe('Button Component', () => {
  it('renders with correct text', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByText('Click me')).toBeInTheDocument();
  });
});
```

### Backend Testing (pytest)
```python
import pytest
from api.index import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_get_users(client):
    response = client.get('/api/users')
    assert response.status_code == 200
    assert response.json['success'] is True
```

## 📝 DOCUMENTATION STANDARDS

### Code Comments
```typescript
/**
 * Formats a date string for display
 * @param date - ISO date string
 * @param format - Format type ('short' | 'long')
 * @returns Formatted date string
 */
function formatDate(date: string, format: 'short' | 'long'): string {
  // Implementation here
}
```

### README Structure
- Project overview and setup instructions
- Development workflow and commands
- API documentation
- Contributing guidelines
- Deployment instructions

## 🚀 PERFORMANCE STANDARDS

### Frontend Optimization
- **Bundle Size:** Monitor and optimize bundle size
- **Loading States:** Implement loading indicators
- **Error Boundaries:** Graceful error handling
- **Accessibility:** WCAG compliance

### Backend Optimization
- **Response Times:** Target < 200ms for API responses
- **Error Handling:** Comprehensive error responses
- **Input Validation:** Validate all inputs
- **Security:** Implement proper CORS and security headers

**Assessment:** Comprehensive style guide ready for consistent development practices. 