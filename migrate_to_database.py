#!/usr/bin/env python3
"""
Migration script to convert Derby Betting System from JSON to Database.

This script will:
1. Backup existing JSON data
2. Create the new database
3. Migrate all data from JSON to database
4. Verify the migration was successful
"""

import os
import shutil
from datetime import datetime
from database import DerbyDatabase

def backup_json_data():
    """Create a backup of the existing JSON file."""
    json_file = "derby_data.json"
    if os.path.exists(json_file):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"derby_data_backup_{timestamp}.json"
        shutil.copy2(json_file, backup_file)
        print(f"✅ Backed up existing data to: {backup_file}")
        return backup_file
    else:
        print("ℹ️  No existing JSON file found - starting fresh")
        return None

def verify_migration(db: DerbyDatabase, backup_file: str = None):
    """Verify that the migration was successful."""
    if not backup_file:
        print("ℹ️  No backup file to verify against - database initialized fresh")
        return True
    
    try:
        import json
        
        # Load original data
        with open(backup_file, 'r') as f:
            original_data = json.load(f)
        
        # Get database stats
        stats = db.get_stats()
        
        # Compare counts
        issues = []
        
        # Check horses
        original_horses = len(original_data.get('horses', []))
        if stats['total_horses'] != original_horses:
            issues.append(f"Horse count mismatch: JSON={original_horses}, DB={stats['total_horses']}")
        
        # Check bettors
        original_bettors = len(original_data.get('bettors', []))
        if stats['total_bettors'] != original_bettors:
            issues.append(f"Bettor count mismatch: JSON={original_bettors}, DB={stats['total_bettors']}")
        
        # Check races
        original_races = len(original_data.get('races', []))
        if stats['total_races'] != original_races:
            issues.append(f"Race count mismatch: JSON={original_races}, DB={stats['total_races']}")
        
        # Check completed races
        original_completed = len([r for r in original_data.get('races', []) if 'results' in r])
        if stats['completed_races'] != original_completed:
            issues.append(f"Completed race count mismatch: JSON={original_completed}, DB={stats['completed_races']}")
        
        if issues:
            print("⚠️  Migration verification found issues:")
            for issue in issues:
                print(f"   • {issue}")
            return False
        else:
            print("✅ Migration verification passed - all data migrated successfully!")
            return True
            
    except Exception as e:
        print(f"❌ Error during verification: {e}")
        return False

def main():
    """Main migration function."""
    print("🏇 Derby Betting System - Database Migration")
    print("=" * 50)
    
    # Step 1: Backup existing data
    print("\n1. Backing up existing data...")
    backup_file = backup_json_data()
    
    # Step 2: Initialize database
    print("\n2. Initializing database...")
    try:
        db = DerbyDatabase()
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize database: {e}")
        return False
    
    # Step 3: Run migration
    print("\n3. Migrating data...")
    try:
        success = db.migrate_from_json()
        if success:
            print("✅ Data migration completed successfully")
        else:
            print("❌ Data migration failed")
            return False
    except Exception as e:
        print(f"❌ Migration error: {e}")
        return False
    
    # Step 4: Verify migration
    print("\n4. Verifying migration...")
    verification_success = verify_migration(db, backup_file)
    
    # Step 5: Display final stats
    print("\n5. Migration Summary:")
    stats = db.get_stats()
    print(f"   • Horses: {stats['total_horses']}")
    print(f"   • Bettors: {stats['total_bettors']}")
    print(f"   • Total Races: {stats['total_races']}")
    print(f"   • Completed Races: {stats['completed_races']}")
    
    # Get current race and setup status
    current_race = db.get_setting('current_race', '1')
    setup_complete = db.get_setting('setup_complete', 'False')
    bettors_setup_complete = db.get_setting('bettors_setup_complete', 'False')
    
    print(f"   • Current Race: {current_race}")
    print(f"   • Setup Complete: {setup_complete}")
    print(f"   • Bettors Setup Complete: {bettors_setup_complete}")
    
    if verification_success:
        print("\n🎉 Migration completed successfully!")
        print("\nNext steps:")
        print("1. Update your main application to use the database")
        print("2. Test the application thoroughly")
        print("3. Remove or rename the old JSON file once you're confident")
        
        if backup_file:
            print(f"4. Keep the backup file ({backup_file}) for safety")
        
        return True
    else:
        print("\n⚠️  Migration completed with issues - please review")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 