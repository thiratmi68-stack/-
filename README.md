# Hospital Management System

This is a Flask-based Hospital Management System with a comprehensive backend and a frontend served by Flask.

## Prerequisites

- Python 3.x

## Installation

1.  **Clone the repository** (if you haven't already):
    ```bash
    git clone <repository_url>
    cd <repository_name>
    ```

2.  **Create a virtual environment**:
    ```bash
    python3 -m venv venv
    ```

3.  **Activate the virtual environment**:
    - On Linux/macOS:
      ```bash
      source venv/bin/activate
      ```
    - On Windows:
      ```bash
      venv\Scripts\activate
      ```

4.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

1.  **Run the backend**:
    Make sure your virtual environment is activated, then run:
    ```bash
    python backend/app.py
    ```

2.  **Access the application**:
    Open your web browser and go to:
    ```
    http://localhost:5000
    ```
    The application will serve the frontend pages directly.

## Project Structure

-   `backend/`: Contains the Flask backend application and routes.
-   `Page/`: Contains the frontend HTML/CSS/JS files.
-   `docs/`: Documentation files.
-   `venv/`: Virtual environment directory (should be excluded from git).
