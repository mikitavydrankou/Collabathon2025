from sqlalchemy import Column, Date, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship

from . import Base


class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    surname = Column(String(100), nullable=False)
    balance = Column(Numeric(15, 2), nullable=False, default=0.00)
    date_of_birth = Column(Date, nullable=False)
    bank_number = Column(String(50), unique=True, nullable=False)
    person_to_contact_id = Column(
        Integer, ForeignKey("person_to_contact.person_to_contact_id"), nullable=True
    )
    username = Column(String(100), unique=True, nullable=False)
    password = Column(String(255), nullable=False)

    # Relationship
    person_to_contact = relationship("PersonToContact", backref="users")

    def __repr__(self):
        return f"<User(id={self.user_id}, username={self.username}, name={self.name} {self.surname})>"
