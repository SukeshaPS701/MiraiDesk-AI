from sqlalchemy.orm import declarative_base

Base = declarative_base()

# Import all models so SQLAlchemy knows about them
from app.models.user import User
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.memory import Memory