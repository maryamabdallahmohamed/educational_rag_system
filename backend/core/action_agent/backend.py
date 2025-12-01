from fastapi import FastAPI
from pydantic import BaseModel

from chains import FULL_ROUTER_CHAIN
from handlers.dispatchers import dispatch_action, dispatch_query

app = FastAPI()

class MessageIn(BaseModel):
    text: str

@app.post("/route")
def route_message(msg: MessageIn):
    result = FULL_ROUTER_CHAIN.invoke(
        {
            "user_message": msg.text,
            "dispatch_action": dispatch_action,
            "dispatch_query": dispatch_query,
        }
    )
    return result