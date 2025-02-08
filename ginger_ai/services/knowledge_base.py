from typing import Dict, List, Optional
import os
from datetime import datetime
import sqlite3
from pathlib import Path
import logging
import anthropic
from llama_index import VectorStoreIndex, Document, ServiceContext
from llama_index.llms import Anthropic
from llama_index.embeddings import HuggingFaceEmbedding
import pandas as pd


class FamilyEnhancementAgent:
    def __init__(self, db_path: str = "family_agent.db"):
        # Initialize logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Initialize database
        self.db_path = db_path
        self.setup_database()
        
        # Initialize LLM (Claude)
        self.client = anthropic.Client(api_key=os.getenv("ANTHROPIC_API_KEY"))
        
        # Initialize embedding model (local)
        self.embed_model = HuggingFaceEmbedding(
            model_name="BAAI/bge-small-en-v1.5"
        )
        
        # Initialize vector store for knowledge base
        self.service_context = ServiceContext.from_defaults(
            llm=Anthropic(model="claude-3-sonnet-20240229"),
            embed_model=self.embed_model
        )
        
        # Create knowledge base directory if it doesn't exist
        self.kb_dir = Path("knowledge_base")
        self.kb_dir.mkdir(exist_ok=True)
        
    def setup_database(self):
        """Initialize SQLite database with necessary tables"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Create tables for tracking interactions, goals, and insights
        c.execute("""
            CREATE TABLE IF NOT EXISTS interactions (
                id INTEGER PRIMARY KEY,
                timestamp DATETIME,
                family_member TEXT,
                interaction_type TEXT,
                duration INTEGER,
                quality_score INTEGER,
                notes TEXT
            )
        """)
        
        c.execute("""
            CREATE TABLE IF NOT EXISTS goals (
                id INTEGER PRIMARY KEY,
                created_at DATETIME,
                category TEXT,
                description TEXT,
                target_date DATETIME,
                status TEXT,
                progress_notes TEXT
            )
        """)
        
        conn.commit()
        conn.close()
        
    def log_interaction(self, family_member: str, interaction_type: str, 
        duration: int, quality_score: int, notes: str = ""
    ):
        """Log a family interaction"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""
            INSERT INTO interactions 
            (timestamp, family_member, interaction_type, duration, quality_score, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (datetime.now(), family_member, interaction_type, duration, quality_score, notes))
        conn.commit()
        conn.close()
        
    def set_goal(self, category: str, description: str, target_date: datetime):
        """Set a new family-related goal"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""
            INSERT INTO goals 
            (created_at, category, description, target_date, status)
            VALUES (?, ?, ?, ?, ?)
        """, (datetime.now(), category, description, target_date, "active"))
        conn.commit()
        conn.close()
        
    def analyze_interactions(self, family_member: Optional[str] = None, 
        days: int = 30) -> Dict:
        """Analyze interaction patterns for insights"""
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query("""
            SELECT * FROM interactions 
            WHERE timestamp >= date('now', ?)
        """, conn, params=(f'-{days} days',))
        conn.close()
        
        if family_member:
            df = df[df['family_member'] == family_member]
            
        analysis = {
            'total_interactions': len(df),
            'total_duration': df['duration'].sum(),
            'avg_quality': df['quality_score'].mean(),
            'interaction_types': df['interaction_type'].value_counts().to_dict()
        }
        
        return analysis
