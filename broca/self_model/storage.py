"""
Storage layer for persisting self-model with version history.
"""

from __future__ import annotations

import json
import os
import tempfile
import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime, timezone

from .model import SelfModel

logger = logging.getLogger(__name__)


class SelfModelStorage:
    """
    Storage for self-model with version history.
    
    DEPRECATED: Use SelfModelSQLiteStorage instead.
    This class is kept only for migration purposes.
    
    Stores self-model as JSON with version history for rollback and analysis.
    """
    
    def __init__(self, storage_path: str = "self_model.json") -> None:
        """
        Initialize self-model storage.
        
        Args:
            storage_path: Path to JSON file for storing self-model
        """
        self.storage_path = Path(storage_path)
        self._version_history: List[Dict[str, Any]] = []
        logger.info(f"Initialized SelfModelStorage at {self.storage_path.absolute()}")
    
    def load(self) -> Optional[SelfModel]:
        """
        Load the current self-model from storage.
        
        Returns:
            SelfModel instance if found, None otherwise
        """
        if not self.storage_path.exists():
            logger.debug(f"Self-model file not found at {self.storage_path}, returning None")
            return None
        
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Load version history if present
            self._version_history = data.get("version_history", [])
            
            # Load current model
            model_data = data.get("current", {})
            if not model_data:
                logger.warning("Self-model file exists but has no current model")
                return None
            
            # If the stored metadata indicates an older schema, optionally
            # perform an automatic non-destructive migration using our
            # migration helper. We will prefer to keep current behavior
            # unless a migration is explicitly requested by the operator.
            try:
                model = SelfModel.from_dict(model_data)
            except Exception:
                # Attempt an on-the-fly migration if validation fails
                try:
                    from .migrations.migrate_to_v2 import migrate_to_v2
                    migrated = migrate_to_v2(model_data)
                    model = SelfModel.from_dict(migrated)
                    logger.info("Auto-migrated self-model during load via migrate_to_v2")
                except Exception as e:
                    logger.error(f"Failed to auto-migrate self-model: {e}", exc_info=True)
                    return None
            logger.info(f"Loaded self-model version {model.metadata.get('version', 'unknown')}")
            return model
            
        except (OSError, IOError, json.JSONDecodeError) as e:
            logger.error(f"Failed to load self-model: {e}", exc_info=True)
            return None
    
    def save(self, model: SelfModel) -> None:
        """
        Save self-model to storage with version history.
        
        Args:
            model: SelfModel instance to save
        """
        try:
            # Load existing data to preserve version history
            existing_data = {}
            if self.storage_path.exists():
                try:
                    with open(self.storage_path, 'r', encoding='utf-8') as f:
                        existing_data = json.load(f)
                except (OSError, IOError, json.JSONDecodeError):
                    pass  # Start fresh if can't read existing
            
            # Get existing version history
            existing_history = existing_data.get("version_history", [])
            
            # Add current model to history if it exists and is different
            current_model_data = existing_data.get("current")
            if current_model_data:
                current_version = current_model_data.get("metadata", {}).get("version", 0)
                new_version = model.metadata.get("version", 0)
                if current_version != new_version:
                    # Add to history with timestamp
                    existing_history.append({
                        "model": current_model_data,
                        "archived_at": datetime.now(timezone.utc).isoformat(),
                        "version": current_version,
                    })
                    # Keep only last 50 versions
                    existing_history = existing_history[-50:]
            
            # Prepare data structure
            data = {
                "current": model.to_dict(),
                "version_history": existing_history,
                "last_saved": datetime.now(timezone.utc).isoformat(),
            }
            
            # Atomic write with custom JSON encoder for datetime
            class DateTimeEncoder(json.JSONEncoder):
                def default(self, obj):
                    if isinstance(obj, datetime):
                        return obj.isoformat()
                    return super().default(obj)
            
            with tempfile.NamedTemporaryFile(
                mode='w',
                dir=self.storage_path.parent,
                delete=False,
                suffix='.tmp'
            ) as tmp_file:
                json.dump(data, tmp_file, indent=2, ensure_ascii=False, cls=DateTimeEncoder)
                tmp_path = tmp_file.name
            
            # Atomic rename
            os.replace(tmp_path, self.storage_path)
            
            # Update in-memory history
            self._version_history = existing_history
            
            logger.info(f"Saved self-model version {model.metadata.get('version', 'unknown')} to {self.storage_path}")
            
        except (OSError, IOError, json.JSONDecodeError) as e:
            logger.error(f"Failed to save self-model: {e}", exc_info=True)
            # Clean up temp file if it exists
            if 'tmp_path' in locals():
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass
            raise
    
    def get_version_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get version history of self-model.
        
        Args:
            limit: Optional limit on number of versions to return
            
        Returns:
            List of version dictionaries
        """
        if not self._version_history:
            # Try to load from file if not in memory
            if self.storage_path.exists():
                try:
                    with open(self.storage_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    self._version_history = data.get("version_history", [])
                except (OSError, IOError, json.JSONDecodeError):
                    pass
        
        history = self._version_history
        if limit:
            history = history[-limit:]
        
        return history
    
    def get_version(self, version: int) -> Optional[SelfModel]:
        """
        Get a specific version of the self-model from history.
        
        Args:
            version: Version number to retrieve
            
        Returns:
            SelfModel instance if found, None otherwise
        """
        history = self.get_version_history()
        
        for entry in history:
            if entry.get("version") == version:
                model_data = entry.get("model", {})
                if model_data:
                    return SelfModel.from_dict(model_data)
        
        # Check current version
        current = self.load()
        if current and current.metadata.get("version") == version:
            return current
        
        logger.warning(f"Version {version} not found in history")
        return None


class SelfModelSQLiteStorage:
    """
    SQLite-based storage for self-model with version history.
    
    Stores self-model in SQLite database with separate tables for:
    - Core self-model data
    - Epistemic layer components
    - Version history
    """
    
    def __init__(self, db_path: str = "self_model.db") -> None:
        """
        Initialize SQLite storage for self-model.
        
        Args:
            db_path: Path to SQLite database file (relative or absolute)
        """
        # Resolve to absolute path to ensure consistent persistence location
        db_path_obj = Path(db_path)
        if not db_path_obj.is_absolute():
            # Resolve relative paths to absolute
            self.db_path = db_path_obj.resolve()
        else:
            self.db_path = db_path_obj
        
        # Ensure parent directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self._init_schema()
        logger.info(f"Initialized SelfModelSQLiteStorage at {self.db_path.absolute()}")
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection using absolute path."""
        # Use absolute path to ensure consistent database location
        abs_path = self.db_path.absolute()
        conn = sqlite3.connect(str(abs_path))
        conn.row_factory = sqlite3.Row
        return conn
    
    def _init_schema(self) -> None:
        """Initialize database schema."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # Core self-model table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS self_models (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    version INTEGER NOT NULL,
                    capabilities TEXT NOT NULL,
                    knowledge_boundaries TEXT NOT NULL,
                    constraints TEXT NOT NULL,
                    metadata TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    last_updated TEXT NOT NULL,
                    is_current INTEGER NOT NULL DEFAULT 0
                )
            """)
            
            # Handle migration: check if old columns exist and drop them if present
            # SQLite doesn't support DROP COLUMN directly, so we'll handle it in queries
            # For now, we'll just not use those columns in new tables
            
            # Epistemic knowledge sources
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS epistemic_knowledge_sources (
                    knowledge_id TEXT PRIMARY KEY,
                    self_model_id INTEGER NOT NULL,
                    source_type TEXT NOT NULL,
                    source_metadata TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (self_model_id) REFERENCES self_models(id)
                )
            """)
            
            # Epistemic confidence metrics
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS epistemic_confidence_metrics (
                    knowledge_id TEXT PRIMARY KEY,
                    self_model_id INTEGER NOT NULL,
                    metrics TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (self_model_id) REFERENCES self_models(id)
                )
            """)
            
            # Epistemic verification history
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS epistemic_verification_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    knowledge_id TEXT NOT NULL,
                    self_model_id INTEGER NOT NULL,
                    verification_record TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    FOREIGN KEY (self_model_id) REFERENCES self_models(id)
                )
            """)
            
            # Epistemic inference chains
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS epistemic_inference_chains (
                    knowledge_id TEXT PRIMARY KEY,
                    self_model_id INTEGER NOT NULL,
                    inference_node TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (self_model_id) REFERENCES self_models(id)
                )
            """)
            
            # Epistemic temporal dynamics
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS epistemic_temporal_dynamics (
                    knowledge_id TEXT PRIMARY KEY,
                    self_model_id INTEGER NOT NULL,
                    evolution TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (self_model_id) REFERENCES self_models(id)
                )
            """)
            
            # Memory-knowledge mapping
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS memory_knowledge_mapping (
                    memory_id INTEGER PRIMARY KEY,
                    knowledge_id TEXT NOT NULL,
                    self_model_id INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (self_model_id) REFERENCES self_models(id)
                )
            """)
            
            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_self_models_version ON self_models(version)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_self_models_current ON self_models(is_current)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_epistemic_self_model ON epistemic_knowledge_sources(self_model_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_verification_self_model ON epistemic_verification_history(self_model_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_memory_mapping_self_model ON memory_knowledge_mapping(self_model_id)")
            
            conn.commit()
            logger.debug("Initialized SQLite schema")
            
        finally:
            conn.close()
    
    def load(self) -> Optional[SelfModel]:
        """
        Load the current self-model from SQLite.
        
        Returns:
            SelfModel instance if found, None otherwise
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # Get current model
            cursor.execute("""
                SELECT * FROM self_models 
                WHERE is_current = 1 
                ORDER BY version DESC 
                LIMIT 1
            """)
            
            row = cursor.fetchone()
            if not row:
                logger.debug("No current self-model found in SQLite")
                return None
            
            # Load core model data (handle backward compatibility)
            # Check which columns exist (for migration from old schema)
            model_data = {
                "capabilities": json.loads(row["capabilities"]),
                "knowledge_boundaries": json.loads(row["knowledge_boundaries"]),
                "constraints": json.loads(row["constraints"]),
                "metadata": json.loads(row["metadata"]),
            }
            # Old schema had preferences and behavioral_patterns - ignore them if present
            # SelfModel.from_dict() will ignore them since they're no longer in the model
            
            # Load epistemic layer
            self_model_id = row["id"]
            epistemic_layer = self._load_epistemic_layer(cursor, self_model_id)
            model_data["epistemic_layer"] = epistemic_layer
            
            # If the stored metadata indicates an older schema, optionally
            # perform an automatic non-destructive migration using our
            # migration helper. We will prefer to keep current behavior
            # unless a migration is explicitly requested by the operator.
            try:
                model = SelfModel.from_dict(model_data)
            except Exception:
                # Attempt an on-the-fly migration if validation fails
                try:
                    from .migrations.migrate_to_v2 import migrate_to_v2
                    migrated = migrate_to_v2(model_data)
                    model = SelfModel.from_dict(migrated)
                    logger.info("Auto-migrated self-model during load via migrate_to_v2")
                except Exception as e:
                    logger.error(f"Failed to auto-migrate self-model: {e}", exc_info=True)
                    return None
            
            # Log epistemic layer status
            if epistemic_layer:
                knowledge_count = len(epistemic_layer.knowledge_sources)
                logger.info(
                    f"Loaded self-model version {model.metadata.get('version', 'unknown')} from SQLite "
                    f"with epistemic layer ({knowledge_count} knowledge items)"
                )
            else:
                logger.info(
                    f"Loaded self-model version {model.metadata.get('version', 'unknown')} from SQLite "
                    f"without epistemic layer"
                )
            
            return model
            
        except Exception as e:
            logger.error(f"Failed to load self-model from SQLite: {e}", exc_info=True)
            return None
        finally:
            conn.close()
    
    def _load_epistemic_layer(self, cursor: sqlite3.Cursor, self_model_id: int) -> Optional[Any]:
        """Load epistemic layer from database.
        
        If no epistemic data exists for the current model, checks for data from
        the most recent model version that has epistemic data.
        """
        from .epistemic.layer import EpistemicLayer
        from .epistemic.models import SourceMetadata, ConfidenceMetrics, VerificationRecord, InferenceNode, KnowledgeEvolution
        
        # Check if there's any epistemic data for this model
        cursor.execute("""
            SELECT COUNT(*) as count FROM epistemic_knowledge_sources 
            WHERE self_model_id = ?
        """, (self_model_id,))
        has_data = cursor.fetchone()["count"] > 0
        
        if not has_data:
            # Check other tables too
            cursor.execute("""
                SELECT COUNT(*) as count FROM epistemic_confidence_metrics 
                WHERE self_model_id = ?
            """, (self_model_id,))
            has_data = cursor.fetchone()["count"] > 0
        
        if not has_data:
            cursor.execute("""
                SELECT COUNT(*) as count FROM memory_knowledge_mapping 
                WHERE self_model_id = ?
            """, (self_model_id,))
            has_data = cursor.fetchone()["count"] > 0
        
        # If no epistemic data exists for current model, check for data from previous versions
        if not has_data:
            # Find the most recent model version that has epistemic data
            cursor.execute("""
                SELECT DISTINCT sm.id, sm.version
                FROM self_models sm
                WHERE EXISTS (
                    SELECT 1 FROM epistemic_knowledge_sources eks
                    WHERE eks.self_model_id = sm.id
                ) OR EXISTS (
                    SELECT 1 FROM epistemic_confidence_metrics ecm
                    WHERE ecm.self_model_id = sm.id
                ) OR EXISTS (
                    SELECT 1 FROM memory_knowledge_mapping mkm
                    WHERE mkm.self_model_id = sm.id
                )
                ORDER BY sm.version DESC
                LIMIT 1
            """)
            row = cursor.fetchone()
            if row:
                # Found epistemic data from a previous version, use that model_id
                previous_model_id = row["id"]
                logger.info(
                    f"No epistemic data for current model (id={self_model_id}), "
                    f"loading from previous version (id={previous_model_id}, version={row['version']})"
                )
                self_model_id = previous_model_id
                has_data = True
        
        # If still no epistemic data exists, return None
        if not has_data:
            logger.debug(f"No epistemic data found for model id={self_model_id}")
            return None
        
        layer = EpistemicLayer()
        
        try:
            # Count total knowledge items for logging
            cursor.execute("""
                SELECT COUNT(*) as count FROM epistemic_knowledge_sources 
                WHERE self_model_id = ?
            """, (self_model_id,))
            knowledge_count = cursor.fetchone()["count"]
            
            logger.info(f"Loading epistemic layer with {knowledge_count} knowledge items from model id={self_model_id}")
            
            # Load knowledge sources
            cursor.execute("""
                SELECT knowledge_id, source_type, source_metadata 
                FROM epistemic_knowledge_sources 
                WHERE self_model_id = ?
            """, (self_model_id,))
            
            for row in cursor.fetchall():
                knowledge_id = row["knowledge_id"]
                source_data = json.loads(row["source_metadata"])
                source_data["source_type"] = row["source_type"]
                # Handle datetime conversion
                if "timestamp" in source_data and isinstance(source_data["timestamp"], str):
                    source_data["timestamp"] = datetime.fromisoformat(source_data["timestamp"])
                layer.knowledge_sources[knowledge_id] = SourceMetadata(**source_data)
            
            # Load confidence metrics
            cursor.execute("""
                SELECT knowledge_id, metrics 
                FROM epistemic_confidence_metrics 
                WHERE self_model_id = ?
            """, (self_model_id,))
            
            for row in cursor.fetchall():
                knowledge_id = row["knowledge_id"]
                metrics_data = json.loads(row["metrics"])
                layer.confidence_calibration[knowledge_id] = ConfidenceMetrics(**metrics_data)
            
            # Load verification history
            cursor.execute("""
                SELECT knowledge_id, verification_record 
                FROM epistemic_verification_history 
                WHERE self_model_id = ?
                ORDER BY timestamp
            """, (self_model_id,))
            
            for row in cursor.fetchall():
                knowledge_id = row["knowledge_id"]
                record_data = json.loads(row["verification_record"])
                # Handle datetime conversion
                if "timestamp" in record_data and isinstance(record_data["timestamp"], str):
                    record_data["timestamp"] = datetime.fromisoformat(record_data["timestamp"])
                # Handle new_evidence list
                if "new_evidence" in record_data:
                    evidence_list = []
                    for ev_data in record_data["new_evidence"]:
                        if isinstance(ev_data, dict):
                            if "timestamp" in ev_data and isinstance(ev_data["timestamp"], str):
                                ev_data["timestamp"] = datetime.fromisoformat(ev_data["timestamp"])
                            evidence_list.append(SourceMetadata(**ev_data))
                        else:
                            evidence_list.append(ev_data)
                    record_data["new_evidence"] = evidence_list
                layer.add_verification_record(knowledge_id, VerificationRecord(**record_data))
            
            # Load inference chains
            cursor.execute("""
                SELECT knowledge_id, inference_node 
                FROM epistemic_inference_chains 
                WHERE self_model_id = ?
            """, (self_model_id,))
            
            for row in cursor.fetchall():
                knowledge_id = row["knowledge_id"]
                node_data = json.loads(row["inference_node"])
                layer.inference_chains[knowledge_id] = InferenceNode(**node_data)
            
            # Load temporal dynamics
            cursor.execute("""
                SELECT knowledge_id, evolution 
                FROM epistemic_temporal_dynamics 
                WHERE self_model_id = ?
            """, (self_model_id,))
            
            for row in cursor.fetchall():
                knowledge_id = row["knowledge_id"]
                evolution_data = json.loads(row["evolution"])
                # Handle datetime in creation_event
                if "creation_event" in evolution_data and "timestamp" in evolution_data["creation_event"]:
                    ts = evolution_data["creation_event"]["timestamp"]
                    if isinstance(ts, str):
                        evolution_data["creation_event"]["timestamp"] = datetime.fromisoformat(ts)
                layer.temporal_dynamics[knowledge_id] = KnowledgeEvolution(**evolution_data)
            
            # Load memory-knowledge mapping
            cursor.execute("""
                SELECT memory_id, knowledge_id 
                FROM memory_knowledge_mapping 
                WHERE self_model_id = ?
            """, (self_model_id,))
            
            for row in cursor.fetchall():
                memory_id = int(row["memory_id"])
                knowledge_id = row["knowledge_id"]
                layer.memory_knowledge_mapping[memory_id] = knowledge_id
            
            # Log successful load with counts
            actual_count = len(layer.knowledge_sources)
            logger.info(
                f"Successfully loaded epistemic layer: {actual_count} knowledge items, "
                f"{len(layer.confidence_calibration)} confidence metrics, "
                f"{sum(len(v) for v in layer.verification_history.values())} verification records"
            )
            
            return layer
            
        except Exception as e:
            logger.warning(f"Error loading epistemic layer: {e}", exc_info=True)
            return None
    
    def save(self, model: SelfModel) -> None:
        """
        Save self-model to SQLite with version history.
        
        Args:
            model: SelfModel instance to save
            
        Raises:
            Exception: If save operation fails
        """
        # Ensure parent directory exists before attempting save
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Log the absolute path being used for persistence
        abs_path = self.db_path.absolute()
        logger.debug(f"Persisting self-model to database at: {abs_path}")
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # Mark previous current model as not current
            cursor.execute("UPDATE self_models SET is_current = 0 WHERE is_current = 1")
            
            # Get current version to check if we need to archive
            cursor.execute("SELECT MAX(version) as max_version FROM self_models")
            row = cursor.fetchone()
            max_version = row["max_version"] if row and row["max_version"] else 0
            current_version = model.metadata.get("version", 1)
            
            # Insert new model
            now = datetime.now(timezone.utc).isoformat()
            cursor.execute("""
                INSERT INTO self_models (
                    version, capabilities, knowledge_boundaries,
                    constraints, metadata,
                    created_at, last_updated, is_current
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 1)
            """, (
                current_version,
                json.dumps(model.capabilities),
                json.dumps(model.knowledge_boundaries),
                json.dumps(model.constraints),
                json.dumps(model.metadata),
                model.metadata.get("created_at", now),
                now
            ))
            
            self_model_id = cursor.lastrowid
            
            # Save epistemic layer
            if model.epistemic_layer:
                self._save_epistemic_layer(cursor, self_model_id, model.epistemic_layer)
            
            # Keep only last 50 versions
            cursor.execute("""
                DELETE FROM self_models 
                WHERE id NOT IN (
                    SELECT id FROM self_models 
                    ORDER BY version DESC 
                    LIMIT 50
                ) AND is_current = 0
            """)
            
            conn.commit()
            logger.info(
                f"Successfully saved self-model version {current_version} to SQLite at {abs_path}"
            )
            
            # Verify the save by checking file exists and was updated
            if not self.db_path.exists():
                logger.warning(f"Database file not found after save at {abs_path}")
            else:
                logger.debug(f"Database file verified at {abs_path}")
            
        except sqlite3.OperationalError as e:
            conn.rollback()
            error_msg = f"Database operational error saving self-model to {abs_path}: {e}"
            logger.error(error_msg, exc_info=True)
            raise RuntimeError(error_msg) from e
        except Exception as e:
            conn.rollback()
            error_msg = f"Failed to save self-model to SQLite at {abs_path}: {e}"
            logger.error(error_msg, exc_info=True)
            raise
        finally:
            conn.close()
    
    def _save_epistemic_layer(self, cursor: sqlite3.Cursor, self_model_id: int, layer: Any) -> None:
        """Save epistemic layer to database."""
        now = datetime.now(timezone.utc).isoformat()
        
        def serialize_for_json(obj):
            """Recursively serialize object for JSON, converting datetime to ISO strings."""
            if isinstance(obj, datetime):
                return obj.isoformat()
            elif isinstance(obj, dict):
                return {k: serialize_for_json(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [serialize_for_json(item) for item in obj]
            elif hasattr(obj, 'model_dump'):
                try:
                    return serialize_for_json(obj.model_dump(mode='json'))
                except TypeError:
                    return serialize_for_json(obj.model_dump())
            else:
                return obj
        
        try:
            # Save knowledge sources
            for knowledge_id, source in layer.knowledge_sources.items():
                source_dict = source.model_dump() if hasattr(source, 'model_dump') else source
                source_dict = serialize_for_json(source_dict)
                cursor.execute("""
                    INSERT OR REPLACE INTO epistemic_knowledge_sources 
                    (knowledge_id, self_model_id, source_type, source_metadata, created_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    knowledge_id,
                    self_model_id,
                    source_dict.get("source_type", ""),
                    json.dumps(source_dict),
                    now
                ))
            
            # Save confidence metrics
            for knowledge_id, metrics in layer.confidence_calibration.items():
                metrics_dict = metrics.model_dump() if hasattr(metrics, 'model_dump') else metrics
                metrics_dict = serialize_for_json(metrics_dict)
                cursor.execute("""
                    INSERT OR REPLACE INTO epistemic_confidence_metrics 
                    (knowledge_id, self_model_id, metrics, updated_at)
                    VALUES (?, ?, ?, ?)
                """, (
                    knowledge_id,
                    self_model_id,
                    json.dumps(metrics_dict),
                    now
                ))
            
            # Save verification history
            for knowledge_id, records in layer.verification_history.items():
                for record in records:
                    record_dict = record.model_dump() if hasattr(record, 'model_dump') else record
                    record_dict = serialize_for_json(record_dict)
                    timestamp = record_dict.get("timestamp", now)
                    if isinstance(timestamp, datetime):
                        timestamp = timestamp.isoformat()
                    cursor.execute("""
                        INSERT INTO epistemic_verification_history 
                        (knowledge_id, self_model_id, verification_record, timestamp)
                        VALUES (?, ?, ?, ?)
                    """, (
                        knowledge_id,
                        self_model_id,
                        json.dumps(record_dict),
                        timestamp
                    ))
            
            # Save inference chains
            for knowledge_id, node in layer.inference_chains.items():
                node_dict = node.model_dump() if hasattr(node, 'model_dump') else node
                node_dict = serialize_for_json(node_dict)
                cursor.execute("""
                    INSERT OR REPLACE INTO epistemic_inference_chains 
                    (knowledge_id, self_model_id, inference_node, updated_at)
                    VALUES (?, ?, ?, ?)
                """, (
                    knowledge_id,
                    self_model_id,
                    json.dumps(node_dict),
                    now
                ))
            
            # Save temporal dynamics
            for knowledge_id, evolution in layer.temporal_dynamics.items():
                evolution_dict = evolution.model_dump() if hasattr(evolution, 'model_dump') else evolution
                evolution_dict = serialize_for_json(evolution_dict)
                cursor.execute("""
                    INSERT OR REPLACE INTO epistemic_temporal_dynamics 
                    (knowledge_id, self_model_id, evolution, updated_at)
                    VALUES (?, ?, ?, ?)
                """, (
                    knowledge_id,
                    self_model_id,
                    json.dumps(evolution_dict),
                    now
                ))
            
            # Save memory-knowledge mapping
            mapping_count = len(layer.memory_knowledge_mapping)
            if mapping_count > 0:
                logger.debug(f"Saving {mapping_count} memory-knowledge mappings to database")
            for memory_id, knowledge_id in layer.memory_knowledge_mapping.items():
                cursor.execute("""
                    INSERT OR REPLACE INTO memory_knowledge_mapping 
                    (memory_id, knowledge_id, self_model_id, created_at)
                    VALUES (?, ?, ?, ?)
                """, (
                    memory_id,
                    knowledge_id,
                    self_model_id,
                    now
                ))
                
        except Exception as e:
            logger.warning(f"Error saving epistemic layer: {e}", exc_info=True)
            raise
    
    def get_version_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get version history of self-model.
        
        Args:
            limit: Optional limit on number of versions to return
            
        Returns:
            List of version dictionaries
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            query = """
                SELECT id, version, metadata, created_at, last_updated 
                FROM self_models 
                ORDER BY version DESC
            """
            if limit:
                query += f" LIMIT {limit}"
            
            cursor.execute(query)
            history = []
            
            for row in cursor.fetchall():
                metadata = json.loads(row["metadata"])
                history.append({
                    "version": row["version"],
                    "archived_at": row["last_updated"],
                    "model_id": row["id"]
                })
            
            return history
            
        finally:
            conn.close()
    
    def get_version(self, version: int) -> Optional[SelfModel]:
        """
        Get a specific version of the self-model from history.
        
        Args:
            version: Version number to retrieve
            
        Returns:
            SelfModel instance if found, None otherwise
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT * FROM self_models 
                WHERE version = ? 
                ORDER BY id DESC 
                LIMIT 1
            """, (version,))
            
            row = cursor.fetchone()
            if not row:
                logger.warning(f"Version {version} not found in SQLite")
                return None
            
            # Load model data (handle backward compatibility)
            # Check which columns exist (for migration from old schema)
            model_data = {
                "capabilities": json.loads(row["capabilities"]),
                "knowledge_boundaries": json.loads(row["knowledge_boundaries"]),
                "constraints": json.loads(row["constraints"]),
                "metadata": json.loads(row["metadata"]),
            }
            # Old schema had preferences and behavioral_patterns - ignore them if present
            # SelfModel.from_dict() will ignore them since they're no longer in the model
            
            # Load epistemic layer
            self_model_id = row["id"]
            epistemic_layer = self._load_epistemic_layer(cursor, self_model_id)
            model_data["epistemic_layer"] = epistemic_layer
            
            return SelfModel.from_dict(model_data)
            
        finally:
            conn.close()


def create_storage(storage_type: str = "sqlite", storage_path: Optional[str] = None) -> SelfModelSQLiteStorage:
    """
    Factory function to create storage backend.
    
    Now defaults to SQLite storage. JSON storage is deprecated.
    
    Args:
        storage_type: "sqlite" (default) or "json" (deprecated)
        storage_path: Path to storage file/database
        
    Returns:
        SelfModelSQLiteStorage instance (or SelfModelStorage if json type specified, but deprecated)
    """
    if storage_type == "json":
        import warnings
        warnings.warn(
            "JSON storage is deprecated. Use SQLite storage instead.",
            DeprecationWarning,
            stacklevel=2
        )
        path = storage_path or "self_model.json"
        return SelfModelStorage(storage_path=path)
    else:
        # Default to SQLite
        path = storage_path or "self_model.db"
        # Path resolution will be handled in SelfModelSQLiteStorage.__init__()
        storage = SelfModelSQLiteStorage(db_path=path)
        
        # Auto-migrate from JSON if JSON file exists and SQLite is empty
        json_path = Path(path).with_suffix('.json')
        if json_path.exists() and storage.load() is None:
            logger.info(f"Auto-migrating from {json_path} to {path}")
            try:
                from .migrate_to_sqlite import migrate_json_to_sqlite
                migrate_json_to_sqlite(
                    json_path=str(json_path),
                    sqlite_path=path,
                    backup_json=True
                )
                logger.info(f"Auto-migration completed successfully")
            except Exception as e:
                logger.warning(f"Auto-migration failed: {e}. Continuing with empty SQLite storage.")
        
        return storage

