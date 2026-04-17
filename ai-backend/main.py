from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
from typing import TypedDict, Optional
import os
import json

load_dotenv()

# ---------------- DATABASE ---------------- #
engine = create_engine(
    "postgresql://postgres:rsnaveen@localhost:5432/crm_db"
)
Base = declarative_base()

class Interaction(Base):
    __tablename__ = "interactions"

    id = Column(Integer, primary_key=True)
    hcp_name = Column(String)
    interaction_type = Column(String)
    date = Column(String)
    time = Column(String)
    attendees = Column(String)
    topics = Column(Text)
    materials = Column(String)
    sentiment = Column(String)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

# ---------------- LLM ---------------- #
llm = ChatGroq(
    api_key=os.getenv("GROQ_API_KEY"),
    model="llama-3.1-8b-instant"
)

# ---------------- FASTAPI ---------------- #
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatInput(BaseModel):
    message: str

# ---------------- STATE ---------------- #
class AgentState(TypedDict):
    message: str
    action: str
    response: Optional[str]
    data: Optional[dict]

# ---------------- TOOL 1: LOG ---------------- #
def log_interaction(state: AgentState):
    session = Session()
    try:
        ai = llm.invoke(f"""
You are a pharma CRM assistant.

Extract structured data.

Message:
{state['message']}

Return ONLY JSON:
{{
  "hcp_name": "...",
  "interaction_type": "...",
  "date": "...",
  "time": "...",
  "attendees": "...",
  "topics": "...",
  "materials": "...",
  "sentiment": "...",
  "notes": "..."
}}
""")

        try:
            extracted = json.loads(ai.content)
        except:
            extracted = {
                "hcp_name": "Unknown",
                "interaction_type": "Meeting",
                "date": str(datetime.utcnow().date()),
                "time": "",
                "attendees": "",
                "topics": "",
                "materials": "",
                "sentiment": "Neutral",
                "notes": state["message"]
            }

        interaction = Interaction(**extracted)
        session.add(interaction)
        session.commit()

        return {"response": "✅ Interaction logged!", "data": extracted}

    finally:
        session.close()

# ---------------- TOOL 2: EDIT ---------------- #
def edit_interaction(state: AgentState):
    session = Session()
    try:
        last = session.query(Interaction).order_by(Interaction.id.desc()).first()

        if not last:
            return {"response": "No interaction found.", "data": None}

        ai = llm.invoke(f"""
You are a CRM updater.

Field meanings:
- attendees = participants
- topics = discussion

IMPORTANT:
- ONLY update mentioned fields
- DO NOT leave fields empty
- KEEP others same

Current Data:
{{
  "hcp_name": "{last.hcp_name}",
  "interaction_type": "{last.interaction_type}",
  "date": "{last.date}",
  "time": "{last.time}",
  "attendees": "{last.attendees}",
  "topics": "{last.topics}",
  "materials": "{last.materials}",
  "sentiment": "{last.sentiment}",
  "notes": "{last.notes}"
}}

User:
{state['message']}

Return ONLY JSON.
""")

        print("EDIT RAW:", ai.content)

        try:
            updated = json.loads(ai.content)
        except:
            return {"response": "❌ Update failed.", "data": None}

        # Synonym handling
        if "participants" in updated:
            updated["attendees"] = updated["participants"]
        if "discussion" in updated:
            updated["topics"] = updated["discussion"]

        # Safe update
        last.hcp_name = updated.get("hcp_name") or last.hcp_name
        last.interaction_type = updated.get("interaction_type") or last.interaction_type
        last.date = updated.get("date") or last.date
        last.time = updated.get("time") or last.time
        last.attendees = updated.get("attendees") or last.attendees
        last.topics = updated.get("topics") or last.topics
        last.materials = updated.get("materials") or last.materials
        last.sentiment = updated.get("sentiment") or last.sentiment
        last.notes = updated.get("notes") or last.notes

        session.commit()

        return {
            "response": "✏️ Interaction updated!",
            "data": {
                "hcp_name": last.hcp_name,
                "interaction_type": last.interaction_type,
                "date": last.date,
                "time": last.time,
                "attendees": last.attendees,
                "topics": last.topics,
                "materials": last.materials,
                "sentiment": last.sentiment,
                "notes": last.notes
            }
        }

    finally:
        session.close()

# ---------------- TOOL 3: HISTORY ---------------- #
def get_history(state: AgentState):
    session = Session()
    try:
        items = session.query(Interaction).all()

        if not items:
            return {"response": "No history found.", "data": None}

        text = "\n".join([
            f"{i.id}. {i.hcp_name} - {i.sentiment}"
            for i in items
        ])

        return {"response": f"📋 History:\n{text}", "data": None}

    finally:
        session.close()

# ---------------- TOOL 4: SUMMARY ---------------- #
def summarize(state: AgentState):
    session = Session()
    try:
        items = session.query(Interaction).all()
        notes = " ".join([i.notes for i in items])

        ai = llm.invoke(f"Summarize these interactions:\n{notes}")

        return {"response": f"📊 Summary:\n{ai.content}", "data": None}

    finally:
        session.close()

# ---------------- TOOL 5: SUGGEST ---------------- #
def suggest(state: AgentState):
    ai = llm.invoke(f"""
Based on this:
{state['message']}

Give 3 follow-up actions for pharma sales.
""")

    return {"response": f"💡 Suggestions:\n{ai.content}", "data": None}

# ---------------- TOOL 6: DELETE ---------------- #
def delete_interaction(state: AgentState):
    session = Session()
    try:
        last = session.query(Interaction).order_by(Interaction.id.desc()).first()

        if not last:
            return {"response": "No interaction found.", "data": None}

        message = state["message"].lower()

        # 🔴 RESET ALL FIELDS
        if "all" in message:
            last.hcp_name = ""
            last.interaction_type = ""
            last.date = ""
            last.time = ""
            last.attendees = ""
            last.topics = ""
            last.materials = ""
            last.sentiment = ""
            last.notes = ""

            session.commit()

            return {
                "response": "🧹 Cleared all fields!",
                "data": {
                    "hcp_name": "",
                    "interaction_type": "",
                    "date": "",
                    "time": "",
                    "attendees": "",
                    "topics": "",
                    "materials": "",
                    "sentiment": "",
                    "notes": ""
                }
            }

        # 🧠 FIELD MAPPING (synonyms support)
        field_map = {
            "name": "hcp_name",
            "doctor": "hcp_name",
            "type": "interaction_type",
            "date": "date",
            "time": "time",
            "attendees": "attendees",
            "participants": "attendees",
            "discussion": "topics",
            "topics": "topics",
            "materials": "materials",
            "sentiment": "sentiment",
            "notes": "notes"
        }

        updated = {}

        # 🔵 CLEAR SPECIFIC FIELDS
        for key, field in field_map.items():
            if key in message:
                setattr(last, field, "")
                updated[field] = ""

        if not updated:
            return {"response": "⚠️ Specify a field to delete", "data": None}

        session.commit()

        return {
            "response": "🗑️ Field(s) cleared!",
            "data": {
                "hcp_name": last.hcp_name,
                "interaction_type": last.interaction_type,
                "date": last.date,
                "time": last.time,
                "attendees": last.attendees,
                "topics": last.topics,
                "materials": last.materials,
                "sentiment": last.sentiment,
                "notes": last.notes
            }
        }

    finally:
        session.close()
# ---------------- DECIDER ---------------- #
def decide(state: AgentState):
    ai = llm.invoke(f"""
You are an AI assistant.

Decide action:

- log → new interaction
- edit → update existing
- history → show past
- summarize → summary
- suggest → recommendations
- delete → remove interaction

Message:
{state['message']}

Return ONLY one word.
""")

    action = ai.content.strip().lower()

    if action not in ["log", "edit", "history", "summarize", "suggest", "delete"]:
        action = "log"

    return {"action": action}

# ---------------- GRAPH ---------------- #
graph = StateGraph(AgentState)

graph.add_node("decide", decide)
graph.add_node("log", log_interaction)
graph.add_node("edit", edit_interaction)
graph.add_node("history", get_history)
graph.add_node("summarize", summarize)
graph.add_node("suggest", suggest)
graph.add_node("delete", delete_interaction)

graph.set_entry_point("decide")

graph.add_conditional_edges(
    "decide",
    lambda state: state["action"],
    {
        "log": "log",
        "edit": "edit",
        "history": "history",
        "summarize": "summarize",
        "suggest": "suggest",
        "delete": "delete"
    }
)

graph.add_edge("log", END)
graph.add_edge("edit", END)
graph.add_edge("history", END)
graph.add_edge("summarize", END)
graph.add_edge("suggest", END)
graph.add_edge("delete", END)

agent = graph.compile()

# ---------------- API ---------------- #
@app.post("/chat")
async def chat(input: ChatInput):
    result = agent.invoke({
        "message": input.message,
        "action": "",
        "response": None,
        "data": None
    })

    return {
        "response": result.get("response"),
        "data": result.get("data")
    }

@app.get("/")
def root():
    return {"message": "AI CRM Backend Running 🚀"}