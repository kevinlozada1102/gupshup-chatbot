# app/models/__init__.py
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

# Import all models here for easy access
from .accounts import TblAccounts
from .chat_session import TblChatSession
from .session_segment import TblChatSessionSegment
from .gupshup_log import TblGupshupLog
from .message import TblMessage
from .products import TblProducts

__all__ = [
    'Base',
    'TblAccounts',
    'TblChatSession', 
    'TblChatSessionSegment',
    'TblGupshupLog',
    'TblMessage',
    'TblProducts'
]
