"""
Database wrapper for Streamlit integration.

This module provides a seamless interface between the database and Streamlit,
maintaining backward compatibility while using the database for persistence.
"""

import streamlit as st
from typing import List, Dict, Optional
from database import DerbyDatabase

class StreamlitDatabaseWrapper:
    """Wrapper that integrates database with Streamlit session state."""
    
    def __init__(self):
        """Initialize the database wrapper."""
        if 'db' not in st.session_state:
            st.session_state.db = DerbyDatabase()
        self.db = st.session_state.db
    
    # INITIALIZATION AND LOADING
    def load_state_from_database(self):
        """Load all data from database into Streamlit session state."""
        # Auto-setup: If database is empty and no setup has been done, create default horses
        if (not self.db.get_all_horses() and 
            self.db.get_setting('setup_complete', 'False') == 'False' and
            self.db.get_setting('auto_setup_done', 'False') == 'False'):
            
            # Auto-create 8 horses for live deployment
            self.setup_horses_bulk(8)
            self.db.set_setting('auto_setup_done', 'True')
        
        # Load horses
        st.session_state.horses = self.db.get_all_horses()
        
        # Load bettors (convert to old format for compatibility)
        bettors_from_db = self.db.get_all_bettors()
        st.session_state.bettors = [{"name": b["name"]} for b in bettors_from_db]
        
        # Load settings
        st.session_state.current_race = int(self.db.get_setting('current_race', '1'))
        st.session_state.setup_complete = self.db.get_setting('setup_complete', 'False') == 'True'
        st.session_state.target_horse_count = int(self.db.get_setting('target_horse_count', '0'))
        st.session_state.bettors_setup_complete = self.db.get_setting('bettors_setup_complete', 'False') == 'True'
        st.session_state.target_bettor_count = int(self.db.get_setting('target_bettor_count', '0'))
        st.session_state.total_races = int(self.db.get_setting('total_races', '10'))
        
        # Load races (convert to old format)
        races_from_db = self.db.get_all_races()
        st.session_state.races = []
        
        for race in races_from_db:
            race_data = {
                'race_number': race['race_number'],
                'bettors': st.session_state.bettors.copy()
            }
            
            if race['is_completed']:
                # Get bets for this race
                race_bets = self.db.get_race_bets(race['race_number'])
                
                race_data['results'] = {
                    'first': race['first'],
                    'second': race['second'],
                    'third': race['third'],
                    'timestamp': race['completed_at'],
                    'bettor_bets': race_bets
                }
            
            st.session_state.races.append(race_data)
        
        # Calculate scores (for backward compatibility)
        self.calculate_scores_from_database()
    
    def calculate_scores_from_database(self):
        """Calculate scores from database and store in session state."""
        scoreboard = self.db.calculate_scoreboard()
        st.session_state.scores = {}
        
        for bettor_data in scoreboard:
            st.session_state.scores[bettor_data['bettor_name']] = bettor_data['total_points']
    
    # HORSE OPERATIONS
    def setup_horses_bulk(self, horse_count: int) -> bool:
        """Set up horses in bulk with auto-numbering."""
        horse_numbers = [str(i) for i in range(1, horse_count + 1)]
        success = self.db.add_horses_bulk(horse_numbers)
        
        if success:
            self.db.set_setting('target_horse_count', str(horse_count))
            self.db.set_setting('setup_complete', 'True')
            # Update session state
            st.session_state.horses = horse_numbers
            st.session_state.target_horse_count = horse_count
            st.session_state.setup_complete = True
        
        return success
    
    def add_horse(self, horse_number: str) -> bool:
        """Add a single horse."""
        success = self.db.add_horse(horse_number)
        if success:
            st.session_state.horses.append(horse_number)
        return success
    
    def remove_horse(self, horse_number: str) -> bool:
        """Remove a horse."""
        success = self.db.remove_horse(horse_number)
        if success:
            if horse_number in st.session_state.horses:
                st.session_state.horses.remove(horse_number)
        return success
    
    # BETTOR OPERATIONS
    def add_bettor(self, name: str) -> bool:
        """Add a bettor."""
        bettor_id = self.db.add_bettor(name)
        if bettor_id:
            st.session_state.bettors.append({"name": name})
            st.session_state.scores[name] = 0
            return True
        return False
    
    def remove_bettor(self, name: str) -> bool:
        """Remove a bettor."""
        bettor = self.db.get_bettor_by_name(name)
        if bettor:
            success = self.db.remove_bettor(bettor['id'])
            if success:
                # Update session state
                st.session_state.bettors = [b for b in st.session_state.bettors if b['name'] != name]
                if name in st.session_state.scores:
                    del st.session_state.scores[name]
                return True
        return False
    
    def set_bettor_target_count(self, count: int):
        """Set the target bettor count."""
        self.db.set_setting('target_bettor_count', str(count))
        st.session_state.target_bettor_count = count
    
    def complete_bettor_setup(self):
        """Mark bettor setup as complete."""
        self.db.set_setting('bettors_setup_complete', 'True')
        st.session_state.bettors_setup_complete = True
    
    # RACE OPERATIONS
    def submit_race_results(self, race_number: int, first: str, second: str, third: str, bettor_bets: Dict[str, str]) -> bool:
        """Submit complete race results."""
        # Create race if it doesn't exist
        race = self.db.get_race_by_number(race_number)
        if not race:
            race_id = self.db.create_race(race_number)
            if not race_id:
                return False
        
        # Complete the race
        success = self.db.complete_race(race_number, first, second, third)
        if not success:
            return False
        
        # Add all bets
        success = self.db.add_bets_bulk(race_number, bettor_bets)
        if not success:
            return False
        
        # Update session state
        self.load_state_from_database()
        
        return True
    
    def advance_to_next_race(self):
        """Move to the next race."""
        new_race_number = st.session_state.current_race + 1
        self.db.set_setting('current_race', str(new_race_number))
        st.session_state.current_race = new_race_number
    
    def set_total_races(self, total_races: int):
        """Set the total number of races."""
        self.db.set_setting('total_races', str(total_races))
        st.session_state.total_races = total_races
    
    def get_total_races(self) -> int:
        """Get the total number of races."""
        return st.session_state.get('total_races', 10)
    
    # UTILITY OPERATIONS
    def reset_all_data(self):
        """Reset all data."""
        success = self.db.reset_all_data()
        if success:
            # Reset session state
            st.session_state.horses = []
            st.session_state.bettors = []
            st.session_state.races = []
            st.session_state.current_race = 1
            st.session_state.scores = {}
            st.session_state.setup_complete = False
            st.session_state.target_horse_count = 0
            st.session_state.bettors_setup_complete = False
            st.session_state.target_bettor_count = 0
            st.session_state.total_races = 10
        return success
    
    def reset_horses_only(self):
        """Reset only horses."""
        # Check if bettors exist
        if st.session_state.bettors:
            return False, "Cannot reset horses while bettors exist"
        
        # Delete all horses
        horses_to_delete = self.db.get_all_horses()
        for horse in horses_to_delete:
            self.db.remove_horse(horse)
        
        # Reset settings
        self.db.set_setting('setup_complete', 'False')
        self.db.set_setting('target_horse_count', '0')
        
        # Update session state
        st.session_state.horses = []
        st.session_state.setup_complete = False
        st.session_state.target_horse_count = 0
        
        return True, "Horses reset successfully"
    
    def reset_bettors_only(self):
        """Reset only bettors."""
        # Check if races have results
        completed_races = [r for r in st.session_state.races if 'results' in r]
        if completed_races:
            return False, "Cannot reset bettors while races have results"
        
        # Delete all bettors
        bettors_to_delete = self.db.get_all_bettors()
        for bettor in bettors_to_delete:
            self.db.remove_bettor(bettor['id'])
        
        # Reset settings
        self.db.set_setting('bettors_setup_complete', 'False')
        self.db.set_setting('target_bettor_count', '0')
        
        # Update session state
        st.session_state.bettors = []
        st.session_state.bettors_setup_complete = False
        st.session_state.target_bettor_count = 0
        st.session_state.scores = {}
        
        return True, "Bettors reset successfully"
    
    def get_scoreboard_data(self) -> List[Dict]:
        """Get formatted scoreboard data for display."""
        return self.db.calculate_scoreboard()
    
    def export_data(self) -> Dict:
        """Export data in the old JSON format for compatibility."""
        return {
            'horses': self.db.get_all_horses(),
            'bettors': [{"name": b["name"]} for b in self.db.get_all_bettors()],
            'races': st.session_state.races,  # Use session state for compatibility
            'scores': st.session_state.scores,
            'current_race': st.session_state.current_race,
            'setup_complete': st.session_state.setup_complete,
            'target_horse_count': st.session_state.target_horse_count,
            'bettors_setup_complete': st.session_state.bettors_setup_complete,
            'target_bettor_count': st.session_state.target_bettor_count,
            'total_races': st.session_state.total_races
        }
    
    def get_stats(self) -> Dict:
        """Get system statistics."""
        return self.db.get_stats()

# Global instance
@st.cache_resource
def get_db_wrapper():
    """Get a cached database wrapper instance."""
    return StreamlitDatabaseWrapper()

def initialize_app():
    """Initialize the app by loading data from database."""
    db_wrapper = get_db_wrapper()
    db_wrapper.load_state_from_database() 