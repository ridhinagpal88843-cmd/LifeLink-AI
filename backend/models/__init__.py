"""
Models Layer (SQLAlchemy Declarative Entities)
==============================================

This module contains the primary database schemas representing persistent entities:
- Alert: Incoming emergency telemetry alerts (vitals, geographic coordinates).
- Patient: Medical profiles, allergies, primary physicians.
- Hospital: Geolocation, specialty departments, available beds.
- Ambulance: Current dispatch location, telemetry speed, active status.

These classes inherit from SQLAlchemy's declarative Base defined in database.py 
and map directly to database tables.
"""
