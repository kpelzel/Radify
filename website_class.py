from spotify_operations import generate_token
import spotipy
from selenium import webdriver
import re

class Website:
    def __init__(
        self, name, url, track_element, artist_element, list_separation, 
        track_value, artist_value, artist_separation, playlist_id, song_count):
        self.name = name
        self.url = url
        self.track_element_class_name = track_element
        self.artist_element_class_name = artist_element

        if self.track_element_class_name == self.artist_element_class_name:
            self.track_artist_same_element = True
        else:
            self.track_artist_same_element = False

        self.list_separation = list_separation
        self.track_list_element_value = track_value
        self.artist_list_element_value = artist_value
        self.artist_element_list_separation = artist_separation
        self.playlist_id = playlist_id
        self.max_song_count = song_count
        self.playlist = []

    def __str__(self):
        return_string = "\n+{:-<75}+\n|{: <75}|\n+{:-<75}+".format("", self.name, "")
        for track in self.playlist:
            return_string = "{}\n{}".format(return_string, track)
        return return_string

    def populatePlaylist(self, user_id):
        print("Populating {} playlist from Spotify".format(self.name))
        match_artist = ""
        match_track = ""
        match_id = ""

        token = generate_token(user_id)

        if token:

            sp = spotipy.Spotify(auth=token)
            results = sp.user_playlist(user_id, playlist_id=self.playlist_id, fields='tracks')
            stringResults = str(results)
            matchList = re.findall(r"'id':(.*?),.*?'name':(.*?),.*?'type':(.*?),", stringResults)

            for match in matchList:
                if match[2].strip() == "'artist'":
                    match_artist = match[1].strip().replace("'","")
                elif match[2].strip() == "'track'":
                    match_id = match[0].strip().replace("'","")
                    match_track = match[1].strip().replace("'","")
                    group = match_track, match_artist, match_id
                    self.playlist.append(group)
                    match_artist = ""
                    match_track = ""
                    match_id = ""
        else:
            print("Can't get token for", user_id)

    def removeTrack(self, track_id):
        for track in self.playlist:
            if track[2] == track_id:
                self.playlist.remove(track)

    def addTrack(self,track_name, track_artists, track_id):
        group = track_name, track_artists, track_id
        self.playlist.append(group)


    def parse(self, chrome_driver_location):
        try:
            browser = webdriver.Chrome(chrome_driver_location) #replace with .Firefox(), or with the browser of your choice
            browser.get(self.url) #navigate to the page
            trackElement = browser.find_elements_by_class_name(self.track_element_class_name)
        except Exception as exc:
            print("Error: Selenium/Chrome error: [{}]".format(exc))
            track = ""
            artists = []
            browser.quit()
            return track, artists

        if self.track_artist_same_element:
            bothElement = trackElement
            if bothElement:
                info = bothElement[0].text.split(self.list_separation)
                track = info[self.track_list_element_value].strip()
                artists = info[self.artist_list_element_value].strip().split(self.artist_element_list_separation)
            else:
                track = ""
                artists = []

        else:
            if trackElement:
                track = trackElement[0].text.strip()

                artistElement = browser.find_elements_by_class_name(self.artist_element_class_name)
                if artistElement:
                    artists = artistElement[0].text.strip().split(self.artist_element_list_separation)
            else:
                track = ""
                artists = []

        # Looks for a parathesis in track name with (feat., ft., or with) and moves that artist to the artists list
        matchList = re.findall(r"((?:(.*)\((?:ft\.|feat\.|with|f\.|feat|ft)(.*)\)|(.*)(?:ft\.|feat\.|with|f\.|feat|ft)(.*)|.+))", track)
        # If match contains parathesis with another artist, move that artist
        if matchList:
            if len(matchList[0]) > 1:
                if matchList[0][1]:
                    artists.append(matchList[0][2].strip())
                    track = matchList[0][1].strip()
                if len(matchList[0]) > 3:
                    if matchList[0][3]:
                        artists.append(matchList[0][4].strip())
                        track = matchList[0][3].strip()
            else:
                track = matchList[0][0].strip()


        for artist in artists:
            # Looks for (feat., ft., or with) in each artist and separates that artist to the artists list
            matchList = re.findall(r"((?:(.*)\((?:ft\.|feat\.|with|f\.|feat|ft)(.*)\)|(.*)(?:ft\.|feat\.|with|f\.|feat|ft)(.*)|(.*)&(.*)|.+))", artist)
            if matchList:
                # If match contains another artist, delete current entry and add separated artists
                # Checking for feat/ft/with/etc with parethesis
                if len(matchList[0]) > 1: 
                    if matchList[0][1]:
                        artists.append(matchList)
                        artists.append(matchList[0][2].strip())
                        artists.remove(artist)
                    # Checking for feat/ft/with/etc without parethesis
                    if len(matchList[0]) > 3:
                        if matchList[0][3]:
                            artists.append(matchList[0][3].strip())
                            artists.append(matchList[0][4].strip())
                            artists.remove(artist)
                        # Checking for '&'
                        if len(matchList[0]) > 5:
                            if matchList[0][5]:
                                artists.append(matchList[0][5].strip())
                                artists.append(matchList[0][6].strip())
                                artists.remove(artist)



        browser.quit()
        return track, artists





