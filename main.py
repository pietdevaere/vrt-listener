#!/usr/bin/env python3
import requests
import pafy
import subprocess
import time
import tempfile
import os
import shutil
import datetime
import argparse
import csv

class Playlist():
    """Store lists of songs """
    def __init__(self):
        self.songs = []
        # used to store vrt_codes, to keep
        # track of what has been played
        self._history = set()

    def lastcode(self):
        return self.songs[-1].vrt_code()
    def add(self, song):
        """add a song to the beginning of a playlist"""
        self.songs.insert(0, song)
        self._history.add(song.vrt_code())

    def append(self, song):
        """append a song to the end of aplaylist"""
        self.songs.append(song)
        self._history.add(song.vrt_code())

    def __str__(self):
        return("lists of {} songs".format(len(self.songs)))

    def print(self):
        for song in self.songs:
            print(song)

    def first(self):
        return self.songs[0]

    def pop(self):
        return self.songs.pop(0)

    def __len__(self):
        return len(self.songs)

    def in_list(self, song2):
        """check if song2 is in this list"""
        for song in self.songs:
            if song == song2:
                return True
        return False

    def in_history(self, song):
        """check of song has been added to this list"""
        if song.vrt_code() in self._history:
            return True
        return False

    def merge(self, other, append = 0, silent = 1):
        """merge self with other"""
        for song in other.songs:
            if not self.in_history(song):
                if append == 0:
                    self.add(song)
                else:
                    self.append(song)
                if not silent:
                    print("new song:",song)

    def find_videos(self):
        """match every song with a youtube video"""
        for song in self.songs:
            if song.video() == None:
                if not song.find_video():
                    self.remove(song)

    def remove(self, song):
        try:
            self.songs.remove(song)
        except ValueError:
            pass
                
class Song():
    """Store the data for a song"""
    def __init__(self, artist, title, code = None):
        assert type(artist) == str
        assert type(title) == str
        self._artist = artist.strip()
        self._title = title.strip()
        self._video = None
        self._vrtcode = code

    def __eq__(self, other):
        if self._vrtcode != None and other._vrtcode != None:
            if self._vrtcode == other._vrtcode:
                return True
            else:
                return False
        if self._title == other._title:
            if self._artist == other._artist:
                return True
        return False

    def searchterm(self):
        """Return the term used to search on youtube"""
        return(self._artist + ' - ' + self._title)

    def vrt_code(self):
        return self._vrtcode

    def artist(self):
        return self._artist

    def title(self):
        return self._title

    def __str__(self):
        return ("{} - {}".format(self._artist, self._title))

    def url(self):
        """return the streaming url"""
        if self._video == None:
            return None
        return self._video.url()

    def video(self):
        """return the video object associated with this song"""
        return self._video

    def ytid(self):
        """return the matched youtubeid"""
        if self._video:
            return self._video.ytid()
        else:
            return None

    def find_video(self):
        """find a youtube video for this song"""
        print('Searching youtube for: {}'.format(str(self)))
        search = YtRequest(self.searchterm())
        self._video = search.perform()
        if self._video:
            self._video.get_url()
            return True
        return None

class VrtRequest():
    """used to perform requests to the vrt api -- obsolete"""
    channel_codes = {'stubru': 41, 'radio1': 11, 'mnm': 55, 'mnmhits': 56}
    headers = {'accept': 'application/vnd.vrt.be.songlist_1.0+json'}

    def __init__(self, channel):
        self.code = self.channel_codes[channel]
        self.payload = {'channel_code': self.code}

    def perform(self):
        r = requests.get('http://services.vrt.be/playlist/items', params=self.payload, headers=self.headers)
        songs = Playlist()
       
        for item in r.json()['songlist']:
            songs.add(Song(item['artist'], item['title']))

        return songs


class VrtRequest_2():
    """used to perform requests to the vrt api"""
    _channel_codes = {'stubru': 41, 'radio1': 11, 'mnm': 55, 'mnmhits': 56}
    _headers = {'accept': 'application/vnd.playlist.vrt.be.playlist_items_1.0+json'}
    _url = 'http://services.vrt.be/playlist/items'
    _basic_payload = {'type': 'song', 'page_size': 20}

    def __init__(self, channel):
        self._code = self._channel_codes[channel]
        self._basic_payload['channel_code'] = self._code
        #self._next = ""
        self._lastcode = None

    def get_latest(self):
        """get the latest 20 tracks from the services.vrt.be
        and return a playlist"""
        self._payload = self._basic_payload
        self._payload['assending'] = 'false'
        r = requests.get(self._url, params=self._payload, headers=self._headers)
        json_data = r.json()
        songs = self.create_songlist(json_data)
        self._lastcode = songs.lastcode()
        return songs

    def get_next(self):
        """gets the 20 tracks that self._next are pointing to"""
        if not self._lastcode:
            return self.get_latest()
        self._payload['begin'] = self._lastcode
        r = requests.get(self._url, params = self._payload, headers=self._headers)
        json_data = r.json()
        self._next = json_data['next']['href']
        return self.create_songlist(json_data)

    def get_from_timestamp(self, timestamp):
        """get the songs played since timestamp"""
        self._payload = self._basic_payload
        self._payload['ascending'] = 'true'
        self._payload['from'] = timestamp
        r = requests.get(self._url, params=self._payload, headers=self._headers)
        json_data = r.json()
        songs = self.create_songlist(json_data)
        self._lastcode = songs.lastcode()
        return songs

    def create_songlist(self, json_data, append = True):
        """decode json data into a songlist"""
        songs = Playlist()
        for item in json_data['playlistItems']:
            code = item['code']
            for data in item['properties']:
                if data['key'] == 'ARTISTNAME':
                    artist = data['value']
                elif data['key'] == 'TITLE':
                    title = data['value']
            if append:
                songs.append(Song(artist, title, code))
            else:
                song.add(Song(artist, title, code))

        return songs
        

class YtVideo():
    """hold information about a youtube video"""
    def __init__(self, title, ytid):
        assert type(title) == str
        assert type(ytid) == str
        self._title = title
        self._ytid = ytid
        self._url = None
        self._stream = None

    def ytid(self):
        """returns the video id"""
        return self._ytid

    def title(self):
        return self._title

    def get_url(self):
        """get the streaming url"""
        vid = pafy.new(self._ytid)
        self._stream = vid.getbestaudio()
        self._url = self._stream.url
        return self._url

    def url(self):
        return self._url

    def download(self):
        if not self._stream:
            self.get_url()
        self._stream.download()

class YtRequest():
    """search for a song on youtube"""
    basic_payload = {'safeSearch': 'none', 'orderby': 'relevance',
            'max-results': 1, 'paid-content': 'false',
            'v': 2, 'start-index': 1, 'alt': 'jsonc',
            'category': 'Music'}
    headers =  {'User-Agent': "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0)"}
    url = "https://gdata.youtube.com/feeds/api/videos"
    song_title = None
    song_id = None

    def __init__(self, term):
        self.payload = self.basic_payload
        self.payload['q'] = term

    def perform(self):
        r = requests.get(self.url, params=self.payload, headers=self.headers)
        try:
            song = r.json()['data']['items'][0]
        except KeyError:
            print('no matches on youtube')
            return None
        else:
            song_title = song['title']
            song_id = song['id']
            video = YtVideo(song_title, song_id)
            return video

class Player():
    """A class for controlling mplayer"""
    _mplayer = None

    def __init__(self):
        pass

    def poll(self):
        if not self._mplayer:
            return False
        else:
            status = self._mplayer.poll()
            if status == None:
                return True
            else:
                self._mplayer = None
                return False

    def play(self, url):
        self._mplayer = subprocess.Popen(['mplayer', '-slave','-quiet', '-prefer-ipv4', url], shell=False,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=1)
        return

    def wait(self):
        if self._mplayer == None:
            return
        else:
            self._mplayer.wait()
            return

    def stop(self):
        pass
        ##self._mplayer()

class PlayLog():
    """A class to write playlists to files"""
    """logfile format: artist,title,ytid,plays"""
    def __init__(self, path):
        self._path = path
        try:    ## create the file if it doens't exist yet
            f = open(path, 'r')
        except FileNotFoundError:
            f = open(path, 'w')
            f.close()
        else:
            f.close()

    def add_play(self, song):
        if not self.in_file(song):
            self.append_song(song)
        else:
            self.up_plays(song)

    def up_plays(self, song):
        """add one the the playcount from a song"""
        fo = open(self._path, 'r', newline='')
        fh, temppath = tempfile.mkstemp()
        fn = open(temppath, 'w', newline='')
        reader = csv.reader(fo, 'unix')
        writer = csv.writer(fn, 'unix')
        for line in reader:
            artist, title, ytid, played = line
            if song.artist() != artist or song.title() != title:
                    writer.writerow(line)
            else:
                played = str(int(played) + 1)
                writer.writerow([artist, title, ytid, played])
        fo.close()
        fn.close()
        os.close(fh)
        os.remove(self._path)
        shutil.move(temppath, self._path)

    def append_song(self, song):
        f = open(self._path, 'a', newline='')
        writer = csv.writer(f, 'unix')
        ytid = song.ytid()
        if not ytid:
            ytid = ''
        writer.writerow([song.artist(), song.title(), ytid, '1'])
        f.close()

    def in_file(self, song):
        f = open(self._path, 'r', newline='')
        reader = csv.reader(f, 'unix')
        for line in reader:
            artist, title, played, ytid = line
            if song.artist() == artist:
                if song.title() == title:
                    f.close()
                    return True
        f.close()
        return False

class Timestamp():
    """A class to store timestamps"""
    def __init__(self):
        self._delta = datetime.datetime.utcnow()
        self._delta -= datetime.datetime.now()
        self._time = datetime.datetime.now()

    def ask(self):
        now = datetime.datetime.now()
        print('Please enter a date and time')
        print('Empty values will be filled with the current time')
        year = now.year
        month = input('Month (number): ')
        day = input('Day (number): ')
        hour = input('Hour (number, 24h): ')
        minute = input('Minute (number):' )
        try:
            month = int(month)
        except ValueError:
            month = now.month
        try:
            day = int(day)
        except ValueError:
            day = now.day
        try:
            hour = int(hour)
        except ValueError:
            hour = now.hour
        try:
            minute = int(minute)
        except ValueError:
            minute = now.minute
        try:
            self._time = datetime.datetime(year, month, day, hour, minute)
        except ValueError:
            print('Something was wrong with your data')
            return None
        else:
            return self._time

    def iso(self):
        return self.utc_time().isoformat()
    
    def utc_time(self):
        utc_time = self._time + self._delta
        utc_time = utc_time.replace(microsecond = 0)
        return utc_time

    def __str__(self):
        return self._time.isoformat()

if __name__ == "__main__":
    ## Parse the command line arugents
    parser = argparse.ArgumentParser(description='Listen to vrt playlists')
    
    parser.add_argument('station',
            help='The station to listen to',
            choices=['stubru', 'radio1', 'mnm', 'mnmhits'])
    parser.add_argument('-p', '--past', action='store_const',
            const=1, default=0, dest='history',
            help='Listen to the history of the playlist')
    args = parser.parse_args()

    history = args.history
    station = args.station
    timestamp = Timestamp()

    log = PlayLog('log2')           ## create a logfile
    radio = VrtRequest_2(station) ## set the station
    
    if history:
        if timestamp.ask() == None:
            history = 0
        else:
            songs = radio.get_from_timestamp(timestamp.iso()) ## get the track list
    if not history:
        songs = radio.get_latest()      ## get the track list
    song = songs.pop()
    song.find_video()
    video = song.video()
    if video:
        print("--> vrt song:", str(song))
        print("--> currently playing:", video.title())
        log.add_play(song)
        mplayer = Player()
        mplayer.play(video.url())
    while True:
        if not history:
            songs.merge(radio.get_latest())
        if len(songs) == 0:
            if not history:
                print('stack is empty, getting older tracks')
            temp = radio.get_next()
            songs.merge(radio.get_next(), append = 1)
        songs.find_videos()
        mplayer.wait()
        song = songs.pop()
        video = song.video()
        if not video: continue
        print("--> vrt song:", str(song))
        print("--> currently playing:", video.title())
        print("still {} songs on stack".format(len(songs)))
        log.add_play(song)
        mplayer.play(video.url())
