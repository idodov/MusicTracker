# Music Tracker
**A Home Assistant script to track played music and generate statistics.**

## Description
This Python script is designed to track music played on Home Assistant media players. It stores track information in a SQLite database and provides various statistics through Home Assistant sensors.

**Key Features:**
* Tracks played music and stores it in a SQLite database.
* Cleans track titles to improve accuracy.
* Calculates and displays top songs, artists, albums, and media channels for different timeframes.
* Automatically removes old tracks from the database to maintain performance.

## How Track Counts Are Calculated
The script employs several strategies to accurately calculate track counts and prevent overcounting:
* **Unique Track Identification:** Tracks are identified by a combination of artist and title. This ensures that different versions or remixes of the same song are counted same.
* **Track Playing Time:** Tracks are started to count if they played at least 5 seconds (user can change this value)
* **Track Deduplication:** A `TrackManager` class maintains a dictionary of recently played tracks. If a track is played again within a specified timeframe (currently 10 minutes), it's considered a duplicate and not counted.

## Installation
1. **Install AppDaemon from HomeAssistant Addon Store**
2. Copy the script file and place it into the appddeamon apps directory 
3. **Create a new App in AppDaemon:**
   * Navigate to AppDaemon -> Apps
   * Add a new app with the following configuration:
     ```yaml
     music_tracker:
       module: music_tracker
       class: MusicTracker
       db_path: "/config/music_history.db"
       media_players:
         - media_player.living_room
         - media_player.bedroom
     ```
   * Replace `media_player.living_room` and `media_player.bedroom` with your actual media player entities.

## Configuration
* **media_players:** A list of media player entities to track.
* **db_path:** The path to the SQLite database file.

## Usage
Once the script is configured and running, it will automatically track played music and update the specified sensors.
You can use Markdown card to see the data

## AI Anaylitics [TODO]
You can use the power of AI to get some more info about your music taste. 
* Add https://github.com/pmazz/ps_hassio_entities/blob/master/python_scripts/hass_entities.py to python_scripts directory
* add python_scripts: to configuration.yaml
* create a sensor helper
* create a script that write text to the sensor
* present the data in markdown card

