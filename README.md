# 🎶 MusicTracker for Home Assistant 🎶
MusicTracker is your ultimate companion for tracking and charting your favorite tunes within Home Assistant. With this powerful AppDaemon script, you can keep tabs on what's playing, create captivating music charts, and explore your music data in depth. Let's get those musical vibes flowing!

There's an exciting bonus feature waiting for you: AI-powered music taste analysis! Imagine receiving a personalized report about your listening habits. In the readme, you'll find an example of how to integrate this with Google AI, but feel free to choose any agent that suits your fancy.

So, whether you're a chart-topper enthusiast or a deep-cut aficionado, MusicTracker has you covered.

## 🎸 Chart Rules

Here are the chart sensors we provide:

- **Top Songs:** Tracks the most played songs.
- **Top Artists:** Artists with the highest play counts.
- **Top Albums:** Albums with the highest play counts (only albums with 3+ songs qualify).
- **Top Media Channels:** Channels where your music is played the most.
- **Popular Artists:** Artists with the most unique songs played.
- ***Update Chart:** You can update the charts by toggling the sensor `input_boolean.music_charts`.*

## 🚀 Installation

Get ready to set up your Home Assistant to rock with MusicTracker!

### 1. Install AppDaemon

First things first, you'll need to install the AppDaemon add-on in Home Assistant:

1. Go to the Home Assistant **Settings** > **Add-ons** > **Add-on Store**.
2. Search for "AppDaemon" and install it.
3. Start the AppDaemon add-on.
4. Set it to start on boot and watch the logs to ensure everything runs smoothly.

### 2. Set Up MusicTracker

1. **Copy the MusicTracker script**:
   - Place the script in `/addon_configs/a0d7b954_appdaemon/apps/music_tracker.py`.

2. **Configure `apps.yaml`**:
   - Open `apps.yaml` in your `appdamon/apps` directory and add the following configuration:
   ```yaml
   music_tracker:
     module: music_tracker
     class: MusicTracker
     db_path: "/config/music_history.db"
     duration: 30
     min_songs_for_album: 3
     update_time: "02:00:00"
     media_players:
       - media_player.living_room
       - media_player.bedroom
   ```
   
#### Customize the Config

- **Media Players:** Replace `media_player.living_room` and `media_player.bedroom` with the names of your media players.
- **Duration:** Adjust `duration` to set the delay before storing a track (in seconds).
- **Minimum Songs for Album:** Set `min_songs_for_album` to determine the minimum songs for an album to appear on the charts.
- **Update Time:** Change `update_time` to specify when the charts should be updated daily.

  The script creates an input boolean called `input_boolean.music_charts` in your Home Assistant configuration. This will control when the charts are updated.

### 3. Restart AppDaemon

To get everything up and running, go ahead and restart AppDaemon. Then, start playing a variety of music tracks.

> [!TIP]
> **Remember to be patient!** The charts work best after a month-long cycle. On the first day, you’ll enjoy the popular artist and songs daily charts. Wait for a week, and you’ll start seeing your own personalized charts displayed on your dashboard.

## Home Assistant Card Examples

### Media Channel Data Card

Add this markdown to your Home Assistant dashboard to display the media channel data:

```yaml
type: custom:markdown-card
title: Media Channel Data
content: |
  ## Media Channels Chart
  ### {{ states('sensor.top_daily_media_channels') }}
  {% set channels = state_attr('sensor.top_daily_media_channels', 'media_channels') %}
  {% set chart_title = state_attr('sensor.top_daily_media_channels', 'chart_title') %}
  {% set chart_dates = state_attr('sensor.top_daily_media_channels', 'chart_dates') %}

  **{{ chart_title }}**
  _{{ chart_dates }}_

  {% if channels %}
    | **Media Channel** | **Play Count** | **Change** | **New Entry** | **Re Entry** |
    |------------------|---------------|------------|---------------|--------------|
    {% for channel in channels %}
      | {{ channel.media_channel }} | {{ channel.play_count }} | {{ channel.change }} | {{ channel.new_entry }} | {{ channel.re_entry }} |
    {% endfor %}
  {% else %}
    No data available.
  {% endif %}
```

### Top Albums Card

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
  album.change | abs }}</font>{% else %} -{% endif %} |{% endfor %}


  ### {{ states.sensor.top_monthly_albums.attributes.chart_title }} {{
  states.sensor.top_monthly_albums.attributes.chart_dates }}

  | # |Artist|Album|Counts|Status|

  |:---|:-----|:----|:----:|:----:|{% for album in
  states.sensor.top_monthly_albums.attributes.albums[:5] %}

  | {{ loop.index }} |{{ album.artist }}| {{ album.album }} | {{
  album.play_count }} |{% if album.change > 0 %}<font color="green">🔺{{
  album.change }}</font>{% elif album.change < 0 %}<font color="red">🔻{{
  album.change | abs }}</font>{% else %} -{% endif %} |{% endfor %}


  ### {{ states.sensor.top_yearly_albums.attributes.chart_title }} {{
  states.sensor.top_yearly_albums.attributes.chart_dates }}

  | # |Artist|Album|Counts|Status|

  |:---|:-----|:----|:----:|:----:|{% for album in
  states.sensor.top_yearly_albums.attributes.albums[:5] %}

  | {{ loop.index }} |{{ album.artist }}| {{ album.album }} | {{
  album.play_count }} |{% if album.change > 0 %}<font color="green">🔺{{
  album.change }}</font>{% elif album.change < 0 %}<font color="red">🔻{{
  album.change | abs }}</font>{% else %} -{% endif %} |{% endfor %}
title: Albums Charts
```

### Top Songs Card

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
  else %} -{% endif %} |{% endfor %}


  ### {{ states.sensor.top_weekly_songs.attributes.chart_title }} {{
  states.sensor.top_weekly_songs.attributes.chart_dates }}

  | # |Artist|Title|Counts|Status|

  |:---|:-----|:----|:----:|:----:|{% for song in
  states.sensor.top_weekly_songs.attributes.songs[:5] %}

  | {{ loop.index }} |{{ song.artist }}| {{ song.title }} | {{ song.play_count
  }} |{% if song.change > 0 %}<font color="green">🔺 {{ song.change }}</font>{%
  elif song.change < 0 %}<font color="red">🔻 {{ song.change | abs }}</font>{%
  else %} -{% endif %} |{% endfor %}


  ### {{ states.sensor.top_monthly_songs.attributes.chart_title }} {{
  states.sensor.top_monthly_songs.attributes.chart_dates }}

  | # |Artist|Title|Counts|Status|

  |:---|:-----|:----|:----:|:----:|{% for song in
  states.sensor.top_monthly_songs.attributes.songs[:5] %}

  | {{ loop.index }} |{{ song.artist }}| {{ song.title }} |  {{ song.play_count
  }}| {% if song.change > 0 %}<font color="green">🔺 {{ song.change }}</font>{%
  elif song.change < 0 %}<font color="red">🔻 {{ song.change | abs }}</font>{%
  else %} -{% endif %} |{% endfor %}


  ### {{ states.sensor.top_yearly_songs.attributes.chart_title }} {{
  states.sensor.top_yearly_songs.attributes.chart_dates }}

  | # |Artist|Title|Counts|Status|

  |:---|:-----|:----|:----:|:----:|{% for song in
  states.sensor.top_yearly_songs.attributes.songs[:5] %}

  | {{ loop.index }} |{{ song.artist }}| {{ song.title }} |  {{ song.play_count
  }}|{% if song.change > 0 %}<font color="green">🔺 {{ song.change }}</font>{%
  elif song.change < 0 %}<font color="red">🔻 {{ song.change | abs }}</font>{%
  else %} -{% endif %}

 |{% endfor %}
title: Song Charts
```

### Top Radio Channels Card

```yaml
type: markdown
content: >
  {% set channels = state_attr('sensor.top_yearly_media_channels', 'media_channels') %}
  {% set chart_title = state_attr('sensor.top_yearly_media_channels', 'chart_title') %}
  {% set chart_dates = state_attr('sensor.top_yearly_media_channels', 'chart_dates') %}

  ## Radio Chart
  _{{ chart_dates }}_

  {% if channels %}
  | # | **Media Channel** | **Play Count** |
  |---|-------------------|----------------|
  {% for channel in channels %}
  | {{ loop.index }} | {{ channel.media_channel }} | {{ channel.play_count }} |{% endfor %}
  {% else %}
  No data available.
  {% endif %}
```

# Guide to Creating an AI Data Analyst for Top Music Charts

Setup an AI data analyst to track top music charts using Google AI Conversation Agent integrated with Home Assistant. Feel free to use any other AI agents you prefer. Let’s get your music data grooving!

## Steps to Get Started

### 1. Google AI Integration

- Install the [Google Generative AI Conversation](https://www.home-assistant.io/integrations/google_generative_ai_conversation/) using your Google API key as described on the integration page.

### 2. Prepare Home Assistant

- If you don't already have a `python_scripts` directory, create one in the `homeassistant/config` directory.

### 3. Download the Python Script

- Grab the Python file from [this repository](https://github.com/pmazz/ps_hassio_entities/tree/master/python_scripts) and place it inside the `python_scripts` directory.

### 4. Update Configuration

- Open `configuration.yaml` and add the following line if it doesn't already exist:

  ```yaml
  python_script:
  ```

### 5. Restart Home Assistant

- Restart Home Assistant to apply the changes.

### 6. Create a Custom Script

Now, let's create a script that will send your music listening habits to the AI agent and store the data inside a sensor attribute for easy access.

- Go to Settings > Automation > Scripts and create a new script.
- Switch to YAML mode and paste this code:

  ```yaml
  alias: ai
  sequence:
    - service: google_generative_ai_conversation.generate_content
      data:
        prompt: >
          {% set songs = state_attr('sensor.top_weekly_songs', 'songs') %}
          {% set chart_title = state_attr('sensor.top_weekly_songs', 'chart_title') %}
          {% set chart_dates = state_attr('sensor.top_weekly_songs', 'chart_dates') %}

          Let's dive into my music taste! Here's a breakdown of what I or anyone who shared in the house music listened to during dates: {{ chart_dates }}.

          | Artist | Title | Play Count |
          |--------|-------|------------|
          {% for song in songs %}
          | {{ song.artist }} | {{ song.title }} | {{ song.play_count }} |
          {% endfor %}

          Analyze my listening habits to uncover my music preferences. What genres, moods, or artists do I gravitate towards? What can my listening data reveal about my musical tastes? Be positive.

          Based on my preferences, recommend new artists and songs that I might enjoy. Surprise me with some fresh tracks and trivia about the artists in the list.

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

- Create an automation to run the script whenever you want and/or create a button entity to press it on your dashboard to run it.

### Dashboard Card Example

Here’s a simple dashboard card to activate and see the AI results:

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

## 🎉 Enjoy Your Music Data!

That’s it! You've now set up an AI-powered music tracking and charting system in your Home Assistant. Dive deep into your music listening habits and discover new trends. Happy listening! 🎧
