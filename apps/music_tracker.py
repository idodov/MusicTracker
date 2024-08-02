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
  min_songs_for_album: 3
  update_time: "00:00:00"
  media_players:
    - media_player.kitchen
    - media_player.bathroom
    - media_player.bedroom
    - media_player.living_room
    - media_player.dining_room
"""
import appdaemon.plugins.hass.hassapi as hass
import datetime
import sqlite3
import re
import time
import threading
import json

class TrackManager:
    def __init__(self):
        self.played_tracks = {}
        self.lock = threading.Lock()
        self.cleanup_interval = 60  # Run cleanup every 60 seconds

        # Start the cleanup thread
        self.cleanup_thread = threading.Thread(target=self.cleanup_tracks)
        self.cleanup_thread.daemon = True
        self.cleanup_thread.start()

    def add_track(self, track_id):
        with self.lock:
            self.played_tracks[track_id] = time.time()

    def cleanup_tracks(self):
        while True:
            time.sleep(self.cleanup_interval)
            current_time = time.time()
            with self.lock:
                to_remove = [track_id for track_id, timestamp in self.played_tracks.items() if current_time - timestamp > 600]
                for track_id in to_remove:
                    del self.played_tracks[track_id]

class MusicTracker(hass.Hass):
    def initialize(self):
        self.media_players = self.args.get("media_players", ["media_player.era300"])
        self.duration = self.args.get("duration", 30)
        self.min_songs_for_album = self.args.get("min_songs_for_album", 3)  # New argument
        self.chart_update_time = self.args.get("update_time", "00:00:00")
        self.db_path = self.args.get("db_path", "/config/MusicTracker.db")
        self.track_manager = TrackManager()  # Initialize TrackManager
        self.create_db()
        self.cleanup_old_tracks()
        self.Restart_Charts = True

        if not self.entity_exists("input_boolean.music_charts"):
            self.set_state("input_boolean.music_charts", state="off")
        
        self.update_sensors()
        self.Restart_Charts = False
        
        for media_player in self.media_players:
            self.listen_state(self.track_media, media_player, attribute="media_title")

        self.run_daily(self.update_daily_charts, self.chart_update_time)
        self.listen_state(self.check_boolean_state, "input_boolean.music_charts", attribute="state")

    def check_boolean_state(self, entity, attribute, old, new, kwargs):
        if new == "on":
            self.update_sensors()

    def update_daily_charts(self, kwargs):
        self.set_state("input_boolean.music_charts", state="on")

    def create_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS music_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    artist TEXT,
                    title TEXT,
                    album TEXT,
                    media_channel TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chart_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    type TEXT,
                    period TEXT,
                    data TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def track_media(self, entity, attribute, old, new, kwargs):
        if new and self.get_state(entity) == "playing":
            self.run_in(self.store_media_info, self.duration, entity=entity)

    def store_media_info(self, kwargs):
        entity = kwargs["entity"]
        if self.get_state(entity) == "playing":
            attributes = self.get_state(entity, attribute="all")["attributes"]
            artist = attributes.get("media_artist")
            title = attributes.get("media_title")
            album = attributes.get("media_album_name")
            media_channel = attributes.get("media_channel")

            if not artist:
                return

            if album:
                album = self.clean_track_title(album)

            if title:
                if title.lower() == "tv":
                    return

                clean_title = self.clean_track_title(title)
                track_id = f"{artist} - {title}"

                if track_id in self.track_manager.played_tracks:
                    return
                
                self.track_manager.add_track(track_id)
                
                if not album and media_channel:
                    album = f'{media_channel} / {artist}'

                if not album:
                    album = title

                self.log(f"Storing track: {artist} | {clean_title} | {album}")
                self.store_in_db(artist, clean_title, album, media_channel)

                latest_song = {
                    "artist": artist,
                    "title": clean_title,
                    "album": album,
                }

                self.set_state("input_boolean.music_charts", state="off", attributes=latest_song)


    def remove_unmatched(self, match):
        """Checks if a match has a closing bracket and returns an empty string if not."""
        start, end = match.span()
        if not re.search(r"[\]\)]", match.string[start:]):
            return ""
        return match.group()

    def clean_track_title(self, title: str) -> str:
        keywords = [
            'remaster', 'remastered', 're-master', 're-mastered', 'mix', 'remix', 'dub', 
            'dubs', 'demo', 'deluxe', 'instrumental', 'extended', 'version', 'radio edit', 'live', 
            'edit', 'anniversary', 'edition', 'single'
        ]
    
        # Create a regex pattern to match the keywords
        pattern = re.compile(
            r'\s*[\(\[\-](?:[^\(\)\[\]\-]*\b(?:' + '|'.join(keywords) + r')\b[^\(\)\[\]\-]*)[\)\]\-]?\s*',
            re.IGNORECASE
        )

        cleaned_title = pattern.sub('', title).strip()
        cleaned_title = re.sub(r"[\(\[].*", self.remove_unmatched, cleaned_title)

        cleaned_title = re.sub(r"\s+$", "", cleaned_title)
    
        return cleaned_title

    def store_in_db(self, artist, title, album, media_channel):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO music_history (artist, title, album, media_channel)
                VALUES (?, ?, ?, ?)
            """, (artist, title, album, media_channel))
            conn.commit()

    def update_sensors(self, *kwargs):
        if self.get_state("input_boolean.music_charts") == "on" or self.Restart_Charts == True:
            timeframes = {
                "daily": "1 day",
                "weekly": "7 days",
                "monthly": "30 days",
                "yearly": "365 days"
            }

            for period, days in timeframes.items():
                limit = 100 #if period in ["monthly", "yearly"] else 20
                chart_title_songs = f"Top {period.capitalize()} Songs"
                chart_title_artists = f"Top {period.capitalize()} Artists"
                chart_title_albums = f"Top {period.capitalize()} Albums"
                chart_title_media_channels = f"Top {period.capitalize()} Media Channels"
                chart_title_popular_artists = f"Popular {period.capitalize()} Artists"
                chart_dates = self.get_chart_dates(days)
                top_songs = self.get_top_songs(days, limit)
                top_artists = self.get_top_artists(days, limit)
                top_albums = self.get_top_albums(days, limit)
                top_media_channels = self.get_top_media_channels(days, limit)
                popular_artists = self.get_popular_artists(days, limit)

                self.set_state(f"sensor.top_{period}_songs", state=f"Top Songs ({chart_dates})", attributes={"songs": top_songs, "chart_title": chart_title_songs, "chart_dates": chart_dates})
                self.set_state(f"sensor.top_{period}_artists", state=f"Top Artists ({chart_dates})", attributes={"artists": top_artists, "chart_title": chart_title_artists, "chart_dates": chart_dates})
                self.set_state(f"sensor.top_{period}_albums", state=f"Top Albums ({chart_dates})", attributes={"albums": top_albums, "chart_title": chart_title_albums, "chart_dates": chart_dates})
                self.set_state(f"sensor.top_{period}_media_channels", state=f"Top Media Channels ({chart_dates})", attributes={"media_channels": top_media_channels, "chart_title": chart_title_media_channels, "chart_dates": chart_dates})
                self.set_state(f"sensor.popular_artist_chart", state=f"Popular Artists ({chart_dates})", attributes={"artists": popular_artists, "chart_title": chart_title_popular_artists, "chart_dates": chart_dates})

                self.store_chart_history("songs", period, top_songs)
                self.store_chart_history("artists", period, top_artists)
                self.store_chart_history("albums", period, top_albums)
                self.store_chart_history("media_channels", period, top_media_channels)

            self.log("Charts updated.")
            self.set_state("input_boolean.music_charts", state="off")
            self.Restart_Charts = False


    def get_chart_dates(self, days):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT MIN(timestamp), MAX(timestamp) FROM music_history WHERE timestamp >= datetime('now', '-{days}')")
            result = cursor.fetchone()
            start_date = datetime.datetime.strptime(result[0], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y') if result[0] else 'N/A'
            end_date = datetime.datetime.strptime(result[1], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y') if result[1] else 'N/A'
            return f"{start_date} - {end_date}"

    def get_top_songs(self, days, limit):
        previous_chart = self.get_previous_chart("songs", "daily")

        query = f"""
            SELECT title, artist, album, COUNT(*) as count
            FROM music_history
            WHERE timestamp >= datetime('now', '-{days}')
            GROUP BY title, artist, album
            ORDER BY count DESC
            LIMIT {limit}
        """

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            results = cursor.fetchall()

        top_songs = []
        for idx, item in enumerate(results):
            change = self.calculate_change(previous_chart, item, idx + 1, 'songs')
            top_songs.append({
                "title": item[0],
                "artist": item[1],
                "album": item[2],
                "play_count": item[3],
                "change": change['change'],
                "new_entry": change['new_entry'],
                "re_entry": change['re_entry']
            })

        return top_songs

    def get_top_artists(self, days, limit):
        previous_chart = self.get_previous_chart("artists", "daily")

        query = f"""
            SELECT artist, COUNT(*) as count
            FROM music_history
            WHERE timestamp >= datetime('now', '-{days}')
            GROUP BY artist
            ORDER BY count DESC
            LIMIT {limit}
        """

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            results = cursor.fetchall()

        top_artists = []
        for idx, item in enumerate(results):
            change = self.calculate_change(previous_chart, item, idx + 1, 'artists')
            top_artists.append({
                "artist": item[0],
                "play_count": item[1],
                "change": change['change'],
                "new_entry": change['new_entry'],
                "re_entry": change['re_entry']
            })

        return top_artists

    def get_top_albums(self, days, limit):
        previous_chart = self.get_previous_chart("albums", "daily")

        album_counts_query = f"""
            SELECT artist, album, COUNT(DISTINCT title) as song_count
            FROM music_history
            WHERE timestamp >= datetime('now', '-{days}')
            GROUP BY artist, album
            HAVING song_count >= {self.min_songs_for_album}
            ORDER BY song_count DESC
            LIMIT {limit}
        """

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(album_counts_query)
            results = cursor.fetchall()

        top_albums = []
        for idx, item in enumerate(results):
            change = self.calculate_change(previous_chart, item, idx + 1, 'albums')
            top_albums.append({
                "album": item[1],
                "artist": item[0],
                "play_count": item[2],
                "change": change['change'],
                "new_entry": change['new_entry'],
                "re_entry": change['re_entry'],
                "songs": self.get_album_songs(item[0], item[1], days)
            })

        return top_albums

    def get_album_songs(self, artist, album, days):
        query = f"""
            SELECT title, COUNT(*) as play_count
            FROM music_history
            WHERE artist = ? AND album = ? AND timestamp >= datetime('now', '-{days}')
            GROUP BY title
            ORDER BY play_count DESC
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query, (artist, album))
            results = cursor.fetchall()

        songs = []
        for item in results:
            songs.append({
                "title": item[0],
                "play_count": item[1]
            })

        return songs

    def get_top_media_channels(self, days, limit):
        query = f"""
            SELECT media_channel, COUNT(*) as count
            FROM music_history
            WHERE timestamp >= datetime('now', '-{days}')
            GROUP BY media_channel
            ORDER BY count DESC
            LIMIT {limit}
        """

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            results = cursor.fetchall()

        previous_chart = self.get_previous_chart('media_channels', days)
        top_media_channels = []
        for idx, item in enumerate(results):
            if item[0] is not None:  # Remove entries where media_channel is null
                change = self.calculate_change(previous_chart, item, idx + 1, 'media_channels')
                top_media_channels.append({
                    "media_channel": item[0],
                    "play_count": item[1],
                    "change": change['change'],
                    "new_entry": change['new_entry'],
                    "re_entry": change['re_entry']
                })

        return top_media_channels

    def get_popular_artists(self, days, limit):
        query = f"""
            SELECT artist, COUNT(DISTINCT title) as unique_songs
            FROM music_history
            WHERE timestamp >= datetime('now', '-{days}')
            GROUP BY artist
            ORDER BY unique_songs DESC
            LIMIT {limit}
        """

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            results = cursor.fetchall()

        popular_artists = []
        for item in results:
            popular_artists.append({
                "artist": item[0],
                "unique_songs": item[1]
            })

        return popular_artists

    def calculate_change(self, previous_chart, current_item, current_rank, chart_type):
        if chart_type == 'songs':
            title, artist, album = current_item[:3]
            previous_rank = next((i + 1 for i, item in enumerate(previous_chart) if item['title'] == title and item['artist'] == artist and item['album'] == album), None)
        elif chart_type == 'artists':
            artist = current_item[0]
            previous_rank = next((i + 1 for i, item in enumerate(previous_chart) if item['artist'] == artist), None)
        elif chart_type == 'albums':
            album, artist = current_item[:2]
            previous_rank = next((i + 1 for i, item in enumerate(previous_chart) if item['album'] == album and item['artist'] == artist), None)
        elif chart_type == 'media_channels':
            media_channel = current_item[0]
            previous_rank = next((i + 1 for i, item in enumerate(previous_chart) if item['media_channel'] == media_channel), None)

        if previous_rank is None:
            return {'change': 0, 'new_entry': True, 're_entry': False}
        else:
            return {'change': previous_rank - current_rank, 'new_entry': False, 're_entry': current_rank > previous_rank}

    def store_chart_history(self, chart_type, period, data):
        data_json = json.dumps(data)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO chart_history (type, period, data)
                VALUES (?, ?, ?)
            """, (chart_type, period, data_json))
            conn.commit()

    def get_previous_chart(self, chart_type, period):
        query = f"""
            SELECT data FROM chart_history
            WHERE type = ? AND period = ?
            ORDER BY timestamp DESC
            LIMIT 1, 1
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query, (chart_type, period))
            result = cursor.fetchone()
            return json.loads(result[0]) if result else []

    def cleanup_old_tracks(self):
        """Removes tracks older than one year from the database."""
        one_year_ago = datetime.datetime.now() - datetime.timedelta(days=365)
        one_year_ago_str = one_year_ago.strftime('%Y-%m-%d')

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM music_history
                WHERE timestamp < ?
            """, (one_year_ago_str,))
            conn.commit()

