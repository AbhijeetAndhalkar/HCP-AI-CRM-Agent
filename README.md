# CogniCRM: AI-Powered Healthcare Professional (HCP) CRM

## Project Overview

CogniCRM is an enterprise-grade, AI-first Customer Relationship Management (CRM) platform purpose-built for the Life Sciences and Pharmaceutical industry. Designed around a 'Human-in-the-loop' agentic workflow, it empowers medical liaisons and sales representatives to capture rich interactions with Healthcare Professionals (HCPs) using natural language. 

By seamlessly integrating a stateful conversational AI with a traditional React-based UI, CogniCRM eliminates data entry friction while enforcing strict data integrity and pharmaceutical compliance.

## Architecture Overview

The application is built on a modern, decoupled architecture:
- **Frontend (React/Redux):** Provides a reactive, split-screen interface where the form state is tightly synchronized with the AI's data extraction.
- **Backend (FastAPI/LangGraph):** Drives the 'AI Brain'. A stateful LangGraph engine manages the conversational flow, evaluates required data fields, and interfaces with the LLM (Llama-3.3-70b-versatile) before safely persisting data to a MySQL database via SQLAlchemy.

This separation of concerns ensures a snappy UI experience while offloading heavy cognitive processing and state management to the robust Python backend.

## Key Technical Features

*   **Stateful Agentic Memory:** Utilizes LangGraph to maintain context across multi-turn interactions. The AI remembers conversation history (preventing "goldfish memory"), allowing for natural, continuous dialogue.
*   **Strict Data Extraction:** Forces the LLM to output structured JSON format, enabling the backend to automatically map natural language into precise database columns and instantly update the React form in real-time.
*   **Regex Safety Net:** Features a custom frontend parser equipped with fallback regex patterns. This safety net catches and successfully processes raw JSON data even if the AI hallucinates formatting tags or omits markdown blocks.
*   **Absolute Tool Ban:** Implements strict guardrails during the "Data Gathering Phase." The AI is restricted from firing database execution tools (like `log_interaction` or `search_hcp`) until all mandatory fields are 100% complete, preventing premature API calls and 500 server errors.
*   **Redux State Merging:** Allows the AI to incrementally update specific form fields without destructively overwriting existing user data or partial form entries.

## Tech Stack

**Frontend:**
*   React 19
*   Redux Toolkit
*   Vite
*   Tailwind CSS / Vanilla CSS

**Backend:**
*   Python 3.8+
*   FastAPI & Uvicorn
*   SQLAlchemy
*   MySQL (via PyMySQL)

**AI & Logic:**
*   LangGraph (StateGraph)
*   LangChain
*   ChatGroq (Llama-3.3-70b-versatile)

## Prerequisites

Before starting, ensure you have the following installed:
*   **Node.js** (v18+ recommended) and **npm**
*   **Python** (v3.8+)
*   **MySQL Server** (Running locally or remotely)
*   **Groq API Key** (for Llama-3.3 inference)

## Installation & Setup Guide

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/hcp-ai-crm.git
cd hcp-ai-crm
```

### 2. Backend Setup
Navigate to the backend directory, set up the virtual environment, and install dependencies.
```bash
cd backend
python -m venv venv

# On Windows:
.\venv\Scripts\activate
# On macOS/Linux:
# source venv/bin/activate

pip install -r requirements.txt
```

Set up your environment variables by copying the example file:
```bash
copy .env.example .env
# macOS/Linux: cp .env.example .env
```
*Edit the `.env` file and insert your `GROQ_API_KEY` and MySQL `DATABASE_URL`.*

Start the FastAPI server:
```bash
uvicorn main:app --reload
```
*The API will be available at `http://localhost:8000`.*

### 3. Frontend Setup
Open a new terminal, navigate to the frontend directory, and start the development server.
```bash
cd frontend
npm install
npm run dev
```
*The React app will be available at `http://localhost:5173`.*

## Quality Management System (QMS) Integration / Task 2

In the heavily regulated Life Sciences industry, compliance is paramount. CogniCRM is designed with a Quality Management System (QMS) mindset to support pharmaceutical compliance requirements natively:

*   **Adverse Event (AE) Detection:** The AI agent is capable of identifying language related to potential Adverse Events during data extraction, prompting immediate alerts for pharmacovigilance reporting.
*   **CAPA Workflows:** Deviations in interaction protocols or missing mandatory regulatory data can trigger Corrective and Preventive Action (CAPA) routing directly within the CRM workflow.
*   **21 CFR Part 11 Compliance (Audit Trails):** By leveraging Redux Toolkit on the frontend and SQLAlchemy transactions on the backend, every incremental state change and AI data mutation is fully traceable. This immutable logging provides a robust audit trail, ensuring that all data entries are attributable, legible, contemporaneously recorded, original, and accurate (ALCOA principles).
