from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

Base = declarative_base()

class TaskRecord(Base):
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    description = Column(String, nullable=False)
    status = Column(String, default="completed") 
    result_summary = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class PreferenceRecord(Base):
    __tablename__ = "preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True)
    value = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class MemoryManager:
    def __init__(self, db_path="sqlite:///./nexus_memory.db"):
        self.engine = create_engine(db_path, connect_args={"check_same_thread": False})
        Base.metadata.create_all(bind=self.engine)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Short-term memory (in-memory per session)
        self.conversation_history = [] 

    def add_message(self, role: str, content: str | list):
        self.conversation_history.append({"role": role, "content": content})

    def get_history(self):
        return self.conversation_history

    def clear_history(self):
        self.conversation_history = []

    def save_task(self, description: str, result_summary: str, status: str = "completed"):
        with self.SessionLocal() as db:
            task = TaskRecord(description=description, result_summary=result_summary, status=status)
            db.add(task)
            db.commit()
            db.refresh(task)
            return task

    def get_tasks(self, limit=50):
        with self.SessionLocal() as db:
            tasks = db.query(TaskRecord).order_by(TaskRecord.created_at.desc()).limit(limit).all()
            result = [{"id": t.id, "description": t.description, "result": t.result_summary, "status": t.status, "date": t.created_at.isoformat()} for t in tasks]
            return result

    def save_preference(self, key: str, value: str):
        with self.SessionLocal() as db:
            pref = db.query(PreferenceRecord).filter(PreferenceRecord.key == key).first()
            if pref:
                pref.value = value
            else:
                pref = PreferenceRecord(key=key, value=value)
                db.add(pref)
            db.commit()

    def get_preferences(self):
        with self.SessionLocal() as db:
            prefs = db.query(PreferenceRecord).all()
            return {p.key: p.value for p in prefs}

memory_manager = MemoryManager()
