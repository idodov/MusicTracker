# File path: apps/music_tracker.py

import appdaemon.plugins.hass.hassapi as hass
import datetime
import sqlite3
import re
import time
import threading

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
                to_remove = [track_id for track_id, timestamp in self.played_tracks.items()
                            if current_time - timestamp > 600]
                for track_id in to_remove:
                    del self.played_tracks[track_id]

class MusicTracker(hass.Hass):
    def initialize(self):
        self.media_players = self.args["media_players"]
        self.duration = self.args["duration"]
        self.db_path = self.args["db_path"]
        self.track_manager = TrackManager()  # Initialize TrackManager
        self.create_db()
        self.cleanup_old_tracks()
        
        for media_player in self.media_players:
            self.listen_state(self.track_media, media_player, attribute="media_title")

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
                #print(self.track_manager.played_tracks)
                
                if not album and media_channel:
                    album = f'{media_channel} / {artist}'

                self.log(f"Storing track: {artist} | {clean_title} | {album}")
                self.store_in_db(artist, clean_title, album, media_channel)
                self.update_sensors()

    def clean_track_title(self, title: str) -> str:
        keywords = [
            'remaster', 'remastered', 'mix', 'remix', 'dub', 'demo', 'instrumental'
            'extended', 'version', 'radio', 'live', 'edit', 'anniversary', 'edition', 'single'
        ]
    
        # Create a regex pattern to match the keywords
        pattern = re.compile(
            r'[\(\[\-]?[^()\[\]-]*\b(?:' + '|'.join(keywords) + r')\b[^()\[\]-]*[\)\]\-]?',
            re.IGNORECASE
        )
    
        # Use regex to substitute the matched patterns with an empty string
        cleaned_title = pattern.sub('', title).strip()
    
        return cleaned_title

    def store_in_db(self, artist, title, album, media_channel):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO music_history (artist, title, album, media_channel)
                VALUES (?, ?, ?, ?)
            """, (artist, title, album, media_channel))
            conn.commit()

    def update_sensors(self):
        timeframes = {
            "daily": "1 day",
            "weekly": "7 days",
            "monthly": "30 days",
            "yearly": "365 days"
        }

        for period, days in timeframes.items():
            limit = 100 if period in ["monthly", "yearly"] else 20
            top_songs = self.get_top_songs(days, limit)
            top_artists = self.get_top_artists(days, limit)
            top_albums = self.get_top_albums(days, limit)
            top_media_channels = self.get_top_media_channels(days, limit)

            self.set_state(f"sensor.top_{period}_songs", state="Top Songs", attributes={"songs": top_songs})
            self.set_state(f"sensor.top_{period}_artists", state="Top Artists", attributes={"artists": top_artists})
            self.set_state(f"sensor.top_{period}_albums", state="Top Albums", attributes={"albums": top_albums})
            self.set_state(f"sensor.top_{period}_media_channels", state="Top Media Channels", attributes={"media_channels": top_media_channels})

    def get_top_songs(self, days, limit):
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
        for item in results:
            top_songs.append({
                "title": item[0],
                "artist": item[1],
                "album": item[2],
                "play_count": item[3]
            })

        return top_songs

    def get_top_artists(self, days, limit):
        query = f"""
            SELECT artist, title, album, COUNT(*) as count
            FROM music_history
            WHERE timestamp >= datetime('now', '-{days}')
            GROUP BY artist, title, album
            ORDER BY count DESC
        """

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            results = cursor.fetchall()

        artist_songs = {}
        for item in results:
            artist = item[0]
            song = {
                "title": item[1],
                "album": item[2],
                "play_count": item[3]
            }
            if artist not in artist_songs:
                artist_songs[artist] = {"songs": [], "total_play_count": 0}
            artist_songs[artist]["songs"].append(song)
            artist_songs[artist]["total_play_count"] += item[3]

        top_artists = []
        for artist, data in sorted(artist_songs.items(), key=lambda x: x[1]["total_play_count"], reverse=True):
            top_artists.append({
                "artist": artist,
                "songs": data["songs"],
                "total_play_count": data["total_play_count"]
            })
            if len(top_artists) >= limit:
                break

        return top_artists

    def get_top_albums(self, days, limit):
        query = f"""
            SELECT artist, album, COUNT(*) as count
            FROM music_history
            WHERE timestamp >= datetime('now', '-{days}')
            GROUP BY artist, album
            ORDER BY count DESC
            LIMIT {limit}
        """

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            results = cursor.fetchall()

        top_albums = []
        for item in results:
            top_albums.append({
                "artist": item[0],
                "album": item[1],
                "play_count": item[2]
            })

        return top_albums

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

        top_media_channels = []
        for item in results:
            top_media_channels.append({
                "media_channel": item[0],
                "play_count": item[1]
            })

        return 
        
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



# In your apps.yaml file, you would configure this app like so:
#
# music_tracker:
#   module: music_tracker
#   class: MusicTracker
#   db_path: "/config/music_history.db"
#   media_players:
#     - media_player.living_room_speaker
#     - media_player.bedroom_speaker
#

