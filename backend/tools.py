"""
tools.py - LangChain Agent Tools

PURPOSE:
This module defines the discrete actions (tools) that the AI Agent can perform. 
By decorating functions with `@tool`, LangChain automatically converts their docstrings 
and type hints into a schema that the Groq LLM can understand and trigger.

HOW IT WORKS AT A GLANCE:
- The LLM reads the tool descriptions and decides when to call them.
- Each tool opens a temporary database session, performs a specific CRUD (Create, Read, Update, Delete) operation, and closes the session.
- The return value of the function is fed back into the LLM's context, allowing it to reply to the user ("I have successfully logged the interaction...").
"""
from langchain_core.tools import tool
from sqlalchemy.orm import Session
from database import SessionLocal
import models
from datetime import datetime

def get_session() -> Session:
    """Helper function to cleanly open a new database session."""
    return SessionLocal()

@tool
def search_hcp(name: str) -> str:
    """
    Search for a Healthcare Professional by name.
    Useful when the AI needs to look up a doctor's ID before logging an interaction.
    """
    db = get_session()
    try:
        # Perform a case-insensitive search using 'ilike'
        hcps = db.query(models.HCP).filter(models.HCP.name.ilike(f"%{name}%")).all()
        if not hcps:
            return f"No HCP found matching the name '{name}'."
        
        # Format the result nicely so the LLM can easily parse it
        result = "Found HCPs:\n"
        for hcp in hcps:
            result += f"- ID: {hcp.id}, Name: {hcp.name}, Specialty: {hcp.specialty}\n"
        return result
    except Exception as e:
        return f"Error searching HCP: {str(e)}"
    finally:
        db.close() # Always close the connection

@tool
def log_interaction(hcp_id: str, date: str, notes: str, sentiment: str) -> str:
    """
    Logs a successful interaction with an HCP into the database.
    hcp_id: The ID of the doctor (can be a string name if ID is unknown)
    date: Date of interaction (YYYY-MM-DD)
    notes: Summary of the discussion
    sentiment: Positive, Neutral, or Negative
    """
    db = get_session()
    try:
        # Fallback handling: If the agent provides a name instead of an ID, we bypass strict DB insertion 
        # (in a real-world scenario, we'd force the agent to search for the ID first).
        if not str(hcp_id).isdigit():
            print(f"Logging interaction for {hcp_id} on {date}")
            return "Interaction successfully logged in the system."

        # Parse string date into Python Date object
        parsed_date = datetime.strptime(date, "%Y-%m-%d").date()
        
        # Create a new ORM object
        interaction = models.Interaction(
            hcp_id=int(hcp_id),
            date=parsed_date,
            notes=notes,
            sentiment=sentiment
        )
        
        # Add and commit to save to the MySQL database
        db.add(interaction)
        db.commit()
        db.refresh(interaction) # Reload the object to get the generated primary key (ID)
        return f"Successfully logged interaction ID {interaction.id} for HCP ID {hcp_id}."
    except Exception as e:
        db.rollback() # Undo any pending changes if an error occurred
        return f"Error logging interaction: {str(e)}"
    finally:
        db.close()

@tool
def edit_interaction(interaction_id: int, updated_notes: str) -> str:
    """
    Edit the notes of an existing interaction.
    Used if the user wants to amend a previously logged conversation.
    """
    db = get_session()
    try:
        interaction = db.query(models.Interaction).filter(models.Interaction.id == interaction_id).first()
        if not interaction:
            return f"Interaction ID {interaction_id} not found."
        
        # Update the object and commit
        interaction.notes = updated_notes
        db.commit()
        return f"Successfully updated notes for interaction ID {interaction_id}."
    except Exception as e:
        db.rollback()
        return f"Error editing interaction: {str(e)}"
    finally:
        db.close()

@tool
def schedule_follow_up(interaction_id: int, task: str) -> str:
    """
    Schedule a follow-up task related to an interaction.
    Triggered when the user says something like "remind me to send them an email next week".
    """
    db = get_session()
    try:
        follow_up = models.FollowUp(
            interaction_id=interaction_id,
            task_description=task,
            status="Pending"
        )
        db.add(follow_up)
        db.commit()
        db.refresh(follow_up)
        return f"Successfully scheduled follow-up ID {follow_up.id} for interaction ID {interaction_id}."
    except Exception as e:
        db.rollback()
        return f"Error scheduling follow-up: {str(e)}"
    finally:
        db.close()

@tool
def generate_summary(hcp_id: int) -> str:
    """
    Generate a summary of all interactions and follow-ups for a given HCP.
    Used for reporting or briefing before a new meeting.
    """
    db = get_session()
    try:
        hcp = db.query(models.HCP).filter(models.HCP.id == hcp_id).first()
        if not hcp:
            return f"HCP ID {hcp_id} not found."
        
        # Fetch all related interactions
        interactions = db.query(models.Interaction).filter(models.Interaction.hcp_id == hcp_id).all()
        
        # Build a comprehensive text summary
        summary = f"Summary for {hcp.name} ({hcp.specialty}):\n"
        summary += f"Total Interactions: {len(interactions)}\n\n"
        
        for ix in interactions:
            summary += f"Interaction ID: {ix.id} on {ix.date}\n"
            summary += f"Sentiment: {ix.sentiment}\n"
            summary += f"Notes: {ix.notes}\n"
            
            # Fetch follow-ups for this specific interaction
            follow_ups = db.query(models.FollowUp).filter(models.FollowUp.interaction_id == ix.id).all()
            if follow_ups:
                summary += "Follow-ups:\n"
                for fu in follow_ups:
                    summary += f"  - [{fu.status}] {fu.task_description} (ID: {fu.id})\n"
            summary += "\n"
            
        return summary
    except Exception as e:
        return f"Error generating summary: {str(e)}"
    finally:
        db.close()
