"""
This script tracks your music listening habits across your media players.
Builds a database of your listening history.
Generates daily charts for your top songs, artists, albums, and more.
Provides insights into your musical tastes.
Includes a fully integrated, automated database cleanup and optimization
process to remove skipped tracks and prune old chart history, keeping the
database lean and efficient.
---

#apps.yaml example:
music_tracker:
  module: music_tracker
  class: MusicTracker
  db_path: "/config/music_data_history.db"
  duration: 30
  min_songs_for_album: 4
  update_time: "23:59:00"
  media_players:
    - media_player.patio
    - media_player.kitchen
  html_output_path: "/homeassistant/www/music_charts.html"
  ai_service: "google_generative_ai_conversation/generate_content"
  run_on_startup: True
  webhook: False

  # --- Database Cleanup Options ---
  # Schedule to run the cleanup process. Recommended to run during off-hours.
  # Example: Run every Sunday at 3:05 AM.
  cleanup_schedule: "03:05:00"
  cleanup_day_of_week: "sun"
  
  # --- Skipped Tracks Options ---
  cleanup_threshold_seconds: 60
  
  # --- Chart History Pruning Options ---
  # Set to true to enable pruning of the chart_history table.
  cleanup_prune_chart_history: true
  # Keep data for this many days. 62 days is good for monthly comparisons.
  cleanup_prune_keep_days: 62

  # --- Execution Options ---
  cleanup_execute_on_run: true
  
  # Set to true to run VACUUM and reclaim disk space after cleanup.
  cleanup_vacuum_on_complete: true
"""

import appdaemon.plugins.hass.hassapi as hass
import datetime
import sqlite3
import re
import time
import threading
import json
import os
import jinja2
import random

TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate" />
<meta http-equiv="Pragma" content="no-cache" />
<meta http-equiv="Expires" content="0" />
<title>Music Charts</title>
<style>
:root{color-scheme:light dark;--bg-light:#f4f4f9;--bg-dark:#1a1a1a;--text-light:#333;--text-dark:#eee;--card-light:#fff;--card-dark:#2a2a2a;--accent-light:#3498db;--accent-dark:#2980b9;}
*{box-sizing:border-box;margin:0;padding:0;}
body{font-family:sans-serif;background:var(--bg-light);color:var(--text-light);padding:1em;}
body.dark-mode{background:var(--bg-dark);color:var(--text-dark);}
#refreshPageButton,#toggleDarkMode,#toggleUpdates{padding:.4em 1em;font-size:.75rem;color:#fff;background:#007bff;border:none;border-radius:5px;cursor:pointer;margin-right:.5em;}
#toggleUpdates:disabled{background:#6c757d;cursor:not-allowed;}
header{display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;margin-bottom:1em;}
h1{font-size:1.6rem;color:var(--accent-light);}
body.dark-mode h1{color:var(--accent-dark);}
#controls label{margin-right:1em;font-size:.9rem;color:#34495e;cursor:pointer;}
body.dark-mode #controls label{color:#ccc;}
#generated-at{font-size:.8rem;color:#7f8c8d;}
main{display:flex;flex-direction:column;gap:2em;}
.chart-section{background:var(--card-light);border-radius:8px;padding:1em;}
body.dark-mode .chart-section{background:var(--card-dark);}
.chart-section h2{color:var(--accent-light);}
body.dark-mode .chart-section h2{color:var(--accent-dark);}
.chart-tables{display:flex;flex-wrap:wrap;gap:1em;}
.table-container{flex:1 1 calc(33.33% - 1em);min-width:280px;}
table{width:100%;border-collapse:collapse;margin-bottom:.5em;}
th,td{padding:.5em;text-align:start;word-break:break-word;font-size:.8rem;}
th{background:var(--accent-light);color:#fff;}
tbody tr:nth-child(even){background:#ecf0f1;}
body.dark-mode tbody tr:nth-child(even){background:#3a3a3a;}
tbody tr:hover{background:var(--hover-light);}
body.dark-mode tbody tr:hover{background:var(--hover-dark);}
h3{margin:.5em 0;font-size:1rem;color:#2980b9;}
.ai-container .chart-container{max-height:90vh;}
.change-up{color:green;font-weight:bold;}
.change-down{color:red;font-weight:bold;}
.change-new{color:orange;font-weight:bold;}
.stats-container{background:#f9f5f0;border-radius:8px;padding:.5em;}
body.dark-mode .stats-container{background:#3a2e24;}
.stats-container h3{color:#e67e22;font-size:1rem;margin-bottom:.3em;}
.stats-container table th{background:#e67e22;color:#fff;}
#update-status-area p{margin-bottom:.5em;font-size:1.1em;}
#countdown-refresh-button{padding:.5em 1.2em;font-size:1rem;color:#fff;background:#007bff;border:none;border-radius:5px;cursor:pointer;}
#countdown-refresh-button:disabled{background:#6c757d;cursor:not-allowed;}
#countdown-refresh-button:hover:not(:disabled){background:#0056b3;}
#ai-analysis h2{color:#856404;}
@media (max-width:768px){
.table-container{flex:1 1 100%;}
header{flex-direction:column;align-items:flex-start;}
header>*:not(:last-child){margin-bottom:1em;}
#controls{display:grid;grid-template-columns:1fr 1fr;gap:10px;width:100%;margin:0;}
#controls label{padding:.7em .5em;margin:0;background:rgba(0,0,0,.04);border-radius:6px;text-align:center;}
body.dark-mode #controls label{background:rgba(255,255,255,.1);}
#controls label:hover{background:rgba(0,0,0,.1);}
body.dark-mode #controls label:hover{background:rgba(255,255,255,.2);}
#action-buttons{display:grid;width:100%;grid-template-columns:1fr 1fr;gap:10px;}
#action-buttons button{margin:0;width:100%;}
}
</style>
</head>
<body>
<header>
<h1>Music Charts</h1>
<div id="controls">
<label><input type="checkbox" data-period="daily" checked> Daily</label>
<label><input type="checkbox" data-period="weekly" checked> Weekly</label>
<label><input type="checkbox" data-period="monthly" checked> Monthly</label>
<label><input type="checkbox" data-period="yearly" checked> Yearly</label>
</div>
<p id="generated-at">Generated at {{ generated_at }}{% if ai_analysis %}<br/><a href="#ai-analysis" id="ai-indicator" style="color: light-blue">AI Report Available</a>{% endif %}</p>
<div id="action-buttons">{% if webhook %}<button id="toggleUpdates" onclick="triggerWebhook()">Update Charts</button>{% endif %}<button id="refreshPageButton">Refresh Page</button><button id="toggleDarkMode">Toggle Dark Mode</button></div>
</header>
<main>
{% macro render_table(title, items, cols, current_period) %}
<div class="table-container">
<h3>{{ title }}</h3>{% if items %}
<table>
<thead>
<tr><th>{% for col in cols.keys() %}<th>{{ col }}</th>{% endfor %}{% if current_period != 'yearly' and title != '📻 Channels/Playlists' %}<th>~</th>{% endif %}</tr>
</thead>
<tbody>{% for item in items %}
<tr><td nowrap>{{ loop.index }}</td>{% for key in cols.values() %}<td{% if key in ['plays','change'] %} nowrap{% endif %}>{{ item[key] }}</td>{% endfor %}{% if current_period != 'yearly' and title != '📻 Channels/Playlists' %}<td nowrap>{% if item.new_entry %}<span class="change-new">NEW</span>{% elif item.change > 0 %}<span class="change-up">▲{{ item.change }}</span>{% elif item.change < 0 %}<span class="change-down">▼{{ (-item.change)|abs }}</span>{% else %}–{% endif %}</td>{% endif %}</tr>{% endfor %}
</tbody>
</table>{% else %}<p>No data for {{ title }}</p>{% endif %}</div>
{% endmacro %}
{% for period, data in charts.items() %}
<section id="chart-{{ period }}" class="chart-section">
<h2>Top {{ period.capitalize() }} ({{ data.dates }})</h2>
<div class="chart-tables">
{{ render_table('🎵 Songs', data.songs, {'Artist':'artist','Title':'title','▶️':'plays'}, period) }}
{{ render_table('👤 Artists', data.artists, {'Artist':'artist','▶️':'plays'}, period) }}
{{ render_table('💽 Albums', data.albums, {'Artist':'artist','Album':'album','▶️':'tracks'}, period) }}
{{ render_table('📻 Channels/Playlists', data.media_channels, {'Channel':'channel','▶️':'plays'}, period) }}
<div class="table-container stats-container" style="max-width:30%;">
<h3>📈 {{ period.capitalize() }} Statistics</h3>
<table>
<thead>
<tr><th>Metric</th><th>Value</th></tr>
</thead>
<tbody>
<tr><td>Days Collected</td><td>{{ overview[period].days }}</td></tr>
<tr><td>Unique Songs</td><td>{{ overview[period].unique_songs }}</td></tr>
<tr><td>Total Plays</td><td>{{ overview[period].total_plays }}</td></tr>
<tr><td>Unique Albums</td><td>{{ overview[period].unique_albums }}</td></tr>
<tr><td>Unique Artists</td><td>{{ overview[period].unique_artists }}</td></tr>
</tbody>
</table>
</div></div></section>
{% endfor %}
{% if ai_analysis %}
<div id="update-status-area" style="padding:1em;text-align:center;"></div>
<section id="ai-analysis">
<h2>🔮 AI Analysis</h2>
{{ ai_analysis|safe }}
</section>
{% endif %}
</main>
<script>
(function(){
let d=localStorage.getItem('dark_mode'),p=window.matchMedia&&window.matchMedia('(prefers-color-scheme: dark)').matches;
if(d==='1'||(d===null&&p))document.body.classList.add('dark-mode');
})();
document.addEventListener("DOMContentLoaded",function(){
let r=document.getElementById('refreshPageButton'),t=document.getElementById('toggleDarkMode');
if(r)r.onclick=function(){location.reload();};
if(t)t.onclick=function(){let n=document.body.classList.toggle('dark-mode');localStorage.setItem('dark_mode',n?'1':'0');};
document.querySelectorAll("#controls input[type=checkbox]").forEach(function(cb){
let per=cb.dataset.period,s=localStorage.getItem('show_'+per),sec=document.getElementById('chart-'+per);
cb.checked=s===null?true:s==="1";
if(sec)sec.style.display=cb.checked?"":"none";
cb.onchange=function(){localStorage.setItem('show_'+per,cb.checked?"1":"0");if(sec)sec.style.display=cb.checked?"":"none";};
});
});
function triggerWebhook() {
const originalUpdateButton=document.getElementById('toggleUpdates');
if(!originalUpdateButton||originalUpdateButton.style.display==='none'){return;}
originalUpdateButton.style.display='none';
const statusArea=document.getElementById('update-status-area');
statusArea.innerHTML=`<p>Update request sent! Please wait while new AI report is generated.</p><button id="countdown-refresh-button" disabled>Refresh in <span id="countdown-timer">30</span>s</button>`;
fetch("/api/webhook/Update_Music_Charts",{method:"POST"}).then(r=>{if(r.ok){console.log("Webhook triggered!");}else{console.error("Failed:",r.statusText);}}).catch(e=>console.error("Error:",e));
let countdown=30,timerSpan=document.getElementById('countdown-timer'),newRefreshButton=document.getElementById('countdown-refresh-button');
const intervalId=setInterval(()=>{
countdown--;timerSpan.innerText=countdown;
if(countdown<=0){clearInterval(intervalId);newRefreshButton.disabled=false;newRefreshButton.innerText='✅ Refresh Now';newRefreshButton.onclick=()=>location.reload();}
},1000);
}
</script>
</body>
</html>
"""

AI_PROMPT_1 = [
    "You are a 'Musical Insights Web Weaver,' an AI expert tasked with creating a beautiful, responsive, and insightful HTML widget from music listening data.",
    "This widget must be self-contained and embeddable, providing an excellent user experience on both mobile and desktop. Prioritize modern, visually stunning, and engaging design.",
    "Begin the HTML output with a prominent main title displaying `Your Musical Insights for [Analyzed Time Period]`, with the period inferred from the provided listening data.",

    "Core Content & Analysis:",
    "1. Musical Preferences Analysis: Deeply analyze provided data to reveal top genres, artists, predominant moods (if inferable), and notable listening patterns/shifts. Frame all insights positively.",
    "   - Identifying notable listening patterns, such as periods of specific genre focus, discovery phases, consistent repeat listening, or any surprising findings or evolution in taste.",
    "   - Highlight connections between artists/genres, and provide overarching themes or summaries of my musical journey.",
    "   - Frame all analysis with positive and encouraging language, celebrating my unique musical journey and preferences.",
    "2. Recommendations: Suggest 3-5 new artists/songs based on habits, including fun, engaging trivia for each.",
    "3. Interactive Game (Highly Desired): Implement a small, fun, self-contained HTML/CSS/JS game related to music preferences and recommendations (e.g., trivia on artists, lyrics, play counts, chart positions, etc.). The game should use buttons and other clickable elements—no typing required.",
    "4. Dynamic AI Artist Visualization (Mandatory):",
    "   - Image: Generate a single, visually striking image featuring 1-2 of the user's top artists. This is the ONLY image allowed in the HTML output.",
    "   - Artist for Visualization: The primary artist for visualization is '{identified_artist_name}'. If no specific artist is provided (e.g., if '{identified_artist_name}' is a generic placeholder like 'a musician'), you may select a prominent artist from the provided data or choose a generic popular one if no data is available.",
    "   - Pollinations.ai Prompt (Crucial Instructions): For EACH request, you MUST generate a NEW, unique, and imaginative prompt string to be used with Pollinations.ai. The prompt MUST explicitly incorporate the actual name of the artist identified above (i.e., '{identified_artist_name}') AND strongly aim to replicate the artist's actual physical likeness and recognizable features as closely as possible. The goal is an image that is as similar as possible to the artist's look. Combine 2-4 diverse elements from your own variations (e.g., style, setting, mood, activity) to create fresh concepts each time. If you choose to create a banner-style image (e.g., a wide aspect ratio like 16:9 or 21:9), you MAY add `&width=[VALUE]&height=[VALUE]` parameters to the URL (e.g., `&width=1200&height=400`). You decide if a banner aspect ratio is most visually appealing for the chosen artist.",
    "   - Model: Use `model=turbo` or `flux`.",
    "   - URL: `https://pollinations.ai/p/[URL_ENCODED_PROMPT]?model=[SELECTED_MODEL]`",
    "   - Embedding: Embed using `<img>` with descriptive `alt` text. Style `<img>` (scoped to `.ai-container`) for responsiveness. Credit Pollinations.ai with a link.",
    "Design & Technical Requirements:",
    "1. Output Format: Generate ONLY pure HTML code. The entire output MUST be wrapped in a single `<div class=\"ai-container\">` and contain NO `<html>`, `<head>`, `<body>` tags, markdown, or conversational text.",
    "2. CSS Styling:",
    "   - Embed ALL CSS within `<style>` tags directly inside `ai-container` (e.g., at the beginning).",
    "   - Scoping: ALL CSS rules MUST be prefixed with `.ai-container` to avoid host page interference. Avoid global selectors (`*`, `body`, `html`) unless scoped.",
    "   - Visuals: Achieve a modern, clean, polished, and unique aesthetic. Develop a harmonious color palette. Use clear, modern web-safe (or Google) fonts. Use ample whitespace. `ai-container` should be `width: 100%`.",
    "   - Image Constraint: Beyond the AI artist image, NO other static images/icons (unless icon font) or complex background images are allowed.",
    "3. Data Visualization:",
    "   - Use Chart.js (via CDN, embedded JS) to create a seamless and visually appealing set of charts, such as a Pie/Doughnut chart for top genres, a Bar chart for top artists, and a Line chart for daily listening trends, while allowing creative freedom in generating additional graphs beyond these examples.",
    "   - Avoid generic 'Others' categories; display distinct top entries.",
    "   - Fallback: Pure CSS charts (scoped) if Chart.js is too complex.",
    "4. Responsiveness (Mobile & Desktop):",
    "   - Primary content should largely fit within ~85vh viewport height on load.",
    "   - Use CSS Flexbox or Grid for layout.",
    "   - Mobile (<768px): Content blocks (charts, AI image, text, game) MUST stack vertically.",
    "   - Desktop (>=768px): Arrange related sub-containers side-by-side.",
    "   - Apply sensible `max-height` to visuals (e.g., AI image ~45vh, charts 300-400px).",
    "   - NO horizontal scrolling.",
    "5. Structure: Organize content logically into: 'Musical Analysis' (including AI image), 'Artist & Song Recommendations', and 'Interactive Game'. All JavaScript (Chart.js, game logic) must be embedded and operate within `.ai-container`."
]


AI_PROMPT_2 = [
    "You are a 'Musical Insights Web Weaver,' an AI expert tasked with creating a beautiful, responsive, and insightful HTML widget from music listening data.",
    "This widget must be self-contained and embeddable, providing an excellent user experience on both mobile and desktop. Prioritize modern, visually stunning, and engaging design.",
    "Begin the HTML output with a prominent main title displaying `Your Musical Insights for [Analyzed Time Period]`, with the period inferred from the provided listening data.",

    "Core Content & Analysis:",
    "1. Musical Preferences Analysis: Deeply analyze provided data to reveal top genres, artists, predominant moods (if inferable), and notable listening patterns/shifts. Frame all insights positively.",
    "   - Identifying notable listening patterns, such as periods of specific genre focus, discovery phases, consistent repeat listening, or any surprising findings or evolution in taste.",
    "   - Highlight connections between artists/genres, and provide overarching themes or summaries of my musical journey.",
    "   - Frame all analysis with positive and encouraging language, celebrating my unique musical journey and preferences.",
    "   - Temporal Listening Analysis: Based on the timestamps, analyze my listening habits throughout the day. Identify peak listening hours (e.g., mornings, late nights), compare weekday vs. weekend patterns, and try to find connections between the time of day and the type of music I listen to (e.g., 'energetic music in the mornings, calmer tracks at night').",
    "   - Musical Taste Patterns: Identify periods of specific genre focus, discovery phases, consistent repeat listening, or any surprising findings or evolution in my taste.",
    "2. Recommendations: Suggest 3-5 new artists/songs based on habits, including fun, engaging trivia for each.",
    "3. Interactive Game (Highly Desired): Implement a small, fun, self-contained HTML/CSS/JS game related to music preferences and recommendations (e.g., trivia on artists, lyrics, play counts, chart positions, etc.). The game should use buttons and other clickable elements—no typing required.",
    "4. Dynamic AI Artist Visualization (Mandatory):",
    "   - Image: Generate a single, visually striking image featuring 1-2 of the user's top artists. This is the ONLY image allowed in the HTML output.",
    "   - Artist for Visualization: The primary artist for visualization is '{identified_artist_name}'. If no specific artist is provided (e.g., if '{identified_artist_name}' is a generic placeholder like 'a musician'), you may select a prominent artist from the provided data or choose a generic popular one if no data is available.",
    "   - Pollinations.ai Prompt (Crucial Instructions): For EACH request, you MUST generate a NEW, unique, and imaginative prompt string to be used with Pollinations.ai. The prompt MUST explicitly incorporate the actual name of the artist identified above (i.e., '{identified_artist_name}') AND strongly aim to replicate the artist's actual physical likeness and recognizable features as closely as possible. The goal is an image that is as similar as possible to the artist's look. Combine 2-4 diverse elements from your own variations (e.g., style, setting, mood, activity) to create fresh concepts each time. If you choose to create a banner-style image (e.g., a wide aspect ratio like 16:9 or 21:9), you MAY add `&width=[VALUE]&height=[VALUE]` parameters to the URL (e.g., `&width=1200&height=400`). You decide if a banner aspect ratio is most visually appealing for the chosen artist.",
    "   - Model: Use `model=turbo` or `flux`.",
    "   - URL: `https://pollinations.ai/p/[URL_ENCODED_PROMPT]?model=[SELECTED_MODEL]`",
    "   - Embedding: Embed using `<img>` with descriptive `alt` text. Style `<img>` (scoped to `.ai-container`) for responsiveness. Credit Pollinations.ai with a link.",
    "Design & Technical Requirements:",
    "1. Output Format: Generate ONLY pure HTML code. The entire output MUST be wrapped in a single `<div class=\"ai-container\">` and contain NO `<html>`, `<head>`, `<body>` tags, markdown, or conversational text.",
    "2. CSS Styling:",
    "   - Embed ALL CSS within `<style>` tags directly inside `ai-container` (e.g., at the beginning).",
    "   - Scoping: ALL CSS rules MUST be prefixed with `.ai-container` to avoid host page interference. Avoid global selectors (`*`, `body`, `html`) unless scoped.",
    "   - Visuals: Achieve a modern, clean, polished, and unique aesthetic. Develop a harmonious color palette. Use clear, modern web-safe (or Google) fonts. Use ample whitespace. `ai-container` should be `width: 100%`.",
    "   - Image Constraint: Beyond the AI artist image, NO other static images/icons (unless icon font) or complex background images are allowed.",
    "3. Data Visualization:",
    "   - Use Chart.js (via CDN, embedded JS) to create a seamless and visually appealing set of charts, such as a Pie/Doughnut chart for top genres, a Bar chart for top artists, and a Line chart for daily listening trends, while allowing creative freedom in generating additional graphs beyond these examples.",
    "   - Avoid generic 'Others' categories; display distinct top entries.",
    "   - Fallback: Pure CSS charts (scoped) if Chart.js is too complex.",
    "4. Responsiveness (Mobile & Desktop):",
    "   - Primary content should largely fit within ~85vh viewport height on load.",
    "   - Use CSS Flexbox or Grid for layout.",
    "   - Mobile (<768px): Content blocks (charts, AI image, text, game) MUST stack vertically.",
    "   - Desktop (>=768px): Arrange related sub-containers side-by-side.",
    "   - Apply sensible `max-height` to visuals (e.g., AI image ~45vh, charts 300-400px).",
    "   - NO horizontal scrolling.",
    "5. Structure: Organize content logically into: 'Musical Analysis' (including AI image), 'Artist & Song Recommendations', and 'Interactive Game'. All JavaScript (Chart.js, game logic) must be embedded and operate within `.ai-container`."
]


class TrackManager:
    """
    Manages recently played tracks to prevent duplicates within a short timeframe.
    """
    def __init__(self):
        self.played_tracks = {}
        self.lock = threading.Lock()
        self.cleanup_interval = 60  # seconds
        self.track_memory_duration = 600  # seconds
        self.cleanup_thread = threading.Thread(target=self.cleanup_tracks_periodically)
        self.cleanup_thread.daemon = True
        self.cleanup_thread.start()

    def add_track(self, track_id):
        with self.lock:
            self.played_tracks[track_id] = time.time()

    def has_been_played_recently(self, track_id):
        with self.lock:
            return track_id in self.played_tracks

    def _perform_cleanup(self):
        current_time = time.time()
        with self.lock:
            to_remove = [
                tid for tid, ts in self.played_tracks.items()
                if current_time - ts > self.track_memory_duration
            ]
            for tid in to_remove:
                del self.played_tracks[tid]

    def cleanup_tracks_periodically(self):
        while True:
            time.sleep(self.cleanup_interval)
            self._perform_cleanup()


class MusicTracker(hass.Hass):
    """
    AppDaemon app to track music history, generate charts, and self-optimize its database.
    """

    def initialize(self):
        self.log("MusicTracker Initializing...")
        
        # --- Original Configuration Loading ---
        self.media_players = self.args.get("media_players", [])
        if not isinstance(self.media_players, list):
            self.media_players = [self.media_players] if self.media_players else []

        self.duration_to_consider_played = self.args.get("duration", 30)
        self.min_songs_for_album_chart = self.args.get("min_songs_for_album", 3)
        self.chart_update_time = self.args.get("update_time", "23:59:00")
        self.db_path = self.args.get("db_path", "/config/music_data_history.db")
        self.html_output_path = self.args.get("html_output_path", "/homeassistant/www/music_charts.html")
        self.ai_service = self.args.get("ai_service", False)
        self.webhook = self.args.get("webhook", False)

        # --- Database Cleanup Configuration Loading ---
        self.cleanup_schedule = self.args.get("cleanup_schedule", "03:45:00")
        self.cleanup_day_of_week = self.args.get("cleanup_day_of_week", "sun")
        self.cleanup_threshold_seconds = self.args.get("cleanup_threshold_seconds", 60)
        self.cleanup_prune_enabled = self.args.get("cleanup_prune_chart_history", True)
        self.cleanup_prune_keep_days = self.args.get("cleanup_prune_keep_days", 62)
        self.cleanup_execute_mode = self.args.get("cleanup_execute_on_run", True)
        self.cleanup_vacuum_on_complete = self.args.get("cleanup_vacuum_on_complete", True)
        
        # --- Validation and Setup ---
        if not self.db_path:
            self.log("db_path not configured. MusicTracker cannot function.", level="ERROR")
            return

        self.track_manager = TrackManager()
        self.create_db_tables()
        self.cleanup_old_db_tracks()

        # Setup Chart Generation Schedule
        try:
            time_obj = datetime.time.fromisoformat(self.chart_update_time)
            self.run_daily(self.scheduled_update_html_callback, time_obj)
            self.log(f"Scheduled HTML chart updates at: {self.chart_update_time}")
        except (ValueError, TypeError):
            self.log(f"Invalid chart_update_time: '{self.chart_update_time}'. Use HH:MM:SS. Scheduling disabled.", level="ERROR")

        # Setup Database Cleanup Schedule
        if self.cleanup_schedule:
            try:
                cleanup_time_obj = datetime.time.fromisoformat(self.cleanup_schedule)
                self.run_daily(self.run_optimization, cleanup_time_obj, constrain_days=self.cleanup_day_of_week)
                self.log(f"Scheduled Database Cleanup to run at {self.cleanup_schedule} on {self.cleanup_day_of_week or 'all days'}.")
                if self.cleanup_execute_mode:
                    self.log("DB Cleanup will run in EXECUTE mode.", level="WARNING")
                else:
                    self.log("DB Cleanup will run in DRY RUN mode.", level="INFO")
            except (ValueError, TypeError):
                self.log(f"Invalid cleanup_schedule: '{self.cleanup_schedule}'. Use HH:MM:SS. Cleanup scheduling disabled.", level="ERROR")
        else:
            self.log("Database cleanup is not scheduled. Set 'cleanup_schedule' to enable it.", level="INFO")
            
        # Original Listener Setup
        self.input_boolean_chart_trigger = self.args.get("chart_trigger_boolean", "input_boolean.music_charts")
        if self.entity_exists(self.input_boolean_chart_trigger):
            self.listen_state(self.manual_update_html_callback, self.input_boolean_chart_trigger, new="on")
            self.log(f"Listening to {self.input_boolean_chart_trigger} for manual updates.")
            self.set_state(self.input_boolean_chart_trigger, state="off", attributes={"last_triggered": "Never"})
        else:
            self.log(f"Input boolean {self.input_boolean_chart_trigger} not found. Manual trigger disabled.", level="WARNING")

        self._active_track_timers = {}
        if self.media_players:
            for player_entity_id in self.media_players:
                if self.entity_exists(player_entity_id):
                    self.listen_state(self.handle_media_player_event, player_entity_id, attribute="all")
                    self.log(f"Listening for state changes on {player_entity_id}")
                else:
                    self.log(f"Configured media player {player_entity_id} not found in Home Assistant.", level="WARNING")
        else:
            self.log("No media_players configured to monitor.", level="WARNING")

        self._last_charts_data = {}
        if self.args.get("run_on_startup", True):
            self.log("run_on_startup is true, generating charts now.")
            self.update_html_and_sensors()

        self.log("MusicTracker Initialization Complete.")

    def scheduled_update_html_callback(self, kwargs):
        """
        Called daily at the configured time to regenerate charts and HTML.
        """
        self.log("Scheduled daily chart update triggered.")
        self.update_html_and_sensors()

    def manual_update_html_callback(self, entity, attribute, old, new, kwargs):
        """
        Called when the input_boolean for manual update is turned on.
        """
        self.log(f"Manual chart update triggered by {entity}.")
        self.update_html_and_sensors()
        if self.entity_exists(self.input_boolean_chart_trigger):
            self.set_state(self.input_boolean_chart_trigger, state="off",
                        attributes={"last_triggered": datetime.datetime.now().isoformat()})

    def update_html_and_sensors(self):
        """
        Main routine: gather data for each period, compute overview stats,
        render HTML, and optionally call AI service.
        """
        self.log("Starting chart data generation and HTML/Sensor update process...")
        timeframes = {
            "daily":   "1 day",
            "weekly":  "7 days",
            "monthly": "30 days",
            "yearly":  "365 days"
        }
        current_charts_data = {}
        all_data_ok = True

        overview_stats_per_period = {}
        for period_name, days_str in timeframes.items():
            stats = self.get_overview_stats_for_period(days_str)
            overview_stats_per_period[period_name] = stats
        self._last_overview_stats_per_period = overview_stats_per_period

        for period_name, days_str in timeframes.items():
            self.log(f"Generating chart data for period: {period_name} ({days_str})")
            try:
                current_charts_data[period_name] = {
                    "songs": self.get_top_songs(days_str, 100, period_name),
                    "artists": self.get_top_artists(days_str, 100, period_name),
                    "albums": self.get_top_albums(days_str, 100, period_name),
                    "media_channels": self.get_top_media_channels(days_str, 100, period_name),
                    "dates": self.get_chart_dates_for_period(days_str)
                }
                self.store_chart_data_history("songs", period_name, current_charts_data[period_name]["songs"])
                self.store_chart_data_history("artists", period_name, current_charts_data[period_name]["artists"])
                self.store_chart_data_history("albums", period_name, current_charts_data[period_name]["albums"])
                self.store_chart_data_history("media_channels", period_name, current_charts_data[period_name]["media_channels"])
            except Exception as e:
                self.log(f"Error generating data for period {period_name}: {e}", level="ERROR")
                all_data_ok = False
                current_charts_data[period_name] = {
                    "songs": [], "artists": [], "albums": [], "media_channels": [], "dates": "Error Generating Data"
                }

        if not all_data_ok:
            self.log("Errors during chart data generation. HTML might be incomplete.", level="WARNING")

        self._last_charts_data = current_charts_data
        self.render_and_write_html(current_charts_data, None, overview_stats_per_period)

        if self.ai_service:
            chosen_method = random.choice(["charts", "recent_songs"])
            if chosen_method == "charts":
                self._call_ai_analysis(current_charts_data)
            else: 
                self._call_ai_analysis_with_recent_songs()
        else:
            self.log("AI service not configured. Skipping AI analysis.")

        self.log("HTML update process finished.")

    def _call_ai_analysis(self, charts_data_for_ai):
        """
        Sends chart data to the configured AI service for analysis and waits for callback.
        """
        if not isinstance(self.ai_service, str): return
        domain, service = self.ai_service.split("/", 1)
        prompt = self.build_prompt_from_chart_data(charts_data_for_ai)
        
        try:
            self.call_service(f"{domain}/{service}", prompt=prompt, timeout=120, hass_timeout=120, callback=self._ai_response_callback)
        except Exception as e:
            self.log(f"Error initiating AI service call: {e}", level="ERROR")
            self.render_and_write_html(self._last_charts_data, f"Error initiating AI analysis: {e}", self._last_overview_stats_per_period)

    def _call_ai_analysis_with_recent_songs(self):
        """
        Gets recent songs, builds a prompt, and calls the AI.
        """
        if not self.ai_service: return
        last_100_songs = self.get_last_n_unique_songs_with_timestamps(100)
        
        if not last_100_songs:
            self.render_and_write_html(self._last_charts_data, "Could not generate AI analysis: no recent listening data found.", self._last_overview_stats_per_period)
            return

        prompt = self.build_ai_prompt_from_recent_songs(last_100_songs)
        domain, service = self.ai_service.split("/", 1)

        try:
            self.call_service(f"{domain}/{service}", prompt=prompt, timeout=120, hass_timeout=120, callback=self._ai_response_callback)
        except Exception as e:
            self.log(f"Error initiating AI service call: {e}", level="ERROR")
            self.render_and_write_html(self._last_charts_data, f"Error initiating AI analysis: {e}", self._last_overview_stats_per_period)


    def _ai_response_callback(self, resp):
        """
        Callback after AI service returns. Extracts AI text and re-renders HTML including it.
        """
        ai_text = None
        if isinstance(resp, dict):
            if resp.get("success"):
                result = resp.get("result", {})
                if isinstance(result.get("response"), dict):
                    ai_text = result["response"].get("text")
                elif "text" in result:
                    ai_text = result.get("text")
                if not ai_text:
                    ai_text = "AI analysis successful, but no content extracted."
            else:
                err_msg = resp.get("error", {}).get("message", "Unspecified error from AI service.")
                ai_text = f"AI analysis failed: {err_msg}"
        else:
            ai_text = "AI analysis returned an unexpected response format."

        if hasattr(self, '_last_charts_data') and self._last_charts_data:
            self.render_and_write_html(self._last_charts_data, ai_text, self._last_overview_stats_per_period)
        else:
            self.log("Cannot re-render HTML with AI: _last_charts_data is missing.", level="ERROR")

    def render_and_write_html(self, charts_data_to_render, ai_text_content, overview_stats_per_period):
        """
        Renders the HTML using Jinja2 template and writes to the configured file path.
        """
        if ai_text_content:
            ai_text_content = re.sub(r'^\s*```(?:html)?\s*|\s*```\s*$', '', ai_text_content)

        try:
            env = jinja2.Environment(loader=jinja2.BaseLoader(), autoescape=jinja2.select_autoescape(['html', 'xml']))
            template = env.from_string(TEMPLATE)
            html_output = template.render(
                generated_at=datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                charts=charts_data_to_render,
                overview=overview_stats_per_period,
                ai_analysis=ai_text_content,
                webhook=self.webhook
            )
        except Exception as e:
            self.log(f"Jinja2 template rendering error: {e}", level="ERROR")
            html_output = f"<html><body><h1>Error rendering charts page</h1><p>Details: {e}</p></body></html>"

        try:
            with open(self.html_output_path, "w", encoding="utf-8") as f:
                f.write(html_output)
            self.log(f"Successfully wrote {len(html_output)} bytes to {self.html_output_path}")
        except Exception as e:
            self.log(f"Failed to write HTML file to {self.html_output_path}: {e}", level="ERROR")

    def build_prompt_from_chart_data(self, charts_for_prompt):
        """
        Builds a prompt string for the AI service based on chart data.
        """
        top_artist_name = "a musician"
        potential_rates = ["daily", "weekly", "monthly", "yearly"]
        available_rate_keys = [rate for rate in potential_rates if rate in charts_for_prompt and charts_for_prompt[rate]]
        
        selected_rate_key = random.choice(available_rate_keys) if available_rate_keys else None
        data_for_selected_rate = charts_for_prompt.get(selected_rate_key, {}) if selected_rate_key else {}
        top_artists_list = data_for_selected_rate.get("artists", [])
        if top_artists_list: top_artist_name = top_artists_list[0].get('artist', "a musician")
        
        display_name_for_rate = selected_rate_key.capitalize() if selected_rate_key else "Overall"
        dates_str_for_selected_rate = data_for_selected_rate.get("dates", "N/A")

        prompt_lines = [line.format(identified_artist_name=top_artist_name) for line in AI_PROMPT_1]
        prompt_lines.extend([
            f"My listening data for the {display_name_for_rate} period covers: {dates_str_for_selected_rate}.",
            f"\nTop {display_name_for_rate} Songs Data (up to 100):",
            "| Artist | Title | Plays |", "|---|---|---|"
        ])
        songs_to_list = data_for_selected_rate.get("songs", [])[:100]
        if songs_to_list:
            for song in songs_to_list:
                prompt_lines.append(f"| {song.get('artist', 'N/A')} | {song.get('title', 'N/A')} | {song.get('plays', 'N/A')} |")
        else:
            prompt_lines.append(f"| No {display_name_for_rate.lower()} song data available. | | |")
        return "\n".join(prompt_lines)

    def build_ai_prompt_from_recent_songs(self, recent_songs_data):
        """
        Builds a detailed prompt for the AI service based on the last 100 songs played.
        """
        top_artist_name = "a musician"
        if recent_songs_data:
            artist_counts = {}
            for song in recent_songs_data:
                artist = song.get('artist')
                if artist: artist_counts[artist] = artist_counts.get(artist, 0) + 1
            if artist_counts: top_artist_name = max(artist_counts, key=artist_counts.get)

        prompt_lines = [line.format(identified_artist_name=top_artist_name) for line in AI_PROMPT_2]
        if not recent_songs_data:
            prompt_lines.append("\nMy listening data is not available at this moment.")
            return "\n".join(prompt_lines)

        first_date = datetime.datetime.strptime(recent_songs_data[0]['timestamp'], '%Y-%m-%d %H:%M:%S').strftime('%B %d, %Y')
        last_date = datetime.datetime.strptime(recent_songs_data[-1]['timestamp'], '%Y-%m-%d %H:%M:%S').strftime('%B %d, %Y')
        date_range_info = f"This data covers my listening from approximately {last_date} to {first_date}."

        prompt_lines.extend([
            f"\nAnalyze my most recent listening history. {date_range_info}",
            "Below is a list of the last 100 unique songs I've played, with the most recent ones listed first.",
            "\nMy Most Recent Songs (newest first):",
            "| Artist | Title | Played At (Timestamp) |", "|---|---|---|"
        ])
        for song in recent_songs_data:
            artist = str(song.get('artist', 'N/A')).replace('|', '-')
            title = str(song.get('title', 'N/A')).replace('|', '-')
            prompt_lines.append(f"| {artist} | {title} | {song.get('timestamp', 'N/A')} |")
        return "\n".join(prompt_lines)

    def create_db_tables(self):
        """
        Creates the necessary SQLite tables if they do not yet exist.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS music_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT, artist TEXT, title TEXT,
                        album TEXT, media_channel TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS chart_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT, period TEXT,
                        data TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_music_history_timestamp ON music_history (timestamp);")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_chart_history_lookup ON chart_history (type, period, timestamp);")
                conn.commit()
            self.log("DB tables checked/created.")
        except sqlite3.Error as e:
            self.log(f"DB error during table creation: {e}", level="ERROR")

    def cleanup_old_db_tracks(self):
        """
        Deletes music_history entries older than one year to keep the database lean.
        """
        one_year_ago = (datetime.datetime.now() - datetime.timedelta(days=366)).strftime('%Y-%m-%d %H:%M:%S')
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM music_history WHERE timestamp < ?", (one_year_ago,))
                if cursor.rowcount > 0:
                    self.log(f"Cleaned {cursor.rowcount} old tracks (>1yr) from DB.")
                conn.commit()
        except sqlite3.Error as e:
            self.log(f"DB error during old track cleanup: {e}", level="ERROR")

    def handle_media_player_event(self, entity_id, attribute, old_state_data, new_state_data, kwargs):
        """
        Listens for state changes on media player entities.
        """
        old_title = old_state_data.get("attributes", {}).get("media_title")
        new_attributes = new_state_data.get("attributes", {})
        new_title = new_attributes.get("media_title")
        new_player_state = new_state_data.get("state")

        if entity_id in self._active_track_timers:
            if old_title != new_title or new_player_state != "playing":
                self.cancel_timer(self._active_track_timers.pop(entity_id))

        if new_player_state == "playing" and new_attributes.get("media_artist") and new_title:
            track_info = {
                "entity_id": entity_id,
                "artist": new_attributes.get("media_artist"),
                "title": new_title,
                "album": new_attributes.get("media_album_name"),
                "media_channel": new_attributes.get("media_channel") or new_attributes.get("source"),
            }
            self._active_track_timers[entity_id] = self.run_in(self._finalize_and_store_track, self.duration_to_consider_played, track_info_at_play_start=track_info)

    def _finalize_and_store_track(self, kwargs):
        """
        After the delay, check that the same track is still playing before writing to DB.
        """
        track_info = kwargs.get("track_info_at_play_start")
        if not track_info: return
        entity_id = track_info["entity_id"]
        self._active_track_timers.pop(entity_id, None)

        current_state = self.get_state(entity_id, attribute="all")
        if not current_state or current_state.get("state") != "playing": return

        current_attrs = current_state.get("attributes", {})
        if current_attrs.get("media_artist") != track_info["artist"] or current_attrs.get("media_title") != track_info["title"]: return

        artist, title, album, media_channel = track_info["artist"], track_info["title"], track_info["album"], track_info["media_channel"]
        if title.lower() in ["tv", "unknown", "advertisement"]: return

        cleaned_title = self.clean_text_for_chart(title)
        cleaned_album = self.clean_text_for_chart(album) if album else "Unknown Album"
        track_identifier = f"{artist.lower().strip()}|{cleaned_title.lower().strip()}"

        if self.track_manager.has_been_played_recently(track_identifier): return
        self.track_manager.add_track(track_identifier)

        self.store_track_in_db(artist, cleaned_title, cleaned_album or cleaned_title, media_channel)

    def clean_text_for_chart(self, text: str) -> str:
        """Removes common version keywords from track/album titles."""
        if not isinstance(text, str): return ""
        keywords = ['remaster', 'mix', 'remix', 'stereo', 'mono', 'demo', 'deluxe', 'instrumental', 'extended', 'version', 'radio edit', 'live', 'edit', 'anniversary', 'edition', 'single', 'explicit', 'clean', 'original', 'acoustic', 'unplugged']
        pattern = r'\s*[\(\[\-](?:[^\(\)\[\]\-]*\b(?:' + '|'.join(f"{k}\\.?" for k in keywords) + r')\b[^\(\)\[\]\-]*?)[\)\]\-]?\s*'
        cleaned = re.sub(pattern, '', text, flags=re.IGNORECASE).strip()
        return cleaned if cleaned else text

    def store_track_in_db(self, artist, title, album, media_channel):
        """Inserts the given track data into the music_history table."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO music_history (artist, title, album, media_channel, timestamp) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)", (artist, title, album, media_channel))
                conn.commit()
        except sqlite3.Error as e:
            self.log(f"DB error storing track: {e}", level="ERROR")

    def get_chart_dates_for_period(self, days_str):
        """Returns a date range string for entries in music_history."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                query = f"SELECT MIN(timestamp), MAX(timestamp) FROM music_history WHERE timestamp >= datetime('now', '-{days_str}')"
                cursor.execute(query)
                res = cursor.fetchone()
                if res and res[0] and res[1]:
                    s_dt = datetime.datetime.strptime(res[0], '%Y-%m-%d %H:%M:%S')
                    e_dt = datetime.datetime.strptime(res[1], '%Y-%m-%d %H:%M:%S')
                    return s_dt.strftime('%d/%m/%Y') if s_dt.date() == e_dt.date() else f"{s_dt.strftime('%d/%m/%Y')} - {e_dt.strftime('%d/%m/%Y')}"
                return "Date Range N/A"
        except Exception as e:
            self.log(f"Error getting chart dates for '{days_str}': {e}", level="WARNING")
            return "Date Range Error"

    def get_top_songs(self, days_str, limit, period_name):
        """Returns a list of dictionaries for the top songs."""
        previous_chart_data = self.get_previous_chart_data("songs", period_name)
        query = f"SELECT title, artist, album, COUNT(*) as c FROM music_history WHERE timestamp >= datetime('now', '-{days_str}') GROUP BY title, artist, album ORDER BY c DESC, artist, title LIMIT {limit}"
        return self._get_chart_data(query, ["title", "artist", "album", "plays"], "songs", period_name, previous_chart_data)

    def get_top_artists(self, days_str, limit, period_name):
        """Returns a list of dictionaries for the top artists."""
        previous_chart_data = self.get_previous_chart_data("artists", period_name)
        query = f"SELECT artist, COUNT(*) as c FROM music_history WHERE timestamp >= datetime('now', '-{days_str}') AND artist IS NOT NULL AND artist != '' GROUP BY artist ORDER BY c DESC, artist LIMIT {limit}"
        return self._get_chart_data(query, ["artist", "plays"], "artists", period_name, previous_chart_data)

    def get_top_albums(self, days_str, limit, period_name):
        """Returns a list of dictionaries for the top albums."""
        previous_chart_data = self.get_previous_chart_data("albums", period_name)
        query = f"SELECT artist, album, COUNT(DISTINCT title) as c FROM music_history WHERE timestamp >= datetime('now', '-{days_str}') AND album IS NOT NULL AND album != '' AND artist IS NOT NULL AND artist != '' GROUP BY artist, album HAVING c >= {self.min_songs_for_album_chart} ORDER BY c DESC, album, artist LIMIT {limit}"
        return self._get_chart_data(query, ["artist", "album", "tracks"], "albums", period_name, previous_chart_data)

    def get_top_media_channels(self, days_str, limit, period_name):
        """Returns a list of dictionaries for the top media channels."""
        previous_chart_data = self.get_previous_chart_data('media_channels', period_name)
        query = f"SELECT media_channel, COUNT(*) as c FROM music_history WHERE timestamp >= datetime('now', '-{days_str}') AND media_channel IS NOT NULL AND media_channel != '' GROUP BY media_channel ORDER BY c DESC, media_channel LIMIT {limit}"
        return self._get_chart_data(query, ["channel", "plays"], "media_channels", period_name, previous_chart_data)
        
    def _get_chart_data(self, query, keys, category, period, prev_data):
        """Generic function to fetch and process chart data."""
        items_list = []
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(query)
                for rank, row in enumerate(cursor.fetchall(), 1):
                    item = dict(zip(keys, row))
                    change_info = self.calculate_chart_change(prev_data, item, rank, category)
                    item.update(change=change_info['change_value'], new_entry=change_info['is_new_entry'])
                    items_list.append(item)
        except sqlite3.Error as e:
            self.log(f"DB error in _get_chart_data for {category}/{period}: {e}", level="ERROR")
        return items_list

    def calculate_chart_change(self, previous_chart_list, current_item, current_rank, category):
        """Computes rank change or marks as new entry."""
        for idx, prev_item in enumerate(previous_chart_list):
            match = False
            if category == 'songs' and prev_item.get('title') == current_item.get('title') and prev_item.get('artist') == current_item.get('artist'): match = True
            elif category == 'artists' and prev_item.get('artist') == current_item.get('artist'): match = True
            elif category == 'albums' and prev_item.get('album') == current_item.get('album') and prev_item.get('artist') == current_item.get('artist'): match = True
            elif category == 'media_channels' and prev_item.get('channel') == current_item.get('channel'): match = True
            if match:
                return {'change_value': (idx + 1) - current_rank, 'is_new_entry': False}
        return {'change_value': 0, 'is_new_entry': True}

    def store_chart_data_history(self, type_of_chart, period, data_list):
        """Saves chart data JSON to chart_history table."""
        if not data_list: return
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO chart_history (type, period, data, timestamp) VALUES (?, ?, ?, CURRENT_TIMESTAMP)", (type_of_chart, period, json.dumps(data_list)))
                conn.commit()
        except Exception as e:
            self.log(f"Error storing chart history for {type_of_chart}/{period}: {e}", level="WARNING")

    def get_previous_chart_data(self, type_of_chart, period):
        """Retrieves the most recent chart_history JSON for comparison."""
        conditions = {
            "daily": "date(timestamp) = date('now','-1 day')", "weekly": "date(timestamp) >= date('now','-14 days') AND date(timestamp) < date('now','-7 days')",
            "monthly": "date(timestamp) >= date('now','-60 days') AND date(timestamp) < date('now','-30 days')", "yearly": "date(timestamp) >= date('now','-730 days') AND date(timestamp) < date('now','-365 days')",
        }
        condition = conditions.get(period)
        if not condition: return []
        query = f"SELECT data FROM chart_history WHERE type = ? AND period = ? AND {condition} ORDER BY timestamp DESC LIMIT 1"
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(query, (type_of_chart, period))
                res = cursor.fetchone()
                if res and res[0]: return json.loads(res[0])
        except Exception as e:
            self.log(f"Error fetching previous chart for {type_of_chart}/{period}: {e}", level="WARNING")
        return []

    def get_overview_stats_for_period(self, days_str):
        """Computes overview statistics for a given period."""
        stats = {}
        queries = {
            "days": f"SELECT COUNT(DISTINCT date(timestamp)) FROM music_history WHERE timestamp >= datetime('now', '-{days_str}')",
            "unique_songs": f"SELECT COUNT(DISTINCT artist || '|' || title) FROM music_history WHERE timestamp >= datetime('now', '-{days_str}')",
            "total_plays": f"SELECT COUNT(*) FROM music_history WHERE timestamp >= datetime('now', '-{days_str}')",
            "unique_albums": f"SELECT COUNT(DISTINCT artist || '|' || album) FROM music_history WHERE timestamp >= datetime('now', '-{days_str}')",
            "unique_artists": f"SELECT COUNT(DISTINCT artist) FROM music_history WHERE timestamp >= datetime('now', '-{days_str}')"
        }
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                for key, query in queries.items():
                    cursor.execute(query)
                    stats[key] = cursor.fetchone()[0] or 0
        except sqlite3.Error as e:
            self.log(f"DB error in get_overview_stats_for_period ({days_str}): {e}", level="ERROR")
            return {key: 0 for key in queries}
        return stats

    def get_last_n_songs_with_timestamps(self, n=100):
        """Retrieves the last N songs played from the database."""
        if not self.db_path: return []
        songs_list = []
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT artist, title, timestamp FROM music_history ORDER BY timestamp DESC LIMIT ?", (n,))
                for row in cursor.fetchall():
                    songs_list.append({"artist": row[0], "title": row[1], "timestamp": row[2]})
        except Exception as e:
            self.log(f"Error retrieving last {n} songs: {e}", level="ERROR")
        return songs_list

    def get_last_n_unique_songs_with_timestamps(self, n=100):
        """Retrieves the last N unique songs played from the database."""
        if not self.db_path: return []
        songs_list = []
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                query = f"SELECT artist, title, MAX(timestamp) as last_played_ts FROM music_history GROUP BY artist, title ORDER BY last_played_ts DESC LIMIT ?"
                cursor.execute(query, (n,))
                for row in cursor.fetchall():
                    songs_list.append({"artist": row[0], "title": row[1], "timestamp": row[2]})
        except Exception as e:
            self.log(f"DB error retrieving last {n} unique songs: {e}", level="ERROR")
        return songs_list


    # --- DATABASE CLEANUP METHODS ---
    
    def run_optimization(self, kwargs):
        """Main function to run all cleanup tasks, triggered by its own schedule."""
        self.log("Scheduled optimization run has started.")
        
        if not os.path.exists(self.db_path):
            self.log(f"❌ Database file not found at '{self.db_path}'. Aborting optimization run.", level="ERROR")
            return
        
        database_was_modified = False
            
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                self.log("--- Task 1: Checking for skipped tracks ---")
                skipped_deleted_count = self._cleanup_skipped_tracks(cursor)
                if skipped_deleted_count > 0:
                    database_was_modified = True

                if self.cleanup_prune_enabled:
                    self.log("--- Task 2: Pruning old chart history ---")
                    pruned_count = self._prune_chart_history(cursor)
                    if pruned_count > 0:
                        database_was_modified = True
                else:
                    self.log("--- Task 2: Pruning disabled, skipping. ---")

                if database_was_modified and self.cleanup_execute_mode:
                    self.log("Committing all changes to the database...")
                    conn.commit()
                
                if database_was_modified and self.cleanup_execute_mode and self.cleanup_vacuum_on_complete:
                    self.log("--- Task 3: Reclaiming disk space ---")
                    self.log("🧹 Starting VACUUM. This may take a moment...")
                    conn.row_factory = None
                    conn.execute("VACUUM;")
                    conn.row_factory = sqlite3.Row
                    self.log("✅ VACUUM complete. Database file has been compacted.")
                
                self.log("Optimization run finished.")

        except sqlite3.Error as e:
            self.log(f"❌ A database error occurred during optimization: {e}", level="ERROR")
        except Exception as e:
            self.log(f"❌ An unexpected error occurred during optimization: {e}", level="ERROR")

    def _cleanup_skipped_tracks(self, cursor):
        """Finds and deletes skipped tracks. Returns number of rows affected."""
        query = "SELECT id, timestamp, LAG(timestamp, 1) OVER (ORDER BY timestamp) AS prev_timestamp FROM music_history"
        cursor.execute(query)
        
        ids_to_delete = []
        for track in cursor.fetchall():
            if track["prev_timestamp"] is None: continue
            
            current_ts = datetime.datetime.fromisoformat(track["timestamp"])
            prev_ts = datetime.datetime.fromisoformat(track["prev_timestamp"])
            time_diff = (current_ts - prev_ts).total_seconds()
            
            if 0 <= time_diff < self.cleanup_threshold_seconds:
                ids_to_delete.append((track["id"],))

        found_count = len(ids_to_delete)
        if found_count == 0:
            self.log("No skipped tracks found.")
            return 0

        self.log(f"Found {found_count} skipped tracks.")
        if self.cleanup_execute_mode:
            cursor.executemany("DELETE FROM music_history WHERE id = ?;", ids_to_delete)
            self.log(f"EXECUTE: Deleted {cursor.rowcount} skipped tracks.")
            return cursor.rowcount
        else:
            self.log("DRY RUN: Would have deleted these tracks. Enable 'cleanup_execute_on_run' to proceed.")
            return 0

    def _prune_chart_history(self, cursor):
        """Deletes records from chart_history older than the configured number of days."""
        cutoff_date_str = f"datetime('now', '-{self.cleanup_prune_keep_days} days')"
        
        query_count = f"SELECT COUNT(*) FROM chart_history WHERE timestamp < {cutoff_date_str};"
        cursor.execute(query_count)
        count_to_delete = cursor.fetchone()[0]

        if count_to_delete == 0:
            self.log("No old chart history records to prune.")
            return 0
            
        self.log(f"Found {count_to_delete} chart history records older than {self.cleanup_prune_keep_days} days.")
        
        if self.cleanup_execute_mode:
            query_delete = f"DELETE FROM chart_history WHERE timestamp < {cutoff_date_str};"
            cursor.execute(query_delete)
            self.log(f"EXECUTE: Deleted {cursor.rowcount} old records from chart_history.")
            return cursor.rowcount
        else:
            self.log("DRY RUN: Would have deleted these records. Enable 'cleanup_execute_on_run' to proceed.")
            return 0
