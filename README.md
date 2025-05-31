# Home Assistant Music Tracker & Charts

Track your music listening habits from Home Assistant media players and generate beautiful, dynamic HTML charts. Includes daily, weekly, monthly, and yearly top songs, artists, albums, and channels/playlists, with an optional AI-powered analysis of your music taste.

![image](https://github.com/user-attachments/assets/f39d931d-1dd3-4fe9-b3f8-011f403cd1c3)

![image](https://github.com/user-attachments/assets/85768a3a-2a81-4ff4-b327-870d3e7ed87c)
```yaml
type: iframe
url: /local/music_charts.html
aspect_ratio: 100%
```

## Features

*   **Comprehensive Tracking:** Logs songs played on configured Home Assistant media players.
*   **Dynamic Charts:** Generates an HTML page with sortable and filterable charts for:
    *   Top Songs (Artist, Title, Plays)
    *   Top Artists (Artist, Plays)
    *   Top Albums (Album, Artist, Tracks Played from Album)
    *   Top Channels/Playlists (Channel/Source, Plays)
*   **Multiple Time Periods:** View charts for Daily, Weekly, Monthly, and Yearly listening.
*   **Chart Movement Indicators:** See if an item is 🆕 (New), ▲ (Moved Up), or ▼ (Moved Down) in the charts compared to the previous period.
*   **Persistent Storage:** Uses an SQLite database to store listening history and chart data.
*   **Configurable Tracking:**
    *   Define how long a song must play to be counted.
    *   Set a minimum number of unique songs for an album to appear in album charts.
*   **Automatic & Manual Updates:**
    *   Charts update automatically at a configured time.
    *   Manually trigger updates via a Home Assistant `input_boolean`.
*   **Title Cleaning:** Intelligently cleans song and album titles by removing common tags (e.g., "Remastered", "Live", "Explicit") for better grouping.
*   **Responsive Design:** The HTML chart page is designed to work on desktop and mobile.
*   **Optional AI Analysis (Appdaemon 4.5+):**
    *   Integrates with a Home Assistant AI service (e.g., local LLM via `conversation.process` or cloud-based).
    *   Provides an analysis of your listening habits, genre preferences, and song/artist recommendations based on your daily and weekly top songs.
    *   AI prompt is customizable.

## Prerequisites

*   **Home Assistant:** A running instance of Home Assistant.
*   **AppDaemon:** AppDaemon **(v4.5+)** installed and configured for Home Assistant.
*   **Media Players:** Media player entities in Home Assistant that report the following attributes:
    *   `media_title`
    *   `media_artist`
    *   `media_album_name` (optional but recommended for album charts)
    *   `media_channel` or `source` (optional but recommended for channel/playlist charts)
*   **(Optional for AI Analysis)** An AI service configured in Home Assistant that can be called.
*   **(Optional for manual trigger)** An `input_boolean` entity in Home Assistant.

## Installation

1.  **Copy Script:** Place the `music_tracker.py` (or whatever you name it) script into your AppDaemon `apps` directory (e.g., `/config/appdaemon/apps/`).
2.  **Configure `apps.yaml`:** Add the configuration for this app to your `apps.yaml` file. See the "Configuration" section below.
3.  **Ensure `www` Directory (for HTML output):**
    *   If you want to access the HTML page directly via Home Assistant's web server, ensure the `html_output_path` points to a location within your Home Assistant `config/www/` directory. For example, if `html_output_path` is `/config/www/music_charts.html`, you can access it at `http://<your_home_assistant_ip>:8123/local/music_charts.html`.
    *   If the `www` directory doesn't exist in your Home Assistant configuration directory, create it.
    *   The `www` directory should also define in `configuration.yaml` (to gain access to: `http://homeassistant.local:8123/local/music_charts.html`)
```yaml
homeassistant:
  allowlist_external_urls:
    - http://192.168.86.220:8123 # HA IP EXAMPLE
    - http://homeassistant.local:8123

  allowlist_external_dirs:
    - "/config/www"
```

## Configuration

Add the following to your `apps.yaml` file:

```yaml
music_charts: # This is the AppDaemon app instance name, can be anything unique
  module: music_tracker # The name of your Python script file (without .py)
  class: MusicTracker # The class name in the script
  
  # Required: List of media player entity IDs to monitor
  media_players:
    - media_player.spotify_user
    # - media_player.kitchen_speaker
    # - media_player.living_room_display
    
  # Required: Path to the SQLite database file. 
  # It will be created if it doesn't exist.
  # Ensure AppDaemon has write permissions to this location.
  db_path: /config/appdaemon/data/music_charts.db 
  
  # Required: Full path where the generated HTML chart file will be saved.
  # For HA web access, use a path inside /config/www/
  html_output_path: /config/www/music_charts.html
  
  # Optional: Duration in seconds a song must play to be considered "played".
  # Default: 30
  duration: 30 
  
  # Optional: Minimum number of unique songs from an album played in the period 
  # for the album to appear in the charts.
  # Default: 3
  min_songs_for_album: 3
  
  # Optional: Time to automatically update the charts daily (HH:MM:SS format).
  # Default: "23:59:00"
  update_time: "23:59:00"
  
  # Optional: Home Assistant input_boolean entity_id to manually trigger chart updates.
  # Create this boolean in HA (e.g., via Helpers UI).
  # Default: "input_boolean.music_charts"
  chart_trigger_boolean: input_boolean.generate_music_charts 
  
  # Optional: AI Service to call for analysis (e.g., "conversation/process" or "ollama/generate").
  # Set to false or omit if not using AI analysis.
  # Example for Google integration: "google_generative_ai_conversation/generate_content"
  # Default: false
  ai_service: false 
  # ai_service: "google_generative_ai_conversation/generate_content" # Example
  
  # Optional: Whether to generate charts when AppDaemon starts/restarts.
  # Default: true
  run_on_startup: true
```

**Important Notes on Paths:**
*   Paths like `/config/appdaemon/...` are typically used when AppDaemon is running in a Docker container alongside Home Assistant. Adjust paths based on your specific AppDaemon setup.
*   Ensure AppDaemon has read/write permissions to the `db_path` and `html_output_path` locations.

## Usage

1.  **Automatic Tracking:** Once configured, the app will automatically listen to state changes from your specified `media_players`.
2.  **Viewing Charts:**
    *   The charts are generated as an HTML file at the `html_output_path`.
    *   If you configured `html_output_path` to be inside Home Assistant's `www` directory (e.g., `/config/www/music_charts.html`), you can access the page via your Home Assistant URL: `http://<your_ha_ip>:8123/local/music_charts.html`.
    *   The page includes checkboxes to toggle the visibility of Daily, Weekly, Monthly, and Yearly chart sections. Your preference is saved in browser local storage.
    *   A "Refresh Page" button is available to reload the current data (useful if you've just triggered a manual update).
3.  **Scheduled Updates:** Charts will automatically regenerate daily at the time specified by `update_time`.
4.  **Manual Updates:**
    *   If `chart_trigger_boolean` is configured, create an `input_boolean` in Home Assistant (e.g., "Generate Music Charts").
    *   Toggling this `input_boolean` to "on" will trigger an immediate regeneration of the charts. The boolean will automatically turn off after the update.
5.  **AI Analysis:**
    *   If `ai_service` is configured, the AI analysis section will appear at the bottom of the HTML page.
    *   The quality and content of the AI analysis depend heavily on the AI model/service you are using and the prompt defined in `build_prompt_from_chart_data`.
    *   The AI service call has a timeout of 120 seconds.

## How it Works

*   **Event Listening:** The app listens for `state_changed` events from the configured `media_player` entities.
*   **Play Confirmation:** When a song starts playing, a timer is set for the configured `duration`. If the song is still playing the same track after this duration (and hasn't been logged recently), it's considered "played."
*   **Duplicate Prevention:** A `TrackManager` temporarily remembers recently played tracks (default: 10 minutes) to avoid logging the same play multiple times if it's paused/resumed or replayed quickly.
*   **Data Cleaning:** Song and album titles are cleaned of common version tags (e.g., "Remastered," "Live," "(feat. ...)") to improve data aggregation.
*   **Database Storage:**
    *   `music_history`: Stores individual song plays (artist, title, album, media_channel, timestamp). Old entries (older than 1 year) are automatically cleaned up.
    *   `chart_history`: Stores a snapshot of the top items for each category (songs, artists, etc.) and period (daily, weekly, etc.) each time charts are generated. This is used to calculate the ▲▼🆕 movement indicators.
*   **Chart Generation:**
    *   SQL queries aggregate play counts from `music_history` for different timeframes.
    *   The results are compared with data from `chart_history` to determine rank changes.
    *   Jinja2 templating is used to render the final HTML page.
*   **AI Prompting:** Daily and Weekly top song data is formatted into a detailed prompt for the configured AI service. The AI's HTML response is then embedded into the chart page.

## Troubleshooting

*   **Check AppDaemon Logs:** This is the first place to look for errors or debug messages.
*   **Media Player Attributes:** Ensure your media players are providing `media_title` and `media_artist`. For album charts, `media_album_name` is needed. For channel/playlist charts, `media_channel` or `source` is used.
*   **File Permissions:** AppDaemon needs write access to `db_path` and `html_output_path`.
*   **AI Service:** If using AI, ensure the service name is correct and the AI service is functioning in Home Assistant. Check HA logs if AI analysis fails.
*   **Path Configuration:** Double-check all file paths in your `apps.yaml` are correct for your AppDaemon and Home Assistant setup.

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details (you'll need to create this file, typically with the standard MIT license text).
