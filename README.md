# 🎵 Music Tracker & AI Insights for Home Assistant

Uncover the story of your musical taste with this powerful AppDaemon application for Home Assistant. Go beyond simple play counts and dive deep into your listening habits with automatically generated, beautiful, and insightful music charts.

This isn't just a scrobbler; it's your personal music historian that passively logs your listening activity and transforms it into rich, interactive charts. Paired with an optional AI musicologist, it delivers deep listening analyses, custom artist artwork, and music mini-games tailored to your listening DNA.

<p align="center">
  <img src="https://github.com/user-attachments/assets/01c96643-0a0e-45dc-a9eb-ddf18b060480" alt="Music Charts Interface" width="800">
</p>

Designed to be completely **self-maintaining**, it cleans up skipped songs, deduplicates daily snapshots, prunes old data, and compacts its own SQLite database so it stays fast and light permanently.

---

## ✨ Key Features

- **✅ Passive Multi-Room Tracking:** Monitors configured Home Assistant media players (Sonos, Spotify, Cast, Volumio, etc.) without manual logging.
- **📊 Granular Dynamic Charts:** Generates clean daily, weekly, monthly, and yearly rankings for top tracks, artists, albums, and source channels/playlists.
- **📈 Chart Trajectory & Movement:** Tracks historical position changes with dynamic indicators (▲ rise, ▼ fall, NEW entry).
- **🧹 Automated Database Optimization:**
  - Detects and drops skipped songs (listened to for less than the configurable threshold).
  - Automatically deduplicates multiple chart snapshots per day.
  - Prunes chart history beyond a user-defined retention window (e.g., 62 days).
  - Executes `VACUUM` post-cleanup to reclaim disk space automatically.
- **🔮 Generative AI Insights (Optional):**
  - Interfaces directly with Home Assistant AI services (`ai_task.generate_data` / Generative AI integrations).
  - Generates responsive, self-contained HTML analysis widgets highlighting listening eras, peak listening hours, and musical taste patterns.
  - Dynamically synthesizes top-artist imagery via [Pollinations.ai](https://gen.pollinations.ai) using your API key.
  - Builds interactive HTML/JS trivia mini-games generated directly from your actual play data.
- **🌓 Adaptive Web UI:** Mobile-first, responsive standalone HTML dashboard with light/dark theme support and time-frame filtering toggles.
- **⚡ Instant On-Demand Generation:** Trigger immediate updates via webhook directly from the web interface, an `input_boolean` helper, or Home Assistant automations.

<p align="center">
  <img src="https://github.com/user-attachments/assets/b94d83da-b82d-46d2-983d-93dc44c61703" alt="AI-Generated Report" width="800">
</p>

---

## 🚀 Installation Guide

### Prerequisites

1. A working **Home Assistant** instance.
2. The **[AppDaemon Add-on](https://github.com/hassio-addons/addon-appdaemon)** installed and configured.
3. *(Optional)* A configured **Generative AI service** in Home Assistant (such as [Google Generative AI](https://www.home-assistant.io/integrations/google_generative_ai_conversation/) or an `ai_task` provider) to enable AI reports.
4. *(Optional)* A **Pollinations API Key** from [enter.pollinations.ai/keys](https://enter.pollinations.ai/keys) to render artist portraits seamlessly.

### Step 1: Add the Script

1. Navigate to your AppDaemon configuration directory (typically `/config/appdaemon/apps`).
2. Create a file named `music_tracker.py`.
3. Copy the full content of `music_tracker.py` from this repository and save it.

### Step 2: Configure `apps.yaml`

Add the application definition to your `/config/appdaemon/apps/apps.yaml`:

```yaml
music_tracker:
  module: music_tracker
  class: MusicTracker

  # --- Required Core Settings ---
  # List of media_player entity IDs to monitor
  media_players:
    - media_player.living_room_sonos
    - media_player.kitchen_speaker
    - media_player.patio

  # SQLite database path (kept inside /config for persistence across container updates)
  db_path: "/config/music_data_history.db"

  # Output destination for the rendered charts HTML (must reside in the Home Assistant www folder)
  html_output_path: "/homeassistant/www/music_charts.html"

  # Time of day (HH:MM:SS) to run scheduled daily chart generation
  update_time: "23:59:00"

  # --- AI Integration (Optional) ---
  # Service call for AI report generation (set to false to disable)
  ai_service: "ai_task.generate_data"

  # API key from enter.pollinations.ai for AI artist image generation
  pollinations_api_key: "YOUR_POLLINATIONS_API_KEY"

  # --- Tracking Fine-Tuning ---
  # Minimum playback time (in seconds) before a song is logged
  duration: 30

  # Minimum unique tracks required from an album for it to rank in album charts
  min_songs_for_album: 3

  # Run chart generation immediately when AppDaemon boots
  run_on_startup: true

  # Enable the interactive "Update Charts" webhook button on the web page
  webhook: true

  # Input boolean entity used for manual/webhook triggers
  chart_trigger_boolean: "input_boolean.music_charts_update"

  # --- Automated Database Cleanup ---
  # Scheduled time and day of week to execute database optimization
  cleanup_schedule: "03:45:00"
  cleanup_day_of_week: "sun"

  # Tracks played for fewer seconds than this threshold are treated as skips and purged
  cleanup_threshold_seconds: 60

  # Retain chart history snapshots for this many days (62 days covers 2 months of comparisons)
  cleanup_prune_chart_history: true
  cleanup_prune_keep_days: 62

  # Set to true to execute actual deletions; set to false for dry-run logging
  cleanup_execute_on_run: true

  # Reclaim disk space by running SQLite VACUUM after pruning
  cleanup_vacuum_on_complete: true
