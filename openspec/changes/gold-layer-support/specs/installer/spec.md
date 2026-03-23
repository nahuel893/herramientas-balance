# Delta for installer

## ADDED Requirements

### Requirement: `selections.json` Reset on Install

`install.bat` MUST reset `selections.json` to an empty JSON object (`{}`) when it runs. This prevents stale silver-schema selections from persisting after the gold migration. The reset MUST happen unconditionally on every install run — not only when the file is absent.

Rationale: `install.bat` is a one-time setup script. Running it after the gold migration is the deploy trigger. Clearing saved selections at this point is safe and expected.

#### Scenario: File exists with silver selections

- GIVEN `selections.json` exists and contains one or more silver-schema selections
- WHEN `install.bat` is executed
- THEN `selections.json` is overwritten with the content `{}`
- AND no silver selections remain after the script completes

#### Scenario: File does not exist

- GIVEN `selections.json` does not exist
- WHEN `install.bat` is executed
- THEN `selections.json` is created with the content `{}`

#### Scenario: File already empty

- GIVEN `selections.json` already contains `{}`
- WHEN `install.bat` is executed
- THEN `selections.json` remains `{}` (idempotent, no error)

---

### Requirement: `start.bat` Does NOT Reset Selections

`start.bat` MUST NOT reset `selections.json`. Clearing on every startup would destroy user-created gold selections. The reset is a one-time migration action scoped to `install.bat`.

#### Scenario: Normal startup preserves selections

- GIVEN `selections.json` contains valid gold-schema selections
- WHEN `start.bat` is executed
- THEN `selections.json` is unchanged after startup completes
