from chainlit.types import ThreadDict
from typing import Optional
import chainlit as cl
import jwt
import os

# # Authenticaion
# @cl.header_auth_callback
# def header_auth_callback(headers: dict) -> Optional[cl.User]:
#   # Verify the signature of a token in the header (ex: jwt token)
#   # or check that the value is matching a row from your database
#   cookie_header = headers.get("cookie")
#   if not cookie_header:
#       return None
  
#   # Parse cookie string
#   cookies = {}
#   for item in cookie_header.split(';'):
#       if '=' in item:
#           key, value = item.strip().split('=', 1)
#           cookies[key] = value
          
#   session_id = cookies.get("session")
#   if not session_id:
#       return None
  
#   try:
#       secret_key = os.getenv("SESSION_SECRET_KEY")
#       payload = jwt.decode(session_id, secret_key, algorithms=["HS256"])
#       return cl.User(
#           identifier=payload.get("email"),
#           metadata={"role": payload.get("role"), "user_id": payload.get("user_id")}
#       )
#   except jwt.InvalidTokenError:
#       return None
    
# Data Layer
@cl.data_layer
def get_data_layer():
    pass
    
@cl.on_chat_start
async def on_chat_start():
    app_user = cl.user_session.get("user")
    print("A new chat session has started!")
    await cl.Message(f"Hello {app_user.identifier}💐✨").send()    
    
@cl.on_chat_end
def on_chat_end():
    print("The user disconnected!")
    
@cl.on_chat_resume
async def on_chat_resume(thread: ThreadDict):
    print("The user resumed a previous chat session!")
    
    