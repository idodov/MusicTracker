# Music Tracker
## 🎶 MusicTracker for Home Assistant 🎶
Welcome to MusicTracker, your ultimate tool for tracking and charting your favorite tunes in Home Assistant. This AppDaemon script lets you keep track of what’s playing, create various charts, and dive deep into your music data. Let's get your music data grooving!

### 🎸 Chart Rules
Here are the charts sensors:
* **Top Songs:** Tracks the most played songs.
* **Top Artists:** Artists with the highest play counts.
* **Top Albums:** Albums with the highest play counts (only albums with 3+ songs qualify).
* **Top Media Channels:** Radio Channels where your music is played the most.
* **Popular Artists:** Artists with the most unique songs played.

* **Update Chart**: The can be update the charts by toggle the sensor `input_boolean.music_charts`

## 🚀 Installation
Get ready to set up your Home Assistant to rock with MusicTracker!

1. **Install AppDaemon**
   First things first, you'll need to install the AppDaemon add-on in Home Assistant:
   * Go to the Home Assistant Settings > Add-ons > "Add-on Store".
   * Search for "AppDaemon" and install it.
   * Start the AppDaemon add-on.
   * Set it to start on boot and watch the logs to ensure everything runs smoothly.
2. Copy the MusicTracker script into appdamon/apps/music_tracker.py.
3. Configure apps.yaml
   ```yaml
   #apps.yaml
   
   music_tracker:
   module: music_tracker
   class: MusicTracker
   db_path: "/config/music_history.db"
   media_players:                        # Your media_players you want to participate the charts
     - media_player.living_room_speaker
     - media_player.bedroom_speaker
   update_time: "02:00:00"               # Daily update time
   min_songs_for_album: 3                # Minimum number of songs for an album to qualify
   ```
4. Restart AppDaemon to get everything up and running. Head over to the Home Assistant dashboard to see your new music charts in action!

## Home Assistant Card Example
Add this markdown to your Home Assistant dashboard to display the media channel data:

 ```yaml
type: markdown
content: >
  ### {{ states.sensor.top_daily_songs.attributes.chart_title }} {{
  states.sensor.top_daily_songs.attributes.chart_dates }}

  | # |Artist|Title|Counts|Status|

  |:---|:-----|:----|:----:|:----:|{% for song in
  states.sensor.top_daily_songs.attributes.songs[:5] %}

  | {{ loop.index }} |{{ song.artist }}| {{ song.title }} | {{ song.play_count
  }} | {% if song.change > 0 %}<font color="green">🔺 {{ song.change }}</font>{%
  elif song.change < 0 %}<font color="red">🔻 {{ song.change | abs }}</font>{%
  else %} ➡️{% endif %} |{% endfor %}


  ### {{ states.sensor.top_weekly_songs.attributes.chart_title }} {{
  states.sensor.top_weekly_songs.attributes.chart_dates }}

  | # |Artist|Title|Counts|Status|

  |:---|:-----|:----|:----:|:----:|{% for song in
  states.sensor.top_weekly_songs.attributes.songs[:5] %}

  | {{ loop.index }} |{{ song.artist }}| {{ song.title }} | {{ song.play_count
  }} |{% if song.change > 0 %}<font color="green">🔺 {{ song.change }}</font>{%
  elif song.change < 0 %}<font color="red">🔻 {{ song.change | abs }}</font>{%
  else %} ➡️{% endif %} |{% endfor %}


  ### {{ states.sensor.top_monthly_songs.attributes.chart_title }} {{
  states.sensor.top_monthly_songs.attributes.chart_dates }}

  | # |Artist|Title|Counts|Status|

  |:---|:-----|:----|:----:|:----:|{% for song in
  states.sensor.top_monthly_songs.attributes.songs[:5] %}

  | {{ loop.index }} |{{ song.artist }}| {{ song.title }} |  {{ song.play_count
  }}| {% if song.change > 0 %}<font color="green">🔺 {{ song.change }}</font>{%
  elif song.change < 0 %}<font color="red">🔻 {{ song.change | abs }}</font>{%
  else %} ➡️{% endif %} |{% endfor %}


  ### {{ states.sensor.top_yearly_songs.attributes.chart_title }} {{
  states.sensor.top_yearly_songs.attributes.chart_dates }}

  | # |Artist|Title|Counts|Status|

  |:---|:-----|:----|:----:|:----:|{% for song in
  states.sensor.top_yearly_songs.attributes.songs[:5] %}

  | {{ loop.index }} |{{ song.artist }}| {{ song.title }} |  {{ song.play_count
  }}|{% if song.change > 0 %}<font color="green">🔺 {{ song.change }}</font>{%
  elif song.change < 0 %}<font color="red">🔻 {{ song.change | abs }}</font>{%
  else %} ➡️{% endif %} |{% endfor %}
title: Song Charts
```
______
The Data in saved local for a year.
