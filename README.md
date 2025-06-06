# 🎵 Music Tracker & AI Insights for Home Assistant

![image](https://github.com/user-attachments/assets/01c96643-0a0e-45dc-a9eb-ddf18b060480)

![image](https://github.com/user-attachments/assets/b94d83da-b82d-46d2-983d-93dc44c61703)

Uncover the story of your musical taste with this powerful AppDaemon script for Home Assistant. Go beyond simple play counts and dive deep into your listening habits with automatically generated, beautiful, and insightful music charts.

This isn't just a tracker; it's your personal music historian, complete with an optional AI musicologist that provides stunning visual and analytical reports on what you've been listening to.

---

## ✨ Features

- **Automatic Music Tracking:** Passively logs every song you play across your configured Home Assistant media players (Sonos, Volumio, Spotify, etc.).
- **Dynamic Charts:** Generates daily, weekly, monthly, and yearly charts for your top songs, artists, albums, and even playlists/radio stations.
- **Historical Analysis:** See how your top songs rise and fall in the charts with position change indicators (▲, ▼, NEW).
- **Beautiful Web Interface:** All charts are rendered into a single, clean, and modern HTML page, accessible directly from your Home Assistant instance.
- **AI-Powered Insights (Optional):**
    - Connect to a Generative AI service (like the Home Assistant Google Generative AI integration).
    - Receive stunning, self-contained HTML reports with deep analysis, artist visualizations, song recommendations, and even interactive music trivia games!
- **Responsive Design:** The charts page looks great on both desktop and mobile devices.
- **Light & Dark Mode:** The interface automatically adapts to your system's theme and includes a manual toggle.
- **On-Demand Updates:** Trigger a chart refresh instantly from the web interface or through a Home Assistant automation.

---

## 🚀 Installation Guide

### Prerequisites

1.  **Home Assistant:** You must have a working Home Assistant installation.
2.  **AppDaemon Add-on:** You need the [AppDaemon 4.5+](https://github.com/hassio-addons/addon-appdaemon) add-on installed and running.
3.  **(Optional) Generative AI Integration:** To use the AI analysis feature, you need a working Generative AI integration configured in Home Assistant, such as [Google Generative AI Conversation](https://www.home-assistant.io/integrations/google_generative_ai_conversation/).

### Step 1: Add the Script

1.  Navigate to your AppDaemon configuration folder (usually `/config/appdaemon/apps`).
2.  Create a new file inside the `apps` folder named `music_tracker.py`.
3.  Copy the entire content of the `music_tracker.py` script and paste it into this new file.

### Step 2: Configure the App

1.  In the `apps` directory, open your `apps.yaml` file.
2.  Add the following configuration block to the file, and customize it to your needs.

```yaml
music_tracker:
  module: music_tracker
  class: MusicTracker
  
  # --- Required Settings ---
  # List of media player entities to monitor
  media_players:
    - media_player.living_room_sonos
    - media_player.kitchen_display
    - media_player.bedroom_speaker
    
  # Path to the database file. A good location is within the appdaemon config folder.
  db_path: "/config/appdaemon/music_data_history.db"

  # Path where the final HTML page will be saved.
  # This MUST be inside your Home Assistant 'www' directory.
  html_output_path: "/config/www/music_charts.html"
  
  # --- Optional & Recommended Settings ---
  # Enable AI-powered analysis reports.
  ai_service: "google_generative_ai_conversation/generate_content" # Set to false to disable
  
  # Run the chart generation when AppDaemon starts.
  run_on_startup: True
  
  # Time of day (24-hour format) to automatically update the charts.
  update_time: "23:59:00"

  # Enable the "Update Charts" button in the web interface.
  # If you set this to True, you MUST complete Step 3 below.
  webhook: True
  
  # --- Fine-Tuning (Advanced) ---
  # How long a song must play (in seconds) to be counted.
  duration: 30
  
  # How many unique songs from an album must be played for it to appear in the charts.
  min_songs_for_album: 4
```
3. In `configuration.yaml` file you need to make sure Home Assistant allows external urls and dirs, for example:
```yaml
homeassistant:
  allowlist_external_urls:
    - http://192.168.86.220:8123
    - http://homeassistant.local:8123

  allowlist_external_dirs:
    - "/config/www"
```
4. Restart Home Assistant (if you modify configuration.yaml file)

### Step 3: (Required if `webhook: True`) Webhook Setup

To use the **"Update Charts"** button on the web page, you need to connect it to a Home Assistant automation. This process links the button press to the AppDaemon script.

#### Part A: Create a Helper Toggle

This toggle acts as the "switch" that the automation will flip to tell the script to run.

1.  In Home Assistant, go to **Settings > Devices & Services > Helpers**.
2.  Click **Create Helper** and select **Toggle**.
3.  Give it a **Name**, for example, `Music Charts Update`. This will create an entity with an ID like `input_boolean.music_charts_update`. The script will listen for this helper to be turned on.

#### Part B: Create the Automation

This automation will listen for the webhook from the button and flip the toggle you just created.

1.  Go to **Settings > Automations & Scenes**.
2.  Click **Create Automation** and choose **Start with an empty automation**.
3.  Give your automation a descriptive name, like "Trigger Music Charts Update".

4.  **Configure the Trigger:**
    - In the **Triggers** section, click **Add Trigger** and select **Webhook**.
    - For the **Webhook ID**, enter `Update_Music_Chats`. **This must match exactly.**

5.  **Configure the Action:**
    - In the **Actions** section, click **Add Action**.
    - Select **Call Service** and choose the service **Input boolean: Turn on** (`input_boolean.turn_on`).
    - For the **Target**, click **Choose entity** and select the `Music Charts Update` toggle you created in Part A.

6.  Click **Save**.

The flow is now complete: Button Press → Webhook → Automation Runs → Turns on Helper Toggle → AppDaemon sees the toggle and updates the charts.

---

## 🖥️ Viewing Your Charts

Once the script runs for the first time, you can access your charts page at:

`http://<your-home-assistant-ip>:8123/local/music_charts.html`

-   Replace `<your-home-assistant-ip>` with the IP address of your Home Assistant instance.
-   Bookmark this page or add it as a `webpage` card to your dashboard. It's recomended to use `Pannel (single card)` dashboard for best results.

---

## 🔧 Troubleshooting

-   **Charts are not updating:**
    - Check the AppDaemon logs for any errors related to `music_tracker`.
    - Ensure the `update_time` in `apps.yaml` is a valid "HH:MM:SS" string.
    - Manually trigger an update by turning on your helper toggle (`input_boolean.music_charts_update`) in Home Assistant's developer tools.

-   **"Update Charts" button doesn't work:**
    - Make sure `webhook: True` is set in your `apps.yaml`.
    - Double-check that your Home Assistant automation's Webhook ID is **exactly** `Update_Music_Chats`.
    - Open your browser's developer tools (F12) on the charts page, go to the Console tab, click the button, and see if any errors appear.

-   **AI Analysis is not appearing:**
    - Make sure your `ai_service` is correctly configured in `apps.yaml` and matches an installed and working Generative AI integration.
    - Check the AppDaemon logs. AI generation can sometimes fail or time out. The logs will provide clues.
    - Be patient! Depending on your hardware and the AI service, generating the report can take a minute or two.

---
