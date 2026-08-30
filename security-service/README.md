# Java Security Service Module

A separate Java-based Spring Boot microservice for handling user authentication (register, login, validate) with JWT tokens and BCrypt password hashing.

## Tech Stack
- **Java 17+**
- **Spring Boot 3.3.x**
- **Spring Security 6.x**
- **JWT (JJWT 0.11.x)**
- **H2 In-Memory Database** (for simple, zero-setup local deployment)

---

## Folder Structure
```text
security-service/
├── src/
│   └── main/
│       ├── java/
│       │   └── com/
│       │       └── project/
│       │           └── security/
│       │               ├── SecurityApplication.java
│       │               ├── controller/
│       │               │   └── AuthController.java
│       │               ├── service/
│       │               │   └── AuthService.java
│       │               ├── model/
│       │               │   └── User.java
│       │               ├── security/
│       │               │   ├── JwtService.java
│       │               │   └── SecurityConfig.java
│       │               └── repository/
│       │                   └── UserRepository.java
│       └── resources/
│           └── application.properties
├── pom.xml
└── README.md
```

---

## Configuration Settings
The service is pre-configured in [application.properties](src/main/resources/application.properties):
- **Server Port**: `8081` (avoids port clash with python backend on port 8000)
- **H2 DB Console URL**: `http://localhost:8081/h2-console`
- **Database URL**: `jdbc:h2:mem:securitydb`
- **Default Database Credentials**: User: `sa`, Password: `password`

---

## REST API Documentation

### 1. User Registration
Creates a new user and returns a signed JWT token.
- **Endpoint**: `POST /api/auth/register`
- **Headers**: `Content-Type: application/json`
- **Request Body**:
```json
{
  "username": "robotics_admin",
  "password": "securepassword123"
}
```
- **Response** (Status `201 Created`):
```json
{
  "token": "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJyb2JvdGljc19hZG1pbiIsIm...",
  "message": "User registered successfully."
}
```

### 2. User Login
Verifies credentials and returns a new signed JWT token.
- **Endpoint**: `POST /api/auth/login`
- **Headers**: `Content-Type: application/json`
- **Request Body**:
```json
{
  "username": "robotics_admin",
  "password": "securepassword123"
}
```
- **Response** (Status `200 OK`):
```json
{
  "token": "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJyb2JvdGljc19hZG1pbiIsIm...",
  "message": "Login successful."
}
```

### 3. JWT Token Validation
Allows other services (like the FastAPI backend) to validate a JWT token and extract the username and role.
- **Endpoint**: `GET /api/auth/validate`
- **Query Parameter**: `token` (String)
- **Example Call**: `GET http://localhost:8081/api/auth/validate?token=eyJhbGciOiJIUzI1NiJ9...`
- **Response** (Status `200 OK` if valid):
```json
{
  "valid": true,
  "username": "robotics_admin",
  "role": "USER"
}
```
- **Response** (Status `401 Unauthorized` if invalid/expired):
```json
{
  "valid": false,
  "error": "Token is invalid or expired."
}
```

---

## How to Build and Run

1. Open a terminal in the `security-service/` folder.
2. Build the project using Maven:
   ```bash
   mvn clean package
   ```
3. Run the Spring Boot application:
   ```bash
   mvn spring-boot:run
   ```
4. Access the H2 Database console at: `http://localhost:8081/h2-console`
   - Set JDBC URL to: `jdbc:h2:mem:securitydb`
   - Set User Name to: `sa`
   - Set Password to: `password`
