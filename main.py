import requests
import pafy
import subprocess
import time

class Playlist():
    """Store lists of songs """
    def __init__(self):
        self.songs = []
        # used to store vrt_codes, to keep
        # track of what has been played
        self._history = set()

    def add(self, song):
        self.songs.insert(0, song)
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

    def merge(self, other, silent = 1):
        """merge self with other"""
        for song in other.songs:
            if not self.in_history(song):
                self.add(song)
                if not silent:
                    print("new song:",song)

    def find_videos(self):
        """match every song with a youtube video"""
        for song in self.songs:
            if song.video() == None:
                song.find_video()
                

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

    def find_video(self):
        """find a youtube video for this song"""
        print('Searching youtube for: {}'.format(str(self)))
        search = YtRequest(self.searchterm())
        self._video = search.perform()
        self._video.get_url()

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
    channel_codes = {'stubru': 41, 'radio1': 11, 'mnm': 55, 'mnmhits': 56}
    headers = {'accept': 'application/vnd.playlist.vrt.be.playlist_items_1.0+json'}

    def __init__(self, channel):
        self.code = self.channel_codes[channel]
        self.payload = {'channel_code': self.code}

    def perform(self):
        """get the latest 20 tracks from the services.vrt.be
        and return a playlist"""
        r = requests.get('http://services.vrt.be/playlist/items', params=self.payload, headers=self.headers)
        songs = Playlist()
       
        for item in r.json()['playlistItems']:
            code = item['code']
            for data in item['properties']:
                if data['key'] == 'ARTISTNAME':
                    artist = data['value']
                elif data['key'] == 'TITLE':
                    title = data['value']
            songs.add(Song(artist, title, code))

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

class Logfile():
    """A class to write playlists to files"""
    """logfile format: artist,title,plays"""
    def __init__(self, path):
        self._path = path
        try:
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
        fo = open(path, 'r')
        fn = open(path+'.new', 'w')
        for line in fo:
            artist, title, played = line.strip().split(',')
            if song.artist() != artist or song.title() != title:
                    fn.write(line)
            else:
                played = str(int(played) + 1)
                fn.write(artist+','+title+','+played+'\n')


    def append_song(self, song):
        f = open(self.path, 'a')
        f.write(song.artist()+","+song.title())
        f.write(",1\n")

    def in_file(self, song):
        f = open(path, 'r')
        for line in f:
            if len(line) < 3:
                continue
            line = line.strip()
            artist, title, played = line.split(',')
            if song.artist() == artist:
                if song.title() == title:
                    return True
        return False





if __name__ == "__main__":
    radio = VrtRequest_2('radio1') ## set the station
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
