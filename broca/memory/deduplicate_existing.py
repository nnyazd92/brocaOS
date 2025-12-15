"""
Migration script to deduplicate existing memories in the database.

This script scans for exact duplicates (same namespace and text) and merges them,
keeping the oldest memory and updating its importance and tags.
"""

import sqlite3
import json
import logging
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)


def deduplicate_existing_memories(db_path: str, dry_run: bool = True) -> Dict[str, int]:
    """
    Deduplicate existing memories in the database.
    
    Args:
        db_path: Path to SQLite database file
        dry_run: If True, only report what would be done without making changes
        
    Returns:
        Dictionary with migration statistics
    """
    stats = {
        "total_memories": 0,
        "duplicates_found": 0,
        "duplicates_merged": 0,
        "errors": 0
    }
    
    try:
        # Connect to database
        db_path_obj = Path(db_path)
        if not db_path_obj.exists():
            logger.error(f"Database file not found: {db_path}")
            stats["errors"] += 1
            return stats
        
        connection = sqlite3.connect(str(db_path_obj))
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()
        
        # Get all memories
        cursor.execute("SELECT id, namespace, text, tags, importance, created_at FROM memories ORDER BY id")
        rows = cursor.fetchall()
        stats["total_memories"] = len(rows)
        
        if stats["total_memories"] == 0:
            logger.info("No memories found in database")
            connection.close()
            return stats
        
        # Group by namespace and text
        memory_groups: Dict[str, List[Tuple[int, List[str], float, str]]] = {}
        
        for row in rows:
            key = f"{row['namespace']}:{row['text']}"
            tags = json.loads(row["tags"])
            memory_info = (row["id"], tags, row["importance"], row["created_at"])
            
            if key in memory_groups:
                memory_groups[key].append(memory_info)
            else:
                memory_groups[key] = [memory_info]
        
        # Find groups with duplicates
        duplicate_groups = {key: group for key, group in memory_groups.items() if len(group) > 1}
        stats["duplicates_found"] = len(duplicate_groups)
        
        if dry_run:
            logger.info(f"DRY RUN: Would merge {stats['duplicates_found']} duplicate groups")
        else:
            logger.info(f"Found {stats['duplicates_found']} duplicate groups to merge")
        
        # Process each duplicate group
        for key, group in duplicate_groups.items():
            try:
                # Sort by created_at (oldest first) to keep the oldest memory
                group.sort(key=lambda x: x[3])  # x[3] is created_at
                
                # The first memory is the one we'll keep
                keep_id, keep_tags, keep_importance, keep_created = group[0]
                
                # IDs to delete (all except the first)
                delete_ids = [mem_id for mem_id, _, _, _ in group[1:]]
                
                # Merge tags from all duplicates
                all_tags = set(keep_tags)
                max_importance = keep_importance
                
                for _, tags, importance, _ in group[1:]:
                    all_tags.update(tags)
                    if importance > max_importance:
                        max_importance = importance
                
                merged_tags = list(all_tags)
                
                if dry_run:
                    logger.info(f"DRY RUN: Would merge duplicates for key '{key}'")
                    logger.info(f"  Keep memory ID: {keep_id} (oldest)")
                    logger.info(f"  Delete memory IDs: {delete_ids}")
                    logger.info(f"  Original importance: {keep_importance}, New importance: {max_importance}")
                    logger.info(f"  Original tags: {keep_tags}, Merged tags: {merged_tags}")
                    stats["duplicates_merged"] += 1
                    continue
                
                # Update the kept memory with merged tags and max importance
                tags_json = json.dumps(merged_tags)
                now = datetime.now(timezone.utc).isoformat()
                
                cursor.execute("""
                    UPDATE memories 
                    SET importance = ?, tags = ?, last_used_at = ?
                    WHERE id = ?
                """, (max_importance, tags_json, now, keep_id))
                
                # Delete the duplicate memories
                # Note: In a real system, we might want to archive instead of delete
                # For now, we'll delete them
                placeholders = ",".join("?" * len(delete_ids))
                cursor.execute(f"""
                    DELETE FROM memories 
                    WHERE id IN ({placeholders})
                """, delete_ids)
                
                connection.commit()
                
                logger.info(f"Merged {len(group)} duplicates for key '{key}'")
                logger.debug(f"  Kept memory {keep_id}, deleted {delete_ids}")
                logger.debug(f"  New importance: {max_importance}, merged tags: {merged_tags}")
                
                stats["duplicates_merged"] += 1
                
            except Exception as e:
                logger.error(f"Error processing duplicate group '{key}': {e}")
                stats["errors"] += 1
        
        # Report summary
        if dry_run:
            logger.info("=== DRY RUN SUMMARY ===")
        else:
            logger.info("=== MIGRATION SUMMARY ===")
        
        logger.info(f"Total memories: {stats['total_memories']}")
        logger.info(f"Duplicate groups found: {stats['duplicates_found']}")
        logger.info(f"Duplicate groups processed: {stats['duplicates_merged']}")
        logger.info(f"Errors: {stats['errors']}")
        
        if not dry_run and stats['duplicates_merged'] > 0:
            # Verify the merge
            cursor.execute("SELECT COUNT(*) as count FROM memories")
            new_count = cursor.fetchone()["count"]
            expected_count = stats["total_memories"] - sum(len(group) - 1 for group in duplicate_groups.values())
            
            logger.info(f"Memory count after merge: {new_count}")
            logger.info(f"Expected count: {expected_count}")
            
            if new_count == expected_count:
                logger.info("✓ Merge successful - counts match")
            else:
                logger.warning(f"⚠️  Count mismatch: expected {expected_count}, got {new_count}")
        
        connection.close()
        return stats
        
    except Exception as e:
        logger.error(f"Error in deduplication: {e}", exc_info=True)
        stats["errors"] += 1
        return stats


def main():
    """Command-line interface for deduplication migration."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Deduplicate existing memories in the database")
    parser.add_argument("db_path", help="Path to SQLite database file")
    parser.add_argument("--dry-run", action="store_true", help="Only report what would be done without making changes")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    print(f"{'DRY RUN: ' if args.dry_run else ''}Deduplicating memories in {args.db_path}")
    print("=" * 60)
    
    stats = deduplicate_existing_memories(args.db_path, dry_run=args.dry_run)
    
    print("=" * 60)
    if args.dry_run:
        print("DRY RUN COMPLETE - No changes were made")
        print("Run without --dry-run to apply changes")
    else:
        print("MIGRATION COMPLETE")
    
    return 0 if stats["errors"] == 0 else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
