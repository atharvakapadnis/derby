import streamlit as st
import pandas as pd
from datetime import datetime
import json
import os
from db_wrapper import get_db_wrapper, initialize_app

# Page configuration
st.set_page_config(
    page_title="Derby Betting System",
    page_icon="🏇",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database and load state
initialize_app()

# Get database wrapper instance
db = get_db_wrapper()

# Initialize session state variables (for UI compatibility)
if 'horses' not in st.session_state:
    st.session_state.horses = []
if 'bettors' not in st.session_state:
    st.session_state.bettors = []
if 'races' not in st.session_state:
    st.session_state.races = []
if 'current_race' not in st.session_state:
    st.session_state.current_race = 1
if 'scores' not in st.session_state:
    st.session_state.scores = {}
if 'setup_complete' not in st.session_state:
    st.session_state.setup_complete = False
if 'target_horse_count' not in st.session_state:
    st.session_state.target_horse_count = 0
if 'bettors_setup_complete' not in st.session_state:
    st.session_state.bettors_setup_complete = False
if 'target_bettor_count' not in st.session_state:
    st.session_state.target_bettor_count = 0

# Initialize authentication session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user_role' not in st.session_state:
    st.session_state.user_role = None
if 'total_races' not in st.session_state:
    st.session_state.total_races = 10

# Hardcoded credentials (in production, these should be stored securely)
ADMIN_CREDENTIALS = {
    "admin": "derby2024",
    "organizer": "racing123"
}

def check_credentials(username: str, password: str) -> tuple[bool, str]:
    """Check if credentials are valid and return user role."""
    if username in ADMIN_CREDENTIALS and ADMIN_CREDENTIALS[username] == password:
        return True, "admin"
    return False, None

def login_page():
    """Display login page."""
    st.title("🏇 Derby Betting System - Login")
    st.markdown("---")
    
    # Center the login form
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.subheader("Admin Login")
        st.info("Enter your credentials to access the admin dashboard")
        
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            
            col_a, col_b, col_c = st.columns([1, 2, 1])
            with col_b:
                login_button = st.form_submit_button("🔑 Login", use_container_width=True, type="primary")
            
            if login_button:
                is_valid, role = check_credentials(username, password)
                
                if is_valid:
                    st.session_state.authenticated = True
                    st.session_state.user_role = role
                    st.success("Login successful! Redirecting...")
                    st.rerun()
                else:
                    st.error("Invalid username or password")
        
        st.markdown("---")
        
        # Public scoreboard access
        st.subheader("View Public Scoreboard")
        st.info("No login required to view current standings")
        
        if st.button("📊 View Scoreboard", use_container_width=True):
            st.session_state.user_role = "viewer"
            st.rerun()

def logout():
    """Handle user logout."""
    st.session_state.authenticated = False
    st.session_state.user_role = None
    st.rerun()

def show_user_scoreboard():
    """Display simplified view-only scoreboard for regular users."""
    st.title("🏇 Derby Betting System - Live Scoreboard")
    st.markdown("---")
    
    # Add a login link for admins
    col1, col2, col3 = st.columns([2, 1, 1])
    with col3:
        if st.button("🔑 Admin Login"):
            st.session_state.user_role = None
            st.rerun()
    
    # Display simplified scoreboard
    display_simple_scoreboard()
    
    # Add refresh functionality
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("🔄 Refresh Scoreboard", use_container_width=True):
            st.rerun()

def display_simple_scoreboard():
    """Display a simplified scoreboard showing only total scores."""
    import pandas as pd
    
    if not st.session_state.bettors:
        st.info("No bettors added yet.")
        return
    
    st.markdown("## 🏆 Current Standings")
    
    # Get basic race info
    completed_races = len([r for r in st.session_state.races if 'results' in r])
    total_bettors = len(st.session_state.bettors)
    
    # Show key stats
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Participants", total_bettors)
    with col2:
        st.metric("Races Completed", f"{completed_races}/{st.session_state.total_races}")
    with col3:
        if completed_races > 0:
            st.metric("Progress", f"{int((completed_races / st.session_state.total_races) * 100)}%")
        else:
            st.metric("Status", "Starting Soon")
    
    st.markdown("---")
    
    # Calculate total scores for each bettor
    bettor_scores = []
    for bettor in st.session_state.bettors:
        total_points = 0
        bettor_name = bettor['name']
        
        # Calculate points from completed races
        for race in st.session_state.races:
            if 'results' in race:
                bet_horse = race['results']['bettor_bets'].get(bettor_name, None)
                if bet_horse == race['results']['first']:
                    total_points += 3
                elif bet_horse == race['results']['second']:
                    total_points += 2
                elif bet_horse == race['results']['third']:
                    total_points += 1
        
        bettor_scores.append({
            'Name': bettor_name,
            'Total Points': total_points
        })
    
    # Sort by points (descending)
    bettor_scores.sort(key=lambda x: x['Total Points'], reverse=True)
    
    # Add rank
    for i, bettor in enumerate(bettor_scores):
        bettor['Rank'] = i + 1
    
    # Create DataFrame
    df = pd.DataFrame(bettor_scores)
    df = df[['Rank', 'Name', 'Total Points']]  # Reorder columns
    
    # Search functionality
    search_term = st.text_input("🔍 Search for your name:", key="simple_search")
    
    # Filter if search term provided
    if search_term:
        filtered_df = df[df['Name'].str.contains(search_term, case=False, na=False)]
        if not filtered_df.empty:
            st.markdown(f"### 📍 Search Results for '{search_term}':")
            st.dataframe(
                filtered_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Rank": st.column_config.NumberColumn("Rank", width="small"),
                    "Name": st.column_config.TextColumn("Name", width="medium"),
                    "Total Points": st.column_config.NumberColumn("Points", width="small")
                }
            )
        else:
            st.warning(f"No results found for '{search_term}'")
        
        st.markdown("---")
    
    # Show top performers in table format
    st.markdown("### 🥇 Top 10 Leaderboard")
    top_10 = df.head(10)
    
    if not top_10.empty:
        st.dataframe(
            top_10,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Rank": st.column_config.NumberColumn("Rank", width="small"),
                "Name": st.column_config.TextColumn("Name", width="medium"),
                "Total Points": st.column_config.NumberColumn("Points", width="small")
            }
        )
    
    # Show all standings in expandable section
    if len(df) > 10:
        with st.expander(f"📊 View All {len(df)} Participants", expanded=False):
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Rank": st.column_config.NumberColumn("Rank", width="small"),
                    "Name": st.column_config.TextColumn("Name", width="medium"),
                    "Total Points": st.column_config.NumberColumn("Points", width="small")
                },
                height=400
            )
    
    # Race completion status
    if completed_races < st.session_state.total_races:
        st.markdown("---")
        st.info(f"🏁 {st.session_state.total_races - completed_races} races remaining. Check back for updates!")
    else:
        st.markdown("---")
        st.success(f"🏆 All {st.session_state.total_races} races completed! Final results above.")

def display_scoreboard():
    """Display the scoreboard as a table with all races - optimized for large numbers of bettors"""
    import pandas as pd
    
    if not st.session_state.bettors:
        st.info("No bettors added yet.")
        return
    
    st.markdown("## 🏆 Scoreboard")
    
    # Scoreboard options and filters
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        search_term = st.text_input("🔍 Search bettors:", key="scoreboard_search")
    
    with col2:
        show_all_races = st.checkbox("Show all races", value=True, key="show_all_races")
        
    with col3:
        bettors_per_page = st.selectbox("Bettors per page:", [10, 25, 50, 100], index=1, key="scoreboard_per_page")
    
    # Create data for the table
    bettor_names = [b['name'] for b in st.session_state.bettors]
    
    # Filter bettors based on search
    if search_term:
        filtered_bettor_names = [name for name in bettor_names if search_term.lower() in name.lower()]
    else:
        filtered_bettor_names = bettor_names
    
    if not filtered_bettor_names:
        st.info("No bettors found matching your search.")
        return
    
    # Initialize the data structure
    table_data = {}
    table_data['Bettor'] = filtered_bettor_names
    
    # Determine which races to show
    if show_all_races:
        races_to_show = range(1, st.session_state.total_races + 1)
    else:
        # Only show completed races
        completed_race_numbers = [r['race_number'] for r in st.session_state.races if 'results' in r]
        races_to_show = completed_race_numbers if completed_race_numbers else [1]
    
    # Add columns for races
    for race_num in races_to_show:
        race_col = f"R{race_num}"  # Shorter column names for mobile
        table_data[race_col] = []
        
        # Find if this race has been completed
        completed_race = None
        for race in st.session_state.races:
            if race.get('race_number') == race_num and 'results' in race:
                completed_race = race
                break
        
        # For each bettor, determine their points in this race
        for bettor_name in filtered_bettor_names:
            if completed_race:
                points = 0
                bet_horse = completed_race['results']['bettor_bets'].get(bettor_name, None)
                if bet_horse == completed_race['results']['first']:
                    points = 3
                elif bet_horse == completed_race['results']['second']:
                    points = 2
                elif bet_horse == completed_race['results']['third']:
                    points = 1
                table_data[race_col].append(points)
            else:
                # Race not completed yet, show blank
                table_data[race_col].append("")
    
    # Calculate total points (only from completed races)
    total_points = []
    for i, bettor_name in enumerate(filtered_bettor_names):
        total = 0
        for col in table_data.keys():
            if col.startswith('R') and table_data[col][i] != "":
                total += table_data[col][i]
        total_points.append(total)
    table_data['Total'] = total_points
    
    # Create DataFrame
    df = pd.DataFrame(table_data)
    
    # Sort by total points (descending), then by name for ties
    df = df.sort_values(['Total', 'Bettor'], ascending=[False, True]).reset_index(drop=True)
    
    # Add rank column
    df.insert(0, 'Rank', range(1, len(df) + 1))
    
    # Statistics
    total_bettors = len(filtered_bettor_names)
    completed_races = len([r for r in st.session_state.races if 'results' in r])
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Bettors", f"{total_bettors}/{len(bettor_names)}")
    with col2:
        st.metric("Races Complete", f"{completed_races}/{st.session_state.total_races}")
    with col3:
        if total_points:
            leader_points = max(total_points)
            st.metric("Leading Score", leader_points)
    with col4:
        if total_points:
            avg_score = sum(total_points) / len(total_points)
            st.metric("Average Score", f"{avg_score:.1f}")
    
    st.markdown("---")
    
    # Pagination
    total_filtered = len(df)
    if total_filtered > bettors_per_page:
        total_pages = (total_filtered - 1) // bettors_per_page + 1
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            page_num = st.selectbox(
                "Page", 
                range(1, total_pages + 1), 
                key="scoreboard_page",
                format_func=lambda x: f"Page {x} of {total_pages}"
            ) - 1
        
        start_idx = page_num * bettors_per_page
        end_idx = min(start_idx + bettors_per_page, total_filtered)
        page_df = df.iloc[start_idx:end_idx].copy()
        
        st.caption(f"Showing {start_idx + 1}-{end_idx} of {total_filtered} bettors")
    else:
        page_df = df
        st.caption(f"Showing all {total_filtered} bettors")
    
    # Configure column display
    column_config = {
        "Rank": st.column_config.NumberColumn(
            "Rank",
            help="Current position",
            format="%d",
            width="small"
        ),
        "Bettor": st.column_config.TextColumn(
            "Bettor",
            help="Bettor name",
            width="medium"
        ),
        "Total": st.column_config.NumberColumn(
            "Total",
            help="Total points from all races",
            format="%d",
            width="small"
        )
    }
    
    # Configure race columns
    for col in page_df.columns:
        if col.startswith('R'):
            column_config[col] = st.column_config.NumberColumn(
                col,
                help=f"Points from {col.replace('R', 'Race ')}",
                format="%d",
                width="small"
            )
    
    # Display the table
    st.dataframe(
        page_df,
        use_container_width=True,
        hide_index=True,
        column_config=column_config
    )
    
    # Additional views
    with st.expander("📊 Additional Views", expanded=False):
        view_tab1, view_tab2, view_tab3 = st.tabs(["🏆 Top 10", "📈 Race Breakdown", "📋 Full List"])
        
        with view_tab1:
            st.subheader("Top 10 Leaderboard")
            top_10 = df.head(10)
            
            # Medal emojis for top 3
            for i, row in top_10.iterrows():
                rank = row['Rank']
                name = row['Bettor']
                score = row['Total']
                
                if rank == 1:
                    st.success(f"🥇 **{name}** - {score} points")
                elif rank == 2:
                    st.info(f"🥈 **{name}** - {score} points")
                elif rank == 3:
                    st.warning(f"🥉 **{name}** - {score} points")
                else:
                    st.write(f"**{rank}.** {name} - {score} points")
        
        with view_tab2:
            st.subheader("Points by Race")
            if completed_races > 0:
                # Show race-by-race statistics
                race_stats = {}
                for race_num in range(1, completed_races + 1):
                    race_col = f"R{race_num}"
                    if race_col in df.columns:
                        points_this_race = [p for p in df[race_col] if p != ""]
                        if points_this_race:
                            race_stats[f"Race {race_num}"] = {
                                "Winners (3pts)": sum(1 for p in points_this_race if p == 3),
                                "Second (2pts)": sum(1 for p in points_this_race if p == 2),
                                "Third (1pt)": sum(1 for p in points_this_race if p == 1),
                                "No points": sum(1 for p in points_this_race if p == 0)
                            }
                
                if race_stats:
                    stats_df = pd.DataFrame(race_stats).T
                    st.dataframe(stats_df, use_container_width=True)
            else:
                st.info("No completed races yet.")
        
        with view_tab3:
            st.subheader("Complete Scoreboard")
            # Show full table without pagination
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
                column_config=column_config,
                height=600  # Fixed height with scrolling
            )
    
    # Export options
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📋 Copy Leaderboard"):
            leaderboard_text = "DERBY LEADERBOARD\n" + "="*20 + "\n"
            for i, row in df.iterrows():
                leaderboard_text += f"{row['Rank']}. {row['Bettor']} - {row['Total']} pts\n"
            st.code(leaderboard_text, language=None)
    
    with col2:
        # Export to CSV
        csv = df.to_csv(index=False)
        st.download_button(
            label="📊 Download CSV",
            data=csv,
            file_name=f"derby_scoreboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    
    with col3:
        # Export detailed results
        if st.button("📤 Export Detailed"):
            detailed_data = {
                "summary": {
                    "total_bettors": len(bettor_names),
                    "completed_races": completed_races,
                    "timestamp": datetime.now().isoformat()
                },
                "scoreboard": df.to_dict('records'),
                "race_results": [race for race in st.session_state.races if 'results' in race]
            }
            
            import json
            st.download_button(
                label="Download JSON",
                data=json.dumps(detailed_data, indent=2),
                file_name=f"derby_detailed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )

# Check authentication and route to appropriate page
if st.session_state.user_role == "viewer":
    # Show public scoreboard only
    show_user_scoreboard()
    st.stop()
elif not st.session_state.authenticated:
    # Show login page
    login_page()
    st.stop()

# From here on, user is authenticated as admin
# Prompt for horse entry if setup not complete
if not st.session_state.setup_complete:
    st.title("🏇 Derby Betting System - Setup Horses")
    st.markdown("---")
    st.info("Select the number of horses for this event. Horse numbers will be automatically assigned (1, 2, 3, etc.).")
    
    # Horse count selection and auto-assignment
    st.subheader("Select Number of Horses")
    horse_count = st.number_input("How many horses do you want for this event?", min_value=2, max_value=20, value=8, step=1)
    
    if st.button("✅ Set Up Horses"):
        # Auto-assign horse numbers based on count using database
        success = db.setup_horses_bulk(horse_count)
        if success:
            st.success(f"Successfully set up {horse_count} horses with numbers 1 through {horse_count}!")
            st.rerun()
        else:
            st.error("Failed to set up horses. Please try again.")
    
    # Show preview of what will be created
    if horse_count > 0:
        st.markdown("### Preview - Horses that will be created:")
        preview_horses = [str(i) for i in range(1, horse_count + 1)]
        cols = st.columns(min(5, len(preview_horses)))  # Max 5 columns
        for i, horse_num in enumerate(preview_horses):
            with cols[i % 5]:
                st.write(f"Horse #{horse_num}")
    
    st.stop()

# Check if bettor setup is needed after horse setup is complete
if st.session_state.setup_complete and not st.session_state.bettors_setup_complete:
    st.title("🏇 Derby Betting System - Setup Bettors")
    st.markdown("---")
    st.info("Great! Horses are set up. Now let's add the bettors for this event.")
    
    # Bettor count selection
    if st.session_state.target_bettor_count == 0:
        st.subheader("Step 1: Select Number of Bettors")
        bettor_count = st.number_input("How many bettors do you want to add?", min_value=2, max_value=50, value=6, step=1)
        if st.button("Set Bettor Count"):
            db.set_bettor_target_count(bettor_count)
            st.rerun()
        st.stop()
    
    st.subheader(f"Step 2: Add Bettors ({len(st.session_state.bettors)}/{st.session_state.target_bettor_count})")
    st.progress(len(st.session_state.bettors) / st.session_state.target_bettor_count)
    
    # Add bettor form
    col1, col2 = st.columns([3, 1])
    with col1:
        bettor_name = st.text_input("Bettor Name", key="main_setup_bettor_name")
    with col2:
        if st.button("Add Bettor", key="main_setup_add_bettor"):
            if not bettor_name:
                st.error("Bettor name is required.")
            elif bettor_name in [b['name'] for b in st.session_state.bettors]:
                st.error("Bettor already exists.")
            else:
                success = db.add_bettor(bettor_name)
                if success:
                    st.success(f"Added bettor: {bettor_name}")
                    st.rerun()
                else:
                    st.error("Failed to add bettor. They may already exist.")
    
    if st.session_state.bettors:
        st.markdown("### Current Bettors:")
        for b in st.session_state.bettors:
            st.write(f"• {b['name']}")
        
        st.markdown("---")
        
        # Only show Done button if target count is reached
        if len(st.session_state.bettors) >= st.session_state.target_bettor_count:
            if st.button("✅ Done Adding Bettors - Proceed to Dashboard"):
                db.complete_bettor_setup()
                st.rerun()
        else:
            remaining = st.session_state.target_bettor_count - len(st.session_state.bettors)
            st.warning(f"Please add {remaining} more bettor(s) to reach your target of {st.session_state.target_bettor_count}.")
        
        if st.button("🔄 Reset Bettors"):
            success, message = db.reset_bettors_only()
            if success:
                st.success(message)
            else:
                st.error(message)
            st.rerun()
    st.stop()

# Main title
st.title("🏇 Derby Betting System")
st.markdown("---")

# Sidebar for navigation
st.sidebar.title("Navigation")

# Show logout button for authenticated users
if st.session_state.authenticated:
    st.sidebar.markdown("---")
    st.sidebar.write(f"👤 Logged in as: **{st.session_state.user_role}**")
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        logout()

page = st.sidebar.selectbox(
    "Choose a page:",
    ["🏠 Dashboard", "🐎 Horse Management", "👥 Manage Bettors", "🏁 Race Management", "📊 Scoreboard", "⚙️ Settings"]
)

if page == "🏠 Dashboard":
    st.header("Dashboard")
    
    # Key metrics in mobile-friendly layout
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
    
    with col1:
        st.metric("Horses", len(st.session_state.horses))
    
    with col2:
        st.metric("Bettors", len(st.session_state.bettors))
    
    with col3:
        completed_races = len([r for r in st.session_state.races if 'results' in r])
        st.metric("Races Done", f"{completed_races}/{st.session_state.total_races}")
    
    with col4:
        if st.session_state.bettors:
            leader_score = max(st.session_state.scores.values()) if st.session_state.scores else 0
            st.metric("Top Score", leader_score)
        else:
            st.metric("Top Score", 0)
    
    st.markdown("---")
    
    # Current race status
    if st.session_state.bettors_setup_complete:
        if completed_races < st.session_state.total_races:
            current_race_completed = any(r.get('race_number') == st.session_state.current_race and 'results' in r 
                                       for r in st.session_state.races)
            
            if current_race_completed:
                st.success(f"✅ Race {st.session_state.current_race} completed! Ready for Race {st.session_state.current_race + 1}")
            else:
                st.info(f"🏁 Current Race: **{st.session_state.current_race}** - Ready for results entry")
        else:
            st.success("🏆 All races completed! Check the final scoreboard!")
    else:
        if not st.session_state.setup_complete:
            st.warning("⚠️ Setup needed: Add horses first")
        else:
            st.warning("⚠️ Setup needed: Add bettors")
    
    st.markdown("---")
    
    # Quick actions - responsive layout
    st.subheader("Quick Actions")
    
    # Mobile-friendly button layout
    if len(st.session_state.bettors) > 20:
        # Large scale - show management-focused actions
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🏁 Manage Current Race", use_container_width=True):
                st.rerun()
            
            if st.button("👥 Manage Bettors", use_container_width=True):
                st.rerun()
        
        with col2:
            if st.button("📊 View Scoreboard", use_container_width=True):
                st.rerun()
            
            if st.button("⚙️ Settings & Export", use_container_width=True):
                st.rerun()
    else:
        # Smaller scale - show all actions
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🐎 Manage Horses", use_container_width=True):
                st.rerun()
        
        with col2:
            if st.button("👥 Add Bettors", use_container_width=True):
                st.rerun()
        
        with col3:
            if st.button("🏁 Manage Race", use_container_width=True):
                st.rerun()
    
    # Recent activity
    st.markdown("---")
    st.subheader("Recent Activity")
    
    if st.session_state.races:
        recent_races = st.session_state.races[-3:]  # Show last 3 races
        for race in recent_races:
            if 'results' in race:
                # Mobile-friendly race result display
                with st.container():
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        st.write(f"**Race {race['race_number']}**")
                        st.caption(f"🥇 #{race['results']['first']} | 🥈 #{race['results']['second']} | 🥉 #{race['results']['third']}")
                    with col2:
                        # Show how many bettors got points
                        bettor_bets = race['results']['bettor_bets']
                        winners = sum(1 for bet in bettor_bets.values() if bet in [race['results']['first'], race['results']['second'], race['results']['third']])
                        st.metric("Winners", f"{winners}/{len(bettor_bets)}")
    else:
        st.info("No races completed yet.")
    
    # System status for large-scale events
    if len(st.session_state.bettors) >= 20:
        st.markdown("---")
        st.subheader("📈 System Status")
        
        col1, col2 = st.columns(2)
        with col1:
            st.success("✅ Large-scale event mode active")
            st.info(f"Managing {len(st.session_state.bettors)} bettors efficiently")
        
        with col2:
            if completed_races > 0:
                avg_bet_completion = sum(len(r['results']['bettor_bets']) for r in st.session_state.races if 'results' in r) / completed_races
                st.metric("Avg Participation", f"{avg_bet_completion:.0f}/{len(st.session_state.bettors)}")
            else:
                st.metric("System Scale", "Enterprise Ready")

# Horse Management page
elif page == "🐎 Horse Management":
    st.header("Horse Management")
    
    # Add new horse
    st.subheader("Add New Horse")
    with st.form("add_horse_management"):
        horse_number = st.text_input("Horse Number", key="mgmt_horse_number")
        add_horse_btn = st.form_submit_button("Add Horse")
        if add_horse_btn:
            if not horse_number:
                st.error("Horse number is required.")
            elif horse_number in st.session_state.horses:
                st.error("Horse number must be unique.")
            else:
                success = db.add_horse(horse_number)
                if success:
                    st.success(f"Added horse #{horse_number}")
                    st.rerun()
                else:
                    st.error("Failed to add horse. It may already exist.")
    
    st.markdown("---")
    
    # Display and manage current horses
    st.subheader("Current Horses")
    if st.session_state.horses:
        for i, horse in enumerate(st.session_state.horses):
            col1, col2 = st.columns([2, 1])
            with col1:
                st.write(f"**#{horse}**")
            with col2:
                if st.button(f"Remove", key=f"remove_horse_{i}"):
                    success = db.remove_horse(horse)
                    if success:
                        st.success(f"Removed horse #{horse}")
                        st.rerun()
                    else:
                        st.error(f"Failed to remove horse #{horse}")
    else:
        st.info("No horses added yet.")

elif page == "👥 Manage Bettors":
    # Check if we need bettor setup first
    if not st.session_state.bettors_setup_complete:
        st.title("🏇 Derby Betting System - Setup Bettors")
        st.markdown("---")
        st.info("Enter the bettors for this event. You can add them individually or in bulk.")
        
        # Bettor count selection
        if st.session_state.target_bettor_count == 0:
            st.subheader("Step 1: Select Number of Bettors")
            bettor_count = st.number_input("How many bettors do you want to add?", min_value=2, max_value=100, value=6, step=1)
            if st.button("Set Bettor Count"):
                db.set_bettor_target_count(bettor_count)
                st.rerun()
            st.stop()
        
        st.subheader(f"Step 2: Add Bettors ({len(st.session_state.bettors)}/{st.session_state.target_bettor_count})")
        st.progress(len(st.session_state.bettors) / st.session_state.target_bettor_count)
        
        # Bulk import section
        with st.expander("📋 Bulk Import Bettors", expanded=len(st.session_state.bettors) == 0):
            st.write("**Option 1: Paste Names (One per line)**")
            bulk_names = st.text_area(
                "Enter bettor names (one per line):",
                placeholder="John Smith\nJane Doe\nMike Johnson\n...",
                height=150,
                key="bulk_bettor_input"
            )
            
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("📥 Import Names", type="primary"):
                    if bulk_names.strip():
                        names = [name.strip() for name in bulk_names.strip().split('\n') if name.strip()]
                        existing_names = [b['name'] for b in st.session_state.bettors]
                        
                        added_count = 0
                        errors = []
                        
                        for name in names:
                            if name not in existing_names:
                                success = db.add_bettor(name)
                                if success:
                                    added_count += 1
                                else:
                                    errors.append(f"Failed to add: {name}")
                            else:
                                errors.append(f"Already exists: {name}")
                        
                        if added_count > 0:
                            st.success(f"Successfully added {added_count} bettors!")
                            st.rerun()
                        if errors:
                            st.warning(f"Issues with {len(errors)} entries")
                            for error in errors[:5]:  # Show first 5 errors
                                st.caption(f"• {error}")
                    else:
                        st.error("Please enter some names")
            
            with col2:
                st.write("**Option 2: Upload CSV File**")
                uploaded_file = st.file_uploader(
                    "Choose CSV file",
                    type=['csv'],
                    help="CSV should have a 'name' column or names in the first column"
                )
                
                if uploaded_file is not None:
                    try:
                        import pandas as pd
                        df = pd.read_csv(uploaded_file)
                        
                        # Try to find name column
                        name_column = None
                        for col in df.columns:
                            if 'name' in col.lower():
                                name_column = col
                                break
                        
                        if name_column is None:
                            name_column = df.columns[0]  # Use first column
                        
                        names = df[name_column].dropna().astype(str).tolist()
                        st.write(f"Found {len(names)} names in file")
                        
                        if st.button("📥 Import from CSV"):
                            existing_names = [b['name'] for b in st.session_state.bettors]
                            added_count = 0
                            
                            for name in names:
                                name = name.strip()
                                if name and name not in existing_names:
                                    success = db.add_bettor(name)
                                    if success:
                                        added_count += 1
                            
                            if added_count > 0:
                                st.success(f"Added {added_count} bettors from CSV!")
                                st.rerun()
                            else:
                                st.warning("No new bettors were added")
                                
                    except Exception as e:
                        st.error(f"Error reading CSV: {str(e)}")
        
        st.markdown("---")
        
        # Individual bettor addition
        st.write("**Add Individual Bettor:**")
        col1, col2 = st.columns([3, 1])
        with col1:
            bettor_name = st.text_input("Bettor Name", key="setup_bettor_name")
        with col2:
            if st.button("Add Bettor", key="setup_add_bettor"):
                if not bettor_name:
                    st.error("Bettor name is required.")
                elif bettor_name in [b['name'] for b in st.session_state.bettors]:
                    st.error("Bettor already exists.")
                else:
                    success = db.add_bettor(bettor_name)
                    if success:
                        st.success(f"Added bettor: {bettor_name}")
                        st.rerun()
                    else:
                        st.error("Failed to add bettor.")
        
        # Current bettors display
        if st.session_state.bettors:
            st.markdown("---")
            st.markdown("### Current Bettors:")
            
            # Search functionality
            search_term = st.text_input("🔍 Search bettors:", key="bettor_search")
            
            # Filter bettors
            filtered_bettors = st.session_state.bettors
            if search_term:
                filtered_bettors = [b for b in st.session_state.bettors 
                                  if search_term.lower() in b['name'].lower()]
            
            # Pagination
            bettors_per_page = 20
            total_bettors = len(filtered_bettors)
            total_pages = (total_bettors - 1) // bettors_per_page + 1 if total_bettors > 0 else 1
            
            if total_pages > 1:
                page_num = st.selectbox("Page", range(1, total_pages + 1), key="bettor_page") - 1
                start_idx = page_num * bettors_per_page
                end_idx = min(start_idx + bettors_per_page, total_bettors)
                page_bettors = filtered_bettors[start_idx:end_idx]
                st.caption(f"Showing {start_idx + 1}-{end_idx} of {total_bettors} bettors")
            else:
                page_bettors = filtered_bettors
            
            # Display bettors in grid
            cols_per_row = 4
            for i in range(0, len(page_bettors), cols_per_row):
                cols = st.columns(cols_per_row)
                for j, bettor in enumerate(page_bettors[i:i+cols_per_row]):
                    with cols[j]:
                        st.write(f"**{bettor['name']}**")
                        if st.button(f"❌", key=f"remove_setup_{bettor['name']}", 
                                   help=f"Remove {bettor['name']}"):
                            success = db.remove_bettor(bettor['name'])
                            if success:
                                st.rerun()
            
            st.markdown("---")
            
            # Completion status
            if len(st.session_state.bettors) >= st.session_state.target_bettor_count:
                st.success(f"✅ Target reached! {len(st.session_state.bettors)} bettors added.")
                if st.button("✅ Done Adding Bettors - Proceed to Racing", type="primary"):
                    db.complete_bettor_setup()
                    st.rerun()
            else:
                remaining = st.session_state.target_bettor_count - len(st.session_state.bettors)
                st.info(f"📝 {remaining} more bettor(s) needed to reach target of {st.session_state.target_bettor_count}")
            
            # Management actions
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 Reset Bettors"):
                    success, message = db.reset_bettors_only()
                    if success:
                        st.success(message)
                    else:
                        st.error(message)
                    st.rerun()
            
            with col2:
                # Export current bettors
                if st.button("📤 Export Bettors List"):
                    bettor_list = '\n'.join([b['name'] for b in st.session_state.bettors])
                    st.download_button(
                        label="Download Names",
                        data=bettor_list,
                        file_name=f"bettors_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                        mime="text/plain"
                    )
        st.stop()
    
    # Main bettor management page (after setup is complete)
    st.header("Manage Bettors")
    
    # Statistics
    total_bettors = len(st.session_state.bettors)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Bettors", total_bettors)
    with col2:
        st.metric("Target Count", st.session_state.target_bettor_count)
    with col3:
        completed_races = len([r for r in st.session_state.races if 'results' in r])
        st.metric("Races Completed", completed_races)
    
    st.markdown("---")
    
    # Bulk operations section
    with st.expander("🔧 Bulk Operations", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📥 Add Multiple Bettors")
            bulk_add_names = st.text_area(
                "Paste names (one per line):",
                placeholder="New Bettor 1\nNew Bettor 2\n...",
                key="bulk_add_main"
            )
            if st.button("Add All", key="bulk_add_btn"):
                if bulk_add_names.strip():
                    names = [name.strip() for name in bulk_add_names.strip().split('\n') if name.strip()]
                    existing_names = [b['name'] for b in st.session_state.bettors]
                    added_count = 0
                    
                    for name in names:
                        if name not in existing_names:
                            success = db.add_bettor(name)
                            if success:
                                added_count += 1
                    
                    if added_count > 0:
                        st.success(f"Added {added_count} new bettors!")
                        st.rerun()
                    else:
                        st.warning("No new bettors were added")
        
        with col2:
            st.subheader("📤 Export Options")
            if st.button("📋 Copy All Names"):
                bettor_list = '\n'.join([b['name'] for b in st.session_state.bettors])
                st.code(bettor_list, language=None)
            
            if st.button("📊 Download CSV"):
                import pandas as pd
                df = pd.DataFrame(st.session_state.bettors)
                csv = df.to_csv(index=False)
                st.download_button(
                    label="Download Bettors CSV",
                    data=csv,
                    file_name=f"bettors_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
    
    st.markdown("---")
    
    # Search and filter
    col1, col2 = st.columns([3, 1])
    with col1:
        search_term = st.text_input("🔍 Search bettors by name:", key="main_bettor_search")
    with col2:
        show_all = st.checkbox("Show all", value=True, key="show_all_bettors")
    
    # Filter bettors
    filtered_bettors = st.session_state.bettors
    if search_term:
        filtered_bettors = [b for b in st.session_state.bettors 
                          if search_term.lower() in b['name'].lower()]
    
    # Pagination for large lists
    bettors_per_page = 25 if show_all else 10
    total_filtered = len(filtered_bettors)
    
    if total_filtered == 0:
        st.info("No bettors found matching your search.")
    else:
        # Pagination controls
        if total_filtered > bettors_per_page:
            total_pages = (total_filtered - 1) // bettors_per_page + 1
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                page_num = st.selectbox(
                    "Page", 
                    range(1, total_pages + 1), 
                    key="main_bettor_page",
                    format_func=lambda x: f"Page {x} of {total_pages}"
                ) - 1
            
            start_idx = page_num * bettors_per_page
            end_idx = min(start_idx + bettors_per_page, total_filtered)
            page_bettors = filtered_bettors[start_idx:end_idx]
            st.caption(f"Showing {start_idx + 1}-{end_idx} of {total_filtered} bettors")
        else:
            page_bettors = filtered_bettors
            st.caption(f"Showing all {total_filtered} bettors")
        
        # Add new bettor section
        with st.expander("➕ Add New Bettor", expanded=False):
            col1, col2 = st.columns([3, 1])
            with col1:
                new_bettor_name = st.text_input("Bettor Name", key="new_bettor_main")
            with col2:
                if st.button("Add", key="add_new_main"):
                    if new_bettor_name and new_bettor_name not in [b['name'] for b in st.session_state.bettors]:
                        success = db.add_bettor(new_bettor_name)
                        if success:
                            st.success(f"Added: {new_bettor_name}")
                            st.rerun()
                        else:
                            st.error("Failed to add bettor")
                    elif new_bettor_name in [b['name'] for b in st.session_state.bettors]:
                        st.error("Bettor already exists!")
                    else:
                        st.error("Please enter a name!")
        
        # Display bettors in a more compact format
        st.subheader(f"Bettors List ({total_filtered} total)")
        
        # Table view for better handling of large lists
        if total_filtered > 15:
            # Create a dataframe for better display
            bettor_data = []
            for i, bettor in enumerate(page_bettors):
                bettor_data.append({
                    "Name": bettor['name'],
                    "Score": st.session_state.scores.get(bettor['name'], 0),
                    "Actions": f"remove_{bettor['name']}"
                })
            
            # Display as table
            for i, bettor in enumerate(page_bettors):
                col1, col2, col3 = st.columns([4, 1, 1])
                with col1:
                    st.write(f"**{bettor['name']}**")
                with col2:
                    score = st.session_state.scores.get(bettor['name'], 0)
                    st.write(f"Score: {score}")
                with col3:
                    if st.button("❌", key=f"remove_main_{bettor['name']}", 
                               help=f"Remove {bettor['name']}"):
                        success = db.remove_bettor(bettor['name'])
                        if success:
                            st.success(f"Removed: {bettor['name']}")
                            st.rerun()
                        else:
                            st.error(f"Failed to remove: {bettor['name']}")
        else:
            # Grid view for smaller lists
            cols_per_row = 3
            for i in range(0, len(page_bettors), cols_per_row):
                cols = st.columns(cols_per_row)
                for j, bettor in enumerate(page_bettors[i:i+cols_per_row]):
                    if j < len(cols):
                        with cols[j]:
                            st.write(f"**{bettor['name']}**")
                            score = st.session_state.scores.get(bettor['name'], 0)
                            st.write(f"Score: {score} pts")
                            if st.button("Remove", key=f"remove_grid_{bettor['name']}"):
                                success = db.remove_bettor(bettor['name'])
                                if success:
                                    st.rerun()
                                else:
                                    st.error("Failed to remove bettor")

elif page == "🏁 Race Management":
    st.header("Race Management")
    
    if not st.session_state.bettors:
        st.warning("Please add some bettors first before managing races!")
        st.stop()
    
    # Race stats
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Current Race", st.session_state.current_race)
    with col2:
        completed_races = len([r for r in st.session_state.races if 'results' in r])
        st.metric("Completed Races", f"{completed_races}/{st.session_state.total_races}")
    with col3:
        st.metric("Total Bettors", len(st.session_state.bettors))
    
    st.subheader(f"Race {st.session_state.current_race}")
    
    # Check if current race already has results
    current_race_data = None
    for race in st.session_state.races:
        if race['race_number'] == st.session_state.current_race:
            current_race_data = race
            break
    
    if current_race_data and 'results' in current_race_data:
        st.success("This race has already been completed!")
        
        # Display results in a clean format
        st.subheader("Race Results:")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.info(f"🥇 **1st Place**\n\nHorse #{current_race_data['results']['first']}\n\n*3 points*")
        with col2:
            st.info(f"🥈 **2nd Place**\n\nHorse #{current_race_data['results']['second']}\n\n*2 points*")
        with col3:
            st.info(f"🥉 **3rd Place**\n\nHorse #{current_race_data['results']['third']}\n\n*1 point*")
        
        # Show betting results summary
        with st.expander("📊 Betting Results Summary", expanded=False):
            bettor_bets = current_race_data['results']['bettor_bets']
            
            # Group bettors by their bets
            horse_bets = {}
            for bettor, horse in bettor_bets.items():
                if horse not in horse_bets:
                    horse_bets[horse] = []
                horse_bets[horse].append(bettor)
            
            # Display grouped results
            for horse_num in sorted(horse_bets.keys(), key=lambda x: int(x) if x.isdigit() else float('inf')):
                bettors_on_horse = horse_bets[horse_num]
                points = 0
                position = ""
                
                if horse_num == current_race_data['results']['first']:
                    points = 3
                    position = "🥇 1st"
                elif horse_num == current_race_data['results']['second']:
                    points = 2
                    position = "🥈 2nd"
                elif horse_num == current_race_data['results']['third']:
                    points = 1
                    position = "🥉 3rd"
                
                if points > 0:
                    st.success(f"**Horse #{horse_num}** ({position}) - {points} points each")
                else:
                    st.write(f"**Horse #{horse_num}** - 0 points")
                
                # Show bettors in columns
                if len(bettors_on_horse) > 6:
                    # Many bettors - show in compact format
                    st.write(f"Bettors ({len(bettors_on_horse)}): {', '.join(bettors_on_horse[:6])}{'...' if len(bettors_on_horse) > 6 else ''}")
                else:
                    # Few bettors - show in grid
                    cols = st.columns(min(3, len(bettors_on_horse)))
                    for i, bettor in enumerate(bettors_on_horse):
                        with cols[i % 3]:
                            st.write(f"• {bettor}")
        
        st.markdown("---")
        
        if st.session_state.current_race < st.session_state.total_races:
            if st.button("🏁 Next Race", type="primary"):
                db.advance_to_next_race()
                st.rerun()
        else:
            st.info(f"🏆 All {st.session_state.total_races} races completed! Check the scoreboard for final results.")
    else:
        # Get horse numbers for the race
        horse_numbers = st.session_state.horses
        
        # Race results entry
        st.subheader("Enter Race Results")
        st.write("Enter the winning horse numbers for each position:")
        
        # Initialize race results for this race
        first_key = f"first_{st.session_state.current_race}"
        second_key = f"second_{st.session_state.current_race}"
        third_key = f"third_{st.session_state.current_race}"
        
        # Initialize keys if they don't exist
        if first_key not in st.session_state:
            st.session_state[first_key] = ''
        if second_key not in st.session_state:
            st.session_state[second_key] = ''
        if third_key not in st.session_state:
            st.session_state[third_key] = ''
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.text_input("1st Place Horse #", key=first_key)
        with col2:
            st.text_input("2nd Place Horse #", key=second_key)
        with col3:
            st.text_input("3rd Place Horse #", key=third_key)
        
        # Get current values from session state
        first_place = st.session_state[first_key]
        second_place = st.session_state[second_key]
        third_place = st.session_state[third_key]
        
        # Validation for race positions
        invalid_horses = []
        for position, horse_num in [("1st", first_place), ("2nd", second_place), ("3rd", third_place)]:
            if horse_num and horse_num not in horse_numbers:
                invalid_horses.append(f"{position} place: Horse #{horse_num}")
        
        if invalid_horses:
            st.error(f"Invalid horse numbers entered: {', '.join(invalid_horses)}")
        
        st.markdown("---")
        
        # Bettor bets entry - Enhanced for large numbers
        st.subheader("Enter Bettor Bets")
        
        bettor_names = [b['name'] for b in st.session_state.bettors]
        total_bettors = len(bettor_names)
        
        # Show available horses for reference
        st.info(f"Available horses: {', '.join([f'#{h}' for h in horse_numbers])}")
        
        # Bulk bet entry options
        with st.expander("🚀 Bulk Bet Entry Options", expanded=total_bettors > 15):
            tab1, tab2, tab3 = st.tabs(["📝 Quick Fill", "📋 Paste Format", "📊 CSV Import"])
            
            with tab1:
                st.write("**Quick fill all bettors with the same horse:**")
                col1, col2 = st.columns([2, 1])
                with col1:
                    quick_horse = st.selectbox("Select horse for all bettors:", [""] + horse_numbers, key="quick_fill_horse")
                with col2:
                    if st.button("Fill All") and quick_horse:
                        for bettor in bettor_names:
                            bet_key = f"bet_{bettor}_{st.session_state.current_race}"
                            st.session_state[bet_key] = quick_horse
                        st.success(f"Set all bettors to Horse #{quick_horse}")
                        st.rerun()
            
            with tab2:
                st.write("**Paste bet data (Format: Bettor Name:Horse Number)**")
                bulk_bets = st.text_area(
                    "Enter bets:",
                    placeholder="John Smith:3\nJane Doe:7\nMike Johnson:2\n...",
                    help="One line per bettor in format 'Name:HorseNumber'",
                    key="bulk_bet_input"
                )
                
                if st.button("📥 Import Bets") and bulk_bets.strip():
                    imported_count = 0
                    errors = []
                    
                    for line in bulk_bets.strip().split('\n'):
                        if ':' in line:
                            try:
                                name, horse = line.split(':', 1)
                                name = name.strip()
                                horse = horse.strip()
                                
                                if name in bettor_names and horse in horse_numbers:
                                    bet_key = f"bet_{name}_{st.session_state.current_race}"
                                    st.session_state[bet_key] = horse
                                    imported_count += 1
                                else:
                                    errors.append(f"Invalid: {line}")
                            except:
                                errors.append(f"Format error: {line}")
                    
                    if imported_count > 0:
                        st.success(f"Imported {imported_count} bets!")
                        st.rerun()
                    if errors:
                        st.warning(f"Errors with {len(errors)} entries")
                        for error in errors[:3]:
                            st.caption(f"• {error}")
            
            with tab3:
                st.write("**Upload CSV with columns: 'name', 'horse'**")
                bet_file = st.file_uploader("Choose CSV file", type=['csv'], key="bet_csv")
                if bet_file is not None:
                    try:
                        import pandas as pd
                        df = pd.read_csv(bet_file)
                        
                        # Find name and horse columns
                        name_col = next((col for col in df.columns if 'name' in col.lower()), df.columns[0])
                        horse_col = next((col for col in df.columns if 'horse' in col.lower()), df.columns[1] if len(df.columns) > 1 else df.columns[0])
                        
                        st.write(f"Found {len(df)} entries using columns: {name_col}, {horse_col}")
                        
                        if st.button("📥 Import from CSV"):
                            imported_count = 0
                            for _, row in df.iterrows():
                                name = str(row[name_col]).strip()
                                horse = str(row[horse_col]).strip()
                                
                                if name in bettor_names and horse in horse_numbers:
                                    bet_key = f"bet_{name}_{st.session_state.current_race}"
                                    st.session_state[bet_key] = horse
                                    imported_count += 1
                            
                            if imported_count > 0:
                                st.success(f"Imported {imported_count} bets from CSV!")
                                st.rerun()
                    except Exception as e:
                        st.error(f"Error reading CSV: {str(e)}")
        
        st.markdown("---")
        
        # Individual bet entry with search and pagination
        st.write("**Individual Bet Entry:**")
        
        # Search functionality
        search_bettor = st.text_input("🔍 Search bettors:", key="race_bettor_search")
        
        # Filter bettors
        if search_bettor:
            filtered_bettors = [name for name in bettor_names if search_bettor.lower() in name.lower()]
        else:
            filtered_bettors = bettor_names
        
        # Pagination
        bets_per_page = 15
        total_filtered = len(filtered_bettors)
        
        if total_filtered > bets_per_page:
            total_pages = (total_filtered - 1) // bets_per_page + 1
            page_num = st.selectbox(
                "Page", 
                range(1, total_pages + 1), 
                key="race_bet_page",
                format_func=lambda x: f"Page {x} of {total_pages}"
            ) - 1
            
            start_idx = page_num * bets_per_page
            end_idx = min(start_idx + bets_per_page, total_filtered)
            page_bettors = filtered_bettors[start_idx:end_idx]
            st.caption(f"Showing {start_idx + 1}-{end_idx} of {total_filtered} bettors")
        else:
            page_bettors = filtered_bettors
        
        # Track bets and validation
        invalid_bets = []
        bettor_bets = {}
        
        # Display bets in grid format (3 columns)
        cols_per_row = 3
        for i in range(0, len(page_bettors), cols_per_row):
            cols = st.columns(cols_per_row)
            for j, bettor in enumerate(page_bettors[i:i+cols_per_row]):
                if j < len(cols):
                    with cols[j]:
                        bet_key = f"bet_{bettor}_{st.session_state.current_race}"
                        if bet_key not in st.session_state:
                            st.session_state[bet_key] = ''
                        
                        # Show bettor name and input
                        st.write(f"**{bettor}**")
                        current_bet = st.text_input(
                            "Horse #:", 
                            value=st.session_state[bet_key],
                            key=f"input_{bet_key}",
                            placeholder="e.g. 3",
                            label_visibility="collapsed"
                        )
                        
                        # Update session state
                        st.session_state[bet_key] = current_bet
                        bettor_bets[bettor] = current_bet
                        
                        # Validate bet
                        if current_bet and current_bet not in horse_numbers:
                            invalid_bets.append(f"{bettor}: Horse #{current_bet}")
                            st.error("❌ Invalid")
                        elif current_bet:
                            st.success("✅ Valid")
        
        # Show validation errors
        if invalid_bets:
            st.error(f"Invalid horse numbers for bets:")
            for error in invalid_bets[:5]:  # Show first 5 errors
                st.write(f"• {error}")
        
        # Progress indicator
        filled_bets = sum(1 for bet in bettor_bets.values() if bet.strip())
        st.progress(filled_bets / len(bettor_names))
        st.caption(f"Bets entered: {filled_bets}/{len(bettor_names)}")
        
        st.markdown("---")
        
        # Results preview and submission
        all_positions_filled = first_place and second_place and third_place
        all_bets_filled = all(bettor_bets.get(b, '') for b in bettor_names)
        unique_positions = len(set([first_place, second_place, third_place])) == 3 if all_positions_filled else False
        valid_horses_positions = not invalid_horses
        valid_horses_bets = not invalid_bets
        
        # Check if all validations pass
        can_submit = (all_positions_filled and all_bets_filled and unique_positions and 
                     valid_horses_positions and valid_horses_bets)
        
        # Quick validation summary
        validation_status = []
        if not all_positions_filled:
            validation_status.append("❌ Race positions incomplete")
        else:
            validation_status.append("✅ Race positions filled")
            
        if not all_bets_filled:
            validation_status.append(f"❌ Bets missing ({filled_bets}/{len(bettor_names)})")
        else:
            validation_status.append("✅ All bets entered")
            
        if all_positions_filled and not unique_positions:
            validation_status.append("❌ Duplicate positions")
        elif all_positions_filled:
            validation_status.append("✅ Unique positions")
            
        # Show validation status
        col1, col2 = st.columns([2, 1])
        with col1:
            for status in validation_status:
                st.write(status)
        
        with col2:
            if st.button("✅ Submit Results", type="primary", disabled=not can_submit):
                # Submit race results using database
                success = db.submit_race_results(
                    st.session_state.current_race,
                    first_place,
                    second_place,
                    third_place,
                    bettor_bets
                )
                
                if success:
                    # Clear all input fields for this race
                    for key in [first_key, second_key, third_key]:
                        if key in st.session_state:
                            del st.session_state[key]
                    for bettor in bettor_names:
                        bet_key = f"bet_{bettor}_{st.session_state.current_race}"
                        if bet_key in st.session_state:
                            del st.session_state[bet_key]
                    
                    st.success("Race results submitted successfully!")
                    st.balloons()
                    st.rerun()
                else:
                    st.error("Failed to submit race results. Please try again.")
        
        # Export current bets for backup
        if filled_bets > 0:
            with st.expander("📤 Export Current Bets", expanded=False):
                export_format = st.radio("Export format:", ["Text", "CSV"], horizontal=True)
                
                if export_format == "Text":
                    bet_text = '\n'.join([f"{bettor}:{bet}" for bettor, bet in bettor_bets.items() if bet])
                    st.download_button(
                        label="Download Bet List",
                        data=bet_text,
                        file_name=f"race_{st.session_state.current_race}_bets.txt",
                        mime="text/plain"
                    )
                else:
                    import pandas as pd
                    bet_df = pd.DataFrame([{"name": bettor, "horse": bet} for bettor, bet in bettor_bets.items() if bet])
                    csv = bet_df.to_csv(index=False)
                    st.download_button(
                        label="Download CSV",
                        data=csv,
                        file_name=f"race_{st.session_state.current_race}_bets.csv",
                        mime="text/csv"
                    )

elif page == "📊 Scoreboard":
    st.header("Scoreboard")
    display_scoreboard()

elif page == "⚙️ Settings":
    st.header("Settings")
    
    # Race Configuration
    st.subheader("🏁 Race Configuration")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        new_total_races = st.number_input(
            "Total Number of Races", 
            min_value=1, 
            max_value=50, 
            value=st.session_state.total_races,
            step=1,
            help="Changes the total number of races for this event"
        )
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)  # Add spacing
        if st.button("Update Race Count", type="primary"):
            # Check if any races have results
            completed_races = len([r for r in st.session_state.races if 'results' in r])
            
            if new_total_races < completed_races:
                st.error(f"Cannot reduce race count below {completed_races} - that many races are already completed!")
            elif new_total_races < st.session_state.current_race:
                st.error(f"Cannot reduce race count below {st.session_state.current_race} - we're already on race {st.session_state.current_race}!")
            else:
                db.set_total_races(new_total_races)
                st.success(f"Race count updated to {new_total_races} races!")
                st.rerun()
    
    # Show current status
    completed_races = len([r for r in st.session_state.races if 'results' in r])
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Current Total", f"{st.session_state.total_races} races")
    with col2:
        st.metric("Completed", f"{completed_races} races")
    with col3:
        st.metric("Remaining", f"{st.session_state.total_races - completed_races} races")
    
    if completed_races > 0:
        st.info(f"📋 Note: You can only increase the race count since {completed_races} race(s) are already completed.")
    
    st.markdown("---")
    
    st.subheader("Data Management")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Reset All Data", type="secondary"):
            success = db.reset_all_data()
            if success:
                st.success("All data has been reset!")
                st.rerun()
            else:
                st.error("Failed to reset data.")
    
    with col2:
        if st.button("Reset Horses Only"):
            success, message = db.reset_horses_only()
            if success:
                st.success(message)
            else:
                st.error(message)
            st.rerun()
    
    with col3:
        if st.button("Reset Bettors Only"):
            success, message = db.reset_bettors_only()
            if success:
                st.success(message)
            else:
                st.error(message)
            st.rerun()
    
    # Export functionality moved to second row
    st.markdown("---")
    if st.button("Export Data", key="export_data_main"):
        data = db.export_data()
        st.download_button(
            label="Download JSON",
            data=json.dumps(data, indent=2),
            file_name=f"derby_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )
    
    st.markdown("---")
    
    st.subheader("System Information")
    stats = db.get_stats()
    
    # Basic stats
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Total Horses:** {stats['total_horses']}")
        st.write(f"**Total Bettors:** {stats['total_bettors']}")
        st.write(f"**Races Completed:** {stats['completed_races']}")
        st.write(f"**Current Race:** {st.session_state.current_race}")
        st.write(f"**Total Races:** {st.session_state.total_races}")
    
    with col2:
        st.write(f"**Target Horse Count:** {st.session_state.target_horse_count}")
        st.write(f"**Target Bettor Count:** {st.session_state.target_bettor_count}")
        st.write(f"**Database:** derby_betting.db")
        
        # System scale indicator
        if stats['total_bettors'] >= 40:
            st.success("🚀 **Large-Scale Mode Active**")
        elif stats['total_bettors'] >= 20:
            st.info("📈 **Medium-Scale Mode**")
        else:
            st.write("📝 **Standard Mode**")
    
    st.markdown("---")
    
    # Enhanced capabilities summary
    st.subheader("🎯 System Capabilities")
    
    cap_col1, cap_col2 = st.columns(2)
    
    with cap_col1:
        st.write("**Bettor Management:**")
        st.write("✅ Bulk import (CSV/Text)")
        st.write("✅ Search & filter")
        st.write("✅ Pagination (up to 100 bettors)")
        st.write("✅ Export options")
        
        st.write("**Race Management:**")
        st.write("✅ Grid-based bet entry")
        st.write("✅ Bulk bet operations")
        st.write("✅ Real-time validation")
        st.write("✅ Progress tracking")
    
    with cap_col2:
        st.write("**Scoreboard Features:**")
        st.write("✅ Live filtering & search")
        st.write("✅ Paginated results")
        st.write("✅ Multiple export formats")
        st.write("✅ Race-by-race breakdown")
        
        st.write("**Database Benefits:**")
        st.write("✅ Persistent data storage")
        st.write("✅ Cloud deployment ready")
        st.write("✅ Concurrent access safe")
        st.write("✅ Automatic backups")
    
    # Performance info
    if stats['total_bettors'] >= 20:
        st.markdown("---")
        st.subheader("⚡ Performance Optimizations")
        
        optimizations = [
            f"Database-powered operations for {stats['total_bettors']} bettors",
            "Paginated views for efficient loading",
            "Bulk operations for faster data entry",
            "Mobile-responsive design",
            "Search and filter capabilities"
        ]
        
        for opt in optimizations:
            st.write(f"• {opt}")
    
    # Deployment info
    st.markdown("---")
    st.subheader("🌐 Deployment Ready")
    st.write("This system is optimized for:")
    st.write("• **Streamlit Cloud** - Free hosting with database")
    st.write("• **Railway/Heroku** - Production hosting")
    st.write("• **Local events** - Offline capable")
    st.write("• **Mobile access** - Responsive design")
    
    if stats['total_bettors'] >= 40:
        st.success("🎉 **Ready for large-scale derby events!**")

# Footer
st.markdown("---")
st.markdown("🏇 Derby Betting System - Built with Streamlit + Database") 