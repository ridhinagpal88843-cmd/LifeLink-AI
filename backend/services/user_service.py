from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.models.user import User
from backend.models.doctor import Doctor
from backend.models.emergency_health_profile import EmergencyHealthProfile
from backend.models.emergency_contact import EmergencyContact
from backend.schemas.user import UserCreate, UserUpdate
from backend.schemas.auth import LoginRequest
from backend.security.auth import get_password_hash, verify_password


class UserService:
    """
    UserService handles all core business logic for user accounts, 
    emergency profiles, primary doctors, and emergency contacts.
    """

    @staticmethod
    def create_user(db: Session, user_data: UserCreate) -> User:
        """
        Registers a new user, hashes password, links primary doctor, 
        creates emergency health profile, and inserts up to 5 contacts.
        Runs in an atomic transaction.
        """
        # 1. Check if user already exists
        existing_user = db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email address already registered"
            )

        # 2. Hash the user's password
        hashed_pw = get_password_hash(user_data.password)

        # 3. Create the User record
        db_user = User(
            email=user_data.email,
            hashed_password=hashed_pw,
            full_name=user_data.full_name,
            phone=user_data.phone
        )
        db.add(db_user)
        db.flush()  # Gen UUID for db_user

        # 4. Resolve Primary Doctor
        doctor_id = None
        if user_data.primary_doctor:
            doc_data = user_data.primary_doctor
            # Check if doctor already exists to reuse entry
            existing_doc = db.query(Doctor).filter(
                Doctor.name == doc_data.name,
                Doctor.phone == doc_data.phone
            ).first()

            if existing_doc:
                doctor_id = existing_doc.id
            else:
                db_doc = Doctor(
                    name=doc_data.name,
                    phone=doc_data.phone,
                    email=doc_data.email,
                    specialty=doc_data.specialty
                )
                db.add(db_doc)
                db.flush()
                doctor_id = db_doc.id

        # 5. Create Emergency Health Profile
        hp_data = user_data.emergency_health_profile
        db_profile = EmergencyHealthProfile(
            user_id=db_user.id,
            primary_doctor_id=doctor_id,
            blood_group=hp_data.blood_group,
            medical_conditions=hp_data.medical_conditions,
            allergies=hp_data.allergies,
            current_medications=hp_data.current_medications,
            emergency_preferences=hp_data.emergency_preferences
        )
        db.add(db_profile)

        # 6. Add Emergency Contacts (Up to 5)
        if len(user_data.emergency_contacts) > 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A maximum of 5 emergency contacts is allowed."
            )

        for contact in user_data.emergency_contacts:
            db_contact = EmergencyContact(
                user_id=db_user.id,
                name=contact.name,
                relationship=contact.relationship,
                phone=contact.phone,
                priority=contact.priority
            )
            db.add(db_contact)

        # Commit transaction
        db.commit()
        db.refresh(db_user)
        return db_user

    @staticmethod
    def authenticate_user(db: Session, login_data: LoginRequest) -> User:
        """
        Verify credentials. Returns user if authentic, else raises 401.
        """
        user = db.query(User).filter(User.email == login_data.email).first()
        if not user or not verify_password(login_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"}
            )
        return user

    @staticmethod
    def get_user_profile(db: Session, user_id: str) -> Optional[User]:
        """
        Retrieve user and relations by user UUID.
        """
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def update_user_profile(db: Session, user_id: str, update_data: UserUpdate) -> User:
        """
        Partially updates user, emergency profile, doctor, and contacts.
        Re-validates emergency contact array size limits (up to 5).
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found"
            )

        # Update User fields
        if update_data.full_name is not None:
            user.full_name = update_data.full_name
        if update_data.phone is not None:
            user.phone = update_data.phone

        # Update Emergency Health Profile fields
        profile = user.emergency_health_profile
        if update_data.emergency_health_profile is not None:
            hp_update = update_data.emergency_health_profile
            if hp_update.blood_group is not None:
                profile.blood_group = hp_update.blood_group
            if hp_update.medical_conditions is not None:
                profile.medical_conditions = hp_update.medical_conditions
            if hp_update.allergies is not None:
                profile.allergies = hp_update.allergies
            if hp_update.current_medications is not None:
                profile.current_medications = hp_update.current_medications
            if hp_update.emergency_preferences is not None:
                profile.emergency_preferences = hp_update.emergency_preferences

        # Update Doctor fields
        if update_data.primary_doctor is not None:
            doc_update = update_data.primary_doctor
            # Check if doctor already exists
            existing_doc = db.query(Doctor).filter(
                Doctor.name == doc_update.name,
                Doctor.phone == doc_update.phone
            ).first()

            if existing_doc:
                profile.primary_doctor_id = existing_doc.id
            else:
                db_doc = Doctor(
                    name=doc_update.name,
                    phone=doc_update.phone,
                    email=doc_update.email,
                    specialty=doc_update.specialty
                )
                db.add(db_doc)
                db.flush()
                profile.primary_doctor_id = db_doc.id

        # Update Emergency Contacts (Overwrite complete list if supplied)
        if update_data.emergency_contacts is not None:
            contacts_list = update_data.emergency_contacts
            if len(contacts_list) > 5:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="A maximum of 5 emergency contacts is allowed."
                )

            # Clear old contacts
            db.query(EmergencyContact).filter(EmergencyContact.user_id == user.id).delete()

            # Insert new contacts
            for contact in contacts_list:
                db_contact = EmergencyContact(
                    user_id=user.id,
                    name=contact.name,
                    relationship=contact.relationship,
                    phone=contact.phone,
                    priority=contact.priority
                )
                db.add(db_contact)

        db.commit()
        db.refresh(user)
        return user
