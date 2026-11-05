# NOCHIs Boarding House Management System

Starter repository: student registration/login, room applications, owner approval, room allocation, payment records, profile, and room-swap requests.

## Stack
- Frontend: HTML, CSS, JavaScript
- Backend: FastAPI
- Database/auth: Supabase (PostgreSQL + Supabase Auth)

## Room setup
- Rooms 1–16: K1,200/student, capacity 3
- Rooms 17–24: K1,500/student, capacity 2
- Rooms 25–27: K1,000/student, capacity 2
- Room 28: K1,800/student, capacity 2
- Total capacity: 60

## Run locally
1. Create a Supabase project.
2. In Supabase SQL Editor, run `database/schema.sql`.
3. Copy `backend/.env.example` to `backend/.env`; fill in your Supabase project URL and **service role key**. Keep `.env` private; never upload it to GitHub.
4. From `backend/`, install dependencies and run:
   ```bash
   pip install -r requirements.txt
   uvicorn app.main:app --reload
   ```
5. Open `frontend/index.html` with a local web server (for example VS Code Live Server). Set `API_BASE` in `frontend/js/config.js` to your backend URL.
6. Create a user using the registration page. In Supabase, set the intended owner account's `profiles.role` to `owner` (SQL example in the schema comments). Do not make student accounts owners.

## Important before public launch
This is a starter implementation, not a finished audited production system. Configure Supabase Auth email confirmation, HTTPS, backups, strong owner credentials, and test role permissions. The backend uses the service role key, so keep it server-side only. Add payment-provider integration before accepting online payments; current payment records are entered by an owner and do not process money.
