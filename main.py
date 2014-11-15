import requests
import pafy
import subprocess
import time

class Playlist():
    """Store lists of songs """
    def __init__(self):
        self.songs = []

    def add(self, song):
        self.songs.append(song)

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
        for song in self.songs:
            if song == song2:
                return True
        return False

    def merge(self, other, silent = 1):
        for song in other.songs:
            if not self.in_list(song):
                self.add(song)
                if not silent:
                    print("new song:",song)

    def find_videos(self):
        for song in self.songs:
            if song.video() == None:
                song.find_video()
                

class Song():
    """Store the data for a song"""
    def __init__(self, artist, title):
        assert type(artist) == str
        assert type(title) == str
        self._artist = artist.strip()
        self._title = title.strip()
        self._video = None

    def __eq__(self, other):
        if self._title == other._title:
            if self._artist == other._artist:
                return True
        return False

    def searchterm(self):
        return(self._artist + ' - ' + self._title)

    def artist():
        return self._artist

    def title():
        return self._title

    def __str__(self):
        return ("{} - {}".format(self._artist, self._title))

    def url(self):
        if self._video == None:
            return None
        return self._video.url()

    def video(self):
        return self._video

    def find_video(self):
        print('Looking for a video for: {}'.format(str(self)))
        search = YtRequest(self.searchterm())
        self._video = search.perform()
        self._video.get_url()

class VrtRequest():
    """used to perform requests to the vtm api"""
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
        return self._ytid

    def title(self):
        return self._title

    def get_url(self):
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

if __name__ == "__main__":
    radio = VrtRequest('radio1') ## set the station
    songs = radio.perform()      ## get the track list
    song = songs.pop()
    song.find_video()
    video = song.video()
    print("--> vrt song:", str(song))
    print("--> currently playing:", video.title())
    mplayer = Player()
    mplayer.play(video.url())
    while True:
        while True:
            songs.merge(radio.perform())
            songs.find_videos()
            if len(songs) == 0:
                time.sleep(10)
            else:
                break
        mplayer.wait()
        song = songs.pop()
        video = song.video()
        print("--> vrt song:", str(song))
        print("--> currently playing:", video.title())
        mplayer.play(video.url())


"""
    songs.find_videos()
    song = songs.first()
    video = song.video()
    print("--> vrt song:", str(song))
    print("--> currently playing:", video.title())
    mplayer = Player()
    mplayer.play(video.url())
    mplayer.wait()
    songs.merge(radio.perform())
    songs.print()
"""
#songs.print()
#print(songs)
