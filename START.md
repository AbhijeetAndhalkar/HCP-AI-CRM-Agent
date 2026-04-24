# How to Start the Project

This project consists of a FastAPI Python backend and a React/Vite frontend. You will need two terminal windows to run both servers simultaneously.

## Prerequisites
- **Python 3.8+** installed
- **Node.js** (v18+ recommended) and **npm** installed

---

## 1. Start the Backend (FastAPI)

Open your first terminal window and follow these steps:

1. **Navigate to the backend directory:**
   ```bash
   cd backend
   ```

2. **Activate the virtual environment:**
   *(Assuming you are on Windows, as the project environment suggests)*
   ```bash
   .\venv\Scripts\activate
   ```
   *(If the `venv` folder is missing, create it first using `python -m venv venv`)*

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Variables:**
   Make sure you have your `.env` file set up. You can copy the provided example:
   ```bash
   copy .env.example .env
   ```
   *Edit the `.env` file to add your API keys (e.g., Groq API key) and Database credentials.*

5. **Run the FastAPI server:**
   ```bash
   uvicorn main:app --reload
   ```
   The backend should now be running, typically at `http://localhost:8000`.

---

## 2. Start the Frontend (React + Vite)

Open your second terminal window and follow these steps:

1. **Navigate to the frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install Node dependencies:**
   ```bash
   npm install
   ```

3. **Run the development server:**
   ```bash
   npm run dev
   ```
   The frontend should now be running, typically accessible at `http://localhost:5173`. Open this URL in your browser to interact with the CRM.

---

## Usage
Once both servers are running, the frontend React application will communicate with the backend FastAPI service. Ensure both terminals remain open and running while you use the application.
