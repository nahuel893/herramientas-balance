# Storage Specification

## Purpose

Migrate selections persistence from shared `selections.json` file to per-user PostgreSQL storage in `app.user_selections`.

## REMOVED Requirements

### Requirement: JSON File Storage

(Reason: Replaced by per-user PostgreSQL storage. `selections.json` is no longer used.)

## ADDED Requirements

### Requirement: Load User Selections

The system MUST load selections filtered by `user_id`. Each user sees only their own selections.

#### Scenario: User with saved selections

- GIVEN user ID 1 has 3 saved selections in `app.user_selections`
- WHEN `GET /api/selections` is requested by user ID 1
- THEN only those 3 selections are returned
- AND selections from other users are NOT included

#### Scenario: User with no selections

- GIVEN user ID 2 has no saved selections
- WHEN `GET /api/selections` is requested by user ID 2
- THEN an empty collection is returned

### Requirement: Save User Selection

The system MUST save a selection associated with the authenticated user's ID. Selection names MUST be unique per user (not globally).

#### Scenario: Save new selection

- GIVEN user ID 1 is authenticated
- WHEN `POST /api/selections` is made with name "monthly-report", table "fact_ventas", columns ["col1", "col2"]
- THEN a row is inserted into `app.user_selections` with `user_id = 1`

#### Scenario: Duplicate name for same user

- GIVEN user ID 1 already has a selection named "monthly-report"
- WHEN `POST /api/selections` is made with name "monthly-report"
- THEN the existing selection is updated (upsert behavior)

#### Scenario: Same name different users

- GIVEN user ID 1 has a selection named "report"
- WHEN user ID 2 saves a selection named "report"
- THEN both selections coexist (names are unique per user, not globally)

### Requirement: Delete User Selection

The system MUST allow deleting a selection only if it belongs to the authenticated user.

#### Scenario: Delete own selection

- GIVEN user ID 1 owns selection "report"
- WHEN `DELETE /api/selections/report` is requested by user ID 1
- THEN the selection is deleted

#### Scenario: Delete another user's selection

- GIVEN user ID 2 owns selection "report"
- WHEN `DELETE /api/selections/report` is requested by user ID 1
- THEN the selection is NOT found (user 1 cannot see user 2's data)
