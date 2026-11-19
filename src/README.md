# Mergington High School Activities API

A super simple FastAPI application that allows students to view and sign up for extracurricular activities.

## Features

- View all available extracurricular activities
- Sign up for activities

## Getting Started

1. Install the dependencies:

   ```
   pip install fastapi uvicorn
   ```

2. Create a teacher account. The command prompts for a password and stores only
   a salted password hash in the local, git-ignored `src/teachers.json` file:

   ```
   python -m src.manage_teachers teacher1
   ```

   Run the same command again to update that teacher's password.

3. Run the application from the repository root:

   ```
   uvicorn src.app:app --reload
   ```

4. Open http://localhost:8000. Anyone can view activities and participants.
   Teachers must sign in to add or remove participants.

The teacher session is held in the running app process and expires after eight
hours. Restarting the app signs out all teachers. This lightweight session
storage is intended for the single-process exercise app, not multi-worker
production deployments.

The API documentation is available at http://localhost:8000/docs and
http://localhost:8000/redoc.

## API Endpoints

| Method | Endpoint                                                          | Description                                                         |
| ------ | ----------------------------------------------------------------- | ------------------------------------------------------------------- |
| GET    | `/activities`                                                     | Get all activities with their details and current participant count |
| POST   | `/activities/{activity_name}/signup?email=student@mergington.edu` | Sign up for an activity                                             |

## Data Model

The application uses a simple data model with meaningful identifiers:

1. **Activities** - Uses activity name as identifier:

   - Description
   - Schedule
   - Maximum number of participants allowed
   - List of student emails who are signed up

2. **Students** - Uses email as identifier:
   - Name
   - Grade level

All data is stored in memory, which means data will be reset when the server restarts.
