# Production Data Migration Guide
## MySQL → PostgreSQL 15

**Purpose:** Step-by-step guide for migrating production data from MySQL to PostgreSQL  
**Estimated Time:** 4-8 hours (depends on data volume)  
**Difficulty:** Moderate  
**Risk Level:** High (production data)  

---

## 🎯 Overview

This guide will help you migrate all production data from MySQL to PostgreSQL 15 with zero data loss and minimal downtime.

### What Will Be Migrated

| Table | Estimated Rows | Priority | Notes |
|-------|----------------|----------|-------|
| `analyzer_sessions` | 1,000+ | HIGH | Main analyzer data |
| `analyzer_followups` | 500+ | HIGH | Follow-up questions |
| `analyzer_feedback` | 200+ | MEDIUM | User feedback |
| `chatbot_sessions` | 2,000+ | HIGH | Chat sessions |
| `chatbot_messages` | 10,000+ | HIGH | All conversations |
| `evaluator_sessions` | 500+ | HIGH | Evaluations |
| `evaluator_followups` | 100+ | MEDIUM | Evaluation follow-ups |
| `evaluator_feedback` | 50+ | MEDIUM | Evaluation feedback |
| `organizations` | 10-50 | HIGH | Organization config |
| `org_guidelines` | 20-100 | HIGH | Org guidelines |
| `users` | 100+ | MEDIUM | User accounts |
| `api_keys` | 50+ | MEDIUM | API authentication |
| `prompts_master` | 100+ | HIGH | System prompts |

### Migration Strategy

**Approach:** Blue-Green Deployment
- Keep MySQL running (Blue)
- Migrate to PostgreSQL (Green)
- Validate Green
- Switch traffic to Green
- Keep Blue as backup for 2 weeks

---

## ⚠️ CRITICAL: Before You Start

### 1. Read This Entire Guide First
Don't start migrating until you've read everything and understand each step.

### 2. Required Access
- [ ] MySQL production database (read access)
- [ ] PostgreSQL production database (full access)
- [ ] Production server SSH/terminal access
- [ ] S3 or backup storage for backups
- [ ] Emergency contact numbers for team

### 3. Required Tools
```bash
# Install these tools before starting
pip install psycopg2-binary mysql-connector-python pandas sqlalchemy
```

### 4. Maintenance Window
- [ ] Schedule 4-hour maintenance window
- [ ] Notify all stakeholders 48 hours in advance
- [ ] Prepare rollback plan
- [ ] Have team on standby

### 5. Backup Everything
```bash
# This is NON-NEGOTIABLE
# Multiple backups in multiple locations
```

---

## 📋 Pre-Migration Checklist

### Step 1: Document Current State

```bash
# 1. Get MySQL database size
mysql -h ${MYSQL_HOST} -u ${MYSQL_USER} -p${MYSQL_PASSWORD} ${MYSQL_DATABASE} -e "
SELECT 
    table_schema AS 'Database',
    ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) AS 'Size (MB)'
FROM information_schema.tables
WHERE table_schema = '${MYSQL_DATABASE}'
GROUP BY table_schema;"

# 2. Get row counts for all tables
mysql -h ${MYSQL_HOST} -u ${MYSQL_USER} -p${MYSQL_PASSWORD} ${MYSQL_DATABASE} -e "
SELECT 
    table_name AS 'Table',
    table_rows AS 'Rows'
FROM information_schema.tables
WHERE table_schema = '${MYSQL_DATABASE}'
ORDER BY table_rows DESC;"

# 3. Save to file for comparison later
mysql -h ${MYSQL_HOST} -u ${MYSQL_USER} -p${MYSQL_PASSWORD} ${MYSQL_DATABASE} -e "
SELECT table_name, table_rows FROM information_schema.tables 
WHERE table_schema = '${MYSQL_DATABASE}';" > mysql_table_counts.txt

# 4. Document current data ranges
mysql -h ${MYSQL_HOST} -u ${MYSQL_USER} -p${MYSQL_PASSWORD} ${MYSQL_DATABASE} -e "
SELECT 
    'analyzer_sessions' AS table_name,
    MIN(created_at) AS oldest_record,
    MAX(created_at) AS newest_record,
    COUNT(*) AS total_rows
FROM analyzer_sessions
UNION ALL
SELECT 
    'chatbot_sessions',
    MIN(created_at),
    MAX(created_at),
    COUNT(*)
FROM chatbot_sessions
UNION ALL
SELECT 
    'evaluator_sessions',
    MIN(created_at),
    MAX(created_at),
    COUNT(*)
FROM evaluator_sessions;" > mysql_data_ranges.txt
```

### Step 2: Create Backups (Multiple!)

```bash
# Backup 1: Full database dump to local file
echo "Creating Backup 1: Local dump..."
mysqldump -h ${MYSQL_HOST} \
  -u ${MYSQL_USER} \
  -p${MYSQL_PASSWORD} \
  --single-transaction \
  --routines \
  --triggers \
  --events \
  ${MYSQL_DATABASE} > backup_mysql_$(date +%Y%m%d_%H%M%S).sql

# Verify backup was created and is not empty
ls -lh backup_mysql_*.sql
if [ $? -ne 0 ]; then
    echo "ERROR: Backup 1 failed!"
    exit 1
fi

# Backup 2: Compressed dump to S3
echo "Creating Backup 2: Compressed to S3..."
mysqldump -h ${MYSQL_HOST} \
  -u ${MYSQL_USER} \
  -p${MYSQL_PASSWORD} \
  --single-transaction \
  ${MYSQL_DATABASE} | gzip > backup_mysql_$(date +%Y%m%d_%H%M%S).sql.gz

aws s3 cp backup_mysql_*.sql.gz s3://your-backup-bucket/migrations/mysql/

# Backup 3: Table-by-table dumps (for granular recovery)
echo "Creating Backup 3: Table-by-table..."
mkdir -p table_backups
for table in analyzer_sessions analyzer_followups analyzer_feedback \
             chatbot_sessions chatbot_messages \
             evaluator_sessions evaluator_followups evaluator_feedback \
             organizations org_guidelines users api_keys prompts_master; do
    echo "Backing up $table..."
    mysqldump -h ${MYSQL_HOST} \
      -u ${MYSQL_USER} \
      -p${MYSQL_PASSWORD} \
      ${MYSQL_DATABASE} $table > table_backups/${table}.sql
done

# Backup 4: Data export as CSV (for manual inspection)
echo "Creating Backup 4: CSV exports..."
mkdir -p csv_backups
mysql -h ${MYSQL_HOST} -u ${MYSQL_USER} -p${MYSQL_PASSWORD} ${MYSQL_DATABASE} -e "
SELECT * FROM analyzer_sessions INTO OUTFILE '/tmp/analyzer_sessions.csv'
FIELDS TERMINATED BY ',' ENCLOSED BY '\"' LINES TERMINATED BY '\n';"
# Repeat for other tables as needed

echo "✅ All backups created!"
```

### Step 3: Test Backup Restoration

```bash
# CRITICAL: Test that you can actually restore from backup
# Do this on a test database, NOT production!

# 1. Create test database
mysql -h ${TEST_MYSQL_HOST} -u root -p -e "CREATE DATABASE test_restore;"

# 2. Restore from backup
mysql -h ${TEST_MYSQL_HOST} -u root -p test_restore < backup_mysql_*.sql

# 3. Verify row counts match
mysql -h ${TEST_MYSQL_HOST} -u root -p test_restore -e "
SELECT table_name, table_rows FROM information_schema.tables 
WHERE table_schema = 'test_restore';" > test_restore_counts.txt

# 4. Compare with original
diff mysql_table_counts.txt test_restore_counts.txt

# If diff shows no differences, backup is good!
# Clean up test database
mysql -h ${TEST_MYSQL_HOST} -u root -p -e "DROP DATABASE test_restore;"

echo "✅ Backup restoration verified!"
```

---

## 🛠️ Migration Scripts

### Script 1: Main Migration Script

Create `scripts/migrate_mysql_to_postgres.py`:

```python
#!/usr/bin/env python3
"""
Production Data Migration Script: MySQL → PostgreSQL
"""
import os
import sys
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
import mysql.connector
import psycopg2
from psycopg2.extras import execute_batch
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'migration_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class DatabaseMigrator:
    """Migrate data from MySQL to PostgreSQL"""
    
    # Tables to migrate in order (respects foreign keys)
    TABLES_ORDER = [
        'organizations',
        'org_guidelines',
        'users',
        'api_keys',
        'prompts_master',
        'analyzer_sessions',
        'analyzer_followups',
        'analyzer_feedback',
        'chatbot_sessions',
        'chatbot_messages',
        'evaluator_sessions',
        'evaluator_followups',
        'evaluator_feedback'
    ]
    
    def __init__(self):
        """Initialize database connections"""
        # MySQL connection
        self.mysql_conn = mysql.connector.connect(
            host=os.getenv('MYSQL_HOST'),
            port=int(os.getenv('MYSQL_PORT', 3306)),
            database=os.getenv('MYSQL_DATABASE'),
            user=os.getenv('MYSQL_USER'),
            password=os.getenv('MYSQL_PASSWORD')
        )
        logger.info("✅ MySQL connection established")
        
        # PostgreSQL connection
        self.pg_conn = psycopg2.connect(
            host=os.getenv('POSTGRES_HOST'),
            port=int(os.getenv('POSTGRES_PORT', 5432)),
            database=os.getenv('POSTGRES_DATABASE'),
            user=os.getenv('POSTGRES_USER'),
            password=os.getenv('POSTGRES_PASSWORD')
        )
        logger.info("✅ PostgreSQL connection established")
        
        self.stats = {}
    
    def transform_row(self, table: str, row: Dict) -> Dict:
        """
        Transform MySQL row to PostgreSQL format
        
        Key transformations:
        1. MySQL DATETIME → PostgreSQL TIMESTAMP
        2. MySQL JSON string → PostgreSQL JSONB
        3. MySQL TINYINT(1) → PostgreSQL BOOLEAN
        4. Handle NULL values
        """
        transformed = {}
        
        for key, value in row.items():
            # Handle None/NULL
            if value is None:
                transformed[key] = None
                continue
            
            # Convert datetime objects to ISO format string
            if isinstance(value, datetime):
                transformed[key] = value.isoformat()
            
            # Convert MySQL JSON strings to proper JSON
            elif key in ['sections', 'context_data', 'internal_analysis', 'external_analysis', 
                        'delta_analysis', 'metadata', 'configuration']:
                if isinstance(value, str):
                    try:
                        transformed[key] = json.loads(value)
                    except json.JSONDecodeError:
                        transformed[key] = value
                else:
                    transformed[key] = value
            
            # Convert MySQL TINYINT(1) to boolean
            elif key in ['is_active', 'is_deleted', 'within_knowledge_base']:
                transformed[key] = bool(value)
            
            else:
                transformed[key] = value
        
        return transformed
    
    def get_table_columns(self, table: str, conn_type: str = 'postgres') -> List[str]:
        """Get column names for a table"""
        if conn_type == 'postgres':
            cursor = self.pg_conn.cursor()
            cursor.execute(f"""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = '{table}'
                ORDER BY ordinal_position
            """)
            columns = [row[0] for row in cursor.fetchall()]
            cursor.close()
            return columns
        else:
            cursor = self.mysql_conn.cursor()
            cursor.execute(f"SHOW COLUMNS FROM {table}")
            columns = [row[0] for row in cursor.fetchall()]
            cursor.close()
            return columns
    
    def migrate_table(self, table: str, batch_size: int = 1000) -> Dict[str, Any]:
        """
        Migrate a single table from MySQL to PostgreSQL
        
        Args:
            table: Table name
            batch_size: Number of rows to process at once
            
        Returns:
            Migration statistics
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"Starting migration of table: {table}")
        logger.info(f"{'='*60}")
        
        start_time = time.time()
        
        try:
            # Get source data
            mysql_cursor = self.mysql_conn.cursor(dictionary=True)
            mysql_cursor.execute(f"SELECT * FROM {table}")
            
            # Get total count
            total_rows = mysql_cursor.rowcount
            logger.info(f"Total rows to migrate: {total_rows}")
            
            if total_rows == 0:
                logger.warning(f"⚠️  Table {table} is empty, skipping")
                mysql_cursor.close()
                return {'table': table, 'rows': 0, 'status': 'empty', 'time': 0}
            
            # Get target columns
            pg_columns = self.get_table_columns(table, 'postgres')
            
            # Prepare PostgreSQL insert
            pg_cursor = self.pg_conn.cursor()
            
            # Build INSERT statement
            placeholders = ', '.join(['%s'] * len(pg_columns))
            insert_sql = f"""
                INSERT INTO {table} ({', '.join(pg_columns)})
                VALUES ({placeholders})
                ON CONFLICT DO NOTHING
            """
            
            # Migrate in batches
            migrated_count = 0
            error_count = 0
            batch = []
            
            for row in mysql_cursor:
                try:
                    # Transform row
                    transformed_row = self.transform_row(table, row)
                    
                    # Extract values in column order
                    values = [transformed_row.get(col) for col in pg_columns]
                    
                    batch.append(values)
                    
                    # Insert batch when full
                    if len(batch) >= batch_size:
                        execute_batch(pg_cursor, insert_sql, batch)
                        self.pg_conn.commit()
                        migrated_count += len(batch)
                        logger.info(f"  ✅ Migrated {migrated_count}/{total_rows} rows...")
                        batch = []
                        
                except Exception as e:
                    logger.error(f"  ❌ Error migrating row: {e}")
                    logger.error(f"  Row data: {row}")
                    error_count += 1
                    if error_count > 10:
                        raise Exception(f"Too many errors ({error_count}), aborting")
            
            # Insert remaining rows
            if batch:
                execute_batch(pg_cursor, insert_sql, batch)
                self.pg_conn.commit()
                migrated_count += len(batch)
                logger.info(f"  ✅ Migrated {migrated_count}/{total_rows} rows (final batch)")
            
            # Verify count
            pg_cursor.execute(f"SELECT COUNT(*) FROM {table}")
            pg_count = pg_cursor.fetchone()[0]
            
            mysql_cursor.close()
            pg_cursor.close()
            
            duration = time.time() - start_time
            
            # Check if counts match
            if pg_count == total_rows:
                logger.info(f"✅ SUCCESS: {table} - {pg_count} rows migrated in {duration:.2f}s")
                status = 'success'
            else:
                logger.warning(f"⚠️  WARNING: {table} - Count mismatch! MySQL: {total_rows}, PostgreSQL: {pg_count}")
                status = 'count_mismatch'
            
            return {
                'table': table,
                'mysql_rows': total_rows,
                'postgres_rows': pg_count,
                'errors': error_count,
                'status': status,
                'time': duration
            }
            
        except Exception as e:
            logger.error(f"❌ FAILED: {table} - {str(e)}")
            self.pg_conn.rollback()
            return {
                'table': table,
                'status': 'failed',
                'error': str(e),
                'time': time.time() - start_time
            }
    
    def migrate_all(self) -> Dict[str, Any]:
        """Migrate all tables"""
        logger.info("\n" + "="*80)
        logger.info("STARTING FULL DATABASE MIGRATION")
        logger.info("="*80 + "\n")
        
        overall_start = time.time()
        results = []
        
        for table in self.TABLES_ORDER:
            result = self.migrate_table(table)
            results.append(result)
            self.stats[table] = result
            
            # Pause between tables
            time.sleep(1)
        
        overall_time = time.time() - overall_start
        
        # Summary
        logger.info("\n" + "="*80)
        logger.info("MIGRATION SUMMARY")
        logger.info("="*80)
        
        total_rows = sum(r.get('postgres_rows', 0) for r in results)
        successful = sum(1 for r in results if r['status'] == 'success')
        failed = sum(1 for r in results if r['status'] == 'failed')
        
        logger.info(f"\nTotal tables: {len(results)}")
        logger.info(f"Successful: {successful}")
        logger.info(f"Failed: {failed}")
        logger.info(f"Total rows migrated: {total_rows}")
        logger.info(f"Total time: {overall_time:.2f}s")
        
        logger.info("\nDetailed Results:")
        for result in results:
            status_emoji = "✅" if result['status'] == 'success' else "❌"
            logger.info(f"  {status_emoji} {result['table']}: {result.get('postgres_rows', 0)} rows")
        
        return {
            'total_tables': len(results),
            'successful': successful,
            'failed': failed,
            'total_rows': total_rows,
            'total_time': overall_time,
            'results': results
        }
    
    def close(self):
        """Close database connections"""
        self.mysql_conn.close()
        self.pg_conn.close()
        logger.info("Database connections closed")


def main():
    """Main migration function"""
    print("\n" + "="*80)
    print("PRODUCTION DATA MIGRATION: MySQL → PostgreSQL")
    print("="*80 + "\n")
    
    # Check environment variables
    required_vars = [
        'MYSQL_HOST', 'MYSQL_DATABASE', 'MYSQL_USER', 'MYSQL_PASSWORD',
        'POSTGRES_HOST', 'POSTGRES_DATABASE', 'POSTGRES_USER', 'POSTGRES_PASSWORD'
    ]
    
    missing = [var for var in required_vars if not os.getenv(var)]
    if missing:
        print(f"❌ ERROR: Missing environment variables: {', '.join(missing)}")
        sys.exit(1)
    
    # Confirm before proceeding
    print("⚠️  WARNING: This will migrate data from MySQL to PostgreSQL")
    print(f"Source: {os.getenv('MYSQL_HOST')}/{os.getenv('MYSQL_DATABASE')}")
    print(f"Target: {os.getenv('POSTGRES_HOST')}/{os.getenv('POSTGRES_DATABASE')}")
    print("\nPlease ensure:")
    print("  1. You have backed up MySQL database")
    print("  2. PostgreSQL schema is created (migrations run)")
    print("  3. You are ready to proceed")
    
    response = input("\nType 'YES' to proceed: ")
    if response != 'YES':
        print("❌ Migration cancelled")
        sys.exit(0)
    
    # Run migration
    migrator = DatabaseMigrator()
    
    try:
        results = migrator.migrate_all()
        
        # Save results to file
        with open(f'migration_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        if results['failed'] == 0:
            print("\n✅ MIGRATION COMPLETED SUCCESSFULLY!")
            sys.exit(0)
        else:
            print(f"\n⚠️  MIGRATION COMPLETED WITH {results['failed']} FAILURES")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ MIGRATION FAILED: {e}")
        logger.exception("Migration failed with exception")
        sys.exit(1)
        
    finally:
        migrator.close()


if __name__ == "__main__":
    main()
```

### Script 2: Validation Script

Create `scripts/validate_migration.py`:

```python
#!/usr/bin/env python3
"""
Migration Validation Script
Compares MySQL and PostgreSQL databases to ensure successful migration
"""
import os
import sys
import json
from datetime import datetime
import mysql.connector
import psycopg2
from psycopg2.extras import RealDictCursor
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class MigrationValidator:
    """Validate data migration between MySQL and PostgreSQL"""
    
    TABLES = [
        'organizations', 'org_guidelines', 'users', 'api_keys', 'prompts_master',
        'analyzer_sessions', 'analyzer_followups', 'analyzer_feedback',
        'chatbot_sessions', 'chatbot_messages',
        'evaluator_sessions', 'evaluator_followups', 'evaluator_feedback'
    ]
    
    def __init__(self):
        self.mysql_conn = mysql.connector.connect(
            host=os.getenv('MYSQL_HOST'),
            port=int(os.getenv('MYSQL_PORT', 3306)),
            database=os.getenv('MYSQL_DATABASE'),
            user=os.getenv('MYSQL_USER'),
            password=os.getenv('MYSQL_PASSWORD')
        )
        
        self.pg_conn = psycopg2.connect(
            host=os.getenv('POSTGRES_HOST'),
            port=int(os.getenv('POSTGRES_PORT', 5432)),
            database=os.getenv('POSTGRES_DATABASE'),
            user=os.getenv('POSTGRES_USER'),
            password=os.getenv('POSTGRES_PASSWORD')
        )
        
        self.issues = []
    
    def validate_row_counts(self):
        """Validate row counts match"""
        logger.info("\n" + "="*60)
        logger.info("VALIDATING ROW COUNTS")
        logger.info("="*60)
        
        for table in self.TABLES:
            # MySQL count
            mysql_cursor = self.mysql_conn.cursor()
            mysql_cursor.execute(f"SELECT COUNT(*) FROM {table}")
            mysql_count = mysql_cursor.fetchone()[0]
            mysql_cursor.close()
            
            # PostgreSQL count
            pg_cursor = self.pg_conn.cursor()
            pg_cursor.execute(f"SELECT COUNT(*) FROM {table}")
            pg_count = pg_cursor.fetchone()[0]
            pg_cursor.close()
            
            if mysql_count == pg_count:
                logger.info(f"  ✅ {table}: {mysql_count} rows (match)")
            else:
                logger.error(f"  ❌ {table}: MySQL={mysql_count}, PostgreSQL={pg_count} (MISMATCH!)")
                self.issues.append(f"{table}: Row count mismatch")
    
    def validate_foreign_keys(self):
        """Validate foreign key relationships"""
        logger.info("\n" + "="*60)
        logger.info("VALIDATING FOREIGN KEY INTEGRITY")
        logger.info("="*60)
        
        pg_cursor = self.pg_conn.cursor()
        
        # Check for orphaned records
        checks = [
            ("analyzer_followups", "session_id", "analyzer_sessions", "session_id"),
            ("analyzer_feedback", "session_id", "analyzer_sessions", "session_id"),
            ("chatbot_messages", "session_id", "chatbot_sessions", "session_id"),
            ("evaluator_followups", "session_id", "evaluator_sessions", "session_id"),
            ("evaluator_feedback", "session_id", "evaluator_sessions", "session_id"),
            ("org_guidelines", "organization_id", "organizations", "organization_id"),
        ]
        
        for child_table, child_col, parent_table, parent_col in checks:
            pg_cursor.execute(f"""
                SELECT COUNT(*) FROM {child_table} c
                WHERE NOT EXISTS (
                    SELECT 1 FROM {parent_table} p
                    WHERE p.{parent_col} = c.{child_col}
                )
            """)
            orphaned = pg_cursor.fetchone()[0]
            
            if orphaned == 0:
                logger.info(f"  ✅ {child_table}.{child_col} → {parent_table}.{parent_col}: OK")
            else:
                logger.error(f"  ❌ {child_table}.{child_col}: {orphaned} orphaned records!")
                self.issues.append(f"{child_table}: {orphaned} orphaned records")
        
        pg_cursor.close()
    
    def spot_check_data(self, sample_size=10):
        """Spot check random records"""
        logger.info("\n" + "="*60)
        logger.info(f"SPOT CHECKING DATA ({sample_size} random records per table)")
        logger.info("="*60)
        
        for table in ['analyzer_sessions', 'chatbot_sessions', 'evaluator_sessions']:
            try:
                # Get random records from MySQL
                mysql_cursor = self.mysql_conn.cursor(dictionary=True)
                mysql_cursor.execute(f"""
                    SELECT * FROM {table}
                    ORDER BY RAND()
                    LIMIT {sample_size}
                """)
                mysql_records = {r['session_id']: r for r in mysql_cursor.fetchall()}
                mysql_cursor.close()
                
                if not mysql_records:
                    logger.info(f"  ⚠️  {table}: No records to check")
                    continue
                
                # Get same records from PostgreSQL
                pg_cursor = self.pg_conn.cursor(cursor_factory=RealDictCursor)
                session_ids = list(mysql_records.keys())
                pg_cursor.execute(f"""
                    SELECT * FROM {table}
                    WHERE session_id = ANY(%s)
                """, (session_ids,))
                pg_records = {r['session_id']: r for r in pg_cursor.fetchall()}
                pg_cursor.close()
                
                # Compare
                mismatches = 0
                for session_id in session_ids:
                    if session_id not in pg_records:
                        logger.error(f"    ❌ Session {session_id} missing in PostgreSQL!")
                        mismatches += 1
                
                if mismatches == 0:
                    logger.info(f"  ✅ {table}: All {len(session_ids)} sample records present")
                else:
                    logger.error(f"  ❌ {table}: {mismatches} records missing!")
                    self.issues.append(f"{table}: {mismatches} sample records missing")
                    
            except Exception as e:
                logger.error(f"  ❌ {table}: Spot check failed - {e}")
                self.issues.append(f"{table}: Spot check error")
    
    def validate_data_ranges(self):
        """Validate data ranges (oldest/newest records)"""
        logger.info("\n" + "="*60)
        logger.info("VALIDATING DATA RANGES")
        logger.info("="*60)
        
        for table in ['analyzer_sessions', 'chatbot_sessions', 'evaluator_sessions']:
            try:
                # MySQL ranges
                mysql_cursor = self.mysql_conn.cursor()
                mysql_cursor.execute(f"""
                    SELECT MIN(created_at), MAX(created_at)
                    FROM {table}
                """)
                mysql_min, mysql_max = mysql_cursor.fetchone()
                mysql_cursor.close()
                
                # PostgreSQL ranges
                pg_cursor = self.pg_conn.cursor()
                pg_cursor.execute(f"""
                    SELECT MIN(created_at), MAX(created_at)
                    FROM {table}
                """)
                pg_min, pg_max = pg_cursor.fetchone()
                pg_cursor.close()
                
                if mysql_min == pg_min and mysql_max == pg_max:
                    logger.info(f"  ✅ {table}: {mysql_min} to {mysql_max}")
                else:
                    logger.warning(f"  ⚠️  {table}: Date range mismatch")
                    logger.warning(f"      MySQL: {mysql_min} to {mysql_max}")
                    logger.warning(f"      PostgreSQL: {pg_min} to {pg_max}")
                    
            except Exception as e:
                logger.error(f"  ❌ {table}: Range check failed - {e}")
    
    def validate_json_columns(self):
        """Validate JSON/JSONB columns"""
        logger.info("\n" + "="*60)
        logger.info("VALIDATING JSON/JSONB COLUMNS")
        logger.info("="*60)
        
        checks = [
            ('analyzer_sessions', 'sections'),
            ('chatbot_messages', 'context_data'),
            ('evaluator_sessions', 'internal_analysis'),
            ('evaluator_sessions', 'external_analysis'),
        ]
        
        pg_cursor = self.pg_conn.cursor()
        
        for table, column in checks:
            try:
                # Check for invalid JSON
                pg_cursor.execute(f"""
                    SELECT COUNT(*)
                    FROM {table}
                    WHERE {column} IS NOT NULL
                    AND jsonb_typeof({column}) IS NULL
                """)
                invalid = pg_cursor.fetchone()[0]
                
                if invalid == 0:
                    logger.info(f"  ✅ {table}.{column}: Valid JSONB")
                else:
                    logger.error(f"  ❌ {table}.{column}: {invalid} invalid JSON records!")
                    self.issues.append(f"{table}.{column}: Invalid JSON")
                    
            except Exception as e:
                logger.error(f"  ❌ {table}.{column}: Check failed - {e}")
        
        pg_cursor.close()
    
    def run_all_validations(self):
        """Run all validation checks"""
        logger.info("\n" + "="*80)
        logger.info("STARTING MIGRATION VALIDATION")
        logger.info("="*80)
        
        self.validate_row_counts()
        self.validate_foreign_keys()
        self.validate_data_ranges()
        self.validate_json_columns()
        self.spot_check_data()
        
        # Summary
        logger.info("\n" + "="*80)
        logger.info("VALIDATION SUMMARY")
        logger.info("="*80)
        
        if not self.issues:
            logger.info("\n✅ ALL VALIDATIONS PASSED!")
            logger.info("Migration appears successful. Proceed to next phase.")
            return True
        else:
            logger.error(f"\n❌ VALIDATION FAILED: {len(self.issues)} issues found")
            logger.error("\nIssues:")
            for issue in self.issues:
                logger.error(f"  - {issue}")
            logger.error("\nDO NOT proceed to production until these issues are resolved!")
            return False
    
    def close(self):
        """Close connections"""
        self.mysql_conn.close()
        self.pg_conn.close()


def main():
    validator = MigrationValidator()
    
    try:
        success = validator.run_all_validations()
        sys.exit(0 if success else 1)
    finally:
        validator.close()


if __name__ == "__main__":
    main()
```

---

## 🚀 Execution Steps

### Phase 1: Preparation (30 minutes)

```bash
# 1. Create working directory
mkdir -p ~/migration_$(date +%Y%m%d)
cd ~/migration_$(date +%Y%m%d)

# 2. Copy scripts
cp /path/to/migrate_mysql_to_postgres.py .
cp /path/to/validate_migration.py .
chmod +x *.py

# 3. Setup environment
cat > .env << EOF
# MySQL Source
MYSQL_HOST=production-mysql-host.rds.amazonaws.com
MYSQL_PORT=3306
MYSQL_DATABASE=document_analyzer
MYSQL_USER=admin
MYSQL_PASSWORD=your_mysql_password

# PostgreSQL Target
POSTGRES_HOST=production-postgres-host.rds.amazonaws.com
POSTGRES_PORT=5432
POSTGRES_DATABASE=document_analyzer
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_postgres_password
EOF

# 4. Load environment
set -a
source .env
set +a

# 5. Test connections
python3 -c "
import mysql.connector
import psycopg2
import os

try:
    mysql_conn = mysql.connector.connect(
        host=os.getenv('MYSQL_HOST'),
        database=os.getenv('MYSQL_DATABASE'),
        user=os.getenv('MYSQL_USER'),
        password=os.getenv('MYSQL_PASSWORD')
    )
    print('✅ MySQL connection successful')
    mysql_conn.close()
except Exception as e:
    print(f'❌ MySQL connection failed: {e}')
    exit(1)

try:
    pg_conn = psycopg2.connect(
        host=os.getenv('POSTGRES_HOST'),
        database=os.getenv('POSTGRES_DATABASE'),
        user=os.getenv('POSTGRES_USER'),
        password=os.getenv('POSTGRES_PASSWORD')
    )
    print('✅ PostgreSQL connection successful')
    pg_conn.close()
except Exception as e:
    print(f'❌ PostgreSQL connection failed: {e}')
    exit(1)
"

echo "✅ Preparation complete!"
```

### Phase 2: Create Backups (1 hour)

```bash
# Run all backup steps from Pre-Migration Checklist
# This is CRITICAL - do not skip!

# Execute Step 2 from Pre-Migration Checklist above
# When complete, verify you have:
ls -lh backup_mysql_*.sql
ls -lh table_backups/
```

### Phase 3: Run Migration (1-3 hours, depends on data volume)

```bash
# 1. Ensure PostgreSQL schema is created
docker-compose exec postgres psql -U ${POSTGRES_USER} -d ${POSTGRES_DATABASE} -f /docker-entrypoint-initdb.d/001_analyzer_schema.sql
docker-compose exec postgres psql -U ${POSTGRES_USER} -d ${POSTGRES_DATABASE} -f /docker-entrypoint-initdb.d/002_chatbot_schema.sql
docker-compose exec postgres psql -U ${POSTGRES_USER} -d ${POSTGRES_DATABASE} -f /docker-entrypoint-initdb.d/003_evaluator_schema.sql
docker-compose exec postgres psql -U ${POSTGRES_USER} -d ${POSTGRES_DATABASE} -f /docker-entrypoint-initdb.d/004_admin_schema.sql

# 2. Verify tables exist
docker-compose exec postgres psql -U ${POSTGRES_USER} -d ${POSTGRES_DATABASE} -c "\dt"

# 3. Run migration script
python3 migrate_mysql_to_postgres.py

# This will:
# - Show source and target databases
# - Ask for confirmation (type 'YES')
# - Migrate all tables in correct order
# - Show progress for each table
# - Save results to migration_results_*.json
# - Create migration_*.log file

# 4. Check logs
tail -f migration_*.log

# 5. Review results
cat migration_results_*.json | jq .
```

### Phase 4: Validation (30 minutes)

```bash
# 1. Run validation script
python3 validate_migration.py

# This will:
# - Compare row counts
# - Check foreign key integrity
# - Validate data ranges
# - Check JSON column validity
# - Spot check random records
# - Generate validation report

# 2. If validation fails:
#    - Review issues in log
#    - DO NOT PROCEED
#    - Fix issues and re-run migration
#    - Re-validate

# 3. If validation passes:
echo "✅ Validation successful! Ready for next phase."
```

### Phase 5: Post-Migration Optimization (30 minutes)

```bash
# 1. Create indexes for performance
docker-compose exec postgres psql -U ${POSTGRES_USER} -d ${POSTGRES_DATABASE} << 'EOF'
-- Standard indexes
CREATE INDEX IF NOT EXISTS idx_analyzer_user_created 
ON analyzer_sessions(user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_chatbot_user_created 
ON chatbot_sessions(user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_evaluator_user_created 
ON evaluator_sessions(user_id, created_at DESC);

-- GIN indexes for JSONB (CRITICAL for performance!)
CREATE INDEX IF NOT EXISTS idx_analyzer_sections 
ON analyzer_sessions USING GIN (sections);

CREATE INDEX IF NOT EXISTS idx_chatbot_context 
ON chatbot_messages USING GIN (context_data);

CREATE INDEX IF NOT EXISTS idx_evaluator_internal 
ON evaluator_sessions USING GIN (internal_analysis);

CREATE INDEX IF NOT EXISTS idx_evaluator_external 
ON evaluator_sessions USING GIN (external_analysis);

CREATE INDEX IF NOT EXISTS idx_evaluator_delta 
ON evaluator_sessions USING GIN (delta_analysis);

-- Analyze tables for query optimization
ANALYZE analyzer_sessions;
ANALYZE analyzer_followups;
ANALYZE analyzer_feedback;
ANALYZE chatbot_sessions;
ANALYZE chatbot_messages;
ANALYZE evaluator_sessions;
ANALYZE evaluator_followups;
ANALYZE evaluator_feedback;
ANALYZE organizations;
ANALYZE org_guidelines;
ANALYZE users;
ANALYZE api_keys;
ANALYZE prompts_master;

\echo '✅ All indexes created and tables analyzed'
EOF

# 2. Check index usage
docker-compose exec postgres psql -U ${POSTGRES_USER} -d ${POSTGRES_DATABASE} << 'EOF'
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan AS scans,
    idx_tup_read AS tuples_read
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;
EOF

# 3. Check database statistics
docker-compose exec postgres psql -U ${POSTGRES_USER} -d ${POSTGRES_DATABASE} << 'EOF'
-- Database size
SELECT pg_size_pretty(pg_database_size(current_database()));

-- Table sizes
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
    pg_total_relation_size(schemaname||'.'||tablename) AS bytes
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY bytes DESC;

-- Cache hit ratio (should be >99%)
SELECT 
    sum(heap_blks_hit) / (sum(heap_blks_hit) + sum(heap_blks_read)) * 100 AS cache_hit_ratio
FROM pg_statio_user_tables;
EOF
```

---

## 🔄 Rollback Procedure

If anything goes wrong:

```bash
# 1. STOP immediately
# Do not proceed if validation fails

# 2. Clear PostgreSQL data
docker-compose exec postgres psql -U ${POSTGRES_USER} -d ${POSTGRES_DATABASE} << 'EOF'
-- Truncate all tables (fast, preserves structure)
TRUNCATE TABLE analyzer_feedback, analyzer_followups, analyzer_sessions CASCADE;
TRUNCATE TABLE chatbot_messages, chatbot_sessions CASCADE;
TRUNCATE TABLE evaluator_feedback, evaluator_followups, evaluator_sessions CASCADE;
TRUNCATE TABLE org_guidelines, organizations CASCADE;
TRUNCATE TABLE users, api_keys, prompts_master CASCADE;
EOF

# 3. Fix issues in migration script

# 4. Re-run migration from Phase 3
python3 migrate_mysql_to_postgres.py

# 5. Re-validate
python3 validate_migration.py
```

---

## 📊 Post-Migration Checklist

After successful migration and validation:

- [ ] All row counts match
- [ ] Foreign key integrity verified
- [ ] Spot checks passed
- [ ] JSON columns validated
- [ ] Indexes created
- [ ] Tables analyzed
- [ ] Cache hit ratio >99%
- [ ] Migration logs saved
- [ ] Results documented
- [ ] Team notified
- [ ] MySQL kept running as backup (2 weeks)

---

## 🆘 Troubleshooting

### Issue: "Connection refused"
```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# Check PostgreSQL logs
docker-compose logs postgres

# Test connection
docker-compose exec postgres pg_isready -U ${POSTGRES_USER}
```

### Issue: "Row count mismatch"
```bash
# Compare specific table
mysql -h ${MYSQL_HOST} -u ${MYSQL_USER} -p${MYSQL_PASSWORD} ${MYSQL_DATABASE} \
  -e "SELECT COUNT(*) FROM analyzer_sessions;"

docker-compose exec postgres psql -U ${POSTGRES_USER} -d ${POSTGRES_DATABASE} \
  -c "SELECT COUNT(*) FROM analyzer_sessions;"

# If counts differ, check for:
# 1. Duplicate session_ids (should cause ON CONFLICT DO NOTHING)
# 2. NULL primary keys (should fail)
# 3. Encoding issues
```

### Issue: "Invalid JSON in JSONB column"
```bash
# Find invalid JSON
docker-compose exec postgres psql -U ${POSTGRES_USER} -d ${POSTGRES_DATABASE} << 'EOF'
SELECT session_id, sections
FROM analyzer_sessions
WHERE sections IS NOT NULL
AND jsonb_typeof(sections) IS NULL;
EOF

# Fix in MySQL first, then re-migrate that table
```

### Issue: "Foreign key violation"
```bash
# Find orphaned records
docker-compose exec postgres psql -U ${POSTGRES_USER} -d ${POSTGRES_DATABASE} << 'EOF'
SELECT session_id
FROM analyzer_followups
WHERE session_id NOT IN (SELECT session_id FROM analyzer_sessions);
EOF

# Option 1: Fix in MySQL and re-migrate
# Option 2: Delete orphaned records in PostgreSQL
```

---

## 📝 Documentation Template

After migration, document the results:

```markdown
# Migration Report

**Date:** YYYY-MM-DD
**Duration:** X hours
**Status:** SUCCESS / PARTIAL / FAILED

## Summary
- Total tables migrated: X
- Total rows migrated: X
- Data volume: X MB
- Issues encountered: X

## Tables Migrated
| Table | MySQL Rows | PostgreSQL Rows | Status |
|-------|------------|-----------------|--------|
| analyzer_sessions | X | X | ✅ |
| ... | ... | ... | ... |

## Validation Results
- Row counts: ✅ PASS
- Foreign keys: ✅ PASS
- Data ranges: ✅ PASS
- JSON columns: ✅ PASS
- Spot checks: ✅ PASS

## Issues & Resolutions
None / List any issues encountered and how they were resolved

## Next Steps
1. Keep MySQL running for 2 weeks as backup
2. Monitor PostgreSQL performance
3. Scheduled decommission date: YYYY-MM-DD
```

---

## ✅ Success Criteria

Migration is successful when:

1. ✅ All tables migrated with matching row counts
2. ✅ All validation checks passed
3. ✅ Foreign key integrity maintained
4. ✅ JSON columns valid
5. ✅ Indexes created and working
6. ✅ Cache hit ratio >99%
7. ✅ Sample queries return correct results
8. ✅ Application connects successfully
9. ✅ No data corruption detected
10. ✅ Backups saved in multiple locations

---

## 🎯 Final Checklist

Before declaring migration complete:

- [ ] Ran through entire guide
- [ ] All backups created (3+ copies)
- [ ] Backup restoration tested
- [ ] Migration script executed successfully
- [ ] Validation script passed all checks
- [ ] Indexes created
- [ ] Tables analyzed
- [ ] Documentation updated
- [ ] Team notified
- [ ] Application tested against PostgreSQL
- [ ] Performance metrics baseline captured
- [ ] MySQL backup plan confirmed (2 weeks)

**If all checkboxes are checked, migration is COMPLETE! 🎉**

---

**Need help?** Review logs, run validation again, or contact your database administrator.

**Remember:** Keep MySQL running for 2 weeks as a safety net!
