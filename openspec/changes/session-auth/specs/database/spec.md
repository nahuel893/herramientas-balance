# Database Specification

## Purpose

PostgreSQL schema and tables in `app` schema for authentication and per-user selections. Separate from the `gold` data warehouse schema.

## Requirements

### Requirement: App Schema

The system MUST create a PostgreSQL schema named `app` if it does not exist. This schema MUST be separate from `gold`.

#### Scenario: First deployment

- GIVEN no `app` schema exists in `medallion_db`
- WHEN the schema initialization runs
- THEN `CREATE SCHEMA IF NOT EXISTS app` succeeds
- AND the `gold` schema is unaffected

### Requirement: Users Table

The system MUST create `app.users` with columns: `id` (SERIAL PK), `username` (VARCHAR UNIQUE NOT NULL), `password_hash` (VARCHAR NOT NULL), `created_at` (TIMESTAMP DEFAULT NOW()).

#### Scenario: Table structure

- GIVEN the `app` schema exists
- WHEN `app.users` is created
- THEN it has a unique constraint on `username`
- AND `id` auto-increments

#### Scenario: Unique username enforcement

- GIVEN user "ana" exists in `app.users`
- WHEN an INSERT with username "ana" is attempted
- THEN the database raises a unique constraint violation

### Requirement: User Selections Table

The system MUST create `app.user_selections` with columns: `id` (SERIAL PK), `user_id` (INTEGER FK to app.users ON DELETE CASCADE), `name` (VARCHAR NOT NULL), `table_name` (VARCHAR NOT NULL), `columns` (JSONB NOT NULL), `created_at` (TIMESTAMP DEFAULT NOW()). There MUST be a unique constraint on `(user_id, name)`.

#### Scenario: Table structure

- GIVEN the `app` schema exists
- WHEN `app.user_selections` is created
- THEN it has a foreign key from `user_id` to `app.users(id)` with CASCADE delete
- AND a unique constraint on `(user_id, name)`

#### Scenario: Cascade delete

- GIVEN user ID 1 has 5 selections in `app.user_selections`
- WHEN user ID 1 is deleted from `app.users`
- THEN all 5 selections are automatically deleted

### Requirement: Schema Initialization

The system MUST auto-create the `app` schema and tables on application startup if they do not exist. It MUST use `IF NOT EXISTS` to be idempotent.

#### Scenario: Repeated startup

- GIVEN the schema and tables already exist
- WHEN the application starts again
- THEN no errors occur and existing data is preserved
