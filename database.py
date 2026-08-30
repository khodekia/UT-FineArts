import random
import string
from sqlalchemy import create_engine, Column, Integer, String, BigInteger
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

engine = create_engine('sqlite:///registrations.db', echo=False)
Base = declarative_base()
Session = sessionmaker(bind=engine)

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, nullable=False)
    full_name = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    national_id = Column(String, nullable=True)
    university = Column(String, nullable=True)
    major = Column(String, nullable=True)
    marital_status = Column(String, nullable=True)
    receipt_file_id = Column(String, nullable=True)
    status = Column(String, default="started") # started, pending, approved, rejected
    ticket_code = Column(String, nullable=True)

    def generate_ticket(self):
        chars = string.ascii_uppercase + string.digits
        self.ticket_code = ''.join(random.choice(chars) for _ in range(8))
        return self.ticket_code

def init_db():
    Base.metadata.create_all(engine)

def get_session():
    return Session()
