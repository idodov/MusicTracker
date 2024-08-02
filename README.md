# Appdaemon Music Tracker
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

Certainly! Here's a rephrased version for your GitHub page in Markdown format:

---

## Guide to Creating an AI Data Analyst for Top Music Charts

This guide will help you set up an AI data analyst to track top music charts using Google AI Conversation Agent integrated with Home Assistant. Feel free to use any other AI agents you prefer.

### Steps:

1. **Google AI Integration**:
    - Install the Google AI integration using your Google API key as described on the integration page.

2. **Prepare Home Assistant**:
    - If you don't already have a `python_scripts` directory, create one in the `homeassistant/config` directory.

3. **Download the Python Script**:
    - Grab the Python file from [this repository](https://github.com/pmazz/ps_hassio_entities/tree/master/python_scripts) and place it inside the `python_scripts` directory.

4. **Update Configuration**:
    - Open `configuration.yaml` and add the following line if it doesn't already exist:

    ```yaml
    python_script:
    ```

5. **Restart Home Assistant** to apply the changes.

6. **Create a Custom Script**:
    - Now, create a script that will send your music listening habits to the AI agent and store the data inside a sensor attribute for easy access.
    - Goto Settings > Automation > Scripts and Create a new script.
    - Goto the YAML mode and paste this code:
      ```yaml
      alias: ai
      sequence:
        - service: google_generative_ai_conversation.generate_content
          data:
            prompt: >
              {% set songs = state_attr('sensor.top_weekly_songs', 'songs') %} {% set
              chart_title = state_attr('sensor.top_weekly_songs', 'chart_title') %} {%
              set chart_dates = state_attr('sensor.top_weekly_songs', 'chart_dates')
              %} Let's dive into my music taste! Here's a breakdown of what I or anyone who shared in the house music listened
              to during dates: {{ chart_dates }}.
              played: | Artist | Title | Play Count |
              |--------|-------|------------|{% for song in songs %} | {{ song.artist
              }} | {{ song.title }} | {{ song.play_count }} |{% endfor %}

              Analyze my listening habits to uncover my music preferences. What
              genres, moods, or artists do I gravitate towards? What can my listening
              data reveal about my musical tastes? Be possitive.

              Based on my preferences, recommend new artists and songs that I might
              enjoy. Surprise me with some fresh tracks and or trivias about the artist in the list.

              Your reply in markdown.
          response_variable: ai_response
        - service: python_script.hass_entities
             data:
               action: set_state_attributes
               entity_id: input_boolean.music_charts
               attributes:
                 - ai_text: "{{ ai_response['text'] }}"
                 - ai_update: "{{ '' ~ now().strftime('%H:%M | %d/%m/%Y') }}"
      ```
   - Now you can create an automation to make the script runs whenever you want and/or create a button entity to press it on your dashboad to run it.
     Here a simple dashboad card to active and see the AI results.

      ```yaml
     type: vertical-stack
     cards:
       - show_name: true
         show_icon: false
         type: button
         tap_action:
           action: call-service
           service: script.ai
           target: {}
         entity: input_boolean.music_charts
         name: AI
         icon: mdi:account-music
         show_state: false
       - type: markdown
         content: |-
            Update: {{ state_attr('input_boolean.music_charts', 'ai_update') }}
            {{ state_attr('input_boolean.music_charts', 'ai_text') }}
       title: AI Analytics
      ```
______
The Data in saved local for a year.
