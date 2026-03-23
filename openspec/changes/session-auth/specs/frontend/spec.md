# Frontend Specification

## Purpose

Login page, protected route behavior, user admin page, and header modifications for authenticated sessions.

## Requirements

### Requirement: Login Page

The system MUST serve `GET /login` as an HTML page with a form containing username and password fields and a submit button. The page MUST NOT require authentication.

#### Scenario: Render login page

- GIVEN a user navigates to `/login`
- WHEN the page loads
- THEN a form with username, password inputs and a submit button is displayed

#### Scenario: Login error display

- GIVEN a failed login attempt
- WHEN the login page re-renders
- THEN an error message is visible (e.g., "Invalid credentials")
- AND the form fields are cleared

### Requirement: Protected Routes Redirect

All HTML routes except `/login` MUST redirect unauthenticated users to `/login`. The frontend JS SHOULD handle 401 API responses by redirecting to `/login`.

#### Scenario: JS handles 401

- GIVEN the user's session has expired
- WHEN a fetch to `/api/tables` returns 401
- THEN `app.js` redirects the browser to `/login`

### Requirement: Header User Info

The main page header MUST display the logged-in username and a logout button.

#### Scenario: Logged-in header

- GIVEN user "ana" is authenticated
- WHEN the main page renders
- THEN the header shows "ana" and a "Cerrar sesion" button

#### Scenario: Logout button

- GIVEN the user clicks "Cerrar sesion"
- WHEN the button is clicked
- THEN a POST to `/logout` is made
- AND the browser redirects to `/login`

### Requirement: User Admin Page

The system MUST serve `GET /users` as an HTML page listing users with a create-user form and delete buttons. This page MUST require authentication.

#### Scenario: View users page

- GIVEN the user is authenticated
- WHEN `GET /users` is requested
- THEN a page shows all users and a form to create new users

#### Scenario: Create user from UI

- GIVEN the admin page is displayed
- WHEN the user fills in username/password and submits
- THEN a POST to `/api/users` is made
- AND the user list refreshes on success

#### Scenario: Delete user from UI

- GIVEN the admin page shows user "carlos"
- WHEN the delete button for "carlos" is clicked
- THEN a DELETE to `/api/users/{id}` is made
- AND the user list refreshes on success
