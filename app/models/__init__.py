# app/models/__init__.py
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

# Import all models here for easy access
from .accounts import TblAccounts
from .account_prompts import TblAccountPrompts
from .chat_session import TblChatSession
from .session_segment import TblChatSessionSegment
from .session_data import TblSessionData
from .simple_answer import TblSimpleAnswer
from .text_chatbot import TblTextChatbot
from .gupshup_log import TblGupshupLog
from .message import TblMessage
from .products import TblProducts

__all__ = [
    'Base',
    'TblAccounts',
    'TblAccountPrompts',
    'TblChatSession', 
    'TblChatSessionSegment',
    'TblSessionData',
    'TblSimpleAnswer',
    'TblTextChatbot',
    'TblGupshupLog',
    'TblMessage',
    'TblProducts'
]
