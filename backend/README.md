Backend (Flask + SQLite)

Quick start:

1. Create a virtual environment (optional but recommended)

   python3 -m venv venv
   source venv/bin/activate

2. Install dependencies

   pip install -r requirements.txt

3. Run the app

   python app.py

The API endpoints:

- POST /api/bookings
  - body (JSON): { patientName, departmentValue, departmentName, doctorName, symptoms, date, time }
  - returns: created booking object with `id` and `created_at`

- GET /api/bookings
  - returns: list of bookings

- GET /api/bookings/<id>
  - returns: booking by id

Notes:
- The app stores data in `bookings.db` inside the `backend` folder.
- CORS is enabled to allow calls from your static pages during development.
