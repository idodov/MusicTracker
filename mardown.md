# Charts with Markdown card
## Song Charts
```yaml
type: markdown
content: >-


  ## Top Daily Songs

  | # |Artist|Title|Counts|

  |:---|:-----|:----|:----:|{% for song in
  states.sensor.top_daily_songs.attributes.songs[:5] %}

  | {{ loop.index }} |{{ song.artist }}| {{ song.title }} | {{ song.play_count
  }} |{% endfor %}


  ## Top Weekly Songs

  | # | Artist | Title | Counts |

  |:---|:--------|:-------|:--------:|{% for song in
  states.sensor.top_weekly_songs.attributes.songs[:5] %}

  | {{ loop.index }} | {{ song.artist }} | {{ song.title }} | {{ song.play_count
  }} | {% endfor %}


  ## Top Monthly Songs

  | # | Artist | Title | Counts |

  |:---|:--------|:-------|:--------:|{% for song in
  states.sensor.top_monthly_songs.attributes.songs[:10] %}

  | {{ loop.index }} | {{ song.artist }} | {{ song.title }} | {{ song.play_count
  }} | {% endfor %}


  ## Top Yearly Songs

  | # | Artist | Title | Counts |

  |:---|:--------|:-------|:--------:|{% for song in
  states.sensor.top_yearly_songs.attributes.songs[:10] %}

  | {{ loop.index }} | {{ song.artist }} | {{ song.title }} | {{ song.play_count
  }} | {% endfor %}
title: Song Charts
```
## Artist Charts
```yaml
type: markdown
content: >+
  ## Top Weekly Artists

  | # | Artist | Total Plays |

  |:--|:------|:------------:|{% for artist in
  states.sensor.top_weekly_artists.attributes.artists[:10] %}

  | {{ loop.index }} | {{ artist.artist }} | {{ artist.songs |
  map(attribute='play_count') | sum }} |{% endfor %}


  ## Top Monthly Artists

  | # | Artist | Total Plays |

  |:--|:------|:------------:|{% for artist in
  states.sensor.top_monthly_artists.attributes.artists[:10] %}

  | {{ loop.index }} | {{ artist.artist }} | {{ artist.songs |
  map(attribute='play_count') | sum }} |{% endfor %}


  ## Top Yearly Artists

  | # | Artist | Total Plays |

  |:--|:------|:------------:|{% for artist in
  states.sensor.top_yearly_artists.attributes.artists[:10] %}

  | {{ loop.index }} | {{ artist.artist }} | {{ artist.songs |
  map(attribute='play_count') | sum }} |{% endfor %}

title: Artist Charts

```
## Album Charts
```yaml
type: markdown
content: >+
  ## Top Weekly Albums

  | # | Artist | Album | Play Count |

  |:--|:------|:-----|:----------|{% for album in
  states.sensor.top_weekly_albums.attributes.albums[:10] %}

  | {{ loop.index }} | {{ album.artist }} | {{ album.album }} | {{
  album.play_count }} |{% endfor %}



  ## Top Monthly Albums

  | # | Artist | Album | Play Count |

  |:--|:------|:-----|:----------|{% for album in
  states.sensor.top_monthly_albums.attributes.albums[:10] %}

  | {{ loop.index }} | {{ album.artist }} | {{ album.album }} | {{
  album.play_count }} |{% endfor %}



  ## Top Yearly Albums

  | # | Artist | Album | Play Count |

  |:--|:------|:-----|:----------|{% for album in
  states.sensor.top_yearly_albums.attributes.albums[:10] %}

  | {{ loop.index }} | {{ album.artist }} | {{ album.album }} | {{
  album.play_count }} |{% endfor %}

title: Albums Charts

```
