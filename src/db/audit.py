import sqlite3
import json
from datetime import datetime
from src.config import DB_PATH
from typing import Dict, Any

class AuditLogger:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    payment_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    input_data TEXT,
                    classification_result TEXT,
                    decision_result TEXT,
                    execution_outcome TEXT,
                    amount_recovered INTEGER DEFAULT 0,
                    status TEXT NOT NULL
                )
            ''')
            conn.commit()

    def log_record(
        self, 
        payment_id: str, 
        input_data: Dict[str, Any], 
        classification: Dict[str, Any], 
        decision: Dict[str, Any],
        execution_outcome: Dict[str, Any],
        amount_recovered: int,
        status: str
    ):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO audit_log (
                    payment_id, timestamp, input_data, classification_result, 
                    decision_result, execution_outcome, amount_recovered, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                payment_id,
                datetime.utcnow().isoformat(),
                json.dumps(input_data),
                json.dumps(classification),
                json.dumps(decision),
                json.dumps(execution_outcome),
                amount_recovered,
                status
            ))
            conn.commit()

    def get_summary_metrics(self) -> Dict[str, Any]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) as total_processed FROM audit_log")
            total = cursor.fetchone()["total_processed"]
            
            cursor.execute("SELECT COUNT(*) as successful_recovery, SUM(amount_recovered) as total_recovered FROM audit_log WHERE status = 'recovered'")
            success_row = cursor.fetchone()
            recovered_count = success_row["successful_recovery"] or 0
            recovered_amount = success_row["total_recovered"] or 0
            
            cursor.execute("SELECT decision_result FROM audit_log WHERE status != 'recovered'")
            exceptions = cursor.fetchall()
            
            return {
                "total_processed": total,
                "recovered_count": recovered_count,
                "recovery_rate_percent": (recovered_count / total * 100) if total > 0 else 0.0,
                "total_amount_recovered_inr": recovered_amount / 100.0,
                "escalations_and_exceptions": len(exceptions)
            }
