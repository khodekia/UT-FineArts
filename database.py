from sqlalchemy import create_engine, Column, Integer, String, BigInteger, Boolean, Table, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
import random
import string

Base = declarative_base()

user_workshops = Table('user_workshops', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('workshop_id', Integer, ForeignKey('workshops.id'))
)

class Workshop(Base):
    __tablename__ = 'workshops'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    capacity = Column(Integer, nullable=False)
    date = Column(String, nullable=False)
    time = Column(String, nullable=False)
    is_open = Column(Boolean, default=True)

class Setting(Base):
    __tablename__ = 'settings'
    key = Column(String, primary_key=True)
    value = Column(String, nullable=False)

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, nullable=False)
    full_name = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    national_id = Column(String, nullable=True)
    university = Column(String, nullable=True)
    major = Column(String, nullable=True)
    receipt_file_id = Column(String, nullable=True)
    status = Column(String, default="started") # started, pending, approved, rejected
    ticket_code = Column(String, nullable=True)

    workshops = relationship("Workshop", secondary=user_workshops, backref="users")

    def generate_ticket(self):
        if not self.ticket_code:
            self.ticket_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        return self.ticket_code

engine = create_engine('sqlite:///registrations.db', echo=False)
SessionLocal = sessionmaker(bind=engine)

def init_db():
    Base.metadata.create_all(engine)

def get_session():
    return SessionLocal()
