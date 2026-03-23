# User Management Specification

## Purpose

CRUD operations for user accounts, accessible to any authenticated user. No roles — all authenticated users can manage users.

## Requirements

### Requirement: List Users

The system MUST provide `GET /users` returning an HTML page listing all users with their username and creation date.

#### Scenario: Authenticated user views user list

- GIVEN the user is logged in
- WHEN `GET /users` is requested
- THEN a page renders showing all users (username, created_at)
- AND the current user is visually indicated

#### Scenario: Unauthenticated access

- GIVEN no valid session
- WHEN `GET /users` is requested
- THEN the response redirects to `/login`

### Requirement: Create User

The system MUST provide `POST /api/users` accepting `username` and `password`. Username MUST be unique. Password MUST be hashed before storage.

#### Scenario: Create user with valid data

- GIVEN the requester is authenticated
- WHEN `POST /api/users` is made with username "carlos" and password "pass123"
- THEN a new user is created with a bcrypt-hashed password
- AND the response confirms success

#### Scenario: Duplicate username

- GIVEN a user "carlos" already exists
- WHEN `POST /api/users` is made with username "carlos"
- THEN the response returns an error indicating the username is taken
- AND no duplicate is created

#### Scenario: Empty username or password

- GIVEN the requester is authenticated
- WHEN `POST /api/users` is made with an empty username or password
- THEN the response returns a validation error

### Requirement: Delete User

The system MUST provide `DELETE /api/users/{user_id}`. A user MUST NOT be able to delete themselves.

#### Scenario: Delete another user

- GIVEN the requester is authenticated as user ID 1
- WHEN `DELETE /api/users/2` is requested
- THEN user ID 2 is deleted along with their selections
- AND the response confirms success

#### Scenario: Self-deletion attempt

- GIVEN the requester is authenticated as user ID 1
- WHEN `DELETE /api/users/1` is requested
- THEN the response returns an error
- AND the user is NOT deleted

#### Scenario: Delete non-existent user

- GIVEN no user with ID 999 exists
- WHEN `DELETE /api/users/999` is requested
- THEN the response returns 404

### Requirement: Bootstrap Script

The system MUST provide `scripts/create_user.py` that creates a user from CLI arguments, for initial setup when no users exist.

#### Scenario: Create first user via CLI

- GIVEN the `app.users` table is empty
- WHEN `python scripts/create_user.py --username admin --password secret` is run
- THEN a user "admin" is created with a bcrypt-hashed password
