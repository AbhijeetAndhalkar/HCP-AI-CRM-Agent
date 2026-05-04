"""
models.py - Database Schema Definitions

PURPOSE:
This module defines the structure of our MySQL database tables using SQLAlchemy ORM models.
Instead of writing raw SQL `CREATE TABLE` commands, we define Python classes. SQLAlchemy 
automatically translates these classes into the appropriate database schema.

HOW IT WORKS AT A GLANCE:
- Each class represents a table in the database.
- Each attribute (Column) represents a column in that table.
- We use `relationship` to define connections (foreign keys) between tables, 
  allowing us to easily fetch related data (e.g., getting an HCP's interactions).
"""
from sqlalchemy import Column, Integer, String, Text, ForeignKey, Date
from sqlalchemy.orm import relationship
from database import Base

class HCP(Base):
    """
    Healthcare Professional (HCP) Model.
    Represents the 'hcps' table holding doctor details.
    """
    __tablename__ = "hcps"

    # Primary key: Unique identifier for each doctor. index=True speeds up lookups.
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), index=True, nullable=False)
    specialty = Column(String(255))

    # One-to-Many Relationship: An HCP can have multiple interactions.
    # cascade="all, delete-orphan": If an HCP is deleted, delete all their interactions too.
    interactions = relationship("Interaction", back_populates="hcp", cascade="all, delete-orphan")


class Interaction(Base):
    """
    Interaction Model.
    Represents the 'interactions' table storing logs of meetings/calls with an HCP.
    """
    __tablename__ = "interactions"

    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign Key linking this interaction to a specific HCP.
    hcp_id = Column(Integer, ForeignKey("hcps.id"), nullable=False)
    date = Column(Date, nullable=False)
    notes = Column(Text)
    sentiment = Column(String(50))  # Expected values: Positive, Neutral, Negative

    # Bidirectional relationship back to the HCP model.
    hcp = relationship("HCP", back_populates="interactions")
    
    # One-to-Many Relationship: An interaction can generate multiple follow-up tasks.
    follow_ups = relationship("FollowUp", back_populates="interaction", cascade="all, delete-orphan")


class FollowUp(Base):
    """
    FollowUp Model.
    Represents the 'follow_ups' table storing tasks assigned after an interaction.
    """
    __tablename__ = "follow_ups"

    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign Key linking this task to a specific interaction.
    interaction_id = Column(Integer, ForeignKey("interactions.id"), nullable=False)
    task_description = Column(Text, nullable=False)
    status = Column(String(50), default="Pending") # e.g., Pending, Completed

    # Bidirectional relationship back to the Interaction model.
    interaction = relationship("Interaction", back_populates="follow_ups")
