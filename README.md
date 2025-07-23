# 🏇 Derby Betting System

A comprehensive betting management system for private derby events, built with Streamlit. This system allows you to manage bettors, track race results, and maintain a dynamic scoreboard across multiple races.

## Features

- **Bettor Management**: Add and manage bettors with their horse selections
- **Race Management**: Record race results (1st, 2nd, 3rd place) for up to 10 races
- **Scoring System**: Automatic point calculation (3-2-1 points for 1st-2nd-3rd place)
- **Dynamic Scoreboard**: Real-time scoreboard that updates after each race
- **Data Persistence**: All data is saved locally and persists between sessions
- **White & Red Theme**: Clean, professional color scheme
- **Export Functionality**: Export all data for backup or analysis

## Installation

1. **Clone or download the project files**
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Starting the Application

Run the Streamlit application:
```bash
streamlit run derby_betting_system.py
```

The application will open in your default web browser at `http://localhost:8501`.

### Getting Started

1. **Dashboard**: Overview of the system with quick actions
2. **Manage Bettors**: Add bettors and assign horses
3. **Race Management**: Record race results and advance to next race
4. **Scoreboard**: View current standings and race history
5. **Settings**: Data management and system information

### Workflow

1. **Add Bettors**: Go to "Manage Bettors" and add participants with their horse selections
2. **Start Racing**: Navigate to "Race Management" to begin recording race results
3. **Record Results**: For each race, select 1st, 2nd, and 3rd place finishers
4. **View Progress**: Check the scoreboard to see current standings
5. **Continue**: Advance to the next race and repeat until all 10 races are complete

### Scoring System

- **1st Place**: 3 points
- **2nd Place**: 2 points
- **3rd Place**: 1 point

Scores accumulate across all races, and the scoreboard automatically reorders after each race.

## File Structure

```
derby/
├── derby_betting_system.py    # Main application
├── requirements.txt           # Python dependencies
├── README.md                 # This file
└── derby_data.json          # Data file (created automatically)
```

## Data Management

- **Automatic Saving**: All data is automatically saved to `derby_data.json`
- **Data Export**: Export all data as JSON from the Settings page
- **Reset Function**: Clear all data and start fresh from Settings
- **Persistence**: Data persists between application restarts

## Customization

### Horse Names
You can modify the horse names by editing the `HORSE_NAMES` list in the main file.

### Number of Races
The system is designed for 10 races but can be easily modified by changing the race progression logic.

### Color Scheme
The white and red color scheme is implemented through custom CSS. You can modify the colors in the CSS section of the code.

## Troubleshooting

### Common Issues

1. **Port already in use**: If port 8501 is busy, Streamlit will automatically use the next available port
2. **Data not saving**: Ensure the application has write permissions in the directory
3. **Import errors**: Make sure all dependencies are installed with `pip install -r requirements.txt`

### Data Recovery

If you need to recover data:
1. Check for `derby_data.json` in the application directory
2. Use the export function to create backups
3. The data file contains all bettors, races, and scores

## Future Enhancements

This prototype can be extended to a full web application with:
- User authentication
- Real-time updates
- Mobile responsiveness
- Advanced analytics
- Multi-event support
- API endpoints

## Support

For issues or questions, check the application's built-in help features or refer to the Streamlit documentation.

---

**Built with ❤️ using Streamlit** 