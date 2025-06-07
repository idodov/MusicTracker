# 🎵 Music Tracker & AI Insights for Home Assistant

Uncover the story of your musical taste with this powerful AppDaemon script for Home Assistant. Go beyond simple play counts and dive deep into your listening habits with automatically generated, beautiful, and insightful music charts.

This isn't just a tracker; it's your personal music historian, complete with an optional AI musicologist that provides stunning visual and analytical reports on what you've been listening to.

<p align="center">
  <img src="https://github.com/user-attachments/assets/01c96643-0a0e-45dc-a9eb-ddf18b060480" alt="Music Charts Interface" width="800">
</p>

Ever wonder what the *real* soundtrack to your life is? Go beyond simple play counts and discover the true story of your musical taste with **Music Tracker & AI Insights**, a powerful AppDaemon application for Home Assistant.

This isn't just a scrobbler; it's your personal music historian that passively logs your listening habits and transforms that data into beautiful, insightful, and dynamic charts. Plus, with an optional AI musicologist, you can receive stunning analytical reports, artist visualizations, and even music-themed mini-games based on your unique listening DNA.

Best of all, it's designed to be **self-maintaining**, automatically cleaning and optimizing its own database to stay fast and efficient forever.

---

## ✨ Key Features

- **✅ Passive Music Tracking:** Automatically logs every song you listen to across configured Home Assistant media players (Sonos, Volumio, Spotify, etc.).
- **📊 Dynamic Charts:** Generates daily, weekly, monthly, and yearly charts for your top songs, artists, albums, and even your favorite radio stations or playlists.
- **📈 Historical Analysis:** See how your top songs rise and fall with position change indicators (▲, ▼, NEW).
- **🚀 Self-Maintaining Database:**
  - Intelligently identifies and removes "skipped" tracks (songs played for less than a minute).
  - Automatically prunes old chart data to keep the database lean and fast.
  - Reclaims disk space by running `VACUUM` after cleanup. Set it and forget it!
- **🧠 AI-Powered Insights (Optional):**
  - Connect a Generative AI service (like the `google_generative_ai_conversation` integration).
  - Receive stunning, self-contained HTML reports with deep analysis, new music recommendations, and fun facts.
  - Get a unique, AI-generated image of your top artist and interactive music trivia games!
- **📱 Modern Web Interface:** All charts are rendered into a single, clean HTML page that looks great on both desktop and mobile.
- **🌓 Light & Dark Mode:** Automatically adapts to your system's theme with a manual override toggle.
- **⚡ On-Demand Updates:** Trigger chart refreshes instantly from the web interface via a webhook or directly from a Home Assistant automation.

<p align="center">
  <img src="https://github.com/user-attachments/assets/b94d83da-b82d-46d2-983d-93dc44c61703" alt="AI-Generated Report" width="800">
</p>

---

## 🚀 Installation

### Prerequisites

1.  A working **Home Assistant** installation.
2.  The **[AppDaemon Add-on](https://github.com/hassio-addons/addon-appdaemon)** installed and running.
3.  **(Optional)** A configured **Generative AI integration** (e.g., [Google Generative AI](https://www.home-assistant.io/integrations/google_generative_ai_conversation/)) to enable the AI features.

### Step 1: Add the Script

1.  Navigate to your AppDaemon configuration folder (e.g., `/config/appdaemon/apps`).
2.  Create a new file inside the `apps` folder named `music_tracker.py`.
3.  Copy the entire content of the `music_tracker.py` script from this repository and paste it into your new file.

### Step 2: Configure `apps.yaml`

Open your `apps.yaml` file (in the `/config/appdaemon/apps` directory) and add the following block. Customize it to fit your setup.

```yaml
music_tracker:
  module: music_tracker
  class: MusicTracker
  
  # --- Required Settings ---
  # A list of all media_player entities you want to monitor.
  media_players:
    - media_player.living_room_sonos
    - media_player.kitchen_display
    - media_player.bedroom_speaker
    
  # The full path to the database file. Using the /config/ folder is recommended.
  db_path: "/config/music_data_history.db"

  # The full path where the final HTML page will be saved.
  # This MUST be inside your Home Assistant 'www' directory.
  html_output_path: "/config/www/music_charts.html"
  
  # --- AI & Chart Generation ---
  # The service call for your Generative AI integration. Set to false to disable.
  ai_service: "google_generative_ai_conversation/generate_content"
  
  # Time of day (24-hour HH:MM:SS format) to automatically update the charts.
  update_time: "23:59:00"

  # --- Database Optimization (Highly Recommended!) ---
  # Schedule to run the cleanup process.
  # This example runs every Sunday at 3:05 AM.
  cleanup_schedule: "03:05:00"
  cleanup_day_of_week: "sun"
  
  # Enable this to actually delete/prune records.
  # !! Run with 'false' first to see what would be cleaned in the logs !!
  cleanup_execute_on_run: false
  
  # Enable this to shrink the database file size after cleanup.
  cleanup_vacuum_on_complete: true

  # --- Fine-Tuning ---
  # How long a song must play (in seconds) to be counted.
  duration: 30
  
  # How many unique songs from an album must be played for it to appear.
  min_songs_for_album: 4

  # Set to true if you want the "Update Charts" button in the web interface.
  # See Step 3 below to set up the required automation.
  webhook: true
  
  # This is the helper toggle the script listens to for manual or webhook updates.
  chart_trigger_boolean: "input_boolean.music_charts_update"
  
  # Run the chart generation immediately when AppDaemon starts.
  run_on_startup: True
```

### Step 3: Set Up Manual & Webhook Updates (Optional)

To trigger updates from Home Assistant or from the chart page itself, you need a helper toggle and an automation.

#### A. Create a Helper Toggle

This toggle is the "switch" that tells the script to run an update.

1.  In Home Assistant, go to **Settings > Devices & Services > Helpers**.
2.  Click **Create Helper** and select **Toggle**.
3.  Name it `Music Charts Update`. This creates an entity `input_boolean.music_charts_update`, which matches the `chart_trigger_boolean` in the config above.

You can now turn this toggle on anytime in Home Assistant to trigger an immediate update.

#### B. Create the Webhook Automation (For the Web Interface Button)

This automation connects the "Update Charts" button on the HTML page to the toggle you just created.

1.  Go to **Settings > Automations & Scenes**.
2.  Click **Create Automation** and choose **Start with an empty automation**.
3.  Switch to **YAML mode** by clicking the three-dots menu in the top right.
4.  Paste the following YAML code and save it:

```yaml
alias: "Trigger Music Charts Update via Webhook"
description: "Listens for a webhook from the music chart page and turns on the update toggle."
trigger:
  - platform: webhook
    webhook_id: Update_Music_Charts # This ID must be exact
action:
  - service: input_boolean.turn_on
    target:
      entity_id: input_boolean.music_charts_update # The helper you created
mode: single
```

**The update flow is now complete:** Button on HTML Page → Webhook → Automation → Turns on Helper Toggle → AppDaemon Script Runs.

---

## 🖥️ Viewing Your Charts

Once the script has run and generated the file, you can access your personal music charts at:

`http://<your-home-assistant-ip>:8123/local/music_charts.html`

-   Replace `<your-home-assistant-ip>` with the actual IP address or hostname of your Home Assistant instance.
-   Bookmark this page, or add it as a `webpage` card to one of your dashboards for easy access!

---

## 🔧 Database Maintenance Explained

Over time, your database can grow large. This script solves that problem automatically.

-   **Why cleanup is needed:** The `chart_history` table, used to calculate chart position changes (▲/▼), can grow to hundreds of megabytes. Also, quickly skipped songs can clutter your history.
-   **What the script does:**
    1.  **Deletes Skipped Songs:** Removes any entry that was played for less than the `cleanup_threshold_seconds`.
    2.  **Prunes Chart History:** Deletes historical chart data older than `cleanup_prune_keep_days`, keeping only what's needed for recent comparisons.
    3.  **Vacuums the Database:** After cleaning, it runs the `VACUUM` command to physically shrink the database file and reclaim disk space.
-   **Safe by Default:** The `cleanup_execute_on_run: false` setting ensures that your first few runs are a "dry run". Check the AppDaemon logs to see what the script *would have* deleted before you enable it for real.

---

## 🧰 Troubleshooting

-   **Charts are not updating:**
    - Check the AppDaemon logs for any errors related to `music_tracker`. Errors are usually very descriptive.
    - Ensure your `db_path` and `html_output_path` are correct and that AppDaemon has permission to write to those locations.
    - Manually trigger an update by turning on your helper toggle in **Developer Tools > States**.

-   **The "Update Charts" button doesn't work:**
    - Confirm that `webhook: True` is set in your `apps.yaml`.
    - Double-check that your automation's Webhook ID is **exactly** `Update_Music_Charts`.
    - Open your browser's developer tools (F12) on the charts page, go to the **Console** tab, click the button, and see if any network errors appear.

-   **AI Analysis is missing:**
    - Verify your `ai_service` is correctly configured and that the integration is working in Home Assistant.
    - Check the AppDaemon logs. AI generation can sometimes fail or time out, and the logs will contain the error details.
    - Generating the report can take 30-120 seconds. Be patient after triggering an update.
