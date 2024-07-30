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
* ***Update Chart**: You can be update the charts by toggle the sensor* `input_boolean.music_charts`

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
   db_path: "/config/music_data_history.db"
   duration: 30
   min_songs_for_album: 4
   update_time: "02:00:00"
   media_players:
     - media_player.living_room
     - media_player.bedroom
   ```
4. Restart AppDaemon to get everything up and running. Head over to the Home Assistant dashboard to see your new music charts in action!

## Customize the config:
* Replace `media_player.living_room` and `media_player.bedroom` with the names of your media players.
* Adjust `duration` to set the delay before storing a track (in seconds).
* Set `min_songs_for_album` to determine the minimum songs for an album to appear on the charts.
* Change `update_time` to specify when the charts should be updated daily.

The script create an input boolean called `input_boolean.music_charts` in your Home Assistant configuration. This will control when the charts are updated.

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

## Top Albums
```yaml
type: markdown
content: >
  ### {{ states.sensor.top_weekly_albums.attributes.chart_title }} {{
  states.sensor.top_weekly_albums.attributes.chart_dates }}

  | # |Artist|Album|Counts|Status|

  |:---|:-----|:----|:----:|:----:|{% for album in
  states.sensor.top_weekly_albums.attributes.albums[:5] %}

  | {{ loop.index }} |{{ album.artist }}| {{ album.album }} | {{
  album.play_count }} | {% if album.change > 0 %}<font color="green">🔺{{
  album.change }}</font>{% elif album.change < 0 %}<font color="red">🔻{{
  album.change | abs }}</font>{% else %} ➡️{% endif %} |{% endfor %}


  ### {{ states.sensor.top_monthly_albums.attributes.chart_title }} {{
  states.sensor.top_monthly_albums.attributes.chart_dates }}

  | # |Artist|Album|Counts|Status|

  |:---|:-----|:----|:----:|:----:|{% for album in
  states.sensor.top_monthly_albums.attributes.albums[:5] %}

  | {{ loop.index }} |{{ album.artist }}| {{ album.album }} | {{
  album.play_count }} |{% if album.change > 0 %}<font color="green">🔺{{
  album.change }}</font>{% elif album.change < 0 %}<font color="red">🔻{{
  album.change | abs }}</font>{% else %} ➡️{% endif %} |{% endfor %}


  ### {{ states.sensor.top_yearly_albums.attributes.chart_title }} {{
  states.sensor.top_yearly_albums.attributes.chart_dates }}

  | # |Artist|Album|Counts|Status|

  |:---|:-----|:----|:----:|:----:|{% for album in
  states.sensor.top_yearly_albums.attributes.albums[:5] %}

  | {{ loop.index }} |{{ album.artist }}| {{ album.album }} | {{
  album.play_count }} |{% if album.change > 0 %}<font color="green">🔺{{
  album.change }}</font>{% elif album.change < 0 %}<font color="red">🔻{{
  album.change | abs }}</font>{% else %} ➡️{% endif %} |{% endfor %}
title: Albums Charts
```

## Top Songs
```yaml
### {{ states.sensor.top_daily_songs.attributes.chart_title }} {{ states.sensor.top_daily_songs.attributes.chart_dates }}
| # |Artist|Title|Counts|Status|
|:---|:-----|:----|:----:|:----:|{% for song in states.sensor.top_daily_songs.attributes.songs[:5] %}
| {{ loop.index }} |{{ song.artist }}| {{ song.title }} | {{ song.play_count }} | {% if song.change > 0 %}<font color="green">🔺 {{ song.change }}</font>{% elif song.change < 0 %}<font color="red">🔻 {{ song.change | abs }}</font>{% else %} ➡️{% endif %} |{% endfor %}

### {{ states.sensor.top_weekly_songs.attributes.chart_title }} {{ states.sensor.top_weekly_songs.attributes.chart_dates }}
| # |Artist|Title|Counts|Status|
|:---|:-----|:----|:----:|:----:|{% for song in states.sensor.top_weekly_songs.attributes.songs[:5] %}
| {{ loop.index }} |{{ song.artist }}| {{ song.title }} | {{ song.play_count }} |{% if song.change > 0 %}<font color="green">🔺 {{ song.change }}</font>{% elif song.change < 0 %}<font color="red">🔻 {{ song.change | abs }}</font>{% else %} ➡️{% endif %} |{% endfor %}

### {{ states.sensor.top_monthly_songs.attributes.chart_title }} {{ states.sensor.top_monthly_songs.attributes.chart_dates }}
| # |Artist|Title|Counts|Status|
|:---|:-----|:----|:----:|:----:|{% for song in states.sensor.top_monthly_songs.attributes.songs[:5] %}
| {{ loop.index }} |{{ song.artist }}| {{ song.title }} |  {{ song.play_count }}| {% if song.change > 0 %}<font color="green">🔺 {{ song.change }}</font>{% elif song.change < 0 %}<font color="red">🔻 {{ song.change | abs }}</font>{% else %} ➡️{% endif %} |{% endfor %}

### {{ states.sensor.top_yearly_songs.attributes.chart_title }} {{ states.sensor.top_yearly_songs.attributes.chart_dates }}
| # |Artist|Title|Counts|Status|
|:---|:-----|:----|:----:|:----:|{% for song in states.sensor.top_yearly_songs.attributes.songs[:5] %}
| {{ loop.index }} |{{ song.artist }}| {{ song.title }} |  {{ song.play_count }}|{% if song.change > 0 %}<font color="green">🔺 {{ song.change }}</font>{% elif song.change < 0 %}<font color="red">🔻 {{ song.change | abs }}</font>{% else %} ➡️{% endif %} |{% endfor %}

```

## Top Radio Channels
```yaml
{% set channels = state_attr('sensor.top_yearly_media_channels', 'media_channels') %}{% set chart_title = state_attr('sensor.top_yearly_media_channels', 'chart_title') %}{% set chart_dates = state_attr('sensor.top_yearly_media_channels', 'chart_dates') %}
## Radio Chart
_{{ chart_dates }}_
{% if channels %}
| **Media Channel** | **Play Count** | 
|------------------|---------------|
{% for channel in channels %}| {{ channel.media_channel }} | {{ channel.play_count }} | 
{% endfor %}
{% else %}No data available.{% endif %}
```

______
The Data in saved local for a year.
