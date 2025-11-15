from sqlalchemy import Column, Integer, String

from . import Base


class PersonToContact(Base):
    __tablename__ = "person_to_contact"

    person_to_contact_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    surname = Column(String(100), nullable=False)
    phone_number = Column(String(20), nullable=False)
    email = Column(String(100), nullable=False)

    def __repr__(self):
        return f"<PersonToContact(id={self.person_to_contact_id}, name={self.name}, surname={self.surname})>"
