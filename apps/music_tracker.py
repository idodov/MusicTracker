"""
This script tracks your music listening habits across your media players.
Builds a database of your listening history.
Generates daily charts for your top songs, artists, albums, and more.
Provides insights into your musical tastes.

#apps.yaml example:
music_tracker:
  module: music_tracker
  class: MusicTracker
  db_path: "/config/music_data_history.db"
  duration: 30
  min_songs_for_album: 4
  update_time: "23:59:00"
  run_on_startup: true
  media_players:
    - media_player.patio
    - media_player.kitchen
    - media_player.bedroom
    - media_player.living_room
    - media_player.dining_room
  html_output_path: "/homeassistant/www/music_charts.html"
  # NEEDS APPDAEMON 4.5+ 
  ai_service: "google_generative_ai_conversation/generate_content"
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

TEMPLATE = '''
<!DOCTYPE html>
<html lang="en" dir="ltr">
<head>
<meta charset="UTF-8">
<meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate" />
<meta http-equiv="Pragma" content="no-cache" />
<meta http-equiv="Expires" content="0" />
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Music Charts</title>
<style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: 'Helvetica Neue', Arial, sans-serif; background: #f4f4f9; color: #333; padding: 1em; }

    #refreshPageButton {
        padding: 0.4em 1.0em;
        font-size: 0.75rem;
        color: white;
        background-color: #007bff; /* A nice blue, adjust as needed */
        border: none;
        border-radius: 5px;
        cursor: pointer;
        transition: background-color 0.2s ease-in-out;
    }
    #refreshPageButton:hover {
        background-color: #0056b3; /* Darker blue on hover */
    }

    header { display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; margin-bottom: 1em; }
    h1 { font-size: 1.6rem; color: #2c3e50; }
    #controls label { margin-right: 1em; font-size: 0.9rem; color: #34495e; }
    #generated-at { font-size: 0.8rem; color: #7f8c8d; }
    main { display: flex; flex-direction: column; gap: 2em; }
    .chart-section { background: #fff; border-radius: 8px; padding: 1em; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    .chart-section h2 { color: #34495e; margin-bottom: 0.5em; }
    .chart-tables { display: flex; flex-wrap: wrap; gap: 1em; }
    .table-container { flex: 1 1 calc(33% - 1em); min-width: 300px; }
    table { width: 100%; border-collapse: collapse; margin-bottom: 0.5em; }
    th, td { padding: 0.5em; text-align: start; word-break: break-word;font-size: 0.8rem; }
    th { background: #3498db; color: #fff; position: sticky; top: 0; z-index: 1;}
    tbody tr:nth-child(even) { background: #ecf0f1; }
    tbody tr:hover { background: #d0e7f9; }
    h3 { margin: 0.5em 0; font-size: 1.0rem; color: #2980b9; }
    @media (max-width: 768px) {
      .table-container { flex: 1 1 100%; }
      header { flex-direction: column; align-items: flex-start; }
      #controls { margin-top: 0.5em; margin-bottom: 0.5em; }
    }
    /* #ai-analysis { margin-top: 1em; background: #fff3cd; border: 1px solid #ffeeba; border-radius: 8px; padding: 1em; } */
    #ai-analysis h2 { color: #856404; }
    .change-up { color: green; font-weight: bold; }
    .change-down { color: red; font-weight: bold; }
    .change-new { color: orange; font-weight: bold; }
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
<p id="generated-at">Generated at {{ generated_at }}</p>
<button id="refreshPageButton">Refresh Page</button>
</header>

<main>
{% macro render_table(title, items, cols, current_period) %}
<div class="table-container">
<h3 dir="auto"><bdi>{{ title }}</bdi></h3>
{% if items %}
<table>
<thead>
<tr><th>#</th>{% for col in cols.keys() %}<th>{{ col }}</th>{% endfor %}{% if current_period != 'yearly' %}<th>~</th>{% endif %}</tr>
</thead>
<tbody>
{% for item in items %}<tr>
<td nowrap>{{ loop.index }}</td>
{% for key in cols.values() %}
<td dir="auto"><bdi>{{ item[key] }}</bdi></td>
{% endfor %}
{% if current_period != 'yearly' %} {# <--- Conditional data cell #}
<td dir="auto" nowrap>
    {% if item.new_entry %}<span class="change-new">🆕</span>
    {% elif item.change > 0 %}<span class="change-up">▲{{ item.change }}</span>
    {% elif item.change < 0 %}<span class="change-down">▼{{ (-item.change)|abs }}</span> {# <--- Corrected class="change-down" #}
    {% else %} — {% endif %}
</td>
{% endif %} {# <--- End conditional data cell #}
</tr>{% endfor %}
</tbody></table>{% else %}<p>No data for {{ title }}</p>{% endif %}</div>
{% endmacro %}

{% for period, data in charts.items() %}
<section id="chart-{{ period }}" class="chart-section">
<h2 dir="auto"><bdi>Top {{ period|capitalize }} ({{ data.dates }})</bdi></h2> 
<div class="chart-tables">
    {{ render_table('🎵 Songs', data.songs, {'Artist':'artist','Title':'title','▶️':'plays'}, period) }} {# <--- Passed period #}
    {{ render_table('👤 Artists', data.artists, {'Artist':'artist','▶️':'plays'}, period) }} {# <--- Passed period #}
    {{ render_table('💽 Albums', data.albums, {'Album':'album','Artist':'artist','▶️':'tracks'}, period) }} {# <--- Passed period #}
    {{ render_table('📻 Channels/Playlists', data.media_channels, {'Channel':'channel','▶️':'plays'}, period) }} {# <--- Passed period #}
</div>
</section>
{% endfor %}

{% if ai_analysis %}
<section id="ai-analysis" dir="auto">
<h2>🔮 AI Analysis</h2>
        {{ ai_analysis|safe }}
</section>
{% endif %}
</main>

<script>
    document.addEventListener("DOMContentLoaded", () => {
      // Logic for the refresh button
        const refreshButton = document.getElementById('refreshPageButton');
        if (refreshButton) {
            refreshButton.addEventListener('click', () => {
                window.location.reload();
            });
        }

        const controls = document.querySelectorAll("#controls input[type=checkbox]");
        function toggleSection(period, show) {
        const section = document.getElementById(`chart-${period}`);
        if (section) section.style.display = show ? "" : "none";
        }
        controls.forEach(cb => {
        const period = cb.dataset.period;
        const stored = localStorage.getItem(`show_${period}`);
        cb.checked = (stored===null) ? true : (stored==="1");
        toggleSection(period, cb.checked);
        cb.addEventListener("change", () => {
            localStorage.setItem(`show_${period}`, cb.checked?"1":"0");
            toggleSection(period, cb.checked);
        });
        });
    });
</script>
</body>
</html>
'''

AI_PROMPT = [
    "You are a 'Musical Insights Web Weaver,' an AI expert in analyzing music listening data and presenting it in a self-contained, visually stunning, modern, and engaging HTML widget.",
    "Your primary goal is to create a beautiful, responsive, and insightful report as an embeddable HTML component based on the provided listening data, ensuring an excellent experience on both mobile and desktop.",

    "Core Task & Content Requirements:",
    "1. Analyze Listening Habits: Deeply analyze the provided data to reveal my musical preferences, focusing on: top genres, top artists, predominant moods (if inferable), and any notable listening patterns or shifts.",
    "2. Deliver Positive Insights: Frame your analysis with positive and encouraging language.",
    "3. Artist & Song Recommendations: Suggest 3-5 new artists and specific songs I might enjoy based on my habits. For each recommendation, include a piece of fun, engaging trivia about the artist or song.",
    "4. Interactive Game Element (Highly Desired): Design and implement a small, fun, interactive game. This could be a trivia quiz, a 'guess the lyric/artist' challenge, or a simple matching game related to my music preferences or the recommendations. Use HTML, CSS, and embedded JavaScript to make it interactive. The game should be self-contained within your HTML output. Do not ask the user to type answer.",
    "5. You can suprise me with ai generated image by 'https://pollinations.ai/p/'prompt'?model=turbo' of my top artists. by prompt (include artist names) 'Imagine these iconic artists reborn in a stunning, cartoon/paint/realistic masterpiece. Their expressions radiate emotion, their surroundings echo their musical legacy'",
    "Design & Technical Requirements - Strive for Maximum Style, Usability, and Embeddability:",
    "1. Top-Level Container: The entire HTML output you generate MUST be wrapped in a single `div` with the class `ai-container`. For example: `<div class=\"ai-container\">...all your content...</div>`.",
    "2. Output Format: Generate ONLY pure HTML code suitable for direct embedding within a `<body>` tag. ABSOLUTELY NO `<html>`, `<head>`, or `<body>` tags in your output.",
    "3. Code Purity: Your entire response must be *only* the HTML code block itself. NO markdown, NO explanations, NO conversational remarks, NO comments outside of HTML comments if absolutely necessary for structure (e.g., `<!-- Section: Analysis -->`).",
    
    "4. Visual Styling (CSS) - Scoped to '.ai-container':",
    "   - Embed all CSS within `<style>` tags directly in the HTML output, preferably at the beginning of the `ai-container` or immediately after its opening tag.",
    "   - **Crucial for Scoping:** ALL your CSS rules MUST be prefixed with `.ai-container` to ensure they only affect elements within this container and do not interfere with the styles of the host page. For example, instead of `h2 { color: blue; }`, use `.ai-container h2 { color: blue; }`. Instead of `.my-button { ... }`, use `.ai-container .my-button { ... }`.",
    "   - Avoid global selectors like `*`, `body`, or `html` unless absolutely necessary and also scoped (e.g., `.ai-container *`).",
    "   - Aesthetic: Aim for a modern, clean, creative, and highly polished design within the `ai-container`. Think 'Spotify Wrapped' but embeddable. Use engaging visuals, smooth transitions, and micro-interactions where appropriate using CSS.",
    "   - Color Palette: Use a visually appealing and harmonious color palette within the `ai-container`. Consider using modern gradients or distinct, stylish accent colors that enhance readability and visual hierarchy.",
    "   - Typography: Use clear, modern web-safe fonts. Strongly consider using a Google Font (e.g., Montserrat, Open Sans, Lato) via `@import` within the `<style>` tags for a more refined look. Ensure font styles are scoped to `.ai-container`.",
    "   - Layout: The `ai-container` itself should utilize `width: 100%;`. Inside it, prioritize concise presentation of insights. Use ample whitespace and clear visual separation between sections (e.g., using cards, borders, or background color changes for different sections like analysis, recommendations, game).",

    "5. Data Visualization (Chart.js Strongly Preferred for Style & Interactivity - Scoped):",
    "   - Represent top genres using a visually appealing Pie or Doughnut chart within the `ai-container`.",
    "   - Represent top artists using a sleek Bar chart within the `ai-container`.",
    "   - Use Chart.js: Include the Chart.js library via CDN (`<script src=\"https://cdn.jsdelivr.net/npm/chart.js\"></script>`) and then provide the necessary JavaScript within `<script>` tags (placed appropriately, usually before the closing of the `ai-container` or at the end of the HTML snippet) to render the charts. Ensure chart container elements have unique IDs if necessary, and JavaScript targets these correctly.",
    "   - Ensure charts are well-styled (custom colors matching the palette, clear labels, informative tooltips, possibly subtle animations) to integrate seamlessly with the `ai-container`'s overall aesthetic.",
    "   - Fallback: If Chart.js implementation proves too complex, you may use pure CSS charts, ensuring all styles are scoped with `.ai-container`.",

    "6. Responsiveness - Optimizing for Both Mobile and Desktop (within '.ai-container'):",
    "   - Mobile-First Design: Ensure all elements within `ai-container` are perfectly legible and functional on mobile devices.",
    "   - Stacking on Mobile: On mobile screens, ensure that major content blocks within `ai-container` (like a chart and its accompanying text, or two separate charts, or the game area) stack vertically. Use CSS Flexbox (`display: flex; flex-direction: column;`) or CSS Grid for robust single-column layouts on smaller screens, all scoped with `.ai-container`.",
    "   - Rich Desktop Layout: On wider screens, leverage the available space within `ai-container` for a more engaging multi-element layout. For instance, display charts side-by-side with their analyses, or arrange recommendations in a grid. The design should feel expansive and utilize the screen real estate effectively. Use media queries and scoped CSS to adjust `flex-direction` to `row`, modify grid layouts, or reveal desktop-specific enhancements.",
    "   - Height Constraints for Visuals: Graphs and other large visual elements within `ai-container` should generally maintain a `max-height` (e.g., `70vh` to `85vh`, adjust based on content) to maximize visibility without causing excessive page scrolling on any device.",
    "   - Crucial Mobile Constraint (Scoped): Reiterate for emphasis: on mobile devices, do NOT display two distinct, major objects within `ai-container` on the same horizontal line unless they are very small and intrinsically part of a single composite visual element.",
    
    "Final Structure & Output Integrity:",
    "The entire output must be a single HTML snippet starting with `<div class=\"ai-container\">` and ending with `</div>`.",
    "Organize the HTML content logically into clearly demarcated sections within `ai-container`, potentially using headings and divs, for 'Musical Analysis', 'Artist & Song Recommendations', and 'Interactive Game'.",
    "All JavaScript, including for Chart.js and any interactive game, must be embedded within `<script>` tags in your HTML output, and should operate on elements within the `ai-container`.",
    "Remember, the entire output must be the HTML code block itself, and nothing else."
]

class TrackManager:
    def __init__(self):
        self.played_tracks = {} 
        self.lock = threading.Lock()
        self.cleanup_interval = 60  
        self.track_memory_duration = 600 
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

    def initialize(self):
        self.log("MusicTracker Initializing...")
        self.media_players = self.args.get("media_players", [])
        if not isinstance(self.media_players, list):
            self.media_players = [self.media_players] if self.media_players else []
            
        self.duration_to_consider_played = self.args.get("duration", 30) 
        self.min_songs_for_album_chart = self.args.get("min_songs_for_album", 3)
        self.chart_update_time = self.args.get("update_time", "00:00:00")
        self.db_path = self.args.get("db_path")
        self.html_output_path = self.args.get("html_output_path", "/homeassistant/www/music_charts.html")
        self.ai_service = self.args.get("ai_service", False)

        if not self.db_path:
            self.log("db_path not configured. MusicTracker cannot function.", level="ERROR")
            return
        if not self.html_output_path:
            self.log("html_output_path not configured. MusicTracker cannot function.", level="ERROR")
            return
        
        self.log(f"Config: DB Path='{self.db_path}', HTML Path='{self.html_output_path}', AI Service='{self.ai_service}'")
        self.log(f"Tracks considered played after: {self.duration_to_consider_played}s")
        self.log(f"Monitoring media players: {self.media_players}")

        self.track_manager = TrackManager()
        self.create_db_tables()
        self.cleanup_old_db_tracks() 

        try:
            time_obj = datetime.time.fromisoformat(self.chart_update_time)
            self.run_daily(self.scheduled_update_html_callback, time_obj)
            self.log(f"Scheduled HTML updates at: {self.chart_update_time}")
        except ValueError:
            self.log(f"Invalid chart_update_time: '{self.chart_update_time}'. Use HH:MM:SS. Scheduling disabled.", level="ERROR")

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
        self.log("Scheduled daily chart update triggered.")
        self.update_html_and_sensors()

    def manual_update_html_callback(self, entity, attribute, old, new, kwargs):
        self.log(f"Manual chart update triggered by {entity}.")
        self.update_html_and_sensors()
        if self.entity_exists(self.input_boolean_chart_trigger):
            self.set_state(self.input_boolean_chart_trigger, state="off", 
                        attributes={"last_triggered": datetime.datetime.now().isoformat()})

    def update_html_and_sensors(self):
        self.log("Starting chart data generation and HTML/Sensor update process...")
        timeframes = {
            "daily": "1 day", "weekly": "7 days",
            "monthly": "30 days", "yearly": "365 days"
        }
        current_charts_data = {}
        all_data_ok = True

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
        
        self.log("Attempting initial HTML write (without AI analysis)...")
        self.render_and_write_html(current_charts_data, None) 

        if self.ai_service:
            self.log("AI service configured. Initiating AI analysis.")
            self._call_ai_analysis(current_charts_data)
        else:
            self.log("AI service not configured. Skipping AI analysis.")

        #self.update_home_assistant_sensors(current_charts_data)
        self.log("HTML update process finished.")

    def _call_ai_analysis(self, charts_data_for_ai):
        if not isinstance(self.ai_service, str):
            self.log(f"AI service not configured as string. Skipping. Current: {self.ai_service}", level="DEBUG")
            return 

        parts = self.ai_service.split("/", 1)
        if len(parts) != 2:
            self.log(f"Invalid ai_service format: '{self.ai_service}'. Skipping.", level="WARNING")
            return

        domain, service = parts
        prompt = self.build_prompt_from_chart_data(charts_data_for_ai)
        
        self.log(f"Calling AI service: {domain}/{service}")
        try:
            self.call_service(
                f"{domain}/{service}", prompt=prompt,
                timeout=120, hass_timeout=120, 
                callback=self._ai_response_callback 
            )
            self.log(f"AI service call for {domain}/{service} initiated.")
        except Exception as e:
            self.log(f"Error initiating AI service call {domain}/{service}: {e}", level="ERROR")
            self.render_and_write_html(self._last_charts_data, f"Error initiating AI analysis: {e}")

    def _ai_response_callback(self, resp): 
        ai_text = None
        #self.log(f"AI response callback. Type: {type(resp)}. Response (first 200): {str(resp)[:200]}")

        if isinstance(resp, dict):
            if resp.get("success"): 
                result = resp.get("result", {})
                if isinstance(result.get("response"), dict): ai_text = result["response"].get("text")
                elif "text" in result: ai_text = result.get("text")
                
                if ai_text: self.log(f"AI analysis successful. Text length: {len(ai_text)}.")
                else:
                    self.log(f"AI success, but 'text' not found. Result: {str(result)[:200]}", level="WARNING")
                    ai_text = "AI analysis successful, but no content extracted." 
            else:
                err_msg = resp.get("error", {}).get("message", "Unspecified error from AI service.")
                self.log(f"AI service call failed. Error: '{err_msg}'. Response: {str(resp)[:200]}", level="WARNING")
                ai_text = f"AI analysis failed: {err_msg}"
        else:
            self.log(f"AI response not a dict. Received: {type(resp)}", level="WARNING")
            ai_text = "AI analysis returned an unexpected response format."

        if hasattr(self, '_last_charts_data') and self._last_charts_data:
            self.render_and_write_html(self._last_charts_data, ai_text)
        else:
            self.log("Cannot re-render HTML with AI: _last_charts_data is missing.", level="ERROR")

    def render_and_write_html(self, charts_data_to_render, ai_text_content):
        if ai_text_content:
            ai_text_content = re.sub(r'^\s*```(?:html)?\s*', '', ai_text_content)
            ai_text_content = re.sub(r'\s*```\s*$', '', ai_text_content)
        self.log(f"Rendering HTML. AI text provided: {ai_text_content is not None}")
        try:
            env = jinja2.Environment(loader=jinja2.BaseLoader(), autoescape=jinja2.select_autoescape(['html', 'xml']))
            template = env.from_string(TEMPLATE)
            html_output = template.render(
                generated_at=datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                charts=charts_data_to_render,
                ai_analysis=ai_text_content
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
        weekly_data = charts_for_prompt.get("weekly", {})
        daily_data = charts_for_prompt.get("daily", {}) # Get daily data

        weekly_dates_str = weekly_data.get("dates", "N/A")
        daily_dates_str = daily_data.get("dates", "N/A") # Get daily dates
        if weekly_dates_str == "N/A":
            weekly_dates_str = daily_dates_str
            weekly_data = daily_data

        prompt_lines = AI_PROMPT
        
        # Weekly Songs
        prompt_lines.extend([
            f"My listening data:{weekly_dates_str}."
            "\nTop Weekly Songs Data (up to 100):",
            "| Artist | Title | Plays |",
            "|---|---|---|"
        ])
        songs_for_weekly_prompt = weekly_data.get("songs", [])[:100]
        if songs_for_weekly_prompt:
            for song_item in songs_for_weekly_prompt:
                prompt_lines.append(f"| {song_item.get('artist','N/A')} | {song_item.get('title','N/A')} | {song_item.get('plays','N/A')} |")
        else:
            prompt_lines.append("| No weekly song data available. | | |")

        # Daily Songs
        #prompt_lines.extend([
        #    "\nTop Daily Songs Data (up to 100):",
        #    "| Artist | Title | Plays |",
        #    "|---|---|---|"
        #])
        #songs_for_daily_prompt = daily_data.get("songs", [])[:100] # Get daily songs
        #if songs_for_daily_prompt:
        #    for song_item in songs_for_daily_prompt:
        #        prompt_lines.append(f"| {song_item.get('artist','N/A')} | {song_item.get('title','N/A')} | {song_item.get('plays','N/A')} |")
        #else:
        #    prompt_lines.append("| No daily song data available. | | |")
            
        return "\n".join(prompt_lines)

    def create_db_tables(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS music_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT, artist TEXT, title TEXT,
                        album TEXT, media_channel TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP )""")
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS chart_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT, period TEXT,
                        data TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP )""")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_music_history_timestamp ON music_history (timestamp);")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_music_history_lookup ON music_history (artist, title, album);")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_chart_history_lookup ON chart_history (type, period, timestamp);")
                conn.commit()
            self.log("DB tables checked/created (using 'type' & 'period' for chart_history).")
        except sqlite3.Error as e: self.log(f"DB error during table creation: {e}", level="ERROR")

    def cleanup_old_db_tracks(self):
        one_year_ago = datetime.datetime.now() - datetime.timedelta(days=366)
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM music_history WHERE timestamp < ?", (one_year_ago.strftime('%Y-%m-%d %H:%M:%S'),))
                if cursor.rowcount > 0: self.log(f"Cleaned {cursor.rowcount} old tracks from DB.")
                conn.commit()
        except sqlite3.Error as e: self.log(f"DB error during old track cleanup: {e}", level="ERROR")

    def handle_media_player_event(self, entity_id, attribute, old_state_data, new_state_data, kwargs):
        old_attributes = old_state_data.get("attributes", {}) if old_state_data else {}
        new_attributes = new_state_data.get("attributes", {}) if new_state_data else {}
        
        old_title = old_attributes.get("media_title")
        new_title = new_attributes.get("media_title")
        new_player_state = new_state_data.get("state") if new_state_data else "unknown"

        if entity_id in self._active_track_timers:
            if (old_title != new_title and new_title is not None) or new_player_state != "playing":
                timer_handle = self._active_track_timers.pop(entity_id)
                if hasattr(self, 'timer_running') and self.timer_running(timer_handle): 
                    self.cancel_timer(timer_handle)
                    self.log(f"Cancelled track timer for {entity_id} due to change.", level="DEBUG")
                elif not hasattr(self, 'timer_running'): 
                    try:
                        self.cancel_timer(timer_handle)
                        self.log(f"Attempted cancellation of track timer for {entity_id} (timer_running not avail).", level="DEBUG")
                    except: pass

        if new_player_state == "playing":
            artist = new_attributes.get("media_artist")
            title = new_title

            if not artist or not title:
                self.log(f"{entity_id} playing, but no artist/title. Attrs: {new_attributes}", level="DEBUG")
                return

            current_track_info = {
                "entity_id": entity_id, "artist": artist, "title": title,
                "album": new_attributes.get("media_album_name"),
                "media_channel": new_attributes.get("media_channel") or new_attributes.get("source")
            }
            
            self.log(f"{entity_id} playing '{title}'. Scheduling storage in {self.duration_to_consider_played}s.", level="DEBUG")
            timer_handle = self.run_in(
                self._finalize_and_store_track,
                self.duration_to_consider_played,
                track_info_at_play_start=current_track_info
            )
            self._active_track_timers[entity_id] = timer_handle

    def _finalize_and_store_track(self, kwargs):
        track_info_original = kwargs.get("track_info_at_play_start")
        if not track_info_original:
            self.log("Error: _finalize_and_store_track missing track_info.", level="ERROR")
            return

        entity_id = track_info_original["entity_id"]
        self._active_track_timers.pop(entity_id, None) 

        current_state = self.get_state(entity_id, attribute="all")
        if not current_state or current_state.get("state") != "playing":
            self.log(f"Track storage for {entity_id} aborted: Not playing.", level="DEBUG")
            return

        current_attrs = current_state.get("attributes", {})
        if current_attrs.get("media_artist") != track_info_original["artist"] or \
            current_attrs.get("media_title") != track_info_original["title"]:
            self.log(f"Track storage for {entity_id} aborted: Song changed.", level="DEBUG")
            return
        
        artist = track_info_original["artist"]
        title = track_info_original["title"]
        album = track_info_original["album"]
        media_channel = track_info_original["media_channel"]

        if title.lower() in ["tv", "unknown", "advertisement"]: return

        cleaned_title = self.clean_text_for_chart(title)
        cleaned_album = self.clean_text_for_chart(album) if album else "Unknown Album"
        track_identifier = f"{artist.lower().strip()}|{cleaned_title.lower().strip()}"

        if self.track_manager.has_been_played_recently(track_identifier):
            self.log(f"Track '{track_identifier}' on {entity_id} recently processed. Skipping.", level="DEBUG")
            return
        
        self.track_manager.add_track(track_identifier) 

        if not cleaned_album or cleaned_album.lower() == "unknown album": cleaned_album = cleaned_title
        if not media_channel: media_channel = "Unknown Source"

        self.log(f"Storing track from {entity_id}: {artist} | {cleaned_title} | {cleaned_album} | {media_channel}")
        self.store_track_in_db(artist, cleaned_title, cleaned_album, media_channel)

    def clean_text_for_chart(self, text_to_clean: str) -> str:
        if not text_to_clean or not isinstance(text_to_clean, str): return ""
        version_keywords = [
            'remaster', 'remastered', 're-master', 're-mastered', 'mix', 'remix', 'dub', 
            'stereo', 'mono', 'dubs', 'demo', 'deluxe', 'instrumental', 'extended', 
            'version', 'radio edit', 'live', 'edit', 'anniversary', 'edition', 'single',
            'explicit', 'clean', 'original', 'acoustic', 'unplugged', 'bonus track', 'feat', 'ft'
        ]
        keyword_pattern_str = r'\s*[\(\[\-](?:[^\(\)\[\]\-]*\b(?:' + '|'.join(f"{k}\\.?" for k in version_keywords) + r')\b[^\(\)\[\]\-]*?)[\)\]\-]?\s*'
        cleaned_text = re.sub(keyword_pattern_str, '', text_to_clean, flags=re.IGNORECASE)
        cleaned_text = cleaned_text.strip()
        cleaned_text = re.sub(r'\s{2,}', ' ', cleaned_text) 
        return cleaned_text if cleaned_text else text_to_clean

    def store_track_in_db(self, artist, title, album, media_channel):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO music_history (artist, title, album, media_channel, timestamp)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (artist, title, album, media_channel))
                conn.commit()
        except sqlite3.Error as e: self.log(f"DB error storing track: {e}", level="ERROR")

    def update_home_assistant_sensors(self, charts_data):
        self.log("Updating Home Assistant sensor entities...")
        if not isinstance(charts_data, dict):
            self.log("Cannot update HA sensors: charts_data invalid.", level="WARNING")
            return

        for period_key, period_config in charts_data.items():
            if not isinstance(period_config, dict):
                self.log(f"Skipping HA sensor update for {period_key}: invalid data.", level="WARNING")
                continue
            limit = 10 
            dates_str = period_config.get("dates", "N/A")
            self.set_state(f"sensor.music_charts_top_songs", state=f"Top Songs ({dates_str})", 
                        attributes={"songs": period_config.get("songs", [])[:limit], "chart_dates": dates_str})
            self.set_state(f"sensor.music_charts_top_artists", state=f"Top Artists ({dates_str})",
                        attributes={"artists": period_config.get("artists", [])[:limit], "chart_dates": dates_str})
            self.set_state(f"sensor.music_charts_top_albums", state=f"Top Albums ({dates_str})",
                        attributes={"albums": period_config.get("albums", [])[:limit], "chart_dates": dates_str})
        self.log("Home Assistant sensor entities updated.")

    def get_chart_dates_for_period(self, days_str):
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
                elif res and res[0]: return datetime.datetime.strptime(res[0], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y')
                else:
                    e_dt = datetime.datetime.now()
                    s_dt = e_dt - datetime.timedelta(days=int(days_str.split()[0])-1)
                    return f"{s_dt.strftime('%d/%m/%Y')} - {e_dt.strftime('%d/%m/%Y')} (No Data)"
        except Exception as e: 
            self.log(f"Error getting chart dates for '{days_str}': {e}", level="WARNING")
            return "Date Range Error"

    def get_top_songs(self, days_str, limit, period_name):
        previous_chart_data = self.get_previous_chart_data("songs", period_name)
        query = f"""
            SELECT title, artist, album, COUNT(*) as item_count
            FROM music_history
            WHERE timestamp >= datetime('now', '-{days_str}')
            GROUP BY title, artist, album
            ORDER BY item_count DESC, artist ASC, title ASC
            LIMIT {limit}
        """
        top_items_list = []
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(query)
                db_results = cursor.fetchall()

            for rank, db_row_tuple in enumerate(db_results, 1):
                current_item_dict = {
                    "title": db_row_tuple[0],
                    "artist": db_row_tuple[1],
                    "album": db_row_tuple[2],
                    "plays": db_row_tuple[3],
                }
                change_info = self.calculate_chart_change(previous_chart_data, current_item_dict, rank, "songs")
                current_item_dict.update({
                    "change": change_info['change_value'],
                    "new_entry": change_info['is_new_entry']
                })
                top_items_list.append(current_item_dict)
        except sqlite3.Error as e:
            self.log(f"DB error in get_top_songs ({period_name}): {e}", level="ERROR")
        #self.log(f"DEBUG: get_top_songs for {period_name} found {len(top_items_list)} items.")
        return top_items_list

    def get_top_artists(self, days_str, limit, period_name):
        previous_chart_data = self.get_previous_chart_data("artists", period_name)
        query = f"""
            SELECT artist, COUNT(*) as item_count
            FROM music_history
            WHERE timestamp >= datetime('now', '-{days_str}') AND artist IS NOT NULL AND artist != ''
            GROUP BY artist
            ORDER BY item_count DESC, artist ASC
            LIMIT {limit}
        """
        top_items_list = []
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(query)
                db_results = cursor.fetchall() 
            for rank, db_row_tuple in enumerate(db_results, 1):
                current_item_dict = {
                    "artist": db_row_tuple[0],
                    "plays": db_row_tuple[1],
                }
                change_info = self.calculate_chart_change(previous_chart_data, current_item_dict, rank, "artists")
                current_item_dict.update({
                    "change": change_info['change_value'],
                    "new_entry": change_info['is_new_entry']
                })
                top_items_list.append(current_item_dict)
        except sqlite3.Error as e:
            self.log(f"DB error in get_top_artists ({period_name}): {e}", level="ERROR")
        #self.log(f"DEBUG: get_top_artists for {period_name} found {len(top_items_list)} items.")
        return top_items_list

    def get_top_albums(self, days_str, limit, period_name):
        previous_chart_data = self.get_previous_chart_data("albums", period_name)
        query = f"""
            SELECT artist, album, COUNT(DISTINCT title) as song_count
            FROM music_history
            WHERE timestamp >= datetime('now', '-{days_str}') AND album IS NOT NULL AND album != '' AND artist IS NOT NULL AND artist != ''
            GROUP BY artist, album
            HAVING song_count >= {self.min_songs_for_album_chart}
            ORDER BY song_count DESC, album ASC, artist ASC
            LIMIT {limit}
        """
        top_items_list = []
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(query)
                db_results = cursor.fetchall()

            for rank, db_row_tuple in enumerate(db_results, 1):
                current_item_dict = {
                    "artist": db_row_tuple[0],
                    "album": db_row_tuple[1],
                    "tracks": db_row_tuple[2], 
                }
                change_info = self.calculate_chart_change(previous_chart_data, current_item_dict, rank, "albums")
                current_item_dict.update({
                    "change": change_info['change_value'],
                    "new_entry": change_info['is_new_entry']
                })
                top_items_list.append(current_item_dict)
        except sqlite3.Error as e:
            self.log(f"DB error in get_top_albums ({period_name}): {e}", level="ERROR")
        #self.log(f"DEBUG: get_top_albums for {period_name} found {len(top_items_list)} items.")
        return top_items_list

    def get_top_media_channels(self, days_str, limit, period_name):
        previous_chart_data = self.get_previous_chart_data('media_channels', period_name)
        query = f"""
            SELECT media_channel, COUNT(*) as item_count
            FROM music_history
            WHERE timestamp >= datetime('now', '-{days_str}') AND media_channel IS NOT NULL AND media_channel != ''
            GROUP BY media_channel
            ORDER BY item_count DESC, media_channel ASC
            LIMIT {limit}
        """
        top_items_list = []
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(query)
                db_results = cursor.fetchall() 
            for rank, db_row_tuple in enumerate(db_results, 1):
                current_item_dict = {
                    "channel": db_row_tuple[0], 
                    "plays": db_row_tuple[1],
                }
                change_info = self.calculate_chart_change(previous_chart_data, current_item_dict, rank, "media_channels")
                current_item_dict.update({
                    "change": change_info['change_value'],
                    "new_entry": change_info['is_new_entry']
                })
                top_items_list.append(current_item_dict)
        except sqlite3.Error as e:
            self.log(f"DB error in get_top_media_channels ({period_name}): {e}", level="ERROR")
        #self.log(f"DEBUG: get_top_media_channels for {period_name} found {len(top_items_list)} items.")
        return top_items_list

    def calculate_chart_change(self, previous_chart_list, current_item_dict, current_rank, category_name):
        #self.log(f"DEBUG: calculate_chart_change for {category_name}, Current: {current_item_dict.get('title') or current_item_dict.get('artist') or current_item_dict.get('album') or current_item_dict.get('channel') }") # Log main identifier
        previous_rank_found = None
        
        # Log structure of first previous item IF list is not empty
        #if previous_chart_list:
        #    self.log(f"DEBUG: Prev list sample for {category_name} (first item): {previous_chart_list[0]}")
        #else:
        #    self.log(f"DEBUG: Prev list empty for {category_name}")


        for idx, prev_item_dict in enumerate(previous_chart_list):
            match = False
            # Ensure prev_item_dict is actually a dictionary
            if not isinstance(prev_item_dict, dict):
                #self.log(f"DEBUG: prev_item_dict is not a dict: {prev_item_dict}", level="WARNING")
                continue

            if category_name == 'songs':
                if prev_item_dict.get('title') == current_item_dict.get('title') and \
                    prev_item_dict.get('artist') == current_item_dict.get('artist') and \
                    prev_item_dict.get('album') == current_item_dict.get('album'):
                    match = True
            elif category_name == 'artists':
                if prev_item_dict.get('artist') == current_item_dict.get('artist'):
                    match = True
            elif category_name == 'albums':
                if prev_item_dict.get('artist') == current_item_dict.get('artist') and \
                    prev_item_dict.get('album') == current_item_dict.get('album'):
                    match = True
            elif category_name == 'media_channels':
                if prev_item_dict.get('channel') == current_item_dict.get('channel'):
                    match = True
            
            if match:
                previous_rank_found = idx + 1 
                #self.log(f"DEBUG: Match found for {category_name} item at prev rank {previous_rank_found}")
                break 
        
        calculated_change = 0
        is_new = (previous_rank_found is None)
        if is_new:
            #self.log(f"DEBUG: No match found for {category_name} item. Marked as NEW.")
            pass

        if not is_new:
            calculated_change = previous_rank_found - current_rank
        
        #self.log(f"DEBUG: Final change for item: Change={calculated_change}, New={is_new}")
        return {'change_value': calculated_change, 'is_new_entry': is_new, 'is_re_entry': False}

    def store_chart_data_history(self, type_of_chart, period_identifier, chart_data_list):
        if not chart_data_list: 
            #self.log(f"DEBUG: store_chart_data_history - No data to store for {type_of_chart}/{period_identifier}")
            return
        
        # Log structure of first item being saved
        #self.log(f"DEBUG: Storing chart history for {type_of_chart}/{period_identifier}. Count: {len(chart_data_list)}. First item: {chart_data_list[0] if chart_data_list else 'None'}")

        try:
            json_data = json.dumps(chart_data_list) 
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO chart_history (type, period, data, timestamp) VALUES (?, ?, ?, CURRENT_TIMESTAMP)",
                            (type_of_chart, period_identifier, json_data))
                conn.commit()
        except Exception as e: self.log(f"Error storing chart history for {type_of_chart}/{period_identifier}: {e}", level="WARNING")

    def get_previous_chart_data(self, type_of_chart, period_identifier):
        self.log(f"Getting previous chart data for {type_of_chart}/{period_identifier}", level="DEBUG")

        period_conditions = {
            "daily":   "date(timestamp) = date('now','-1 day')",
            "weekly":  "date(timestamp) >= date('now','-14 days') AND date(timestamp) < date('now','-7 days')",
            "monthly": "date(timestamp) >= date('now','-60 days') AND date(timestamp) < date('now','-30 days')",
            "yearly":  "date(timestamp) >= date('now','-730 days') AND date(timestamp) < date('now','-365 days')",
        }
        condition = period_conditions.get(period_identifier)

        if condition:
            query = (
                "SELECT data FROM chart_history "
                "WHERE type = ? AND period = ? AND " + condition + " "
                "ORDER BY timestamp DESC LIMIT 1"
            )
        else:
            query = "SELECT data FROM chart_history WHERE type = ? AND period = ? ORDER BY timestamp DESC LIMIT 1"

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(query, (type_of_chart, period_identifier))
                res = cursor.fetchone()
                if res and res[0]:
                    loaded = json.loads(res[0])
                    #self.log(f"DEBUG: Loaded previous data for {type_of_chart}/{period_identifier}. Count: {len(loaded)}", level="DEBUG")
                    return loaded
        except Exception as e:
            self.log(f"Error fetching previous chart for {type_of_chart}/{period_identifier}: {e}", level="WARNING")

        #self.log(f"DEBUG: No previous data found for {type_of_chart}/{period_identifier}", level="DEBUG")
        return []
