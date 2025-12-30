"""
Relationship management for memory system.

Manages relationships between memories including linking, unlinking,
graph traversal, and auto-detection.
"""

from __future__ import annotations

import logging
from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime, timezone

from . import MemoryRecord, RelationshipRecord, RelationType
from .storage import MemoryStorage

logger = logging.getLogger(__name__)
from inspect import signature as _mutmut_signature
from typing import Annotated
from typing import Callable
from typing import ClassVar


MutantDict = Annotated[dict[str, Callable], "Mutant"]


def _mutmut_trampoline(orig, mutants, call_args, call_kwargs, self_arg = None):
    """Forward call to original or mutated function, depending on the environment"""
    import os
    mutant_under_test = os.environ['MUTANT_UNDER_TEST']
    if mutant_under_test == 'fail':
        from mutmut.__main__ import MutmutProgrammaticFailException
        raise MutmutProgrammaticFailException('Failed programmatically')      
    elif mutant_under_test == 'stats':
        from mutmut.__main__ import record_trampoline_hit
        record_trampoline_hit(orig.__module__ + '.' + orig.__name__)
        result = orig(*call_args, **call_kwargs)
        return result
    prefix = orig.__module__ + '.' + orig.__name__ + '__mutmut_'
    if not mutant_under_test.startswith(prefix):
        result = orig(*call_args, **call_kwargs)
        return result
    mutant_name = mutant_under_test.rpartition('.')[-1]
    if self_arg is not None:
        # call to a class method where self is not bound
        result = mutants[mutant_name](self_arg, *call_args, **call_kwargs)
    else:
        result = mutants[mutant_name](*call_args, **call_kwargs)
    return result


class RelationshipManager:
    """
    Manages relationships between memories.
    
    Provides methods for creating, querying, and managing typed relationships
    between memories, including auto-detection based on similarity, conflicts,
    and namespace hierarchy.
    """
    
    def xǁRelationshipManagerǁ__init____mutmut_orig(self, storage: MemoryStorage) -> None:
        """
        Initialize relationship manager.
        
        Args:
            storage: MemoryStorage instance
        """
        self.storage = storage
        
        # Initialize causal chain validator for CAUSES/CAUSED_BY relationships
        self.causal_validator = None
        try:
            from .causal_validator import CausalChainValidator
            self.causal_validator = CausalChainValidator(enable_z3=True)
        except Exception as e:
            logger.debug(f"Failed to initialize causal validator: {e}")
            self.causal_validator = None
        
        logger.info("Initialized RelationshipManager")
    
    def xǁRelationshipManagerǁ__init____mutmut_1(self, storage: MemoryStorage) -> None:
        """
        Initialize relationship manager.
        
        Args:
            storage: MemoryStorage instance
        """
        self.storage = None
        
        # Initialize causal chain validator for CAUSES/CAUSED_BY relationships
        self.causal_validator = None
        try:
            from .causal_validator import CausalChainValidator
            self.causal_validator = CausalChainValidator(enable_z3=True)
        except Exception as e:
            logger.debug(f"Failed to initialize causal validator: {e}")
            self.causal_validator = None
        
        logger.info("Initialized RelationshipManager")
    
    def xǁRelationshipManagerǁ__init____mutmut_2(self, storage: MemoryStorage) -> None:
        """
        Initialize relationship manager.
        
        Args:
            storage: MemoryStorage instance
        """
        self.storage = storage
        
        # Initialize causal chain validator for CAUSES/CAUSED_BY relationships
        self.causal_validator = ""
        try:
            from .causal_validator import CausalChainValidator
            self.causal_validator = CausalChainValidator(enable_z3=True)
        except Exception as e:
            logger.debug(f"Failed to initialize causal validator: {e}")
            self.causal_validator = None
        
        logger.info("Initialized RelationshipManager")
    
    def xǁRelationshipManagerǁ__init____mutmut_3(self, storage: MemoryStorage) -> None:
        """
        Initialize relationship manager.
        
        Args:
            storage: MemoryStorage instance
        """
        self.storage = storage
        
        # Initialize causal chain validator for CAUSES/CAUSED_BY relationships
        self.causal_validator = None
        try:
            from .causal_validator import CausalChainValidator
            self.causal_validator = None
        except Exception as e:
            logger.debug(f"Failed to initialize causal validator: {e}")
            self.causal_validator = None
        
        logger.info("Initialized RelationshipManager")
    
    def xǁRelationshipManagerǁ__init____mutmut_4(self, storage: MemoryStorage) -> None:
        """
        Initialize relationship manager.
        
        Args:
            storage: MemoryStorage instance
        """
        self.storage = storage
        
        # Initialize causal chain validator for CAUSES/CAUSED_BY relationships
        self.causal_validator = None
        try:
            from .causal_validator import CausalChainValidator
            self.causal_validator = CausalChainValidator(enable_z3=None)
        except Exception as e:
            logger.debug(f"Failed to initialize causal validator: {e}")
            self.causal_validator = None
        
        logger.info("Initialized RelationshipManager")
    
    def xǁRelationshipManagerǁ__init____mutmut_5(self, storage: MemoryStorage) -> None:
        """
        Initialize relationship manager.
        
        Args:
            storage: MemoryStorage instance
        """
        self.storage = storage
        
        # Initialize causal chain validator for CAUSES/CAUSED_BY relationships
        self.causal_validator = None
        try:
            from .causal_validator import CausalChainValidator
            self.causal_validator = CausalChainValidator(enable_z3=False)
        except Exception as e:
            logger.debug(f"Failed to initialize causal validator: {e}")
            self.causal_validator = None
        
        logger.info("Initialized RelationshipManager")
    
    def xǁRelationshipManagerǁ__init____mutmut_6(self, storage: MemoryStorage) -> None:
        """
        Initialize relationship manager.
        
        Args:
            storage: MemoryStorage instance
        """
        self.storage = storage
        
        # Initialize causal chain validator for CAUSES/CAUSED_BY relationships
        self.causal_validator = None
        try:
            from .causal_validator import CausalChainValidator
            self.causal_validator = CausalChainValidator(enable_z3=True)
        except Exception as e:
            logger.debug(None)
            self.causal_validator = None
        
        logger.info("Initialized RelationshipManager")
    
    def xǁRelationshipManagerǁ__init____mutmut_7(self, storage: MemoryStorage) -> None:
        """
        Initialize relationship manager.
        
        Args:
            storage: MemoryStorage instance
        """
        self.storage = storage
        
        # Initialize causal chain validator for CAUSES/CAUSED_BY relationships
        self.causal_validator = None
        try:
            from .causal_validator import CausalChainValidator
            self.causal_validator = CausalChainValidator(enable_z3=True)
        except Exception as e:
            logger.debug(f"Failed to initialize causal validator: {e}")
            self.causal_validator = ""
        
        logger.info("Initialized RelationshipManager")
    
    def xǁRelationshipManagerǁ__init____mutmut_8(self, storage: MemoryStorage) -> None:
        """
        Initialize relationship manager.
        
        Args:
            storage: MemoryStorage instance
        """
        self.storage = storage
        
        # Initialize causal chain validator for CAUSES/CAUSED_BY relationships
        self.causal_validator = None
        try:
            from .causal_validator import CausalChainValidator
            self.causal_validator = CausalChainValidator(enable_z3=True)
        except Exception as e:
            logger.debug(f"Failed to initialize causal validator: {e}")
            self.causal_validator = None
        
        logger.info(None)
    
    def xǁRelationshipManagerǁ__init____mutmut_9(self, storage: MemoryStorage) -> None:
        """
        Initialize relationship manager.
        
        Args:
            storage: MemoryStorage instance
        """
        self.storage = storage
        
        # Initialize causal chain validator for CAUSES/CAUSED_BY relationships
        self.causal_validator = None
        try:
            from .causal_validator import CausalChainValidator
            self.causal_validator = CausalChainValidator(enable_z3=True)
        except Exception as e:
            logger.debug(f"Failed to initialize causal validator: {e}")
            self.causal_validator = None
        
        logger.info("XXInitialized RelationshipManagerXX")
    
    def xǁRelationshipManagerǁ__init____mutmut_10(self, storage: MemoryStorage) -> None:
        """
        Initialize relationship manager.
        
        Args:
            storage: MemoryStorage instance
        """
        self.storage = storage
        
        # Initialize causal chain validator for CAUSES/CAUSED_BY relationships
        self.causal_validator = None
        try:
            from .causal_validator import CausalChainValidator
            self.causal_validator = CausalChainValidator(enable_z3=True)
        except Exception as e:
            logger.debug(f"Failed to initialize causal validator: {e}")
            self.causal_validator = None
        
        logger.info("initialized relationshipmanager")
    
    def xǁRelationshipManagerǁ__init____mutmut_11(self, storage: MemoryStorage) -> None:
        """
        Initialize relationship manager.
        
        Args:
            storage: MemoryStorage instance
        """
        self.storage = storage
        
        # Initialize causal chain validator for CAUSES/CAUSED_BY relationships
        self.causal_validator = None
        try:
            from .causal_validator import CausalChainValidator
            self.causal_validator = CausalChainValidator(enable_z3=True)
        except Exception as e:
            logger.debug(f"Failed to initialize causal validator: {e}")
            self.causal_validator = None
        
        logger.info("INITIALIZED RELATIONSHIPMANAGER")
    
    xǁRelationshipManagerǁ__init____mutmut_mutants : ClassVar[MutantDict] = {
    'xǁRelationshipManagerǁ__init____mutmut_1': xǁRelationshipManagerǁ__init____mutmut_1, 
        'xǁRelationshipManagerǁ__init____mutmut_2': xǁRelationshipManagerǁ__init____mutmut_2, 
        'xǁRelationshipManagerǁ__init____mutmut_3': xǁRelationshipManagerǁ__init____mutmut_3, 
        'xǁRelationshipManagerǁ__init____mutmut_4': xǁRelationshipManagerǁ__init____mutmut_4, 
        'xǁRelationshipManagerǁ__init____mutmut_5': xǁRelationshipManagerǁ__init____mutmut_5, 
        'xǁRelationshipManagerǁ__init____mutmut_6': xǁRelationshipManagerǁ__init____mutmut_6, 
        'xǁRelationshipManagerǁ__init____mutmut_7': xǁRelationshipManagerǁ__init____mutmut_7, 
        'xǁRelationshipManagerǁ__init____mutmut_8': xǁRelationshipManagerǁ__init____mutmut_8, 
        'xǁRelationshipManagerǁ__init____mutmut_9': xǁRelationshipManagerǁ__init____mutmut_9, 
        'xǁRelationshipManagerǁ__init____mutmut_10': xǁRelationshipManagerǁ__init____mutmut_10, 
        'xǁRelationshipManagerǁ__init____mutmut_11': xǁRelationshipManagerǁ__init____mutmut_11
    }
    
    def __init__(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁRelationshipManagerǁ__init____mutmut_orig"), object.__getattribute__(self, "xǁRelationshipManagerǁ__init____mutmut_mutants"), args, kwargs, self)
        return result 
    
    __init__.__signature__ = _mutmut_signature(xǁRelationshipManagerǁ__init____mutmut_orig)
    xǁRelationshipManagerǁ__init____mutmut_orig.__name__ = 'xǁRelationshipManagerǁ__init__'
    
    def xǁRelationshipManagerǁlink__mutmut_orig(
        self,
        source_id: int,
        target_id: int,
        relation_type: RelationType,
        strength: float = 1.0,
        bidirectional: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Create a relationship between two memories.
        
        Args:
            source_id: ID of source memory
            target_id: ID of target memory
            relation_type: Type of relationship
            strength: Relationship strength (0.0-1.0, default: 1.0)
            bidirectional: Whether relationship goes both ways (default: False)
            metadata: Optional additional context
            
        Returns:
            ID of the created relationship
        """
        if source_id == target_id:
            raise ValueError("Cannot create relationship from memory to itself")
        
        # Verify both memories exist
        source_memory = self.storage.get_memory(source_id)
        target_memory = self.storage.get_memory(target_id)
        
        if source_memory is None:
            raise ValueError(f"Source memory {source_id} not found")
        if target_memory is None:
            raise ValueError(f"Target memory {target_id} not found")
        
        # Avoid inserting duplicate relationships: check if identical relationship exists
        existing = self.storage.get_relationships(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type
        )
        if existing:
            # If an identical relationship exists, return its id (first match)
            logger.info(
                f"Relationship already exists {source_id} -> {target_id} ({relation_type.value}), skipping insert"
            )
            return existing[0].id

        # Validate causal relationships with Z3 before creating
        if relation_type in (RelationType.CAUSES, RelationType.CAUSED_BY) and self.causal_validator:
            try:
                # Get existing relationships for validation
                all_relationships = self.storage.get_relationships()
                existing_rels = [(r.source_id, r.target_id, r.relation_type) for r in all_relationships]
                
                # Get existing memories
                existing_memories = [source_memory, target_memory]
                
                is_valid, error = self.causal_validator.validate_single_causal_relationship(
                    source_id=source_id,
                    target_id=target_id,
                    existing_relationships=existing_rels,
                    existing_memories=existing_memories
                )
                
                if not is_valid:
                    logger.warning(f"Causal relationship validation failed: {error}")
                    # Still create the relationship but log the warning
                    # (non-blocking to allow manual override if needed)
                    
            except Exception as e:
                logger.error(f"Error in causal relationship validation: {e}", exc_info=True)
                # Continue with relationship creation even if validation fails

        # Create relationship record
        relationship = RelationshipRecord(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            strength=strength,
            bidirectional=bidirectional,
            metadata=metadata,
            created_at=datetime.now(timezone.utc)
        )
        
        # Store in database
        relationship_id = self.storage.store_relationship(relationship)
        
        logger.info(
            f"Linked memory {source_id} -> {target_id} "
            f"({relation_type.value}, strength={strength})"
        )
        
        return relationship_id
    
    def xǁRelationshipManagerǁlink__mutmut_1(
        self,
        source_id: int,
        target_id: int,
        relation_type: RelationType,
        strength: float = 2.0,
        bidirectional: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Create a relationship between two memories.
        
        Args:
            source_id: ID of source memory
            target_id: ID of target memory
            relation_type: Type of relationship
            strength: Relationship strength (0.0-1.0, default: 1.0)
            bidirectional: Whether relationship goes both ways (default: False)
            metadata: Optional additional context
            
        Returns:
            ID of the created relationship
        """
        if source_id == target_id:
            raise ValueError("Cannot create relationship from memory to itself")
        
        # Verify both memories exist
        source_memory = self.storage.get_memory(source_id)
        target_memory = self.storage.get_memory(target_id)
        
        if source_memory is None:
            raise ValueError(f"Source memory {source_id} not found")
        if target_memory is None:
            raise ValueError(f"Target memory {target_id} not found")
        
        # Avoid inserting duplicate relationships: check if identical relationship exists
        existing = self.storage.get_relationships(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type
        )
        if existing:
            # If an identical relationship exists, return its id (first match)
            logger.info(
                f"Relationship already exists {source_id} -> {target_id} ({relation_type.value}), skipping insert"
            )
            return existing[0].id

        # Validate causal relationships with Z3 before creating
        if relation_type in (RelationType.CAUSES, RelationType.CAUSED_BY) and self.causal_validator:
            try:
                # Get existing relationships for validation
                all_relationships = self.storage.get_relationships()
                existing_rels = [(r.source_id, r.target_id, r.relation_type) for r in all_relationships]
                
                # Get existing memories
                existing_memories = [source_memory, target_memory]
                
                is_valid, error = self.causal_validator.validate_single_causal_relationship(
                    source_id=source_id,
                    target_id=target_id,
                    existing_relationships=existing_rels,
                    existing_memories=existing_memories
                )
                
                if not is_valid:
                    logger.warning(f"Causal relationship validation failed: {error}")
                    # Still create the relationship but log the warning
                    # (non-blocking to allow manual override if needed)
                    
            except Exception as e:
                logger.error(f"Error in causal relationship validation: {e}", exc_info=True)
                # Continue with relationship creation even if validation fails

        # Create relationship record
        relationship = RelationshipRecord(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            strength=strength,
            bidirectional=bidirectional,
            metadata=metadata,
            created_at=datetime.now(timezone.utc)
        )
        
        # Store in database
        relationship_id = self.storage.store_relationship(relationship)
        
        logger.info(
            f"Linked memory {source_id} -> {target_id} "
            f"({relation_type.value}, strength={strength})"
        )
        
        return relationship_id
    
    def xǁRelationshipManagerǁlink__mutmut_2(
        self,
        source_id: int,
        target_id: int,
        relation_type: RelationType,
        strength: float = 1.0,
        bidirectional: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Create a relationship between two memories.
        
        Args:
            source_id: ID of source memory
            target_id: ID of target memory
            relation_type: Type of relationship
            strength: Relationship strength (0.0-1.0, default: 1.0)
            bidirectional: Whether relationship goes both ways (default: False)
            metadata: Optional additional context
            
        Returns:
            ID of the created relationship
        """
        if source_id == target_id:
            raise ValueError("Cannot create relationship from memory to itself")
        
        # Verify both memories exist
        source_memory = self.storage.get_memory(source_id)
        target_memory = self.storage.get_memory(target_id)
        
        if source_memory is None:
            raise ValueError(f"Source memory {source_id} not found")
        if target_memory is None:
            raise ValueError(f"Target memory {target_id} not found")
        
        # Avoid inserting duplicate relationships: check if identical relationship exists
        existing = self.storage.get_relationships(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type
        )
        if existing:
            # If an identical relationship exists, return its id (first match)
            logger.info(
                f"Relationship already exists {source_id} -> {target_id} ({relation_type.value}), skipping insert"
            )
            return existing[0].id

        # Validate causal relationships with Z3 before creating
        if relation_type in (RelationType.CAUSES, RelationType.CAUSED_BY) and self.causal_validator:
            try:
                # Get existing relationships for validation
                all_relationships = self.storage.get_relationships()
                existing_rels = [(r.source_id, r.target_id, r.relation_type) for r in all_relationships]
                
                # Get existing memories
                existing_memories = [source_memory, target_memory]
                
                is_valid, error = self.causal_validator.validate_single_causal_relationship(
                    source_id=source_id,
                    target_id=target_id,
                    existing_relationships=existing_rels,
                    existing_memories=existing_memories
                )
                
                if not is_valid:
                    logger.warning(f"Causal relationship validation failed: {error}")
                    # Still create the relationship but log the warning
                    # (non-blocking to allow manual override if needed)
                    
            except Exception as e:
                logger.error(f"Error in causal relationship validation: {e}", exc_info=True)
                # Continue with relationship creation even if validation fails

        # Create relationship record
        relationship = RelationshipRecord(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            strength=strength,
            bidirectional=bidirectional,
            metadata=metadata,
            created_at=datetime.now(timezone.utc)
        )
        
        # Store in database
        relationship_id = self.storage.store_relationship(relationship)
        
        logger.info(
            f"Linked memory {source_id} -> {target_id} "
            f"({relation_type.value}, strength={strength})"
        )
        
        return relationship_id
    
    def xǁRelationshipManagerǁlink__mutmut_3(
        self,
        source_id: int,
        target_id: int,
        relation_type: RelationType,
        strength: float = 1.0,
        bidirectional: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Create a relationship between two memories.
        
        Args:
            source_id: ID of source memory
            target_id: ID of target memory
            relation_type: Type of relationship
            strength: Relationship strength (0.0-1.0, default: 1.0)
            bidirectional: Whether relationship goes both ways (default: False)
            metadata: Optional additional context
            
        Returns:
            ID of the created relationship
        """
        if source_id != target_id:
            raise ValueError("Cannot create relationship from memory to itself")
        
        # Verify both memories exist
        source_memory = self.storage.get_memory(source_id)
        target_memory = self.storage.get_memory(target_id)
        
        if source_memory is None:
            raise ValueError(f"Source memory {source_id} not found")
        if target_memory is None:
            raise ValueError(f"Target memory {target_id} not found")
        
        # Avoid inserting duplicate relationships: check if identical relationship exists
        existing = self.storage.get_relationships(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type
        )
        if existing:
            # If an identical relationship exists, return its id (first match)
            logger.info(
                f"Relationship already exists {source_id} -> {target_id} ({relation_type.value}), skipping insert"
            )
            return existing[0].id

        # Validate causal relationships with Z3 before creating
        if relation_type in (RelationType.CAUSES, RelationType.CAUSED_BY) and self.causal_validator:
            try:
                # Get existing relationships for validation
                all_relationships = self.storage.get_relationships()
                existing_rels = [(r.source_id, r.target_id, r.relation_type) for r in all_relationships]
                
                # Get existing memories
                existing_memories = [source_memory, target_memory]
                
                is_valid, error = self.causal_validator.validate_single_causal_relationship(
                    source_id=source_id,
                    target_id=target_id,
                    existing_relationships=existing_rels,
                    existing_memories=existing_memories
                )
                
                if not is_valid:
                    logger.warning(f"Causal relationship validation failed: {error}")
                    # Still create the relationship but log the warning
                    # (non-blocking to allow manual override if needed)
                    
            except Exception as e:
                logger.error(f"Error in causal relationship validation: {e}", exc_info=True)
                # Continue with relationship creation even if validation fails

        # Create relationship record
        relationship = RelationshipRecord(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            strength=strength,
            bidirectional=bidirectional,
            metadata=metadata,
            created_at=datetime.now(timezone.utc)
        )
        
        # Store in database
        relationship_id = self.storage.store_relationship(relationship)
        
        logger.info(
            f"Linked memory {source_id} -> {target_id} "
            f"({relation_type.value}, strength={strength})"
        )
        
        return relationship_id
    
    def xǁRelationshipManagerǁlink__mutmut_4(
        self,
        source_id: int,
        target_id: int,
        relation_type: RelationType,
        strength: float = 1.0,
        bidirectional: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Create a relationship between two memories.
        
        Args:
            source_id: ID of source memory
            target_id: ID of target memory
            relation_type: Type of relationship
            strength: Relationship strength (0.0-1.0, default: 1.0)
            bidirectional: Whether relationship goes both ways (default: False)
            metadata: Optional additional context
            
        Returns:
            ID of the created relationship
        """
        if source_id == target_id:
            raise ValueError(None)
        
        # Verify both memories exist
        source_memory = self.storage.get_memory(source_id)
        target_memory = self.storage.get_memory(target_id)
        
        if source_memory is None:
            raise ValueError(f"Source memory {source_id} not found")
        if target_memory is None:
            raise ValueError(f"Target memory {target_id} not found")
        
        # Avoid inserting duplicate relationships: check if identical relationship exists
        existing = self.storage.get_relationships(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type
        )
        if existing:
            # If an identical relationship exists, return its id (first match)
            logger.info(
                f"Relationship already exists {source_id} -> {target_id} ({relation_type.value}), skipping insert"
            )
            return existing[0].id

        # Validate causal relationships with Z3 before creating
        if relation_type in (RelationType.CAUSES, RelationType.CAUSED_BY) and self.causal_validator:
            try:
                # Get existing relationships for validation
                all_relationships = self.storage.get_relationships()
                existing_rels = [(r.source_id, r.target_id, r.relation_type) for r in all_relationships]
                
                # Get existing memories
                existing_memories = [source_memory, target_memory]
                
                is_valid, error = self.causal_validator.validate_single_causal_relationship(
                    source_id=source_id,
                    target_id=target_id,
                    existing_relationships=existing_rels,
                    existing_memories=existing_memories
                )
                
                if not is_valid:
                    logger.warning(f"Causal relationship validation failed: {error}")
                    # Still create the relationship but log the warning
                    # (non-blocking to allow manual override if needed)
                    
            except Exception as e:
                logger.error(f"Error in causal relationship validation: {e}", exc_info=True)
                # Continue with relationship creation even if validation fails

        # Create relationship record
        relationship = RelationshipRecord(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            strength=strength,
            bidirectional=bidirectional,
            metadata=metadata,
            created_at=datetime.now(timezone.utc)
        )
        
        # Store in database
        relationship_id = self.storage.store_relationship(relationship)
        
        logger.info(
            f"Linked memory {source_id} -> {target_id} "
            f"({relation_type.value}, strength={strength})"
        )
        
        return relationship_id
    
    def xǁRelationshipManagerǁlink__mutmut_5(
        self,
        source_id: int,
        target_id: int,
        relation_type: RelationType,
        strength: float = 1.0,
        bidirectional: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Create a relationship between two memories.
        
        Args:
            source_id: ID of source memory
            target_id: ID of target memory
            relation_type: Type of relationship
            strength: Relationship strength (0.0-1.0, default: 1.0)
            bidirectional: Whether relationship goes both ways (default: False)
            metadata: Optional additional context
            
        Returns:
            ID of the created relationship
        """
        if source_id == target_id:
            raise ValueError("XXCannot create relationship from memory to itselfXX")
        
        # Verify both memories exist
        source_memory = self.storage.get_memory(source_id)
        target_memory = self.storage.get_memory(target_id)
        
        if source_memory is None:
            raise ValueError(f"Source memory {source_id} not found")
        if target_memory is None:
            raise ValueError(f"Target memory {target_id} not found")
        
        # Avoid inserting duplicate relationships: check if identical relationship exists
        existing = self.storage.get_relationships(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type
        )
        if existing:
            # If an identical relationship exists, return its id (first match)
            logger.info(
                f"Relationship already exists {source_id} -> {target_id} ({relation_type.value}), skipping insert"
            )
            return existing[0].id

        # Validate causal relationships with Z3 before creating
        if relation_type in (RelationType.CAUSES, RelationType.CAUSED_BY) and self.causal_validator:
            try:
                # Get existing relationships for validation
                all_relationships = self.storage.get_relationships()
                existing_rels = [(r.source_id, r.target_id, r.relation_type) for r in all_relationships]
                
                # Get existing memories
                existing_memories = [source_memory, target_memory]
                
                is_valid, error = self.causal_validator.validate_single_causal_relationship(
                    source_id=source_id,
                    target_id=target_id,
                    existing_relationships=existing_rels,
                    existing_memories=existing_memories
                )
                
                if not is_valid:
                    logger.warning(f"Causal relationship validation failed: {error}")
                    # Still create the relationship but log the warning
                    # (non-blocking to allow manual override if needed)
                    
            except Exception as e:
                logger.error(f"Error in causal relationship validation: {e}", exc_info=True)
                # Continue with relationship creation even if validation fails

        # Create relationship record
        relationship = RelationshipRecord(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            strength=strength,
            bidirectional=bidirectional,
            metadata=metadata,
            created_at=datetime.now(timezone.utc)
        )
        
        # Store in database
        relationship_id = self.storage.store_relationship(relationship)
        
        logger.info(
            f"Linked memory {source_id} -> {target_id} "
            f"({relation_type.value}, strength={strength})"
        )
        
        return relationship_id
    
    def xǁRelationshipManagerǁlink__mutmut_6(
        self,
        source_id: int,
        target_id: int,
        relation_type: RelationType,
        strength: float = 1.0,
        bidirectional: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Create a relationship between two memories.
        
        Args:
            source_id: ID of source memory
            target_id: ID of target memory
            relation_type: Type of relationship
            strength: Relationship strength (0.0-1.0, default: 1.0)
            bidirectional: Whether relationship goes both ways (default: False)
            metadata: Optional additional context
            
        Returns:
            ID of the created relationship
        """
        if source_id == target_id:
            raise ValueError("cannot create relationship from memory to itself")
        
        # Verify both memories exist
        source_memory = self.storage.get_memory(source_id)
        target_memory = self.storage.get_memory(target_id)
        
        if source_memory is None:
            raise ValueError(f"Source memory {source_id} not found")
        if target_memory is None:
            raise ValueError(f"Target memory {target_id} not found")
        
        # Avoid inserting duplicate relationships: check if identical relationship exists
        existing = self.storage.get_relationships(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type
        )
        if existing:
            # If an identical relationship exists, return its id (first match)
            logger.info(
                f"Relationship already exists {source_id} -> {target_id} ({relation_type.value}), skipping insert"
            )
            return existing[0].id

        # Validate causal relationships with Z3 before creating
        if relation_type in (RelationType.CAUSES, RelationType.CAUSED_BY) and self.causal_validator:
            try:
                # Get existing relationships for validation
                all_relationships = self.storage.get_relationships()
                existing_rels = [(r.source_id, r.target_id, r.relation_type) for r in all_relationships]
                
                # Get existing memories
                existing_memories = [source_memory, target_memory]
                
                is_valid, error = self.causal_validator.validate_single_causal_relationship(
                    source_id=source_id,
                    target_id=target_id,
                    existing_relationships=existing_rels,
                    existing_memories=existing_memories
                )
                
                if not is_valid:
                    logger.warning(f"Causal relationship validation failed: {error}")
                    # Still create the relationship but log the warning
                    # (non-blocking to allow manual override if needed)
                    
            except Exception as e:
                logger.error(f"Error in causal relationship validation: {e}", exc_info=True)
                # Continue with relationship creation even if validation fails

        # Create relationship record
        relationship = RelationshipRecord(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            strength=strength,
            bidirectional=bidirectional,
            metadata=metadata,
            created_at=datetime.now(timezone.utc)
        )
        
        # Store in database
        relationship_id = self.storage.store_relationship(relationship)
        
        logger.info(
            f"Linked memory {source_id} -> {target_id} "
            f"({relation_type.value}, strength={strength})"
        )
        
        return relationship_id
    
    def xǁRelationshipManagerǁlink__mutmut_7(
        self,
        source_id: int,
        target_id: int,
        relation_type: RelationType,
        strength: float = 1.0,
        bidirectional: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Create a relationship between two memories.
        
        Args:
            source_id: ID of source memory
            target_id: ID of target memory
            relation_type: Type of relationship
            strength: Relationship strength (0.0-1.0, default: 1.0)
            bidirectional: Whether relationship goes both ways (default: False)
            metadata: Optional additional context
            
        Returns:
            ID of the created relationship
        """
        if source_id == target_id:
            raise ValueError("CANNOT CREATE RELATIONSHIP FROM MEMORY TO ITSELF")
        
        # Verify both memories exist
        source_memory = self.storage.get_memory(source_id)
        target_memory = self.storage.get_memory(target_id)
        
        if source_memory is None:
            raise ValueError(f"Source memory {source_id} not found")
        if target_memory is None:
            raise ValueError(f"Target memory {target_id} not found")
        
        # Avoid inserting duplicate relationships: check if identical relationship exists
        existing = self.storage.get_relationships(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type
        )
        if existing:
            # If an identical relationship exists, return its id (first match)
            logger.info(
                f"Relationship already exists {source_id} -> {target_id} ({relation_type.value}), skipping insert"
            )
            return existing[0].id

        # Validate causal relationships with Z3 before creating
        if relation_type in (RelationType.CAUSES, RelationType.CAUSED_BY) and self.causal_validator:
            try:
                # Get existing relationships for validation
                all_relationships = self.storage.get_relationships()
                existing_rels = [(r.source_id, r.target_id, r.relation_type) for r in all_relationships]
                
                # Get existing memories
                existing_memories = [source_memory, target_memory]
                
                is_valid, error = self.causal_validator.validate_single_causal_relationship(
                    source_id=source_id,
                    target_id=target_id,
                    existing_relationships=existing_rels,
                    existing_memories=existing_memories
                )
                
                if not is_valid:
                    logger.warning(f"Causal relationship validation failed: {error}")
                    # Still create the relationship but log the warning
                    # (non-blocking to allow manual override if needed)
                    
            except Exception as e:
                logger.error(f"Error in causal relationship validation: {e}", exc_info=True)
                # Continue with relationship creation even if validation fails

        # Create relationship record
        relationship = RelationshipRecord(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            strength=strength,
            bidirectional=bidirectional,
            metadata=metadata,
            created_at=datetime.now(timezone.utc)
        )
        
        # Store in database
        relationship_id = self.storage.store_relationship(relationship)
        
        logger.info(
            f"Linked memory {source_id} -> {target_id} "
            f"({relation_type.value}, strength={strength})"
        )
        
        return relationship_id
    
    def xǁRelationshipManagerǁlink__mutmut_8(
        self,
        source_id: int,
        target_id: int,
        relation_type: RelationType,
        strength: float = 1.0,
        bidirectional: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Create a relationship between two memories.
        
        Args:
            source_id: ID of source memory
            target_id: ID of target memory
            relation_type: Type of relationship
            strength: Relationship strength (0.0-1.0, default: 1.0)
            bidirectional: Whether relationship goes both ways (default: False)
            metadata: Optional additional context
            
        Returns:
            ID of the created relationship
        """
        if source_id == target_id:
            raise ValueError("Cannot create relationship from memory to itself")
        
        # Verify both memories exist
        source_memory = None
        target_memory = self.storage.get_memory(target_id)
        
        if source_memory is None:
            raise ValueError(f"Source memory {source_id} not found")
        if target_memory is None:
            raise ValueError(f"Target memory {target_id} not found")
        
        # Avoid inserting duplicate relationships: check if identical relationship exists
        existing = self.storage.get_relationships(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type
        )
        if existing:
            # If an identical relationship exists, return its id (first match)
            logger.info(
                f"Relationship already exists {source_id} -> {target_id} ({relation_type.value}), skipping insert"
            )
            return existing[0].id

        # Validate causal relationships with Z3 before creating
        if relation_type in (RelationType.CAUSES, RelationType.CAUSED_BY) and self.causal_validator:
            try:
                # Get existing relationships for validation
                all_relationships = self.storage.get_relationships()
                existing_rels = [(r.source_id, r.target_id, r.relation_type) for r in all_relationships]
                
                # Get existing memories
                existing_memories = [source_memory, target_memory]
                
                is_valid, error = self.causal_validator.validate_single_causal_relationship(
                    source_id=source_id,
                    target_id=target_id,
                    existing_relationships=existing_rels,
                    existing_memories=existing_memories
                )
                
                if not is_valid:
                    logger.warning(f"Causal relationship validation failed: {error}")
                    # Still create the relationship but log the warning
                    # (non-blocking to allow manual override if needed)
                    
            except Exception as e:
                logger.error(f"Error in causal relationship validation: {e}", exc_info=True)
                # Continue with relationship creation even if validation fails

        # Create relationship record
        relationship = RelationshipRecord(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            strength=strength,
            bidirectional=bidirectional,
            metadata=metadata,
            created_at=datetime.now(timezone.utc)
        )
        
        # Store in database
        relationship_id = self.storage.store_relationship(relationship)
        
        logger.info(
            f"Linked memory {source_id} -> {target_id} "
            f"({relation_type.value}, strength={strength})"
        )
        
        return relationship_id
    
    def xǁRelationshipManagerǁlink__mutmut_9(
        self,
        source_id: int,
        target_id: int,
        relation_type: RelationType,
        strength: float = 1.0,
        bidirectional: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Create a relationship between two memories.
        
        Args:
            source_id: ID of source memory
            target_id: ID of target memory
            relation_type: Type of relationship
            strength: Relationship strength (0.0-1.0, default: 1.0)
            bidirectional: Whether relationship goes both ways (default: False)
            metadata: Optional additional context
            
        Returns:
            ID of the created relationship
        """
        if source_id == target_id:
            raise ValueError("Cannot create relationship from memory to itself")
        
        # Verify both memories exist
        source_memory = self.storage.get_memory(None)
        target_memory = self.storage.get_memory(target_id)
        
        if source_memory is None:
            raise ValueError(f"Source memory {source_id} not found")
        if target_memory is None:
            raise ValueError(f"Target memory {target_id} not found")
        
        # Avoid inserting duplicate relationships: check if identical relationship exists
        existing = self.storage.get_relationships(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type
        )
        if existing:
            # If an identical relationship exists, return its id (first match)
            logger.info(
                f"Relationship already exists {source_id} -> {target_id} ({relation_type.value}), skipping insert"
            )
            return existing[0].id

        # Validate causal relationships with Z3 before creating
        if relation_type in (RelationType.CAUSES, RelationType.CAUSED_BY) and self.causal_validator:
            try:
                # Get existing relationships for validation
                all_relationships = self.storage.get_relationships()
                existing_rels = [(r.source_id, r.target_id, r.relation_type) for r in all_relationships]
                
                # Get existing memories
                existing_memories = [source_memory, target_memory]
                
                is_valid, error = self.causal_validator.validate_single_causal_relationship(
                    source_id=source_id,
                    target_id=target_id,
                    existing_relationships=existing_rels,
                    existing_memories=existing_memories
                )
                
                if not is_valid:
                    logger.warning(f"Causal relationship validation failed: {error}")
                    # Still create the relationship but log the warning
                    # (non-blocking to allow manual override if needed)
                    
            except Exception as e:
                logger.error(f"Error in causal relationship validation: {e}", exc_info=True)
                # Continue with relationship creation even if validation fails

        # Create relationship record
        relationship = RelationshipRecord(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            strength=strength,
            bidirectional=bidirectional,
            metadata=metadata,
            created_at=datetime.now(timezone.utc)
        )
        
        # Store in database
        relationship_id = self.storage.store_relationship(relationship)
        
        logger.info(
            f"Linked memory {source_id} -> {target_id} "
            f"({relation_type.value}, strength={strength})"
        )
        
        return relationship_id
    
    def xǁRelationshipManagerǁlink__mutmut_10(
        self,
        source_id: int,
        target_id: int,
        relation_type: RelationType,
        strength: float = 1.0,
        bidirectional: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Create a relationship between two memories.
        
        Args:
            source_id: ID of source memory
            target_id: ID of target memory
            relation_type: Type of relationship
            strength: Relationship strength (0.0-1.0, default: 1.0)
            bidirectional: Whether relationship goes both ways (default: False)
            metadata: Optional additional context
            
        Returns:
            ID of the created relationship
        """
        if source_id == target_id:
            raise ValueError("Cannot create relationship from memory to itself")
        
        # Verify both memories exist
        source_memory = self.storage.get_memory(source_id)
        target_memory = None
        
        if source_memory is None:
            raise ValueError(f"Source memory {source_id} not found")
        if target_memory is None:
            raise ValueError(f"Target memory {target_id} not found")
        
        # Avoid inserting duplicate relationships: check if identical relationship exists
        existing = self.storage.get_relationships(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type
        )
        if existing:
            # If an identical relationship exists, return its id (first match)
            logger.info(
                f"Relationship already exists {source_id} -> {target_id} ({relation_type.value}), skipping insert"
            )
            return existing[0].id

        # Validate causal relationships with Z3 before creating
        if relation_type in (RelationType.CAUSES, RelationType.CAUSED_BY) and self.causal_validator:
            try:
                # Get existing relationships for validation
                all_relationships = self.storage.get_relationships()
                existing_rels = [(r.source_id, r.target_id, r.relation_type) for r in all_relationships]
                
                # Get existing memories
                existing_memories = [source_memory, target_memory]
                
                is_valid, error = self.causal_validator.validate_single_causal_relationship(
                    source_id=source_id,
                    target_id=target_id,
                    existing_relationships=existing_rels,
                    existing_memories=existing_memories
                )
                
                if not is_valid:
                    logger.warning(f"Causal relationship validation failed: {error}")
                    # Still create the relationship but log the warning
                    # (non-blocking to allow manual override if needed)
                    
            except Exception as e:
                logger.error(f"Error in causal relationship validation: {e}", exc_info=True)
                # Continue with relationship creation even if validation fails

        # Create relationship record
        relationship = RelationshipRecord(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            strength=strength,
            bidirectional=bidirectional,
            metadata=metadata,
            created_at=datetime.now(timezone.utc)
        )
        
        # Store in database
        relationship_id = self.storage.store_relationship(relationship)
        
        logger.info(
            f"Linked memory {source_id} -> {target_id} "
            f"({relation_type.value}, strength={strength})"
        )
        
        return relationship_id
    
    def xǁRelationshipManagerǁlink__mutmut_11(
        self,
        source_id: int,
        target_id: int,
        relation_type: RelationType,
        strength: float = 1.0,
        bidirectional: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Create a relationship between two memories.
        
        Args:
            source_id: ID of source memory
            target_id: ID of target memory
            relation_type: Type of relationship
            strength: Relationship strength (0.0-1.0, default: 1.0)
            bidirectional: Whether relationship goes both ways (default: False)
            metadata: Optional additional context
            
        Returns:
            ID of the created relationship
        """
        if source_id == target_id:
            raise ValueError("Cannot create relationship from memory to itself")
        
        # Verify both memories exist
        source_memory = self.storage.get_memory(source_id)
        target_memory = self.storage.get_memory(None)
        
        if source_memory is None:
            raise ValueError(f"Source memory {source_id} not found")
        if target_memory is None:
            raise ValueError(f"Target memory {target_id} not found")
        
        # Avoid inserting duplicate relationships: check if identical relationship exists
        existing = self.storage.get_relationships(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type
        )
        if existing:
            # If an identical relationship exists, return its id (first match)
            logger.info(
                f"Relationship already exists {source_id} -> {target_id} ({relation_type.value}), skipping insert"
            )
            return existing[0].id

        # Validate causal relationships with Z3 before creating
        if relation_type in (RelationType.CAUSES, RelationType.CAUSED_BY) and self.causal_validator:
            try:
                # Get existing relationships for validation
                all_relationships = self.storage.get_relationships()
                existing_rels = [(r.source_id, r.target_id, r.relation_type) for r in all_relationships]
                
                # Get existing memories
                existing_memories = [source_memory, target_memory]
                
                is_valid, error = self.causal_validator.validate_single_causal_relationship(
                    source_id=source_id,
                    target_id=target_id,
                    existing_relationships=existing_rels,
                    existing_memories=existing_memories
                )
                
                if not is_valid:
                    logger.warning(f"Causal relationship validation failed: {error}")
                    # Still create the relationship but log the warning
                    # (non-blocking to allow manual override if needed)
                    
            except Exception as e:
                logger.error(f"Error in causal relationship validation: {e}", exc_info=True)
                # Continue with relationship creation even if validation fails

        # Create relationship record
        relationship = RelationshipRecord(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            strength=strength,
            bidirectional=bidirectional,
            metadata=metadata,
            created_at=datetime.now(timezone.utc)
        )
        
        # Store in database
        relationship_id = self.storage.store_relationship(relationship)
        
        logger.info(
            f"Linked memory {source_id} -> {target_id} "
            f"({relation_type.value}, strength={strength})"
        )
        
        return relationship_id
    
    def xǁRelationshipManagerǁlink__mutmut_12(
        self,
        source_id: int,
        target_id: int,
        relation_type: RelationType,
        strength: float = 1.0,
        bidirectional: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Create a relationship between two memories.
        
        Args:
            source_id: ID of source memory
            target_id: ID of target memory
            relation_type: Type of relationship
            strength: Relationship strength (0.0-1.0, default: 1.0)
            bidirectional: Whether relationship goes both ways (default: False)
            metadata: Optional additional context
            
        Returns:
            ID of the created relationship
        """
        if source_id == target_id:
            raise ValueError("Cannot create relationship from memory to itself")
        
        # Verify both memories exist
        source_memory = self.storage.get_memory(source_id)
        target_memory = self.storage.get_memory(target_id)
        
        if source_memory is not None:
            raise ValueError(f"Source memory {source_id} not found")
        if target_memory is None:
            raise ValueError(f"Target memory {target_id} not found")
        
        # Avoid inserting duplicate relationships: check if identical relationship exists
        existing = self.storage.get_relationships(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type
        )
        if existing:
            # If an identical relationship exists, return its id (first match)
            logger.info(
                f"Relationship already exists {source_id} -> {target_id} ({relation_type.value}), skipping insert"
            )
            return existing[0].id

        # Validate causal relationships with Z3 before creating
        if relation_type in (RelationType.CAUSES, RelationType.CAUSED_BY) and self.causal_validator:
            try:
                # Get existing relationships for validation
                all_relationships = self.storage.get_relationships()
                existing_rels = [(r.source_id, r.target_id, r.relation_type) for r in all_relationships]
                
                # Get existing memories
                existing_memories = [source_memory, target_memory]
                
                is_valid, error = self.causal_validator.validate_single_causal_relationship(
                    source_id=source_id,
                    target_id=target_id,
                    existing_relationships=existing_rels,
                    existing_memories=existing_memories
                )
                
                if not is_valid:
                    logger.warning(f"Causal relationship validation failed: {error}")
                    # Still create the relationship but log the warning
                    # (non-blocking to allow manual override if needed)
                    
            except Exception as e:
                logger.error(f"Error in causal relationship validation: {e}", exc_info=True)
                # Continue with relationship creation even if validation fails

        # Create relationship record
        relationship = RelationshipRecord(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            strength=strength,
            bidirectional=bidirectional,
            metadata=metadata,
            created_at=datetime.now(timezone.utc)
        )
        
        # Store in database
        relationship_id = self.storage.store_relationship(relationship)
        
        logger.info(
            f"Linked memory {source_id} -> {target_id} "
            f"({relation_type.value}, strength={strength})"
        )
        
        return relationship_id
    
    def xǁRelationshipManagerǁlink__mutmut_13(
        self,
        source_id: int,
        target_id: int,
        relation_type: RelationType,
        strength: float = 1.0,
        bidirectional: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Create a relationship between two memories.
        
        Args:
            source_id: ID of source memory
            target_id: ID of target memory
            relation_type: Type of relationship
            strength: Relationship strength (0.0-1.0, default: 1.0)
            bidirectional: Whether relationship goes both ways (default: False)
            metadata: Optional additional context
            
        Returns:
            ID of the created relationship
        """
        if source_id == target_id:
            raise ValueError("Cannot create relationship from memory to itself")
        
        # Verify both memories exist
        source_memory = self.storage.get_memory(source_id)
        target_memory = self.storage.get_memory(target_id)
        
        if source_memory is None:
            raise ValueError(None)
        if target_memory is None:
            raise ValueError(f"Target memory {target_id} not found")
        
        # Avoid inserting duplicate relationships: check if identical relationship exists
        existing = self.storage.get_relationships(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type
        )
        if existing:
            # If an identical relationship exists, return its id (first match)
            logger.info(
                f"Relationship already exists {source_id} -> {target_id} ({relation_type.value}), skipping insert"
            )
            return existing[0].id

        # Validate causal relationships with Z3 before creating
        if relation_type in (RelationType.CAUSES, RelationType.CAUSED_BY) and self.causal_validator:
            try:
                # Get existing relationships for validation
                all_relationships = self.storage.get_relationships()
                existing_rels = [(r.source_id, r.target_id, r.relation_type) for r in all_relationships]
                
                # Get existing memories
                existing_memories = [source_memory, target_memory]
                
                is_valid, error = self.causal_validator.validate_single_causal_relationship(
                    source_id=source_id,
                    target_id=target_id,
                    existing_relationships=existing_rels,
                    existing_memories=existing_memories
                )
                
                if not is_valid:
                    logger.warning(f"Causal relationship validation failed: {error}")
                    # Still create the relationship but log the warning
                    # (non-blocking to allow manual override if needed)
                    
            except Exception as e:
                logger.error(f"Error in causal relationship validation: {e}", exc_info=True)
                # Continue with relationship creation even if validation fails

        # Create relationship record
        relationship = RelationshipRecord(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            strength=strength,
            bidirectional=bidirectional,
            metadata=metadata,
            created_at=datetime.now(timezone.utc)
        )
        
        # Store in database
        relationship_id = self.storage.store_relationship(relationship)
        
        logger.info(
            f"Linked memory {source_id} -> {target_id} "
            f"({relation_type.value}, strength={strength})"
        )
        
        return relationship_id
    
    def xǁRelationshipManagerǁlink__mutmut_14(
        self,
        source_id: int,
        target_id: int,
        relation_type: RelationType,
        strength: float = 1.0,
        bidirectional: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Create a relationship between two memories.
        
        Args:
            source_id: ID of source memory
            target_id: ID of target memory
            relation_type: Type of relationship
            strength: Relationship strength (0.0-1.0, default: 1.0)
            bidirectional: Whether relationship goes both ways (default: False)
            metadata: Optional additional context
            
        Returns:
            ID of the created relationship
        """
        if source_id == target_id:
            raise ValueError("Cannot create relationship from memory to itself")
        
        # Verify both memories exist
        source_memory = self.storage.get_memory(source_id)
        target_memory = self.storage.get_memory(target_id)
        
        if source_memory is None:
            raise ValueError(f"Source memory {source_id} not found")
        if target_memory is not None:
            raise ValueError(f"Target memory {target_id} not found")
        
        # Avoid inserting duplicate relationships: check if identical relationship exists
        existing = self.storage.get_relationships(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type
        )
        if existing:
            # If an identical relationship exists, return its id (first match)
            logger.info(
                f"Relationship already exists {source_id} -> {target_id} ({relation_type.value}), skipping insert"
            )
            return existing[0].id

        # Validate causal relationships with Z3 before creating
        if relation_type in (RelationType.CAUSES, RelationType.CAUSED_BY) and self.causal_validator:
            try:
                # Get existing relationships for validation
                all_relationships = self.storage.get_relationships()
                existing_rels = [(r.source_id, r.target_id, r.relation_type) for r in all_relationships]
                
                # Get existing memories
                existing_memories = [source_memory, target_memory]
                
                is_valid, error = self.causal_validator.validate_single_causal_relationship(
                    source_id=source_id,
                    target_id=target_id,
                    existing_relationships=existing_rels,
                    existing_memories=existing_memories
                )
                
                if not is_valid:
                    logger.warning(f"Causal relationship validation failed: {error}")
                    # Still create the relationship but log the warning
                    # (non-blocking to allow manual override if needed)
                    
            except Exception as e:
                logger.error(f"Error in causal relationship validation: {e}", exc_info=True)
                # Continue with relationship creation even if validation fails

        # Create relationship record
        relationship = RelationshipRecord(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            strength=strength,
            bidirectional=bidirectional,
            metadata=metadata,
            created_at=datetime.now(timezone.utc)
        )
        
        # Store in database
        relationship_id = self.storage.store_relationship(relationship)
        
        logger.info(
            f"Linked memory {source_id} -> {target_id} "
            f"({relation_type.value}, strength={strength})"
        )
        
        return relationship_id
    
    def xǁRelationshipManagerǁlink__mutmut_15(
        self,
        source_id: int,
        target_id: int,
        relation_type: RelationType,
        strength: float = 1.0,
        bidirectional: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Create a relationship between two memories.
        
        Args:
            source_id: ID of source memory
            target_id: ID of target memory
            relation_type: Type of relationship
            strength: Relationship strength (0.0-1.0, default: 1.0)
            bidirectional: Whether relationship goes both ways (default: False)
            metadata: Optional additional context
            
        Returns:
            ID of the created relationship
        """
        if source_id == target_id:
            raise ValueError("Cannot create relationship from memory to itself")
        
        # Verify both memories exist
        source_memory = self.storage.get_memory(source_id)
        target_memory = self.storage.get_memory(target_id)
        
        if source_memory is None:
            raise ValueError(f"Source memory {source_id} not found")
        if target_memory is None:
            raise ValueError(None)
        
        # Avoid inserting duplicate relationships: check if identical relationship exists
        existing = self.storage.get_relationships(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type
        )
        if existing:
            # If an identical relationship exists, return its id (first match)
            logger.info(
                f"Relationship already exists {source_id} -> {target_id} ({relation_type.value}), skipping insert"
            )
            return existing[0].id

        # Validate causal relationships with Z3 before creating
        if relation_type in (RelationType.CAUSES, RelationType.CAUSED_BY) and self.causal_validator:
            try:
                # Get existing relationships for validation
                all_relationships = self.storage.get_relationships()
                existing_rels = [(r.source_id, r.target_id, r.relation_type) for r in all_relationships]
                
                # Get existing memories
                existing_memories = [source_memory, target_memory]
                
                is_valid, error = self.causal_validator.validate_single_causal_relationship(
                    source_id=source_id,
                    target_id=target_id,
                    existing_relationships=existing_rels,
                    existing_memories=existing_memories
                )
                
                if not is_valid:
                    logger.warning(f"Causal relationship validation failed: {error}")
                    # Still create the relationship but log the warning
                    # (non-blocking to allow manual override if needed)
                    
            except Exception as e:
                logger.error(f"Error in causal relationship validation: {e}", exc_info=True)
                # Continue with relationship creation even if validation fails

        # Create relationship record
        relationship = RelationshipRecord(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            strength=strength,
            bidirectional=bidirectional,
            metadata=metadata,
            created_at=datetime.now(timezone.utc)
        )
        
        # Store in database
        relationship_id = self.storage.store_relationship(relationship)
        
        logger.info(
            f"Linked memory {source_id} -> {target_id} "
            f"({relation_type.value}, strength={strength})"
        )
        
        return relationship_id
    
    def xǁRelationshipManagerǁlink__mutmut_16(
        self,
        source_id: int,
        target_id: int,
        relation_type: RelationType,
        strength: float = 1.0,
        bidirectional: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Create a relationship between two memories.
        
        Args:
            source_id: ID of source memory
            target_id: ID of target memory
            relation_type: Type of relationship
            strength: Relationship strength (0.0-1.0, default: 1.0)
            bidirectional: Whether relationship goes both ways (default: False)
            metadata: Optional additional context
            
        Returns:
            ID of the created relationship
        """
        if source_id == target_id:
            raise ValueError("Cannot create relationship from memory to itself")
        
        # Verify both memories exist
        source_memory = self.storage.get_memory(source_id)
        target_memory = self.storage.get_memory(target_id)
        
        if source_memory is None:
            raise ValueError(f"Source memory {source_id} not found")
        if target_memory is None:
            raise ValueError(f"Target memory {target_id} not found")
        
        # Avoid inserting duplicate relationships: check if identical relationship exists
        existing = None
        if existing:
            # If an identical relationship exists, return its id (first match)
            logger.info(
                f"Relationship already exists {source_id} -> {target_id} ({relation_type.value}), skipping insert"
            )
            return existing[0].id

        # Validate causal relationships with Z3 before creating
        if relation_type in (RelationType.CAUSES, RelationType.CAUSED_BY) and self.causal_validator:
            try:
                # Get existing relationships for validation
                all_relationships = self.storage.get_relationships()
                existing_rels = [(r.source_id, r.target_id, r.relation_type) for r in all_relationships]
                
                # Get existing memories
                existing_memories = [source_memory, target_memory]
                
                is_valid, error = self.causal_validator.validate_single_causal_relationship(
                    source_id=source_id,
                    target_id=target_id,
                    existing_relationships=existing_rels,
                    existing_memories=existing_memories
                )
                
                if not is_valid:
                    logger.warning(f"Causal relationship validation failed: {error}")
                    # Still create the relationship but log the warning
                    # (non-blocking to allow manual override if needed)
                    
            except Exception as e:
                logger.error(f"Error in causal relationship validation: {e}", exc_info=True)
                # Continue with relationship creation even if validation fails

        # Create relationship record
        relationship = RelationshipRecord(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            strength=strength,
            bidirectional=bidirectional,
            metadata=metadata,
            created_at=datetime.now(timezone.utc)
        )
        
        # Store in database
        relationship_id = self.storage.store_relationship(relationship)
        
        logger.info(
            f"Linked memory {source_id} -> {target_id} "
            f"({relation_type.value}, strength={strength})"
        )
        
        return relationship_id
    
    def xǁRelationshipManagerǁlink__mutmut_17(
        self,
        source_id: int,
        target_id: int,
        relation_type: RelationType,
        strength: float = 1.0,
        bidirectional: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Create a relationship between two memories.
        
        Args:
            source_id: ID of source memory
            target_id: ID of target memory
            relation_type: Type of relationship
            strength: Relationship strength (0.0-1.0, default: 1.0)
            bidirectional: Whether relationship goes both ways (default: False)
            metadata: Optional additional context
            
        Returns:
            ID of the created relationship
        """
        if source_id == target_id:
            raise ValueError("Cannot create relationship from memory to itself")
        
        # Verify both memories exist
        source_memory = self.storage.get_memory(source_id)
        target_memory = self.storage.get_memory(target_id)
        
        if source_memory is None:
            raise ValueError(f"Source memory {source_id} not found")
        if target_memory is None:
            raise ValueError(f"Target memory {target_id} not found")
        
        # Avoid inserting duplicate relationships: check if identical relationship exists
        existing = self.storage.get_relationships(
            source_id=None,
            target_id=target_id,
            relation_type=relation_type
        )
        if existing:
            # If an identical relationship exists, return its id (first match)
            logger.info(
                f"Relationship already exists {source_id} -> {target_id} ({relation_type.value}), skipping insert"
            )
            return existing[0].id

        # Validate causal relationships with Z3 before creating
        if relation_type in (RelationType.CAUSES, RelationType.CAUSED_BY) and self.causal_validator:
            try:
                # Get existing relationships for validation
                all_relationships = self.storage.get_relationships()
                existing_rels = [(r.source_id, r.target_id, r.relation_type) for r in all_relationships]
                
                # Get existing memories
                existing_memories = [source_memory, target_memory]
                
                is_valid, error = self.causal_validator.validate_single_causal_relationship(
                    source_id=source_id,
                    target_id=target_id,
                    existing_relationships=existing_rels,
                    existing_memories=existing_memories
                )
                
                if not is_valid:
                    logger.warning(f"Causal relationship validation failed: {error}")
                    # Still create the relationship but log the warning
                    # (non-blocking to allow manual override if needed)
                    
            except Exception as e:
                logger.error(f"Error in causal relationship validation: {e}", exc_info=True)
                # Continue with relationship creation even if validation fails

        # Create relationship record
        relationship = RelationshipRecord(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            strength=strength,
            bidirectional=bidirectional,
            metadata=metadata,
            created_at=datetime.now(timezone.utc)
        )
        
        # Store in database
        relationship_id = self.storage.store_relationship(relationship)
        
        logger.info(
            f"Linked memory {source_id} -> {target_id} "
            f"({relation_type.value}, strength={strength})"
        )
        
        return relationship_id
    
    def xǁRelationshipManagerǁlink__mutmut_18(
        self,
        source_id: int,
        target_id: int,
        relation_type: RelationType,
        strength: float = 1.0,
        bidirectional: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Create a relationship between two memories.
        
        Args:
            source_id: ID of source memory
            target_id: ID of target memory
            relation_type: Type of relationship
            strength: Relationship strength (0.0-1.0, default: 1.0)
            bidirectional: Whether relationship goes both ways (default: False)
            metadata: Optional additional context
            
        Returns:
            ID of the created relationship
        """
        if source_id == target_id:
            raise ValueError("Cannot create relationship from memory to itself")
        
        # Verify both memories exist
        source_memory = self.storage.get_memory(source_id)
        target_memory = self.storage.get_memory(target_id)
        
        if source_memory is None:
            raise ValueError(f"Source memory {source_id} not found")
        if target_memory is None:
            raise ValueError(f"Target memory {target_id} not found")
        
        # Avoid inserting duplicate relationships: check if identical relationship exists
        existing = self.storage.get_relationships(
            source_id=source_id,
            target_id=None,
            relation_type=relation_type
        )
        if existing:
            # If an identical relationship exists, return its id (first match)
            logger.info(
                f"Relationship already exists {source_id} -> {target_id} ({relation_type.value}), skipping insert"
            )
            return existing[0].id

        # Validate causal relationships with Z3 before creating
        if relation_type in (RelationType.CAUSES, RelationType.CAUSED_BY) and self.causal_validator:
            try:
                # Get existing relationships for validation
                all_relationships = self.storage.get_relationships()
                existing_rels = [(r.source_id, r.target_id, r.relation_type) for r in all_relationships]
                
                # Get existing memories
                existing_memories = [source_memory, target_memory]
                
                is_valid, error = self.causal_validator.validate_single_causal_relationship(
                    source_id=source_id,
                    target_id=target_id,
                    existing_relationships=existing_rels,
                    existing_memories=existing_memories
                )
                
                if not is_valid:
                    logger.warning(f"Causal relationship validation failed: {error}")
                    # Still create the relationship but log the warning
                    # (non-blocking to allow manual override if needed)
                    
            except Exception as e:
                logger.error(f"Error in causal relationship validation: {e}", exc_info=True)
                # Continue with relationship creation even if validation fails

        # Create relationship record
        relationship = RelationshipRecord(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            strength=strength,
            bidirectional=bidirectional,
            metadata=metadata,
            created_at=datetime.now(timezone.utc)
        )
        
        # Store in database
        relationship_id = self.storage.store_relationship(relationship)
        
        logger.info(
            f"Linked memory {source_id} -> {target_id} "
            f"({relation_type.value}, strength={strength})"
        )
        
        return relationship_id
    
    def xǁRelationshipManagerǁlink__mutmut_19(
        self,
        source_id: int,
        target_id: int,
        relation_type: RelationType,
        strength: float = 1.0,
        bidirectional: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Create a relationship between two memories.
        
        Args:
            source_id: ID of source memory
            target_id: ID of target memory
            relation_type: Type of relationship
            strength: Relationship strength (0.0-1.0, default: 1.0)
            bidirectional: Whether relationship goes both ways (default: False)
            metadata: Optional additional context
            
        Returns:
            ID of the created relationship
        """
        if source_id == target_id:
            raise ValueError("Cannot create relationship from memory to itself")
        
        # Verify both memories exist
        source_memory = self.storage.get_memory(source_id)
        target_memory = self.storage.get_memory(target_id)
        
        if source_memory is None:
            raise ValueError(f"Source memory {source_id} not found")
        if target_memory is None:
            raise ValueError(f"Target memory {target_id} not found")
        
        # Avoid inserting duplicate relationships: check if identical relationship exists
        existing = self.storage.get_relationships(
            source_id=source_id,
            target_id=target_id,
            relation_type=None
        )
        if existing:
            # If an identical relationship exists, return its id (first match)
            logger.info(
                f"Relationship already exists {source_id} -> {target_id} ({relation_type.value}), skipping insert"
            )
            return existing[0].id

        # Validate causal relationships with Z3 before creating
        if relation_type in (RelationType.CAUSES, RelationType.CAUSED_BY) and self.causal_validator:
            try:
                # Get existing relationships for validation
                all_relationships = self.storage.get_relationships()
                existing_rels = [(r.source_id, r.target_id, r.relation_type) for r in all_relationships]
                
                # Get existing memories
                existing_memories = [source_memory, target_memory]
                
                is_valid, error = self.causal_validator.validate_single_causal_relationship(
                    source_id=source_id,
                    target_id=target_id,
                    existing_relationships=existing_rels,
                    existing_memories=existing_memories
                )
                
                if not is_valid:
                    logger.warning(f"Causal relationship validation failed: {error}")
                    # Still create the relationship but log the warning
                    # (non-blocking to allow manual override if needed)
                    
            except Exception as e:
                logger.error(f"Error in causal relationship validation: {e}", exc_info=True)
                # Continue with relationship creation even if validation fails

        # Create relationship record
        relationship = RelationshipRecord(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            strength=strength,
            bidirectional=bidirectional,
            metadata=metadata,
            created_at=datetime.now(timezone.utc)
        )
        
        # Store in database
        relationship_id = self.storage.store_relationship(relationship)
        
        logger.info(
            f"Linked memory {source_id} -> {target_id} "
            f"({relation_type.value}, strength={strength})"
        )
        
        return relationship_id
    
    def xǁRelationshipManagerǁlink__mutmut_20(
        self,
        source_id: int,
        target_id: int,
        relation_type: RelationType,
        strength: float = 1.0,
        bidirectional: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Create a relationship between two memories.
        
        Args:
            source_id: ID of source memory
            target_id: ID of target memory
            relation_type: Type of relationship
            strength: Relationship strength (0.0-1.0, default: 1.0)
            bidirectional: Whether relationship goes both ways (default: False)
            metadata: Optional additional context
            
        Returns:
            ID of the created relationship
        """
        if source_id == target_id:
            raise ValueError("Cannot create relationship from memory to itself")
        
        # Verify both memories exist
        source_memory = self.storage.get_memory(source_id)
        target_memory = self.storage.get_memory(target_id)
        
        if source_memory is None:
            raise ValueError(f"Source memory {source_id} not found")
        if target_memory is None:
            raise ValueError(f"Target memory {target_id} not found")
        
        # Avoid inserting duplicate relationships: check if identical relationship exists
        existing = self.storage.get_relationships(
            target_id=target_id,
            relation_type=relation_type
        )
        if existing:
            # If an identical relationship exists, return its id (first match)
            logger.info(
                f"Relationship already exists {source_id} -> {target_id} ({relation_type.value}), skipping insert"
            )
            return existing[0].id

        # Validate causal relationships with Z3 before creating
        if relation_type in (RelationType.CAUSES, RelationType.CAUSED_BY) and self.causal_validator:
            try:
                # Get existing relationships for validation
                all_relationships = self.storage.get_relationships()
                existing_rels = [(r.source_id, r.target_id, r.relation_type) for r in all_relationships]
                
                # Get existing memories
                existing_memories = [source_memory, target_memory]
                
                is_valid, error = self.causal_validator.validate_single_causal_relationship(
                    source_id=source_id,
                    target_id=target_id,
                    existing_relationships=existing_rels,
                    existing_memories=existing_memories
                )
                
                if not is_valid:
                    logger.warning(f"Causal relationship validation failed: {error}")
                    # Still create the relationship but log the warning
                    # (non-blocking to allow manual override if needed)
                    
            except Exception as e:
                logger.error(f"Error in causal relationship validation: {e}", exc_info=True)
                # Continue with relationship creation even if validation fails

        # Create relationship record
        relationship = RelationshipRecord(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            strength=strength,
            bidirectional=bidirectional,
            metadata=metadata,
            created_at=datetime.now(timezone.utc)
        )
        
        # Store in database
        relationship_id = self.storage.store_relationship(relationship)
        
        logger.info(
            f"Linked memory {source_id} -> {target_id} "
            f"({relation_type.value}, strength={strength})"
        )
        
        return relationship_id
    
    def xǁRelationshipManagerǁlink__mutmut_21(
        self,
        source_id: int,
        target_id: int,
        relation_type: RelationType,
        strength: float = 1.0,
        bidirectional: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Create a relationship between two memories.
        
        Args:
            source_id: ID of source memory
            target_id: ID of target memory
            relation_type: Type of relationship
            strength: Relationship strength (0.0-1.0, default: 1.0)
            bidirectional: Whether relationship goes both ways (default: False)
            metadata: Optional additional context
            
        Returns:
            ID of the created relationship
        """
        if source_id == target_id:
            raise ValueError("Cannot create relationship from memory to itself")
        
        # Verify both memories exist
        source_memory = self.storage.get_memory(source_id)
        target_memory = self.storage.get_memory(target_id)
        
        if source_memory is None:
            raise ValueError(f"Source memory {source_id} not found")
        if target_memory is None:
            raise ValueError(f"Target memory {target_id} not found")
        
        # Avoid inserting duplicate relationships: check if identical relationship exists
        existing = self.storage.get_relationships(
            source_id=source_id,
            relation_type=relation_type
        )
        if existing:
            # If an identical relationship exists, return its id (first match)
            logger.info(
                f"Relationship already exists {source_id} -> {target_id} ({relation_type.value}), skipping insert"
            )
            return existing[0].id

        # Validate causal relationships with Z3 before creating
        if relation_type in (RelationType.CAUSES, RelationType.CAUSED_BY) and self.causal_validator:
            try:
                # Get existing relationships for validation
                all_relationships = self.storage.get_relationships()
                existing_rels = [(r.source_id, r.target_id, r.relation_type) for r in all_relationships]
                
                # Get existing memories
                existing_memories = [source_memory, target_memory]
                
                is_valid, error = self.causal_validator.validate_single_causal_relationship(
                    source_id=source_id,
                    target_id=target_id,
                    existing_relationships=existing_rels,
                    existing_memories=existing_memories
                )
                
                if not is_valid:
                    logger.warning(f"Causal relationship validation failed: {error}")
                    # Still create the relationship but log the warning
                    # (non-blocking to allow manual override if needed)
                    
            except Exception as e:
                logger.error(f"Error in causal relationship validation: {e}", exc_info=True)
                # Continue with relationship creation even if validation fails

        # Create relationship record
        relationship = RelationshipRecord(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            strength=strength,
            bidirectional=bidirectional,
            metadata=metadata,
            created_at=datetime.now(timezone.utc)
        )
        
        # Store in database
        relationship_id = self.storage.store_relationship(relationship)
        
        logger.info(
            f"Linked memory {source_id} -> {target_id} "
            f"({relation_type.value}, strength={strength})"
        )
        
        return relationship_id
    
    def xǁRelationshipManagerǁlink__mutmut_22(
        self,
        source_id: int,
        target_id: int,
        relation_type: RelationType,
        strength: float = 1.0,
        bidirectional: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Create a relationship between two memories.
        
        Args:
            source_id: ID of source memory
            target_id: ID of target memory
            relation_type: Type of relationship
            strength: Relationship strength (0.0-1.0, default: 1.0)
            bidirectional: Whether relationship goes both ways (default: False)
            metadata: Optional additional context
            
        Returns:
            ID of the created relationship
        """
        if source_id == target_id:
            raise ValueError("Cannot create relationship from memory to itself")
        
        # Verify both memories exist
        source_memory = self.storage.get_memory(source_id)
        target_memory = self.storage.get_memory(target_id)
        
        if source_memory is None:
            raise ValueError(f"Source memory {source_id} not found")
        if target_memory is None:
            raise ValueError(f"Target memory {target_id} not found")
        
        # Avoid inserting duplicate relationships: check if identical relationship exists
        existing = self.storage.get_relationships(
            source_id=source_id,
            target_id=target_id,
            )
        if existing:
            # If an identical relationship exists, return its id (first match)
            logger.info(
                f"Relationship already exists {source_id} -> {target_id} ({relation_type.value}), skipping insert"
            )
            return existing[0].id

        # Validate causal relationships with Z3 before creating
        if relation_type in (RelationType.CAUSES, RelationType.CAUSED_BY) and self.causal_validator:
            try:
                # Get existing relationships for validation
                all_relationships = self.storage.get_relationships()
                existing_rels = [(r.source_id, r.target_id, r.relation_type) for r in all_relationships]
                
                # Get existing memories
                existing_memories = [source_memory, target_memory]
                
                is_valid, error = self.causal_validator.validate_single_causal_relationship(
                    source_id=source_id,
                    target_id=target_id,
                    existing_relationships=existing_rels,
                    existing_memories=existing_memories
                )
                
                if not is_valid:
                    logger.warning(f"Causal relationship validation failed: {error}")
                    # Still create the relationship but log the warning
                    # (non-blocking to allow manual override if needed)
                    
            except Exception as e:
                logger.error(f"Error in causal relationship validation: {e}", exc_info=True)
                # Continue with relationship creation even if validation fails

        # Create relationship record
        relationship = RelationshipRecord(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            strength=strength,
            bidirectional=bidirectional,
            metadata=metadata,
            created_at=datetime.now(timezone.utc)
        )
        
        # Store in database
        relationship_id = self.storage.store_relationship(relationship)
        
        logger.info(
            f"Linked memory {source_id} -> {target_id} "
            f"({relation_type.value}, strength={strength})"
        )
        
        return relationship_id
    
    def xǁRelationshipManagerǁlink__mutmut_23(
        self,
        source_id: int,
        target_id: int,
        relation_type: RelationType,
        strength: float = 1.0,
        bidirectional: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Create a relationship between two memories.
        
        Args:
            source_id: ID of source memory
            target_id: ID of target memory
            relation_type: Type of relationship
            strength: Relationship strength (0.0-1.0, default: 1.0)
            bidirectional: Whether relationship goes both ways (default: False)
            metadata: Optional additional context
            
        Returns:
            ID of the created relationship
        """
        if source_id == target_id:
            raise ValueError("Cannot create relationship from memory to itself")
        
        # Verify both memories exist
        source_memory = self.storage.get_memory(source_id)
        target_memory = self.storage.get_memory(target_id)
        
        if source_memory is None:
            raise ValueError(f"Source memory {source_id} not found")
        if target_memory is None:
            raise ValueError(f"Target memory {target_id} not found")
        
        # Avoid inserting duplicate relationships: check if identical relationship exists
        existing = self.storage.get_relationships(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type
        )
        if existing:
            # If an identical relationship exists, return its id (first match)
            logger.info(
                None
            )
            return existing[0].id

        # Validate causal relationships with Z3 before creating
        if relation_type in (RelationType.CAUSES, RelationType.CAUSED_BY) and self.causal_validator:
            try:
                # Get existing relationships for validation
                all_relationships = self.storage.get_relationships()
                existing_rels = [(r.source_id, r.target_id, r.relation_type) for r in all_relationships]
                
                # Get existing memories
                existing_memories = [source_memory, target_memory]
                
                is_valid, error = self.causal_validator.validate_single_causal_relationship(
                    source_id=source_id,
                    target_id=target_id,
                    existing_relationships=existing_rels,
                    existing_memories=existing_memories
                )
                
                if not is_valid:
                    logger.warning(f"Causal relationship validation failed: {error}")
                    # Still create the relationship but log the warning
                    # (non-blocking to allow manual override if needed)
                    
            except Exception as e:
                logger.error(f"Error in causal relationship validation: {e}", exc_info=True)
                # Continue with relationship creation even if validation fails

        # Create relationship record
        relationship = RelationshipRecord(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            strength=strength,
            bidirectional=bidirectional,
            metadata=metadata,
            created_at=datetime.now(timezone.utc)
        )
        
        # Store in database
        relationship_id = self.storage.store_relationship(relationship)
        
        logger.info(
            f"Linked memory {source_id} -> {target_id} "
            f"({relation_type.value}, strength={strength})"
        )
        
        return relationship_id
    
    def xǁRelationshipManagerǁlink__mutmut_24(
        self,
        source_id: int,
        target_id: int,
        relation_type: RelationType,
        strength: float = 1.0,
        bidirectional: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Create a relationship between two memories.
        
        Args:
            source_id: ID of source memory
            target_id: ID of target memory
            relation_type: Type of relationship
            strength: Relationship strength (0.0-1.0, default: 1.0)
            bidirectional: Whether relationship goes both ways (default: False)
            metadata: Optional additional context
            
        Returns:
            ID of the created relationship
        """
        if source_id == target_id:
            raise ValueError("Cannot create relationship from memory to itself")
        
        # Verify both memories exist
        source_memory = self.storage.get_memory(source_id)
        target_memory = self.storage.get_memory(target_id)
        
        if source_memory is None:
            raise ValueError(f"Source memory {source_id} not found")
        if target_memory is None:
            raise ValueError(f"Target memory {target_id} not found")
        
        # Avoid inserting duplicate relationships: check if identical relationship exists
        existing = self.storage.get_relationships(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type
        )
        if existing:
            # If an identical relationship exists, return its id (first match)
            logger.info(
                f"Relationship already exists {source_id} -> {target_id} ({relation_type.value}), skipping insert"
            )
            return existing[1].id

        # Validate causal relationships with Z3 before creating
        if relation_type in (RelationType.CAUSES, RelationType.CAUSED_BY) and self.causal_validator:
            try:
                # Get existing relationships for validation
                all_relationships = self.storage.get_relationships()
                existing_rels = [(r.source_id, r.target_id, r.relation_type) for r in all_relationships]
                
                # Get existing memories
                existing_memories = [source_memory, target_memory]
                
                is_valid, error = self.causal_validator.validate_single_causal_relationship(
                    source_id=source_id,
                    target_id=target_id,
                    existing_relationships=existing_rels,
                    existing_memories=existing_memories
                )
                
                if not is_valid:
                    logger.warning(f"Causal relationship validation failed: {error}")
                    # Still create the relationship but log the warning
                    # (non-blocking to allow manual override if needed)
                    
            except Exception as e:
                logger.error(f"Error in causal relationship validation: {e}", exc_info=True)
                # Continue with relationship creation even if validation fails

        # Create relationship record
        relationship = RelationshipRecord(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            strength=strength,
            bidirectional=bidirectional,
            metadata=metadata,
            created_at=datetime.now(timezone.utc)
        )
        
        # Store in database
        relationship_id = self.storage.store_relationship(relationship)
        
        logger.info(
            f"Linked memory {source_id} -> {target_id} "
            f"({relation_type.value}, strength={strength})"
        )
        
        return relationship_id
    
    def xǁRelationshipManagerǁlink__mutmut_25(
        self,
        source_id: int,
        target_id: int,
        relation_type: RelationType,
        strength: float = 1.0,
        bidirectional: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Create a relationship between two memories.
        
        Args:
            source_id: ID of source memory
            target_id: ID of target memory
            relation_type: Type of relationship
            strength: Relationship strength (0.0-1.0, default: 1.0)
            bidirectional: Whether relationship goes both ways (default: False)
            metadata: Optional additional context
            
        Returns:
            ID of the created relationship
        """
        if source_id == target_id:
            raise ValueError("Cannot create relationship from memory to itself")
        
        # Verify both memories exist
        source_memory = self.storage.get_memory(source_id)
        target_memory = self.storage.get_memory(target_id)
        
        if source_memory is None:
            raise ValueError(f"Source memory {source_id} not found")
        if target_memory is None:
            raise ValueError(f"Target memory {target_id} not found")
        
        # Avoid inserting duplicate relationships: check if identical relationship exists
        existing = self.storage.get_relationships(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type
        )
        if existing:
            # If an identical relationship exists, return its id (first match)
            logger.info(
                f"Relationship already exists {source_id} -> {target_id} ({relation_type.value}), skipping insert"
            )
            return existing[0].id

        # Validate causal relationships with Z3 before creating
        if relation_type in (RelationType.CAUSES, RelationType.CAUSED_BY) or self.causal_validator:
            try:
                # Get existing relationships for validation
                all_relationships = self.storage.get_relationships()
                existing_rels = [(r.source_id, r.target_id, r.relation_type) for r in all_relationships]
                
                # Get existing memories
                existing_memories = [source_memory, target_memory]
                
                is_valid, error = self.causal_validator.validate_single_causal_relationship(
                    source_id=source_id,
                    target_id=target_id,
                    existing_relationships=existing_rels,
                    existing_memories=existing_memories
                )
                
                if not is_valid:
                    logger.warning(f"Causal relationship validation failed: {error}")
                    # Still create the relationship but log the warning
                    # (non-blocking to allow manual override if needed)
                    
            except Exception as e:
                logger.error(f"Error in causal relationship validation: {e}", exc_info=True)
                # Continue with relationship creation even if validation fails

        # Create relationship record
        relationship = RelationshipRecord(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            strength=strength,
            bidirectional=bidirectional,
            metadata=metadata,
            created_at=datetime.now(timezone.utc)
        )
        
        # Store in database
        relationship_id = self.storage.store_relationship(relationship)
        
        logger.info(
            f"Linked memory {source_id} -> {target_id} "
            f"({relation_type.value}, strength={strength})"
        )
        
        return relationship_id
    
    def xǁRelationshipManagerǁlink__mutmut_26(
        self,
        source_id: int,
        target_id: int,
        relation_type: RelationType,
        strength: float = 1.0,
        bidirectional: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Create a relationship between two memories.
        
        Args:
            source_id: ID of source memory
            target_id: ID of target memory
            relation_type: Type of relationship
            strength: Relationship strength (0.0-1.0, default: 1.0)
            bidirectional: Whether relationship goes both ways (default: False)
            metadata: Optional additional context
            
        Returns:
            ID of the created relationship
        """
        if source_id == target_id:
            raise ValueError("Cannot create relationship from memory to itself")
        
        # Verify both memories exist
        source_memory = self.storage.get_memory(source_id)
        target_memory = self.storage.get_memory(target_id)
        
        if source_memory is None:
            raise ValueError(f"Source memory {source_id} not found")
        if target_memory is None:
            raise ValueError(f"Target memory {target_id} not found")
        
        # Avoid inserting duplicate relationships: check if identical relationship exists
        existing = self.storage.get_relationships(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type
        )
        if existing:
            # If an identical relationship exists, return its id (first match)
            logger.info(
                f"Relationship already exists {source_id} -> {target_id} ({relation_type.value}), skipping insert"
            )
            return existing[0].id

        # Validate causal relationships with Z3 before creating
        if relation_type not in (RelationType.CAUSES, RelationType.CAUSED_BY) and self.causal_validator:
            try:
                # Get existing relationships for validation
                all_relationships = self.storage.get_relationships()
                existing_rels = [(r.source_id, r.target_id, r.relation_type) for r in all_relationships]
                
                # Get existing memories
                existing_memories = [source_memory, target_memory]
                
                is_valid, error = self.causal_validator.validate_single_causal_relationship(
                    source_id=source_id,
                    target_id=target_id,
                    existing_relationships=existing_rels,
                    existing_memories=existing_memories
                )
                
                if not is_valid:
                    logger.warning(f"Causal relationship validation failed: {error}")
                    # Still create the relationship but log the warning
                    # (non-blocking to allow manual override if needed)
                    
            except Exception as e:
                logger.error(f"Error in causal relationship validation: {e}", exc_info=True)
                # Continue with relationship creation even if validation fails

        # Create relationship record
        relationship = RelationshipRecord(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            strength=strength,
            bidirectional=bidirectional,
            metadata=metadata,
            created_at=datetime.now(timezone.utc)
        )
        
        # Store in database
        relationship_id = self.storage.store_relationship(relationship)
        
        logger.info(
            f"Linked memory {source_id} -> {target_id} "
            f"({relation_type.value}, strength={strength})"
        )
        
        return relationship_id
    
    def xǁRelationshipManagerǁlink__mutmut_27(
        self,
        source_id: int,
        target_id: int,
        relation_type: RelationType,
        strength: float = 1.0,
        bidirectional: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Create a relationship between two memories.
        
        Args:
            source_id: ID of source memory
            target_id: ID of target memory
            relation_type: Type of relationship
            strength: Relationship strength (0.0-1.0, default: 1.0)
            bidirectional: Whether relationship goes both ways (default: False)
            metadata: Optional additional context
            
        Returns:
            ID of the created relationship
        """
        if source_id == target_id:
            raise ValueError("Cannot create relationship from memory to itself")
        
        # Verify both memories exist
        source_memory = self.storage.get_memory(source_id)
        target_memory = self.storage.get_memory(target_id)
        
        if source_memory is None:
            raise ValueError(f"Source memory {source_id} not found")
        if target_memory is None:
            raise ValueError(f"Target memory {target_id} not found")
        
        # Avoid inserting duplicate relationships: check if identical relationship exists
        existing = self.storage.get_relationships(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type
        )
        if existing:
            # If an identical relationship exists, return its id (first match)
            logger.info(
                f"Relationship already exists {source_id} -> {target_id} ({relation_type.value}), skipping insert"
            )
            return existing[0].id

        # Validate causal relationships with Z3 before creating
        if relation_type in (RelationType.CAUSES, RelationType.CAUSED_BY) and self.causal_validator:
            try:
                # Get existing relationships for validation
                all_relationships = None
                existing_rels = [(r.source_id, r.target_id, r.relation_type) for r in all_relationships]
                
                # Get existing memories
                existing_memories = [source_memory, target_memory]
                
                is_valid, error = self.causal_validator.validate_single_causal_relationship(
                    source_id=source_id,
                    target_id=target_id,
                    existing_relationships=existing_rels,
                    existing_memories=existing_memories
                )
                
                if not is_valid:
                    logger.warning(f"Causal relationship validation failed: {error}")
                    # Still create the relationship but log the warning
                    # (non-blocking to allow manual override if needed)
                    
            except Exception as e:
                logger.error(f"Error in causal relationship validation: {e}", exc_info=True)
                # Continue with relationship creation even if validation fails

        # Create relationship record
        relationship = RelationshipRecord(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            strength=strength,
            bidirectional=bidirectional,
            metadata=metadata,
            created_at=datetime.now(timezone.utc)
        )
        
        # Store in database
        relationship_id = self.storage.store_relationship(relationship)
        
        logger.info(
            f"Linked memory {source_id} -> {target_id} "
            f"({relation_type.value}, strength={strength})"
        )
        
        return relationship_id
    
    def xǁRelationshipManagerǁlink__mutmut_28(
        self,
        source_id: int,
        target_id: int,
        relation_type: RelationType,
        strength: float = 1.0,
        bidirectional: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Create a relationship between two memories.
        
        Args:
            source_id: ID of source memory
            target_id: ID of target memory
            relation_type: Type of relationship
            strength: Relationship strength (0.0-1.0, default: 1.0)
            bidirectional: Whether relationship goes both ways (default: False)
            metadata: Optional additional context
            
        Returns:
            ID of the created relationship
        """
        if source_id == target_id:
            raise ValueError("Cannot create relationship from memory to itself")
        
        # Verify both memories exist
        source_memory = self.storage.get_memory(source_id)
        target_memory = self.storage.get_memory(target_id)
        
        if source_memory is None:
            raise ValueError(f"Source memory {source_id} not found")
        if target_memory is None:
            raise ValueError(f"Target memory {target_id} not found")
        
        # Avoid inserting duplicate relationships: check if identical relationship exists
        existing = self.storage.get_relationships(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type
        )
        if existing:
            # If an identical relationship exists, return its id (first match)
            logger.info(
                f"Relationship already exists {source_id} -> {target_id} ({relation_type.value}), skipping insert"
            )
            return existing[0].id

        # Validate causal relationships with Z3 before creating
        if relation_type in (RelationType.CAUSES, RelationType.CAUSED_BY) and self.causal_validator:
            try:
                # Get existing relationships for validation
                all_relationships = self.storage.get_relationships()
                existing_rels = None
                
                # Get existing memories
                existing_memories = [source_memory, target_memory]
                
                is_valid, error = self.causal_validator.validate_single_causal_relationship(
                    source_id=source_id,
                    target_id=target_id,
                    existing_relationships=existing_rels,
                    existing_memories=existing_memories
                )
                
                if not is_valid:
                    logger.warning(f"Causal relationship validation failed: {error}")
                    # Still create the relationship but log the warning
                    # (non-blocking to allow manual override if needed)
                    
            except Exception as e:
                logger.error(f"Error in causal relationship validation: {e}", exc_info=True)
                # Continue with relationship creation even if validation fails

        # Create relationship record
        relationship = RelationshipRecord(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            strength=strength,
            bidirectional=bidirectional,
            metadata=metadata,
            created_at=datetime.now(timezone.utc)
        )
        
        # Store in database
        relationship_id = self.storage.store_relationship(relationship)
        
        logger.info(
            f"Linked memory {source_id} -> {target_id} "
            f"({relation_type.value}, strength={strength})"
        )
        
        return relationship_id
    
    def xǁRelationshipManagerǁlink__mutmut_29(
        self,
        source_id: int,
        target_id: int,
        relation_type: RelationType,
        strength: float = 1.0,
        bidirectional: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Create a relationship between two memories.
        
        Args:
            source_id: ID of source memory
            target_id: ID of target memory
            relation_type: Type of relationship
            strength: Relationship strength (0.0-1.0, default: 1.0)
            bidirectional: Whether relationship goes both ways (default: False)
            metadata: Optional additional context
            
        Returns:
            ID of the created relationship
        """
        if source_id == target_id:
            raise ValueError("Cannot create relationship from memory to itself")
        
        # Verify both memories exist
        source_memory = self.storage.get_memory(source_id)
        target_memory = self.storage.get_memory(target_id)
        
        if source_memory is None:
            raise ValueError(f"Source memory {source_id} not found")
        if target_memory is None:
            raise ValueError(f"Target memory {target_id} not found")
        
        # Avoid inserting duplicate relationships: check if identical relationship exists
        existing = self.storage.get_relationships(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type
        )
        if existing:
            # If an identical relationship exists, return its id (first match)
            logger.info(
                f"Relationship already exists {source_id} -> {target_id} ({relation_type.value}), skipping insert"
            )
            return existing[0].id

        # Validate causal relationships with Z3 before creating
        if relation_type in (RelationType.CAUSES, RelationType.CAUSED_BY) and self.causal_validator:
            try:
                # Get existing relationships for validation
                all_relationships = self.storage.get_relationships()
                existing_rels = [(r.source_id, r.target_id, r.relation_type) for r in all_relationships]
                
                # Get existing memories
                existing_memories = None
                
                is_valid, error = self.causal_validator.validate_single_causal_relationship(
                    source_id=source_id,
                    target_id=target_id,
                    existing_relationships=existing_rels,
                    existing_memories=existing_memories
                )
                
                if not is_valid:
                    logger.warning(f"Causal relationship validation failed: {error}")
                    # Still create the relationship but log the warning
                    # (non-blocking to allow manual override if needed)
                    
            except Exception as e:
                logger.error(f"Error in causal relationship validation: {e}", exc_info=True)
                # Continue with relationship creation even if validation fails

        # Create relationship record
        relationship = RelationshipRecord(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            strength=strength,
            bidirectional=bidirectional,
            metadata=metadata,
            created_at=datetime.now(timezone.utc)
        )
        
        # Store in database
        relationship_id = self.storage.store_relationship(relationship)
        
        logger.info(
            f"Linked memory {source_id} -> {target_id} "
            f"({relation_type.value}, strength={strength})"
        )
        
        return relationship_id
    
    def xǁRelationshipManagerǁlink__mutmut_30(
        self,
        source_id: int,
        target_id: int,
        relation_type: RelationType,
        strength: float = 1.0,
        bidirectional: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Create a relationship between two memories.
        
        Args:
            source_id: ID of source memory
            target_id: ID of target memory
            relation_type: Type of relationship
            strength: Relationship strength (0.0-1.0, default: 1.0)
            bidirectional: Whether relationship goes both ways (default: False)
            metadata: Optional additional context
            
        Returns:
            ID of the created relationship
        """
        if source_id == target_id:
            raise ValueError("Cannot create relationship from memory to itself")
        
        # Verify both memories exist
        source_memory = self.storage.get_memory(source_id)
        target_memory = self.storage.get_memory(target_id)
        
        if source_memory is None:
            raise ValueError(f"Source memory {source_id} not found")
        if target_memory is None:
            raise ValueError(f"Target memory {target_id} not found")
        
        # Avoid inserting duplicate relationships: check if identical relationship exists
        existing = self.storage.get_relationships(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type
        )
        if existing:
            # If an identical relationship exists, return its id (first match)
            logger.info(
                f"Relationship already exists {source_id} -> {target_id} ({relation_type.value}), skipping insert"
            )
            return existing[0].id

        # Validate causal relationships with Z3 before creating
        if relation_type in (RelationType.CAUSES, RelationType.CAUSED_BY) and self.causal_validator:
            try:
                # Get existing relationships for validation
                all_relationships = self.storage.get_relationships()
                existing_rels = [(r.source_id, r.target_id, r.relation_type) for r in all_relationships]
                
                # Get existing memories
                existing_memories = [source_memory, target_memory]
                
                is_valid, error = None
                
                if not is_valid:
                    logger.warning(f"Causal relationship validation failed: {error}")
                    # Still create the relationship but log the warning
                    # (non-blocking to allow manual override if needed)
                    
            except Exception as e:
                logger.error(f"Error in causal relationship validation: {e}", exc_info=True)
                # Continue with relationship creation even if validation fails

        # Create relationship record
        relationship = RelationshipRecord(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            strength=strength,
            bidirectional=bidirectional,
            metadata=metadata,
            created_at=datetime.now(timezone.utc)
        )
        
        # Store in database
        relationship_id = self.storage.store_relationship(relationship)
        
        logger.info(
            f"Linked memory {source_id} -> {target_id} "
            f"({relation_type.value}, strength={strength})"
        )
        
        return relationship_id
    
    def xǁRelationshipManagerǁlink__mutmut_31(
        self,
        source_id: int,
        target_id: int,
        relation_type: RelationType,
        strength: float = 1.0,
        bidirectional: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Create a relationship between two memories.
        
        Args:
            source_id: ID of source memory
            target_id: ID of target memory
            relation_type: Type of relationship
            strength: Relationship strength (0.0-1.0, default: 1.0)
            bidirectional: Whether relationship goes both ways (default: False)
            metadata: Optional additional context
            
        Returns:
            ID of the created relationship
        """
        if source_id == target_id:
            raise ValueError("Cannot create relationship from memory to itself")
        
        # Verify both memories exist
        source_memory = self.storage.get_memory(source_id)
        target_memory = self.storage.get_memory(target_id)
        
        if source_memory is None:
            raise ValueError(f"Source memory {source_id} not found")
        if target_memory is None:
            raise ValueError(f"Target memory {target_id} not found")
        
        # Avoid inserting duplicate relationships: check if identical relationship exists
        existing = self.storage.get_relationships(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type
        )
        if existing:
            # If an identical relationship exists, return its id (first match)
            logger.info(
                f"Relationship already exists {source_id} -> {target_id} ({relation_type.value}), skipping insert"
            )
            return existing[0].id

        # Validate causal relationships with Z3 before creating
        if relation_type in (RelationType.CAUSES, RelationType.CAUSED_BY) and self.causal_validator:
            try:
                # Get existing relationships for validation
                all_relationships = self.storage.get_relationships()
                existing_rels = [(r.source_id, r.target_id, r.relation_type) for r in all_relationships]
                
                # Get existing memories
                existing_memories = [source_memory, target_memory]
                
                is_valid, error = self.causal_validator.validate_single_causal_relationship(
                    source_id=None,
                    target_id=target_id,
                    existing_relationships=existing_rels,
                    existing_memories=existing_memories
                )
                
                if not is_valid:
                    logger.warning(f"Causal relationship validation failed: {error}")
                    # Still create the relationship but log the warning
                    # (non-blocking to allow manual override if needed)
                    
            except Exception as e:
                logger.error(f"Error in causal relationship validation: {e}", exc_info=True)
                # Continue with relationship creation even if validation fails

        # Create relationship record
        relationship = RelationshipRecord(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            strength=strength,
            bidirectional=bidirectional,
            metadata=metadata,
            created_at=datetime.now(timezone.utc)
        )
        
        # Store in database
        relationship_id = self.storage.store_relationship(relationship)
        
        logger.info(
            f"Linked memory {source_id} -> {target_id} "
            f"({relation_type.value}, strength={strength})"
        )
        
        return relationship_id
    
    def xǁRelationshipManagerǁlink__mutmut_32(
        self,
        source_id: int,
        target_id: int,
        relation_type: RelationType,
        strength: float = 1.0,
        bidirectional: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Create a relationship between two memories.
        
        Args:
            source_id: ID of source memory
            target_id: ID of target memory
            relation_type: Type of relationship
            strength: Relationship strength (0.0-1.0, default: 1.0)
            bidirectional: Whether relationship goes both ways (default: False)
            metadata: Optional additional context
            
        Returns:
            ID of the created relationship
        """
        if source_id == target_id:
            raise ValueError("Cannot create relationship from memory to itself")
        
        # Verify both memories exist
        source_memory = self.storage.get_memory(source_id)
        target_memory = self.storage.get_memory(target_id)
        
        if source_memory is None:
            raise ValueError(f"Source memory {source_id} not found")
        if target_memory is None:
            raise ValueError(f"Target memory {target_id} not found")
        
        # Avoid inserting duplicate relationships: check if identical relationship exists
        existing = self.storage.get_relationships(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type
        )
        if existing:
            # If an identical relationship exists, return its id (first match)
            logger.info(
                f"Relationship already exists {source_id} -> {target_id} ({relation_type.value}), skipping insert"
            )
            return existing[0].id

        # Validate causal relationships with Z3 before creating
        if relation_type in (RelationType.CAUSES, RelationType.CAUSED_BY) and self.causal_validator:
            try:
                # Get existing relationships for validation
                all_relationships = self.storage.get_relationships()
                existing_rels = [(r.source_id, r.target_id, r.relation_type) for r in all_relationships]
                
                # Get existing memories
                existing_memories = [source_memory, target_memory]
                
                is_valid, error = self.causal_validator.validate_single_causal_relationship(
                    source_id=source_id,
                    target_id=None,
                    existing_relationships=existing_rels,
                    existing_memories=existing_memories
                )
                
                if not is_valid:
                    logger.warning(f"Causal relationship validation failed: {error}")
                    # Still create the relationship but log the warning
                    # (non-blocking to allow manual override if needed)
                    
            except Exception as e:
                logger.error(f"Error in causal relationship validation: {e}", exc_info=True)
                # Continue with relationship creation even if validation fails

        # Create relationship record
        relationship = RelationshipRecord(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            strength=strength,
            bidirectional=bidirectional,
            metadata=metadata,
            created_at=datetime.now(timezone.utc)
        )
        
        # Store in database
        relationship_id = self.storage.store_relationship(relationship)
        
        logger.info(
            f"Linked memory {source_id} -> {target_id} "
            f"({relation_type.value}, strength={strength})"
        )
        
        return relationship_id
    
    def xǁRelationshipManagerǁlink__mutmut_33(
        self,
        source_id: int,
        target_id: int,
        relation_type: RelationType,
        strength: float = 1.0,
        bidirectional: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Create a relationship between two memories.
        
        Args:
            source_id: ID of source memory
            target_id: ID of target memory
            relation_type: Type of relationship
            strength: Relationship strength (0.0-1.0, default: 1.0)
            bidirectional: Whether relationship goes both ways (default: False)
            metadata: Optional additional context
            
        Returns:
            ID of the created relationship
        """
        if source_id == target_id:
            raise ValueError("Cannot create relationship from memory to itself")
        
        # Verify both memories exist
        source_memory = self.storage.get_memory(source_id)
        target_memory = self.storage.get_memory(target_id)
        
        if source_memory is None:
            raise ValueError(f"Source memory {source_id} not found")
        if target_memory is None:
            raise ValueError(f"Target memory {target_id} not found")
        
        # Avoid inserting duplicate relationships: check if identical relationship exists
        existing = self.storage.get_relationships(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type
        )
        if existing:
            # If an identical relationship exists, return its id (first match)
            logger.info(
                f"Relationship already exists {source_id} -> {target_id} ({relation_type.value}), skipping insert"
            )
            return existing[0].id

        # Validate causal relationships with Z3 before creating
        if relation_type in (RelationType.CAUSES, RelationType.CAUSED_BY) and self.causal_validator:
            try:
                # Get existing relationships for validation
                all_relationships = self.storage.get_relationships()
                existing_rels = [(r.source_id, r.target_id, r.relation_type) for r in all_relationships]
                
                # Get existing memories
                existing_memories = [source_memory, target_memory]
                
                is_valid, error = self.causal_validator.validate_single_causal_relationship(
                    source_id=source_id,
                    target_id=target_id,
                    existing_relationships=None,
                    existing_memories=existing_memories
                )
                
                if not is_valid:
                    logger.warning(f"Causal relationship validation failed: {error}")
                    # Still create the relationship but log the warning
                    # (non-blocking to allow manual override if needed)
                    
            except Exception as e:
                logger.error(f"Error in causal relationship validation: {e}", exc_info=True)
                # Continue with relationship creation even if validation fails

        # Create relationship record
        relationship = RelationshipRecord(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            strength=strength,
            bidirectional=bidirectional,
            metadata=metadata,
            created_at=datetime.now(timezone.utc)
        )
        
        # Store in database
        relationship_id = self.storage.store_relationship(relationship)
        
        logger.info(
            f"Linked memory {source_id} -> {target_id} "
            f"({relation_type.value}, strength={strength})"
        )
        
        return relationship_id
    
    def xǁRelationshipManagerǁlink__mutmut_34(
        self,
        source_id: int,
        target_id: int,
        relation_type: RelationType,
        strength: float = 1.0,
        bidirectional: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Create a relationship between two memories.
        
        Args:
            source_id: ID of source memory
            target_id: ID of target memory
            relation_type: Type of relationship
            strength: Relationship strength (0.0-1.0, default: 1.0)
            bidirectional: Whether relationship goes both ways (default: False)
            metadata: Optional additional context
            
        Returns:
            ID of the created relationship
        """
        if source_id == target_id:
            raise ValueError("Cannot create relationship from memory to itself")
        
        # Verify both memories exist
        source_memory = self.storage.get_memory(source_id)
        target_memory = self.storage.get_memory(target_id)
        
        if source_memory is None:
            raise ValueError(f"Source memory {source_id} not found")
        if target_memory is None:
            raise ValueError(f"Target memory {target_id} not found")
        
        # Avoid inserting duplicate relationships: check if identical relationship exists
        existing = self.storage.get_relationships(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type
        )
        if existing:
            # If an identical relationship exists, return its id (first match)
            logger.info(
                f"Relationship already exists {source_id} -> {target_id} ({relation_type.value}), skipping insert"
            )
            return existing[0].id

        # Validate causal relationships with Z3 before creating
        if relation_type in (RelationType.CAUSES, RelationType.CAUSED_BY) and self.causal_validator:
            try:
                # Get existing relationships for validation
                all_relationships = self.storage.get_relationships()
                existing_rels = [(r.source_id, r.target_id, r.relation_type) for r in all_relationships]
                
                # Get existing memories
                existing_memories = [source_memory, target_memory]
                
                is_valid, error = self.causal_validator.validate_single_causal_relationship(
                    source_id=source_id,
                    target_id=target_id,
                    existing_relationships=existing_rels,
                    existing_memories=None
                )
                
                if not is_valid:
                    logger.warning(f"Causal relationship validation failed: {error}")
                    # Still create the relationship but log the warning
                    # (non-blocking to allow manual override if needed)
                    
            except Exception as e:
                logger.error(f"Error in causal relationship validation: {e}", exc_info=True)
                # Continue with relationship creation even if validation fails

        # Create relationship record
        relationship = RelationshipRecord(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            strength=strength,
            bidirectional=bidirectional,
            metadata=metadata,
            created_at=datetime.now(timezone.utc)
        )
        
        # Store in database
        relationship_id = self.storage.store_relationship(relationship)
        
        logger.info(
            f"Linked memory {source_id} -> {target_id} "
            f"({relation_type.value}, strength={strength})"
        )
        
        return relationship_id
    
    def xǁRelationshipManagerǁlink__mutmut_35(
        self,
        source_id: int,
        target_id: int,
        relation_type: RelationType,
        strength: float = 1.0,
        bidirectional: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Create a relationship between two memories.
        
        Args:
            source_id: ID of source memory
            target_id: ID of target memory
            relation_type: Type of relationship
            strength: Relationship strength (0.0-1.0, default: 1.0)
            bidirectional: Whether relationship goes both ways (default: False)
            metadata: Optional additional context
            
        Returns:
            ID of the created relationship
        """
        if source_id == target_id:
            raise ValueError("Cannot create relationship from memory to itself")
        
        # Verify both memories exist
        source_memory = self.storage.get_memory(source_id)
        target_memory = self.storage.get_memory(target_id)
        
        if source_memory is None:
            raise ValueError(f"Source memory {source_id} not found")
        if target_memory is None:
            raise ValueError(f"Target memory {target_id} not found")
        
        # Avoid inserting duplicate relationships: check if identical relationship exists
        existing = self.storage.get_relationships(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type
        )
        if existing:
            # If an identical relationship exists, return its id (first match)
            logger.info(
                f"Relationship already exists {source_id} -> {target_id} ({relation_type.value}), skipping insert"
            )
            return existing[0].id

        # Validate causal relationships with Z3 before creating
        if relation_type in (RelationType.CAUSES, RelationType.CAUSED_BY) and self.causal_validator:
            try:
                # Get existing relationships for validation
                all_relationships = self.storage.get_relationships()
                existing_rels = [(r.source_id, r.target_id, r.relation_type) for r in all_relationships]
                
                # Get existing memories
                existing_memories = [source_memory, target_memory]
                
                is_valid, error = self.causal_validator.validate_single_causal_relationship(
                    target_id=target_id,
                    existing_relationships=existing_rels,
                    existing_memories=existing_memories
                )
                
                if not is_valid:
                    logger.warning(f"Causal relationship validation failed: {error}")
                    # Still create the relationship but log the warning
                    # (non-blocking to allow manual override if needed)
                    
            except Exception as e:
                logger.error(f"Error in causal relationship validation: {e}", exc_info=True)
                # Continue with relationship creation even if validation fails

        # Create relationship record
        relationship = RelationshipRecord(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            strength=strength,
            bidirectional=bidirectional,
            metadata=metadata,
            created_at=datetime.now(timezone.utc)
        )
        
        # Store in database
        relationship_id = self.storage.store_relationship(relationship)
        
        logger.info(
            f"Linked memory {source_id} -> {target_id} "
            f"({relation_type.value}, strength={strength})"
        )
        
        return relationship_id
    
    def xǁRelationshipManagerǁlink__mutmut_36(
        self,
        source_id: int,
        target_id: int,
        relation_type: RelationType,
        strength: float = 1.0,
        bidirectional: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Create a relationship between two memories.
        
        Args:
            source_id: ID of source memory
            target_id: ID of target memory
            relation_type: Type of relationship
            strength: Relationship strength (0.0-1.0, default: 1.0)
            bidirectional: Whether relationship goes both ways (default: False)
            metadata: Optional additional context
            
        Returns:
            ID of the created relationship
        """
        if source_id == target_id:
            raise ValueError("Cannot create relationship from memory to itself")
        
        # Verify both memories exist
        source_memory = self.storage.get_memory(source_id)
        target_memory = self.storage.get_memory(target_id)
        
        if source_memory is None:
            raise ValueError(f"Source memory {source_id} not found")
        if target_memory is None:
            raise ValueError(f"Target memory {target_id} not found")
        
        # Avoid inserting duplicate relationships: check if identical relationship exists
        existing = self.storage.get_relationships(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type
        )
        if existing:
            # If an identical relationship exists, return its id (first match)
            logger.info(
                f"Relationship already exists {source_id} -> {target_id} ({relation_type.value}), skipping insert"
            )
            return existing[0].id

        # Validate causal relationships with Z3 before creating
        if relation_type in (RelationType.CAUSES, RelationType.CAUSED_BY) and self.causal_validator:
            try:
                # Get existing relationships for validation
                all_relationships = self.storage.get_relationships()
                existing_rels = [(r.source_id, r.target_id, r.relation_type) for r in all_relationships]
                
                # Get existing memories
                existing_memories = [source_memory, target_memory]
                
                is_valid, error = self.causal_validator.validate_single_causal_relationship(
                    source_id=source_id,
                    existing_relationships=existing_rels,
                    existing_memories=existing_memories
                )
                
                if not is_valid:
                    logger.warning(f"Causal relationship validation failed: {error}")
                    # Still create the relationship but log the warning
                    # (non-blocking to allow manual override if needed)
                    
            except Exception as e:
                logger.error(f"Error in causal relationship validation: {e}", exc_info=True)
                # Continue with relationship creation even if validation fails

        # Create relationship record
        relationship = RelationshipRecord(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            strength=strength,
            bidirectional=bidirectional,
            metadata=metadata,
            created_at=datetime.now(timezone.utc)
        )
        
        # Store in database
        relationship_id = self.storage.store_relationship(relationship)
        
        logger.info(
            f"Linked memory {source_id} -> {target_id} "
            f"({relation_type.value}, strength={strength})"
        )
        
        return relationship_id
    
    def xǁRelationshipManagerǁlink__mutmut_37(
        self,
        source_id: int,
        target_id: int,
        relation_type: RelationType,
        strength: float = 1.0,
        bidirectional: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Create a relationship between two memories.
        
        Args:
            source_id: ID of source memory
            target_id: ID of target memory
            relation_type: Type of relationship
            strength: Relationship strength (0.0-1.0, default: 1.0)
            bidirectional: Whether relationship goes both ways (default: False)
            metadata: Optional additional context
            
        Returns:
            ID of the created relationship
        """
        if source_id == target_id:
            raise ValueError("Cannot create relationship from memory to itself")
        
        # Verify both memories exist
        source_memory = self.storage.get_memory(source_id)
        target_memory = self.storage.get_memory(target_id)
        
        if source_memory is None:
            raise ValueError(f"Source memory {source_id} not found")
        if target_memory is None:
            raise ValueError(f"Target memory {target_id} not found")
        
        # Avoid inserting duplicate relationships: check if identical relationship exists
        existing = self.storage.get_relationships(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type
        )
        if existing:
            # If an identical relationship exists, return its id (first match)
            logger.info(
                f"Relationship already exists {source_id} -> {target_id} ({relation_type.value}), skipping insert"
            )
            return existing[0].id

        # Validate causal relationships with Z3 before creating
        if relation_type in (RelationType.CAUSES, RelationType.CAUSED_BY) and self.causal_validator:
            try:
                # Get existing relationships for validation
                all_relationships = self.storage.get_relationships()
                existing_rels = [(r.source_id, r.target_id, r.relation_type) for r in all_relationships]
                
                # Get existing memories
                existing_memories = [source_memory, target_memory]
                
                is_valid, error = self.causal_validator.validate_single_causal_relationship(
                    source_id=source_id,
                    target_id=target_id,
                    existing_memories=existing_memories
                )
                
                if not is_valid:
                    logger.warning(f"Causal relationship validation failed: {error}")
                    # Still create the relationship but log the warning
                    # (non-blocking to allow manual override if needed)
                    
            except Exception as e:
                logger.error(f"Error in causal relationship validation: {e}", exc_info=True)
                # Continue with relationship creation even if validation fails

        # Create relationship record
        relationship = RelationshipRecord(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            strength=strength,
            bidirectional=bidirectional,
            metadata=metadata,
            created_at=datetime.now(timezone.utc)
        )
        
        # Store in database
        relationship_id = self.storage.store_relationship(relationship)
        
        logger.info(
            f"Linked memory {source_id} -> {target_id} "
            f"({relation_type.value}, strength={strength})"
        )
        
        return relationship_id
    
    def xǁRelationshipManagerǁlink__mutmut_38(
        self,
        source_id: int,
        target_id: int,
        relation_type: RelationType,
        strength: float = 1.0,
        bidirectional: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Create a relationship between two memories.
        
        Args:
            source_id: ID of source memory
            target_id: ID of target memory
            relation_type: Type of relationship
            strength: Relationship strength (0.0-1.0, default: 1.0)
            bidirectional: Whether relationship goes both ways (default: False)
            metadata: Optional additional context
            
        Returns:
            ID of the created relationship
        """
        if source_id == target_id:
            raise ValueError("Cannot create relationship from memory to itself")
        
        # Verify both memories exist
        source_memory = self.storage.get_memory(source_id)
        target_memory = self.storage.get_memory(target_id)
        
        if source_memory is None:
            raise ValueError(f"Source memory {source_id} not found")
        if target_memory is None:
            raise ValueError(f"Target memory {target_id} not found")
        
        # Avoid inserting duplicate relationships: check if identical relationship exists
        existing = self.storage.get_relationships(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type
        )
        if existing:
            # If an identical relationship exists, return its id (first match)
            logger.info(
                f"Relationship already exists {source_id} -> {target_id} ({relation_type.value}), skipping insert"
            )
            return existing[0].id

        # Validate causal relationships with Z3 before creating
        if relation_type in (RelationType.CAUSES, RelationType.CAUSED_BY) and self.causal_validator:
            try:
                # Get existing relationships for validation
                all_relationships = self.storage.get_relationships()
                existing_rels = [(r.source_id, r.target_id, r.relation_type) for r in all_relationships]
                
                # Get existing memories
                existing_memories = [source_memory, target_memory]
                
                is_valid, error = self.causal_validator.validate_single_causal_relationship(
                    source_id=source_id,
                    target_id=target_id,
                    existing_relationships=existing_rels,
                    )
                
                if not is_valid:
                    logger.warning(f"Causal relationship validation failed: {error}")
                    # Still create the relationship but log the warning
                    # (non-blocking to allow manual override if needed)
                    
            except Exception as e:
                logger.error(f"Error in causal relationship validation: {e}", exc_info=True)
                # Continue with relationship creation even if validation fails

        # Create relationship record
        relationship = RelationshipRecord(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            strength=strength,
            bidirectional=bidirectional,
            metadata=metadata,
            created_at=datetime.now(timezone.utc)
        )
        
        # Store in database
        relationship_id = self.storage.store_relationship(relationship)
        
        logger.info(
            f"Linked memory {source_id} -> {target_id} "
            f"({relation_type.value}, strength={strength})"
        )
        
        return relationship_id
    
    def xǁRelationshipManagerǁlink__mutmut_39(
        self,
        source_id: int,
        target_id: int,
        relation_type: RelationType,
        strength: float = 1.0,
        bidirectional: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Create a relationship between two memories.
        
        Args:
            source_id: ID of source memory
            target_id: ID of target memory
            relation_type: Type of relationship
            strength: Relationship strength (0.0-1.0, default: 1.0)
            bidirectional: Whether relationship goes both ways (default: False)
            metadata: Optional additional context
            
        Returns:
            ID of the created relationship
        """
        if source_id == target_id:
            raise ValueError("Cannot create relationship from memory to itself")
        
        # Verify both memories exist
        source_memory = self.storage.get_memory(source_id)
        target_memory = self.storage.get_memory(target_id)
        
        if source_memory is None:
            raise ValueError(f"Source memory {source_id} not found")
        if target_memory is None:
            raise ValueError(f"Target memory {target_id} not found")
        
        # Avoid inserting duplicate relationships: check if identical relationship exists
        existing = self.storage.get_relationships(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type
        )
        if existing:
            # If an identical relationship exists, return its id (first match)
            logger.info(
                f"Relationship already exists {source_id} -> {target_id} ({relation_type.value}), skipping insert"
            )
            return existing[0].id

        # Validate causal relationships with Z3 before creating
        if relation_type in (RelationType.CAUSES, RelationType.CAUSED_BY) and self.causal_validator:
            try:
                # Get existing relationships for validation
                all_relationships = self.storage.get_relationships()
                existing_rels = [(r.source_id, r.target_id, r.relation_type) for r in all_relationships]
                
                # Get existing memories
                existing_memories = [source_memory, target_memory]
                
                is_valid, error = self.causal_validator.validate_single_causal_relationship(
                    source_id=source_id,
                    target_id=target_id,
                    existing_relationships=existing_rels,
                    existing_memories=existing_memories
                )
                
                if is_valid:
                    logger.warning(f"Causal relationship validation failed: {error}")
                    # Still create the relationship but log the warning
                    # (non-blocking to allow manual override if needed)
                    
            except Exception as e:
                logger.error(f"Error in causal relationship validation: {e}", exc_info=True)
                # Continue with relationship creation even if validation fails

        # Create relationship record
        relationship = RelationshipRecord(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            strength=strength,
            bidirectional=bidirectional,
            metadata=metadata,
            created_at=datetime.now(timezone.utc)
        )
        
        # Store in database
        relationship_id = self.storage.store_relationship(relationship)
        
        logger.info(
            f"Linked memory {source_id} -> {target_id} "
            f"({relation_type.value}, strength={strength})"
        )
        
        return relationship_id
    
    def xǁRelationshipManagerǁlink__mutmut_40(
        self,
        source_id: int,
        target_id: int,
        relation_type: RelationType,
        strength: float = 1.0,
        bidirectional: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Create a relationship between two memories.
        
        Args:
            source_id: ID of source memory
            target_id: ID of target memory
            relation_type: Type of relationship
            strength: Relationship strength (0.0-1.0, default: 1.0)
            bidirectional: Whether relationship goes both ways (default: False)
            metadata: Optional additional context
            
        Returns:
            ID of the created relationship
        """
        if source_id == target_id:
            raise ValueError("Cannot create relationship from memory to itself")
        
        # Verify both memories exist
        source_memory = self.storage.get_memory(source_id)
        target_memory = self.storage.get_memory(target_id)
        
        if source_memory is None:
            raise ValueError(f"Source memory {source_id} not found")
        if target_memory is None:
            raise ValueError(f"Target memory {target_id} not found")
        
        # Avoid inserting duplicate relationships: check if identical relationship exists
        existing = self.storage.get_relationships(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type
        )
        if existing:
            # If an identical relationship exists, return its id (first match)
            logger.info(
                f"Relationship already exists {source_id} -> {target_id} ({relation_type.value}), skipping insert"
            )
            return existing[0].id

        # Validate causal relationships with Z3 before creating
        if relation_type in (RelationType.CAUSES, RelationType.CAUSED_BY) and self.causal_validator:
            try:
                # Get existing relationships for validation
                all_relationships = self.storage.get_relationships()
                existing_rels = [(r.source_id, r.target_id, r.relation_type) for r in all_relationships]
                
                # Get existing memories
                existing_memories = [source_memory, target_memory]
                
                is_valid, error = self.causal_validator.validate_single_causal_relationship(
                    source_id=source_id,
                    target_id=target_id,
                    existing_relationships=existing_rels,
                    existing_memories=existing_memories
                )
                
                if not is_valid:
                    logger.warning(None)
                    # Still create the relationship but log the warning
                    # (non-blocking to allow manual override if needed)
                    
            except Exception as e:
                logger.error(f"Error in causal relationship validation: {e}", exc_info=True)
                # Continue with relationship creation even if validation fails

        # Create relationship record
        relationship = RelationshipRecord(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            strength=strength,
            bidirectional=bidirectional,
            metadata=metadata,
            created_at=datetime.now(timezone.utc)
        )
        
        # Store in database
        relationship_id = self.storage.store_relationship(relationship)
        
        logger.info(
            f"Linked memory {source_id} -> {target_id} "
            f"({relation_type.value}, strength={strength})"
        )
        
        return relationship_id
    
    def xǁRelationshipManagerǁlink__mutmut_41(
        self,
        source_id: int,
        target_id: int,
        relation_type: RelationType,
        strength: float = 1.0,
        bidirectional: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Create a relationship between two memories.
        
        Args:
            source_id: ID of source memory
            target_id: ID of target memory
            relation_type: Type of relationship
            strength: Relationship strength (0.0-1.0, default: 1.0)
            bidirectional: Whether relationship goes both ways (default: False)
            metadata: Optional additional context
            
        Returns:
            ID of the created relationship
        """
        if source_id == target_id:
            raise ValueError("Cannot create relationship from memory to itself")
        
        # Verify both memories exist
        source_memory = self.storage.get_memory(source_id)
        target_memory = self.storage.get_memory(target_id)
        
        if source_memory is None:
            raise ValueError(f"Source memory {source_id} not found")
        if target_memory is None:
            raise ValueError(f"Target memory {target_id} not found")
        
        # Avoid inserting duplicate relationships: check if identical relationship exists
        existing = self.storage.get_relationships(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type
        )
        if existing:
            # If an identical relationship exists, return its id (first match)
            logger.info(
                f"Relationship already exists {source_id} -> {target_id} ({relation_type.value}), skipping insert"
            )
            return existing[0].id

        # Validate causal relationships with Z3 before creating
        if relation_type in (RelationType.CAUSES, RelationType.CAUSED_BY) and self.causal_validator:
            try:
                # Get existing relationships for validation
                all_relationships = self.storage.get_relationships()
                existing_rels = [(r.source_id, r.target_id, r.relation_type) for r in all_relationships]
                
                # Get existing memories
                existing_memories = [source_memory, target_memory]
                
                is_valid, error = self.causal_validator.validate_single_causal_relationship(
                    source_id=source_id,
                    target_id=target_id,
                    existing_relationships=existing_rels,
                    existing_memories=existing_memories
                )
                
                if not is_valid:
                    logger.warning(f"Causal relationship validation failed: {error}")
                    # Still create the relationship but log the warning
                    # (non-blocking to allow manual override if needed)
                    
            except Exception as e:
                logger.error(None, exc_info=True)
                # Continue with relationship creation even if validation fails

        # Create relationship record
        relationship = RelationshipRecord(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            strength=strength,
            bidirectional=bidirectional,
            metadata=metadata,
            created_at=datetime.now(timezone.utc)
        )
        
        # Store in database
        relationship_id = self.storage.store_relationship(relationship)
        
        logger.info(
            f"Linked memory {source_id} -> {target_id} "
            f"({relation_type.value}, strength={strength})"
        )
        
        return relationship_id
    
    def xǁRelationshipManagerǁlink__mutmut_42(
        self,
        source_id: int,
        target_id: int,
        relation_type: RelationType,
        strength: float = 1.0,
        bidirectional: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Create a relationship between two memories.
        
        Args:
            source_id: ID of source memory
            target_id: ID of target memory
            relation_type: Type of relationship
            strength: Relationship strength (0.0-1.0, default: 1.0)
            bidirectional: Whether relationship goes both ways (default: False)
            metadata: Optional additional context
            
        Returns:
            ID of the created relationship
        """
        if source_id == target_id:
            raise ValueError("Cannot create relationship from memory to itself")
        
        # Verify both memories exist
        source_memory = self.storage.get_memory(source_id)
        target_memory = self.storage.get_memory(target_id)
        
        if source_memory is None:
            raise ValueError(f"Source memory {source_id} not found")
        if target_memory is None:
            raise ValueError(f"Target memory {target_id} not found")
        
        # Avoid inserting duplicate relationships: check if identical relationship exists
        existing = self.storage.get_relationships(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type
        )
        if existing:
            # If an identical relationship exists, return its id (first match)
            logger.info(
                f"Relationship already exists {source_id} -> {target_id} ({relation_type.value}), skipping insert"
            )
            return existing[0].id

        # Validate causal relationships with Z3 before creating
        if relation_type in (RelationType.CAUSES, RelationType.CAUSED_BY) and self.causal_validator:
            try:
                # Get existing relationships for validation
                all_relationships = self.storage.get_relationships()
                existing_rels = [(r.source_id, r.target_id, r.relation_type) for r in all_relationships]
                
                # Get existing memories
                existing_memories = [source_memory, target_memory]
                
                is_valid, error = self.causal_validator.validate_single_causal_relationship(
                    source_id=source_id,
                    target_id=target_id,
                    existing_relationships=existing_rels,
                    existing_memories=existing_memories
                )
                
                if not is_valid:
                    logger.warning(f"Causal relationship validation failed: {error}")
                    # Still create the relationship but log the warning
                    # (non-blocking to allow manual override if needed)
                    
            except Exception as e:
                logger.error(f"Error in causal relationship validation: {e}", exc_info=None)
                # Continue with relationship creation even if validation fails

        # Create relationship record
        relationship = RelationshipRecord(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            strength=strength,
            bidirectional=bidirectional,
            metadata=metadata,
            created_at=datetime.now(timezone.utc)
        )
        
        # Store in database
        relationship_id = self.storage.store_relationship(relationship)
        
        logger.info(
            f"Linked memory {source_id} -> {target_id} "
            f"({relation_type.value}, strength={strength})"
        )
        
        return relationship_id
    
    def xǁRelationshipManagerǁlink__mutmut_43(
        self,
        source_id: int,
        target_id: int,
        relation_type: RelationType,
        strength: float = 1.0,
        bidirectional: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Create a relationship between two memories.
        
        Args:
            source_id: ID of source memory
            target_id: ID of target memory
            relation_type: Type of relationship
            strength: Relationship strength (0.0-1.0, default: 1.0)
            bidirectional: Whether relationship goes both ways (default: False)
            metadata: Optional additional context
            
        Returns:
            ID of the created relationship
        """
        if source_id == target_id:
            raise ValueError("Cannot create relationship from memory to itself")
        
        # Verify both memories exist
        source_memory = self.storage.get_memory(source_id)
        target_memory = self.storage.get_memory(target_id)
        
        if source_memory is None:
            raise ValueError(f"Source memory {source_id} not found")
        if target_memory is None:
            raise ValueError(f"Target memory {target_id} not found")
        
        # Avoid inserting duplicate relationships: check if identical relationship exists
        existing = self.storage.get_relationships(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type
        )
        if existing:
            # If an identical relationship exists, return its id (first match)
            logger.info(
                f"Relationship already exists {source_id} -> {target_id} ({relation_type.value}), skipping insert"
            )
            return existing[0].id

        # Validate causal relationships with Z3 before creating
        if relation_type in (RelationType.CAUSES, RelationType.CAUSED_BY) and self.causal_validator:
            try:
                # Get existing relationships for validation
                all_relationships = self.storage.get_relationships()
                existing_rels = [(r.source_id, r.target_id, r.relation_type) for r in all_relationships]
                
                # Get existing memories
                existing_memories = [source_memory, target_memory]
                
                is_valid, error = self.causal_validator.validate_single_causal_relationship(
                    source_id=source_id,
                    target_id=target_id,
                    existing_relationships=existing_rels,
                    existing_memories=existing_memories
                )
                
                if not is_valid:
                    logger.warning(f"Causal relationship validation failed: {error}")
                    # Still create the relationship but log the warning
                    # (non-blocking to allow manual override if needed)
                    
            except Exception as e:
                logger.error(exc_info=True)
                # Continue with relationship creation even if validation fails

        # Create relationship record
        relationship = RelationshipRecord(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            strength=strength,
            bidirectional=bidirectional,
            metadata=metadata,
            created_at=datetime.now(timezone.utc)
        )
        
        # Store in database
        relationship_id = self.storage.store_relationship(relationship)
        
        logger.info(
            f"Linked memory {source_id} -> {target_id} "
            f"({relation_type.value}, strength={strength})"
        )
        
        return relationship_id
    
    def xǁRelationshipManagerǁlink__mutmut_44(
        self,
        source_id: int,
        target_id: int,
        relation_type: RelationType,
        strength: float = 1.0,
        bidirectional: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Create a relationship between two memories.
        
        Args:
            source_id: ID of source memory
            target_id: ID of target memory
            relation_type: Type of relationship
            strength: Relationship strength (0.0-1.0, default: 1.0)
            bidirectional: Whether relationship goes both ways (default: False)
            metadata: Optional additional context
            
        Returns:
            ID of the created relationship
        """
        if source_id == target_id:
            raise ValueError("Cannot create relationship from memory to itself")
        
        # Verify both memories exist
        source_memory = self.storage.get_memory(source_id)
        target_memory = self.storage.get_memory(target_id)
        
        if source_memory is None:
            raise ValueError(f"Source memory {source_id} not found")
        if target_memory is None:
            raise ValueError(f"Target memory {target_id} not found")
        
        # Avoid inserting duplicate relationships: check if identical relationship exists
        existing = self.storage.get_relationships(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type
        )
        if existing:
            # If an identical relationship exists, return its id (first match)
            logger.info(
                f"Relationship already exists {source_id} -> {target_id} ({relation_type.value}), skipping insert"
            )
            return existing[0].id

        # Validate causal relationships with Z3 before creating
        if relation_type in (RelationType.CAUSES, RelationType.CAUSED_BY) and self.causal_validator:
            try:
                # Get existing relationships for validation
                all_relationships = self.storage.get_relationships()
                existing_rels = [(r.source_id, r.target_id, r.relation_type) for r in all_relationships]
                
                # Get existing memories
                existing_memories = [source_memory, target_memory]
                
                is_valid, error = self.causal_validator.validate_single_causal_relationship(
                    source_id=source_id,
                    target_id=target_id,
                    existing_relationships=existing_rels,
                    existing_memories=existing_memories
                )
                
                if not is_valid:
                    logger.warning(f"Causal relationship validation failed: {error}")
                    # Still create the relationship but log the warning
                    # (non-blocking to allow manual override if needed)
                    
            except Exception as e:
                logger.error(f"Error in causal relationship validation: {e}", )
                # Continue with relationship creation even if validation fails

        # Create relationship record
        relationship = RelationshipRecord(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            strength=strength,
            bidirectional=bidirectional,
            metadata=metadata,
            created_at=datetime.now(timezone.utc)
        )
        
        # Store in database
        relationship_id = self.storage.store_relationship(relationship)
        
        logger.info(
            f"Linked memory {source_id} -> {target_id} "
            f"({relation_type.value}, strength={strength})"
        )
        
        return relationship_id
    
    def xǁRelationshipManagerǁlink__mutmut_45(
        self,
        source_id: int,
        target_id: int,
        relation_type: RelationType,
        strength: float = 1.0,
        bidirectional: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Create a relationship between two memories.
        
        Args:
            source_id: ID of source memory
            target_id: ID of target memory
            relation_type: Type of relationship
            strength: Relationship strength (0.0-1.0, default: 1.0)
            bidirectional: Whether relationship goes both ways (default: False)
            metadata: Optional additional context
            
        Returns:
            ID of the created relationship
        """
        if source_id == target_id:
            raise ValueError("Cannot create relationship from memory to itself")
        
        # Verify both memories exist
        source_memory = self.storage.get_memory(source_id)
        target_memory = self.storage.get_memory(target_id)
        
        if source_memory is None:
            raise ValueError(f"Source memory {source_id} not found")
        if target_memory is None:
            raise ValueError(f"Target memory {target_id} not found")
        
        # Avoid inserting duplicate relationships: check if identical relationship exists
        existing = self.storage.get_relationships(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type
        )
        if existing:
            # If an identical relationship exists, return its id (first match)
            logger.info(
                f"Relationship already exists {source_id} -> {target_id} ({relation_type.value}), skipping insert"
            )
            return existing[0].id

        # Validate causal relationships with Z3 before creating
        if relation_type in (RelationType.CAUSES, RelationType.CAUSED_BY) and self.causal_validator:
            try:
                # Get existing relationships for validation
                all_relationships = self.storage.get_relationships()
                existing_rels = [(r.source_id, r.target_id, r.relation_type) for r in all_relationships]
                
                # Get existing memories
                existing_memories = [source_memory, target_memory]
                
                is_valid, error = self.causal_validator.validate_single_causal_relationship(
                    source_id=source_id,
                    target_id=target_id,
                    existing_relationships=existing_rels,
                    existing_memories=existing_memories
                )
                
                if not is_valid:
                    logger.warning(f"Causal relationship validation failed: {error}")
                    # Still create the relationship but log the warning
                    # (non-blocking to allow manual override if needed)
                    
            except Exception as e:
                logger.error(f"Error in causal relationship validation: {e}", exc_info=False)
                # Continue with relationship creation even if validation fails

        # Create relationship record
        relationship = RelationshipRecord(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            strength=strength,
            bidirectional=bidirectional,
            metadata=metadata,
            created_at=datetime.now(timezone.utc)
        )
        
        # Store in database
        relationship_id = self.storage.store_relationship(relationship)
        
        logger.info(
            f"Linked memory {source_id} -> {target_id} "
            f"({relation_type.value}, strength={strength})"
        )
        
        return relationship_id
    
    def xǁRelationshipManagerǁlink__mutmut_46(
        self,
        source_id: int,
        target_id: int,
        relation_type: RelationType,
        strength: float = 1.0,
        bidirectional: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Create a relationship between two memories.
        
        Args:
            source_id: ID of source memory
            target_id: ID of target memory
            relation_type: Type of relationship
            strength: Relationship strength (0.0-1.0, default: 1.0)
            bidirectional: Whether relationship goes both ways (default: False)
            metadata: Optional additional context
            
        Returns:
            ID of the created relationship
        """
        if source_id == target_id:
            raise ValueError("Cannot create relationship from memory to itself")
        
        # Verify both memories exist
        source_memory = self.storage.get_memory(source_id)
        target_memory = self.storage.get_memory(target_id)
        
        if source_memory is None:
            raise ValueError(f"Source memory {source_id} not found")
        if target_memory is None:
            raise ValueError(f"Target memory {target_id} not found")
        
        # Avoid inserting duplicate relationships: check if identical relationship exists
        existing = self.storage.get_relationships(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type
        )
        if existing:
            # If an identical relationship exists, return its id (first match)
            logger.info(
                f"Relationship already exists {source_id} -> {target_id} ({relation_type.value}), skipping insert"
            )
            return existing[0].id

        # Validate causal relationships with Z3 before creating
        if relation_type in (RelationType.CAUSES, RelationType.CAUSED_BY) and self.causal_validator:
            try:
                # Get existing relationships for validation
                all_relationships = self.storage.get_relationships()
                existing_rels = [(r.source_id, r.target_id, r.relation_type) for r in all_relationships]
                
                # Get existing memories
                existing_memories = [source_memory, target_memory]
                
                is_valid, error = self.causal_validator.validate_single_causal_relationship(
                    source_id=source_id,
                    target_id=target_id,
                    existing_relationships=existing_rels,
                    existing_memories=existing_memories
                )
                
                if not is_valid:
                    logger.warning(f"Causal relationship validation failed: {error}")
                    # Still create the relationship but log the warning
                    # (non-blocking to allow manual override if needed)
                    
            except Exception as e:
                logger.error(f"Error in causal relationship validation: {e}", exc_info=True)
                # Continue with relationship creation even if validation fails

        # Create relationship record
        relationship = None
        
        # Store in database
        relationship_id = self.storage.store_relationship(relationship)
        
        logger.info(
            f"Linked memory {source_id} -> {target_id} "
            f"({relation_type.value}, strength={strength})"
        )
        
        return relationship_id
    
    def xǁRelationshipManagerǁlink__mutmut_47(
        self,
        source_id: int,
        target_id: int,
        relation_type: RelationType,
        strength: float = 1.0,
        bidirectional: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Create a relationship between two memories.
        
        Args:
            source_id: ID of source memory
            target_id: ID of target memory
            relation_type: Type of relationship
            strength: Relationship strength (0.0-1.0, default: 1.0)
            bidirectional: Whether relationship goes both ways (default: False)
            metadata: Optional additional context
            
        Returns:
            ID of the created relationship
        """
        if source_id == target_id:
            raise ValueError("Cannot create relationship from memory to itself")
        
        # Verify both memories exist
        source_memory = self.storage.get_memory(source_id)
        target_memory = self.storage.get_memory(target_id)
        
        if source_memory is None:
            raise ValueError(f"Source memory {source_id} not found")
        if target_memory is None:
            raise ValueError(f"Target memory {target_id} not found")
        
        # Avoid inserting duplicate relationships: check if identical relationship exists
        existing = self.storage.get_relationships(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type
        )
        if existing:
            # If an identical relationship exists, return its id (first match)
            logger.info(
                f"Relationship already exists {source_id} -> {target_id} ({relation_type.value}), skipping insert"
            )
            return existing[0].id

        # Validate causal relationships with Z3 before creating
        if relation_type in (RelationType.CAUSES, RelationType.CAUSED_BY) and self.causal_validator:
            try:
                # Get existing relationships for validation
                all_relationships = self.storage.get_relationships()
                existing_rels = [(r.source_id, r.target_id, r.relation_type) for r in all_relationships]
                
                # Get existing memories
                existing_memories = [source_memory, target_memory]
                
                is_valid, error = self.causal_validator.validate_single_causal_relationship(
                    source_id=source_id,
                    target_id=target_id,
                    existing_relationships=existing_rels,
                    existing_memories=existing_memories
                )
                
                if not is_valid:
                    logger.warning(f"Causal relationship validation failed: {error}")
                    # Still create the relationship but log the warning
                    # (non-blocking to allow manual override if needed)
                    
            except Exception as e:
                logger.error(f"Error in causal relationship validation: {e}", exc_info=True)
                # Continue with relationship creation even if validation fails

        # Create relationship record
        relationship = RelationshipRecord(
            source_id=None,
            target_id=target_id,
            relation_type=relation_type,
            strength=strength,
            bidirectional=bidirectional,
            metadata=metadata,
            created_at=datetime.now(timezone.utc)
        )
        
        # Store in database
        relationship_id = self.storage.store_relationship(relationship)
        
        logger.info(
            f"Linked memory {source_id} -> {target_id} "
            f"({relation_type.value}, strength={strength})"
        )
        
        return relationship_id
    
    def xǁRelationshipManagerǁlink__mutmut_48(
        self,
        source_id: int,
        target_id: int,
        relation_type: RelationType,
        strength: float = 1.0,
        bidirectional: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Create a relationship between two memories.
        
        Args:
            source_id: ID of source memory
            target_id: ID of target memory
            relation_type: Type of relationship
            strength: Relationship strength (0.0-1.0, default: 1.0)
            bidirectional: Whether relationship goes both ways (default: False)
            metadata: Optional additional context
            
        Returns:
            ID of the created relationship
        """
        if source_id == target_id:
            raise ValueError("Cannot create relationship from memory to itself")
        
        # Verify both memories exist
        source_memory = self.storage.get_memory(source_id)
        target_memory = self.storage.get_memory(target_id)
        
        if source_memory is None:
            raise ValueError(f"Source memory {source_id} not found")
        if target_memory is None:
            raise ValueError(f"Target memory {target_id} not found")
        
        # Avoid inserting duplicate relationships: check if identical relationship exists
        existing = self.storage.get_relationships(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type
        )
        if existing:
            # If an identical relationship exists, return its id (first match)
            logger.info(
                f"Relationship already exists {source_id} -> {target_id} ({relation_type.value}), skipping insert"
            )
            return existing[0].id

        # Validate causal relationships with Z3 before creating
        if relation_type in (RelationType.CAUSES, RelationType.CAUSED_BY) and self.causal_validator:
            try:
                # Get existing relationships for validation
                all_relationships = self.storage.get_relationships()
                existing_rels = [(r.source_id, r.target_id, r.relation_type) for r in all_relationships]
                
                # Get existing memories
                existing_memories = [source_memory, target_memory]
                
                is_valid, error = self.causal_validator.validate_single_causal_relationship(
                    source_id=source_id,
                    target_id=target_id,
                    existing_relationships=existing_rels,
                    existing_memories=existing_memories
                )
                
                if not is_valid:
                    logger.warning(f"Causal relationship validation failed: {error}")
                    # Still create the relationship but log the warning
                    # (non-blocking to allow manual override if needed)
                    
            except Exception as e:
                logger.error(f"Error in causal relationship validation: {e}", exc_info=True)
                # Continue with relationship creation even if validation fails

        # Create relationship record
        relationship = RelationshipRecord(
            source_id=source_id,
            target_id=None,
            relation_type=relation_type,
            strength=strength,
            bidirectional=bidirectional,
            metadata=metadata,
            created_at=datetime.now(timezone.utc)
        )
        
        # Store in database
        relationship_id = self.storage.store_relationship(relationship)
        
        logger.info(
            f"Linked memory {source_id} -> {target_id} "
            f"({relation_type.value}, strength={strength})"
        )
        
        return relationship_id
    
    def xǁRelationshipManagerǁlink__mutmut_49(
        self,
        source_id: int,
        target_id: int,
        relation_type: RelationType,
        strength: float = 1.0,
        bidirectional: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Create a relationship between two memories.
        
        Args:
            source_id: ID of source memory
            target_id: ID of target memory
            relation_type: Type of relationship
            strength: Relationship strength (0.0-1.0, default: 1.0)
            bidirectional: Whether relationship goes both ways (default: False)
            metadata: Optional additional context
            
        Returns:
            ID of the created relationship
        """
        if source_id == target_id:
            raise ValueError("Cannot create relationship from memory to itself")
        
        # Verify both memories exist
        source_memory = self.storage.get_memory(source_id)
        target_memory = self.storage.get_memory(target_id)
        
        if source_memory is None:
            raise ValueError(f"Source memory {source_id} not found")
        if target_memory is None:
            raise ValueError(f"Target memory {target_id} not found")
        
        # Avoid inserting duplicate relationships: check if identical relationship exists
        existing = self.storage.get_relationships(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type
        )
        if existing:
            # If an identical relationship exists, return its id (first match)
            logger.info(
                f"Relationship already exists {source_id} -> {target_id} ({relation_type.value}), skipping insert"
            )
            return existing[0].id

        # Validate causal relationships with Z3 before creating
        if relation_type in (RelationType.CAUSES, RelationType.CAUSED_BY) and self.causal_validator:
            try:
                # Get existing relationships for validation
                all_relationships = self.storage.get_relationships()
                existing_rels = [(r.source_id, r.target_id, r.relation_type) for r in all_relationships]
                
                # Get existing memories
                existing_memories = [source_memory, target_memory]
                
                is_valid, error = self.causal_validator.validate_single_causal_relationship(
                    source_id=source_id,
                    target_id=target_id,
                    existing_relationships=existing_rels,
                    existing_memories=existing_memories
                )
                
                if not is_valid:
                    logger.warning(f"Causal relationship validation failed: {error}")
                    # Still create the relationship but log the warning
                    # (non-blocking to allow manual override if needed)
                    
            except Exception as e:
                logger.error(f"Error in causal relationship validation: {e}", exc_info=True)
                # Continue with relationship creation even if validation fails

        # Create relationship record
        relationship = RelationshipRecord(
            source_id=source_id,
            target_id=target_id,
            relation_type=None,
            strength=strength,
            bidirectional=bidirectional,
            metadata=metadata,
            created_at=datetime.now(timezone.utc)
        )
        
        # Store in database
        relationship_id = self.storage.store_relationship(relationship)
        
        logger.info(
            f"Linked memory {source_id} -> {target_id} "
            f"({relation_type.value}, strength={strength})"
        )
        
        return relationship_id
    
    def xǁRelationshipManagerǁlink__mutmut_50(
        self,
        source_id: int,
        target_id: int,
        relation_type: RelationType,
        strength: float = 1.0,
        bidirectional: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Create a relationship between two memories.
        
        Args:
            source_id: ID of source memory
            target_id: ID of target memory
            relation_type: Type of relationship
            strength: Relationship strength (0.0-1.0, default: 1.0)
            bidirectional: Whether relationship goes both ways (default: False)
            metadata: Optional additional context
            
        Returns:
            ID of the created relationship
        """
        if source_id == target_id:
            raise ValueError("Cannot create relationship from memory to itself")
        
        # Verify both memories exist
        source_memory = self.storage.get_memory(source_id)
        target_memory = self.storage.get_memory(target_id)
        
        if source_memory is None:
            raise ValueError(f"Source memory {source_id} not found")
        if target_memory is None:
            raise ValueError(f"Target memory {target_id} not found")
        
        # Avoid inserting duplicate relationships: check if identical relationship exists
        existing = self.storage.get_relationships(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type
        )
        if existing:
            # If an identical relationship exists, return its id (first match)
            logger.info(
                f"Relationship already exists {source_id} -> {target_id} ({relation_type.value}), skipping insert"
            )
            return existing[0].id

        # Validate causal relationships with Z3 before creating
        if relation_type in (RelationType.CAUSES, RelationType.CAUSED_BY) and self.causal_validator:
            try:
                # Get existing relationships for validation
                all_relationships = self.storage.get_relationships()
                existing_rels = [(r.source_id, r.target_id, r.relation_type) for r in all_relationships]
                
                # Get existing memories
                existing_memories = [source_memory, target_memory]
                
                is_valid, error = self.causal_validator.validate_single_causal_relationship(
                    source_id=source_id,
                    target_id=target_id,
                    existing_relationships=existing_rels,
                    existing_memories=existing_memories
                )
                
                if not is_valid:
                    logger.warning(f"Causal relationship validation failed: {error}")
                    # Still create the relationship but log the warning
                    # (non-blocking to allow manual override if needed)
                    
            except Exception as e:
                logger.error(f"Error in causal relationship validation: {e}", exc_info=True)
                # Continue with relationship creation even if validation fails

        # Create relationship record
        relationship = RelationshipRecord(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            strength=None,
            bidirectional=bidirectional,
            metadata=metadata,
            created_at=datetime.now(timezone.utc)
        )
        
        # Store in database
        relationship_id = self.storage.store_relationship(relationship)
        
        logger.info(
            f"Linked memory {source_id} -> {target_id} "
            f"({relation_type.value}, strength={strength})"
        )
        
        return relationship_id
    
    def xǁRelationshipManagerǁlink__mutmut_51(
        self,
        source_id: int,
        target_id: int,
        relation_type: RelationType,
        strength: float = 1.0,
        bidirectional: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Create a relationship between two memories.
        
        Args:
            source_id: ID of source memory
            target_id: ID of target memory
            relation_type: Type of relationship
            strength: Relationship strength (0.0-1.0, default: 1.0)
            bidirectional: Whether relationship goes both ways (default: False)
            metadata: Optional additional context
            
        Returns:
            ID of the created relationship
        """
        if source_id == target_id:
            raise ValueError("Cannot create relationship from memory to itself")
        
        # Verify both memories exist
        source_memory = self.storage.get_memory(source_id)
        target_memory = self.storage.get_memory(target_id)
        
        if source_memory is None:
            raise ValueError(f"Source memory {source_id} not found")
        if target_memory is None:
            raise ValueError(f"Target memory {target_id} not found")
        
        # Avoid inserting duplicate relationships: check if identical relationship exists
        existing = self.storage.get_relationships(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type
        )
        if existing:
            # If an identical relationship exists, return its id (first match)
            logger.info(
                f"Relationship already exists {source_id} -> {target_id} ({relation_type.value}), skipping insert"
            )
            return existing[0].id

        # Validate causal relationships with Z3 before creating
        if relation_type in (RelationType.CAUSES, RelationType.CAUSED_BY) and self.causal_validator:
            try:
                # Get existing relationships for validation
                all_relationships = self.storage.get_relationships()
                existing_rels = [(r.source_id, r.target_id, r.relation_type) for r in all_relationships]
                
                # Get existing memories
                existing_memories = [source_memory, target_memory]
                
                is_valid, error = self.causal_validator.validate_single_causal_relationship(
                    source_id=source_id,
                    target_id=target_id,
                    existing_relationships=existing_rels,
                    existing_memories=existing_memories
                )
                
                if not is_valid:
                    logger.warning(f"Causal relationship validation failed: {error}")
                    # Still create the relationship but log the warning
                    # (non-blocking to allow manual override if needed)
                    
            except Exception as e:
                logger.error(f"Error in causal relationship validation: {e}", exc_info=True)
                # Continue with relationship creation even if validation fails

        # Create relationship record
        relationship = RelationshipRecord(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            strength=strength,
            bidirectional=None,
            metadata=metadata,
            created_at=datetime.now(timezone.utc)
        )
        
        # Store in database
        relationship_id = self.storage.store_relationship(relationship)
        
        logger.info(
            f"Linked memory {source_id} -> {target_id} "
            f"({relation_type.value}, strength={strength})"
        )
        
        return relationship_id
    
    def xǁRelationshipManagerǁlink__mutmut_52(
        self,
        source_id: int,
        target_id: int,
        relation_type: RelationType,
        strength: float = 1.0,
        bidirectional: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Create a relationship between two memories.
        
        Args:
            source_id: ID of source memory
            target_id: ID of target memory
            relation_type: Type of relationship
            strength: Relationship strength (0.0-1.0, default: 1.0)
            bidirectional: Whether relationship goes both ways (default: False)
            metadata: Optional additional context
            
        Returns:
            ID of the created relationship
        """
        if source_id == target_id:
            raise ValueError("Cannot create relationship from memory to itself")
        
        # Verify both memories exist
        source_memory = self.storage.get_memory(source_id)
        target_memory = self.storage.get_memory(target_id)
        
        if source_memory is None:
            raise ValueError(f"Source memory {source_id} not found")
        if target_memory is None:
            raise ValueError(f"Target memory {target_id} not found")
        
        # Avoid inserting duplicate relationships: check if identical relationship exists
        existing = self.storage.get_relationships(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type
        )
        if existing:
            # If an identical relationship exists, return its id (first match)
            logger.info(
                f"Relationship already exists {source_id} -> {target_id} ({relation_type.value}), skipping insert"
            )
            return existing[0].id

        # Validate causal relationships with Z3 before creating
        if relation_type in (RelationType.CAUSES, RelationType.CAUSED_BY) and self.causal_validator:
            try:
                # Get existing relationships for validation
                all_relationships = self.storage.get_relationships()
                existing_rels = [(r.source_id, r.target_id, r.relation_type) for r in all_relationships]
                
                # Get existing memories
                existing_memories = [source_memory, target_memory]
                
                is_valid, error = self.causal_validator.validate_single_causal_relationship(
                    source_id=source_id,
                    target_id=target_id,
                    existing_relationships=existing_rels,
                    existing_memories=existing_memories
                )
                
                if not is_valid:
                    logger.warning(f"Causal relationship validation failed: {error}")
                    # Still create the relationship but log the warning
                    # (non-blocking to allow manual override if needed)
                    
            except Exception as e:
                logger.error(f"Error in causal relationship validation: {e}", exc_info=True)
                # Continue with relationship creation even if validation fails

        # Create relationship record
        relationship = RelationshipRecord(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            strength=strength,
            bidirectional=bidirectional,
            metadata=None,
            created_at=datetime.now(timezone.utc)
        )
        
        # Store in database
        relationship_id = self.storage.store_relationship(relationship)
        
        logger.info(
            f"Linked memory {source_id} -> {target_id} "
            f"({relation_type.value}, strength={strength})"
        )
        
        return relationship_id
    
    def xǁRelationshipManagerǁlink__mutmut_53(
        self,
        source_id: int,
        target_id: int,
        relation_type: RelationType,
        strength: float = 1.0,
        bidirectional: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Create a relationship between two memories.
        
        Args:
            source_id: ID of source memory
            target_id: ID of target memory
            relation_type: Type of relationship
            strength: Relationship strength (0.0-1.0, default: 1.0)
            bidirectional: Whether relationship goes both ways (default: False)
            metadata: Optional additional context
            
        Returns:
            ID of the created relationship
        """
        if source_id == target_id:
            raise ValueError("Cannot create relationship from memory to itself")
        
        # Verify both memories exist
        source_memory = self.storage.get_memory(source_id)
        target_memory = self.storage.get_memory(target_id)
        
        if source_memory is None:
            raise ValueError(f"Source memory {source_id} not found")
        if target_memory is None:
            raise ValueError(f"Target memory {target_id} not found")
        
        # Avoid inserting duplicate relationships: check if identical relationship exists
        existing = self.storage.get_relationships(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type
        )
        if existing:
            # If an identical relationship exists, return its id (first match)
            logger.info(
                f"Relationship already exists {source_id} -> {target_id} ({relation_type.value}), skipping insert"
            )
            return existing[0].id

        # Validate causal relationships with Z3 before creating
        if relation_type in (RelationType.CAUSES, RelationType.CAUSED_BY) and self.causal_validator:
            try:
                # Get existing relationships for validation
                all_relationships = self.storage.get_relationships()
                existing_rels = [(r.source_id, r.target_id, r.relation_type) for r in all_relationships]
                
                # Get existing memories
                existing_memories = [source_memory, target_memory]
                
                is_valid, error = self.causal_validator.validate_single_causal_relationship(
                    source_id=source_id,
                    target_id=target_id,
                    existing_relationships=existing_rels,
                    existing_memories=existing_memories
                )
                
                if not is_valid:
                    logger.warning(f"Causal relationship validation failed: {error}")
                    # Still create the relationship but log the warning
                    # (non-blocking to allow manual override if needed)
                    
            except Exception as e:
                logger.error(f"Error in causal relationship validation: {e}", exc_info=True)
                # Continue with relationship creation even if validation fails

        # Create relationship record
        relationship = RelationshipRecord(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            strength=strength,
            bidirectional=bidirectional,
            metadata=metadata,
            created_at=None
        )
        
        # Store in database
        relationship_id = self.storage.store_relationship(relationship)
        
        logger.info(
            f"Linked memory {source_id} -> {target_id} "
            f"({relation_type.value}, strength={strength})"
        )
        
        return relationship_id
    
    def xǁRelationshipManagerǁlink__mutmut_54(
        self,
        source_id: int,
        target_id: int,
        relation_type: RelationType,
        strength: float = 1.0,
        bidirectional: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Create a relationship between two memories.
        
        Args:
            source_id: ID of source memory
            target_id: ID of target memory
            relation_type: Type of relationship
            strength: Relationship strength (0.0-1.0, default: 1.0)
            bidirectional: Whether relationship goes both ways (default: False)
            metadata: Optional additional context
            
        Returns:
            ID of the created relationship
        """
        if source_id == target_id:
            raise ValueError("Cannot create relationship from memory to itself")
        
        # Verify both memories exist
        source_memory = self.storage.get_memory(source_id)
        target_memory = self.storage.get_memory(target_id)
        
        if source_memory is None:
            raise ValueError(f"Source memory {source_id} not found")
        if target_memory is None:
            raise ValueError(f"Target memory {target_id} not found")
        
        # Avoid inserting duplicate relationships: check if identical relationship exists
        existing = self.storage.get_relationships(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type
        )
        if existing:
            # If an identical relationship exists, return its id (first match)
            logger.info(
                f"Relationship already exists {source_id} -> {target_id} ({relation_type.value}), skipping insert"
            )
            return existing[0].id

        # Validate causal relationships with Z3 before creating
        if relation_type in (RelationType.CAUSES, RelationType.CAUSED_BY) and self.causal_validator:
            try:
                # Get existing relationships for validation
                all_relationships = self.storage.get_relationships()
                existing_rels = [(r.source_id, r.target_id, r.relation_type) for r in all_relationships]
                
                # Get existing memories
                existing_memories = [source_memory, target_memory]
                
                is_valid, error = self.causal_validator.validate_single_causal_relationship(
                    source_id=source_id,
                    target_id=target_id,
                    existing_relationships=existing_rels,
                    existing_memories=existing_memories
                )
                
                if not is_valid:
                    logger.warning(f"Causal relationship validation failed: {error}")
                    # Still create the relationship but log the warning
                    # (non-blocking to allow manual override if needed)
                    
            except Exception as e:
                logger.error(f"Error in causal relationship validation: {e}", exc_info=True)
                # Continue with relationship creation even if validation fails

        # Create relationship record
        relationship = RelationshipRecord(
            target_id=target_id,
            relation_type=relation_type,
            strength=strength,
            bidirectional=bidirectional,
            metadata=metadata,
            created_at=datetime.now(timezone.utc)
        )
        
        # Store in database
        relationship_id = self.storage.store_relationship(relationship)
        
        logger.info(
            f"Linked memory {source_id} -> {target_id} "
            f"({relation_type.value}, strength={strength})"
        )
        
        return relationship_id
    
    def xǁRelationshipManagerǁlink__mutmut_55(
        self,
        source_id: int,
        target_id: int,
        relation_type: RelationType,
        strength: float = 1.0,
        bidirectional: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Create a relationship between two memories.
        
        Args:
            source_id: ID of source memory
            target_id: ID of target memory
            relation_type: Type of relationship
            strength: Relationship strength (0.0-1.0, default: 1.0)
            bidirectional: Whether relationship goes both ways (default: False)
            metadata: Optional additional context
            
        Returns:
            ID of the created relationship
        """
        if source_id == target_id:
            raise ValueError("Cannot create relationship from memory to itself")
        
        # Verify both memories exist
        source_memory = self.storage.get_memory(source_id)
        target_memory = self.storage.get_memory(target_id)
        
        if source_memory is None:
            raise ValueError(f"Source memory {source_id} not found")
        if target_memory is None:
            raise ValueError(f"Target memory {target_id} not found")
        
        # Avoid inserting duplicate relationships: check if identical relationship exists
        existing = self.storage.get_relationships(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type
        )
        if existing:
            # If an identical relationship exists, return its id (first match)
            logger.info(
                f"Relationship already exists {source_id} -> {target_id} ({relation_type.value}), skipping insert"
            )
            return existing[0].id

        # Validate causal relationships with Z3 before creating
        if relation_type in (RelationType.CAUSES, RelationType.CAUSED_BY) and self.causal_validator:
            try:
                # Get existing relationships for validation
                all_relationships = self.storage.get_relationships()
                existing_rels = [(r.source_id, r.target_id, r.relation_type) for r in all_relationships]
                
                # Get existing memories
                existing_memories = [source_memory, target_memory]
                
                is_valid, error = self.causal_validator.validate_single_causal_relationship(
                    source_id=source_id,
                    target_id=target_id,
                    existing_relationships=existing_rels,
                    existing_memories=existing_memories
                )
                
                if not is_valid:
                    logger.warning(f"Causal relationship validation failed: {error}")
                    # Still create the relationship but log the warning
                    # (non-blocking to allow manual override if needed)
                    
            except Exception as e:
                logger.error(f"Error in causal relationship validation: {e}", exc_info=True)
                # Continue with relationship creation even if validation fails

        # Create relationship record
        relationship = RelationshipRecord(
            source_id=source_id,
            relation_type=relation_type,
            strength=strength,
            bidirectional=bidirectional,
            metadata=metadata,
            created_at=datetime.now(timezone.utc)
        )
        
        # Store in database
        relationship_id = self.storage.store_relationship(relationship)
        
        logger.info(
            f"Linked memory {source_id} -> {target_id} "
            f"({relation_type.value}, strength={strength})"
        )
        
        return relationship_id
    
    def xǁRelationshipManagerǁlink__mutmut_56(
        self,
        source_id: int,
        target_id: int,
        relation_type: RelationType,
        strength: float = 1.0,
        bidirectional: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Create a relationship between two memories.
        
        Args:
            source_id: ID of source memory
            target_id: ID of target memory
            relation_type: Type of relationship
            strength: Relationship strength (0.0-1.0, default: 1.0)
            bidirectional: Whether relationship goes both ways (default: False)
            metadata: Optional additional context
            
        Returns:
            ID of the created relationship
        """
        if source_id == target_id:
            raise ValueError("Cannot create relationship from memory to itself")
        
        # Verify both memories exist
        source_memory = self.storage.get_memory(source_id)
        target_memory = self.storage.get_memory(target_id)
        
        if source_memory is None:
            raise ValueError(f"Source memory {source_id} not found")
        if target_memory is None:
            raise ValueError(f"Target memory {target_id} not found")
        
        # Avoid inserting duplicate relationships: check if identical relationship exists
        existing = self.storage.get_relationships(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type
        )
        if existing:
            # If an identical relationship exists, return its id (first match)
            logger.info(
                f"Relationship already exists {source_id} -> {target_id} ({relation_type.value}), skipping insert"
            )
            return existing[0].id

        # Validate causal relationships with Z3 before creating
        if relation_type in (RelationType.CAUSES, RelationType.CAUSED_BY) and self.causal_validator:
            try:
                # Get existing relationships for validation
                all_relationships = self.storage.get_relationships()
                existing_rels = [(r.source_id, r.target_id, r.relation_type) for r in all_relationships]
                
                # Get existing memories
                existing_memories = [source_memory, target_memory]
                
                is_valid, error = self.causal_validator.validate_single_causal_relationship(
                    source_id=source_id,
                    target_id=target_id,
                    existing_relationships=existing_rels,
                    existing_memories=existing_memories
                )
                
                if not is_valid:
                    logger.warning(f"Causal relationship validation failed: {error}")
                    # Still create the relationship but log the warning
                    # (non-blocking to allow manual override if needed)
                    
            except Exception as e:
                logger.error(f"Error in causal relationship validation: {e}", exc_info=True)
                # Continue with relationship creation even if validation fails

        # Create relationship record
        relationship = RelationshipRecord(
            source_id=source_id,
            target_id=target_id,
            strength=strength,
            bidirectional=bidirectional,
            metadata=metadata,
            created_at=datetime.now(timezone.utc)
        )
        
        # Store in database
        relationship_id = self.storage.store_relationship(relationship)
        
        logger.info(
            f"Linked memory {source_id} -> {target_id} "
            f"({relation_type.value}, strength={strength})"
        )
        
        return relationship_id
    
    def xǁRelationshipManagerǁlink__mutmut_57(
        self,
        source_id: int,
        target_id: int,
        relation_type: RelationType,
        strength: float = 1.0,
        bidirectional: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Create a relationship between two memories.
        
        Args:
            source_id: ID of source memory
            target_id: ID of target memory
            relation_type: Type of relationship
            strength: Relationship strength (0.0-1.0, default: 1.0)
            bidirectional: Whether relationship goes both ways (default: False)
            metadata: Optional additional context
            
        Returns:
            ID of the created relationship
        """
        if source_id == target_id:
            raise ValueError("Cannot create relationship from memory to itself")
        
        # Verify both memories exist
        source_memory = self.storage.get_memory(source_id)
        target_memory = self.storage.get_memory(target_id)
        
        if source_memory is None:
            raise ValueError(f"Source memory {source_id} not found")
        if target_memory is None:
            raise ValueError(f"Target memory {target_id} not found")
        
        # Avoid inserting duplicate relationships: check if identical relationship exists
        existing = self.storage.get_relationships(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type
        )
        if existing:
            # If an identical relationship exists, return its id (first match)
            logger.info(
                f"Relationship already exists {source_id} -> {target_id} ({relation_type.value}), skipping insert"
            )
            return existing[0].id

        # Validate causal relationships with Z3 before creating
        if relation_type in (RelationType.CAUSES, RelationType.CAUSED_BY) and self.causal_validator:
            try:
                # Get existing relationships for validation
                all_relationships = self.storage.get_relationships()
                existing_rels = [(r.source_id, r.target_id, r.relation_type) for r in all_relationships]
                
                # Get existing memories
                existing_memories = [source_memory, target_memory]
                
                is_valid, error = self.causal_validator.validate_single_causal_relationship(
                    source_id=source_id,
                    target_id=target_id,
                    existing_relationships=existing_rels,
                    existing_memories=existing_memories
                )
                
                if not is_valid:
                    logger.warning(f"Causal relationship validation failed: {error}")
                    # Still create the relationship but log the warning
                    # (non-blocking to allow manual override if needed)
                    
            except Exception as e:
                logger.error(f"Error in causal relationship validation: {e}", exc_info=True)
                # Continue with relationship creation even if validation fails

        # Create relationship record
        relationship = RelationshipRecord(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            bidirectional=bidirectional,
            metadata=metadata,
            created_at=datetime.now(timezone.utc)
        )
        
        # Store in database
        relationship_id = self.storage.store_relationship(relationship)
        
        logger.info(
            f"Linked memory {source_id} -> {target_id} "
            f"({relation_type.value}, strength={strength})"
        )
        
        return relationship_id
    
    def xǁRelationshipManagerǁlink__mutmut_58(
        self,
        source_id: int,
        target_id: int,
        relation_type: RelationType,
        strength: float = 1.0,
        bidirectional: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Create a relationship between two memories.
        
        Args:
            source_id: ID of source memory
            target_id: ID of target memory
            relation_type: Type of relationship
            strength: Relationship strength (0.0-1.0, default: 1.0)
            bidirectional: Whether relationship goes both ways (default: False)
            metadata: Optional additional context
            
        Returns:
            ID of the created relationship
        """
        if source_id == target_id:
            raise ValueError("Cannot create relationship from memory to itself")
        
        # Verify both memories exist
        source_memory = self.storage.get_memory(source_id)
        target_memory = self.storage.get_memory(target_id)
        
        if source_memory is None:
            raise ValueError(f"Source memory {source_id} not found")
        if target_memory is None:
            raise ValueError(f"Target memory {target_id} not found")
        
        # Avoid inserting duplicate relationships: check if identical relationship exists
        existing = self.storage.get_relationships(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type
        )
        if existing:
            # If an identical relationship exists, return its id (first match)
            logger.info(
                f"Relationship already exists {source_id} -> {target_id} ({relation_type.value}), skipping insert"
            )
            return existing[0].id

        # Validate causal relationships with Z3 before creating
        if relation_type in (RelationType.CAUSES, RelationType.CAUSED_BY) and self.causal_validator:
            try:
                # Get existing relationships for validation
                all_relationships = self.storage.get_relationships()
                existing_rels = [(r.source_id, r.target_id, r.relation_type) for r in all_relationships]
                
                # Get existing memories
                existing_memories = [source_memory, target_memory]
                
                is_valid, error = self.causal_validator.validate_single_causal_relationship(
                    source_id=source_id,
                    target_id=target_id,
                    existing_relationships=existing_rels,
                    existing_memories=existing_memories
                )
                
                if not is_valid:
                    logger.warning(f"Causal relationship validation failed: {error}")
                    # Still create the relationship but log the warning
                    # (non-blocking to allow manual override if needed)
                    
            except Exception as e:
                logger.error(f"Error in causal relationship validation: {e}", exc_info=True)
                # Continue with relationship creation even if validation fails

        # Create relationship record
        relationship = RelationshipRecord(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            strength=strength,
            metadata=metadata,
            created_at=datetime.now(timezone.utc)
        )
        
        # Store in database
        relationship_id = self.storage.store_relationship(relationship)
        
        logger.info(
            f"Linked memory {source_id} -> {target_id} "
            f"({relation_type.value}, strength={strength})"
        )
        
        return relationship_id
    
    def xǁRelationshipManagerǁlink__mutmut_59(
        self,
        source_id: int,
        target_id: int,
        relation_type: RelationType,
        strength: float = 1.0,
        bidirectional: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Create a relationship between two memories.
        
        Args:
            source_id: ID of source memory
            target_id: ID of target memory
            relation_type: Type of relationship
            strength: Relationship strength (0.0-1.0, default: 1.0)
            bidirectional: Whether relationship goes both ways (default: False)
            metadata: Optional additional context
            
        Returns:
            ID of the created relationship
        """
        if source_id == target_id:
            raise ValueError("Cannot create relationship from memory to itself")
        
        # Verify both memories exist
        source_memory = self.storage.get_memory(source_id)
        target_memory = self.storage.get_memory(target_id)
        
        if source_memory is None:
            raise ValueError(f"Source memory {source_id} not found")
        if target_memory is None:
            raise ValueError(f"Target memory {target_id} not found")
        
        # Avoid inserting duplicate relationships: check if identical relationship exists
        existing = self.storage.get_relationships(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type
        )
        if existing:
            # If an identical relationship exists, return its id (first match)
            logger.info(
                f"Relationship already exists {source_id} -> {target_id} ({relation_type.value}), skipping insert"
            )
            return existing[0].id

        # Validate causal relationships with Z3 before creating
        if relation_type in (RelationType.CAUSES, RelationType.CAUSED_BY) and self.causal_validator:
            try:
                # Get existing relationships for validation
                all_relationships = self.storage.get_relationships()
                existing_rels = [(r.source_id, r.target_id, r.relation_type) for r in all_relationships]
                
                # Get existing memories
                existing_memories = [source_memory, target_memory]
                
                is_valid, error = self.causal_validator.validate_single_causal_relationship(
                    source_id=source_id,
                    target_id=target_id,
                    existing_relationships=existing_rels,
                    existing_memories=existing_memories
                )
                
                if not is_valid:
                    logger.warning(f"Causal relationship validation failed: {error}")
                    # Still create the relationship but log the warning
                    # (non-blocking to allow manual override if needed)
                    
            except Exception as e:
                logger.error(f"Error in causal relationship validation: {e}", exc_info=True)
                # Continue with relationship creation even if validation fails

        # Create relationship record
        relationship = RelationshipRecord(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            strength=strength,
            bidirectional=bidirectional,
            created_at=datetime.now(timezone.utc)
        )
        
        # Store in database
        relationship_id = self.storage.store_relationship(relationship)
        
        logger.info(
            f"Linked memory {source_id} -> {target_id} "
            f"({relation_type.value}, strength={strength})"
        )
        
        return relationship_id
    
    def xǁRelationshipManagerǁlink__mutmut_60(
        self,
        source_id: int,
        target_id: int,
        relation_type: RelationType,
        strength: float = 1.0,
        bidirectional: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Create a relationship between two memories.
        
        Args:
            source_id: ID of source memory
            target_id: ID of target memory
            relation_type: Type of relationship
            strength: Relationship strength (0.0-1.0, default: 1.0)
            bidirectional: Whether relationship goes both ways (default: False)
            metadata: Optional additional context
            
        Returns:
            ID of the created relationship
        """
        if source_id == target_id:
            raise ValueError("Cannot create relationship from memory to itself")
        
        # Verify both memories exist
        source_memory = self.storage.get_memory(source_id)
        target_memory = self.storage.get_memory(target_id)
        
        if source_memory is None:
            raise ValueError(f"Source memory {source_id} not found")
        if target_memory is None:
            raise ValueError(f"Target memory {target_id} not found")
        
        # Avoid inserting duplicate relationships: check if identical relationship exists
        existing = self.storage.get_relationships(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type
        )
        if existing:
            # If an identical relationship exists, return its id (first match)
            logger.info(
                f"Relationship already exists {source_id} -> {target_id} ({relation_type.value}), skipping insert"
            )
            return existing[0].id

        # Validate causal relationships with Z3 before creating
        if relation_type in (RelationType.CAUSES, RelationType.CAUSED_BY) and self.causal_validator:
            try:
                # Get existing relationships for validation
                all_relationships = self.storage.get_relationships()
                existing_rels = [(r.source_id, r.target_id, r.relation_type) for r in all_relationships]
                
                # Get existing memories
                existing_memories = [source_memory, target_memory]
                
                is_valid, error = self.causal_validator.validate_single_causal_relationship(
                    source_id=source_id,
                    target_id=target_id,
                    existing_relationships=existing_rels,
                    existing_memories=existing_memories
                )
                
                if not is_valid:
                    logger.warning(f"Causal relationship validation failed: {error}")
                    # Still create the relationship but log the warning
                    # (non-blocking to allow manual override if needed)
                    
            except Exception as e:
                logger.error(f"Error in causal relationship validation: {e}", exc_info=True)
                # Continue with relationship creation even if validation fails

        # Create relationship record
        relationship = RelationshipRecord(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            strength=strength,
            bidirectional=bidirectional,
            metadata=metadata,
            )
        
        # Store in database
        relationship_id = self.storage.store_relationship(relationship)
        
        logger.info(
            f"Linked memory {source_id} -> {target_id} "
            f"({relation_type.value}, strength={strength})"
        )
        
        return relationship_id
    
    def xǁRelationshipManagerǁlink__mutmut_61(
        self,
        source_id: int,
        target_id: int,
        relation_type: RelationType,
        strength: float = 1.0,
        bidirectional: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Create a relationship between two memories.
        
        Args:
            source_id: ID of source memory
            target_id: ID of target memory
            relation_type: Type of relationship
            strength: Relationship strength (0.0-1.0, default: 1.0)
            bidirectional: Whether relationship goes both ways (default: False)
            metadata: Optional additional context
            
        Returns:
            ID of the created relationship
        """
        if source_id == target_id:
            raise ValueError("Cannot create relationship from memory to itself")
        
        # Verify both memories exist
        source_memory = self.storage.get_memory(source_id)
        target_memory = self.storage.get_memory(target_id)
        
        if source_memory is None:
            raise ValueError(f"Source memory {source_id} not found")
        if target_memory is None:
            raise ValueError(f"Target memory {target_id} not found")
        
        # Avoid inserting duplicate relationships: check if identical relationship exists
        existing = self.storage.get_relationships(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type
        )
        if existing:
            # If an identical relationship exists, return its id (first match)
            logger.info(
                f"Relationship already exists {source_id} -> {target_id} ({relation_type.value}), skipping insert"
            )
            return existing[0].id

        # Validate causal relationships with Z3 before creating
        if relation_type in (RelationType.CAUSES, RelationType.CAUSED_BY) and self.causal_validator:
            try:
                # Get existing relationships for validation
                all_relationships = self.storage.get_relationships()
                existing_rels = [(r.source_id, r.target_id, r.relation_type) for r in all_relationships]
                
                # Get existing memories
                existing_memories = [source_memory, target_memory]
                
                is_valid, error = self.causal_validator.validate_single_causal_relationship(
                    source_id=source_id,
                    target_id=target_id,
                    existing_relationships=existing_rels,
                    existing_memories=existing_memories
                )
                
                if not is_valid:
                    logger.warning(f"Causal relationship validation failed: {error}")
                    # Still create the relationship but log the warning
                    # (non-blocking to allow manual override if needed)
                    
            except Exception as e:
                logger.error(f"Error in causal relationship validation: {e}", exc_info=True)
                # Continue with relationship creation even if validation fails

        # Create relationship record
        relationship = RelationshipRecord(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            strength=strength,
            bidirectional=bidirectional,
            metadata=metadata,
            created_at=datetime.now(None)
        )
        
        # Store in database
        relationship_id = self.storage.store_relationship(relationship)
        
        logger.info(
            f"Linked memory {source_id} -> {target_id} "
            f"({relation_type.value}, strength={strength})"
        )
        
        return relationship_id
    
    def xǁRelationshipManagerǁlink__mutmut_62(
        self,
        source_id: int,
        target_id: int,
        relation_type: RelationType,
        strength: float = 1.0,
        bidirectional: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Create a relationship between two memories.
        
        Args:
            source_id: ID of source memory
            target_id: ID of target memory
            relation_type: Type of relationship
            strength: Relationship strength (0.0-1.0, default: 1.0)
            bidirectional: Whether relationship goes both ways (default: False)
            metadata: Optional additional context
            
        Returns:
            ID of the created relationship
        """
        if source_id == target_id:
            raise ValueError("Cannot create relationship from memory to itself")
        
        # Verify both memories exist
        source_memory = self.storage.get_memory(source_id)
        target_memory = self.storage.get_memory(target_id)
        
        if source_memory is None:
            raise ValueError(f"Source memory {source_id} not found")
        if target_memory is None:
            raise ValueError(f"Target memory {target_id} not found")
        
        # Avoid inserting duplicate relationships: check if identical relationship exists
        existing = self.storage.get_relationships(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type
        )
        if existing:
            # If an identical relationship exists, return its id (first match)
            logger.info(
                f"Relationship already exists {source_id} -> {target_id} ({relation_type.value}), skipping insert"
            )
            return existing[0].id

        # Validate causal relationships with Z3 before creating
        if relation_type in (RelationType.CAUSES, RelationType.CAUSED_BY) and self.causal_validator:
            try:
                # Get existing relationships for validation
                all_relationships = self.storage.get_relationships()
                existing_rels = [(r.source_id, r.target_id, r.relation_type) for r in all_relationships]
                
                # Get existing memories
                existing_memories = [source_memory, target_memory]
                
                is_valid, error = self.causal_validator.validate_single_causal_relationship(
                    source_id=source_id,
                    target_id=target_id,
                    existing_relationships=existing_rels,
                    existing_memories=existing_memories
                )
                
                if not is_valid:
                    logger.warning(f"Causal relationship validation failed: {error}")
                    # Still create the relationship but log the warning
                    # (non-blocking to allow manual override if needed)
                    
            except Exception as e:
                logger.error(f"Error in causal relationship validation: {e}", exc_info=True)
                # Continue with relationship creation even if validation fails

        # Create relationship record
        relationship = RelationshipRecord(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            strength=strength,
            bidirectional=bidirectional,
            metadata=metadata,
            created_at=datetime.now(timezone.utc)
        )
        
        # Store in database
        relationship_id = None
        
        logger.info(
            f"Linked memory {source_id} -> {target_id} "
            f"({relation_type.value}, strength={strength})"
        )
        
        return relationship_id
    
    def xǁRelationshipManagerǁlink__mutmut_63(
        self,
        source_id: int,
        target_id: int,
        relation_type: RelationType,
        strength: float = 1.0,
        bidirectional: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Create a relationship between two memories.
        
        Args:
            source_id: ID of source memory
            target_id: ID of target memory
            relation_type: Type of relationship
            strength: Relationship strength (0.0-1.0, default: 1.0)
            bidirectional: Whether relationship goes both ways (default: False)
            metadata: Optional additional context
            
        Returns:
            ID of the created relationship
        """
        if source_id == target_id:
            raise ValueError("Cannot create relationship from memory to itself")
        
        # Verify both memories exist
        source_memory = self.storage.get_memory(source_id)
        target_memory = self.storage.get_memory(target_id)
        
        if source_memory is None:
            raise ValueError(f"Source memory {source_id} not found")
        if target_memory is None:
            raise ValueError(f"Target memory {target_id} not found")
        
        # Avoid inserting duplicate relationships: check if identical relationship exists
        existing = self.storage.get_relationships(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type
        )
        if existing:
            # If an identical relationship exists, return its id (first match)
            logger.info(
                f"Relationship already exists {source_id} -> {target_id} ({relation_type.value}), skipping insert"
            )
            return existing[0].id

        # Validate causal relationships with Z3 before creating
        if relation_type in (RelationType.CAUSES, RelationType.CAUSED_BY) and self.causal_validator:
            try:
                # Get existing relationships for validation
                all_relationships = self.storage.get_relationships()
                existing_rels = [(r.source_id, r.target_id, r.relation_type) for r in all_relationships]
                
                # Get existing memories
                existing_memories = [source_memory, target_memory]
                
                is_valid, error = self.causal_validator.validate_single_causal_relationship(
                    source_id=source_id,
                    target_id=target_id,
                    existing_relationships=existing_rels,
                    existing_memories=existing_memories
                )
                
                if not is_valid:
                    logger.warning(f"Causal relationship validation failed: {error}")
                    # Still create the relationship but log the warning
                    # (non-blocking to allow manual override if needed)
                    
            except Exception as e:
                logger.error(f"Error in causal relationship validation: {e}", exc_info=True)
                # Continue with relationship creation even if validation fails

        # Create relationship record
        relationship = RelationshipRecord(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            strength=strength,
            bidirectional=bidirectional,
            metadata=metadata,
            created_at=datetime.now(timezone.utc)
        )
        
        # Store in database
        relationship_id = self.storage.store_relationship(None)
        
        logger.info(
            f"Linked memory {source_id} -> {target_id} "
            f"({relation_type.value}, strength={strength})"
        )
        
        return relationship_id
    
    def xǁRelationshipManagerǁlink__mutmut_64(
        self,
        source_id: int,
        target_id: int,
        relation_type: RelationType,
        strength: float = 1.0,
        bidirectional: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Create a relationship between two memories.
        
        Args:
            source_id: ID of source memory
            target_id: ID of target memory
            relation_type: Type of relationship
            strength: Relationship strength (0.0-1.0, default: 1.0)
            bidirectional: Whether relationship goes both ways (default: False)
            metadata: Optional additional context
            
        Returns:
            ID of the created relationship
        """
        if source_id == target_id:
            raise ValueError("Cannot create relationship from memory to itself")
        
        # Verify both memories exist
        source_memory = self.storage.get_memory(source_id)
        target_memory = self.storage.get_memory(target_id)
        
        if source_memory is None:
            raise ValueError(f"Source memory {source_id} not found")
        if target_memory is None:
            raise ValueError(f"Target memory {target_id} not found")
        
        # Avoid inserting duplicate relationships: check if identical relationship exists
        existing = self.storage.get_relationships(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type
        )
        if existing:
            # If an identical relationship exists, return its id (first match)
            logger.info(
                f"Relationship already exists {source_id} -> {target_id} ({relation_type.value}), skipping insert"
            )
            return existing[0].id

        # Validate causal relationships with Z3 before creating
        if relation_type in (RelationType.CAUSES, RelationType.CAUSED_BY) and self.causal_validator:
            try:
                # Get existing relationships for validation
                all_relationships = self.storage.get_relationships()
                existing_rels = [(r.source_id, r.target_id, r.relation_type) for r in all_relationships]
                
                # Get existing memories
                existing_memories = [source_memory, target_memory]
                
                is_valid, error = self.causal_validator.validate_single_causal_relationship(
                    source_id=source_id,
                    target_id=target_id,
                    existing_relationships=existing_rels,
                    existing_memories=existing_memories
                )
                
                if not is_valid:
                    logger.warning(f"Causal relationship validation failed: {error}")
                    # Still create the relationship but log the warning
                    # (non-blocking to allow manual override if needed)
                    
            except Exception as e:
                logger.error(f"Error in causal relationship validation: {e}", exc_info=True)
                # Continue with relationship creation even if validation fails

        # Create relationship record
        relationship = RelationshipRecord(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            strength=strength,
            bidirectional=bidirectional,
            metadata=metadata,
            created_at=datetime.now(timezone.utc)
        )
        
        # Store in database
        relationship_id = self.storage.store_relationship(relationship)
        
        logger.info(
            None
        )
        
        return relationship_id
    
    xǁRelationshipManagerǁlink__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁRelationshipManagerǁlink__mutmut_1': xǁRelationshipManagerǁlink__mutmut_1, 
        'xǁRelationshipManagerǁlink__mutmut_2': xǁRelationshipManagerǁlink__mutmut_2, 
        'xǁRelationshipManagerǁlink__mutmut_3': xǁRelationshipManagerǁlink__mutmut_3, 
        'xǁRelationshipManagerǁlink__mutmut_4': xǁRelationshipManagerǁlink__mutmut_4, 
        'xǁRelationshipManagerǁlink__mutmut_5': xǁRelationshipManagerǁlink__mutmut_5, 
        'xǁRelationshipManagerǁlink__mutmut_6': xǁRelationshipManagerǁlink__mutmut_6, 
        'xǁRelationshipManagerǁlink__mutmut_7': xǁRelationshipManagerǁlink__mutmut_7, 
        'xǁRelationshipManagerǁlink__mutmut_8': xǁRelationshipManagerǁlink__mutmut_8, 
        'xǁRelationshipManagerǁlink__mutmut_9': xǁRelationshipManagerǁlink__mutmut_9, 
        'xǁRelationshipManagerǁlink__mutmut_10': xǁRelationshipManagerǁlink__mutmut_10, 
        'xǁRelationshipManagerǁlink__mutmut_11': xǁRelationshipManagerǁlink__mutmut_11, 
        'xǁRelationshipManagerǁlink__mutmut_12': xǁRelationshipManagerǁlink__mutmut_12, 
        'xǁRelationshipManagerǁlink__mutmut_13': xǁRelationshipManagerǁlink__mutmut_13, 
        'xǁRelationshipManagerǁlink__mutmut_14': xǁRelationshipManagerǁlink__mutmut_14, 
        'xǁRelationshipManagerǁlink__mutmut_15': xǁRelationshipManagerǁlink__mutmut_15, 
        'xǁRelationshipManagerǁlink__mutmut_16': xǁRelationshipManagerǁlink__mutmut_16, 
        'xǁRelationshipManagerǁlink__mutmut_17': xǁRelationshipManagerǁlink__mutmut_17, 
        'xǁRelationshipManagerǁlink__mutmut_18': xǁRelationshipManagerǁlink__mutmut_18, 
        'xǁRelationshipManagerǁlink__mutmut_19': xǁRelationshipManagerǁlink__mutmut_19, 
        'xǁRelationshipManagerǁlink__mutmut_20': xǁRelationshipManagerǁlink__mutmut_20, 
        'xǁRelationshipManagerǁlink__mutmut_21': xǁRelationshipManagerǁlink__mutmut_21, 
        'xǁRelationshipManagerǁlink__mutmut_22': xǁRelationshipManagerǁlink__mutmut_22, 
        'xǁRelationshipManagerǁlink__mutmut_23': xǁRelationshipManagerǁlink__mutmut_23, 
        'xǁRelationshipManagerǁlink__mutmut_24': xǁRelationshipManagerǁlink__mutmut_24, 
        'xǁRelationshipManagerǁlink__mutmut_25': xǁRelationshipManagerǁlink__mutmut_25, 
        'xǁRelationshipManagerǁlink__mutmut_26': xǁRelationshipManagerǁlink__mutmut_26, 
        'xǁRelationshipManagerǁlink__mutmut_27': xǁRelationshipManagerǁlink__mutmut_27, 
        'xǁRelationshipManagerǁlink__mutmut_28': xǁRelationshipManagerǁlink__mutmut_28, 
        'xǁRelationshipManagerǁlink__mutmut_29': xǁRelationshipManagerǁlink__mutmut_29, 
        'xǁRelationshipManagerǁlink__mutmut_30': xǁRelationshipManagerǁlink__mutmut_30, 
        'xǁRelationshipManagerǁlink__mutmut_31': xǁRelationshipManagerǁlink__mutmut_31, 
        'xǁRelationshipManagerǁlink__mutmut_32': xǁRelationshipManagerǁlink__mutmut_32, 
        'xǁRelationshipManagerǁlink__mutmut_33': xǁRelationshipManagerǁlink__mutmut_33, 
        'xǁRelationshipManagerǁlink__mutmut_34': xǁRelationshipManagerǁlink__mutmut_34, 
        'xǁRelationshipManagerǁlink__mutmut_35': xǁRelationshipManagerǁlink__mutmut_35, 
        'xǁRelationshipManagerǁlink__mutmut_36': xǁRelationshipManagerǁlink__mutmut_36, 
        'xǁRelationshipManagerǁlink__mutmut_37': xǁRelationshipManagerǁlink__mutmut_37, 
        'xǁRelationshipManagerǁlink__mutmut_38': xǁRelationshipManagerǁlink__mutmut_38, 
        'xǁRelationshipManagerǁlink__mutmut_39': xǁRelationshipManagerǁlink__mutmut_39, 
        'xǁRelationshipManagerǁlink__mutmut_40': xǁRelationshipManagerǁlink__mutmut_40, 
        'xǁRelationshipManagerǁlink__mutmut_41': xǁRelationshipManagerǁlink__mutmut_41, 
        'xǁRelationshipManagerǁlink__mutmut_42': xǁRelationshipManagerǁlink__mutmut_42, 
        'xǁRelationshipManagerǁlink__mutmut_43': xǁRelationshipManagerǁlink__mutmut_43, 
        'xǁRelationshipManagerǁlink__mutmut_44': xǁRelationshipManagerǁlink__mutmut_44, 
        'xǁRelationshipManagerǁlink__mutmut_45': xǁRelationshipManagerǁlink__mutmut_45, 
        'xǁRelationshipManagerǁlink__mutmut_46': xǁRelationshipManagerǁlink__mutmut_46, 
        'xǁRelationshipManagerǁlink__mutmut_47': xǁRelationshipManagerǁlink__mutmut_47, 
        'xǁRelationshipManagerǁlink__mutmut_48': xǁRelationshipManagerǁlink__mutmut_48, 
        'xǁRelationshipManagerǁlink__mutmut_49': xǁRelationshipManagerǁlink__mutmut_49, 
        'xǁRelationshipManagerǁlink__mutmut_50': xǁRelationshipManagerǁlink__mutmut_50, 
        'xǁRelationshipManagerǁlink__mutmut_51': xǁRelationshipManagerǁlink__mutmut_51, 
        'xǁRelationshipManagerǁlink__mutmut_52': xǁRelationshipManagerǁlink__mutmut_52, 
        'xǁRelationshipManagerǁlink__mutmut_53': xǁRelationshipManagerǁlink__mutmut_53, 
        'xǁRelationshipManagerǁlink__mutmut_54': xǁRelationshipManagerǁlink__mutmut_54, 
        'xǁRelationshipManagerǁlink__mutmut_55': xǁRelationshipManagerǁlink__mutmut_55, 
        'xǁRelationshipManagerǁlink__mutmut_56': xǁRelationshipManagerǁlink__mutmut_56, 
        'xǁRelationshipManagerǁlink__mutmut_57': xǁRelationshipManagerǁlink__mutmut_57, 
        'xǁRelationshipManagerǁlink__mutmut_58': xǁRelationshipManagerǁlink__mutmut_58, 
        'xǁRelationshipManagerǁlink__mutmut_59': xǁRelationshipManagerǁlink__mutmut_59, 
        'xǁRelationshipManagerǁlink__mutmut_60': xǁRelationshipManagerǁlink__mutmut_60, 
        'xǁRelationshipManagerǁlink__mutmut_61': xǁRelationshipManagerǁlink__mutmut_61, 
        'xǁRelationshipManagerǁlink__mutmut_62': xǁRelationshipManagerǁlink__mutmut_62, 
        'xǁRelationshipManagerǁlink__mutmut_63': xǁRelationshipManagerǁlink__mutmut_63, 
        'xǁRelationshipManagerǁlink__mutmut_64': xǁRelationshipManagerǁlink__mutmut_64
    }
    
    def link(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁRelationshipManagerǁlink__mutmut_orig"), object.__getattribute__(self, "xǁRelationshipManagerǁlink__mutmut_mutants"), args, kwargs, self)
        return result 
    
    link.__signature__ = _mutmut_signature(xǁRelationshipManagerǁlink__mutmut_orig)
    xǁRelationshipManagerǁlink__mutmut_orig.__name__ = 'xǁRelationshipManagerǁlink'
    
    def xǁRelationshipManagerǁunlink__mutmut_orig(
        self,
        source_id: int,
        target_id: int,
        relation_type: Optional[RelationType] = None
    ) -> bool:
        """
        Remove relationship(s) between two memories.
        
        Args:
            source_id: ID of source memory
            target_id: ID of target memory
            relation_type: Optional specific relationship type to remove.
                          If None, removes all relationships between the memories.
            
        Returns:
            True if any relationships were removed, False otherwise
        """
        if relation_type is not None:
            # Remove specific relationship type
            relationships = self.storage.get_relationships(
                source_id=source_id,
                target_id=target_id,
                relation_type=relation_type
            )
        else:
            # Remove all relationships between these memories
            relationships = self.storage.get_relationships(
                source_id=source_id,
                target_id=target_id
            )
        
        if not relationships:
            return False
        
        # Delete all found relationships
        success = False
        for rel in relationships:
            if rel.id:
                deleted = self.storage.delete_relationship(rel.id)
                if deleted:
                    success = True
        
        if success:
            logger.info(
                f"Unlinked memory {source_id} -> {target_id} "
                f"({relation_type.value if relation_type else 'all types'})"
            )
        
        return success
    
    def xǁRelationshipManagerǁunlink__mutmut_1(
        self,
        source_id: int,
        target_id: int,
        relation_type: Optional[RelationType] = None
    ) -> bool:
        """
        Remove relationship(s) between two memories.
        
        Args:
            source_id: ID of source memory
            target_id: ID of target memory
            relation_type: Optional specific relationship type to remove.
                          If None, removes all relationships between the memories.
            
        Returns:
            True if any relationships were removed, False otherwise
        """
        if relation_type is None:
            # Remove specific relationship type
            relationships = self.storage.get_relationships(
                source_id=source_id,
                target_id=target_id,
                relation_type=relation_type
            )
        else:
            # Remove all relationships between these memories
            relationships = self.storage.get_relationships(
                source_id=source_id,
                target_id=target_id
            )
        
        if not relationships:
            return False
        
        # Delete all found relationships
        success = False
        for rel in relationships:
            if rel.id:
                deleted = self.storage.delete_relationship(rel.id)
                if deleted:
                    success = True
        
        if success:
            logger.info(
                f"Unlinked memory {source_id} -> {target_id} "
                f"({relation_type.value if relation_type else 'all types'})"
            )
        
        return success
    
    def xǁRelationshipManagerǁunlink__mutmut_2(
        self,
        source_id: int,
        target_id: int,
        relation_type: Optional[RelationType] = None
    ) -> bool:
        """
        Remove relationship(s) between two memories.
        
        Args:
            source_id: ID of source memory
            target_id: ID of target memory
            relation_type: Optional specific relationship type to remove.
                          If None, removes all relationships between the memories.
            
        Returns:
            True if any relationships were removed, False otherwise
        """
        if relation_type is not None:
            # Remove specific relationship type
            relationships = None
        else:
            # Remove all relationships between these memories
            relationships = self.storage.get_relationships(
                source_id=source_id,
                target_id=target_id
            )
        
        if not relationships:
            return False
        
        # Delete all found relationships
        success = False
        for rel in relationships:
            if rel.id:
                deleted = self.storage.delete_relationship(rel.id)
                if deleted:
                    success = True
        
        if success:
            logger.info(
                f"Unlinked memory {source_id} -> {target_id} "
                f"({relation_type.value if relation_type else 'all types'})"
            )
        
        return success
    
    def xǁRelationshipManagerǁunlink__mutmut_3(
        self,
        source_id: int,
        target_id: int,
        relation_type: Optional[RelationType] = None
    ) -> bool:
        """
        Remove relationship(s) between two memories.
        
        Args:
            source_id: ID of source memory
            target_id: ID of target memory
            relation_type: Optional specific relationship type to remove.
                          If None, removes all relationships between the memories.
            
        Returns:
            True if any relationships were removed, False otherwise
        """
        if relation_type is not None:
            # Remove specific relationship type
            relationships = self.storage.get_relationships(
                source_id=None,
                target_id=target_id,
                relation_type=relation_type
            )
        else:
            # Remove all relationships between these memories
            relationships = self.storage.get_relationships(
                source_id=source_id,
                target_id=target_id
            )
        
        if not relationships:
            return False
        
        # Delete all found relationships
        success = False
        for rel in relationships:
            if rel.id:
                deleted = self.storage.delete_relationship(rel.id)
                if deleted:
                    success = True
        
        if success:
            logger.info(
                f"Unlinked memory {source_id} -> {target_id} "
                f"({relation_type.value if relation_type else 'all types'})"
            )
        
        return success
    
    def xǁRelationshipManagerǁunlink__mutmut_4(
        self,
        source_id: int,
        target_id: int,
        relation_type: Optional[RelationType] = None
    ) -> bool:
        """
        Remove relationship(s) between two memories.
        
        Args:
            source_id: ID of source memory
            target_id: ID of target memory
            relation_type: Optional specific relationship type to remove.
                          If None, removes all relationships between the memories.
            
        Returns:
            True if any relationships were removed, False otherwise
        """
        if relation_type is not None:
            # Remove specific relationship type
            relationships = self.storage.get_relationships(
                source_id=source_id,
                target_id=None,
                relation_type=relation_type
            )
        else:
            # Remove all relationships between these memories
            relationships = self.storage.get_relationships(
                source_id=source_id,
                target_id=target_id
            )
        
        if not relationships:
            return False
        
        # Delete all found relationships
        success = False
        for rel in relationships:
            if rel.id:
                deleted = self.storage.delete_relationship(rel.id)
                if deleted:
                    success = True
        
        if success:
            logger.info(
                f"Unlinked memory {source_id} -> {target_id} "
                f"({relation_type.value if relation_type else 'all types'})"
            )
        
        return success
    
    def xǁRelationshipManagerǁunlink__mutmut_5(
        self,
        source_id: int,
        target_id: int,
        relation_type: Optional[RelationType] = None
    ) -> bool:
        """
        Remove relationship(s) between two memories.
        
        Args:
            source_id: ID of source memory
            target_id: ID of target memory
            relation_type: Optional specific relationship type to remove.
                          If None, removes all relationships between the memories.
            
        Returns:
            True if any relationships were removed, False otherwise
        """
        if relation_type is not None:
            # Remove specific relationship type
            relationships = self.storage.get_relationships(
                source_id=source_id,
                target_id=target_id,
                relation_type=None
            )
        else:
            # Remove all relationships between these memories
            relationships = self.storage.get_relationships(
                source_id=source_id,
                target_id=target_id
            )
        
        if not relationships:
            return False
        
        # Delete all found relationships
        success = False
        for rel in relationships:
            if rel.id:
                deleted = self.storage.delete_relationship(rel.id)
                if deleted:
                    success = True
        
        if success:
            logger.info(
                f"Unlinked memory {source_id} -> {target_id} "
                f"({relation_type.value if relation_type else 'all types'})"
            )
        
        return success
    
    def xǁRelationshipManagerǁunlink__mutmut_6(
        self,
        source_id: int,
        target_id: int,
        relation_type: Optional[RelationType] = None
    ) -> bool:
        """
        Remove relationship(s) between two memories.
        
        Args:
            source_id: ID of source memory
            target_id: ID of target memory
            relation_type: Optional specific relationship type to remove.
                          If None, removes all relationships between the memories.
            
        Returns:
            True if any relationships were removed, False otherwise
        """
        if relation_type is not None:
            # Remove specific relationship type
            relationships = self.storage.get_relationships(
                target_id=target_id,
                relation_type=relation_type
            )
        else:
            # Remove all relationships between these memories
            relationships = self.storage.get_relationships(
                source_id=source_id,
                target_id=target_id
            )
        
        if not relationships:
            return False
        
        # Delete all found relationships
        success = False
        for rel in relationships:
            if rel.id:
                deleted = self.storage.delete_relationship(rel.id)
                if deleted:
                    success = True
        
        if success:
            logger.info(
                f"Unlinked memory {source_id} -> {target_id} "
                f"({relation_type.value if relation_type else 'all types'})"
            )
        
        return success
    
    def xǁRelationshipManagerǁunlink__mutmut_7(
        self,
        source_id: int,
        target_id: int,
        relation_type: Optional[RelationType] = None
    ) -> bool:
        """
        Remove relationship(s) between two memories.
        
        Args:
            source_id: ID of source memory
            target_id: ID of target memory
            relation_type: Optional specific relationship type to remove.
                          If None, removes all relationships between the memories.
            
        Returns:
            True if any relationships were removed, False otherwise
        """
        if relation_type is not None:
            # Remove specific relationship type
            relationships = self.storage.get_relationships(
                source_id=source_id,
                relation_type=relation_type
            )
        else:
            # Remove all relationships between these memories
            relationships = self.storage.get_relationships(
                source_id=source_id,
                target_id=target_id
            )
        
        if not relationships:
            return False
        
        # Delete all found relationships
        success = False
        for rel in relationships:
            if rel.id:
                deleted = self.storage.delete_relationship(rel.id)
                if deleted:
                    success = True
        
        if success:
            logger.info(
                f"Unlinked memory {source_id} -> {target_id} "
                f"({relation_type.value if relation_type else 'all types'})"
            )
        
        return success
    
    def xǁRelationshipManagerǁunlink__mutmut_8(
        self,
        source_id: int,
        target_id: int,
        relation_type: Optional[RelationType] = None
    ) -> bool:
        """
        Remove relationship(s) between two memories.
        
        Args:
            source_id: ID of source memory
            target_id: ID of target memory
            relation_type: Optional specific relationship type to remove.
                          If None, removes all relationships between the memories.
            
        Returns:
            True if any relationships were removed, False otherwise
        """
        if relation_type is not None:
            # Remove specific relationship type
            relationships = self.storage.get_relationships(
                source_id=source_id,
                target_id=target_id,
                )
        else:
            # Remove all relationships between these memories
            relationships = self.storage.get_relationships(
                source_id=source_id,
                target_id=target_id
            )
        
        if not relationships:
            return False
        
        # Delete all found relationships
        success = False
        for rel in relationships:
            if rel.id:
                deleted = self.storage.delete_relationship(rel.id)
                if deleted:
                    success = True
        
        if success:
            logger.info(
                f"Unlinked memory {source_id} -> {target_id} "
                f"({relation_type.value if relation_type else 'all types'})"
            )
        
        return success
    
    def xǁRelationshipManagerǁunlink__mutmut_9(
        self,
        source_id: int,
        target_id: int,
        relation_type: Optional[RelationType] = None
    ) -> bool:
        """
        Remove relationship(s) between two memories.
        
        Args:
            source_id: ID of source memory
            target_id: ID of target memory
            relation_type: Optional specific relationship type to remove.
                          If None, removes all relationships between the memories.
            
        Returns:
            True if any relationships were removed, False otherwise
        """
        if relation_type is not None:
            # Remove specific relationship type
            relationships = self.storage.get_relationships(
                source_id=source_id,
                target_id=target_id,
                relation_type=relation_type
            )
        else:
            # Remove all relationships between these memories
            relationships = None
        
        if not relationships:
            return False
        
        # Delete all found relationships
        success = False
        for rel in relationships:
            if rel.id:
                deleted = self.storage.delete_relationship(rel.id)
                if deleted:
                    success = True
        
        if success:
            logger.info(
                f"Unlinked memory {source_id} -> {target_id} "
                f"({relation_type.value if relation_type else 'all types'})"
            )
        
        return success
    
    def xǁRelationshipManagerǁunlink__mutmut_10(
        self,
        source_id: int,
        target_id: int,
        relation_type: Optional[RelationType] = None
    ) -> bool:
        """
        Remove relationship(s) between two memories.
        
        Args:
            source_id: ID of source memory
            target_id: ID of target memory
            relation_type: Optional specific relationship type to remove.
                          If None, removes all relationships between the memories.
            
        Returns:
            True if any relationships were removed, False otherwise
        """
        if relation_type is not None:
            # Remove specific relationship type
            relationships = self.storage.get_relationships(
                source_id=source_id,
                target_id=target_id,
                relation_type=relation_type
            )
        else:
            # Remove all relationships between these memories
            relationships = self.storage.get_relationships(
                source_id=None,
                target_id=target_id
            )
        
        if not relationships:
            return False
        
        # Delete all found relationships
        success = False
        for rel in relationships:
            if rel.id:
                deleted = self.storage.delete_relationship(rel.id)
                if deleted:
                    success = True
        
        if success:
            logger.info(
                f"Unlinked memory {source_id} -> {target_id} "
                f"({relation_type.value if relation_type else 'all types'})"
            )
        
        return success
    
    def xǁRelationshipManagerǁunlink__mutmut_11(
        self,
        source_id: int,
        target_id: int,
        relation_type: Optional[RelationType] = None
    ) -> bool:
        """
        Remove relationship(s) between two memories.
        
        Args:
            source_id: ID of source memory
            target_id: ID of target memory
            relation_type: Optional specific relationship type to remove.
                          If None, removes all relationships between the memories.
            
        Returns:
            True if any relationships were removed, False otherwise
        """
        if relation_type is not None:
            # Remove specific relationship type
            relationships = self.storage.get_relationships(
                source_id=source_id,
                target_id=target_id,
                relation_type=relation_type
            )
        else:
            # Remove all relationships between these memories
            relationships = self.storage.get_relationships(
                source_id=source_id,
                target_id=None
            )
        
        if not relationships:
            return False
        
        # Delete all found relationships
        success = False
        for rel in relationships:
            if rel.id:
                deleted = self.storage.delete_relationship(rel.id)
                if deleted:
                    success = True
        
        if success:
            logger.info(
                f"Unlinked memory {source_id} -> {target_id} "
                f"({relation_type.value if relation_type else 'all types'})"
            )
        
        return success
    
    def xǁRelationshipManagerǁunlink__mutmut_12(
        self,
        source_id: int,
        target_id: int,
        relation_type: Optional[RelationType] = None
    ) -> bool:
        """
        Remove relationship(s) between two memories.
        
        Args:
            source_id: ID of source memory
            target_id: ID of target memory
            relation_type: Optional specific relationship type to remove.
                          If None, removes all relationships between the memories.
            
        Returns:
            True if any relationships were removed, False otherwise
        """
        if relation_type is not None:
            # Remove specific relationship type
            relationships = self.storage.get_relationships(
                source_id=source_id,
                target_id=target_id,
                relation_type=relation_type
            )
        else:
            # Remove all relationships between these memories
            relationships = self.storage.get_relationships(
                target_id=target_id
            )
        
        if not relationships:
            return False
        
        # Delete all found relationships
        success = False
        for rel in relationships:
            if rel.id:
                deleted = self.storage.delete_relationship(rel.id)
                if deleted:
                    success = True
        
        if success:
            logger.info(
                f"Unlinked memory {source_id} -> {target_id} "
                f"({relation_type.value if relation_type else 'all types'})"
            )
        
        return success
    
    def xǁRelationshipManagerǁunlink__mutmut_13(
        self,
        source_id: int,
        target_id: int,
        relation_type: Optional[RelationType] = None
    ) -> bool:
        """
        Remove relationship(s) between two memories.
        
        Args:
            source_id: ID of source memory
            target_id: ID of target memory
            relation_type: Optional specific relationship type to remove.
                          If None, removes all relationships between the memories.
            
        Returns:
            True if any relationships were removed, False otherwise
        """
        if relation_type is not None:
            # Remove specific relationship type
            relationships = self.storage.get_relationships(
                source_id=source_id,
                target_id=target_id,
                relation_type=relation_type
            )
        else:
            # Remove all relationships between these memories
            relationships = self.storage.get_relationships(
                source_id=source_id,
                )
        
        if not relationships:
            return False
        
        # Delete all found relationships
        success = False
        for rel in relationships:
            if rel.id:
                deleted = self.storage.delete_relationship(rel.id)
                if deleted:
                    success = True
        
        if success:
            logger.info(
                f"Unlinked memory {source_id} -> {target_id} "
                f"({relation_type.value if relation_type else 'all types'})"
            )
        
        return success
    
    def xǁRelationshipManagerǁunlink__mutmut_14(
        self,
        source_id: int,
        target_id: int,
        relation_type: Optional[RelationType] = None
    ) -> bool:
        """
        Remove relationship(s) between two memories.
        
        Args:
            source_id: ID of source memory
            target_id: ID of target memory
            relation_type: Optional specific relationship type to remove.
                          If None, removes all relationships between the memories.
            
        Returns:
            True if any relationships were removed, False otherwise
        """
        if relation_type is not None:
            # Remove specific relationship type
            relationships = self.storage.get_relationships(
                source_id=source_id,
                target_id=target_id,
                relation_type=relation_type
            )
        else:
            # Remove all relationships between these memories
            relationships = self.storage.get_relationships(
                source_id=source_id,
                target_id=target_id
            )
        
        if relationships:
            return False
        
        # Delete all found relationships
        success = False
        for rel in relationships:
            if rel.id:
                deleted = self.storage.delete_relationship(rel.id)
                if deleted:
                    success = True
        
        if success:
            logger.info(
                f"Unlinked memory {source_id} -> {target_id} "
                f"({relation_type.value if relation_type else 'all types'})"
            )
        
        return success
    
    def xǁRelationshipManagerǁunlink__mutmut_15(
        self,
        source_id: int,
        target_id: int,
        relation_type: Optional[RelationType] = None
    ) -> bool:
        """
        Remove relationship(s) between two memories.
        
        Args:
            source_id: ID of source memory
            target_id: ID of target memory
            relation_type: Optional specific relationship type to remove.
                          If None, removes all relationships between the memories.
            
        Returns:
            True if any relationships were removed, False otherwise
        """
        if relation_type is not None:
            # Remove specific relationship type
            relationships = self.storage.get_relationships(
                source_id=source_id,
                target_id=target_id,
                relation_type=relation_type
            )
        else:
            # Remove all relationships between these memories
            relationships = self.storage.get_relationships(
                source_id=source_id,
                target_id=target_id
            )
        
        if not relationships:
            return True
        
        # Delete all found relationships
        success = False
        for rel in relationships:
            if rel.id:
                deleted = self.storage.delete_relationship(rel.id)
                if deleted:
                    success = True
        
        if success:
            logger.info(
                f"Unlinked memory {source_id} -> {target_id} "
                f"({relation_type.value if relation_type else 'all types'})"
            )
        
        return success
    
    def xǁRelationshipManagerǁunlink__mutmut_16(
        self,
        source_id: int,
        target_id: int,
        relation_type: Optional[RelationType] = None
    ) -> bool:
        """
        Remove relationship(s) between two memories.
        
        Args:
            source_id: ID of source memory
            target_id: ID of target memory
            relation_type: Optional specific relationship type to remove.
                          If None, removes all relationships between the memories.
            
        Returns:
            True if any relationships were removed, False otherwise
        """
        if relation_type is not None:
            # Remove specific relationship type
            relationships = self.storage.get_relationships(
                source_id=source_id,
                target_id=target_id,
                relation_type=relation_type
            )
        else:
            # Remove all relationships between these memories
            relationships = self.storage.get_relationships(
                source_id=source_id,
                target_id=target_id
            )
        
        if not relationships:
            return False
        
        # Delete all found relationships
        success = None
        for rel in relationships:
            if rel.id:
                deleted = self.storage.delete_relationship(rel.id)
                if deleted:
                    success = True
        
        if success:
            logger.info(
                f"Unlinked memory {source_id} -> {target_id} "
                f"({relation_type.value if relation_type else 'all types'})"
            )
        
        return success
    
    def xǁRelationshipManagerǁunlink__mutmut_17(
        self,
        source_id: int,
        target_id: int,
        relation_type: Optional[RelationType] = None
    ) -> bool:
        """
        Remove relationship(s) between two memories.
        
        Args:
            source_id: ID of source memory
            target_id: ID of target memory
            relation_type: Optional specific relationship type to remove.
                          If None, removes all relationships between the memories.
            
        Returns:
            True if any relationships were removed, False otherwise
        """
        if relation_type is not None:
            # Remove specific relationship type
            relationships = self.storage.get_relationships(
                source_id=source_id,
                target_id=target_id,
                relation_type=relation_type
            )
        else:
            # Remove all relationships between these memories
            relationships = self.storage.get_relationships(
                source_id=source_id,
                target_id=target_id
            )
        
        if not relationships:
            return False
        
        # Delete all found relationships
        success = True
        for rel in relationships:
            if rel.id:
                deleted = self.storage.delete_relationship(rel.id)
                if deleted:
                    success = True
        
        if success:
            logger.info(
                f"Unlinked memory {source_id} -> {target_id} "
                f"({relation_type.value if relation_type else 'all types'})"
            )
        
        return success
    
    def xǁRelationshipManagerǁunlink__mutmut_18(
        self,
        source_id: int,
        target_id: int,
        relation_type: Optional[RelationType] = None
    ) -> bool:
        """
        Remove relationship(s) between two memories.
        
        Args:
            source_id: ID of source memory
            target_id: ID of target memory
            relation_type: Optional specific relationship type to remove.
                          If None, removes all relationships between the memories.
            
        Returns:
            True if any relationships were removed, False otherwise
        """
        if relation_type is not None:
            # Remove specific relationship type
            relationships = self.storage.get_relationships(
                source_id=source_id,
                target_id=target_id,
                relation_type=relation_type
            )
        else:
            # Remove all relationships between these memories
            relationships = self.storage.get_relationships(
                source_id=source_id,
                target_id=target_id
            )
        
        if not relationships:
            return False
        
        # Delete all found relationships
        success = False
        for rel in relationships:
            if rel.id:
                deleted = None
                if deleted:
                    success = True
        
        if success:
            logger.info(
                f"Unlinked memory {source_id} -> {target_id} "
                f"({relation_type.value if relation_type else 'all types'})"
            )
        
        return success
    
    def xǁRelationshipManagerǁunlink__mutmut_19(
        self,
        source_id: int,
        target_id: int,
        relation_type: Optional[RelationType] = None
    ) -> bool:
        """
        Remove relationship(s) between two memories.
        
        Args:
            source_id: ID of source memory
            target_id: ID of target memory
            relation_type: Optional specific relationship type to remove.
                          If None, removes all relationships between the memories.
            
        Returns:
            True if any relationships were removed, False otherwise
        """
        if relation_type is not None:
            # Remove specific relationship type
            relationships = self.storage.get_relationships(
                source_id=source_id,
                target_id=target_id,
                relation_type=relation_type
            )
        else:
            # Remove all relationships between these memories
            relationships = self.storage.get_relationships(
                source_id=source_id,
                target_id=target_id
            )
        
        if not relationships:
            return False
        
        # Delete all found relationships
        success = False
        for rel in relationships:
            if rel.id:
                deleted = self.storage.delete_relationship(None)
                if deleted:
                    success = True
        
        if success:
            logger.info(
                f"Unlinked memory {source_id} -> {target_id} "
                f"({relation_type.value if relation_type else 'all types'})"
            )
        
        return success
    
    def xǁRelationshipManagerǁunlink__mutmut_20(
        self,
        source_id: int,
        target_id: int,
        relation_type: Optional[RelationType] = None
    ) -> bool:
        """
        Remove relationship(s) between two memories.
        
        Args:
            source_id: ID of source memory
            target_id: ID of target memory
            relation_type: Optional specific relationship type to remove.
                          If None, removes all relationships between the memories.
            
        Returns:
            True if any relationships were removed, False otherwise
        """
        if relation_type is not None:
            # Remove specific relationship type
            relationships = self.storage.get_relationships(
                source_id=source_id,
                target_id=target_id,
                relation_type=relation_type
            )
        else:
            # Remove all relationships between these memories
            relationships = self.storage.get_relationships(
                source_id=source_id,
                target_id=target_id
            )
        
        if not relationships:
            return False
        
        # Delete all found relationships
        success = False
        for rel in relationships:
            if rel.id:
                deleted = self.storage.delete_relationship(rel.id)
                if deleted:
                    success = None
        
        if success:
            logger.info(
                f"Unlinked memory {source_id} -> {target_id} "
                f"({relation_type.value if relation_type else 'all types'})"
            )
        
        return success
    
    def xǁRelationshipManagerǁunlink__mutmut_21(
        self,
        source_id: int,
        target_id: int,
        relation_type: Optional[RelationType] = None
    ) -> bool:
        """
        Remove relationship(s) between two memories.
        
        Args:
            source_id: ID of source memory
            target_id: ID of target memory
            relation_type: Optional specific relationship type to remove.
                          If None, removes all relationships between the memories.
            
        Returns:
            True if any relationships were removed, False otherwise
        """
        if relation_type is not None:
            # Remove specific relationship type
            relationships = self.storage.get_relationships(
                source_id=source_id,
                target_id=target_id,
                relation_type=relation_type
            )
        else:
            # Remove all relationships between these memories
            relationships = self.storage.get_relationships(
                source_id=source_id,
                target_id=target_id
            )
        
        if not relationships:
            return False
        
        # Delete all found relationships
        success = False
        for rel in relationships:
            if rel.id:
                deleted = self.storage.delete_relationship(rel.id)
                if deleted:
                    success = False
        
        if success:
            logger.info(
                f"Unlinked memory {source_id} -> {target_id} "
                f"({relation_type.value if relation_type else 'all types'})"
            )
        
        return success
    
    def xǁRelationshipManagerǁunlink__mutmut_22(
        self,
        source_id: int,
        target_id: int,
        relation_type: Optional[RelationType] = None
    ) -> bool:
        """
        Remove relationship(s) between two memories.
        
        Args:
            source_id: ID of source memory
            target_id: ID of target memory
            relation_type: Optional specific relationship type to remove.
                          If None, removes all relationships between the memories.
            
        Returns:
            True if any relationships were removed, False otherwise
        """
        if relation_type is not None:
            # Remove specific relationship type
            relationships = self.storage.get_relationships(
                source_id=source_id,
                target_id=target_id,
                relation_type=relation_type
            )
        else:
            # Remove all relationships between these memories
            relationships = self.storage.get_relationships(
                source_id=source_id,
                target_id=target_id
            )
        
        if not relationships:
            return False
        
        # Delete all found relationships
        success = False
        for rel in relationships:
            if rel.id:
                deleted = self.storage.delete_relationship(rel.id)
                if deleted:
                    success = True
        
        if success:
            logger.info(
                None
            )
        
        return success
    
    def xǁRelationshipManagerǁunlink__mutmut_23(
        self,
        source_id: int,
        target_id: int,
        relation_type: Optional[RelationType] = None
    ) -> bool:
        """
        Remove relationship(s) between two memories.
        
        Args:
            source_id: ID of source memory
            target_id: ID of target memory
            relation_type: Optional specific relationship type to remove.
                          If None, removes all relationships between the memories.
            
        Returns:
            True if any relationships were removed, False otherwise
        """
        if relation_type is not None:
            # Remove specific relationship type
            relationships = self.storage.get_relationships(
                source_id=source_id,
                target_id=target_id,
                relation_type=relation_type
            )
        else:
            # Remove all relationships between these memories
            relationships = self.storage.get_relationships(
                source_id=source_id,
                target_id=target_id
            )
        
        if not relationships:
            return False
        
        # Delete all found relationships
        success = False
        for rel in relationships:
            if rel.id:
                deleted = self.storage.delete_relationship(rel.id)
                if deleted:
                    success = True
        
        if success:
            logger.info(
                f"Unlinked memory {source_id} -> {target_id} "
                f"({relation_type.value if relation_type else 'XXall typesXX'})"
            )
        
        return success
    
    def xǁRelationshipManagerǁunlink__mutmut_24(
        self,
        source_id: int,
        target_id: int,
        relation_type: Optional[RelationType] = None
    ) -> bool:
        """
        Remove relationship(s) between two memories.
        
        Args:
            source_id: ID of source memory
            target_id: ID of target memory
            relation_type: Optional specific relationship type to remove.
                          If None, removes all relationships between the memories.
            
        Returns:
            True if any relationships were removed, False otherwise
        """
        if relation_type is not None:
            # Remove specific relationship type
            relationships = self.storage.get_relationships(
                source_id=source_id,
                target_id=target_id,
                relation_type=relation_type
            )
        else:
            # Remove all relationships between these memories
            relationships = self.storage.get_relationships(
                source_id=source_id,
                target_id=target_id
            )
        
        if not relationships:
            return False
        
        # Delete all found relationships
        success = False
        for rel in relationships:
            if rel.id:
                deleted = self.storage.delete_relationship(rel.id)
                if deleted:
                    success = True
        
        if success:
            logger.info(
                f"Unlinked memory {source_id} -> {target_id} "
                f"({relation_type.value if relation_type else 'ALL TYPES'})"
            )
        
        return success
    
    xǁRelationshipManagerǁunlink__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁRelationshipManagerǁunlink__mutmut_1': xǁRelationshipManagerǁunlink__mutmut_1, 
        'xǁRelationshipManagerǁunlink__mutmut_2': xǁRelationshipManagerǁunlink__mutmut_2, 
        'xǁRelationshipManagerǁunlink__mutmut_3': xǁRelationshipManagerǁunlink__mutmut_3, 
        'xǁRelationshipManagerǁunlink__mutmut_4': xǁRelationshipManagerǁunlink__mutmut_4, 
        'xǁRelationshipManagerǁunlink__mutmut_5': xǁRelationshipManagerǁunlink__mutmut_5, 
        'xǁRelationshipManagerǁunlink__mutmut_6': xǁRelationshipManagerǁunlink__mutmut_6, 
        'xǁRelationshipManagerǁunlink__mutmut_7': xǁRelationshipManagerǁunlink__mutmut_7, 
        'xǁRelationshipManagerǁunlink__mutmut_8': xǁRelationshipManagerǁunlink__mutmut_8, 
        'xǁRelationshipManagerǁunlink__mutmut_9': xǁRelationshipManagerǁunlink__mutmut_9, 
        'xǁRelationshipManagerǁunlink__mutmut_10': xǁRelationshipManagerǁunlink__mutmut_10, 
        'xǁRelationshipManagerǁunlink__mutmut_11': xǁRelationshipManagerǁunlink__mutmut_11, 
        'xǁRelationshipManagerǁunlink__mutmut_12': xǁRelationshipManagerǁunlink__mutmut_12, 
        'xǁRelationshipManagerǁunlink__mutmut_13': xǁRelationshipManagerǁunlink__mutmut_13, 
        'xǁRelationshipManagerǁunlink__mutmut_14': xǁRelationshipManagerǁunlink__mutmut_14, 
        'xǁRelationshipManagerǁunlink__mutmut_15': xǁRelationshipManagerǁunlink__mutmut_15, 
        'xǁRelationshipManagerǁunlink__mutmut_16': xǁRelationshipManagerǁunlink__mutmut_16, 
        'xǁRelationshipManagerǁunlink__mutmut_17': xǁRelationshipManagerǁunlink__mutmut_17, 
        'xǁRelationshipManagerǁunlink__mutmut_18': xǁRelationshipManagerǁunlink__mutmut_18, 
        'xǁRelationshipManagerǁunlink__mutmut_19': xǁRelationshipManagerǁunlink__mutmut_19, 
        'xǁRelationshipManagerǁunlink__mutmut_20': xǁRelationshipManagerǁunlink__mutmut_20, 
        'xǁRelationshipManagerǁunlink__mutmut_21': xǁRelationshipManagerǁunlink__mutmut_21, 
        'xǁRelationshipManagerǁunlink__mutmut_22': xǁRelationshipManagerǁunlink__mutmut_22, 
        'xǁRelationshipManagerǁunlink__mutmut_23': xǁRelationshipManagerǁunlink__mutmut_23, 
        'xǁRelationshipManagerǁunlink__mutmut_24': xǁRelationshipManagerǁunlink__mutmut_24
    }
    
    def unlink(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁRelationshipManagerǁunlink__mutmut_orig"), object.__getattribute__(self, "xǁRelationshipManagerǁunlink__mutmut_mutants"), args, kwargs, self)
        return result 
    
    unlink.__signature__ = _mutmut_signature(xǁRelationshipManagerǁunlink__mutmut_orig)
    xǁRelationshipManagerǁunlink__mutmut_orig.__name__ = 'xǁRelationshipManagerǁunlink'
    
    def xǁRelationshipManagerǁget_related__mutmut_orig(
        self,
        memory_id: int,
        relation_types: Optional[List[RelationType]] = None,
        direction: str = "both",
        min_strength: float = 0.0,
        limit: int = 20
    ) -> List[Tuple[MemoryRecord, RelationshipRecord]]:
        """
        Get memories related to a given memory.
        
        Args:
            memory_id: ID of memory to find relations for
            relation_types: Optional list of relation types to filter by
            direction: "outgoing", "incoming", or "both" (default: "both")
            min_strength: Minimum relationship strength (default: 0.0)
            limit: Maximum number of results (default: 20)
            
        Returns:
            List of tuples (MemoryRecord, RelationshipRecord) sorted by strength
        """
        # Get related memories from storage
        related = self.storage.get_related_memories(
            memory_id=memory_id,
            relation_types=relation_types,
            direction=direction
        )
        
        # Filter by minimum strength
        filtered = [
            (mem, rel) for mem, rel in related
            if rel.strength >= min_strength
        ]
        
        # Sort by strength (descending) and limit
        filtered.sort(key=lambda x: x[1].strength, reverse=True)
        return filtered[:limit]
    
    def xǁRelationshipManagerǁget_related__mutmut_1(
        self,
        memory_id: int,
        relation_types: Optional[List[RelationType]] = None,
        direction: str = "XXbothXX",
        min_strength: float = 0.0,
        limit: int = 20
    ) -> List[Tuple[MemoryRecord, RelationshipRecord]]:
        """
        Get memories related to a given memory.
        
        Args:
            memory_id: ID of memory to find relations for
            relation_types: Optional list of relation types to filter by
            direction: "outgoing", "incoming", or "both" (default: "both")
            min_strength: Minimum relationship strength (default: 0.0)
            limit: Maximum number of results (default: 20)
            
        Returns:
            List of tuples (MemoryRecord, RelationshipRecord) sorted by strength
        """
        # Get related memories from storage
        related = self.storage.get_related_memories(
            memory_id=memory_id,
            relation_types=relation_types,
            direction=direction
        )
        
        # Filter by minimum strength
        filtered = [
            (mem, rel) for mem, rel in related
            if rel.strength >= min_strength
        ]
        
        # Sort by strength (descending) and limit
        filtered.sort(key=lambda x: x[1].strength, reverse=True)
        return filtered[:limit]
    
    def xǁRelationshipManagerǁget_related__mutmut_2(
        self,
        memory_id: int,
        relation_types: Optional[List[RelationType]] = None,
        direction: str = "BOTH",
        min_strength: float = 0.0,
        limit: int = 20
    ) -> List[Tuple[MemoryRecord, RelationshipRecord]]:
        """
        Get memories related to a given memory.
        
        Args:
            memory_id: ID of memory to find relations for
            relation_types: Optional list of relation types to filter by
            direction: "outgoing", "incoming", or "both" (default: "both")
            min_strength: Minimum relationship strength (default: 0.0)
            limit: Maximum number of results (default: 20)
            
        Returns:
            List of tuples (MemoryRecord, RelationshipRecord) sorted by strength
        """
        # Get related memories from storage
        related = self.storage.get_related_memories(
            memory_id=memory_id,
            relation_types=relation_types,
            direction=direction
        )
        
        # Filter by minimum strength
        filtered = [
            (mem, rel) for mem, rel in related
            if rel.strength >= min_strength
        ]
        
        # Sort by strength (descending) and limit
        filtered.sort(key=lambda x: x[1].strength, reverse=True)
        return filtered[:limit]
    
    def xǁRelationshipManagerǁget_related__mutmut_3(
        self,
        memory_id: int,
        relation_types: Optional[List[RelationType]] = None,
        direction: str = "both",
        min_strength: float = 1.0,
        limit: int = 20
    ) -> List[Tuple[MemoryRecord, RelationshipRecord]]:
        """
        Get memories related to a given memory.
        
        Args:
            memory_id: ID of memory to find relations for
            relation_types: Optional list of relation types to filter by
            direction: "outgoing", "incoming", or "both" (default: "both")
            min_strength: Minimum relationship strength (default: 0.0)
            limit: Maximum number of results (default: 20)
            
        Returns:
            List of tuples (MemoryRecord, RelationshipRecord) sorted by strength
        """
        # Get related memories from storage
        related = self.storage.get_related_memories(
            memory_id=memory_id,
            relation_types=relation_types,
            direction=direction
        )
        
        # Filter by minimum strength
        filtered = [
            (mem, rel) for mem, rel in related
            if rel.strength >= min_strength
        ]
        
        # Sort by strength (descending) and limit
        filtered.sort(key=lambda x: x[1].strength, reverse=True)
        return filtered[:limit]
    
    def xǁRelationshipManagerǁget_related__mutmut_4(
        self,
        memory_id: int,
        relation_types: Optional[List[RelationType]] = None,
        direction: str = "both",
        min_strength: float = 0.0,
        limit: int = 21
    ) -> List[Tuple[MemoryRecord, RelationshipRecord]]:
        """
        Get memories related to a given memory.
        
        Args:
            memory_id: ID of memory to find relations for
            relation_types: Optional list of relation types to filter by
            direction: "outgoing", "incoming", or "both" (default: "both")
            min_strength: Minimum relationship strength (default: 0.0)
            limit: Maximum number of results (default: 20)
            
        Returns:
            List of tuples (MemoryRecord, RelationshipRecord) sorted by strength
        """
        # Get related memories from storage
        related = self.storage.get_related_memories(
            memory_id=memory_id,
            relation_types=relation_types,
            direction=direction
        )
        
        # Filter by minimum strength
        filtered = [
            (mem, rel) for mem, rel in related
            if rel.strength >= min_strength
        ]
        
        # Sort by strength (descending) and limit
        filtered.sort(key=lambda x: x[1].strength, reverse=True)
        return filtered[:limit]
    
    def xǁRelationshipManagerǁget_related__mutmut_5(
        self,
        memory_id: int,
        relation_types: Optional[List[RelationType]] = None,
        direction: str = "both",
        min_strength: float = 0.0,
        limit: int = 20
    ) -> List[Tuple[MemoryRecord, RelationshipRecord]]:
        """
        Get memories related to a given memory.
        
        Args:
            memory_id: ID of memory to find relations for
            relation_types: Optional list of relation types to filter by
            direction: "outgoing", "incoming", or "both" (default: "both")
            min_strength: Minimum relationship strength (default: 0.0)
            limit: Maximum number of results (default: 20)
            
        Returns:
            List of tuples (MemoryRecord, RelationshipRecord) sorted by strength
        """
        # Get related memories from storage
        related = None
        
        # Filter by minimum strength
        filtered = [
            (mem, rel) for mem, rel in related
            if rel.strength >= min_strength
        ]
        
        # Sort by strength (descending) and limit
        filtered.sort(key=lambda x: x[1].strength, reverse=True)
        return filtered[:limit]
    
    def xǁRelationshipManagerǁget_related__mutmut_6(
        self,
        memory_id: int,
        relation_types: Optional[List[RelationType]] = None,
        direction: str = "both",
        min_strength: float = 0.0,
        limit: int = 20
    ) -> List[Tuple[MemoryRecord, RelationshipRecord]]:
        """
        Get memories related to a given memory.
        
        Args:
            memory_id: ID of memory to find relations for
            relation_types: Optional list of relation types to filter by
            direction: "outgoing", "incoming", or "both" (default: "both")
            min_strength: Minimum relationship strength (default: 0.0)
            limit: Maximum number of results (default: 20)
            
        Returns:
            List of tuples (MemoryRecord, RelationshipRecord) sorted by strength
        """
        # Get related memories from storage
        related = self.storage.get_related_memories(
            memory_id=None,
            relation_types=relation_types,
            direction=direction
        )
        
        # Filter by minimum strength
        filtered = [
            (mem, rel) for mem, rel in related
            if rel.strength >= min_strength
        ]
        
        # Sort by strength (descending) and limit
        filtered.sort(key=lambda x: x[1].strength, reverse=True)
        return filtered[:limit]
    
    def xǁRelationshipManagerǁget_related__mutmut_7(
        self,
        memory_id: int,
        relation_types: Optional[List[RelationType]] = None,
        direction: str = "both",
        min_strength: float = 0.0,
        limit: int = 20
    ) -> List[Tuple[MemoryRecord, RelationshipRecord]]:
        """
        Get memories related to a given memory.
        
        Args:
            memory_id: ID of memory to find relations for
            relation_types: Optional list of relation types to filter by
            direction: "outgoing", "incoming", or "both" (default: "both")
            min_strength: Minimum relationship strength (default: 0.0)
            limit: Maximum number of results (default: 20)
            
        Returns:
            List of tuples (MemoryRecord, RelationshipRecord) sorted by strength
        """
        # Get related memories from storage
        related = self.storage.get_related_memories(
            memory_id=memory_id,
            relation_types=None,
            direction=direction
        )
        
        # Filter by minimum strength
        filtered = [
            (mem, rel) for mem, rel in related
            if rel.strength >= min_strength
        ]
        
        # Sort by strength (descending) and limit
        filtered.sort(key=lambda x: x[1].strength, reverse=True)
        return filtered[:limit]
    
    def xǁRelationshipManagerǁget_related__mutmut_8(
        self,
        memory_id: int,
        relation_types: Optional[List[RelationType]] = None,
        direction: str = "both",
        min_strength: float = 0.0,
        limit: int = 20
    ) -> List[Tuple[MemoryRecord, RelationshipRecord]]:
        """
        Get memories related to a given memory.
        
        Args:
            memory_id: ID of memory to find relations for
            relation_types: Optional list of relation types to filter by
            direction: "outgoing", "incoming", or "both" (default: "both")
            min_strength: Minimum relationship strength (default: 0.0)
            limit: Maximum number of results (default: 20)
            
        Returns:
            List of tuples (MemoryRecord, RelationshipRecord) sorted by strength
        """
        # Get related memories from storage
        related = self.storage.get_related_memories(
            memory_id=memory_id,
            relation_types=relation_types,
            direction=None
        )
        
        # Filter by minimum strength
        filtered = [
            (mem, rel) for mem, rel in related
            if rel.strength >= min_strength
        ]
        
        # Sort by strength (descending) and limit
        filtered.sort(key=lambda x: x[1].strength, reverse=True)
        return filtered[:limit]
    
    def xǁRelationshipManagerǁget_related__mutmut_9(
        self,
        memory_id: int,
        relation_types: Optional[List[RelationType]] = None,
        direction: str = "both",
        min_strength: float = 0.0,
        limit: int = 20
    ) -> List[Tuple[MemoryRecord, RelationshipRecord]]:
        """
        Get memories related to a given memory.
        
        Args:
            memory_id: ID of memory to find relations for
            relation_types: Optional list of relation types to filter by
            direction: "outgoing", "incoming", or "both" (default: "both")
            min_strength: Minimum relationship strength (default: 0.0)
            limit: Maximum number of results (default: 20)
            
        Returns:
            List of tuples (MemoryRecord, RelationshipRecord) sorted by strength
        """
        # Get related memories from storage
        related = self.storage.get_related_memories(
            relation_types=relation_types,
            direction=direction
        )
        
        # Filter by minimum strength
        filtered = [
            (mem, rel) for mem, rel in related
            if rel.strength >= min_strength
        ]
        
        # Sort by strength (descending) and limit
        filtered.sort(key=lambda x: x[1].strength, reverse=True)
        return filtered[:limit]
    
    def xǁRelationshipManagerǁget_related__mutmut_10(
        self,
        memory_id: int,
        relation_types: Optional[List[RelationType]] = None,
        direction: str = "both",
        min_strength: float = 0.0,
        limit: int = 20
    ) -> List[Tuple[MemoryRecord, RelationshipRecord]]:
        """
        Get memories related to a given memory.
        
        Args:
            memory_id: ID of memory to find relations for
            relation_types: Optional list of relation types to filter by
            direction: "outgoing", "incoming", or "both" (default: "both")
            min_strength: Minimum relationship strength (default: 0.0)
            limit: Maximum number of results (default: 20)
            
        Returns:
            List of tuples (MemoryRecord, RelationshipRecord) sorted by strength
        """
        # Get related memories from storage
        related = self.storage.get_related_memories(
            memory_id=memory_id,
            direction=direction
        )
        
        # Filter by minimum strength
        filtered = [
            (mem, rel) for mem, rel in related
            if rel.strength >= min_strength
        ]
        
        # Sort by strength (descending) and limit
        filtered.sort(key=lambda x: x[1].strength, reverse=True)
        return filtered[:limit]
    
    def xǁRelationshipManagerǁget_related__mutmut_11(
        self,
        memory_id: int,
        relation_types: Optional[List[RelationType]] = None,
        direction: str = "both",
        min_strength: float = 0.0,
        limit: int = 20
    ) -> List[Tuple[MemoryRecord, RelationshipRecord]]:
        """
        Get memories related to a given memory.
        
        Args:
            memory_id: ID of memory to find relations for
            relation_types: Optional list of relation types to filter by
            direction: "outgoing", "incoming", or "both" (default: "both")
            min_strength: Minimum relationship strength (default: 0.0)
            limit: Maximum number of results (default: 20)
            
        Returns:
            List of tuples (MemoryRecord, RelationshipRecord) sorted by strength
        """
        # Get related memories from storage
        related = self.storage.get_related_memories(
            memory_id=memory_id,
            relation_types=relation_types,
            )
        
        # Filter by minimum strength
        filtered = [
            (mem, rel) for mem, rel in related
            if rel.strength >= min_strength
        ]
        
        # Sort by strength (descending) and limit
        filtered.sort(key=lambda x: x[1].strength, reverse=True)
        return filtered[:limit]
    
    def xǁRelationshipManagerǁget_related__mutmut_12(
        self,
        memory_id: int,
        relation_types: Optional[List[RelationType]] = None,
        direction: str = "both",
        min_strength: float = 0.0,
        limit: int = 20
    ) -> List[Tuple[MemoryRecord, RelationshipRecord]]:
        """
        Get memories related to a given memory.
        
        Args:
            memory_id: ID of memory to find relations for
            relation_types: Optional list of relation types to filter by
            direction: "outgoing", "incoming", or "both" (default: "both")
            min_strength: Minimum relationship strength (default: 0.0)
            limit: Maximum number of results (default: 20)
            
        Returns:
            List of tuples (MemoryRecord, RelationshipRecord) sorted by strength
        """
        # Get related memories from storage
        related = self.storage.get_related_memories(
            memory_id=memory_id,
            relation_types=relation_types,
            direction=direction
        )
        
        # Filter by minimum strength
        filtered = None
        
        # Sort by strength (descending) and limit
        filtered.sort(key=lambda x: x[1].strength, reverse=True)
        return filtered[:limit]
    
    def xǁRelationshipManagerǁget_related__mutmut_13(
        self,
        memory_id: int,
        relation_types: Optional[List[RelationType]] = None,
        direction: str = "both",
        min_strength: float = 0.0,
        limit: int = 20
    ) -> List[Tuple[MemoryRecord, RelationshipRecord]]:
        """
        Get memories related to a given memory.
        
        Args:
            memory_id: ID of memory to find relations for
            relation_types: Optional list of relation types to filter by
            direction: "outgoing", "incoming", or "both" (default: "both")
            min_strength: Minimum relationship strength (default: 0.0)
            limit: Maximum number of results (default: 20)
            
        Returns:
            List of tuples (MemoryRecord, RelationshipRecord) sorted by strength
        """
        # Get related memories from storage
        related = self.storage.get_related_memories(
            memory_id=memory_id,
            relation_types=relation_types,
            direction=direction
        )
        
        # Filter by minimum strength
        filtered = [
            (mem, rel) for mem, rel in related
            if rel.strength > min_strength
        ]
        
        # Sort by strength (descending) and limit
        filtered.sort(key=lambda x: x[1].strength, reverse=True)
        return filtered[:limit]
    
    def xǁRelationshipManagerǁget_related__mutmut_14(
        self,
        memory_id: int,
        relation_types: Optional[List[RelationType]] = None,
        direction: str = "both",
        min_strength: float = 0.0,
        limit: int = 20
    ) -> List[Tuple[MemoryRecord, RelationshipRecord]]:
        """
        Get memories related to a given memory.
        
        Args:
            memory_id: ID of memory to find relations for
            relation_types: Optional list of relation types to filter by
            direction: "outgoing", "incoming", or "both" (default: "both")
            min_strength: Minimum relationship strength (default: 0.0)
            limit: Maximum number of results (default: 20)
            
        Returns:
            List of tuples (MemoryRecord, RelationshipRecord) sorted by strength
        """
        # Get related memories from storage
        related = self.storage.get_related_memories(
            memory_id=memory_id,
            relation_types=relation_types,
            direction=direction
        )
        
        # Filter by minimum strength
        filtered = [
            (mem, rel) for mem, rel in related
            if rel.strength >= min_strength
        ]
        
        # Sort by strength (descending) and limit
        filtered.sort(key=None, reverse=True)
        return filtered[:limit]
    
    def xǁRelationshipManagerǁget_related__mutmut_15(
        self,
        memory_id: int,
        relation_types: Optional[List[RelationType]] = None,
        direction: str = "both",
        min_strength: float = 0.0,
        limit: int = 20
    ) -> List[Tuple[MemoryRecord, RelationshipRecord]]:
        """
        Get memories related to a given memory.
        
        Args:
            memory_id: ID of memory to find relations for
            relation_types: Optional list of relation types to filter by
            direction: "outgoing", "incoming", or "both" (default: "both")
            min_strength: Minimum relationship strength (default: 0.0)
            limit: Maximum number of results (default: 20)
            
        Returns:
            List of tuples (MemoryRecord, RelationshipRecord) sorted by strength
        """
        # Get related memories from storage
        related = self.storage.get_related_memories(
            memory_id=memory_id,
            relation_types=relation_types,
            direction=direction
        )
        
        # Filter by minimum strength
        filtered = [
            (mem, rel) for mem, rel in related
            if rel.strength >= min_strength
        ]
        
        # Sort by strength (descending) and limit
        filtered.sort(key=lambda x: x[1].strength, reverse=None)
        return filtered[:limit]
    
    def xǁRelationshipManagerǁget_related__mutmut_16(
        self,
        memory_id: int,
        relation_types: Optional[List[RelationType]] = None,
        direction: str = "both",
        min_strength: float = 0.0,
        limit: int = 20
    ) -> List[Tuple[MemoryRecord, RelationshipRecord]]:
        """
        Get memories related to a given memory.
        
        Args:
            memory_id: ID of memory to find relations for
            relation_types: Optional list of relation types to filter by
            direction: "outgoing", "incoming", or "both" (default: "both")
            min_strength: Minimum relationship strength (default: 0.0)
            limit: Maximum number of results (default: 20)
            
        Returns:
            List of tuples (MemoryRecord, RelationshipRecord) sorted by strength
        """
        # Get related memories from storage
        related = self.storage.get_related_memories(
            memory_id=memory_id,
            relation_types=relation_types,
            direction=direction
        )
        
        # Filter by minimum strength
        filtered = [
            (mem, rel) for mem, rel in related
            if rel.strength >= min_strength
        ]
        
        # Sort by strength (descending) and limit
        filtered.sort(reverse=True)
        return filtered[:limit]
    
    def xǁRelationshipManagerǁget_related__mutmut_17(
        self,
        memory_id: int,
        relation_types: Optional[List[RelationType]] = None,
        direction: str = "both",
        min_strength: float = 0.0,
        limit: int = 20
    ) -> List[Tuple[MemoryRecord, RelationshipRecord]]:
        """
        Get memories related to a given memory.
        
        Args:
            memory_id: ID of memory to find relations for
            relation_types: Optional list of relation types to filter by
            direction: "outgoing", "incoming", or "both" (default: "both")
            min_strength: Minimum relationship strength (default: 0.0)
            limit: Maximum number of results (default: 20)
            
        Returns:
            List of tuples (MemoryRecord, RelationshipRecord) sorted by strength
        """
        # Get related memories from storage
        related = self.storage.get_related_memories(
            memory_id=memory_id,
            relation_types=relation_types,
            direction=direction
        )
        
        # Filter by minimum strength
        filtered = [
            (mem, rel) for mem, rel in related
            if rel.strength >= min_strength
        ]
        
        # Sort by strength (descending) and limit
        filtered.sort(key=lambda x: x[1].strength, )
        return filtered[:limit]
    
    def xǁRelationshipManagerǁget_related__mutmut_18(
        self,
        memory_id: int,
        relation_types: Optional[List[RelationType]] = None,
        direction: str = "both",
        min_strength: float = 0.0,
        limit: int = 20
    ) -> List[Tuple[MemoryRecord, RelationshipRecord]]:
        """
        Get memories related to a given memory.
        
        Args:
            memory_id: ID of memory to find relations for
            relation_types: Optional list of relation types to filter by
            direction: "outgoing", "incoming", or "both" (default: "both")
            min_strength: Minimum relationship strength (default: 0.0)
            limit: Maximum number of results (default: 20)
            
        Returns:
            List of tuples (MemoryRecord, RelationshipRecord) sorted by strength
        """
        # Get related memories from storage
        related = self.storage.get_related_memories(
            memory_id=memory_id,
            relation_types=relation_types,
            direction=direction
        )
        
        # Filter by minimum strength
        filtered = [
            (mem, rel) for mem, rel in related
            if rel.strength >= min_strength
        ]
        
        # Sort by strength (descending) and limit
        filtered.sort(key=lambda x: None, reverse=True)
        return filtered[:limit]
    
    def xǁRelationshipManagerǁget_related__mutmut_19(
        self,
        memory_id: int,
        relation_types: Optional[List[RelationType]] = None,
        direction: str = "both",
        min_strength: float = 0.0,
        limit: int = 20
    ) -> List[Tuple[MemoryRecord, RelationshipRecord]]:
        """
        Get memories related to a given memory.
        
        Args:
            memory_id: ID of memory to find relations for
            relation_types: Optional list of relation types to filter by
            direction: "outgoing", "incoming", or "both" (default: "both")
            min_strength: Minimum relationship strength (default: 0.0)
            limit: Maximum number of results (default: 20)
            
        Returns:
            List of tuples (MemoryRecord, RelationshipRecord) sorted by strength
        """
        # Get related memories from storage
        related = self.storage.get_related_memories(
            memory_id=memory_id,
            relation_types=relation_types,
            direction=direction
        )
        
        # Filter by minimum strength
        filtered = [
            (mem, rel) for mem, rel in related
            if rel.strength >= min_strength
        ]
        
        # Sort by strength (descending) and limit
        filtered.sort(key=lambda x: x[2].strength, reverse=True)
        return filtered[:limit]
    
    def xǁRelationshipManagerǁget_related__mutmut_20(
        self,
        memory_id: int,
        relation_types: Optional[List[RelationType]] = None,
        direction: str = "both",
        min_strength: float = 0.0,
        limit: int = 20
    ) -> List[Tuple[MemoryRecord, RelationshipRecord]]:
        """
        Get memories related to a given memory.
        
        Args:
            memory_id: ID of memory to find relations for
            relation_types: Optional list of relation types to filter by
            direction: "outgoing", "incoming", or "both" (default: "both")
            min_strength: Minimum relationship strength (default: 0.0)
            limit: Maximum number of results (default: 20)
            
        Returns:
            List of tuples (MemoryRecord, RelationshipRecord) sorted by strength
        """
        # Get related memories from storage
        related = self.storage.get_related_memories(
            memory_id=memory_id,
            relation_types=relation_types,
            direction=direction
        )
        
        # Filter by minimum strength
        filtered = [
            (mem, rel) for mem, rel in related
            if rel.strength >= min_strength
        ]
        
        # Sort by strength (descending) and limit
        filtered.sort(key=lambda x: x[1].strength, reverse=False)
        return filtered[:limit]
    
    xǁRelationshipManagerǁget_related__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁRelationshipManagerǁget_related__mutmut_1': xǁRelationshipManagerǁget_related__mutmut_1, 
        'xǁRelationshipManagerǁget_related__mutmut_2': xǁRelationshipManagerǁget_related__mutmut_2, 
        'xǁRelationshipManagerǁget_related__mutmut_3': xǁRelationshipManagerǁget_related__mutmut_3, 
        'xǁRelationshipManagerǁget_related__mutmut_4': xǁRelationshipManagerǁget_related__mutmut_4, 
        'xǁRelationshipManagerǁget_related__mutmut_5': xǁRelationshipManagerǁget_related__mutmut_5, 
        'xǁRelationshipManagerǁget_related__mutmut_6': xǁRelationshipManagerǁget_related__mutmut_6, 
        'xǁRelationshipManagerǁget_related__mutmut_7': xǁRelationshipManagerǁget_related__mutmut_7, 
        'xǁRelationshipManagerǁget_related__mutmut_8': xǁRelationshipManagerǁget_related__mutmut_8, 
        'xǁRelationshipManagerǁget_related__mutmut_9': xǁRelationshipManagerǁget_related__mutmut_9, 
        'xǁRelationshipManagerǁget_related__mutmut_10': xǁRelationshipManagerǁget_related__mutmut_10, 
        'xǁRelationshipManagerǁget_related__mutmut_11': xǁRelationshipManagerǁget_related__mutmut_11, 
        'xǁRelationshipManagerǁget_related__mutmut_12': xǁRelationshipManagerǁget_related__mutmut_12, 
        'xǁRelationshipManagerǁget_related__mutmut_13': xǁRelationshipManagerǁget_related__mutmut_13, 
        'xǁRelationshipManagerǁget_related__mutmut_14': xǁRelationshipManagerǁget_related__mutmut_14, 
        'xǁRelationshipManagerǁget_related__mutmut_15': xǁRelationshipManagerǁget_related__mutmut_15, 
        'xǁRelationshipManagerǁget_related__mutmut_16': xǁRelationshipManagerǁget_related__mutmut_16, 
        'xǁRelationshipManagerǁget_related__mutmut_17': xǁRelationshipManagerǁget_related__mutmut_17, 
        'xǁRelationshipManagerǁget_related__mutmut_18': xǁRelationshipManagerǁget_related__mutmut_18, 
        'xǁRelationshipManagerǁget_related__mutmut_19': xǁRelationshipManagerǁget_related__mutmut_19, 
        'xǁRelationshipManagerǁget_related__mutmut_20': xǁRelationshipManagerǁget_related__mutmut_20
    }
    
    def get_related(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁRelationshipManagerǁget_related__mutmut_orig"), object.__getattribute__(self, "xǁRelationshipManagerǁget_related__mutmut_mutants"), args, kwargs, self)
        return result 
    
    get_related.__signature__ = _mutmut_signature(xǁRelationshipManagerǁget_related__mutmut_orig)
    xǁRelationshipManagerǁget_related__mutmut_orig.__name__ = 'xǁRelationshipManagerǁget_related'
    
    def xǁRelationshipManagerǁget_relationship_graph__mutmut_orig(
        self,
        memory_ids: List[int],
        depth: int = 2
    ) -> Dict[str, Any]:
        """
        Get subgraph of relationships around given memories.
        
        Args:
            memory_ids: List of memory IDs to start from
            depth: Maximum depth of traversal (default: 2)
            
        Returns:
            Dictionary with "nodes" and "edges" representing the graph
        """
        nodes: Dict[int, Dict[str, Any]] = {}
        edges: List[Dict[str, Any]] = []
        visited: set = set()
        
        # BFS traversal
        queue: List[Tuple[int, int]] = [(mem_id, 0) for mem_id in memory_ids]  # (memory_id, current_depth)
        
        while queue:
            current_id, current_depth = queue.pop(0)
            
            if current_id in visited or current_depth > depth:
                continue
            
            visited.add(current_id)
            
            # Get memory
            memory = self.storage.get_memory(current_id)
            if not memory:
                continue
            
            # Add node
            nodes[current_id] = {
                "id": current_id,
                "namespace": memory.namespace,
                "text": memory.text[:50] + "..." if len(memory.text) > 50 else memory.text,
                "importance": memory.importance
            }
            
            # If not at max depth, explore relationships
            if current_depth < depth:
                # Get outgoing relationships
                relationships = self.storage.get_relationships(source_id=current_id)
                for rel in relationships:
                    target_id = rel.target_id
                    
                    # Add edge
                    edges.append({
                        "source": current_id,
                        "target": target_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if target_id not in visited:
                        queue.append((target_id, current_depth + 1))
                
                # Get incoming relationships
                relationships = self.storage.get_relationships(target_id=current_id)
                for rel in relationships:
                    source_id = rel.source_id
                    
                    # Add edge
                    edges.append({
                        "source": source_id,
                        "target": current_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if source_id not in visited:
                        queue.append((source_id, current_depth + 1))
        
        return {
            "nodes": list(nodes.values()),
            "edges": edges
        }
    
    def xǁRelationshipManagerǁget_relationship_graph__mutmut_1(
        self,
        memory_ids: List[int],
        depth: int = 3
    ) -> Dict[str, Any]:
        """
        Get subgraph of relationships around given memories.
        
        Args:
            memory_ids: List of memory IDs to start from
            depth: Maximum depth of traversal (default: 2)
            
        Returns:
            Dictionary with "nodes" and "edges" representing the graph
        """
        nodes: Dict[int, Dict[str, Any]] = {}
        edges: List[Dict[str, Any]] = []
        visited: set = set()
        
        # BFS traversal
        queue: List[Tuple[int, int]] = [(mem_id, 0) for mem_id in memory_ids]  # (memory_id, current_depth)
        
        while queue:
            current_id, current_depth = queue.pop(0)
            
            if current_id in visited or current_depth > depth:
                continue
            
            visited.add(current_id)
            
            # Get memory
            memory = self.storage.get_memory(current_id)
            if not memory:
                continue
            
            # Add node
            nodes[current_id] = {
                "id": current_id,
                "namespace": memory.namespace,
                "text": memory.text[:50] + "..." if len(memory.text) > 50 else memory.text,
                "importance": memory.importance
            }
            
            # If not at max depth, explore relationships
            if current_depth < depth:
                # Get outgoing relationships
                relationships = self.storage.get_relationships(source_id=current_id)
                for rel in relationships:
                    target_id = rel.target_id
                    
                    # Add edge
                    edges.append({
                        "source": current_id,
                        "target": target_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if target_id not in visited:
                        queue.append((target_id, current_depth + 1))
                
                # Get incoming relationships
                relationships = self.storage.get_relationships(target_id=current_id)
                for rel in relationships:
                    source_id = rel.source_id
                    
                    # Add edge
                    edges.append({
                        "source": source_id,
                        "target": current_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if source_id not in visited:
                        queue.append((source_id, current_depth + 1))
        
        return {
            "nodes": list(nodes.values()),
            "edges": edges
        }
    
    def xǁRelationshipManagerǁget_relationship_graph__mutmut_2(
        self,
        memory_ids: List[int],
        depth: int = 2
    ) -> Dict[str, Any]:
        """
        Get subgraph of relationships around given memories.
        
        Args:
            memory_ids: List of memory IDs to start from
            depth: Maximum depth of traversal (default: 2)
            
        Returns:
            Dictionary with "nodes" and "edges" representing the graph
        """
        nodes: Dict[int, Dict[str, Any]] = None
        edges: List[Dict[str, Any]] = []
        visited: set = set()
        
        # BFS traversal
        queue: List[Tuple[int, int]] = [(mem_id, 0) for mem_id in memory_ids]  # (memory_id, current_depth)
        
        while queue:
            current_id, current_depth = queue.pop(0)
            
            if current_id in visited or current_depth > depth:
                continue
            
            visited.add(current_id)
            
            # Get memory
            memory = self.storage.get_memory(current_id)
            if not memory:
                continue
            
            # Add node
            nodes[current_id] = {
                "id": current_id,
                "namespace": memory.namespace,
                "text": memory.text[:50] + "..." if len(memory.text) > 50 else memory.text,
                "importance": memory.importance
            }
            
            # If not at max depth, explore relationships
            if current_depth < depth:
                # Get outgoing relationships
                relationships = self.storage.get_relationships(source_id=current_id)
                for rel in relationships:
                    target_id = rel.target_id
                    
                    # Add edge
                    edges.append({
                        "source": current_id,
                        "target": target_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if target_id not in visited:
                        queue.append((target_id, current_depth + 1))
                
                # Get incoming relationships
                relationships = self.storage.get_relationships(target_id=current_id)
                for rel in relationships:
                    source_id = rel.source_id
                    
                    # Add edge
                    edges.append({
                        "source": source_id,
                        "target": current_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if source_id not in visited:
                        queue.append((source_id, current_depth + 1))
        
        return {
            "nodes": list(nodes.values()),
            "edges": edges
        }
    
    def xǁRelationshipManagerǁget_relationship_graph__mutmut_3(
        self,
        memory_ids: List[int],
        depth: int = 2
    ) -> Dict[str, Any]:
        """
        Get subgraph of relationships around given memories.
        
        Args:
            memory_ids: List of memory IDs to start from
            depth: Maximum depth of traversal (default: 2)
            
        Returns:
            Dictionary with "nodes" and "edges" representing the graph
        """
        nodes: Dict[int, Dict[str, Any]] = {}
        edges: List[Dict[str, Any]] = None
        visited: set = set()
        
        # BFS traversal
        queue: List[Tuple[int, int]] = [(mem_id, 0) for mem_id in memory_ids]  # (memory_id, current_depth)
        
        while queue:
            current_id, current_depth = queue.pop(0)
            
            if current_id in visited or current_depth > depth:
                continue
            
            visited.add(current_id)
            
            # Get memory
            memory = self.storage.get_memory(current_id)
            if not memory:
                continue
            
            # Add node
            nodes[current_id] = {
                "id": current_id,
                "namespace": memory.namespace,
                "text": memory.text[:50] + "..." if len(memory.text) > 50 else memory.text,
                "importance": memory.importance
            }
            
            # If not at max depth, explore relationships
            if current_depth < depth:
                # Get outgoing relationships
                relationships = self.storage.get_relationships(source_id=current_id)
                for rel in relationships:
                    target_id = rel.target_id
                    
                    # Add edge
                    edges.append({
                        "source": current_id,
                        "target": target_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if target_id not in visited:
                        queue.append((target_id, current_depth + 1))
                
                # Get incoming relationships
                relationships = self.storage.get_relationships(target_id=current_id)
                for rel in relationships:
                    source_id = rel.source_id
                    
                    # Add edge
                    edges.append({
                        "source": source_id,
                        "target": current_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if source_id not in visited:
                        queue.append((source_id, current_depth + 1))
        
        return {
            "nodes": list(nodes.values()),
            "edges": edges
        }
    
    def xǁRelationshipManagerǁget_relationship_graph__mutmut_4(
        self,
        memory_ids: List[int],
        depth: int = 2
    ) -> Dict[str, Any]:
        """
        Get subgraph of relationships around given memories.
        
        Args:
            memory_ids: List of memory IDs to start from
            depth: Maximum depth of traversal (default: 2)
            
        Returns:
            Dictionary with "nodes" and "edges" representing the graph
        """
        nodes: Dict[int, Dict[str, Any]] = {}
        edges: List[Dict[str, Any]] = []
        visited: set = None
        
        # BFS traversal
        queue: List[Tuple[int, int]] = [(mem_id, 0) for mem_id in memory_ids]  # (memory_id, current_depth)
        
        while queue:
            current_id, current_depth = queue.pop(0)
            
            if current_id in visited or current_depth > depth:
                continue
            
            visited.add(current_id)
            
            # Get memory
            memory = self.storage.get_memory(current_id)
            if not memory:
                continue
            
            # Add node
            nodes[current_id] = {
                "id": current_id,
                "namespace": memory.namespace,
                "text": memory.text[:50] + "..." if len(memory.text) > 50 else memory.text,
                "importance": memory.importance
            }
            
            # If not at max depth, explore relationships
            if current_depth < depth:
                # Get outgoing relationships
                relationships = self.storage.get_relationships(source_id=current_id)
                for rel in relationships:
                    target_id = rel.target_id
                    
                    # Add edge
                    edges.append({
                        "source": current_id,
                        "target": target_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if target_id not in visited:
                        queue.append((target_id, current_depth + 1))
                
                # Get incoming relationships
                relationships = self.storage.get_relationships(target_id=current_id)
                for rel in relationships:
                    source_id = rel.source_id
                    
                    # Add edge
                    edges.append({
                        "source": source_id,
                        "target": current_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if source_id not in visited:
                        queue.append((source_id, current_depth + 1))
        
        return {
            "nodes": list(nodes.values()),
            "edges": edges
        }
    
    def xǁRelationshipManagerǁget_relationship_graph__mutmut_5(
        self,
        memory_ids: List[int],
        depth: int = 2
    ) -> Dict[str, Any]:
        """
        Get subgraph of relationships around given memories.
        
        Args:
            memory_ids: List of memory IDs to start from
            depth: Maximum depth of traversal (default: 2)
            
        Returns:
            Dictionary with "nodes" and "edges" representing the graph
        """
        nodes: Dict[int, Dict[str, Any]] = {}
        edges: List[Dict[str, Any]] = []
        visited: set = set()
        
        # BFS traversal
        queue: List[Tuple[int, int]] = None  # (memory_id, current_depth)
        
        while queue:
            current_id, current_depth = queue.pop(0)
            
            if current_id in visited or current_depth > depth:
                continue
            
            visited.add(current_id)
            
            # Get memory
            memory = self.storage.get_memory(current_id)
            if not memory:
                continue
            
            # Add node
            nodes[current_id] = {
                "id": current_id,
                "namespace": memory.namespace,
                "text": memory.text[:50] + "..." if len(memory.text) > 50 else memory.text,
                "importance": memory.importance
            }
            
            # If not at max depth, explore relationships
            if current_depth < depth:
                # Get outgoing relationships
                relationships = self.storage.get_relationships(source_id=current_id)
                for rel in relationships:
                    target_id = rel.target_id
                    
                    # Add edge
                    edges.append({
                        "source": current_id,
                        "target": target_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if target_id not in visited:
                        queue.append((target_id, current_depth + 1))
                
                # Get incoming relationships
                relationships = self.storage.get_relationships(target_id=current_id)
                for rel in relationships:
                    source_id = rel.source_id
                    
                    # Add edge
                    edges.append({
                        "source": source_id,
                        "target": current_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if source_id not in visited:
                        queue.append((source_id, current_depth + 1))
        
        return {
            "nodes": list(nodes.values()),
            "edges": edges
        }
    
    def xǁRelationshipManagerǁget_relationship_graph__mutmut_6(
        self,
        memory_ids: List[int],
        depth: int = 2
    ) -> Dict[str, Any]:
        """
        Get subgraph of relationships around given memories.
        
        Args:
            memory_ids: List of memory IDs to start from
            depth: Maximum depth of traversal (default: 2)
            
        Returns:
            Dictionary with "nodes" and "edges" representing the graph
        """
        nodes: Dict[int, Dict[str, Any]] = {}
        edges: List[Dict[str, Any]] = []
        visited: set = set()
        
        # BFS traversal
        queue: List[Tuple[int, int]] = [(mem_id, 1) for mem_id in memory_ids]  # (memory_id, current_depth)
        
        while queue:
            current_id, current_depth = queue.pop(0)
            
            if current_id in visited or current_depth > depth:
                continue
            
            visited.add(current_id)
            
            # Get memory
            memory = self.storage.get_memory(current_id)
            if not memory:
                continue
            
            # Add node
            nodes[current_id] = {
                "id": current_id,
                "namespace": memory.namespace,
                "text": memory.text[:50] + "..." if len(memory.text) > 50 else memory.text,
                "importance": memory.importance
            }
            
            # If not at max depth, explore relationships
            if current_depth < depth:
                # Get outgoing relationships
                relationships = self.storage.get_relationships(source_id=current_id)
                for rel in relationships:
                    target_id = rel.target_id
                    
                    # Add edge
                    edges.append({
                        "source": current_id,
                        "target": target_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if target_id not in visited:
                        queue.append((target_id, current_depth + 1))
                
                # Get incoming relationships
                relationships = self.storage.get_relationships(target_id=current_id)
                for rel in relationships:
                    source_id = rel.source_id
                    
                    # Add edge
                    edges.append({
                        "source": source_id,
                        "target": current_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if source_id not in visited:
                        queue.append((source_id, current_depth + 1))
        
        return {
            "nodes": list(nodes.values()),
            "edges": edges
        }
    
    def xǁRelationshipManagerǁget_relationship_graph__mutmut_7(
        self,
        memory_ids: List[int],
        depth: int = 2
    ) -> Dict[str, Any]:
        """
        Get subgraph of relationships around given memories.
        
        Args:
            memory_ids: List of memory IDs to start from
            depth: Maximum depth of traversal (default: 2)
            
        Returns:
            Dictionary with "nodes" and "edges" representing the graph
        """
        nodes: Dict[int, Dict[str, Any]] = {}
        edges: List[Dict[str, Any]] = []
        visited: set = set()
        
        # BFS traversal
        queue: List[Tuple[int, int]] = [(mem_id, 0) for mem_id in memory_ids]  # (memory_id, current_depth)
        
        while queue:
            current_id, current_depth = None
            
            if current_id in visited or current_depth > depth:
                continue
            
            visited.add(current_id)
            
            # Get memory
            memory = self.storage.get_memory(current_id)
            if not memory:
                continue
            
            # Add node
            nodes[current_id] = {
                "id": current_id,
                "namespace": memory.namespace,
                "text": memory.text[:50] + "..." if len(memory.text) > 50 else memory.text,
                "importance": memory.importance
            }
            
            # If not at max depth, explore relationships
            if current_depth < depth:
                # Get outgoing relationships
                relationships = self.storage.get_relationships(source_id=current_id)
                for rel in relationships:
                    target_id = rel.target_id
                    
                    # Add edge
                    edges.append({
                        "source": current_id,
                        "target": target_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if target_id not in visited:
                        queue.append((target_id, current_depth + 1))
                
                # Get incoming relationships
                relationships = self.storage.get_relationships(target_id=current_id)
                for rel in relationships:
                    source_id = rel.source_id
                    
                    # Add edge
                    edges.append({
                        "source": source_id,
                        "target": current_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if source_id not in visited:
                        queue.append((source_id, current_depth + 1))
        
        return {
            "nodes": list(nodes.values()),
            "edges": edges
        }
    
    def xǁRelationshipManagerǁget_relationship_graph__mutmut_8(
        self,
        memory_ids: List[int],
        depth: int = 2
    ) -> Dict[str, Any]:
        """
        Get subgraph of relationships around given memories.
        
        Args:
            memory_ids: List of memory IDs to start from
            depth: Maximum depth of traversal (default: 2)
            
        Returns:
            Dictionary with "nodes" and "edges" representing the graph
        """
        nodes: Dict[int, Dict[str, Any]] = {}
        edges: List[Dict[str, Any]] = []
        visited: set = set()
        
        # BFS traversal
        queue: List[Tuple[int, int]] = [(mem_id, 0) for mem_id in memory_ids]  # (memory_id, current_depth)
        
        while queue:
            current_id, current_depth = queue.pop(None)
            
            if current_id in visited or current_depth > depth:
                continue
            
            visited.add(current_id)
            
            # Get memory
            memory = self.storage.get_memory(current_id)
            if not memory:
                continue
            
            # Add node
            nodes[current_id] = {
                "id": current_id,
                "namespace": memory.namespace,
                "text": memory.text[:50] + "..." if len(memory.text) > 50 else memory.text,
                "importance": memory.importance
            }
            
            # If not at max depth, explore relationships
            if current_depth < depth:
                # Get outgoing relationships
                relationships = self.storage.get_relationships(source_id=current_id)
                for rel in relationships:
                    target_id = rel.target_id
                    
                    # Add edge
                    edges.append({
                        "source": current_id,
                        "target": target_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if target_id not in visited:
                        queue.append((target_id, current_depth + 1))
                
                # Get incoming relationships
                relationships = self.storage.get_relationships(target_id=current_id)
                for rel in relationships:
                    source_id = rel.source_id
                    
                    # Add edge
                    edges.append({
                        "source": source_id,
                        "target": current_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if source_id not in visited:
                        queue.append((source_id, current_depth + 1))
        
        return {
            "nodes": list(nodes.values()),
            "edges": edges
        }
    
    def xǁRelationshipManagerǁget_relationship_graph__mutmut_9(
        self,
        memory_ids: List[int],
        depth: int = 2
    ) -> Dict[str, Any]:
        """
        Get subgraph of relationships around given memories.
        
        Args:
            memory_ids: List of memory IDs to start from
            depth: Maximum depth of traversal (default: 2)
            
        Returns:
            Dictionary with "nodes" and "edges" representing the graph
        """
        nodes: Dict[int, Dict[str, Any]] = {}
        edges: List[Dict[str, Any]] = []
        visited: set = set()
        
        # BFS traversal
        queue: List[Tuple[int, int]] = [(mem_id, 0) for mem_id in memory_ids]  # (memory_id, current_depth)
        
        while queue:
            current_id, current_depth = queue.pop(1)
            
            if current_id in visited or current_depth > depth:
                continue
            
            visited.add(current_id)
            
            # Get memory
            memory = self.storage.get_memory(current_id)
            if not memory:
                continue
            
            # Add node
            nodes[current_id] = {
                "id": current_id,
                "namespace": memory.namespace,
                "text": memory.text[:50] + "..." if len(memory.text) > 50 else memory.text,
                "importance": memory.importance
            }
            
            # If not at max depth, explore relationships
            if current_depth < depth:
                # Get outgoing relationships
                relationships = self.storage.get_relationships(source_id=current_id)
                for rel in relationships:
                    target_id = rel.target_id
                    
                    # Add edge
                    edges.append({
                        "source": current_id,
                        "target": target_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if target_id not in visited:
                        queue.append((target_id, current_depth + 1))
                
                # Get incoming relationships
                relationships = self.storage.get_relationships(target_id=current_id)
                for rel in relationships:
                    source_id = rel.source_id
                    
                    # Add edge
                    edges.append({
                        "source": source_id,
                        "target": current_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if source_id not in visited:
                        queue.append((source_id, current_depth + 1))
        
        return {
            "nodes": list(nodes.values()),
            "edges": edges
        }
    
    def xǁRelationshipManagerǁget_relationship_graph__mutmut_10(
        self,
        memory_ids: List[int],
        depth: int = 2
    ) -> Dict[str, Any]:
        """
        Get subgraph of relationships around given memories.
        
        Args:
            memory_ids: List of memory IDs to start from
            depth: Maximum depth of traversal (default: 2)
            
        Returns:
            Dictionary with "nodes" and "edges" representing the graph
        """
        nodes: Dict[int, Dict[str, Any]] = {}
        edges: List[Dict[str, Any]] = []
        visited: set = set()
        
        # BFS traversal
        queue: List[Tuple[int, int]] = [(mem_id, 0) for mem_id in memory_ids]  # (memory_id, current_depth)
        
        while queue:
            current_id, current_depth = queue.pop(0)
            
            if current_id in visited and current_depth > depth:
                continue
            
            visited.add(current_id)
            
            # Get memory
            memory = self.storage.get_memory(current_id)
            if not memory:
                continue
            
            # Add node
            nodes[current_id] = {
                "id": current_id,
                "namespace": memory.namespace,
                "text": memory.text[:50] + "..." if len(memory.text) > 50 else memory.text,
                "importance": memory.importance
            }
            
            # If not at max depth, explore relationships
            if current_depth < depth:
                # Get outgoing relationships
                relationships = self.storage.get_relationships(source_id=current_id)
                for rel in relationships:
                    target_id = rel.target_id
                    
                    # Add edge
                    edges.append({
                        "source": current_id,
                        "target": target_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if target_id not in visited:
                        queue.append((target_id, current_depth + 1))
                
                # Get incoming relationships
                relationships = self.storage.get_relationships(target_id=current_id)
                for rel in relationships:
                    source_id = rel.source_id
                    
                    # Add edge
                    edges.append({
                        "source": source_id,
                        "target": current_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if source_id not in visited:
                        queue.append((source_id, current_depth + 1))
        
        return {
            "nodes": list(nodes.values()),
            "edges": edges
        }
    
    def xǁRelationshipManagerǁget_relationship_graph__mutmut_11(
        self,
        memory_ids: List[int],
        depth: int = 2
    ) -> Dict[str, Any]:
        """
        Get subgraph of relationships around given memories.
        
        Args:
            memory_ids: List of memory IDs to start from
            depth: Maximum depth of traversal (default: 2)
            
        Returns:
            Dictionary with "nodes" and "edges" representing the graph
        """
        nodes: Dict[int, Dict[str, Any]] = {}
        edges: List[Dict[str, Any]] = []
        visited: set = set()
        
        # BFS traversal
        queue: List[Tuple[int, int]] = [(mem_id, 0) for mem_id in memory_ids]  # (memory_id, current_depth)
        
        while queue:
            current_id, current_depth = queue.pop(0)
            
            if current_id not in visited or current_depth > depth:
                continue
            
            visited.add(current_id)
            
            # Get memory
            memory = self.storage.get_memory(current_id)
            if not memory:
                continue
            
            # Add node
            nodes[current_id] = {
                "id": current_id,
                "namespace": memory.namespace,
                "text": memory.text[:50] + "..." if len(memory.text) > 50 else memory.text,
                "importance": memory.importance
            }
            
            # If not at max depth, explore relationships
            if current_depth < depth:
                # Get outgoing relationships
                relationships = self.storage.get_relationships(source_id=current_id)
                for rel in relationships:
                    target_id = rel.target_id
                    
                    # Add edge
                    edges.append({
                        "source": current_id,
                        "target": target_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if target_id not in visited:
                        queue.append((target_id, current_depth + 1))
                
                # Get incoming relationships
                relationships = self.storage.get_relationships(target_id=current_id)
                for rel in relationships:
                    source_id = rel.source_id
                    
                    # Add edge
                    edges.append({
                        "source": source_id,
                        "target": current_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if source_id not in visited:
                        queue.append((source_id, current_depth + 1))
        
        return {
            "nodes": list(nodes.values()),
            "edges": edges
        }
    
    def xǁRelationshipManagerǁget_relationship_graph__mutmut_12(
        self,
        memory_ids: List[int],
        depth: int = 2
    ) -> Dict[str, Any]:
        """
        Get subgraph of relationships around given memories.
        
        Args:
            memory_ids: List of memory IDs to start from
            depth: Maximum depth of traversal (default: 2)
            
        Returns:
            Dictionary with "nodes" and "edges" representing the graph
        """
        nodes: Dict[int, Dict[str, Any]] = {}
        edges: List[Dict[str, Any]] = []
        visited: set = set()
        
        # BFS traversal
        queue: List[Tuple[int, int]] = [(mem_id, 0) for mem_id in memory_ids]  # (memory_id, current_depth)
        
        while queue:
            current_id, current_depth = queue.pop(0)
            
            if current_id in visited or current_depth >= depth:
                continue
            
            visited.add(current_id)
            
            # Get memory
            memory = self.storage.get_memory(current_id)
            if not memory:
                continue
            
            # Add node
            nodes[current_id] = {
                "id": current_id,
                "namespace": memory.namespace,
                "text": memory.text[:50] + "..." if len(memory.text) > 50 else memory.text,
                "importance": memory.importance
            }
            
            # If not at max depth, explore relationships
            if current_depth < depth:
                # Get outgoing relationships
                relationships = self.storage.get_relationships(source_id=current_id)
                for rel in relationships:
                    target_id = rel.target_id
                    
                    # Add edge
                    edges.append({
                        "source": current_id,
                        "target": target_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if target_id not in visited:
                        queue.append((target_id, current_depth + 1))
                
                # Get incoming relationships
                relationships = self.storage.get_relationships(target_id=current_id)
                for rel in relationships:
                    source_id = rel.source_id
                    
                    # Add edge
                    edges.append({
                        "source": source_id,
                        "target": current_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if source_id not in visited:
                        queue.append((source_id, current_depth + 1))
        
        return {
            "nodes": list(nodes.values()),
            "edges": edges
        }
    
    def xǁRelationshipManagerǁget_relationship_graph__mutmut_13(
        self,
        memory_ids: List[int],
        depth: int = 2
    ) -> Dict[str, Any]:
        """
        Get subgraph of relationships around given memories.
        
        Args:
            memory_ids: List of memory IDs to start from
            depth: Maximum depth of traversal (default: 2)
            
        Returns:
            Dictionary with "nodes" and "edges" representing the graph
        """
        nodes: Dict[int, Dict[str, Any]] = {}
        edges: List[Dict[str, Any]] = []
        visited: set = set()
        
        # BFS traversal
        queue: List[Tuple[int, int]] = [(mem_id, 0) for mem_id in memory_ids]  # (memory_id, current_depth)
        
        while queue:
            current_id, current_depth = queue.pop(0)
            
            if current_id in visited or current_depth > depth:
                break
            
            visited.add(current_id)
            
            # Get memory
            memory = self.storage.get_memory(current_id)
            if not memory:
                continue
            
            # Add node
            nodes[current_id] = {
                "id": current_id,
                "namespace": memory.namespace,
                "text": memory.text[:50] + "..." if len(memory.text) > 50 else memory.text,
                "importance": memory.importance
            }
            
            # If not at max depth, explore relationships
            if current_depth < depth:
                # Get outgoing relationships
                relationships = self.storage.get_relationships(source_id=current_id)
                for rel in relationships:
                    target_id = rel.target_id
                    
                    # Add edge
                    edges.append({
                        "source": current_id,
                        "target": target_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if target_id not in visited:
                        queue.append((target_id, current_depth + 1))
                
                # Get incoming relationships
                relationships = self.storage.get_relationships(target_id=current_id)
                for rel in relationships:
                    source_id = rel.source_id
                    
                    # Add edge
                    edges.append({
                        "source": source_id,
                        "target": current_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if source_id not in visited:
                        queue.append((source_id, current_depth + 1))
        
        return {
            "nodes": list(nodes.values()),
            "edges": edges
        }
    
    def xǁRelationshipManagerǁget_relationship_graph__mutmut_14(
        self,
        memory_ids: List[int],
        depth: int = 2
    ) -> Dict[str, Any]:
        """
        Get subgraph of relationships around given memories.
        
        Args:
            memory_ids: List of memory IDs to start from
            depth: Maximum depth of traversal (default: 2)
            
        Returns:
            Dictionary with "nodes" and "edges" representing the graph
        """
        nodes: Dict[int, Dict[str, Any]] = {}
        edges: List[Dict[str, Any]] = []
        visited: set = set()
        
        # BFS traversal
        queue: List[Tuple[int, int]] = [(mem_id, 0) for mem_id in memory_ids]  # (memory_id, current_depth)
        
        while queue:
            current_id, current_depth = queue.pop(0)
            
            if current_id in visited or current_depth > depth:
                continue
            
            visited.add(None)
            
            # Get memory
            memory = self.storage.get_memory(current_id)
            if not memory:
                continue
            
            # Add node
            nodes[current_id] = {
                "id": current_id,
                "namespace": memory.namespace,
                "text": memory.text[:50] + "..." if len(memory.text) > 50 else memory.text,
                "importance": memory.importance
            }
            
            # If not at max depth, explore relationships
            if current_depth < depth:
                # Get outgoing relationships
                relationships = self.storage.get_relationships(source_id=current_id)
                for rel in relationships:
                    target_id = rel.target_id
                    
                    # Add edge
                    edges.append({
                        "source": current_id,
                        "target": target_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if target_id not in visited:
                        queue.append((target_id, current_depth + 1))
                
                # Get incoming relationships
                relationships = self.storage.get_relationships(target_id=current_id)
                for rel in relationships:
                    source_id = rel.source_id
                    
                    # Add edge
                    edges.append({
                        "source": source_id,
                        "target": current_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if source_id not in visited:
                        queue.append((source_id, current_depth + 1))
        
        return {
            "nodes": list(nodes.values()),
            "edges": edges
        }
    
    def xǁRelationshipManagerǁget_relationship_graph__mutmut_15(
        self,
        memory_ids: List[int],
        depth: int = 2
    ) -> Dict[str, Any]:
        """
        Get subgraph of relationships around given memories.
        
        Args:
            memory_ids: List of memory IDs to start from
            depth: Maximum depth of traversal (default: 2)
            
        Returns:
            Dictionary with "nodes" and "edges" representing the graph
        """
        nodes: Dict[int, Dict[str, Any]] = {}
        edges: List[Dict[str, Any]] = []
        visited: set = set()
        
        # BFS traversal
        queue: List[Tuple[int, int]] = [(mem_id, 0) for mem_id in memory_ids]  # (memory_id, current_depth)
        
        while queue:
            current_id, current_depth = queue.pop(0)
            
            if current_id in visited or current_depth > depth:
                continue
            
            visited.add(current_id)
            
            # Get memory
            memory = None
            if not memory:
                continue
            
            # Add node
            nodes[current_id] = {
                "id": current_id,
                "namespace": memory.namespace,
                "text": memory.text[:50] + "..." if len(memory.text) > 50 else memory.text,
                "importance": memory.importance
            }
            
            # If not at max depth, explore relationships
            if current_depth < depth:
                # Get outgoing relationships
                relationships = self.storage.get_relationships(source_id=current_id)
                for rel in relationships:
                    target_id = rel.target_id
                    
                    # Add edge
                    edges.append({
                        "source": current_id,
                        "target": target_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if target_id not in visited:
                        queue.append((target_id, current_depth + 1))
                
                # Get incoming relationships
                relationships = self.storage.get_relationships(target_id=current_id)
                for rel in relationships:
                    source_id = rel.source_id
                    
                    # Add edge
                    edges.append({
                        "source": source_id,
                        "target": current_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if source_id not in visited:
                        queue.append((source_id, current_depth + 1))
        
        return {
            "nodes": list(nodes.values()),
            "edges": edges
        }
    
    def xǁRelationshipManagerǁget_relationship_graph__mutmut_16(
        self,
        memory_ids: List[int],
        depth: int = 2
    ) -> Dict[str, Any]:
        """
        Get subgraph of relationships around given memories.
        
        Args:
            memory_ids: List of memory IDs to start from
            depth: Maximum depth of traversal (default: 2)
            
        Returns:
            Dictionary with "nodes" and "edges" representing the graph
        """
        nodes: Dict[int, Dict[str, Any]] = {}
        edges: List[Dict[str, Any]] = []
        visited: set = set()
        
        # BFS traversal
        queue: List[Tuple[int, int]] = [(mem_id, 0) for mem_id in memory_ids]  # (memory_id, current_depth)
        
        while queue:
            current_id, current_depth = queue.pop(0)
            
            if current_id in visited or current_depth > depth:
                continue
            
            visited.add(current_id)
            
            # Get memory
            memory = self.storage.get_memory(None)
            if not memory:
                continue
            
            # Add node
            nodes[current_id] = {
                "id": current_id,
                "namespace": memory.namespace,
                "text": memory.text[:50] + "..." if len(memory.text) > 50 else memory.text,
                "importance": memory.importance
            }
            
            # If not at max depth, explore relationships
            if current_depth < depth:
                # Get outgoing relationships
                relationships = self.storage.get_relationships(source_id=current_id)
                for rel in relationships:
                    target_id = rel.target_id
                    
                    # Add edge
                    edges.append({
                        "source": current_id,
                        "target": target_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if target_id not in visited:
                        queue.append((target_id, current_depth + 1))
                
                # Get incoming relationships
                relationships = self.storage.get_relationships(target_id=current_id)
                for rel in relationships:
                    source_id = rel.source_id
                    
                    # Add edge
                    edges.append({
                        "source": source_id,
                        "target": current_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if source_id not in visited:
                        queue.append((source_id, current_depth + 1))
        
        return {
            "nodes": list(nodes.values()),
            "edges": edges
        }
    
    def xǁRelationshipManagerǁget_relationship_graph__mutmut_17(
        self,
        memory_ids: List[int],
        depth: int = 2
    ) -> Dict[str, Any]:
        """
        Get subgraph of relationships around given memories.
        
        Args:
            memory_ids: List of memory IDs to start from
            depth: Maximum depth of traversal (default: 2)
            
        Returns:
            Dictionary with "nodes" and "edges" representing the graph
        """
        nodes: Dict[int, Dict[str, Any]] = {}
        edges: List[Dict[str, Any]] = []
        visited: set = set()
        
        # BFS traversal
        queue: List[Tuple[int, int]] = [(mem_id, 0) for mem_id in memory_ids]  # (memory_id, current_depth)
        
        while queue:
            current_id, current_depth = queue.pop(0)
            
            if current_id in visited or current_depth > depth:
                continue
            
            visited.add(current_id)
            
            # Get memory
            memory = self.storage.get_memory(current_id)
            if memory:
                continue
            
            # Add node
            nodes[current_id] = {
                "id": current_id,
                "namespace": memory.namespace,
                "text": memory.text[:50] + "..." if len(memory.text) > 50 else memory.text,
                "importance": memory.importance
            }
            
            # If not at max depth, explore relationships
            if current_depth < depth:
                # Get outgoing relationships
                relationships = self.storage.get_relationships(source_id=current_id)
                for rel in relationships:
                    target_id = rel.target_id
                    
                    # Add edge
                    edges.append({
                        "source": current_id,
                        "target": target_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if target_id not in visited:
                        queue.append((target_id, current_depth + 1))
                
                # Get incoming relationships
                relationships = self.storage.get_relationships(target_id=current_id)
                for rel in relationships:
                    source_id = rel.source_id
                    
                    # Add edge
                    edges.append({
                        "source": source_id,
                        "target": current_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if source_id not in visited:
                        queue.append((source_id, current_depth + 1))
        
        return {
            "nodes": list(nodes.values()),
            "edges": edges
        }
    
    def xǁRelationshipManagerǁget_relationship_graph__mutmut_18(
        self,
        memory_ids: List[int],
        depth: int = 2
    ) -> Dict[str, Any]:
        """
        Get subgraph of relationships around given memories.
        
        Args:
            memory_ids: List of memory IDs to start from
            depth: Maximum depth of traversal (default: 2)
            
        Returns:
            Dictionary with "nodes" and "edges" representing the graph
        """
        nodes: Dict[int, Dict[str, Any]] = {}
        edges: List[Dict[str, Any]] = []
        visited: set = set()
        
        # BFS traversal
        queue: List[Tuple[int, int]] = [(mem_id, 0) for mem_id in memory_ids]  # (memory_id, current_depth)
        
        while queue:
            current_id, current_depth = queue.pop(0)
            
            if current_id in visited or current_depth > depth:
                continue
            
            visited.add(current_id)
            
            # Get memory
            memory = self.storage.get_memory(current_id)
            if not memory:
                break
            
            # Add node
            nodes[current_id] = {
                "id": current_id,
                "namespace": memory.namespace,
                "text": memory.text[:50] + "..." if len(memory.text) > 50 else memory.text,
                "importance": memory.importance
            }
            
            # If not at max depth, explore relationships
            if current_depth < depth:
                # Get outgoing relationships
                relationships = self.storage.get_relationships(source_id=current_id)
                for rel in relationships:
                    target_id = rel.target_id
                    
                    # Add edge
                    edges.append({
                        "source": current_id,
                        "target": target_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if target_id not in visited:
                        queue.append((target_id, current_depth + 1))
                
                # Get incoming relationships
                relationships = self.storage.get_relationships(target_id=current_id)
                for rel in relationships:
                    source_id = rel.source_id
                    
                    # Add edge
                    edges.append({
                        "source": source_id,
                        "target": current_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if source_id not in visited:
                        queue.append((source_id, current_depth + 1))
        
        return {
            "nodes": list(nodes.values()),
            "edges": edges
        }
    
    def xǁRelationshipManagerǁget_relationship_graph__mutmut_19(
        self,
        memory_ids: List[int],
        depth: int = 2
    ) -> Dict[str, Any]:
        """
        Get subgraph of relationships around given memories.
        
        Args:
            memory_ids: List of memory IDs to start from
            depth: Maximum depth of traversal (default: 2)
            
        Returns:
            Dictionary with "nodes" and "edges" representing the graph
        """
        nodes: Dict[int, Dict[str, Any]] = {}
        edges: List[Dict[str, Any]] = []
        visited: set = set()
        
        # BFS traversal
        queue: List[Tuple[int, int]] = [(mem_id, 0) for mem_id in memory_ids]  # (memory_id, current_depth)
        
        while queue:
            current_id, current_depth = queue.pop(0)
            
            if current_id in visited or current_depth > depth:
                continue
            
            visited.add(current_id)
            
            # Get memory
            memory = self.storage.get_memory(current_id)
            if not memory:
                continue
            
            # Add node
            nodes[current_id] = None
            
            # If not at max depth, explore relationships
            if current_depth < depth:
                # Get outgoing relationships
                relationships = self.storage.get_relationships(source_id=current_id)
                for rel in relationships:
                    target_id = rel.target_id
                    
                    # Add edge
                    edges.append({
                        "source": current_id,
                        "target": target_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if target_id not in visited:
                        queue.append((target_id, current_depth + 1))
                
                # Get incoming relationships
                relationships = self.storage.get_relationships(target_id=current_id)
                for rel in relationships:
                    source_id = rel.source_id
                    
                    # Add edge
                    edges.append({
                        "source": source_id,
                        "target": current_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if source_id not in visited:
                        queue.append((source_id, current_depth + 1))
        
        return {
            "nodes": list(nodes.values()),
            "edges": edges
        }
    
    def xǁRelationshipManagerǁget_relationship_graph__mutmut_20(
        self,
        memory_ids: List[int],
        depth: int = 2
    ) -> Dict[str, Any]:
        """
        Get subgraph of relationships around given memories.
        
        Args:
            memory_ids: List of memory IDs to start from
            depth: Maximum depth of traversal (default: 2)
            
        Returns:
            Dictionary with "nodes" and "edges" representing the graph
        """
        nodes: Dict[int, Dict[str, Any]] = {}
        edges: List[Dict[str, Any]] = []
        visited: set = set()
        
        # BFS traversal
        queue: List[Tuple[int, int]] = [(mem_id, 0) for mem_id in memory_ids]  # (memory_id, current_depth)
        
        while queue:
            current_id, current_depth = queue.pop(0)
            
            if current_id in visited or current_depth > depth:
                continue
            
            visited.add(current_id)
            
            # Get memory
            memory = self.storage.get_memory(current_id)
            if not memory:
                continue
            
            # Add node
            nodes[current_id] = {
                "XXidXX": current_id,
                "namespace": memory.namespace,
                "text": memory.text[:50] + "..." if len(memory.text) > 50 else memory.text,
                "importance": memory.importance
            }
            
            # If not at max depth, explore relationships
            if current_depth < depth:
                # Get outgoing relationships
                relationships = self.storage.get_relationships(source_id=current_id)
                for rel in relationships:
                    target_id = rel.target_id
                    
                    # Add edge
                    edges.append({
                        "source": current_id,
                        "target": target_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if target_id not in visited:
                        queue.append((target_id, current_depth + 1))
                
                # Get incoming relationships
                relationships = self.storage.get_relationships(target_id=current_id)
                for rel in relationships:
                    source_id = rel.source_id
                    
                    # Add edge
                    edges.append({
                        "source": source_id,
                        "target": current_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if source_id not in visited:
                        queue.append((source_id, current_depth + 1))
        
        return {
            "nodes": list(nodes.values()),
            "edges": edges
        }
    
    def xǁRelationshipManagerǁget_relationship_graph__mutmut_21(
        self,
        memory_ids: List[int],
        depth: int = 2
    ) -> Dict[str, Any]:
        """
        Get subgraph of relationships around given memories.
        
        Args:
            memory_ids: List of memory IDs to start from
            depth: Maximum depth of traversal (default: 2)
            
        Returns:
            Dictionary with "nodes" and "edges" representing the graph
        """
        nodes: Dict[int, Dict[str, Any]] = {}
        edges: List[Dict[str, Any]] = []
        visited: set = set()
        
        # BFS traversal
        queue: List[Tuple[int, int]] = [(mem_id, 0) for mem_id in memory_ids]  # (memory_id, current_depth)
        
        while queue:
            current_id, current_depth = queue.pop(0)
            
            if current_id in visited or current_depth > depth:
                continue
            
            visited.add(current_id)
            
            # Get memory
            memory = self.storage.get_memory(current_id)
            if not memory:
                continue
            
            # Add node
            nodes[current_id] = {
                "ID": current_id,
                "namespace": memory.namespace,
                "text": memory.text[:50] + "..." if len(memory.text) > 50 else memory.text,
                "importance": memory.importance
            }
            
            # If not at max depth, explore relationships
            if current_depth < depth:
                # Get outgoing relationships
                relationships = self.storage.get_relationships(source_id=current_id)
                for rel in relationships:
                    target_id = rel.target_id
                    
                    # Add edge
                    edges.append({
                        "source": current_id,
                        "target": target_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if target_id not in visited:
                        queue.append((target_id, current_depth + 1))
                
                # Get incoming relationships
                relationships = self.storage.get_relationships(target_id=current_id)
                for rel in relationships:
                    source_id = rel.source_id
                    
                    # Add edge
                    edges.append({
                        "source": source_id,
                        "target": current_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if source_id not in visited:
                        queue.append((source_id, current_depth + 1))
        
        return {
            "nodes": list(nodes.values()),
            "edges": edges
        }
    
    def xǁRelationshipManagerǁget_relationship_graph__mutmut_22(
        self,
        memory_ids: List[int],
        depth: int = 2
    ) -> Dict[str, Any]:
        """
        Get subgraph of relationships around given memories.
        
        Args:
            memory_ids: List of memory IDs to start from
            depth: Maximum depth of traversal (default: 2)
            
        Returns:
            Dictionary with "nodes" and "edges" representing the graph
        """
        nodes: Dict[int, Dict[str, Any]] = {}
        edges: List[Dict[str, Any]] = []
        visited: set = set()
        
        # BFS traversal
        queue: List[Tuple[int, int]] = [(mem_id, 0) for mem_id in memory_ids]  # (memory_id, current_depth)
        
        while queue:
            current_id, current_depth = queue.pop(0)
            
            if current_id in visited or current_depth > depth:
                continue
            
            visited.add(current_id)
            
            # Get memory
            memory = self.storage.get_memory(current_id)
            if not memory:
                continue
            
            # Add node
            nodes[current_id] = {
                "id": current_id,
                "XXnamespaceXX": memory.namespace,
                "text": memory.text[:50] + "..." if len(memory.text) > 50 else memory.text,
                "importance": memory.importance
            }
            
            # If not at max depth, explore relationships
            if current_depth < depth:
                # Get outgoing relationships
                relationships = self.storage.get_relationships(source_id=current_id)
                for rel in relationships:
                    target_id = rel.target_id
                    
                    # Add edge
                    edges.append({
                        "source": current_id,
                        "target": target_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if target_id not in visited:
                        queue.append((target_id, current_depth + 1))
                
                # Get incoming relationships
                relationships = self.storage.get_relationships(target_id=current_id)
                for rel in relationships:
                    source_id = rel.source_id
                    
                    # Add edge
                    edges.append({
                        "source": source_id,
                        "target": current_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if source_id not in visited:
                        queue.append((source_id, current_depth + 1))
        
        return {
            "nodes": list(nodes.values()),
            "edges": edges
        }
    
    def xǁRelationshipManagerǁget_relationship_graph__mutmut_23(
        self,
        memory_ids: List[int],
        depth: int = 2
    ) -> Dict[str, Any]:
        """
        Get subgraph of relationships around given memories.
        
        Args:
            memory_ids: List of memory IDs to start from
            depth: Maximum depth of traversal (default: 2)
            
        Returns:
            Dictionary with "nodes" and "edges" representing the graph
        """
        nodes: Dict[int, Dict[str, Any]] = {}
        edges: List[Dict[str, Any]] = []
        visited: set = set()
        
        # BFS traversal
        queue: List[Tuple[int, int]] = [(mem_id, 0) for mem_id in memory_ids]  # (memory_id, current_depth)
        
        while queue:
            current_id, current_depth = queue.pop(0)
            
            if current_id in visited or current_depth > depth:
                continue
            
            visited.add(current_id)
            
            # Get memory
            memory = self.storage.get_memory(current_id)
            if not memory:
                continue
            
            # Add node
            nodes[current_id] = {
                "id": current_id,
                "NAMESPACE": memory.namespace,
                "text": memory.text[:50] + "..." if len(memory.text) > 50 else memory.text,
                "importance": memory.importance
            }
            
            # If not at max depth, explore relationships
            if current_depth < depth:
                # Get outgoing relationships
                relationships = self.storage.get_relationships(source_id=current_id)
                for rel in relationships:
                    target_id = rel.target_id
                    
                    # Add edge
                    edges.append({
                        "source": current_id,
                        "target": target_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if target_id not in visited:
                        queue.append((target_id, current_depth + 1))
                
                # Get incoming relationships
                relationships = self.storage.get_relationships(target_id=current_id)
                for rel in relationships:
                    source_id = rel.source_id
                    
                    # Add edge
                    edges.append({
                        "source": source_id,
                        "target": current_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if source_id not in visited:
                        queue.append((source_id, current_depth + 1))
        
        return {
            "nodes": list(nodes.values()),
            "edges": edges
        }
    
    def xǁRelationshipManagerǁget_relationship_graph__mutmut_24(
        self,
        memory_ids: List[int],
        depth: int = 2
    ) -> Dict[str, Any]:
        """
        Get subgraph of relationships around given memories.
        
        Args:
            memory_ids: List of memory IDs to start from
            depth: Maximum depth of traversal (default: 2)
            
        Returns:
            Dictionary with "nodes" and "edges" representing the graph
        """
        nodes: Dict[int, Dict[str, Any]] = {}
        edges: List[Dict[str, Any]] = []
        visited: set = set()
        
        # BFS traversal
        queue: List[Tuple[int, int]] = [(mem_id, 0) for mem_id in memory_ids]  # (memory_id, current_depth)
        
        while queue:
            current_id, current_depth = queue.pop(0)
            
            if current_id in visited or current_depth > depth:
                continue
            
            visited.add(current_id)
            
            # Get memory
            memory = self.storage.get_memory(current_id)
            if not memory:
                continue
            
            # Add node
            nodes[current_id] = {
                "id": current_id,
                "namespace": memory.namespace,
                "XXtextXX": memory.text[:50] + "..." if len(memory.text) > 50 else memory.text,
                "importance": memory.importance
            }
            
            # If not at max depth, explore relationships
            if current_depth < depth:
                # Get outgoing relationships
                relationships = self.storage.get_relationships(source_id=current_id)
                for rel in relationships:
                    target_id = rel.target_id
                    
                    # Add edge
                    edges.append({
                        "source": current_id,
                        "target": target_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if target_id not in visited:
                        queue.append((target_id, current_depth + 1))
                
                # Get incoming relationships
                relationships = self.storage.get_relationships(target_id=current_id)
                for rel in relationships:
                    source_id = rel.source_id
                    
                    # Add edge
                    edges.append({
                        "source": source_id,
                        "target": current_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if source_id not in visited:
                        queue.append((source_id, current_depth + 1))
        
        return {
            "nodes": list(nodes.values()),
            "edges": edges
        }
    
    def xǁRelationshipManagerǁget_relationship_graph__mutmut_25(
        self,
        memory_ids: List[int],
        depth: int = 2
    ) -> Dict[str, Any]:
        """
        Get subgraph of relationships around given memories.
        
        Args:
            memory_ids: List of memory IDs to start from
            depth: Maximum depth of traversal (default: 2)
            
        Returns:
            Dictionary with "nodes" and "edges" representing the graph
        """
        nodes: Dict[int, Dict[str, Any]] = {}
        edges: List[Dict[str, Any]] = []
        visited: set = set()
        
        # BFS traversal
        queue: List[Tuple[int, int]] = [(mem_id, 0) for mem_id in memory_ids]  # (memory_id, current_depth)
        
        while queue:
            current_id, current_depth = queue.pop(0)
            
            if current_id in visited or current_depth > depth:
                continue
            
            visited.add(current_id)
            
            # Get memory
            memory = self.storage.get_memory(current_id)
            if not memory:
                continue
            
            # Add node
            nodes[current_id] = {
                "id": current_id,
                "namespace": memory.namespace,
                "TEXT": memory.text[:50] + "..." if len(memory.text) > 50 else memory.text,
                "importance": memory.importance
            }
            
            # If not at max depth, explore relationships
            if current_depth < depth:
                # Get outgoing relationships
                relationships = self.storage.get_relationships(source_id=current_id)
                for rel in relationships:
                    target_id = rel.target_id
                    
                    # Add edge
                    edges.append({
                        "source": current_id,
                        "target": target_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if target_id not in visited:
                        queue.append((target_id, current_depth + 1))
                
                # Get incoming relationships
                relationships = self.storage.get_relationships(target_id=current_id)
                for rel in relationships:
                    source_id = rel.source_id
                    
                    # Add edge
                    edges.append({
                        "source": source_id,
                        "target": current_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if source_id not in visited:
                        queue.append((source_id, current_depth + 1))
        
        return {
            "nodes": list(nodes.values()),
            "edges": edges
        }
    
    def xǁRelationshipManagerǁget_relationship_graph__mutmut_26(
        self,
        memory_ids: List[int],
        depth: int = 2
    ) -> Dict[str, Any]:
        """
        Get subgraph of relationships around given memories.
        
        Args:
            memory_ids: List of memory IDs to start from
            depth: Maximum depth of traversal (default: 2)
            
        Returns:
            Dictionary with "nodes" and "edges" representing the graph
        """
        nodes: Dict[int, Dict[str, Any]] = {}
        edges: List[Dict[str, Any]] = []
        visited: set = set()
        
        # BFS traversal
        queue: List[Tuple[int, int]] = [(mem_id, 0) for mem_id in memory_ids]  # (memory_id, current_depth)
        
        while queue:
            current_id, current_depth = queue.pop(0)
            
            if current_id in visited or current_depth > depth:
                continue
            
            visited.add(current_id)
            
            # Get memory
            memory = self.storage.get_memory(current_id)
            if not memory:
                continue
            
            # Add node
            nodes[current_id] = {
                "id": current_id,
                "namespace": memory.namespace,
                "text": memory.text[:50] - "..." if len(memory.text) > 50 else memory.text,
                "importance": memory.importance
            }
            
            # If not at max depth, explore relationships
            if current_depth < depth:
                # Get outgoing relationships
                relationships = self.storage.get_relationships(source_id=current_id)
                for rel in relationships:
                    target_id = rel.target_id
                    
                    # Add edge
                    edges.append({
                        "source": current_id,
                        "target": target_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if target_id not in visited:
                        queue.append((target_id, current_depth + 1))
                
                # Get incoming relationships
                relationships = self.storage.get_relationships(target_id=current_id)
                for rel in relationships:
                    source_id = rel.source_id
                    
                    # Add edge
                    edges.append({
                        "source": source_id,
                        "target": current_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if source_id not in visited:
                        queue.append((source_id, current_depth + 1))
        
        return {
            "nodes": list(nodes.values()),
            "edges": edges
        }
    
    def xǁRelationshipManagerǁget_relationship_graph__mutmut_27(
        self,
        memory_ids: List[int],
        depth: int = 2
    ) -> Dict[str, Any]:
        """
        Get subgraph of relationships around given memories.
        
        Args:
            memory_ids: List of memory IDs to start from
            depth: Maximum depth of traversal (default: 2)
            
        Returns:
            Dictionary with "nodes" and "edges" representing the graph
        """
        nodes: Dict[int, Dict[str, Any]] = {}
        edges: List[Dict[str, Any]] = []
        visited: set = set()
        
        # BFS traversal
        queue: List[Tuple[int, int]] = [(mem_id, 0) for mem_id in memory_ids]  # (memory_id, current_depth)
        
        while queue:
            current_id, current_depth = queue.pop(0)
            
            if current_id in visited or current_depth > depth:
                continue
            
            visited.add(current_id)
            
            # Get memory
            memory = self.storage.get_memory(current_id)
            if not memory:
                continue
            
            # Add node
            nodes[current_id] = {
                "id": current_id,
                "namespace": memory.namespace,
                "text": memory.text[:51] + "..." if len(memory.text) > 50 else memory.text,
                "importance": memory.importance
            }
            
            # If not at max depth, explore relationships
            if current_depth < depth:
                # Get outgoing relationships
                relationships = self.storage.get_relationships(source_id=current_id)
                for rel in relationships:
                    target_id = rel.target_id
                    
                    # Add edge
                    edges.append({
                        "source": current_id,
                        "target": target_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if target_id not in visited:
                        queue.append((target_id, current_depth + 1))
                
                # Get incoming relationships
                relationships = self.storage.get_relationships(target_id=current_id)
                for rel in relationships:
                    source_id = rel.source_id
                    
                    # Add edge
                    edges.append({
                        "source": source_id,
                        "target": current_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if source_id not in visited:
                        queue.append((source_id, current_depth + 1))
        
        return {
            "nodes": list(nodes.values()),
            "edges": edges
        }
    
    def xǁRelationshipManagerǁget_relationship_graph__mutmut_28(
        self,
        memory_ids: List[int],
        depth: int = 2
    ) -> Dict[str, Any]:
        """
        Get subgraph of relationships around given memories.
        
        Args:
            memory_ids: List of memory IDs to start from
            depth: Maximum depth of traversal (default: 2)
            
        Returns:
            Dictionary with "nodes" and "edges" representing the graph
        """
        nodes: Dict[int, Dict[str, Any]] = {}
        edges: List[Dict[str, Any]] = []
        visited: set = set()
        
        # BFS traversal
        queue: List[Tuple[int, int]] = [(mem_id, 0) for mem_id in memory_ids]  # (memory_id, current_depth)
        
        while queue:
            current_id, current_depth = queue.pop(0)
            
            if current_id in visited or current_depth > depth:
                continue
            
            visited.add(current_id)
            
            # Get memory
            memory = self.storage.get_memory(current_id)
            if not memory:
                continue
            
            # Add node
            nodes[current_id] = {
                "id": current_id,
                "namespace": memory.namespace,
                "text": memory.text[:50] + "XX...XX" if len(memory.text) > 50 else memory.text,
                "importance": memory.importance
            }
            
            # If not at max depth, explore relationships
            if current_depth < depth:
                # Get outgoing relationships
                relationships = self.storage.get_relationships(source_id=current_id)
                for rel in relationships:
                    target_id = rel.target_id
                    
                    # Add edge
                    edges.append({
                        "source": current_id,
                        "target": target_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if target_id not in visited:
                        queue.append((target_id, current_depth + 1))
                
                # Get incoming relationships
                relationships = self.storage.get_relationships(target_id=current_id)
                for rel in relationships:
                    source_id = rel.source_id
                    
                    # Add edge
                    edges.append({
                        "source": source_id,
                        "target": current_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if source_id not in visited:
                        queue.append((source_id, current_depth + 1))
        
        return {
            "nodes": list(nodes.values()),
            "edges": edges
        }
    
    def xǁRelationshipManagerǁget_relationship_graph__mutmut_29(
        self,
        memory_ids: List[int],
        depth: int = 2
    ) -> Dict[str, Any]:
        """
        Get subgraph of relationships around given memories.
        
        Args:
            memory_ids: List of memory IDs to start from
            depth: Maximum depth of traversal (default: 2)
            
        Returns:
            Dictionary with "nodes" and "edges" representing the graph
        """
        nodes: Dict[int, Dict[str, Any]] = {}
        edges: List[Dict[str, Any]] = []
        visited: set = set()
        
        # BFS traversal
        queue: List[Tuple[int, int]] = [(mem_id, 0) for mem_id in memory_ids]  # (memory_id, current_depth)
        
        while queue:
            current_id, current_depth = queue.pop(0)
            
            if current_id in visited or current_depth > depth:
                continue
            
            visited.add(current_id)
            
            # Get memory
            memory = self.storage.get_memory(current_id)
            if not memory:
                continue
            
            # Add node
            nodes[current_id] = {
                "id": current_id,
                "namespace": memory.namespace,
                "text": memory.text[:50] + "..." if len(memory.text) >= 50 else memory.text,
                "importance": memory.importance
            }
            
            # If not at max depth, explore relationships
            if current_depth < depth:
                # Get outgoing relationships
                relationships = self.storage.get_relationships(source_id=current_id)
                for rel in relationships:
                    target_id = rel.target_id
                    
                    # Add edge
                    edges.append({
                        "source": current_id,
                        "target": target_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if target_id not in visited:
                        queue.append((target_id, current_depth + 1))
                
                # Get incoming relationships
                relationships = self.storage.get_relationships(target_id=current_id)
                for rel in relationships:
                    source_id = rel.source_id
                    
                    # Add edge
                    edges.append({
                        "source": source_id,
                        "target": current_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if source_id not in visited:
                        queue.append((source_id, current_depth + 1))
        
        return {
            "nodes": list(nodes.values()),
            "edges": edges
        }
    
    def xǁRelationshipManagerǁget_relationship_graph__mutmut_30(
        self,
        memory_ids: List[int],
        depth: int = 2
    ) -> Dict[str, Any]:
        """
        Get subgraph of relationships around given memories.
        
        Args:
            memory_ids: List of memory IDs to start from
            depth: Maximum depth of traversal (default: 2)
            
        Returns:
            Dictionary with "nodes" and "edges" representing the graph
        """
        nodes: Dict[int, Dict[str, Any]] = {}
        edges: List[Dict[str, Any]] = []
        visited: set = set()
        
        # BFS traversal
        queue: List[Tuple[int, int]] = [(mem_id, 0) for mem_id in memory_ids]  # (memory_id, current_depth)
        
        while queue:
            current_id, current_depth = queue.pop(0)
            
            if current_id in visited or current_depth > depth:
                continue
            
            visited.add(current_id)
            
            # Get memory
            memory = self.storage.get_memory(current_id)
            if not memory:
                continue
            
            # Add node
            nodes[current_id] = {
                "id": current_id,
                "namespace": memory.namespace,
                "text": memory.text[:50] + "..." if len(memory.text) > 51 else memory.text,
                "importance": memory.importance
            }
            
            # If not at max depth, explore relationships
            if current_depth < depth:
                # Get outgoing relationships
                relationships = self.storage.get_relationships(source_id=current_id)
                for rel in relationships:
                    target_id = rel.target_id
                    
                    # Add edge
                    edges.append({
                        "source": current_id,
                        "target": target_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if target_id not in visited:
                        queue.append((target_id, current_depth + 1))
                
                # Get incoming relationships
                relationships = self.storage.get_relationships(target_id=current_id)
                for rel in relationships:
                    source_id = rel.source_id
                    
                    # Add edge
                    edges.append({
                        "source": source_id,
                        "target": current_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if source_id not in visited:
                        queue.append((source_id, current_depth + 1))
        
        return {
            "nodes": list(nodes.values()),
            "edges": edges
        }
    
    def xǁRelationshipManagerǁget_relationship_graph__mutmut_31(
        self,
        memory_ids: List[int],
        depth: int = 2
    ) -> Dict[str, Any]:
        """
        Get subgraph of relationships around given memories.
        
        Args:
            memory_ids: List of memory IDs to start from
            depth: Maximum depth of traversal (default: 2)
            
        Returns:
            Dictionary with "nodes" and "edges" representing the graph
        """
        nodes: Dict[int, Dict[str, Any]] = {}
        edges: List[Dict[str, Any]] = []
        visited: set = set()
        
        # BFS traversal
        queue: List[Tuple[int, int]] = [(mem_id, 0) for mem_id in memory_ids]  # (memory_id, current_depth)
        
        while queue:
            current_id, current_depth = queue.pop(0)
            
            if current_id in visited or current_depth > depth:
                continue
            
            visited.add(current_id)
            
            # Get memory
            memory = self.storage.get_memory(current_id)
            if not memory:
                continue
            
            # Add node
            nodes[current_id] = {
                "id": current_id,
                "namespace": memory.namespace,
                "text": memory.text[:50] + "..." if len(memory.text) > 50 else memory.text,
                "XXimportanceXX": memory.importance
            }
            
            # If not at max depth, explore relationships
            if current_depth < depth:
                # Get outgoing relationships
                relationships = self.storage.get_relationships(source_id=current_id)
                for rel in relationships:
                    target_id = rel.target_id
                    
                    # Add edge
                    edges.append({
                        "source": current_id,
                        "target": target_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if target_id not in visited:
                        queue.append((target_id, current_depth + 1))
                
                # Get incoming relationships
                relationships = self.storage.get_relationships(target_id=current_id)
                for rel in relationships:
                    source_id = rel.source_id
                    
                    # Add edge
                    edges.append({
                        "source": source_id,
                        "target": current_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if source_id not in visited:
                        queue.append((source_id, current_depth + 1))
        
        return {
            "nodes": list(nodes.values()),
            "edges": edges
        }
    
    def xǁRelationshipManagerǁget_relationship_graph__mutmut_32(
        self,
        memory_ids: List[int],
        depth: int = 2
    ) -> Dict[str, Any]:
        """
        Get subgraph of relationships around given memories.
        
        Args:
            memory_ids: List of memory IDs to start from
            depth: Maximum depth of traversal (default: 2)
            
        Returns:
            Dictionary with "nodes" and "edges" representing the graph
        """
        nodes: Dict[int, Dict[str, Any]] = {}
        edges: List[Dict[str, Any]] = []
        visited: set = set()
        
        # BFS traversal
        queue: List[Tuple[int, int]] = [(mem_id, 0) for mem_id in memory_ids]  # (memory_id, current_depth)
        
        while queue:
            current_id, current_depth = queue.pop(0)
            
            if current_id in visited or current_depth > depth:
                continue
            
            visited.add(current_id)
            
            # Get memory
            memory = self.storage.get_memory(current_id)
            if not memory:
                continue
            
            # Add node
            nodes[current_id] = {
                "id": current_id,
                "namespace": memory.namespace,
                "text": memory.text[:50] + "..." if len(memory.text) > 50 else memory.text,
                "IMPORTANCE": memory.importance
            }
            
            # If not at max depth, explore relationships
            if current_depth < depth:
                # Get outgoing relationships
                relationships = self.storage.get_relationships(source_id=current_id)
                for rel in relationships:
                    target_id = rel.target_id
                    
                    # Add edge
                    edges.append({
                        "source": current_id,
                        "target": target_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if target_id not in visited:
                        queue.append((target_id, current_depth + 1))
                
                # Get incoming relationships
                relationships = self.storage.get_relationships(target_id=current_id)
                for rel in relationships:
                    source_id = rel.source_id
                    
                    # Add edge
                    edges.append({
                        "source": source_id,
                        "target": current_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if source_id not in visited:
                        queue.append((source_id, current_depth + 1))
        
        return {
            "nodes": list(nodes.values()),
            "edges": edges
        }
    
    def xǁRelationshipManagerǁget_relationship_graph__mutmut_33(
        self,
        memory_ids: List[int],
        depth: int = 2
    ) -> Dict[str, Any]:
        """
        Get subgraph of relationships around given memories.
        
        Args:
            memory_ids: List of memory IDs to start from
            depth: Maximum depth of traversal (default: 2)
            
        Returns:
            Dictionary with "nodes" and "edges" representing the graph
        """
        nodes: Dict[int, Dict[str, Any]] = {}
        edges: List[Dict[str, Any]] = []
        visited: set = set()
        
        # BFS traversal
        queue: List[Tuple[int, int]] = [(mem_id, 0) for mem_id in memory_ids]  # (memory_id, current_depth)
        
        while queue:
            current_id, current_depth = queue.pop(0)
            
            if current_id in visited or current_depth > depth:
                continue
            
            visited.add(current_id)
            
            # Get memory
            memory = self.storage.get_memory(current_id)
            if not memory:
                continue
            
            # Add node
            nodes[current_id] = {
                "id": current_id,
                "namespace": memory.namespace,
                "text": memory.text[:50] + "..." if len(memory.text) > 50 else memory.text,
                "importance": memory.importance
            }
            
            # If not at max depth, explore relationships
            if current_depth <= depth:
                # Get outgoing relationships
                relationships = self.storage.get_relationships(source_id=current_id)
                for rel in relationships:
                    target_id = rel.target_id
                    
                    # Add edge
                    edges.append({
                        "source": current_id,
                        "target": target_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if target_id not in visited:
                        queue.append((target_id, current_depth + 1))
                
                # Get incoming relationships
                relationships = self.storage.get_relationships(target_id=current_id)
                for rel in relationships:
                    source_id = rel.source_id
                    
                    # Add edge
                    edges.append({
                        "source": source_id,
                        "target": current_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if source_id not in visited:
                        queue.append((source_id, current_depth + 1))
        
        return {
            "nodes": list(nodes.values()),
            "edges": edges
        }
    
    def xǁRelationshipManagerǁget_relationship_graph__mutmut_34(
        self,
        memory_ids: List[int],
        depth: int = 2
    ) -> Dict[str, Any]:
        """
        Get subgraph of relationships around given memories.
        
        Args:
            memory_ids: List of memory IDs to start from
            depth: Maximum depth of traversal (default: 2)
            
        Returns:
            Dictionary with "nodes" and "edges" representing the graph
        """
        nodes: Dict[int, Dict[str, Any]] = {}
        edges: List[Dict[str, Any]] = []
        visited: set = set()
        
        # BFS traversal
        queue: List[Tuple[int, int]] = [(mem_id, 0) for mem_id in memory_ids]  # (memory_id, current_depth)
        
        while queue:
            current_id, current_depth = queue.pop(0)
            
            if current_id in visited or current_depth > depth:
                continue
            
            visited.add(current_id)
            
            # Get memory
            memory = self.storage.get_memory(current_id)
            if not memory:
                continue
            
            # Add node
            nodes[current_id] = {
                "id": current_id,
                "namespace": memory.namespace,
                "text": memory.text[:50] + "..." if len(memory.text) > 50 else memory.text,
                "importance": memory.importance
            }
            
            # If not at max depth, explore relationships
            if current_depth < depth:
                # Get outgoing relationships
                relationships = None
                for rel in relationships:
                    target_id = rel.target_id
                    
                    # Add edge
                    edges.append({
                        "source": current_id,
                        "target": target_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if target_id not in visited:
                        queue.append((target_id, current_depth + 1))
                
                # Get incoming relationships
                relationships = self.storage.get_relationships(target_id=current_id)
                for rel in relationships:
                    source_id = rel.source_id
                    
                    # Add edge
                    edges.append({
                        "source": source_id,
                        "target": current_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if source_id not in visited:
                        queue.append((source_id, current_depth + 1))
        
        return {
            "nodes": list(nodes.values()),
            "edges": edges
        }
    
    def xǁRelationshipManagerǁget_relationship_graph__mutmut_35(
        self,
        memory_ids: List[int],
        depth: int = 2
    ) -> Dict[str, Any]:
        """
        Get subgraph of relationships around given memories.
        
        Args:
            memory_ids: List of memory IDs to start from
            depth: Maximum depth of traversal (default: 2)
            
        Returns:
            Dictionary with "nodes" and "edges" representing the graph
        """
        nodes: Dict[int, Dict[str, Any]] = {}
        edges: List[Dict[str, Any]] = []
        visited: set = set()
        
        # BFS traversal
        queue: List[Tuple[int, int]] = [(mem_id, 0) for mem_id in memory_ids]  # (memory_id, current_depth)
        
        while queue:
            current_id, current_depth = queue.pop(0)
            
            if current_id in visited or current_depth > depth:
                continue
            
            visited.add(current_id)
            
            # Get memory
            memory = self.storage.get_memory(current_id)
            if not memory:
                continue
            
            # Add node
            nodes[current_id] = {
                "id": current_id,
                "namespace": memory.namespace,
                "text": memory.text[:50] + "..." if len(memory.text) > 50 else memory.text,
                "importance": memory.importance
            }
            
            # If not at max depth, explore relationships
            if current_depth < depth:
                # Get outgoing relationships
                relationships = self.storage.get_relationships(source_id=None)
                for rel in relationships:
                    target_id = rel.target_id
                    
                    # Add edge
                    edges.append({
                        "source": current_id,
                        "target": target_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if target_id not in visited:
                        queue.append((target_id, current_depth + 1))
                
                # Get incoming relationships
                relationships = self.storage.get_relationships(target_id=current_id)
                for rel in relationships:
                    source_id = rel.source_id
                    
                    # Add edge
                    edges.append({
                        "source": source_id,
                        "target": current_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if source_id not in visited:
                        queue.append((source_id, current_depth + 1))
        
        return {
            "nodes": list(nodes.values()),
            "edges": edges
        }
    
    def xǁRelationshipManagerǁget_relationship_graph__mutmut_36(
        self,
        memory_ids: List[int],
        depth: int = 2
    ) -> Dict[str, Any]:
        """
        Get subgraph of relationships around given memories.
        
        Args:
            memory_ids: List of memory IDs to start from
            depth: Maximum depth of traversal (default: 2)
            
        Returns:
            Dictionary with "nodes" and "edges" representing the graph
        """
        nodes: Dict[int, Dict[str, Any]] = {}
        edges: List[Dict[str, Any]] = []
        visited: set = set()
        
        # BFS traversal
        queue: List[Tuple[int, int]] = [(mem_id, 0) for mem_id in memory_ids]  # (memory_id, current_depth)
        
        while queue:
            current_id, current_depth = queue.pop(0)
            
            if current_id in visited or current_depth > depth:
                continue
            
            visited.add(current_id)
            
            # Get memory
            memory = self.storage.get_memory(current_id)
            if not memory:
                continue
            
            # Add node
            nodes[current_id] = {
                "id": current_id,
                "namespace": memory.namespace,
                "text": memory.text[:50] + "..." if len(memory.text) > 50 else memory.text,
                "importance": memory.importance
            }
            
            # If not at max depth, explore relationships
            if current_depth < depth:
                # Get outgoing relationships
                relationships = self.storage.get_relationships(source_id=current_id)
                for rel in relationships:
                    target_id = None
                    
                    # Add edge
                    edges.append({
                        "source": current_id,
                        "target": target_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if target_id not in visited:
                        queue.append((target_id, current_depth + 1))
                
                # Get incoming relationships
                relationships = self.storage.get_relationships(target_id=current_id)
                for rel in relationships:
                    source_id = rel.source_id
                    
                    # Add edge
                    edges.append({
                        "source": source_id,
                        "target": current_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if source_id not in visited:
                        queue.append((source_id, current_depth + 1))
        
        return {
            "nodes": list(nodes.values()),
            "edges": edges
        }
    
    def xǁRelationshipManagerǁget_relationship_graph__mutmut_37(
        self,
        memory_ids: List[int],
        depth: int = 2
    ) -> Dict[str, Any]:
        """
        Get subgraph of relationships around given memories.
        
        Args:
            memory_ids: List of memory IDs to start from
            depth: Maximum depth of traversal (default: 2)
            
        Returns:
            Dictionary with "nodes" and "edges" representing the graph
        """
        nodes: Dict[int, Dict[str, Any]] = {}
        edges: List[Dict[str, Any]] = []
        visited: set = set()
        
        # BFS traversal
        queue: List[Tuple[int, int]] = [(mem_id, 0) for mem_id in memory_ids]  # (memory_id, current_depth)
        
        while queue:
            current_id, current_depth = queue.pop(0)
            
            if current_id in visited or current_depth > depth:
                continue
            
            visited.add(current_id)
            
            # Get memory
            memory = self.storage.get_memory(current_id)
            if not memory:
                continue
            
            # Add node
            nodes[current_id] = {
                "id": current_id,
                "namespace": memory.namespace,
                "text": memory.text[:50] + "..." if len(memory.text) > 50 else memory.text,
                "importance": memory.importance
            }
            
            # If not at max depth, explore relationships
            if current_depth < depth:
                # Get outgoing relationships
                relationships = self.storage.get_relationships(source_id=current_id)
                for rel in relationships:
                    target_id = rel.target_id
                    
                    # Add edge
                    edges.append(None)
                    
                    # Add to queue if not visited
                    if target_id not in visited:
                        queue.append((target_id, current_depth + 1))
                
                # Get incoming relationships
                relationships = self.storage.get_relationships(target_id=current_id)
                for rel in relationships:
                    source_id = rel.source_id
                    
                    # Add edge
                    edges.append({
                        "source": source_id,
                        "target": current_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if source_id not in visited:
                        queue.append((source_id, current_depth + 1))
        
        return {
            "nodes": list(nodes.values()),
            "edges": edges
        }
    
    def xǁRelationshipManagerǁget_relationship_graph__mutmut_38(
        self,
        memory_ids: List[int],
        depth: int = 2
    ) -> Dict[str, Any]:
        """
        Get subgraph of relationships around given memories.
        
        Args:
            memory_ids: List of memory IDs to start from
            depth: Maximum depth of traversal (default: 2)
            
        Returns:
            Dictionary with "nodes" and "edges" representing the graph
        """
        nodes: Dict[int, Dict[str, Any]] = {}
        edges: List[Dict[str, Any]] = []
        visited: set = set()
        
        # BFS traversal
        queue: List[Tuple[int, int]] = [(mem_id, 0) for mem_id in memory_ids]  # (memory_id, current_depth)
        
        while queue:
            current_id, current_depth = queue.pop(0)
            
            if current_id in visited or current_depth > depth:
                continue
            
            visited.add(current_id)
            
            # Get memory
            memory = self.storage.get_memory(current_id)
            if not memory:
                continue
            
            # Add node
            nodes[current_id] = {
                "id": current_id,
                "namespace": memory.namespace,
                "text": memory.text[:50] + "..." if len(memory.text) > 50 else memory.text,
                "importance": memory.importance
            }
            
            # If not at max depth, explore relationships
            if current_depth < depth:
                # Get outgoing relationships
                relationships = self.storage.get_relationships(source_id=current_id)
                for rel in relationships:
                    target_id = rel.target_id
                    
                    # Add edge
                    edges.append({
                        "XXsourceXX": current_id,
                        "target": target_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if target_id not in visited:
                        queue.append((target_id, current_depth + 1))
                
                # Get incoming relationships
                relationships = self.storage.get_relationships(target_id=current_id)
                for rel in relationships:
                    source_id = rel.source_id
                    
                    # Add edge
                    edges.append({
                        "source": source_id,
                        "target": current_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if source_id not in visited:
                        queue.append((source_id, current_depth + 1))
        
        return {
            "nodes": list(nodes.values()),
            "edges": edges
        }
    
    def xǁRelationshipManagerǁget_relationship_graph__mutmut_39(
        self,
        memory_ids: List[int],
        depth: int = 2
    ) -> Dict[str, Any]:
        """
        Get subgraph of relationships around given memories.
        
        Args:
            memory_ids: List of memory IDs to start from
            depth: Maximum depth of traversal (default: 2)
            
        Returns:
            Dictionary with "nodes" and "edges" representing the graph
        """
        nodes: Dict[int, Dict[str, Any]] = {}
        edges: List[Dict[str, Any]] = []
        visited: set = set()
        
        # BFS traversal
        queue: List[Tuple[int, int]] = [(mem_id, 0) for mem_id in memory_ids]  # (memory_id, current_depth)
        
        while queue:
            current_id, current_depth = queue.pop(0)
            
            if current_id in visited or current_depth > depth:
                continue
            
            visited.add(current_id)
            
            # Get memory
            memory = self.storage.get_memory(current_id)
            if not memory:
                continue
            
            # Add node
            nodes[current_id] = {
                "id": current_id,
                "namespace": memory.namespace,
                "text": memory.text[:50] + "..." if len(memory.text) > 50 else memory.text,
                "importance": memory.importance
            }
            
            # If not at max depth, explore relationships
            if current_depth < depth:
                # Get outgoing relationships
                relationships = self.storage.get_relationships(source_id=current_id)
                for rel in relationships:
                    target_id = rel.target_id
                    
                    # Add edge
                    edges.append({
                        "SOURCE": current_id,
                        "target": target_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if target_id not in visited:
                        queue.append((target_id, current_depth + 1))
                
                # Get incoming relationships
                relationships = self.storage.get_relationships(target_id=current_id)
                for rel in relationships:
                    source_id = rel.source_id
                    
                    # Add edge
                    edges.append({
                        "source": source_id,
                        "target": current_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if source_id not in visited:
                        queue.append((source_id, current_depth + 1))
        
        return {
            "nodes": list(nodes.values()),
            "edges": edges
        }
    
    def xǁRelationshipManagerǁget_relationship_graph__mutmut_40(
        self,
        memory_ids: List[int],
        depth: int = 2
    ) -> Dict[str, Any]:
        """
        Get subgraph of relationships around given memories.
        
        Args:
            memory_ids: List of memory IDs to start from
            depth: Maximum depth of traversal (default: 2)
            
        Returns:
            Dictionary with "nodes" and "edges" representing the graph
        """
        nodes: Dict[int, Dict[str, Any]] = {}
        edges: List[Dict[str, Any]] = []
        visited: set = set()
        
        # BFS traversal
        queue: List[Tuple[int, int]] = [(mem_id, 0) for mem_id in memory_ids]  # (memory_id, current_depth)
        
        while queue:
            current_id, current_depth = queue.pop(0)
            
            if current_id in visited or current_depth > depth:
                continue
            
            visited.add(current_id)
            
            # Get memory
            memory = self.storage.get_memory(current_id)
            if not memory:
                continue
            
            # Add node
            nodes[current_id] = {
                "id": current_id,
                "namespace": memory.namespace,
                "text": memory.text[:50] + "..." if len(memory.text) > 50 else memory.text,
                "importance": memory.importance
            }
            
            # If not at max depth, explore relationships
            if current_depth < depth:
                # Get outgoing relationships
                relationships = self.storage.get_relationships(source_id=current_id)
                for rel in relationships:
                    target_id = rel.target_id
                    
                    # Add edge
                    edges.append({
                        "source": current_id,
                        "XXtargetXX": target_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if target_id not in visited:
                        queue.append((target_id, current_depth + 1))
                
                # Get incoming relationships
                relationships = self.storage.get_relationships(target_id=current_id)
                for rel in relationships:
                    source_id = rel.source_id
                    
                    # Add edge
                    edges.append({
                        "source": source_id,
                        "target": current_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if source_id not in visited:
                        queue.append((source_id, current_depth + 1))
        
        return {
            "nodes": list(nodes.values()),
            "edges": edges
        }
    
    def xǁRelationshipManagerǁget_relationship_graph__mutmut_41(
        self,
        memory_ids: List[int],
        depth: int = 2
    ) -> Dict[str, Any]:
        """
        Get subgraph of relationships around given memories.
        
        Args:
            memory_ids: List of memory IDs to start from
            depth: Maximum depth of traversal (default: 2)
            
        Returns:
            Dictionary with "nodes" and "edges" representing the graph
        """
        nodes: Dict[int, Dict[str, Any]] = {}
        edges: List[Dict[str, Any]] = []
        visited: set = set()
        
        # BFS traversal
        queue: List[Tuple[int, int]] = [(mem_id, 0) for mem_id in memory_ids]  # (memory_id, current_depth)
        
        while queue:
            current_id, current_depth = queue.pop(0)
            
            if current_id in visited or current_depth > depth:
                continue
            
            visited.add(current_id)
            
            # Get memory
            memory = self.storage.get_memory(current_id)
            if not memory:
                continue
            
            # Add node
            nodes[current_id] = {
                "id": current_id,
                "namespace": memory.namespace,
                "text": memory.text[:50] + "..." if len(memory.text) > 50 else memory.text,
                "importance": memory.importance
            }
            
            # If not at max depth, explore relationships
            if current_depth < depth:
                # Get outgoing relationships
                relationships = self.storage.get_relationships(source_id=current_id)
                for rel in relationships:
                    target_id = rel.target_id
                    
                    # Add edge
                    edges.append({
                        "source": current_id,
                        "TARGET": target_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if target_id not in visited:
                        queue.append((target_id, current_depth + 1))
                
                # Get incoming relationships
                relationships = self.storage.get_relationships(target_id=current_id)
                for rel in relationships:
                    source_id = rel.source_id
                    
                    # Add edge
                    edges.append({
                        "source": source_id,
                        "target": current_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if source_id not in visited:
                        queue.append((source_id, current_depth + 1))
        
        return {
            "nodes": list(nodes.values()),
            "edges": edges
        }
    
    def xǁRelationshipManagerǁget_relationship_graph__mutmut_42(
        self,
        memory_ids: List[int],
        depth: int = 2
    ) -> Dict[str, Any]:
        """
        Get subgraph of relationships around given memories.
        
        Args:
            memory_ids: List of memory IDs to start from
            depth: Maximum depth of traversal (default: 2)
            
        Returns:
            Dictionary with "nodes" and "edges" representing the graph
        """
        nodes: Dict[int, Dict[str, Any]] = {}
        edges: List[Dict[str, Any]] = []
        visited: set = set()
        
        # BFS traversal
        queue: List[Tuple[int, int]] = [(mem_id, 0) for mem_id in memory_ids]  # (memory_id, current_depth)
        
        while queue:
            current_id, current_depth = queue.pop(0)
            
            if current_id in visited or current_depth > depth:
                continue
            
            visited.add(current_id)
            
            # Get memory
            memory = self.storage.get_memory(current_id)
            if not memory:
                continue
            
            # Add node
            nodes[current_id] = {
                "id": current_id,
                "namespace": memory.namespace,
                "text": memory.text[:50] + "..." if len(memory.text) > 50 else memory.text,
                "importance": memory.importance
            }
            
            # If not at max depth, explore relationships
            if current_depth < depth:
                # Get outgoing relationships
                relationships = self.storage.get_relationships(source_id=current_id)
                for rel in relationships:
                    target_id = rel.target_id
                    
                    # Add edge
                    edges.append({
                        "source": current_id,
                        "target": target_id,
                        "XXtypeXX": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if target_id not in visited:
                        queue.append((target_id, current_depth + 1))
                
                # Get incoming relationships
                relationships = self.storage.get_relationships(target_id=current_id)
                for rel in relationships:
                    source_id = rel.source_id
                    
                    # Add edge
                    edges.append({
                        "source": source_id,
                        "target": current_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if source_id not in visited:
                        queue.append((source_id, current_depth + 1))
        
        return {
            "nodes": list(nodes.values()),
            "edges": edges
        }
    
    def xǁRelationshipManagerǁget_relationship_graph__mutmut_43(
        self,
        memory_ids: List[int],
        depth: int = 2
    ) -> Dict[str, Any]:
        """
        Get subgraph of relationships around given memories.
        
        Args:
            memory_ids: List of memory IDs to start from
            depth: Maximum depth of traversal (default: 2)
            
        Returns:
            Dictionary with "nodes" and "edges" representing the graph
        """
        nodes: Dict[int, Dict[str, Any]] = {}
        edges: List[Dict[str, Any]] = []
        visited: set = set()
        
        # BFS traversal
        queue: List[Tuple[int, int]] = [(mem_id, 0) for mem_id in memory_ids]  # (memory_id, current_depth)
        
        while queue:
            current_id, current_depth = queue.pop(0)
            
            if current_id in visited or current_depth > depth:
                continue
            
            visited.add(current_id)
            
            # Get memory
            memory = self.storage.get_memory(current_id)
            if not memory:
                continue
            
            # Add node
            nodes[current_id] = {
                "id": current_id,
                "namespace": memory.namespace,
                "text": memory.text[:50] + "..." if len(memory.text) > 50 else memory.text,
                "importance": memory.importance
            }
            
            # If not at max depth, explore relationships
            if current_depth < depth:
                # Get outgoing relationships
                relationships = self.storage.get_relationships(source_id=current_id)
                for rel in relationships:
                    target_id = rel.target_id
                    
                    # Add edge
                    edges.append({
                        "source": current_id,
                        "target": target_id,
                        "TYPE": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if target_id not in visited:
                        queue.append((target_id, current_depth + 1))
                
                # Get incoming relationships
                relationships = self.storage.get_relationships(target_id=current_id)
                for rel in relationships:
                    source_id = rel.source_id
                    
                    # Add edge
                    edges.append({
                        "source": source_id,
                        "target": current_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if source_id not in visited:
                        queue.append((source_id, current_depth + 1))
        
        return {
            "nodes": list(nodes.values()),
            "edges": edges
        }
    
    def xǁRelationshipManagerǁget_relationship_graph__mutmut_44(
        self,
        memory_ids: List[int],
        depth: int = 2
    ) -> Dict[str, Any]:
        """
        Get subgraph of relationships around given memories.
        
        Args:
            memory_ids: List of memory IDs to start from
            depth: Maximum depth of traversal (default: 2)
            
        Returns:
            Dictionary with "nodes" and "edges" representing the graph
        """
        nodes: Dict[int, Dict[str, Any]] = {}
        edges: List[Dict[str, Any]] = []
        visited: set = set()
        
        # BFS traversal
        queue: List[Tuple[int, int]] = [(mem_id, 0) for mem_id in memory_ids]  # (memory_id, current_depth)
        
        while queue:
            current_id, current_depth = queue.pop(0)
            
            if current_id in visited or current_depth > depth:
                continue
            
            visited.add(current_id)
            
            # Get memory
            memory = self.storage.get_memory(current_id)
            if not memory:
                continue
            
            # Add node
            nodes[current_id] = {
                "id": current_id,
                "namespace": memory.namespace,
                "text": memory.text[:50] + "..." if len(memory.text) > 50 else memory.text,
                "importance": memory.importance
            }
            
            # If not at max depth, explore relationships
            if current_depth < depth:
                # Get outgoing relationships
                relationships = self.storage.get_relationships(source_id=current_id)
                for rel in relationships:
                    target_id = rel.target_id
                    
                    # Add edge
                    edges.append({
                        "source": current_id,
                        "target": target_id,
                        "type": rel.relation_type.value,
                        "XXstrengthXX": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if target_id not in visited:
                        queue.append((target_id, current_depth + 1))
                
                # Get incoming relationships
                relationships = self.storage.get_relationships(target_id=current_id)
                for rel in relationships:
                    source_id = rel.source_id
                    
                    # Add edge
                    edges.append({
                        "source": source_id,
                        "target": current_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if source_id not in visited:
                        queue.append((source_id, current_depth + 1))
        
        return {
            "nodes": list(nodes.values()),
            "edges": edges
        }
    
    def xǁRelationshipManagerǁget_relationship_graph__mutmut_45(
        self,
        memory_ids: List[int],
        depth: int = 2
    ) -> Dict[str, Any]:
        """
        Get subgraph of relationships around given memories.
        
        Args:
            memory_ids: List of memory IDs to start from
            depth: Maximum depth of traversal (default: 2)
            
        Returns:
            Dictionary with "nodes" and "edges" representing the graph
        """
        nodes: Dict[int, Dict[str, Any]] = {}
        edges: List[Dict[str, Any]] = []
        visited: set = set()
        
        # BFS traversal
        queue: List[Tuple[int, int]] = [(mem_id, 0) for mem_id in memory_ids]  # (memory_id, current_depth)
        
        while queue:
            current_id, current_depth = queue.pop(0)
            
            if current_id in visited or current_depth > depth:
                continue
            
            visited.add(current_id)
            
            # Get memory
            memory = self.storage.get_memory(current_id)
            if not memory:
                continue
            
            # Add node
            nodes[current_id] = {
                "id": current_id,
                "namespace": memory.namespace,
                "text": memory.text[:50] + "..." if len(memory.text) > 50 else memory.text,
                "importance": memory.importance
            }
            
            # If not at max depth, explore relationships
            if current_depth < depth:
                # Get outgoing relationships
                relationships = self.storage.get_relationships(source_id=current_id)
                for rel in relationships:
                    target_id = rel.target_id
                    
                    # Add edge
                    edges.append({
                        "source": current_id,
                        "target": target_id,
                        "type": rel.relation_type.value,
                        "STRENGTH": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if target_id not in visited:
                        queue.append((target_id, current_depth + 1))
                
                # Get incoming relationships
                relationships = self.storage.get_relationships(target_id=current_id)
                for rel in relationships:
                    source_id = rel.source_id
                    
                    # Add edge
                    edges.append({
                        "source": source_id,
                        "target": current_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if source_id not in visited:
                        queue.append((source_id, current_depth + 1))
        
        return {
            "nodes": list(nodes.values()),
            "edges": edges
        }
    
    def xǁRelationshipManagerǁget_relationship_graph__mutmut_46(
        self,
        memory_ids: List[int],
        depth: int = 2
    ) -> Dict[str, Any]:
        """
        Get subgraph of relationships around given memories.
        
        Args:
            memory_ids: List of memory IDs to start from
            depth: Maximum depth of traversal (default: 2)
            
        Returns:
            Dictionary with "nodes" and "edges" representing the graph
        """
        nodes: Dict[int, Dict[str, Any]] = {}
        edges: List[Dict[str, Any]] = []
        visited: set = set()
        
        # BFS traversal
        queue: List[Tuple[int, int]] = [(mem_id, 0) for mem_id in memory_ids]  # (memory_id, current_depth)
        
        while queue:
            current_id, current_depth = queue.pop(0)
            
            if current_id in visited or current_depth > depth:
                continue
            
            visited.add(current_id)
            
            # Get memory
            memory = self.storage.get_memory(current_id)
            if not memory:
                continue
            
            # Add node
            nodes[current_id] = {
                "id": current_id,
                "namespace": memory.namespace,
                "text": memory.text[:50] + "..." if len(memory.text) > 50 else memory.text,
                "importance": memory.importance
            }
            
            # If not at max depth, explore relationships
            if current_depth < depth:
                # Get outgoing relationships
                relationships = self.storage.get_relationships(source_id=current_id)
                for rel in relationships:
                    target_id = rel.target_id
                    
                    # Add edge
                    edges.append({
                        "source": current_id,
                        "target": target_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if target_id in visited:
                        queue.append((target_id, current_depth + 1))
                
                # Get incoming relationships
                relationships = self.storage.get_relationships(target_id=current_id)
                for rel in relationships:
                    source_id = rel.source_id
                    
                    # Add edge
                    edges.append({
                        "source": source_id,
                        "target": current_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if source_id not in visited:
                        queue.append((source_id, current_depth + 1))
        
        return {
            "nodes": list(nodes.values()),
            "edges": edges
        }
    
    def xǁRelationshipManagerǁget_relationship_graph__mutmut_47(
        self,
        memory_ids: List[int],
        depth: int = 2
    ) -> Dict[str, Any]:
        """
        Get subgraph of relationships around given memories.
        
        Args:
            memory_ids: List of memory IDs to start from
            depth: Maximum depth of traversal (default: 2)
            
        Returns:
            Dictionary with "nodes" and "edges" representing the graph
        """
        nodes: Dict[int, Dict[str, Any]] = {}
        edges: List[Dict[str, Any]] = []
        visited: set = set()
        
        # BFS traversal
        queue: List[Tuple[int, int]] = [(mem_id, 0) for mem_id in memory_ids]  # (memory_id, current_depth)
        
        while queue:
            current_id, current_depth = queue.pop(0)
            
            if current_id in visited or current_depth > depth:
                continue
            
            visited.add(current_id)
            
            # Get memory
            memory = self.storage.get_memory(current_id)
            if not memory:
                continue
            
            # Add node
            nodes[current_id] = {
                "id": current_id,
                "namespace": memory.namespace,
                "text": memory.text[:50] + "..." if len(memory.text) > 50 else memory.text,
                "importance": memory.importance
            }
            
            # If not at max depth, explore relationships
            if current_depth < depth:
                # Get outgoing relationships
                relationships = self.storage.get_relationships(source_id=current_id)
                for rel in relationships:
                    target_id = rel.target_id
                    
                    # Add edge
                    edges.append({
                        "source": current_id,
                        "target": target_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if target_id not in visited:
                        queue.append(None)
                
                # Get incoming relationships
                relationships = self.storage.get_relationships(target_id=current_id)
                for rel in relationships:
                    source_id = rel.source_id
                    
                    # Add edge
                    edges.append({
                        "source": source_id,
                        "target": current_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if source_id not in visited:
                        queue.append((source_id, current_depth + 1))
        
        return {
            "nodes": list(nodes.values()),
            "edges": edges
        }
    
    def xǁRelationshipManagerǁget_relationship_graph__mutmut_48(
        self,
        memory_ids: List[int],
        depth: int = 2
    ) -> Dict[str, Any]:
        """
        Get subgraph of relationships around given memories.
        
        Args:
            memory_ids: List of memory IDs to start from
            depth: Maximum depth of traversal (default: 2)
            
        Returns:
            Dictionary with "nodes" and "edges" representing the graph
        """
        nodes: Dict[int, Dict[str, Any]] = {}
        edges: List[Dict[str, Any]] = []
        visited: set = set()
        
        # BFS traversal
        queue: List[Tuple[int, int]] = [(mem_id, 0) for mem_id in memory_ids]  # (memory_id, current_depth)
        
        while queue:
            current_id, current_depth = queue.pop(0)
            
            if current_id in visited or current_depth > depth:
                continue
            
            visited.add(current_id)
            
            # Get memory
            memory = self.storage.get_memory(current_id)
            if not memory:
                continue
            
            # Add node
            nodes[current_id] = {
                "id": current_id,
                "namespace": memory.namespace,
                "text": memory.text[:50] + "..." if len(memory.text) > 50 else memory.text,
                "importance": memory.importance
            }
            
            # If not at max depth, explore relationships
            if current_depth < depth:
                # Get outgoing relationships
                relationships = self.storage.get_relationships(source_id=current_id)
                for rel in relationships:
                    target_id = rel.target_id
                    
                    # Add edge
                    edges.append({
                        "source": current_id,
                        "target": target_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if target_id not in visited:
                        queue.append((target_id, current_depth - 1))
                
                # Get incoming relationships
                relationships = self.storage.get_relationships(target_id=current_id)
                for rel in relationships:
                    source_id = rel.source_id
                    
                    # Add edge
                    edges.append({
                        "source": source_id,
                        "target": current_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if source_id not in visited:
                        queue.append((source_id, current_depth + 1))
        
        return {
            "nodes": list(nodes.values()),
            "edges": edges
        }
    
    def xǁRelationshipManagerǁget_relationship_graph__mutmut_49(
        self,
        memory_ids: List[int],
        depth: int = 2
    ) -> Dict[str, Any]:
        """
        Get subgraph of relationships around given memories.
        
        Args:
            memory_ids: List of memory IDs to start from
            depth: Maximum depth of traversal (default: 2)
            
        Returns:
            Dictionary with "nodes" and "edges" representing the graph
        """
        nodes: Dict[int, Dict[str, Any]] = {}
        edges: List[Dict[str, Any]] = []
        visited: set = set()
        
        # BFS traversal
        queue: List[Tuple[int, int]] = [(mem_id, 0) for mem_id in memory_ids]  # (memory_id, current_depth)
        
        while queue:
            current_id, current_depth = queue.pop(0)
            
            if current_id in visited or current_depth > depth:
                continue
            
            visited.add(current_id)
            
            # Get memory
            memory = self.storage.get_memory(current_id)
            if not memory:
                continue
            
            # Add node
            nodes[current_id] = {
                "id": current_id,
                "namespace": memory.namespace,
                "text": memory.text[:50] + "..." if len(memory.text) > 50 else memory.text,
                "importance": memory.importance
            }
            
            # If not at max depth, explore relationships
            if current_depth < depth:
                # Get outgoing relationships
                relationships = self.storage.get_relationships(source_id=current_id)
                for rel in relationships:
                    target_id = rel.target_id
                    
                    # Add edge
                    edges.append({
                        "source": current_id,
                        "target": target_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if target_id not in visited:
                        queue.append((target_id, current_depth + 2))
                
                # Get incoming relationships
                relationships = self.storage.get_relationships(target_id=current_id)
                for rel in relationships:
                    source_id = rel.source_id
                    
                    # Add edge
                    edges.append({
                        "source": source_id,
                        "target": current_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if source_id not in visited:
                        queue.append((source_id, current_depth + 1))
        
        return {
            "nodes": list(nodes.values()),
            "edges": edges
        }
    
    def xǁRelationshipManagerǁget_relationship_graph__mutmut_50(
        self,
        memory_ids: List[int],
        depth: int = 2
    ) -> Dict[str, Any]:
        """
        Get subgraph of relationships around given memories.
        
        Args:
            memory_ids: List of memory IDs to start from
            depth: Maximum depth of traversal (default: 2)
            
        Returns:
            Dictionary with "nodes" and "edges" representing the graph
        """
        nodes: Dict[int, Dict[str, Any]] = {}
        edges: List[Dict[str, Any]] = []
        visited: set = set()
        
        # BFS traversal
        queue: List[Tuple[int, int]] = [(mem_id, 0) for mem_id in memory_ids]  # (memory_id, current_depth)
        
        while queue:
            current_id, current_depth = queue.pop(0)
            
            if current_id in visited or current_depth > depth:
                continue
            
            visited.add(current_id)
            
            # Get memory
            memory = self.storage.get_memory(current_id)
            if not memory:
                continue
            
            # Add node
            nodes[current_id] = {
                "id": current_id,
                "namespace": memory.namespace,
                "text": memory.text[:50] + "..." if len(memory.text) > 50 else memory.text,
                "importance": memory.importance
            }
            
            # If not at max depth, explore relationships
            if current_depth < depth:
                # Get outgoing relationships
                relationships = self.storage.get_relationships(source_id=current_id)
                for rel in relationships:
                    target_id = rel.target_id
                    
                    # Add edge
                    edges.append({
                        "source": current_id,
                        "target": target_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if target_id not in visited:
                        queue.append((target_id, current_depth + 1))
                
                # Get incoming relationships
                relationships = None
                for rel in relationships:
                    source_id = rel.source_id
                    
                    # Add edge
                    edges.append({
                        "source": source_id,
                        "target": current_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if source_id not in visited:
                        queue.append((source_id, current_depth + 1))
        
        return {
            "nodes": list(nodes.values()),
            "edges": edges
        }
    
    def xǁRelationshipManagerǁget_relationship_graph__mutmut_51(
        self,
        memory_ids: List[int],
        depth: int = 2
    ) -> Dict[str, Any]:
        """
        Get subgraph of relationships around given memories.
        
        Args:
            memory_ids: List of memory IDs to start from
            depth: Maximum depth of traversal (default: 2)
            
        Returns:
            Dictionary with "nodes" and "edges" representing the graph
        """
        nodes: Dict[int, Dict[str, Any]] = {}
        edges: List[Dict[str, Any]] = []
        visited: set = set()
        
        # BFS traversal
        queue: List[Tuple[int, int]] = [(mem_id, 0) for mem_id in memory_ids]  # (memory_id, current_depth)
        
        while queue:
            current_id, current_depth = queue.pop(0)
            
            if current_id in visited or current_depth > depth:
                continue
            
            visited.add(current_id)
            
            # Get memory
            memory = self.storage.get_memory(current_id)
            if not memory:
                continue
            
            # Add node
            nodes[current_id] = {
                "id": current_id,
                "namespace": memory.namespace,
                "text": memory.text[:50] + "..." if len(memory.text) > 50 else memory.text,
                "importance": memory.importance
            }
            
            # If not at max depth, explore relationships
            if current_depth < depth:
                # Get outgoing relationships
                relationships = self.storage.get_relationships(source_id=current_id)
                for rel in relationships:
                    target_id = rel.target_id
                    
                    # Add edge
                    edges.append({
                        "source": current_id,
                        "target": target_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if target_id not in visited:
                        queue.append((target_id, current_depth + 1))
                
                # Get incoming relationships
                relationships = self.storage.get_relationships(target_id=None)
                for rel in relationships:
                    source_id = rel.source_id
                    
                    # Add edge
                    edges.append({
                        "source": source_id,
                        "target": current_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if source_id not in visited:
                        queue.append((source_id, current_depth + 1))
        
        return {
            "nodes": list(nodes.values()),
            "edges": edges
        }
    
    def xǁRelationshipManagerǁget_relationship_graph__mutmut_52(
        self,
        memory_ids: List[int],
        depth: int = 2
    ) -> Dict[str, Any]:
        """
        Get subgraph of relationships around given memories.
        
        Args:
            memory_ids: List of memory IDs to start from
            depth: Maximum depth of traversal (default: 2)
            
        Returns:
            Dictionary with "nodes" and "edges" representing the graph
        """
        nodes: Dict[int, Dict[str, Any]] = {}
        edges: List[Dict[str, Any]] = []
        visited: set = set()
        
        # BFS traversal
        queue: List[Tuple[int, int]] = [(mem_id, 0) for mem_id in memory_ids]  # (memory_id, current_depth)
        
        while queue:
            current_id, current_depth = queue.pop(0)
            
            if current_id in visited or current_depth > depth:
                continue
            
            visited.add(current_id)
            
            # Get memory
            memory = self.storage.get_memory(current_id)
            if not memory:
                continue
            
            # Add node
            nodes[current_id] = {
                "id": current_id,
                "namespace": memory.namespace,
                "text": memory.text[:50] + "..." if len(memory.text) > 50 else memory.text,
                "importance": memory.importance
            }
            
            # If not at max depth, explore relationships
            if current_depth < depth:
                # Get outgoing relationships
                relationships = self.storage.get_relationships(source_id=current_id)
                for rel in relationships:
                    target_id = rel.target_id
                    
                    # Add edge
                    edges.append({
                        "source": current_id,
                        "target": target_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if target_id not in visited:
                        queue.append((target_id, current_depth + 1))
                
                # Get incoming relationships
                relationships = self.storage.get_relationships(target_id=current_id)
                for rel in relationships:
                    source_id = None
                    
                    # Add edge
                    edges.append({
                        "source": source_id,
                        "target": current_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if source_id not in visited:
                        queue.append((source_id, current_depth + 1))
        
        return {
            "nodes": list(nodes.values()),
            "edges": edges
        }
    
    def xǁRelationshipManagerǁget_relationship_graph__mutmut_53(
        self,
        memory_ids: List[int],
        depth: int = 2
    ) -> Dict[str, Any]:
        """
        Get subgraph of relationships around given memories.
        
        Args:
            memory_ids: List of memory IDs to start from
            depth: Maximum depth of traversal (default: 2)
            
        Returns:
            Dictionary with "nodes" and "edges" representing the graph
        """
        nodes: Dict[int, Dict[str, Any]] = {}
        edges: List[Dict[str, Any]] = []
        visited: set = set()
        
        # BFS traversal
        queue: List[Tuple[int, int]] = [(mem_id, 0) for mem_id in memory_ids]  # (memory_id, current_depth)
        
        while queue:
            current_id, current_depth = queue.pop(0)
            
            if current_id in visited or current_depth > depth:
                continue
            
            visited.add(current_id)
            
            # Get memory
            memory = self.storage.get_memory(current_id)
            if not memory:
                continue
            
            # Add node
            nodes[current_id] = {
                "id": current_id,
                "namespace": memory.namespace,
                "text": memory.text[:50] + "..." if len(memory.text) > 50 else memory.text,
                "importance": memory.importance
            }
            
            # If not at max depth, explore relationships
            if current_depth < depth:
                # Get outgoing relationships
                relationships = self.storage.get_relationships(source_id=current_id)
                for rel in relationships:
                    target_id = rel.target_id
                    
                    # Add edge
                    edges.append({
                        "source": current_id,
                        "target": target_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if target_id not in visited:
                        queue.append((target_id, current_depth + 1))
                
                # Get incoming relationships
                relationships = self.storage.get_relationships(target_id=current_id)
                for rel in relationships:
                    source_id = rel.source_id
                    
                    # Add edge
                    edges.append(None)
                    
                    # Add to queue if not visited
                    if source_id not in visited:
                        queue.append((source_id, current_depth + 1))
        
        return {
            "nodes": list(nodes.values()),
            "edges": edges
        }
    
    def xǁRelationshipManagerǁget_relationship_graph__mutmut_54(
        self,
        memory_ids: List[int],
        depth: int = 2
    ) -> Dict[str, Any]:
        """
        Get subgraph of relationships around given memories.
        
        Args:
            memory_ids: List of memory IDs to start from
            depth: Maximum depth of traversal (default: 2)
            
        Returns:
            Dictionary with "nodes" and "edges" representing the graph
        """
        nodes: Dict[int, Dict[str, Any]] = {}
        edges: List[Dict[str, Any]] = []
        visited: set = set()
        
        # BFS traversal
        queue: List[Tuple[int, int]] = [(mem_id, 0) for mem_id in memory_ids]  # (memory_id, current_depth)
        
        while queue:
            current_id, current_depth = queue.pop(0)
            
            if current_id in visited or current_depth > depth:
                continue
            
            visited.add(current_id)
            
            # Get memory
            memory = self.storage.get_memory(current_id)
            if not memory:
                continue
            
            # Add node
            nodes[current_id] = {
                "id": current_id,
                "namespace": memory.namespace,
                "text": memory.text[:50] + "..." if len(memory.text) > 50 else memory.text,
                "importance": memory.importance
            }
            
            # If not at max depth, explore relationships
            if current_depth < depth:
                # Get outgoing relationships
                relationships = self.storage.get_relationships(source_id=current_id)
                for rel in relationships:
                    target_id = rel.target_id
                    
                    # Add edge
                    edges.append({
                        "source": current_id,
                        "target": target_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if target_id not in visited:
                        queue.append((target_id, current_depth + 1))
                
                # Get incoming relationships
                relationships = self.storage.get_relationships(target_id=current_id)
                for rel in relationships:
                    source_id = rel.source_id
                    
                    # Add edge
                    edges.append({
                        "XXsourceXX": source_id,
                        "target": current_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if source_id not in visited:
                        queue.append((source_id, current_depth + 1))
        
        return {
            "nodes": list(nodes.values()),
            "edges": edges
        }
    
    def xǁRelationshipManagerǁget_relationship_graph__mutmut_55(
        self,
        memory_ids: List[int],
        depth: int = 2
    ) -> Dict[str, Any]:
        """
        Get subgraph of relationships around given memories.
        
        Args:
            memory_ids: List of memory IDs to start from
            depth: Maximum depth of traversal (default: 2)
            
        Returns:
            Dictionary with "nodes" and "edges" representing the graph
        """
        nodes: Dict[int, Dict[str, Any]] = {}
        edges: List[Dict[str, Any]] = []
        visited: set = set()
        
        # BFS traversal
        queue: List[Tuple[int, int]] = [(mem_id, 0) for mem_id in memory_ids]  # (memory_id, current_depth)
        
        while queue:
            current_id, current_depth = queue.pop(0)
            
            if current_id in visited or current_depth > depth:
                continue
            
            visited.add(current_id)
            
            # Get memory
            memory = self.storage.get_memory(current_id)
            if not memory:
                continue
            
            # Add node
            nodes[current_id] = {
                "id": current_id,
                "namespace": memory.namespace,
                "text": memory.text[:50] + "..." if len(memory.text) > 50 else memory.text,
                "importance": memory.importance
            }
            
            # If not at max depth, explore relationships
            if current_depth < depth:
                # Get outgoing relationships
                relationships = self.storage.get_relationships(source_id=current_id)
                for rel in relationships:
                    target_id = rel.target_id
                    
                    # Add edge
                    edges.append({
                        "source": current_id,
                        "target": target_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if target_id not in visited:
                        queue.append((target_id, current_depth + 1))
                
                # Get incoming relationships
                relationships = self.storage.get_relationships(target_id=current_id)
                for rel in relationships:
                    source_id = rel.source_id
                    
                    # Add edge
                    edges.append({
                        "SOURCE": source_id,
                        "target": current_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if source_id not in visited:
                        queue.append((source_id, current_depth + 1))
        
        return {
            "nodes": list(nodes.values()),
            "edges": edges
        }
    
    def xǁRelationshipManagerǁget_relationship_graph__mutmut_56(
        self,
        memory_ids: List[int],
        depth: int = 2
    ) -> Dict[str, Any]:
        """
        Get subgraph of relationships around given memories.
        
        Args:
            memory_ids: List of memory IDs to start from
            depth: Maximum depth of traversal (default: 2)
            
        Returns:
            Dictionary with "nodes" and "edges" representing the graph
        """
        nodes: Dict[int, Dict[str, Any]] = {}
        edges: List[Dict[str, Any]] = []
        visited: set = set()
        
        # BFS traversal
        queue: List[Tuple[int, int]] = [(mem_id, 0) for mem_id in memory_ids]  # (memory_id, current_depth)
        
        while queue:
            current_id, current_depth = queue.pop(0)
            
            if current_id in visited or current_depth > depth:
                continue
            
            visited.add(current_id)
            
            # Get memory
            memory = self.storage.get_memory(current_id)
            if not memory:
                continue
            
            # Add node
            nodes[current_id] = {
                "id": current_id,
                "namespace": memory.namespace,
                "text": memory.text[:50] + "..." if len(memory.text) > 50 else memory.text,
                "importance": memory.importance
            }
            
            # If not at max depth, explore relationships
            if current_depth < depth:
                # Get outgoing relationships
                relationships = self.storage.get_relationships(source_id=current_id)
                for rel in relationships:
                    target_id = rel.target_id
                    
                    # Add edge
                    edges.append({
                        "source": current_id,
                        "target": target_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if target_id not in visited:
                        queue.append((target_id, current_depth + 1))
                
                # Get incoming relationships
                relationships = self.storage.get_relationships(target_id=current_id)
                for rel in relationships:
                    source_id = rel.source_id
                    
                    # Add edge
                    edges.append({
                        "source": source_id,
                        "XXtargetXX": current_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if source_id not in visited:
                        queue.append((source_id, current_depth + 1))
        
        return {
            "nodes": list(nodes.values()),
            "edges": edges
        }
    
    def xǁRelationshipManagerǁget_relationship_graph__mutmut_57(
        self,
        memory_ids: List[int],
        depth: int = 2
    ) -> Dict[str, Any]:
        """
        Get subgraph of relationships around given memories.
        
        Args:
            memory_ids: List of memory IDs to start from
            depth: Maximum depth of traversal (default: 2)
            
        Returns:
            Dictionary with "nodes" and "edges" representing the graph
        """
        nodes: Dict[int, Dict[str, Any]] = {}
        edges: List[Dict[str, Any]] = []
        visited: set = set()
        
        # BFS traversal
        queue: List[Tuple[int, int]] = [(mem_id, 0) for mem_id in memory_ids]  # (memory_id, current_depth)
        
        while queue:
            current_id, current_depth = queue.pop(0)
            
            if current_id in visited or current_depth > depth:
                continue
            
            visited.add(current_id)
            
            # Get memory
            memory = self.storage.get_memory(current_id)
            if not memory:
                continue
            
            # Add node
            nodes[current_id] = {
                "id": current_id,
                "namespace": memory.namespace,
                "text": memory.text[:50] + "..." if len(memory.text) > 50 else memory.text,
                "importance": memory.importance
            }
            
            # If not at max depth, explore relationships
            if current_depth < depth:
                # Get outgoing relationships
                relationships = self.storage.get_relationships(source_id=current_id)
                for rel in relationships:
                    target_id = rel.target_id
                    
                    # Add edge
                    edges.append({
                        "source": current_id,
                        "target": target_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if target_id not in visited:
                        queue.append((target_id, current_depth + 1))
                
                # Get incoming relationships
                relationships = self.storage.get_relationships(target_id=current_id)
                for rel in relationships:
                    source_id = rel.source_id
                    
                    # Add edge
                    edges.append({
                        "source": source_id,
                        "TARGET": current_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if source_id not in visited:
                        queue.append((source_id, current_depth + 1))
        
        return {
            "nodes": list(nodes.values()),
            "edges": edges
        }
    
    def xǁRelationshipManagerǁget_relationship_graph__mutmut_58(
        self,
        memory_ids: List[int],
        depth: int = 2
    ) -> Dict[str, Any]:
        """
        Get subgraph of relationships around given memories.
        
        Args:
            memory_ids: List of memory IDs to start from
            depth: Maximum depth of traversal (default: 2)
            
        Returns:
            Dictionary with "nodes" and "edges" representing the graph
        """
        nodes: Dict[int, Dict[str, Any]] = {}
        edges: List[Dict[str, Any]] = []
        visited: set = set()
        
        # BFS traversal
        queue: List[Tuple[int, int]] = [(mem_id, 0) for mem_id in memory_ids]  # (memory_id, current_depth)
        
        while queue:
            current_id, current_depth = queue.pop(0)
            
            if current_id in visited or current_depth > depth:
                continue
            
            visited.add(current_id)
            
            # Get memory
            memory = self.storage.get_memory(current_id)
            if not memory:
                continue
            
            # Add node
            nodes[current_id] = {
                "id": current_id,
                "namespace": memory.namespace,
                "text": memory.text[:50] + "..." if len(memory.text) > 50 else memory.text,
                "importance": memory.importance
            }
            
            # If not at max depth, explore relationships
            if current_depth < depth:
                # Get outgoing relationships
                relationships = self.storage.get_relationships(source_id=current_id)
                for rel in relationships:
                    target_id = rel.target_id
                    
                    # Add edge
                    edges.append({
                        "source": current_id,
                        "target": target_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if target_id not in visited:
                        queue.append((target_id, current_depth + 1))
                
                # Get incoming relationships
                relationships = self.storage.get_relationships(target_id=current_id)
                for rel in relationships:
                    source_id = rel.source_id
                    
                    # Add edge
                    edges.append({
                        "source": source_id,
                        "target": current_id,
                        "XXtypeXX": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if source_id not in visited:
                        queue.append((source_id, current_depth + 1))
        
        return {
            "nodes": list(nodes.values()),
            "edges": edges
        }
    
    def xǁRelationshipManagerǁget_relationship_graph__mutmut_59(
        self,
        memory_ids: List[int],
        depth: int = 2
    ) -> Dict[str, Any]:
        """
        Get subgraph of relationships around given memories.
        
        Args:
            memory_ids: List of memory IDs to start from
            depth: Maximum depth of traversal (default: 2)
            
        Returns:
            Dictionary with "nodes" and "edges" representing the graph
        """
        nodes: Dict[int, Dict[str, Any]] = {}
        edges: List[Dict[str, Any]] = []
        visited: set = set()
        
        # BFS traversal
        queue: List[Tuple[int, int]] = [(mem_id, 0) for mem_id in memory_ids]  # (memory_id, current_depth)
        
        while queue:
            current_id, current_depth = queue.pop(0)
            
            if current_id in visited or current_depth > depth:
                continue
            
            visited.add(current_id)
            
            # Get memory
            memory = self.storage.get_memory(current_id)
            if not memory:
                continue
            
            # Add node
            nodes[current_id] = {
                "id": current_id,
                "namespace": memory.namespace,
                "text": memory.text[:50] + "..." if len(memory.text) > 50 else memory.text,
                "importance": memory.importance
            }
            
            # If not at max depth, explore relationships
            if current_depth < depth:
                # Get outgoing relationships
                relationships = self.storage.get_relationships(source_id=current_id)
                for rel in relationships:
                    target_id = rel.target_id
                    
                    # Add edge
                    edges.append({
                        "source": current_id,
                        "target": target_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if target_id not in visited:
                        queue.append((target_id, current_depth + 1))
                
                # Get incoming relationships
                relationships = self.storage.get_relationships(target_id=current_id)
                for rel in relationships:
                    source_id = rel.source_id
                    
                    # Add edge
                    edges.append({
                        "source": source_id,
                        "target": current_id,
                        "TYPE": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if source_id not in visited:
                        queue.append((source_id, current_depth + 1))
        
        return {
            "nodes": list(nodes.values()),
            "edges": edges
        }
    
    def xǁRelationshipManagerǁget_relationship_graph__mutmut_60(
        self,
        memory_ids: List[int],
        depth: int = 2
    ) -> Dict[str, Any]:
        """
        Get subgraph of relationships around given memories.
        
        Args:
            memory_ids: List of memory IDs to start from
            depth: Maximum depth of traversal (default: 2)
            
        Returns:
            Dictionary with "nodes" and "edges" representing the graph
        """
        nodes: Dict[int, Dict[str, Any]] = {}
        edges: List[Dict[str, Any]] = []
        visited: set = set()
        
        # BFS traversal
        queue: List[Tuple[int, int]] = [(mem_id, 0) for mem_id in memory_ids]  # (memory_id, current_depth)
        
        while queue:
            current_id, current_depth = queue.pop(0)
            
            if current_id in visited or current_depth > depth:
                continue
            
            visited.add(current_id)
            
            # Get memory
            memory = self.storage.get_memory(current_id)
            if not memory:
                continue
            
            # Add node
            nodes[current_id] = {
                "id": current_id,
                "namespace": memory.namespace,
                "text": memory.text[:50] + "..." if len(memory.text) > 50 else memory.text,
                "importance": memory.importance
            }
            
            # If not at max depth, explore relationships
            if current_depth < depth:
                # Get outgoing relationships
                relationships = self.storage.get_relationships(source_id=current_id)
                for rel in relationships:
                    target_id = rel.target_id
                    
                    # Add edge
                    edges.append({
                        "source": current_id,
                        "target": target_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if target_id not in visited:
                        queue.append((target_id, current_depth + 1))
                
                # Get incoming relationships
                relationships = self.storage.get_relationships(target_id=current_id)
                for rel in relationships:
                    source_id = rel.source_id
                    
                    # Add edge
                    edges.append({
                        "source": source_id,
                        "target": current_id,
                        "type": rel.relation_type.value,
                        "XXstrengthXX": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if source_id not in visited:
                        queue.append((source_id, current_depth + 1))
        
        return {
            "nodes": list(nodes.values()),
            "edges": edges
        }
    
    def xǁRelationshipManagerǁget_relationship_graph__mutmut_61(
        self,
        memory_ids: List[int],
        depth: int = 2
    ) -> Dict[str, Any]:
        """
        Get subgraph of relationships around given memories.
        
        Args:
            memory_ids: List of memory IDs to start from
            depth: Maximum depth of traversal (default: 2)
            
        Returns:
            Dictionary with "nodes" and "edges" representing the graph
        """
        nodes: Dict[int, Dict[str, Any]] = {}
        edges: List[Dict[str, Any]] = []
        visited: set = set()
        
        # BFS traversal
        queue: List[Tuple[int, int]] = [(mem_id, 0) for mem_id in memory_ids]  # (memory_id, current_depth)
        
        while queue:
            current_id, current_depth = queue.pop(0)
            
            if current_id in visited or current_depth > depth:
                continue
            
            visited.add(current_id)
            
            # Get memory
            memory = self.storage.get_memory(current_id)
            if not memory:
                continue
            
            # Add node
            nodes[current_id] = {
                "id": current_id,
                "namespace": memory.namespace,
                "text": memory.text[:50] + "..." if len(memory.text) > 50 else memory.text,
                "importance": memory.importance
            }
            
            # If not at max depth, explore relationships
            if current_depth < depth:
                # Get outgoing relationships
                relationships = self.storage.get_relationships(source_id=current_id)
                for rel in relationships:
                    target_id = rel.target_id
                    
                    # Add edge
                    edges.append({
                        "source": current_id,
                        "target": target_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if target_id not in visited:
                        queue.append((target_id, current_depth + 1))
                
                # Get incoming relationships
                relationships = self.storage.get_relationships(target_id=current_id)
                for rel in relationships:
                    source_id = rel.source_id
                    
                    # Add edge
                    edges.append({
                        "source": source_id,
                        "target": current_id,
                        "type": rel.relation_type.value,
                        "STRENGTH": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if source_id not in visited:
                        queue.append((source_id, current_depth + 1))
        
        return {
            "nodes": list(nodes.values()),
            "edges": edges
        }
    
    def xǁRelationshipManagerǁget_relationship_graph__mutmut_62(
        self,
        memory_ids: List[int],
        depth: int = 2
    ) -> Dict[str, Any]:
        """
        Get subgraph of relationships around given memories.
        
        Args:
            memory_ids: List of memory IDs to start from
            depth: Maximum depth of traversal (default: 2)
            
        Returns:
            Dictionary with "nodes" and "edges" representing the graph
        """
        nodes: Dict[int, Dict[str, Any]] = {}
        edges: List[Dict[str, Any]] = []
        visited: set = set()
        
        # BFS traversal
        queue: List[Tuple[int, int]] = [(mem_id, 0) for mem_id in memory_ids]  # (memory_id, current_depth)
        
        while queue:
            current_id, current_depth = queue.pop(0)
            
            if current_id in visited or current_depth > depth:
                continue
            
            visited.add(current_id)
            
            # Get memory
            memory = self.storage.get_memory(current_id)
            if not memory:
                continue
            
            # Add node
            nodes[current_id] = {
                "id": current_id,
                "namespace": memory.namespace,
                "text": memory.text[:50] + "..." if len(memory.text) > 50 else memory.text,
                "importance": memory.importance
            }
            
            # If not at max depth, explore relationships
            if current_depth < depth:
                # Get outgoing relationships
                relationships = self.storage.get_relationships(source_id=current_id)
                for rel in relationships:
                    target_id = rel.target_id
                    
                    # Add edge
                    edges.append({
                        "source": current_id,
                        "target": target_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if target_id not in visited:
                        queue.append((target_id, current_depth + 1))
                
                # Get incoming relationships
                relationships = self.storage.get_relationships(target_id=current_id)
                for rel in relationships:
                    source_id = rel.source_id
                    
                    # Add edge
                    edges.append({
                        "source": source_id,
                        "target": current_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if source_id in visited:
                        queue.append((source_id, current_depth + 1))
        
        return {
            "nodes": list(nodes.values()),
            "edges": edges
        }
    
    def xǁRelationshipManagerǁget_relationship_graph__mutmut_63(
        self,
        memory_ids: List[int],
        depth: int = 2
    ) -> Dict[str, Any]:
        """
        Get subgraph of relationships around given memories.
        
        Args:
            memory_ids: List of memory IDs to start from
            depth: Maximum depth of traversal (default: 2)
            
        Returns:
            Dictionary with "nodes" and "edges" representing the graph
        """
        nodes: Dict[int, Dict[str, Any]] = {}
        edges: List[Dict[str, Any]] = []
        visited: set = set()
        
        # BFS traversal
        queue: List[Tuple[int, int]] = [(mem_id, 0) for mem_id in memory_ids]  # (memory_id, current_depth)
        
        while queue:
            current_id, current_depth = queue.pop(0)
            
            if current_id in visited or current_depth > depth:
                continue
            
            visited.add(current_id)
            
            # Get memory
            memory = self.storage.get_memory(current_id)
            if not memory:
                continue
            
            # Add node
            nodes[current_id] = {
                "id": current_id,
                "namespace": memory.namespace,
                "text": memory.text[:50] + "..." if len(memory.text) > 50 else memory.text,
                "importance": memory.importance
            }
            
            # If not at max depth, explore relationships
            if current_depth < depth:
                # Get outgoing relationships
                relationships = self.storage.get_relationships(source_id=current_id)
                for rel in relationships:
                    target_id = rel.target_id
                    
                    # Add edge
                    edges.append({
                        "source": current_id,
                        "target": target_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if target_id not in visited:
                        queue.append((target_id, current_depth + 1))
                
                # Get incoming relationships
                relationships = self.storage.get_relationships(target_id=current_id)
                for rel in relationships:
                    source_id = rel.source_id
                    
                    # Add edge
                    edges.append({
                        "source": source_id,
                        "target": current_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if source_id not in visited:
                        queue.append(None)
        
        return {
            "nodes": list(nodes.values()),
            "edges": edges
        }
    
    def xǁRelationshipManagerǁget_relationship_graph__mutmut_64(
        self,
        memory_ids: List[int],
        depth: int = 2
    ) -> Dict[str, Any]:
        """
        Get subgraph of relationships around given memories.
        
        Args:
            memory_ids: List of memory IDs to start from
            depth: Maximum depth of traversal (default: 2)
            
        Returns:
            Dictionary with "nodes" and "edges" representing the graph
        """
        nodes: Dict[int, Dict[str, Any]] = {}
        edges: List[Dict[str, Any]] = []
        visited: set = set()
        
        # BFS traversal
        queue: List[Tuple[int, int]] = [(mem_id, 0) for mem_id in memory_ids]  # (memory_id, current_depth)
        
        while queue:
            current_id, current_depth = queue.pop(0)
            
            if current_id in visited or current_depth > depth:
                continue
            
            visited.add(current_id)
            
            # Get memory
            memory = self.storage.get_memory(current_id)
            if not memory:
                continue
            
            # Add node
            nodes[current_id] = {
                "id": current_id,
                "namespace": memory.namespace,
                "text": memory.text[:50] + "..." if len(memory.text) > 50 else memory.text,
                "importance": memory.importance
            }
            
            # If not at max depth, explore relationships
            if current_depth < depth:
                # Get outgoing relationships
                relationships = self.storage.get_relationships(source_id=current_id)
                for rel in relationships:
                    target_id = rel.target_id
                    
                    # Add edge
                    edges.append({
                        "source": current_id,
                        "target": target_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if target_id not in visited:
                        queue.append((target_id, current_depth + 1))
                
                # Get incoming relationships
                relationships = self.storage.get_relationships(target_id=current_id)
                for rel in relationships:
                    source_id = rel.source_id
                    
                    # Add edge
                    edges.append({
                        "source": source_id,
                        "target": current_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if source_id not in visited:
                        queue.append((source_id, current_depth - 1))
        
        return {
            "nodes": list(nodes.values()),
            "edges": edges
        }
    
    def xǁRelationshipManagerǁget_relationship_graph__mutmut_65(
        self,
        memory_ids: List[int],
        depth: int = 2
    ) -> Dict[str, Any]:
        """
        Get subgraph of relationships around given memories.
        
        Args:
            memory_ids: List of memory IDs to start from
            depth: Maximum depth of traversal (default: 2)
            
        Returns:
            Dictionary with "nodes" and "edges" representing the graph
        """
        nodes: Dict[int, Dict[str, Any]] = {}
        edges: List[Dict[str, Any]] = []
        visited: set = set()
        
        # BFS traversal
        queue: List[Tuple[int, int]] = [(mem_id, 0) for mem_id in memory_ids]  # (memory_id, current_depth)
        
        while queue:
            current_id, current_depth = queue.pop(0)
            
            if current_id in visited or current_depth > depth:
                continue
            
            visited.add(current_id)
            
            # Get memory
            memory = self.storage.get_memory(current_id)
            if not memory:
                continue
            
            # Add node
            nodes[current_id] = {
                "id": current_id,
                "namespace": memory.namespace,
                "text": memory.text[:50] + "..." if len(memory.text) > 50 else memory.text,
                "importance": memory.importance
            }
            
            # If not at max depth, explore relationships
            if current_depth < depth:
                # Get outgoing relationships
                relationships = self.storage.get_relationships(source_id=current_id)
                for rel in relationships:
                    target_id = rel.target_id
                    
                    # Add edge
                    edges.append({
                        "source": current_id,
                        "target": target_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if target_id not in visited:
                        queue.append((target_id, current_depth + 1))
                
                # Get incoming relationships
                relationships = self.storage.get_relationships(target_id=current_id)
                for rel in relationships:
                    source_id = rel.source_id
                    
                    # Add edge
                    edges.append({
                        "source": source_id,
                        "target": current_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if source_id not in visited:
                        queue.append((source_id, current_depth + 2))
        
        return {
            "nodes": list(nodes.values()),
            "edges": edges
        }
    
    def xǁRelationshipManagerǁget_relationship_graph__mutmut_66(
        self,
        memory_ids: List[int],
        depth: int = 2
    ) -> Dict[str, Any]:
        """
        Get subgraph of relationships around given memories.
        
        Args:
            memory_ids: List of memory IDs to start from
            depth: Maximum depth of traversal (default: 2)
            
        Returns:
            Dictionary with "nodes" and "edges" representing the graph
        """
        nodes: Dict[int, Dict[str, Any]] = {}
        edges: List[Dict[str, Any]] = []
        visited: set = set()
        
        # BFS traversal
        queue: List[Tuple[int, int]] = [(mem_id, 0) for mem_id in memory_ids]  # (memory_id, current_depth)
        
        while queue:
            current_id, current_depth = queue.pop(0)
            
            if current_id in visited or current_depth > depth:
                continue
            
            visited.add(current_id)
            
            # Get memory
            memory = self.storage.get_memory(current_id)
            if not memory:
                continue
            
            # Add node
            nodes[current_id] = {
                "id": current_id,
                "namespace": memory.namespace,
                "text": memory.text[:50] + "..." if len(memory.text) > 50 else memory.text,
                "importance": memory.importance
            }
            
            # If not at max depth, explore relationships
            if current_depth < depth:
                # Get outgoing relationships
                relationships = self.storage.get_relationships(source_id=current_id)
                for rel in relationships:
                    target_id = rel.target_id
                    
                    # Add edge
                    edges.append({
                        "source": current_id,
                        "target": target_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if target_id not in visited:
                        queue.append((target_id, current_depth + 1))
                
                # Get incoming relationships
                relationships = self.storage.get_relationships(target_id=current_id)
                for rel in relationships:
                    source_id = rel.source_id
                    
                    # Add edge
                    edges.append({
                        "source": source_id,
                        "target": current_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if source_id not in visited:
                        queue.append((source_id, current_depth + 1))
        
        return {
            "XXnodesXX": list(nodes.values()),
            "edges": edges
        }
    
    def xǁRelationshipManagerǁget_relationship_graph__mutmut_67(
        self,
        memory_ids: List[int],
        depth: int = 2
    ) -> Dict[str, Any]:
        """
        Get subgraph of relationships around given memories.
        
        Args:
            memory_ids: List of memory IDs to start from
            depth: Maximum depth of traversal (default: 2)
            
        Returns:
            Dictionary with "nodes" and "edges" representing the graph
        """
        nodes: Dict[int, Dict[str, Any]] = {}
        edges: List[Dict[str, Any]] = []
        visited: set = set()
        
        # BFS traversal
        queue: List[Tuple[int, int]] = [(mem_id, 0) for mem_id in memory_ids]  # (memory_id, current_depth)
        
        while queue:
            current_id, current_depth = queue.pop(0)
            
            if current_id in visited or current_depth > depth:
                continue
            
            visited.add(current_id)
            
            # Get memory
            memory = self.storage.get_memory(current_id)
            if not memory:
                continue
            
            # Add node
            nodes[current_id] = {
                "id": current_id,
                "namespace": memory.namespace,
                "text": memory.text[:50] + "..." if len(memory.text) > 50 else memory.text,
                "importance": memory.importance
            }
            
            # If not at max depth, explore relationships
            if current_depth < depth:
                # Get outgoing relationships
                relationships = self.storage.get_relationships(source_id=current_id)
                for rel in relationships:
                    target_id = rel.target_id
                    
                    # Add edge
                    edges.append({
                        "source": current_id,
                        "target": target_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if target_id not in visited:
                        queue.append((target_id, current_depth + 1))
                
                # Get incoming relationships
                relationships = self.storage.get_relationships(target_id=current_id)
                for rel in relationships:
                    source_id = rel.source_id
                    
                    # Add edge
                    edges.append({
                        "source": source_id,
                        "target": current_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if source_id not in visited:
                        queue.append((source_id, current_depth + 1))
        
        return {
            "NODES": list(nodes.values()),
            "edges": edges
        }
    
    def xǁRelationshipManagerǁget_relationship_graph__mutmut_68(
        self,
        memory_ids: List[int],
        depth: int = 2
    ) -> Dict[str, Any]:
        """
        Get subgraph of relationships around given memories.
        
        Args:
            memory_ids: List of memory IDs to start from
            depth: Maximum depth of traversal (default: 2)
            
        Returns:
            Dictionary with "nodes" and "edges" representing the graph
        """
        nodes: Dict[int, Dict[str, Any]] = {}
        edges: List[Dict[str, Any]] = []
        visited: set = set()
        
        # BFS traversal
        queue: List[Tuple[int, int]] = [(mem_id, 0) for mem_id in memory_ids]  # (memory_id, current_depth)
        
        while queue:
            current_id, current_depth = queue.pop(0)
            
            if current_id in visited or current_depth > depth:
                continue
            
            visited.add(current_id)
            
            # Get memory
            memory = self.storage.get_memory(current_id)
            if not memory:
                continue
            
            # Add node
            nodes[current_id] = {
                "id": current_id,
                "namespace": memory.namespace,
                "text": memory.text[:50] + "..." if len(memory.text) > 50 else memory.text,
                "importance": memory.importance
            }
            
            # If not at max depth, explore relationships
            if current_depth < depth:
                # Get outgoing relationships
                relationships = self.storage.get_relationships(source_id=current_id)
                for rel in relationships:
                    target_id = rel.target_id
                    
                    # Add edge
                    edges.append({
                        "source": current_id,
                        "target": target_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if target_id not in visited:
                        queue.append((target_id, current_depth + 1))
                
                # Get incoming relationships
                relationships = self.storage.get_relationships(target_id=current_id)
                for rel in relationships:
                    source_id = rel.source_id
                    
                    # Add edge
                    edges.append({
                        "source": source_id,
                        "target": current_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if source_id not in visited:
                        queue.append((source_id, current_depth + 1))
        
        return {
            "nodes": list(None),
            "edges": edges
        }
    
    def xǁRelationshipManagerǁget_relationship_graph__mutmut_69(
        self,
        memory_ids: List[int],
        depth: int = 2
    ) -> Dict[str, Any]:
        """
        Get subgraph of relationships around given memories.
        
        Args:
            memory_ids: List of memory IDs to start from
            depth: Maximum depth of traversal (default: 2)
            
        Returns:
            Dictionary with "nodes" and "edges" representing the graph
        """
        nodes: Dict[int, Dict[str, Any]] = {}
        edges: List[Dict[str, Any]] = []
        visited: set = set()
        
        # BFS traversal
        queue: List[Tuple[int, int]] = [(mem_id, 0) for mem_id in memory_ids]  # (memory_id, current_depth)
        
        while queue:
            current_id, current_depth = queue.pop(0)
            
            if current_id in visited or current_depth > depth:
                continue
            
            visited.add(current_id)
            
            # Get memory
            memory = self.storage.get_memory(current_id)
            if not memory:
                continue
            
            # Add node
            nodes[current_id] = {
                "id": current_id,
                "namespace": memory.namespace,
                "text": memory.text[:50] + "..." if len(memory.text) > 50 else memory.text,
                "importance": memory.importance
            }
            
            # If not at max depth, explore relationships
            if current_depth < depth:
                # Get outgoing relationships
                relationships = self.storage.get_relationships(source_id=current_id)
                for rel in relationships:
                    target_id = rel.target_id
                    
                    # Add edge
                    edges.append({
                        "source": current_id,
                        "target": target_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if target_id not in visited:
                        queue.append((target_id, current_depth + 1))
                
                # Get incoming relationships
                relationships = self.storage.get_relationships(target_id=current_id)
                for rel in relationships:
                    source_id = rel.source_id
                    
                    # Add edge
                    edges.append({
                        "source": source_id,
                        "target": current_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if source_id not in visited:
                        queue.append((source_id, current_depth + 1))
        
        return {
            "nodes": list(nodes.values()),
            "XXedgesXX": edges
        }
    
    def xǁRelationshipManagerǁget_relationship_graph__mutmut_70(
        self,
        memory_ids: List[int],
        depth: int = 2
    ) -> Dict[str, Any]:
        """
        Get subgraph of relationships around given memories.
        
        Args:
            memory_ids: List of memory IDs to start from
            depth: Maximum depth of traversal (default: 2)
            
        Returns:
            Dictionary with "nodes" and "edges" representing the graph
        """
        nodes: Dict[int, Dict[str, Any]] = {}
        edges: List[Dict[str, Any]] = []
        visited: set = set()
        
        # BFS traversal
        queue: List[Tuple[int, int]] = [(mem_id, 0) for mem_id in memory_ids]  # (memory_id, current_depth)
        
        while queue:
            current_id, current_depth = queue.pop(0)
            
            if current_id in visited or current_depth > depth:
                continue
            
            visited.add(current_id)
            
            # Get memory
            memory = self.storage.get_memory(current_id)
            if not memory:
                continue
            
            # Add node
            nodes[current_id] = {
                "id": current_id,
                "namespace": memory.namespace,
                "text": memory.text[:50] + "..." if len(memory.text) > 50 else memory.text,
                "importance": memory.importance
            }
            
            # If not at max depth, explore relationships
            if current_depth < depth:
                # Get outgoing relationships
                relationships = self.storage.get_relationships(source_id=current_id)
                for rel in relationships:
                    target_id = rel.target_id
                    
                    # Add edge
                    edges.append({
                        "source": current_id,
                        "target": target_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if target_id not in visited:
                        queue.append((target_id, current_depth + 1))
                
                # Get incoming relationships
                relationships = self.storage.get_relationships(target_id=current_id)
                for rel in relationships:
                    source_id = rel.source_id
                    
                    # Add edge
                    edges.append({
                        "source": source_id,
                        "target": current_id,
                        "type": rel.relation_type.value,
                        "strength": rel.strength
                    })
                    
                    # Add to queue if not visited
                    if source_id not in visited:
                        queue.append((source_id, current_depth + 1))
        
        return {
            "nodes": list(nodes.values()),
            "EDGES": edges
        }
    
    xǁRelationshipManagerǁget_relationship_graph__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁRelationshipManagerǁget_relationship_graph__mutmut_1': xǁRelationshipManagerǁget_relationship_graph__mutmut_1, 
        'xǁRelationshipManagerǁget_relationship_graph__mutmut_2': xǁRelationshipManagerǁget_relationship_graph__mutmut_2, 
        'xǁRelationshipManagerǁget_relationship_graph__mutmut_3': xǁRelationshipManagerǁget_relationship_graph__mutmut_3, 
        'xǁRelationshipManagerǁget_relationship_graph__mutmut_4': xǁRelationshipManagerǁget_relationship_graph__mutmut_4, 
        'xǁRelationshipManagerǁget_relationship_graph__mutmut_5': xǁRelationshipManagerǁget_relationship_graph__mutmut_5, 
        'xǁRelationshipManagerǁget_relationship_graph__mutmut_6': xǁRelationshipManagerǁget_relationship_graph__mutmut_6, 
        'xǁRelationshipManagerǁget_relationship_graph__mutmut_7': xǁRelationshipManagerǁget_relationship_graph__mutmut_7, 
        'xǁRelationshipManagerǁget_relationship_graph__mutmut_8': xǁRelationshipManagerǁget_relationship_graph__mutmut_8, 
        'xǁRelationshipManagerǁget_relationship_graph__mutmut_9': xǁRelationshipManagerǁget_relationship_graph__mutmut_9, 
        'xǁRelationshipManagerǁget_relationship_graph__mutmut_10': xǁRelationshipManagerǁget_relationship_graph__mutmut_10, 
        'xǁRelationshipManagerǁget_relationship_graph__mutmut_11': xǁRelationshipManagerǁget_relationship_graph__mutmut_11, 
        'xǁRelationshipManagerǁget_relationship_graph__mutmut_12': xǁRelationshipManagerǁget_relationship_graph__mutmut_12, 
        'xǁRelationshipManagerǁget_relationship_graph__mutmut_13': xǁRelationshipManagerǁget_relationship_graph__mutmut_13, 
        'xǁRelationshipManagerǁget_relationship_graph__mutmut_14': xǁRelationshipManagerǁget_relationship_graph__mutmut_14, 
        'xǁRelationshipManagerǁget_relationship_graph__mutmut_15': xǁRelationshipManagerǁget_relationship_graph__mutmut_15, 
        'xǁRelationshipManagerǁget_relationship_graph__mutmut_16': xǁRelationshipManagerǁget_relationship_graph__mutmut_16, 
        'xǁRelationshipManagerǁget_relationship_graph__mutmut_17': xǁRelationshipManagerǁget_relationship_graph__mutmut_17, 
        'xǁRelationshipManagerǁget_relationship_graph__mutmut_18': xǁRelationshipManagerǁget_relationship_graph__mutmut_18, 
        'xǁRelationshipManagerǁget_relationship_graph__mutmut_19': xǁRelationshipManagerǁget_relationship_graph__mutmut_19, 
        'xǁRelationshipManagerǁget_relationship_graph__mutmut_20': xǁRelationshipManagerǁget_relationship_graph__mutmut_20, 
        'xǁRelationshipManagerǁget_relationship_graph__mutmut_21': xǁRelationshipManagerǁget_relationship_graph__mutmut_21, 
        'xǁRelationshipManagerǁget_relationship_graph__mutmut_22': xǁRelationshipManagerǁget_relationship_graph__mutmut_22, 
        'xǁRelationshipManagerǁget_relationship_graph__mutmut_23': xǁRelationshipManagerǁget_relationship_graph__mutmut_23, 
        'xǁRelationshipManagerǁget_relationship_graph__mutmut_24': xǁRelationshipManagerǁget_relationship_graph__mutmut_24, 
        'xǁRelationshipManagerǁget_relationship_graph__mutmut_25': xǁRelationshipManagerǁget_relationship_graph__mutmut_25, 
        'xǁRelationshipManagerǁget_relationship_graph__mutmut_26': xǁRelationshipManagerǁget_relationship_graph__mutmut_26, 
        'xǁRelationshipManagerǁget_relationship_graph__mutmut_27': xǁRelationshipManagerǁget_relationship_graph__mutmut_27, 
        'xǁRelationshipManagerǁget_relationship_graph__mutmut_28': xǁRelationshipManagerǁget_relationship_graph__mutmut_28, 
        'xǁRelationshipManagerǁget_relationship_graph__mutmut_29': xǁRelationshipManagerǁget_relationship_graph__mutmut_29, 
        'xǁRelationshipManagerǁget_relationship_graph__mutmut_30': xǁRelationshipManagerǁget_relationship_graph__mutmut_30, 
        'xǁRelationshipManagerǁget_relationship_graph__mutmut_31': xǁRelationshipManagerǁget_relationship_graph__mutmut_31, 
        'xǁRelationshipManagerǁget_relationship_graph__mutmut_32': xǁRelationshipManagerǁget_relationship_graph__mutmut_32, 
        'xǁRelationshipManagerǁget_relationship_graph__mutmut_33': xǁRelationshipManagerǁget_relationship_graph__mutmut_33, 
        'xǁRelationshipManagerǁget_relationship_graph__mutmut_34': xǁRelationshipManagerǁget_relationship_graph__mutmut_34, 
        'xǁRelationshipManagerǁget_relationship_graph__mutmut_35': xǁRelationshipManagerǁget_relationship_graph__mutmut_35, 
        'xǁRelationshipManagerǁget_relationship_graph__mutmut_36': xǁRelationshipManagerǁget_relationship_graph__mutmut_36, 
        'xǁRelationshipManagerǁget_relationship_graph__mutmut_37': xǁRelationshipManagerǁget_relationship_graph__mutmut_37, 
        'xǁRelationshipManagerǁget_relationship_graph__mutmut_38': xǁRelationshipManagerǁget_relationship_graph__mutmut_38, 
        'xǁRelationshipManagerǁget_relationship_graph__mutmut_39': xǁRelationshipManagerǁget_relationship_graph__mutmut_39, 
        'xǁRelationshipManagerǁget_relationship_graph__mutmut_40': xǁRelationshipManagerǁget_relationship_graph__mutmut_40, 
        'xǁRelationshipManagerǁget_relationship_graph__mutmut_41': xǁRelationshipManagerǁget_relationship_graph__mutmut_41, 
        'xǁRelationshipManagerǁget_relationship_graph__mutmut_42': xǁRelationshipManagerǁget_relationship_graph__mutmut_42, 
        'xǁRelationshipManagerǁget_relationship_graph__mutmut_43': xǁRelationshipManagerǁget_relationship_graph__mutmut_43, 
        'xǁRelationshipManagerǁget_relationship_graph__mutmut_44': xǁRelationshipManagerǁget_relationship_graph__mutmut_44, 
        'xǁRelationshipManagerǁget_relationship_graph__mutmut_45': xǁRelationshipManagerǁget_relationship_graph__mutmut_45, 
        'xǁRelationshipManagerǁget_relationship_graph__mutmut_46': xǁRelationshipManagerǁget_relationship_graph__mutmut_46, 
        'xǁRelationshipManagerǁget_relationship_graph__mutmut_47': xǁRelationshipManagerǁget_relationship_graph__mutmut_47, 
        'xǁRelationshipManagerǁget_relationship_graph__mutmut_48': xǁRelationshipManagerǁget_relationship_graph__mutmut_48, 
        'xǁRelationshipManagerǁget_relationship_graph__mutmut_49': xǁRelationshipManagerǁget_relationship_graph__mutmut_49, 
        'xǁRelationshipManagerǁget_relationship_graph__mutmut_50': xǁRelationshipManagerǁget_relationship_graph__mutmut_50, 
        'xǁRelationshipManagerǁget_relationship_graph__mutmut_51': xǁRelationshipManagerǁget_relationship_graph__mutmut_51, 
        'xǁRelationshipManagerǁget_relationship_graph__mutmut_52': xǁRelationshipManagerǁget_relationship_graph__mutmut_52, 
        'xǁRelationshipManagerǁget_relationship_graph__mutmut_53': xǁRelationshipManagerǁget_relationship_graph__mutmut_53, 
        'xǁRelationshipManagerǁget_relationship_graph__mutmut_54': xǁRelationshipManagerǁget_relationship_graph__mutmut_54, 
        'xǁRelationshipManagerǁget_relationship_graph__mutmut_55': xǁRelationshipManagerǁget_relationship_graph__mutmut_55, 
        'xǁRelationshipManagerǁget_relationship_graph__mutmut_56': xǁRelationshipManagerǁget_relationship_graph__mutmut_56, 
        'xǁRelationshipManagerǁget_relationship_graph__mutmut_57': xǁRelationshipManagerǁget_relationship_graph__mutmut_57, 
        'xǁRelationshipManagerǁget_relationship_graph__mutmut_58': xǁRelationshipManagerǁget_relationship_graph__mutmut_58, 
        'xǁRelationshipManagerǁget_relationship_graph__mutmut_59': xǁRelationshipManagerǁget_relationship_graph__mutmut_59, 
        'xǁRelationshipManagerǁget_relationship_graph__mutmut_60': xǁRelationshipManagerǁget_relationship_graph__mutmut_60, 
        'xǁRelationshipManagerǁget_relationship_graph__mutmut_61': xǁRelationshipManagerǁget_relationship_graph__mutmut_61, 
        'xǁRelationshipManagerǁget_relationship_graph__mutmut_62': xǁRelationshipManagerǁget_relationship_graph__mutmut_62, 
        'xǁRelationshipManagerǁget_relationship_graph__mutmut_63': xǁRelationshipManagerǁget_relationship_graph__mutmut_63, 
        'xǁRelationshipManagerǁget_relationship_graph__mutmut_64': xǁRelationshipManagerǁget_relationship_graph__mutmut_64, 
        'xǁRelationshipManagerǁget_relationship_graph__mutmut_65': xǁRelationshipManagerǁget_relationship_graph__mutmut_65, 
        'xǁRelationshipManagerǁget_relationship_graph__mutmut_66': xǁRelationshipManagerǁget_relationship_graph__mutmut_66, 
        'xǁRelationshipManagerǁget_relationship_graph__mutmut_67': xǁRelationshipManagerǁget_relationship_graph__mutmut_67, 
        'xǁRelationshipManagerǁget_relationship_graph__mutmut_68': xǁRelationshipManagerǁget_relationship_graph__mutmut_68, 
        'xǁRelationshipManagerǁget_relationship_graph__mutmut_69': xǁRelationshipManagerǁget_relationship_graph__mutmut_69, 
        'xǁRelationshipManagerǁget_relationship_graph__mutmut_70': xǁRelationshipManagerǁget_relationship_graph__mutmut_70
    }
    
    def get_relationship_graph(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁRelationshipManagerǁget_relationship_graph__mutmut_orig"), object.__getattribute__(self, "xǁRelationshipManagerǁget_relationship_graph__mutmut_mutants"), args, kwargs, self)
        return result 
    
    get_relationship_graph.__signature__ = _mutmut_signature(xǁRelationshipManagerǁget_relationship_graph__mutmut_orig)
    xǁRelationshipManagerǁget_relationship_graph__mutmut_orig.__name__ = 'xǁRelationshipManagerǁget_relationship_graph'
    
    def xǁRelationshipManagerǁauto_detect_relationships__mutmut_orig(
        self,
        memory_id: int,
        storage: MemoryStorage,
        similarity_threshold: float = 0.85
    ) -> List[RelationshipRecord]:
        """
        Auto-detect relationships for a memory.
        
        This method is a placeholder - actual auto-detection requires
        MemoryManager for similarity search. Will be implemented in
        MemoryManager integration.
        
        Args:
            memory_id: ID of memory to detect relationships for
            storage: MemoryStorage instance (for namespace queries)
            similarity_threshold: Minimum similarity for SIMILAR_TO (default: 0.85)
            
        Returns:
            List of detected RelationshipRecord objects
        """
        detected: List[RelationshipRecord] = []
        
        memory = storage.get_memory(memory_id)
        if not memory:
            return detected
        
        # Detect namespace hierarchy relationships
        if "." in memory.namespace:
            parent_ns = memory.namespace.rsplit(".", 1)[0]
            parent_memories = storage.search_by_namespace(parent_ns, exact=True, limit=10)
            
            for parent_memory in parent_memories:
                if parent_memory.id and parent_memory.id != memory_id:
                    # Child namespace elaborates parent
                    rel = RelationshipRecord(
                        source_id=memory_id,
                        target_id=parent_memory.id,
                        relation_type=RelationType.ELABORATES,
                        strength=0.7,
                        metadata={"detection_method": "namespace_hierarchy", "auto_detected": True},
                        created_at=datetime.now(timezone.utc)
                    )
                    detected.append(rel)
        
        return detected
    
    def xǁRelationshipManagerǁauto_detect_relationships__mutmut_1(
        self,
        memory_id: int,
        storage: MemoryStorage,
        similarity_threshold: float = 1.85
    ) -> List[RelationshipRecord]:
        """
        Auto-detect relationships for a memory.
        
        This method is a placeholder - actual auto-detection requires
        MemoryManager for similarity search. Will be implemented in
        MemoryManager integration.
        
        Args:
            memory_id: ID of memory to detect relationships for
            storage: MemoryStorage instance (for namespace queries)
            similarity_threshold: Minimum similarity for SIMILAR_TO (default: 0.85)
            
        Returns:
            List of detected RelationshipRecord objects
        """
        detected: List[RelationshipRecord] = []
        
        memory = storage.get_memory(memory_id)
        if not memory:
            return detected
        
        # Detect namespace hierarchy relationships
        if "." in memory.namespace:
            parent_ns = memory.namespace.rsplit(".", 1)[0]
            parent_memories = storage.search_by_namespace(parent_ns, exact=True, limit=10)
            
            for parent_memory in parent_memories:
                if parent_memory.id and parent_memory.id != memory_id:
                    # Child namespace elaborates parent
                    rel = RelationshipRecord(
                        source_id=memory_id,
                        target_id=parent_memory.id,
                        relation_type=RelationType.ELABORATES,
                        strength=0.7,
                        metadata={"detection_method": "namespace_hierarchy", "auto_detected": True},
                        created_at=datetime.now(timezone.utc)
                    )
                    detected.append(rel)
        
        return detected
    
    def xǁRelationshipManagerǁauto_detect_relationships__mutmut_2(
        self,
        memory_id: int,
        storage: MemoryStorage,
        similarity_threshold: float = 0.85
    ) -> List[RelationshipRecord]:
        """
        Auto-detect relationships for a memory.
        
        This method is a placeholder - actual auto-detection requires
        MemoryManager for similarity search. Will be implemented in
        MemoryManager integration.
        
        Args:
            memory_id: ID of memory to detect relationships for
            storage: MemoryStorage instance (for namespace queries)
            similarity_threshold: Minimum similarity for SIMILAR_TO (default: 0.85)
            
        Returns:
            List of detected RelationshipRecord objects
        """
        detected: List[RelationshipRecord] = None
        
        memory = storage.get_memory(memory_id)
        if not memory:
            return detected
        
        # Detect namespace hierarchy relationships
        if "." in memory.namespace:
            parent_ns = memory.namespace.rsplit(".", 1)[0]
            parent_memories = storage.search_by_namespace(parent_ns, exact=True, limit=10)
            
            for parent_memory in parent_memories:
                if parent_memory.id and parent_memory.id != memory_id:
                    # Child namespace elaborates parent
                    rel = RelationshipRecord(
                        source_id=memory_id,
                        target_id=parent_memory.id,
                        relation_type=RelationType.ELABORATES,
                        strength=0.7,
                        metadata={"detection_method": "namespace_hierarchy", "auto_detected": True},
                        created_at=datetime.now(timezone.utc)
                    )
                    detected.append(rel)
        
        return detected
    
    def xǁRelationshipManagerǁauto_detect_relationships__mutmut_3(
        self,
        memory_id: int,
        storage: MemoryStorage,
        similarity_threshold: float = 0.85
    ) -> List[RelationshipRecord]:
        """
        Auto-detect relationships for a memory.
        
        This method is a placeholder - actual auto-detection requires
        MemoryManager for similarity search. Will be implemented in
        MemoryManager integration.
        
        Args:
            memory_id: ID of memory to detect relationships for
            storage: MemoryStorage instance (for namespace queries)
            similarity_threshold: Minimum similarity for SIMILAR_TO (default: 0.85)
            
        Returns:
            List of detected RelationshipRecord objects
        """
        detected: List[RelationshipRecord] = []
        
        memory = None
        if not memory:
            return detected
        
        # Detect namespace hierarchy relationships
        if "." in memory.namespace:
            parent_ns = memory.namespace.rsplit(".", 1)[0]
            parent_memories = storage.search_by_namespace(parent_ns, exact=True, limit=10)
            
            for parent_memory in parent_memories:
                if parent_memory.id and parent_memory.id != memory_id:
                    # Child namespace elaborates parent
                    rel = RelationshipRecord(
                        source_id=memory_id,
                        target_id=parent_memory.id,
                        relation_type=RelationType.ELABORATES,
                        strength=0.7,
                        metadata={"detection_method": "namespace_hierarchy", "auto_detected": True},
                        created_at=datetime.now(timezone.utc)
                    )
                    detected.append(rel)
        
        return detected
    
    def xǁRelationshipManagerǁauto_detect_relationships__mutmut_4(
        self,
        memory_id: int,
        storage: MemoryStorage,
        similarity_threshold: float = 0.85
    ) -> List[RelationshipRecord]:
        """
        Auto-detect relationships for a memory.
        
        This method is a placeholder - actual auto-detection requires
        MemoryManager for similarity search. Will be implemented in
        MemoryManager integration.
        
        Args:
            memory_id: ID of memory to detect relationships for
            storage: MemoryStorage instance (for namespace queries)
            similarity_threshold: Minimum similarity for SIMILAR_TO (default: 0.85)
            
        Returns:
            List of detected RelationshipRecord objects
        """
        detected: List[RelationshipRecord] = []
        
        memory = storage.get_memory(None)
        if not memory:
            return detected
        
        # Detect namespace hierarchy relationships
        if "." in memory.namespace:
            parent_ns = memory.namespace.rsplit(".", 1)[0]
            parent_memories = storage.search_by_namespace(parent_ns, exact=True, limit=10)
            
            for parent_memory in parent_memories:
                if parent_memory.id and parent_memory.id != memory_id:
                    # Child namespace elaborates parent
                    rel = RelationshipRecord(
                        source_id=memory_id,
                        target_id=parent_memory.id,
                        relation_type=RelationType.ELABORATES,
                        strength=0.7,
                        metadata={"detection_method": "namespace_hierarchy", "auto_detected": True},
                        created_at=datetime.now(timezone.utc)
                    )
                    detected.append(rel)
        
        return detected
    
    def xǁRelationshipManagerǁauto_detect_relationships__mutmut_5(
        self,
        memory_id: int,
        storage: MemoryStorage,
        similarity_threshold: float = 0.85
    ) -> List[RelationshipRecord]:
        """
        Auto-detect relationships for a memory.
        
        This method is a placeholder - actual auto-detection requires
        MemoryManager for similarity search. Will be implemented in
        MemoryManager integration.
        
        Args:
            memory_id: ID of memory to detect relationships for
            storage: MemoryStorage instance (for namespace queries)
            similarity_threshold: Minimum similarity for SIMILAR_TO (default: 0.85)
            
        Returns:
            List of detected RelationshipRecord objects
        """
        detected: List[RelationshipRecord] = []
        
        memory = storage.get_memory(memory_id)
        if memory:
            return detected
        
        # Detect namespace hierarchy relationships
        if "." in memory.namespace:
            parent_ns = memory.namespace.rsplit(".", 1)[0]
            parent_memories = storage.search_by_namespace(parent_ns, exact=True, limit=10)
            
            for parent_memory in parent_memories:
                if parent_memory.id and parent_memory.id != memory_id:
                    # Child namespace elaborates parent
                    rel = RelationshipRecord(
                        source_id=memory_id,
                        target_id=parent_memory.id,
                        relation_type=RelationType.ELABORATES,
                        strength=0.7,
                        metadata={"detection_method": "namespace_hierarchy", "auto_detected": True},
                        created_at=datetime.now(timezone.utc)
                    )
                    detected.append(rel)
        
        return detected
    
    def xǁRelationshipManagerǁauto_detect_relationships__mutmut_6(
        self,
        memory_id: int,
        storage: MemoryStorage,
        similarity_threshold: float = 0.85
    ) -> List[RelationshipRecord]:
        """
        Auto-detect relationships for a memory.
        
        This method is a placeholder - actual auto-detection requires
        MemoryManager for similarity search. Will be implemented in
        MemoryManager integration.
        
        Args:
            memory_id: ID of memory to detect relationships for
            storage: MemoryStorage instance (for namespace queries)
            similarity_threshold: Minimum similarity for SIMILAR_TO (default: 0.85)
            
        Returns:
            List of detected RelationshipRecord objects
        """
        detected: List[RelationshipRecord] = []
        
        memory = storage.get_memory(memory_id)
        if not memory:
            return detected
        
        # Detect namespace hierarchy relationships
        if "XX.XX" in memory.namespace:
            parent_ns = memory.namespace.rsplit(".", 1)[0]
            parent_memories = storage.search_by_namespace(parent_ns, exact=True, limit=10)
            
            for parent_memory in parent_memories:
                if parent_memory.id and parent_memory.id != memory_id:
                    # Child namespace elaborates parent
                    rel = RelationshipRecord(
                        source_id=memory_id,
                        target_id=parent_memory.id,
                        relation_type=RelationType.ELABORATES,
                        strength=0.7,
                        metadata={"detection_method": "namespace_hierarchy", "auto_detected": True},
                        created_at=datetime.now(timezone.utc)
                    )
                    detected.append(rel)
        
        return detected
    
    def xǁRelationshipManagerǁauto_detect_relationships__mutmut_7(
        self,
        memory_id: int,
        storage: MemoryStorage,
        similarity_threshold: float = 0.85
    ) -> List[RelationshipRecord]:
        """
        Auto-detect relationships for a memory.
        
        This method is a placeholder - actual auto-detection requires
        MemoryManager for similarity search. Will be implemented in
        MemoryManager integration.
        
        Args:
            memory_id: ID of memory to detect relationships for
            storage: MemoryStorage instance (for namespace queries)
            similarity_threshold: Minimum similarity for SIMILAR_TO (default: 0.85)
            
        Returns:
            List of detected RelationshipRecord objects
        """
        detected: List[RelationshipRecord] = []
        
        memory = storage.get_memory(memory_id)
        if not memory:
            return detected
        
        # Detect namespace hierarchy relationships
        if "." not in memory.namespace:
            parent_ns = memory.namespace.rsplit(".", 1)[0]
            parent_memories = storage.search_by_namespace(parent_ns, exact=True, limit=10)
            
            for parent_memory in parent_memories:
                if parent_memory.id and parent_memory.id != memory_id:
                    # Child namespace elaborates parent
                    rel = RelationshipRecord(
                        source_id=memory_id,
                        target_id=parent_memory.id,
                        relation_type=RelationType.ELABORATES,
                        strength=0.7,
                        metadata={"detection_method": "namespace_hierarchy", "auto_detected": True},
                        created_at=datetime.now(timezone.utc)
                    )
                    detected.append(rel)
        
        return detected
    
    def xǁRelationshipManagerǁauto_detect_relationships__mutmut_8(
        self,
        memory_id: int,
        storage: MemoryStorage,
        similarity_threshold: float = 0.85
    ) -> List[RelationshipRecord]:
        """
        Auto-detect relationships for a memory.
        
        This method is a placeholder - actual auto-detection requires
        MemoryManager for similarity search. Will be implemented in
        MemoryManager integration.
        
        Args:
            memory_id: ID of memory to detect relationships for
            storage: MemoryStorage instance (for namespace queries)
            similarity_threshold: Minimum similarity for SIMILAR_TO (default: 0.85)
            
        Returns:
            List of detected RelationshipRecord objects
        """
        detected: List[RelationshipRecord] = []
        
        memory = storage.get_memory(memory_id)
        if not memory:
            return detected
        
        # Detect namespace hierarchy relationships
        if "." in memory.namespace:
            parent_ns = None
            parent_memories = storage.search_by_namespace(parent_ns, exact=True, limit=10)
            
            for parent_memory in parent_memories:
                if parent_memory.id and parent_memory.id != memory_id:
                    # Child namespace elaborates parent
                    rel = RelationshipRecord(
                        source_id=memory_id,
                        target_id=parent_memory.id,
                        relation_type=RelationType.ELABORATES,
                        strength=0.7,
                        metadata={"detection_method": "namespace_hierarchy", "auto_detected": True},
                        created_at=datetime.now(timezone.utc)
                    )
                    detected.append(rel)
        
        return detected
    
    def xǁRelationshipManagerǁauto_detect_relationships__mutmut_9(
        self,
        memory_id: int,
        storage: MemoryStorage,
        similarity_threshold: float = 0.85
    ) -> List[RelationshipRecord]:
        """
        Auto-detect relationships for a memory.
        
        This method is a placeholder - actual auto-detection requires
        MemoryManager for similarity search. Will be implemented in
        MemoryManager integration.
        
        Args:
            memory_id: ID of memory to detect relationships for
            storage: MemoryStorage instance (for namespace queries)
            similarity_threshold: Minimum similarity for SIMILAR_TO (default: 0.85)
            
        Returns:
            List of detected RelationshipRecord objects
        """
        detected: List[RelationshipRecord] = []
        
        memory = storage.get_memory(memory_id)
        if not memory:
            return detected
        
        # Detect namespace hierarchy relationships
        if "." in memory.namespace:
            parent_ns = memory.namespace.rsplit(None, 1)[0]
            parent_memories = storage.search_by_namespace(parent_ns, exact=True, limit=10)
            
            for parent_memory in parent_memories:
                if parent_memory.id and parent_memory.id != memory_id:
                    # Child namespace elaborates parent
                    rel = RelationshipRecord(
                        source_id=memory_id,
                        target_id=parent_memory.id,
                        relation_type=RelationType.ELABORATES,
                        strength=0.7,
                        metadata={"detection_method": "namespace_hierarchy", "auto_detected": True},
                        created_at=datetime.now(timezone.utc)
                    )
                    detected.append(rel)
        
        return detected
    
    def xǁRelationshipManagerǁauto_detect_relationships__mutmut_10(
        self,
        memory_id: int,
        storage: MemoryStorage,
        similarity_threshold: float = 0.85
    ) -> List[RelationshipRecord]:
        """
        Auto-detect relationships for a memory.
        
        This method is a placeholder - actual auto-detection requires
        MemoryManager for similarity search. Will be implemented in
        MemoryManager integration.
        
        Args:
            memory_id: ID of memory to detect relationships for
            storage: MemoryStorage instance (for namespace queries)
            similarity_threshold: Minimum similarity for SIMILAR_TO (default: 0.85)
            
        Returns:
            List of detected RelationshipRecord objects
        """
        detected: List[RelationshipRecord] = []
        
        memory = storage.get_memory(memory_id)
        if not memory:
            return detected
        
        # Detect namespace hierarchy relationships
        if "." in memory.namespace:
            parent_ns = memory.namespace.rsplit(".", None)[0]
            parent_memories = storage.search_by_namespace(parent_ns, exact=True, limit=10)
            
            for parent_memory in parent_memories:
                if parent_memory.id and parent_memory.id != memory_id:
                    # Child namespace elaborates parent
                    rel = RelationshipRecord(
                        source_id=memory_id,
                        target_id=parent_memory.id,
                        relation_type=RelationType.ELABORATES,
                        strength=0.7,
                        metadata={"detection_method": "namespace_hierarchy", "auto_detected": True},
                        created_at=datetime.now(timezone.utc)
                    )
                    detected.append(rel)
        
        return detected
    
    def xǁRelationshipManagerǁauto_detect_relationships__mutmut_11(
        self,
        memory_id: int,
        storage: MemoryStorage,
        similarity_threshold: float = 0.85
    ) -> List[RelationshipRecord]:
        """
        Auto-detect relationships for a memory.
        
        This method is a placeholder - actual auto-detection requires
        MemoryManager for similarity search. Will be implemented in
        MemoryManager integration.
        
        Args:
            memory_id: ID of memory to detect relationships for
            storage: MemoryStorage instance (for namespace queries)
            similarity_threshold: Minimum similarity for SIMILAR_TO (default: 0.85)
            
        Returns:
            List of detected RelationshipRecord objects
        """
        detected: List[RelationshipRecord] = []
        
        memory = storage.get_memory(memory_id)
        if not memory:
            return detected
        
        # Detect namespace hierarchy relationships
        if "." in memory.namespace:
            parent_ns = memory.namespace.rsplit(1)[0]
            parent_memories = storage.search_by_namespace(parent_ns, exact=True, limit=10)
            
            for parent_memory in parent_memories:
                if parent_memory.id and parent_memory.id != memory_id:
                    # Child namespace elaborates parent
                    rel = RelationshipRecord(
                        source_id=memory_id,
                        target_id=parent_memory.id,
                        relation_type=RelationType.ELABORATES,
                        strength=0.7,
                        metadata={"detection_method": "namespace_hierarchy", "auto_detected": True},
                        created_at=datetime.now(timezone.utc)
                    )
                    detected.append(rel)
        
        return detected
    
    def xǁRelationshipManagerǁauto_detect_relationships__mutmut_12(
        self,
        memory_id: int,
        storage: MemoryStorage,
        similarity_threshold: float = 0.85
    ) -> List[RelationshipRecord]:
        """
        Auto-detect relationships for a memory.
        
        This method is a placeholder - actual auto-detection requires
        MemoryManager for similarity search. Will be implemented in
        MemoryManager integration.
        
        Args:
            memory_id: ID of memory to detect relationships for
            storage: MemoryStorage instance (for namespace queries)
            similarity_threshold: Minimum similarity for SIMILAR_TO (default: 0.85)
            
        Returns:
            List of detected RelationshipRecord objects
        """
        detected: List[RelationshipRecord] = []
        
        memory = storage.get_memory(memory_id)
        if not memory:
            return detected
        
        # Detect namespace hierarchy relationships
        if "." in memory.namespace:
            parent_ns = memory.namespace.rsplit(".", )[0]
            parent_memories = storage.search_by_namespace(parent_ns, exact=True, limit=10)
            
            for parent_memory in parent_memories:
                if parent_memory.id and parent_memory.id != memory_id:
                    # Child namespace elaborates parent
                    rel = RelationshipRecord(
                        source_id=memory_id,
                        target_id=parent_memory.id,
                        relation_type=RelationType.ELABORATES,
                        strength=0.7,
                        metadata={"detection_method": "namespace_hierarchy", "auto_detected": True},
                        created_at=datetime.now(timezone.utc)
                    )
                    detected.append(rel)
        
        return detected
    
    def xǁRelationshipManagerǁauto_detect_relationships__mutmut_13(
        self,
        memory_id: int,
        storage: MemoryStorage,
        similarity_threshold: float = 0.85
    ) -> List[RelationshipRecord]:
        """
        Auto-detect relationships for a memory.
        
        This method is a placeholder - actual auto-detection requires
        MemoryManager for similarity search. Will be implemented in
        MemoryManager integration.
        
        Args:
            memory_id: ID of memory to detect relationships for
            storage: MemoryStorage instance (for namespace queries)
            similarity_threshold: Minimum similarity for SIMILAR_TO (default: 0.85)
            
        Returns:
            List of detected RelationshipRecord objects
        """
        detected: List[RelationshipRecord] = []
        
        memory = storage.get_memory(memory_id)
        if not memory:
            return detected
        
        # Detect namespace hierarchy relationships
        if "." in memory.namespace:
            parent_ns = memory.namespace.split(".", 1)[0]
            parent_memories = storage.search_by_namespace(parent_ns, exact=True, limit=10)
            
            for parent_memory in parent_memories:
                if parent_memory.id and parent_memory.id != memory_id:
                    # Child namespace elaborates parent
                    rel = RelationshipRecord(
                        source_id=memory_id,
                        target_id=parent_memory.id,
                        relation_type=RelationType.ELABORATES,
                        strength=0.7,
                        metadata={"detection_method": "namespace_hierarchy", "auto_detected": True},
                        created_at=datetime.now(timezone.utc)
                    )
                    detected.append(rel)
        
        return detected
    
    def xǁRelationshipManagerǁauto_detect_relationships__mutmut_14(
        self,
        memory_id: int,
        storage: MemoryStorage,
        similarity_threshold: float = 0.85
    ) -> List[RelationshipRecord]:
        """
        Auto-detect relationships for a memory.
        
        This method is a placeholder - actual auto-detection requires
        MemoryManager for similarity search. Will be implemented in
        MemoryManager integration.
        
        Args:
            memory_id: ID of memory to detect relationships for
            storage: MemoryStorage instance (for namespace queries)
            similarity_threshold: Minimum similarity for SIMILAR_TO (default: 0.85)
            
        Returns:
            List of detected RelationshipRecord objects
        """
        detected: List[RelationshipRecord] = []
        
        memory = storage.get_memory(memory_id)
        if not memory:
            return detected
        
        # Detect namespace hierarchy relationships
        if "." in memory.namespace:
            parent_ns = memory.namespace.rsplit("XX.XX", 1)[0]
            parent_memories = storage.search_by_namespace(parent_ns, exact=True, limit=10)
            
            for parent_memory in parent_memories:
                if parent_memory.id and parent_memory.id != memory_id:
                    # Child namespace elaborates parent
                    rel = RelationshipRecord(
                        source_id=memory_id,
                        target_id=parent_memory.id,
                        relation_type=RelationType.ELABORATES,
                        strength=0.7,
                        metadata={"detection_method": "namespace_hierarchy", "auto_detected": True},
                        created_at=datetime.now(timezone.utc)
                    )
                    detected.append(rel)
        
        return detected
    
    def xǁRelationshipManagerǁauto_detect_relationships__mutmut_15(
        self,
        memory_id: int,
        storage: MemoryStorage,
        similarity_threshold: float = 0.85
    ) -> List[RelationshipRecord]:
        """
        Auto-detect relationships for a memory.
        
        This method is a placeholder - actual auto-detection requires
        MemoryManager for similarity search. Will be implemented in
        MemoryManager integration.
        
        Args:
            memory_id: ID of memory to detect relationships for
            storage: MemoryStorage instance (for namespace queries)
            similarity_threshold: Minimum similarity for SIMILAR_TO (default: 0.85)
            
        Returns:
            List of detected RelationshipRecord objects
        """
        detected: List[RelationshipRecord] = []
        
        memory = storage.get_memory(memory_id)
        if not memory:
            return detected
        
        # Detect namespace hierarchy relationships
        if "." in memory.namespace:
            parent_ns = memory.namespace.rsplit(".", 2)[0]
            parent_memories = storage.search_by_namespace(parent_ns, exact=True, limit=10)
            
            for parent_memory in parent_memories:
                if parent_memory.id and parent_memory.id != memory_id:
                    # Child namespace elaborates parent
                    rel = RelationshipRecord(
                        source_id=memory_id,
                        target_id=parent_memory.id,
                        relation_type=RelationType.ELABORATES,
                        strength=0.7,
                        metadata={"detection_method": "namespace_hierarchy", "auto_detected": True},
                        created_at=datetime.now(timezone.utc)
                    )
                    detected.append(rel)
        
        return detected
    
    def xǁRelationshipManagerǁauto_detect_relationships__mutmut_16(
        self,
        memory_id: int,
        storage: MemoryStorage,
        similarity_threshold: float = 0.85
    ) -> List[RelationshipRecord]:
        """
        Auto-detect relationships for a memory.
        
        This method is a placeholder - actual auto-detection requires
        MemoryManager for similarity search. Will be implemented in
        MemoryManager integration.
        
        Args:
            memory_id: ID of memory to detect relationships for
            storage: MemoryStorage instance (for namespace queries)
            similarity_threshold: Minimum similarity for SIMILAR_TO (default: 0.85)
            
        Returns:
            List of detected RelationshipRecord objects
        """
        detected: List[RelationshipRecord] = []
        
        memory = storage.get_memory(memory_id)
        if not memory:
            return detected
        
        # Detect namespace hierarchy relationships
        if "." in memory.namespace:
            parent_ns = memory.namespace.rsplit(".", 1)[1]
            parent_memories = storage.search_by_namespace(parent_ns, exact=True, limit=10)
            
            for parent_memory in parent_memories:
                if parent_memory.id and parent_memory.id != memory_id:
                    # Child namespace elaborates parent
                    rel = RelationshipRecord(
                        source_id=memory_id,
                        target_id=parent_memory.id,
                        relation_type=RelationType.ELABORATES,
                        strength=0.7,
                        metadata={"detection_method": "namespace_hierarchy", "auto_detected": True},
                        created_at=datetime.now(timezone.utc)
                    )
                    detected.append(rel)
        
        return detected
    
    def xǁRelationshipManagerǁauto_detect_relationships__mutmut_17(
        self,
        memory_id: int,
        storage: MemoryStorage,
        similarity_threshold: float = 0.85
    ) -> List[RelationshipRecord]:
        """
        Auto-detect relationships for a memory.
        
        This method is a placeholder - actual auto-detection requires
        MemoryManager for similarity search. Will be implemented in
        MemoryManager integration.
        
        Args:
            memory_id: ID of memory to detect relationships for
            storage: MemoryStorage instance (for namespace queries)
            similarity_threshold: Minimum similarity for SIMILAR_TO (default: 0.85)
            
        Returns:
            List of detected RelationshipRecord objects
        """
        detected: List[RelationshipRecord] = []
        
        memory = storage.get_memory(memory_id)
        if not memory:
            return detected
        
        # Detect namespace hierarchy relationships
        if "." in memory.namespace:
            parent_ns = memory.namespace.rsplit(".", 1)[0]
            parent_memories = None
            
            for parent_memory in parent_memories:
                if parent_memory.id and parent_memory.id != memory_id:
                    # Child namespace elaborates parent
                    rel = RelationshipRecord(
                        source_id=memory_id,
                        target_id=parent_memory.id,
                        relation_type=RelationType.ELABORATES,
                        strength=0.7,
                        metadata={"detection_method": "namespace_hierarchy", "auto_detected": True},
                        created_at=datetime.now(timezone.utc)
                    )
                    detected.append(rel)
        
        return detected
    
    def xǁRelationshipManagerǁauto_detect_relationships__mutmut_18(
        self,
        memory_id: int,
        storage: MemoryStorage,
        similarity_threshold: float = 0.85
    ) -> List[RelationshipRecord]:
        """
        Auto-detect relationships for a memory.
        
        This method is a placeholder - actual auto-detection requires
        MemoryManager for similarity search. Will be implemented in
        MemoryManager integration.
        
        Args:
            memory_id: ID of memory to detect relationships for
            storage: MemoryStorage instance (for namespace queries)
            similarity_threshold: Minimum similarity for SIMILAR_TO (default: 0.85)
            
        Returns:
            List of detected RelationshipRecord objects
        """
        detected: List[RelationshipRecord] = []
        
        memory = storage.get_memory(memory_id)
        if not memory:
            return detected
        
        # Detect namespace hierarchy relationships
        if "." in memory.namespace:
            parent_ns = memory.namespace.rsplit(".", 1)[0]
            parent_memories = storage.search_by_namespace(None, exact=True, limit=10)
            
            for parent_memory in parent_memories:
                if parent_memory.id and parent_memory.id != memory_id:
                    # Child namespace elaborates parent
                    rel = RelationshipRecord(
                        source_id=memory_id,
                        target_id=parent_memory.id,
                        relation_type=RelationType.ELABORATES,
                        strength=0.7,
                        metadata={"detection_method": "namespace_hierarchy", "auto_detected": True},
                        created_at=datetime.now(timezone.utc)
                    )
                    detected.append(rel)
        
        return detected
    
    def xǁRelationshipManagerǁauto_detect_relationships__mutmut_19(
        self,
        memory_id: int,
        storage: MemoryStorage,
        similarity_threshold: float = 0.85
    ) -> List[RelationshipRecord]:
        """
        Auto-detect relationships for a memory.
        
        This method is a placeholder - actual auto-detection requires
        MemoryManager for similarity search. Will be implemented in
        MemoryManager integration.
        
        Args:
            memory_id: ID of memory to detect relationships for
            storage: MemoryStorage instance (for namespace queries)
            similarity_threshold: Minimum similarity for SIMILAR_TO (default: 0.85)
            
        Returns:
            List of detected RelationshipRecord objects
        """
        detected: List[RelationshipRecord] = []
        
        memory = storage.get_memory(memory_id)
        if not memory:
            return detected
        
        # Detect namespace hierarchy relationships
        if "." in memory.namespace:
            parent_ns = memory.namespace.rsplit(".", 1)[0]
            parent_memories = storage.search_by_namespace(parent_ns, exact=None, limit=10)
            
            for parent_memory in parent_memories:
                if parent_memory.id and parent_memory.id != memory_id:
                    # Child namespace elaborates parent
                    rel = RelationshipRecord(
                        source_id=memory_id,
                        target_id=parent_memory.id,
                        relation_type=RelationType.ELABORATES,
                        strength=0.7,
                        metadata={"detection_method": "namespace_hierarchy", "auto_detected": True},
                        created_at=datetime.now(timezone.utc)
                    )
                    detected.append(rel)
        
        return detected
    
    def xǁRelationshipManagerǁauto_detect_relationships__mutmut_20(
        self,
        memory_id: int,
        storage: MemoryStorage,
        similarity_threshold: float = 0.85
    ) -> List[RelationshipRecord]:
        """
        Auto-detect relationships for a memory.
        
        This method is a placeholder - actual auto-detection requires
        MemoryManager for similarity search. Will be implemented in
        MemoryManager integration.
        
        Args:
            memory_id: ID of memory to detect relationships for
            storage: MemoryStorage instance (for namespace queries)
            similarity_threshold: Minimum similarity for SIMILAR_TO (default: 0.85)
            
        Returns:
            List of detected RelationshipRecord objects
        """
        detected: List[RelationshipRecord] = []
        
        memory = storage.get_memory(memory_id)
        if not memory:
            return detected
        
        # Detect namespace hierarchy relationships
        if "." in memory.namespace:
            parent_ns = memory.namespace.rsplit(".", 1)[0]
            parent_memories = storage.search_by_namespace(parent_ns, exact=True, limit=None)
            
            for parent_memory in parent_memories:
                if parent_memory.id and parent_memory.id != memory_id:
                    # Child namespace elaborates parent
                    rel = RelationshipRecord(
                        source_id=memory_id,
                        target_id=parent_memory.id,
                        relation_type=RelationType.ELABORATES,
                        strength=0.7,
                        metadata={"detection_method": "namespace_hierarchy", "auto_detected": True},
                        created_at=datetime.now(timezone.utc)
                    )
                    detected.append(rel)
        
        return detected
    
    def xǁRelationshipManagerǁauto_detect_relationships__mutmut_21(
        self,
        memory_id: int,
        storage: MemoryStorage,
        similarity_threshold: float = 0.85
    ) -> List[RelationshipRecord]:
        """
        Auto-detect relationships for a memory.
        
        This method is a placeholder - actual auto-detection requires
        MemoryManager for similarity search. Will be implemented in
        MemoryManager integration.
        
        Args:
            memory_id: ID of memory to detect relationships for
            storage: MemoryStorage instance (for namespace queries)
            similarity_threshold: Minimum similarity for SIMILAR_TO (default: 0.85)
            
        Returns:
            List of detected RelationshipRecord objects
        """
        detected: List[RelationshipRecord] = []
        
        memory = storage.get_memory(memory_id)
        if not memory:
            return detected
        
        # Detect namespace hierarchy relationships
        if "." in memory.namespace:
            parent_ns = memory.namespace.rsplit(".", 1)[0]
            parent_memories = storage.search_by_namespace(exact=True, limit=10)
            
            for parent_memory in parent_memories:
                if parent_memory.id and parent_memory.id != memory_id:
                    # Child namespace elaborates parent
                    rel = RelationshipRecord(
                        source_id=memory_id,
                        target_id=parent_memory.id,
                        relation_type=RelationType.ELABORATES,
                        strength=0.7,
                        metadata={"detection_method": "namespace_hierarchy", "auto_detected": True},
                        created_at=datetime.now(timezone.utc)
                    )
                    detected.append(rel)
        
        return detected
    
    def xǁRelationshipManagerǁauto_detect_relationships__mutmut_22(
        self,
        memory_id: int,
        storage: MemoryStorage,
        similarity_threshold: float = 0.85
    ) -> List[RelationshipRecord]:
        """
        Auto-detect relationships for a memory.
        
        This method is a placeholder - actual auto-detection requires
        MemoryManager for similarity search. Will be implemented in
        MemoryManager integration.
        
        Args:
            memory_id: ID of memory to detect relationships for
            storage: MemoryStorage instance (for namespace queries)
            similarity_threshold: Minimum similarity for SIMILAR_TO (default: 0.85)
            
        Returns:
            List of detected RelationshipRecord objects
        """
        detected: List[RelationshipRecord] = []
        
        memory = storage.get_memory(memory_id)
        if not memory:
            return detected
        
        # Detect namespace hierarchy relationships
        if "." in memory.namespace:
            parent_ns = memory.namespace.rsplit(".", 1)[0]
            parent_memories = storage.search_by_namespace(parent_ns, limit=10)
            
            for parent_memory in parent_memories:
                if parent_memory.id and parent_memory.id != memory_id:
                    # Child namespace elaborates parent
                    rel = RelationshipRecord(
                        source_id=memory_id,
                        target_id=parent_memory.id,
                        relation_type=RelationType.ELABORATES,
                        strength=0.7,
                        metadata={"detection_method": "namespace_hierarchy", "auto_detected": True},
                        created_at=datetime.now(timezone.utc)
                    )
                    detected.append(rel)
        
        return detected
    
    def xǁRelationshipManagerǁauto_detect_relationships__mutmut_23(
        self,
        memory_id: int,
        storage: MemoryStorage,
        similarity_threshold: float = 0.85
    ) -> List[RelationshipRecord]:
        """
        Auto-detect relationships for a memory.
        
        This method is a placeholder - actual auto-detection requires
        MemoryManager for similarity search. Will be implemented in
        MemoryManager integration.
        
        Args:
            memory_id: ID of memory to detect relationships for
            storage: MemoryStorage instance (for namespace queries)
            similarity_threshold: Minimum similarity for SIMILAR_TO (default: 0.85)
            
        Returns:
            List of detected RelationshipRecord objects
        """
        detected: List[RelationshipRecord] = []
        
        memory = storage.get_memory(memory_id)
        if not memory:
            return detected
        
        # Detect namespace hierarchy relationships
        if "." in memory.namespace:
            parent_ns = memory.namespace.rsplit(".", 1)[0]
            parent_memories = storage.search_by_namespace(parent_ns, exact=True, )
            
            for parent_memory in parent_memories:
                if parent_memory.id and parent_memory.id != memory_id:
                    # Child namespace elaborates parent
                    rel = RelationshipRecord(
                        source_id=memory_id,
                        target_id=parent_memory.id,
                        relation_type=RelationType.ELABORATES,
                        strength=0.7,
                        metadata={"detection_method": "namespace_hierarchy", "auto_detected": True},
                        created_at=datetime.now(timezone.utc)
                    )
                    detected.append(rel)
        
        return detected
    
    def xǁRelationshipManagerǁauto_detect_relationships__mutmut_24(
        self,
        memory_id: int,
        storage: MemoryStorage,
        similarity_threshold: float = 0.85
    ) -> List[RelationshipRecord]:
        """
        Auto-detect relationships for a memory.
        
        This method is a placeholder - actual auto-detection requires
        MemoryManager for similarity search. Will be implemented in
        MemoryManager integration.
        
        Args:
            memory_id: ID of memory to detect relationships for
            storage: MemoryStorage instance (for namespace queries)
            similarity_threshold: Minimum similarity for SIMILAR_TO (default: 0.85)
            
        Returns:
            List of detected RelationshipRecord objects
        """
        detected: List[RelationshipRecord] = []
        
        memory = storage.get_memory(memory_id)
        if not memory:
            return detected
        
        # Detect namespace hierarchy relationships
        if "." in memory.namespace:
            parent_ns = memory.namespace.rsplit(".", 1)[0]
            parent_memories = storage.search_by_namespace(parent_ns, exact=False, limit=10)
            
            for parent_memory in parent_memories:
                if parent_memory.id and parent_memory.id != memory_id:
                    # Child namespace elaborates parent
                    rel = RelationshipRecord(
                        source_id=memory_id,
                        target_id=parent_memory.id,
                        relation_type=RelationType.ELABORATES,
                        strength=0.7,
                        metadata={"detection_method": "namespace_hierarchy", "auto_detected": True},
                        created_at=datetime.now(timezone.utc)
                    )
                    detected.append(rel)
        
        return detected
    
    def xǁRelationshipManagerǁauto_detect_relationships__mutmut_25(
        self,
        memory_id: int,
        storage: MemoryStorage,
        similarity_threshold: float = 0.85
    ) -> List[RelationshipRecord]:
        """
        Auto-detect relationships for a memory.
        
        This method is a placeholder - actual auto-detection requires
        MemoryManager for similarity search. Will be implemented in
        MemoryManager integration.
        
        Args:
            memory_id: ID of memory to detect relationships for
            storage: MemoryStorage instance (for namespace queries)
            similarity_threshold: Minimum similarity for SIMILAR_TO (default: 0.85)
            
        Returns:
            List of detected RelationshipRecord objects
        """
        detected: List[RelationshipRecord] = []
        
        memory = storage.get_memory(memory_id)
        if not memory:
            return detected
        
        # Detect namespace hierarchy relationships
        if "." in memory.namespace:
            parent_ns = memory.namespace.rsplit(".", 1)[0]
            parent_memories = storage.search_by_namespace(parent_ns, exact=True, limit=11)
            
            for parent_memory in parent_memories:
                if parent_memory.id and parent_memory.id != memory_id:
                    # Child namespace elaborates parent
                    rel = RelationshipRecord(
                        source_id=memory_id,
                        target_id=parent_memory.id,
                        relation_type=RelationType.ELABORATES,
                        strength=0.7,
                        metadata={"detection_method": "namespace_hierarchy", "auto_detected": True},
                        created_at=datetime.now(timezone.utc)
                    )
                    detected.append(rel)
        
        return detected
    
    def xǁRelationshipManagerǁauto_detect_relationships__mutmut_26(
        self,
        memory_id: int,
        storage: MemoryStorage,
        similarity_threshold: float = 0.85
    ) -> List[RelationshipRecord]:
        """
        Auto-detect relationships for a memory.
        
        This method is a placeholder - actual auto-detection requires
        MemoryManager for similarity search. Will be implemented in
        MemoryManager integration.
        
        Args:
            memory_id: ID of memory to detect relationships for
            storage: MemoryStorage instance (for namespace queries)
            similarity_threshold: Minimum similarity for SIMILAR_TO (default: 0.85)
            
        Returns:
            List of detected RelationshipRecord objects
        """
        detected: List[RelationshipRecord] = []
        
        memory = storage.get_memory(memory_id)
        if not memory:
            return detected
        
        # Detect namespace hierarchy relationships
        if "." in memory.namespace:
            parent_ns = memory.namespace.rsplit(".", 1)[0]
            parent_memories = storage.search_by_namespace(parent_ns, exact=True, limit=10)
            
            for parent_memory in parent_memories:
                if parent_memory.id or parent_memory.id != memory_id:
                    # Child namespace elaborates parent
                    rel = RelationshipRecord(
                        source_id=memory_id,
                        target_id=parent_memory.id,
                        relation_type=RelationType.ELABORATES,
                        strength=0.7,
                        metadata={"detection_method": "namespace_hierarchy", "auto_detected": True},
                        created_at=datetime.now(timezone.utc)
                    )
                    detected.append(rel)
        
        return detected
    
    def xǁRelationshipManagerǁauto_detect_relationships__mutmut_27(
        self,
        memory_id: int,
        storage: MemoryStorage,
        similarity_threshold: float = 0.85
    ) -> List[RelationshipRecord]:
        """
        Auto-detect relationships for a memory.
        
        This method is a placeholder - actual auto-detection requires
        MemoryManager for similarity search. Will be implemented in
        MemoryManager integration.
        
        Args:
            memory_id: ID of memory to detect relationships for
            storage: MemoryStorage instance (for namespace queries)
            similarity_threshold: Minimum similarity for SIMILAR_TO (default: 0.85)
            
        Returns:
            List of detected RelationshipRecord objects
        """
        detected: List[RelationshipRecord] = []
        
        memory = storage.get_memory(memory_id)
        if not memory:
            return detected
        
        # Detect namespace hierarchy relationships
        if "." in memory.namespace:
            parent_ns = memory.namespace.rsplit(".", 1)[0]
            parent_memories = storage.search_by_namespace(parent_ns, exact=True, limit=10)
            
            for parent_memory in parent_memories:
                if parent_memory.id and parent_memory.id == memory_id:
                    # Child namespace elaborates parent
                    rel = RelationshipRecord(
                        source_id=memory_id,
                        target_id=parent_memory.id,
                        relation_type=RelationType.ELABORATES,
                        strength=0.7,
                        metadata={"detection_method": "namespace_hierarchy", "auto_detected": True},
                        created_at=datetime.now(timezone.utc)
                    )
                    detected.append(rel)
        
        return detected
    
    def xǁRelationshipManagerǁauto_detect_relationships__mutmut_28(
        self,
        memory_id: int,
        storage: MemoryStorage,
        similarity_threshold: float = 0.85
    ) -> List[RelationshipRecord]:
        """
        Auto-detect relationships for a memory.
        
        This method is a placeholder - actual auto-detection requires
        MemoryManager for similarity search. Will be implemented in
        MemoryManager integration.
        
        Args:
            memory_id: ID of memory to detect relationships for
            storage: MemoryStorage instance (for namespace queries)
            similarity_threshold: Minimum similarity for SIMILAR_TO (default: 0.85)
            
        Returns:
            List of detected RelationshipRecord objects
        """
        detected: List[RelationshipRecord] = []
        
        memory = storage.get_memory(memory_id)
        if not memory:
            return detected
        
        # Detect namespace hierarchy relationships
        if "." in memory.namespace:
            parent_ns = memory.namespace.rsplit(".", 1)[0]
            parent_memories = storage.search_by_namespace(parent_ns, exact=True, limit=10)
            
            for parent_memory in parent_memories:
                if parent_memory.id and parent_memory.id != memory_id:
                    # Child namespace elaborates parent
                    rel = None
                    detected.append(rel)
        
        return detected
    
    def xǁRelationshipManagerǁauto_detect_relationships__mutmut_29(
        self,
        memory_id: int,
        storage: MemoryStorage,
        similarity_threshold: float = 0.85
    ) -> List[RelationshipRecord]:
        """
        Auto-detect relationships for a memory.
        
        This method is a placeholder - actual auto-detection requires
        MemoryManager for similarity search. Will be implemented in
        MemoryManager integration.
        
        Args:
            memory_id: ID of memory to detect relationships for
            storage: MemoryStorage instance (for namespace queries)
            similarity_threshold: Minimum similarity for SIMILAR_TO (default: 0.85)
            
        Returns:
            List of detected RelationshipRecord objects
        """
        detected: List[RelationshipRecord] = []
        
        memory = storage.get_memory(memory_id)
        if not memory:
            return detected
        
        # Detect namespace hierarchy relationships
        if "." in memory.namespace:
            parent_ns = memory.namespace.rsplit(".", 1)[0]
            parent_memories = storage.search_by_namespace(parent_ns, exact=True, limit=10)
            
            for parent_memory in parent_memories:
                if parent_memory.id and parent_memory.id != memory_id:
                    # Child namespace elaborates parent
                    rel = RelationshipRecord(
                        source_id=None,
                        target_id=parent_memory.id,
                        relation_type=RelationType.ELABORATES,
                        strength=0.7,
                        metadata={"detection_method": "namespace_hierarchy", "auto_detected": True},
                        created_at=datetime.now(timezone.utc)
                    )
                    detected.append(rel)
        
        return detected
    
    def xǁRelationshipManagerǁauto_detect_relationships__mutmut_30(
        self,
        memory_id: int,
        storage: MemoryStorage,
        similarity_threshold: float = 0.85
    ) -> List[RelationshipRecord]:
        """
        Auto-detect relationships for a memory.
        
        This method is a placeholder - actual auto-detection requires
        MemoryManager for similarity search. Will be implemented in
        MemoryManager integration.
        
        Args:
            memory_id: ID of memory to detect relationships for
            storage: MemoryStorage instance (for namespace queries)
            similarity_threshold: Minimum similarity for SIMILAR_TO (default: 0.85)
            
        Returns:
            List of detected RelationshipRecord objects
        """
        detected: List[RelationshipRecord] = []
        
        memory = storage.get_memory(memory_id)
        if not memory:
            return detected
        
        # Detect namespace hierarchy relationships
        if "." in memory.namespace:
            parent_ns = memory.namespace.rsplit(".", 1)[0]
            parent_memories = storage.search_by_namespace(parent_ns, exact=True, limit=10)
            
            for parent_memory in parent_memories:
                if parent_memory.id and parent_memory.id != memory_id:
                    # Child namespace elaborates parent
                    rel = RelationshipRecord(
                        source_id=memory_id,
                        target_id=None,
                        relation_type=RelationType.ELABORATES,
                        strength=0.7,
                        metadata={"detection_method": "namespace_hierarchy", "auto_detected": True},
                        created_at=datetime.now(timezone.utc)
                    )
                    detected.append(rel)
        
        return detected
    
    def xǁRelationshipManagerǁauto_detect_relationships__mutmut_31(
        self,
        memory_id: int,
        storage: MemoryStorage,
        similarity_threshold: float = 0.85
    ) -> List[RelationshipRecord]:
        """
        Auto-detect relationships for a memory.
        
        This method is a placeholder - actual auto-detection requires
        MemoryManager for similarity search. Will be implemented in
        MemoryManager integration.
        
        Args:
            memory_id: ID of memory to detect relationships for
            storage: MemoryStorage instance (for namespace queries)
            similarity_threshold: Minimum similarity for SIMILAR_TO (default: 0.85)
            
        Returns:
            List of detected RelationshipRecord objects
        """
        detected: List[RelationshipRecord] = []
        
        memory = storage.get_memory(memory_id)
        if not memory:
            return detected
        
        # Detect namespace hierarchy relationships
        if "." in memory.namespace:
            parent_ns = memory.namespace.rsplit(".", 1)[0]
            parent_memories = storage.search_by_namespace(parent_ns, exact=True, limit=10)
            
            for parent_memory in parent_memories:
                if parent_memory.id and parent_memory.id != memory_id:
                    # Child namespace elaborates parent
                    rel = RelationshipRecord(
                        source_id=memory_id,
                        target_id=parent_memory.id,
                        relation_type=None,
                        strength=0.7,
                        metadata={"detection_method": "namespace_hierarchy", "auto_detected": True},
                        created_at=datetime.now(timezone.utc)
                    )
                    detected.append(rel)
        
        return detected
    
    def xǁRelationshipManagerǁauto_detect_relationships__mutmut_32(
        self,
        memory_id: int,
        storage: MemoryStorage,
        similarity_threshold: float = 0.85
    ) -> List[RelationshipRecord]:
        """
        Auto-detect relationships for a memory.
        
        This method is a placeholder - actual auto-detection requires
        MemoryManager for similarity search. Will be implemented in
        MemoryManager integration.
        
        Args:
            memory_id: ID of memory to detect relationships for
            storage: MemoryStorage instance (for namespace queries)
            similarity_threshold: Minimum similarity for SIMILAR_TO (default: 0.85)
            
        Returns:
            List of detected RelationshipRecord objects
        """
        detected: List[RelationshipRecord] = []
        
        memory = storage.get_memory(memory_id)
        if not memory:
            return detected
        
        # Detect namespace hierarchy relationships
        if "." in memory.namespace:
            parent_ns = memory.namespace.rsplit(".", 1)[0]
            parent_memories = storage.search_by_namespace(parent_ns, exact=True, limit=10)
            
            for parent_memory in parent_memories:
                if parent_memory.id and parent_memory.id != memory_id:
                    # Child namespace elaborates parent
                    rel = RelationshipRecord(
                        source_id=memory_id,
                        target_id=parent_memory.id,
                        relation_type=RelationType.ELABORATES,
                        strength=None,
                        metadata={"detection_method": "namespace_hierarchy", "auto_detected": True},
                        created_at=datetime.now(timezone.utc)
                    )
                    detected.append(rel)
        
        return detected
    
    def xǁRelationshipManagerǁauto_detect_relationships__mutmut_33(
        self,
        memory_id: int,
        storage: MemoryStorage,
        similarity_threshold: float = 0.85
    ) -> List[RelationshipRecord]:
        """
        Auto-detect relationships for a memory.
        
        This method is a placeholder - actual auto-detection requires
        MemoryManager for similarity search. Will be implemented in
        MemoryManager integration.
        
        Args:
            memory_id: ID of memory to detect relationships for
            storage: MemoryStorage instance (for namespace queries)
            similarity_threshold: Minimum similarity for SIMILAR_TO (default: 0.85)
            
        Returns:
            List of detected RelationshipRecord objects
        """
        detected: List[RelationshipRecord] = []
        
        memory = storage.get_memory(memory_id)
        if not memory:
            return detected
        
        # Detect namespace hierarchy relationships
        if "." in memory.namespace:
            parent_ns = memory.namespace.rsplit(".", 1)[0]
            parent_memories = storage.search_by_namespace(parent_ns, exact=True, limit=10)
            
            for parent_memory in parent_memories:
                if parent_memory.id and parent_memory.id != memory_id:
                    # Child namespace elaborates parent
                    rel = RelationshipRecord(
                        source_id=memory_id,
                        target_id=parent_memory.id,
                        relation_type=RelationType.ELABORATES,
                        strength=0.7,
                        metadata=None,
                        created_at=datetime.now(timezone.utc)
                    )
                    detected.append(rel)
        
        return detected
    
    def xǁRelationshipManagerǁauto_detect_relationships__mutmut_34(
        self,
        memory_id: int,
        storage: MemoryStorage,
        similarity_threshold: float = 0.85
    ) -> List[RelationshipRecord]:
        """
        Auto-detect relationships for a memory.
        
        This method is a placeholder - actual auto-detection requires
        MemoryManager for similarity search. Will be implemented in
        MemoryManager integration.
        
        Args:
            memory_id: ID of memory to detect relationships for
            storage: MemoryStorage instance (for namespace queries)
            similarity_threshold: Minimum similarity for SIMILAR_TO (default: 0.85)
            
        Returns:
            List of detected RelationshipRecord objects
        """
        detected: List[RelationshipRecord] = []
        
        memory = storage.get_memory(memory_id)
        if not memory:
            return detected
        
        # Detect namespace hierarchy relationships
        if "." in memory.namespace:
            parent_ns = memory.namespace.rsplit(".", 1)[0]
            parent_memories = storage.search_by_namespace(parent_ns, exact=True, limit=10)
            
            for parent_memory in parent_memories:
                if parent_memory.id and parent_memory.id != memory_id:
                    # Child namespace elaborates parent
                    rel = RelationshipRecord(
                        source_id=memory_id,
                        target_id=parent_memory.id,
                        relation_type=RelationType.ELABORATES,
                        strength=0.7,
                        metadata={"detection_method": "namespace_hierarchy", "auto_detected": True},
                        created_at=None
                    )
                    detected.append(rel)
        
        return detected
    
    def xǁRelationshipManagerǁauto_detect_relationships__mutmut_35(
        self,
        memory_id: int,
        storage: MemoryStorage,
        similarity_threshold: float = 0.85
    ) -> List[RelationshipRecord]:
        """
        Auto-detect relationships for a memory.
        
        This method is a placeholder - actual auto-detection requires
        MemoryManager for similarity search. Will be implemented in
        MemoryManager integration.
        
        Args:
            memory_id: ID of memory to detect relationships for
            storage: MemoryStorage instance (for namespace queries)
            similarity_threshold: Minimum similarity for SIMILAR_TO (default: 0.85)
            
        Returns:
            List of detected RelationshipRecord objects
        """
        detected: List[RelationshipRecord] = []
        
        memory = storage.get_memory(memory_id)
        if not memory:
            return detected
        
        # Detect namespace hierarchy relationships
        if "." in memory.namespace:
            parent_ns = memory.namespace.rsplit(".", 1)[0]
            parent_memories = storage.search_by_namespace(parent_ns, exact=True, limit=10)
            
            for parent_memory in parent_memories:
                if parent_memory.id and parent_memory.id != memory_id:
                    # Child namespace elaborates parent
                    rel = RelationshipRecord(
                        target_id=parent_memory.id,
                        relation_type=RelationType.ELABORATES,
                        strength=0.7,
                        metadata={"detection_method": "namespace_hierarchy", "auto_detected": True},
                        created_at=datetime.now(timezone.utc)
                    )
                    detected.append(rel)
        
        return detected
    
    def xǁRelationshipManagerǁauto_detect_relationships__mutmut_36(
        self,
        memory_id: int,
        storage: MemoryStorage,
        similarity_threshold: float = 0.85
    ) -> List[RelationshipRecord]:
        """
        Auto-detect relationships for a memory.
        
        This method is a placeholder - actual auto-detection requires
        MemoryManager for similarity search. Will be implemented in
        MemoryManager integration.
        
        Args:
            memory_id: ID of memory to detect relationships for
            storage: MemoryStorage instance (for namespace queries)
            similarity_threshold: Minimum similarity for SIMILAR_TO (default: 0.85)
            
        Returns:
            List of detected RelationshipRecord objects
        """
        detected: List[RelationshipRecord] = []
        
        memory = storage.get_memory(memory_id)
        if not memory:
            return detected
        
        # Detect namespace hierarchy relationships
        if "." in memory.namespace:
            parent_ns = memory.namespace.rsplit(".", 1)[0]
            parent_memories = storage.search_by_namespace(parent_ns, exact=True, limit=10)
            
            for parent_memory in parent_memories:
                if parent_memory.id and parent_memory.id != memory_id:
                    # Child namespace elaborates parent
                    rel = RelationshipRecord(
                        source_id=memory_id,
                        relation_type=RelationType.ELABORATES,
                        strength=0.7,
                        metadata={"detection_method": "namespace_hierarchy", "auto_detected": True},
                        created_at=datetime.now(timezone.utc)
                    )
                    detected.append(rel)
        
        return detected
    
    def xǁRelationshipManagerǁauto_detect_relationships__mutmut_37(
        self,
        memory_id: int,
        storage: MemoryStorage,
        similarity_threshold: float = 0.85
    ) -> List[RelationshipRecord]:
        """
        Auto-detect relationships for a memory.
        
        This method is a placeholder - actual auto-detection requires
        MemoryManager for similarity search. Will be implemented in
        MemoryManager integration.
        
        Args:
            memory_id: ID of memory to detect relationships for
            storage: MemoryStorage instance (for namespace queries)
            similarity_threshold: Minimum similarity for SIMILAR_TO (default: 0.85)
            
        Returns:
            List of detected RelationshipRecord objects
        """
        detected: List[RelationshipRecord] = []
        
        memory = storage.get_memory(memory_id)
        if not memory:
            return detected
        
        # Detect namespace hierarchy relationships
        if "." in memory.namespace:
            parent_ns = memory.namespace.rsplit(".", 1)[0]
            parent_memories = storage.search_by_namespace(parent_ns, exact=True, limit=10)
            
            for parent_memory in parent_memories:
                if parent_memory.id and parent_memory.id != memory_id:
                    # Child namespace elaborates parent
                    rel = RelationshipRecord(
                        source_id=memory_id,
                        target_id=parent_memory.id,
                        strength=0.7,
                        metadata={"detection_method": "namespace_hierarchy", "auto_detected": True},
                        created_at=datetime.now(timezone.utc)
                    )
                    detected.append(rel)
        
        return detected
    
    def xǁRelationshipManagerǁauto_detect_relationships__mutmut_38(
        self,
        memory_id: int,
        storage: MemoryStorage,
        similarity_threshold: float = 0.85
    ) -> List[RelationshipRecord]:
        """
        Auto-detect relationships for a memory.
        
        This method is a placeholder - actual auto-detection requires
        MemoryManager for similarity search. Will be implemented in
        MemoryManager integration.
        
        Args:
            memory_id: ID of memory to detect relationships for
            storage: MemoryStorage instance (for namespace queries)
            similarity_threshold: Minimum similarity for SIMILAR_TO (default: 0.85)
            
        Returns:
            List of detected RelationshipRecord objects
        """
        detected: List[RelationshipRecord] = []
        
        memory = storage.get_memory(memory_id)
        if not memory:
            return detected
        
        # Detect namespace hierarchy relationships
        if "." in memory.namespace:
            parent_ns = memory.namespace.rsplit(".", 1)[0]
            parent_memories = storage.search_by_namespace(parent_ns, exact=True, limit=10)
            
            for parent_memory in parent_memories:
                if parent_memory.id and parent_memory.id != memory_id:
                    # Child namespace elaborates parent
                    rel = RelationshipRecord(
                        source_id=memory_id,
                        target_id=parent_memory.id,
                        relation_type=RelationType.ELABORATES,
                        metadata={"detection_method": "namespace_hierarchy", "auto_detected": True},
                        created_at=datetime.now(timezone.utc)
                    )
                    detected.append(rel)
        
        return detected
    
    def xǁRelationshipManagerǁauto_detect_relationships__mutmut_39(
        self,
        memory_id: int,
        storage: MemoryStorage,
        similarity_threshold: float = 0.85
    ) -> List[RelationshipRecord]:
        """
        Auto-detect relationships for a memory.
        
        This method is a placeholder - actual auto-detection requires
        MemoryManager for similarity search. Will be implemented in
        MemoryManager integration.
        
        Args:
            memory_id: ID of memory to detect relationships for
            storage: MemoryStorage instance (for namespace queries)
            similarity_threshold: Minimum similarity for SIMILAR_TO (default: 0.85)
            
        Returns:
            List of detected RelationshipRecord objects
        """
        detected: List[RelationshipRecord] = []
        
        memory = storage.get_memory(memory_id)
        if not memory:
            return detected
        
        # Detect namespace hierarchy relationships
        if "." in memory.namespace:
            parent_ns = memory.namespace.rsplit(".", 1)[0]
            parent_memories = storage.search_by_namespace(parent_ns, exact=True, limit=10)
            
            for parent_memory in parent_memories:
                if parent_memory.id and parent_memory.id != memory_id:
                    # Child namespace elaborates parent
                    rel = RelationshipRecord(
                        source_id=memory_id,
                        target_id=parent_memory.id,
                        relation_type=RelationType.ELABORATES,
                        strength=0.7,
                        created_at=datetime.now(timezone.utc)
                    )
                    detected.append(rel)
        
        return detected
    
    def xǁRelationshipManagerǁauto_detect_relationships__mutmut_40(
        self,
        memory_id: int,
        storage: MemoryStorage,
        similarity_threshold: float = 0.85
    ) -> List[RelationshipRecord]:
        """
        Auto-detect relationships for a memory.
        
        This method is a placeholder - actual auto-detection requires
        MemoryManager for similarity search. Will be implemented in
        MemoryManager integration.
        
        Args:
            memory_id: ID of memory to detect relationships for
            storage: MemoryStorage instance (for namespace queries)
            similarity_threshold: Minimum similarity for SIMILAR_TO (default: 0.85)
            
        Returns:
            List of detected RelationshipRecord objects
        """
        detected: List[RelationshipRecord] = []
        
        memory = storage.get_memory(memory_id)
        if not memory:
            return detected
        
        # Detect namespace hierarchy relationships
        if "." in memory.namespace:
            parent_ns = memory.namespace.rsplit(".", 1)[0]
            parent_memories = storage.search_by_namespace(parent_ns, exact=True, limit=10)
            
            for parent_memory in parent_memories:
                if parent_memory.id and parent_memory.id != memory_id:
                    # Child namespace elaborates parent
                    rel = RelationshipRecord(
                        source_id=memory_id,
                        target_id=parent_memory.id,
                        relation_type=RelationType.ELABORATES,
                        strength=0.7,
                        metadata={"detection_method": "namespace_hierarchy", "auto_detected": True},
                        )
                    detected.append(rel)
        
        return detected
    
    def xǁRelationshipManagerǁauto_detect_relationships__mutmut_41(
        self,
        memory_id: int,
        storage: MemoryStorage,
        similarity_threshold: float = 0.85
    ) -> List[RelationshipRecord]:
        """
        Auto-detect relationships for a memory.
        
        This method is a placeholder - actual auto-detection requires
        MemoryManager for similarity search. Will be implemented in
        MemoryManager integration.
        
        Args:
            memory_id: ID of memory to detect relationships for
            storage: MemoryStorage instance (for namespace queries)
            similarity_threshold: Minimum similarity for SIMILAR_TO (default: 0.85)
            
        Returns:
            List of detected RelationshipRecord objects
        """
        detected: List[RelationshipRecord] = []
        
        memory = storage.get_memory(memory_id)
        if not memory:
            return detected
        
        # Detect namespace hierarchy relationships
        if "." in memory.namespace:
            parent_ns = memory.namespace.rsplit(".", 1)[0]
            parent_memories = storage.search_by_namespace(parent_ns, exact=True, limit=10)
            
            for parent_memory in parent_memories:
                if parent_memory.id and parent_memory.id != memory_id:
                    # Child namespace elaborates parent
                    rel = RelationshipRecord(
                        source_id=memory_id,
                        target_id=parent_memory.id,
                        relation_type=RelationType.ELABORATES,
                        strength=1.7,
                        metadata={"detection_method": "namespace_hierarchy", "auto_detected": True},
                        created_at=datetime.now(timezone.utc)
                    )
                    detected.append(rel)
        
        return detected
    
    def xǁRelationshipManagerǁauto_detect_relationships__mutmut_42(
        self,
        memory_id: int,
        storage: MemoryStorage,
        similarity_threshold: float = 0.85
    ) -> List[RelationshipRecord]:
        """
        Auto-detect relationships for a memory.
        
        This method is a placeholder - actual auto-detection requires
        MemoryManager for similarity search. Will be implemented in
        MemoryManager integration.
        
        Args:
            memory_id: ID of memory to detect relationships for
            storage: MemoryStorage instance (for namespace queries)
            similarity_threshold: Minimum similarity for SIMILAR_TO (default: 0.85)
            
        Returns:
            List of detected RelationshipRecord objects
        """
        detected: List[RelationshipRecord] = []
        
        memory = storage.get_memory(memory_id)
        if not memory:
            return detected
        
        # Detect namespace hierarchy relationships
        if "." in memory.namespace:
            parent_ns = memory.namespace.rsplit(".", 1)[0]
            parent_memories = storage.search_by_namespace(parent_ns, exact=True, limit=10)
            
            for parent_memory in parent_memories:
                if parent_memory.id and parent_memory.id != memory_id:
                    # Child namespace elaborates parent
                    rel = RelationshipRecord(
                        source_id=memory_id,
                        target_id=parent_memory.id,
                        relation_type=RelationType.ELABORATES,
                        strength=0.7,
                        metadata={"XXdetection_methodXX": "namespace_hierarchy", "auto_detected": True},
                        created_at=datetime.now(timezone.utc)
                    )
                    detected.append(rel)
        
        return detected
    
    def xǁRelationshipManagerǁauto_detect_relationships__mutmut_43(
        self,
        memory_id: int,
        storage: MemoryStorage,
        similarity_threshold: float = 0.85
    ) -> List[RelationshipRecord]:
        """
        Auto-detect relationships for a memory.
        
        This method is a placeholder - actual auto-detection requires
        MemoryManager for similarity search. Will be implemented in
        MemoryManager integration.
        
        Args:
            memory_id: ID of memory to detect relationships for
            storage: MemoryStorage instance (for namespace queries)
            similarity_threshold: Minimum similarity for SIMILAR_TO (default: 0.85)
            
        Returns:
            List of detected RelationshipRecord objects
        """
        detected: List[RelationshipRecord] = []
        
        memory = storage.get_memory(memory_id)
        if not memory:
            return detected
        
        # Detect namespace hierarchy relationships
        if "." in memory.namespace:
            parent_ns = memory.namespace.rsplit(".", 1)[0]
            parent_memories = storage.search_by_namespace(parent_ns, exact=True, limit=10)
            
            for parent_memory in parent_memories:
                if parent_memory.id and parent_memory.id != memory_id:
                    # Child namespace elaborates parent
                    rel = RelationshipRecord(
                        source_id=memory_id,
                        target_id=parent_memory.id,
                        relation_type=RelationType.ELABORATES,
                        strength=0.7,
                        metadata={"DETECTION_METHOD": "namespace_hierarchy", "auto_detected": True},
                        created_at=datetime.now(timezone.utc)
                    )
                    detected.append(rel)
        
        return detected
    
    def xǁRelationshipManagerǁauto_detect_relationships__mutmut_44(
        self,
        memory_id: int,
        storage: MemoryStorage,
        similarity_threshold: float = 0.85
    ) -> List[RelationshipRecord]:
        """
        Auto-detect relationships for a memory.
        
        This method is a placeholder - actual auto-detection requires
        MemoryManager for similarity search. Will be implemented in
        MemoryManager integration.
        
        Args:
            memory_id: ID of memory to detect relationships for
            storage: MemoryStorage instance (for namespace queries)
            similarity_threshold: Minimum similarity for SIMILAR_TO (default: 0.85)
            
        Returns:
            List of detected RelationshipRecord objects
        """
        detected: List[RelationshipRecord] = []
        
        memory = storage.get_memory(memory_id)
        if not memory:
            return detected
        
        # Detect namespace hierarchy relationships
        if "." in memory.namespace:
            parent_ns = memory.namespace.rsplit(".", 1)[0]
            parent_memories = storage.search_by_namespace(parent_ns, exact=True, limit=10)
            
            for parent_memory in parent_memories:
                if parent_memory.id and parent_memory.id != memory_id:
                    # Child namespace elaborates parent
                    rel = RelationshipRecord(
                        source_id=memory_id,
                        target_id=parent_memory.id,
                        relation_type=RelationType.ELABORATES,
                        strength=0.7,
                        metadata={"detection_method": "XXnamespace_hierarchyXX", "auto_detected": True},
                        created_at=datetime.now(timezone.utc)
                    )
                    detected.append(rel)
        
        return detected
    
    def xǁRelationshipManagerǁauto_detect_relationships__mutmut_45(
        self,
        memory_id: int,
        storage: MemoryStorage,
        similarity_threshold: float = 0.85
    ) -> List[RelationshipRecord]:
        """
        Auto-detect relationships for a memory.
        
        This method is a placeholder - actual auto-detection requires
        MemoryManager for similarity search. Will be implemented in
        MemoryManager integration.
        
        Args:
            memory_id: ID of memory to detect relationships for
            storage: MemoryStorage instance (for namespace queries)
            similarity_threshold: Minimum similarity for SIMILAR_TO (default: 0.85)
            
        Returns:
            List of detected RelationshipRecord objects
        """
        detected: List[RelationshipRecord] = []
        
        memory = storage.get_memory(memory_id)
        if not memory:
            return detected
        
        # Detect namespace hierarchy relationships
        if "." in memory.namespace:
            parent_ns = memory.namespace.rsplit(".", 1)[0]
            parent_memories = storage.search_by_namespace(parent_ns, exact=True, limit=10)
            
            for parent_memory in parent_memories:
                if parent_memory.id and parent_memory.id != memory_id:
                    # Child namespace elaborates parent
                    rel = RelationshipRecord(
                        source_id=memory_id,
                        target_id=parent_memory.id,
                        relation_type=RelationType.ELABORATES,
                        strength=0.7,
                        metadata={"detection_method": "NAMESPACE_HIERARCHY", "auto_detected": True},
                        created_at=datetime.now(timezone.utc)
                    )
                    detected.append(rel)
        
        return detected
    
    def xǁRelationshipManagerǁauto_detect_relationships__mutmut_46(
        self,
        memory_id: int,
        storage: MemoryStorage,
        similarity_threshold: float = 0.85
    ) -> List[RelationshipRecord]:
        """
        Auto-detect relationships for a memory.
        
        This method is a placeholder - actual auto-detection requires
        MemoryManager for similarity search. Will be implemented in
        MemoryManager integration.
        
        Args:
            memory_id: ID of memory to detect relationships for
            storage: MemoryStorage instance (for namespace queries)
            similarity_threshold: Minimum similarity for SIMILAR_TO (default: 0.85)
            
        Returns:
            List of detected RelationshipRecord objects
        """
        detected: List[RelationshipRecord] = []
        
        memory = storage.get_memory(memory_id)
        if not memory:
            return detected
        
        # Detect namespace hierarchy relationships
        if "." in memory.namespace:
            parent_ns = memory.namespace.rsplit(".", 1)[0]
            parent_memories = storage.search_by_namespace(parent_ns, exact=True, limit=10)
            
            for parent_memory in parent_memories:
                if parent_memory.id and parent_memory.id != memory_id:
                    # Child namespace elaborates parent
                    rel = RelationshipRecord(
                        source_id=memory_id,
                        target_id=parent_memory.id,
                        relation_type=RelationType.ELABORATES,
                        strength=0.7,
                        metadata={"detection_method": "namespace_hierarchy", "XXauto_detectedXX": True},
                        created_at=datetime.now(timezone.utc)
                    )
                    detected.append(rel)
        
        return detected
    
    def xǁRelationshipManagerǁauto_detect_relationships__mutmut_47(
        self,
        memory_id: int,
        storage: MemoryStorage,
        similarity_threshold: float = 0.85
    ) -> List[RelationshipRecord]:
        """
        Auto-detect relationships for a memory.
        
        This method is a placeholder - actual auto-detection requires
        MemoryManager for similarity search. Will be implemented in
        MemoryManager integration.
        
        Args:
            memory_id: ID of memory to detect relationships for
            storage: MemoryStorage instance (for namespace queries)
            similarity_threshold: Minimum similarity for SIMILAR_TO (default: 0.85)
            
        Returns:
            List of detected RelationshipRecord objects
        """
        detected: List[RelationshipRecord] = []
        
        memory = storage.get_memory(memory_id)
        if not memory:
            return detected
        
        # Detect namespace hierarchy relationships
        if "." in memory.namespace:
            parent_ns = memory.namespace.rsplit(".", 1)[0]
            parent_memories = storage.search_by_namespace(parent_ns, exact=True, limit=10)
            
            for parent_memory in parent_memories:
                if parent_memory.id and parent_memory.id != memory_id:
                    # Child namespace elaborates parent
                    rel = RelationshipRecord(
                        source_id=memory_id,
                        target_id=parent_memory.id,
                        relation_type=RelationType.ELABORATES,
                        strength=0.7,
                        metadata={"detection_method": "namespace_hierarchy", "AUTO_DETECTED": True},
                        created_at=datetime.now(timezone.utc)
                    )
                    detected.append(rel)
        
        return detected
    
    def xǁRelationshipManagerǁauto_detect_relationships__mutmut_48(
        self,
        memory_id: int,
        storage: MemoryStorage,
        similarity_threshold: float = 0.85
    ) -> List[RelationshipRecord]:
        """
        Auto-detect relationships for a memory.
        
        This method is a placeholder - actual auto-detection requires
        MemoryManager for similarity search. Will be implemented in
        MemoryManager integration.
        
        Args:
            memory_id: ID of memory to detect relationships for
            storage: MemoryStorage instance (for namespace queries)
            similarity_threshold: Minimum similarity for SIMILAR_TO (default: 0.85)
            
        Returns:
            List of detected RelationshipRecord objects
        """
        detected: List[RelationshipRecord] = []
        
        memory = storage.get_memory(memory_id)
        if not memory:
            return detected
        
        # Detect namespace hierarchy relationships
        if "." in memory.namespace:
            parent_ns = memory.namespace.rsplit(".", 1)[0]
            parent_memories = storage.search_by_namespace(parent_ns, exact=True, limit=10)
            
            for parent_memory in parent_memories:
                if parent_memory.id and parent_memory.id != memory_id:
                    # Child namespace elaborates parent
                    rel = RelationshipRecord(
                        source_id=memory_id,
                        target_id=parent_memory.id,
                        relation_type=RelationType.ELABORATES,
                        strength=0.7,
                        metadata={"detection_method": "namespace_hierarchy", "auto_detected": False},
                        created_at=datetime.now(timezone.utc)
                    )
                    detected.append(rel)
        
        return detected
    
    def xǁRelationshipManagerǁauto_detect_relationships__mutmut_49(
        self,
        memory_id: int,
        storage: MemoryStorage,
        similarity_threshold: float = 0.85
    ) -> List[RelationshipRecord]:
        """
        Auto-detect relationships for a memory.
        
        This method is a placeholder - actual auto-detection requires
        MemoryManager for similarity search. Will be implemented in
        MemoryManager integration.
        
        Args:
            memory_id: ID of memory to detect relationships for
            storage: MemoryStorage instance (for namespace queries)
            similarity_threshold: Minimum similarity for SIMILAR_TO (default: 0.85)
            
        Returns:
            List of detected RelationshipRecord objects
        """
        detected: List[RelationshipRecord] = []
        
        memory = storage.get_memory(memory_id)
        if not memory:
            return detected
        
        # Detect namespace hierarchy relationships
        if "." in memory.namespace:
            parent_ns = memory.namespace.rsplit(".", 1)[0]
            parent_memories = storage.search_by_namespace(parent_ns, exact=True, limit=10)
            
            for parent_memory in parent_memories:
                if parent_memory.id and parent_memory.id != memory_id:
                    # Child namespace elaborates parent
                    rel = RelationshipRecord(
                        source_id=memory_id,
                        target_id=parent_memory.id,
                        relation_type=RelationType.ELABORATES,
                        strength=0.7,
                        metadata={"detection_method": "namespace_hierarchy", "auto_detected": True},
                        created_at=datetime.now(None)
                    )
                    detected.append(rel)
        
        return detected
    
    def xǁRelationshipManagerǁauto_detect_relationships__mutmut_50(
        self,
        memory_id: int,
        storage: MemoryStorage,
        similarity_threshold: float = 0.85
    ) -> List[RelationshipRecord]:
        """
        Auto-detect relationships for a memory.
        
        This method is a placeholder - actual auto-detection requires
        MemoryManager for similarity search. Will be implemented in
        MemoryManager integration.
        
        Args:
            memory_id: ID of memory to detect relationships for
            storage: MemoryStorage instance (for namespace queries)
            similarity_threshold: Minimum similarity for SIMILAR_TO (default: 0.85)
            
        Returns:
            List of detected RelationshipRecord objects
        """
        detected: List[RelationshipRecord] = []
        
        memory = storage.get_memory(memory_id)
        if not memory:
            return detected
        
        # Detect namespace hierarchy relationships
        if "." in memory.namespace:
            parent_ns = memory.namespace.rsplit(".", 1)[0]
            parent_memories = storage.search_by_namespace(parent_ns, exact=True, limit=10)
            
            for parent_memory in parent_memories:
                if parent_memory.id and parent_memory.id != memory_id:
                    # Child namespace elaborates parent
                    rel = RelationshipRecord(
                        source_id=memory_id,
                        target_id=parent_memory.id,
                        relation_type=RelationType.ELABORATES,
                        strength=0.7,
                        metadata={"detection_method": "namespace_hierarchy", "auto_detected": True},
                        created_at=datetime.now(timezone.utc)
                    )
                    detected.append(None)
        
        return detected
    
    xǁRelationshipManagerǁauto_detect_relationships__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁRelationshipManagerǁauto_detect_relationships__mutmut_1': xǁRelationshipManagerǁauto_detect_relationships__mutmut_1, 
        'xǁRelationshipManagerǁauto_detect_relationships__mutmut_2': xǁRelationshipManagerǁauto_detect_relationships__mutmut_2, 
        'xǁRelationshipManagerǁauto_detect_relationships__mutmut_3': xǁRelationshipManagerǁauto_detect_relationships__mutmut_3, 
        'xǁRelationshipManagerǁauto_detect_relationships__mutmut_4': xǁRelationshipManagerǁauto_detect_relationships__mutmut_4, 
        'xǁRelationshipManagerǁauto_detect_relationships__mutmut_5': xǁRelationshipManagerǁauto_detect_relationships__mutmut_5, 
        'xǁRelationshipManagerǁauto_detect_relationships__mutmut_6': xǁRelationshipManagerǁauto_detect_relationships__mutmut_6, 
        'xǁRelationshipManagerǁauto_detect_relationships__mutmut_7': xǁRelationshipManagerǁauto_detect_relationships__mutmut_7, 
        'xǁRelationshipManagerǁauto_detect_relationships__mutmut_8': xǁRelationshipManagerǁauto_detect_relationships__mutmut_8, 
        'xǁRelationshipManagerǁauto_detect_relationships__mutmut_9': xǁRelationshipManagerǁauto_detect_relationships__mutmut_9, 
        'xǁRelationshipManagerǁauto_detect_relationships__mutmut_10': xǁRelationshipManagerǁauto_detect_relationships__mutmut_10, 
        'xǁRelationshipManagerǁauto_detect_relationships__mutmut_11': xǁRelationshipManagerǁauto_detect_relationships__mutmut_11, 
        'xǁRelationshipManagerǁauto_detect_relationships__mutmut_12': xǁRelationshipManagerǁauto_detect_relationships__mutmut_12, 
        'xǁRelationshipManagerǁauto_detect_relationships__mutmut_13': xǁRelationshipManagerǁauto_detect_relationships__mutmut_13, 
        'xǁRelationshipManagerǁauto_detect_relationships__mutmut_14': xǁRelationshipManagerǁauto_detect_relationships__mutmut_14, 
        'xǁRelationshipManagerǁauto_detect_relationships__mutmut_15': xǁRelationshipManagerǁauto_detect_relationships__mutmut_15, 
        'xǁRelationshipManagerǁauto_detect_relationships__mutmut_16': xǁRelationshipManagerǁauto_detect_relationships__mutmut_16, 
        'xǁRelationshipManagerǁauto_detect_relationships__mutmut_17': xǁRelationshipManagerǁauto_detect_relationships__mutmut_17, 
        'xǁRelationshipManagerǁauto_detect_relationships__mutmut_18': xǁRelationshipManagerǁauto_detect_relationships__mutmut_18, 
        'xǁRelationshipManagerǁauto_detect_relationships__mutmut_19': xǁRelationshipManagerǁauto_detect_relationships__mutmut_19, 
        'xǁRelationshipManagerǁauto_detect_relationships__mutmut_20': xǁRelationshipManagerǁauto_detect_relationships__mutmut_20, 
        'xǁRelationshipManagerǁauto_detect_relationships__mutmut_21': xǁRelationshipManagerǁauto_detect_relationships__mutmut_21, 
        'xǁRelationshipManagerǁauto_detect_relationships__mutmut_22': xǁRelationshipManagerǁauto_detect_relationships__mutmut_22, 
        'xǁRelationshipManagerǁauto_detect_relationships__mutmut_23': xǁRelationshipManagerǁauto_detect_relationships__mutmut_23, 
        'xǁRelationshipManagerǁauto_detect_relationships__mutmut_24': xǁRelationshipManagerǁauto_detect_relationships__mutmut_24, 
        'xǁRelationshipManagerǁauto_detect_relationships__mutmut_25': xǁRelationshipManagerǁauto_detect_relationships__mutmut_25, 
        'xǁRelationshipManagerǁauto_detect_relationships__mutmut_26': xǁRelationshipManagerǁauto_detect_relationships__mutmut_26, 
        'xǁRelationshipManagerǁauto_detect_relationships__mutmut_27': xǁRelationshipManagerǁauto_detect_relationships__mutmut_27, 
        'xǁRelationshipManagerǁauto_detect_relationships__mutmut_28': xǁRelationshipManagerǁauto_detect_relationships__mutmut_28, 
        'xǁRelationshipManagerǁauto_detect_relationships__mutmut_29': xǁRelationshipManagerǁauto_detect_relationships__mutmut_29, 
        'xǁRelationshipManagerǁauto_detect_relationships__mutmut_30': xǁRelationshipManagerǁauto_detect_relationships__mutmut_30, 
        'xǁRelationshipManagerǁauto_detect_relationships__mutmut_31': xǁRelationshipManagerǁauto_detect_relationships__mutmut_31, 
        'xǁRelationshipManagerǁauto_detect_relationships__mutmut_32': xǁRelationshipManagerǁauto_detect_relationships__mutmut_32, 
        'xǁRelationshipManagerǁauto_detect_relationships__mutmut_33': xǁRelationshipManagerǁauto_detect_relationships__mutmut_33, 
        'xǁRelationshipManagerǁauto_detect_relationships__mutmut_34': xǁRelationshipManagerǁauto_detect_relationships__mutmut_34, 
        'xǁRelationshipManagerǁauto_detect_relationships__mutmut_35': xǁRelationshipManagerǁauto_detect_relationships__mutmut_35, 
        'xǁRelationshipManagerǁauto_detect_relationships__mutmut_36': xǁRelationshipManagerǁauto_detect_relationships__mutmut_36, 
        'xǁRelationshipManagerǁauto_detect_relationships__mutmut_37': xǁRelationshipManagerǁauto_detect_relationships__mutmut_37, 
        'xǁRelationshipManagerǁauto_detect_relationships__mutmut_38': xǁRelationshipManagerǁauto_detect_relationships__mutmut_38, 
        'xǁRelationshipManagerǁauto_detect_relationships__mutmut_39': xǁRelationshipManagerǁauto_detect_relationships__mutmut_39, 
        'xǁRelationshipManagerǁauto_detect_relationships__mutmut_40': xǁRelationshipManagerǁauto_detect_relationships__mutmut_40, 
        'xǁRelationshipManagerǁauto_detect_relationships__mutmut_41': xǁRelationshipManagerǁauto_detect_relationships__mutmut_41, 
        'xǁRelationshipManagerǁauto_detect_relationships__mutmut_42': xǁRelationshipManagerǁauto_detect_relationships__mutmut_42, 
        'xǁRelationshipManagerǁauto_detect_relationships__mutmut_43': xǁRelationshipManagerǁauto_detect_relationships__mutmut_43, 
        'xǁRelationshipManagerǁauto_detect_relationships__mutmut_44': xǁRelationshipManagerǁauto_detect_relationships__mutmut_44, 
        'xǁRelationshipManagerǁauto_detect_relationships__mutmut_45': xǁRelationshipManagerǁauto_detect_relationships__mutmut_45, 
        'xǁRelationshipManagerǁauto_detect_relationships__mutmut_46': xǁRelationshipManagerǁauto_detect_relationships__mutmut_46, 
        'xǁRelationshipManagerǁauto_detect_relationships__mutmut_47': xǁRelationshipManagerǁauto_detect_relationships__mutmut_47, 
        'xǁRelationshipManagerǁauto_detect_relationships__mutmut_48': xǁRelationshipManagerǁauto_detect_relationships__mutmut_48, 
        'xǁRelationshipManagerǁauto_detect_relationships__mutmut_49': xǁRelationshipManagerǁauto_detect_relationships__mutmut_49, 
        'xǁRelationshipManagerǁauto_detect_relationships__mutmut_50': xǁRelationshipManagerǁauto_detect_relationships__mutmut_50
    }
    
    def auto_detect_relationships(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁRelationshipManagerǁauto_detect_relationships__mutmut_orig"), object.__getattribute__(self, "xǁRelationshipManagerǁauto_detect_relationships__mutmut_mutants"), args, kwargs, self)
        return result 
    
    auto_detect_relationships.__signature__ = _mutmut_signature(xǁRelationshipManagerǁauto_detect_relationships__mutmut_orig)
    xǁRelationshipManagerǁauto_detect_relationships__mutmut_orig.__name__ = 'xǁRelationshipManagerǁauto_detect_relationships'

