import sqlite3
import json
import os
from datetime import datetime
from typing import List, Dict, Optional, Tuple

class DerbyDatabase:
    def __init__(self, db_path: str = "derby_betting.db"):
        """Initialize the database connection and create tables if they don't exist."""
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        """Get a database connection with foreign key support enabled."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
    
    def init_database(self):
        """Create all necessary tables."""
        with self.get_connection() as conn:
            # Horses table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS horses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    number TEXT UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Bettors table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS bettors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Races table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS races (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    race_number INTEGER UNIQUE NOT NULL,
                    first_place_horse TEXT,
                    second_place_horse TEXT,
                    third_place_horse TEXT,
                    completed_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (first_place_horse) REFERENCES horses(number),
                    FOREIGN KEY (second_place_horse) REFERENCES horses(number),
                    FOREIGN KEY (third_place_horse) REFERENCES horses(number)
                )
            """)
            
            # Bets table - stores each bettor's bet for each race
            conn.execute("""
                CREATE TABLE IF NOT EXISTS bets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    bettor_id INTEGER NOT NULL,
                    race_id INTEGER NOT NULL,
                    horse_number TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (bettor_id) REFERENCES bettors(id) ON DELETE CASCADE,
                    FOREIGN KEY (race_id) REFERENCES races(id) ON DELETE CASCADE,
                    FOREIGN KEY (horse_number) REFERENCES horses(number),
                    UNIQUE(bettor_id, race_id)
                )
            """)
            
            # System settings table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
    
    # HORSE OPERATIONS
    def add_horses_bulk(self, horse_numbers: List[str]) -> bool:
        """Add multiple horses at once."""
        try:
            with self.get_connection() as conn:
                conn.executemany(
                    "INSERT OR IGNORE INTO horses (number) VALUES (?)",
                    [(num,) for num in horse_numbers]
                )
                conn.commit()
                return True
        except Exception as e:
            print(f"Error adding horses: {e}")
            return False
    
    def add_horse(self, horse_number: str) -> bool:
        """Add a single horse."""
        try:
            with self.get_connection() as conn:
                conn.execute("INSERT INTO horses (number) VALUES (?)", (horse_number,))
                conn.commit()
                return True
        except sqlite3.IntegrityError:
            return False  # Horse already exists
    
    def get_all_horses(self) -> List[str]:
        """Get all horse numbers."""
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT number FROM horses ORDER BY CAST(number AS INTEGER)")
            return [row[0] for row in cursor.fetchall()]
    
    def remove_horse(self, horse_number: str) -> bool:
        """Remove a horse if not referenced in any bets."""
        try:
            with self.get_connection() as conn:
                conn.execute("DELETE FROM horses WHERE number = ?", (horse_number,))
                conn.commit()
                return True
        except Exception:
            return False
    
    # BETTOR OPERATIONS
    def add_bettor(self, name: str) -> Optional[int]:
        """Add a bettor and return their ID."""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("INSERT INTO bettors (name) VALUES (?)", (name,))
                conn.commit()
                return cursor.lastrowid
        except sqlite3.IntegrityError:
            return None  # Bettor already exists
    
    def get_all_bettors(self) -> List[Dict]:
        """Get all bettors."""
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT id, name FROM bettors ORDER BY name")
            return [{"id": row[0], "name": row[1]} for row in cursor.fetchall()]
    
    def remove_bettor(self, bettor_id: int) -> bool:
        """Remove a bettor and all their bets."""
        try:
            with self.get_connection() as conn:
                conn.execute("DELETE FROM bettors WHERE id = ?", (bettor_id,))
                conn.commit()
                return True
        except Exception:
            return False
    
    def get_bettor_by_name(self, name: str) -> Optional[Dict]:
        """Get bettor by name."""
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT id, name FROM bettors WHERE name = ?", (name,))
            row = cursor.fetchone()
            return {"id": row[0], "name": row[1]} if row else None
    
    # RACE OPERATIONS
    def create_race(self, race_number: int) -> Optional[int]:
        """Create a new race."""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("INSERT INTO races (race_number) VALUES (?)", (race_number,))
                conn.commit()
                return cursor.lastrowid
        except sqlite3.IntegrityError:
            return None  # Race already exists
    
    def complete_race(self, race_number: int, first: str, second: str, third: str) -> bool:
        """Mark a race as completed with results."""
        try:
            with self.get_connection() as conn:
                conn.execute("""
                    UPDATE races 
                    SET first_place_horse = ?, second_place_horse = ?, third_place_horse = ?, 
                        completed_at = CURRENT_TIMESTAMP
                    WHERE race_number = ?
                """, (first, second, third, race_number))
                conn.commit()
                return True
        except Exception:
            return False
    
    def get_race_by_number(self, race_number: int) -> Optional[Dict]:
        """Get race details by race number."""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT id, race_number, first_place_horse, second_place_horse, 
                       third_place_horse, completed_at
                FROM races WHERE race_number = ?
            """, (race_number,))
            row = cursor.fetchone()
            if row:
                return {
                    "id": row[0],
                    "race_number": row[1],
                    "first": row[2],
                    "second": row[3],
                    "third": row[4],
                    "completed_at": row[5],
                    "is_completed": row[5] is not None
                }
            return None
    
    def get_all_races(self) -> List[Dict]:
        """Get all races."""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT id, race_number, first_place_horse, second_place_horse, 
                       third_place_horse, completed_at
                FROM races ORDER BY race_number
            """)
            return [{
                "id": row[0],
                "race_number": row[1],
                "first": row[2],
                "second": row[3],
                "third": row[4],
                "completed_at": row[5],
                "is_completed": row[5] is not None
            } for row in cursor.fetchall()]
    
    # BET OPERATIONS
    def add_bet(self, bettor_id: int, race_id: int, horse_number: str) -> bool:
        """Add a bet for a bettor in a race."""
        try:
            with self.get_connection() as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO bets (bettor_id, race_id, horse_number) 
                    VALUES (?, ?, ?)
                """, (bettor_id, race_id, horse_number))
                conn.commit()
                return True
        except Exception:
            return False
    
    def add_bets_bulk(self, race_number: int, bettor_bets: Dict[str, str]) -> bool:
        """Add multiple bets for a race."""
        try:
            with self.get_connection() as conn:
                # Get race ID
                race = self.get_race_by_number(race_number)
                if not race:
                    return False
                
                # Add all bets
                for bettor_name, horse_number in bettor_bets.items():
                    bettor = self.get_bettor_by_name(bettor_name)
                    if bettor:
                        conn.execute("""
                            INSERT OR REPLACE INTO bets (bettor_id, race_id, horse_number) 
                            VALUES (?, ?, ?)
                        """, (bettor["id"], race["id"], horse_number))
                
                conn.commit()
                return True
        except Exception:
            return False
    
    def get_race_bets(self, race_number: int) -> Dict[str, str]:
        """Get all bets for a specific race."""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT b.name, bets.horse_number
                FROM bets
                JOIN bettors b ON bets.bettor_id = b.id
                JOIN races r ON bets.race_id = r.id
                WHERE r.race_number = ?
            """, (race_number,))
            return {row[0]: row[1] for row in cursor.fetchall()}
    
    # SCORING AND ANALYTICS
    def calculate_scoreboard(self) -> List[Dict]:
        """Calculate current scoreboard with race-by-race breakdown."""
        with self.get_connection() as conn:
            # Get all bettors
            bettors = self.get_all_bettors()
            
            # Initialize scoreboard
            scoreboard = []
            
            for bettor in bettors:
                bettor_data = {
                    "bettor_id": bettor["id"],
                    "bettor_name": bettor["name"],
                    "total_points": 0,
                    "race_scores": {}
                }
                
                # Get points for each race
                cursor = conn.execute("""
                    SELECT r.race_number, r.first_place_horse, r.second_place_horse, 
                           r.third_place_horse, bets.horse_number
                    FROM races r
                    LEFT JOIN bets ON r.id = bets.race_id AND bets.bettor_id = ?
                    WHERE r.completed_at IS NOT NULL
                    ORDER BY r.race_number
                """, (bettor["id"],))
                
                for row in cursor.fetchall():
                    race_num, first, second, third, bet_horse = row
                    points = 0
                    
                    if bet_horse:
                        if bet_horse == first:
                            points = 3
                        elif bet_horse == second:
                            points = 2
                        elif bet_horse == third:
                            points = 1
                    
                    bettor_data["race_scores"][f"Race {race_num}"] = points
                    bettor_data["total_points"] += points
                
                scoreboard.append(bettor_data)
            
            # Sort by total points (descending)
            scoreboard.sort(key=lambda x: x["total_points"], reverse=True)
            
            # Add ranks
            for i, bettor in enumerate(scoreboard):
                bettor["rank"] = i + 1
            
            return scoreboard
    
    # SETTINGS
    def set_setting(self, key: str, value: str) -> bool:
        """Set a system setting."""
        try:
            with self.get_connection() as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO settings (key, value, updated_at) 
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                """, (key, value))
                conn.commit()
                return True
        except Exception:
            return False
    
    def get_setting(self, key: str, default: str = "") -> str:
        """Get a system setting."""
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT value FROM settings WHERE key = ?", (key,))
            row = cursor.fetchone()
            return row[0] if row else default
    
    # MIGRATION FROM JSON
    def migrate_from_json(self, json_file: str = "derby_data.json") -> bool:
        """Migrate existing JSON data to database."""
        if not os.path.exists(json_file):
            return True  # No file to migrate
        
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
            
            # Migrate horses
            if 'horses' in data:
                self.add_horses_bulk(data['horses'])
            
            # Migrate bettors
            if 'bettors' in data:
                for bettor in data['bettors']:
                    self.add_bettor(bettor['name'])
            
            # Migrate races and results
            if 'races' in data:
                for race in data['races']:
                    race_id = self.create_race(race['race_number'])
                    
                    if 'results' in race:
                        # Complete the race
                        self.complete_race(
                            race['race_number'],
                            race['results']['first'],
                            race['results']['second'],
                            race['results']['third']
                        )
                        
                        # Add bets
                        if 'bettor_bets' in race['results']:
                            self.add_bets_bulk(race['race_number'], race['results']['bettor_bets'])
            
            # Migrate settings
            settings_to_migrate = [
                'current_race', 'setup_complete', 'target_horse_count',
                'bettors_setup_complete', 'target_bettor_count'
            ]
            
            for setting in settings_to_migrate:
                if setting in data:
                    self.set_setting(setting, str(data[setting]))
            
            return True
            
        except Exception as e:
            print(f"Migration error: {e}")
            return False
    
    # UTILITY METHODS
    def get_stats(self) -> Dict:
        """Get system statistics."""
        with self.get_connection() as conn:
            stats = {}
            
            # Count horses
            cursor = conn.execute("SELECT COUNT(*) FROM horses")
            stats['total_horses'] = cursor.fetchone()[0]
            
            # Count bettors
            cursor = conn.execute("SELECT COUNT(*) FROM bettors")
            stats['total_bettors'] = cursor.fetchone()[0]
            
            # Count races
            cursor = conn.execute("SELECT COUNT(*) FROM races")
            stats['total_races'] = cursor.fetchone()[0]
            
            # Count completed races
            cursor = conn.execute("SELECT COUNT(*) FROM races WHERE completed_at IS NOT NULL")
            stats['completed_races'] = cursor.fetchone()[0]
            
            return stats
    
    def reset_all_data(self) -> bool:
        """Reset all data (for testing/reset functionality)."""
        try:
            with self.get_connection() as conn:
                # Delete in correct order to respect foreign keys
                conn.execute("DELETE FROM bets")
                conn.execute("DELETE FROM races")
                conn.execute("DELETE FROM bettors")
                conn.execute("DELETE FROM horses")
                conn.execute("DELETE FROM settings")
                conn.commit()
                return True
        except Exception:
            return False 