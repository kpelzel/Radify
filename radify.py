#!/usr/local/bin/python3.6

from selenium import webdriver
import spotipy
import re
import subprocess
import time as t
from datetime import datetime, timedelta, time
from website_class import Website
from spotify_operations import generate_token, removeTrackSpotify, addTrackSpotify
import yaml
from difflib import SequenceMatcher


website_objects = []
CHROME_DRIVER_LOCATION = ""
USER_ID = ""
normal_sleep_time = 20
error_sleep_time = 40
silence_start = "00:00"
silence_stop = "06:00"


def main():

    # Parse yml file and create website objects
    with open("config.yml", 'r') as stream:
        config = yaml.load(stream)

        USER_ID = (config["spotify_info"]["user_id"])
        CHROME_DRIVER_LOCATION = (config["spotify_info"]["chrome_driver_location"])

        normal_sleep_time = (config["general_settings"]["normal_sleep_time"])
        error_sleep_time = (config["general_settings"]["error_sleep_time"])
        silence_start = (config["general_settings"]["silence_start"])
        silence_stop = (config["general_settings"]["silence_stop"])

        for name, values in config["websites"].items():
            myWebsite = Website(
                name, 
                values["url"], 
                values["track_element_class_name"], 
                values["artist_element_class_name"], 
                values["track_artist_same_element"]["list_separation"],
                values["track_artist_same_element"]["track_element_value"], 
                values["track_artist_same_element"]["artist_element_value"], 
                values["artist_element_list_separation"],
                values["playlist_id"],
                values["max_song_count"])
            myWebsite.populatePlaylist(USER_ID)
            website_objects.append(myWebsite)


    # Print playlists for all websites
    for website in website_objects:
        print(website)
    print()

    # Begin loop for main program
    while(True):
        sleep_time = 0

        # Check if it's between midnight and 6:00 am
        # If it is, sleep until 6:00 am
        now = datetime.now()
        now_time = now.time()
        silence_start_array = re.split(':', silence_start)
        silence_stop_array = re.split(':', silence_stop)
        if now_time >= time(int(silence_start_array[0]),int(silence_start_array[1])) and now_time <= time(int(silence_stop_array[0]),int(silence_stop_array[1])):
            extended_sleep_time = (timedelta(hours=24) - (now - now.replace(hour=int(silence_stop_array[0]), minute=int(silence_stop_array[1])+1, second=0, microsecond=0))).total_seconds() % (24 * 3600)
            print("\nIt's late at night. Sleeping for {} seconds. Be back at {}!\n".format(extended_sleep_time, silence_stop))
            t.sleep(extended_sleep_time)

        # Check if any playlist is over 30 tracks
        # If it is, remove the last one and continue
        # If it isn't, parse website to see if there's a new track
        for website in website_objects:
            if len(website.playlist) > website.max_song_count:
                print("{} playlist has over 30 songs. Removing {} by {}".format(website.name, website.playlist[0][0], website.playlist[0][1]))
                if removeTrackSpotify(website.playlist[0][2], website.playlist_id, USER_ID):
                    website.removeTrack(website.playlist[0][2])
                else:
                    print("Error: Error occurred when removing track from spotify")
            else:
                print("Parsing {} to find the current song".format(website.name))
                parseinfo = website.parse(CHROME_DRIVER_LOCATION)

                if parseinfo[0] == "":
                    print("Parse failed for {}. Skipping for now...".format(website.name))
                else:
                    print("Found Track: {}\nArtists: {}".format(parseinfo[0],parseinfo[1]))
                    # Try to find if track is already in the playlist
                    trackFound = False
                    for track in website.playlist:
                        first = "".join(parseinfo[0].split()).upper().replace("'","").replace("\"","")
                        second = "".join(track[0].split()).upper().replace("'","").replace("\"","")
                        results = similar(first, second)
                        print("{:.2f} = {} vs {}".format(results, first, second))
                        # If the track name is more than an 90% match then we'll say that's a match
                        if results >= 0.9:
                            trackFound = True

                    if trackFound == False:
                        print("\n{} is not already in {} playlist. Adding now...".format(parseinfo[0], website.name))
                        try:
                            track_id = getTrackIdFromSpotify(parseinfo[0], parseinfo[1])
                        except Exception as exc:
                            print("Error: Error from getTrackIdFromSpotify(): [{}]".format(exc))
                            track_id = 0
                        if track_id != 0:
                            # Double check to make sure track isn't already in playlist by checking the track_id
                            for track in website.playlist:
                                if track_id == track[2]:
                                    print("Track is actually already in playlist")
                                    trackFound = True
                            if trackFound == False:
                                result = addTrackSpotify(track_id, website.playlist_id, USER_ID)
                                if result:
                                    website.addTrack(parseinfo[0], parseinfo[1], track_id)
                                    print("Successfully added {} by {} to {} playlist\n".format(website.playlist[len(website.playlist)-1][0], website.playlist[len(website.playlist)-1][1], website.name))
                                else:
                                    print("Error: problem occured adding {} to spotify {} playlist\n".format(parseinfo[0], website.name))
                                    sleep_time = error_sleep_time
                            else:
                                print("Song is already in {} playlist.\n".format(website.name))
                                sleep_time = normal_sleep_time
                    else:
                        print("Song is already in {} playlist.\n".format(website.name))
                        sleep_time = normal_sleep_time
            
        print("Sleeping for {} seconds...\n\n".format(sleep_time))
        t.sleep(sleep_time)


def getTrackIdFromSpotify(track_name, track_artists):
    token = generate_token(USER_ID)
    if token:
        sp = spotipy.Spotify(auth=token)
        searchResults = str(sp.search(q=track_name, limit=10, type='track'))
        matchList = re.findall(r"'id':(.*?),.*?'name':(.*?),.*?'type':(.*?),", searchResults)

        # Parse through the search results from spotify
        Groups = []
        for match in matchList:
            if match[2].strip() == "'artist'":
                match_artist = match[1].strip().replace("'","")
            elif match[2].strip() == "'track'":
                match_id = match[0].strip().replace("'","")
                match_track = match[1].strip().replace("'","")
                group = match_track, match_artist, match_id
                Groups.append(group)
                match_artist = ""
                match_track = ""
                match_id = ""

        finalGroups = []
        artist_number = 0
        while not finalGroups:
            if artist_number > len(track_artists) - 1:
                print("Could not find track on spotify. Not adding to playlist...")
                return 0
            for group in Groups:
                # Comparing the website known artists with the spotify found artists
                first = "".join(group[1].split()).upper().replace("'","")
                second = "".join(track_artists[artist_number].split()).upper().replace("'","")
                results = similar(first, second)
                print("{:.2f} = {} vs {}".format(results, first, second))

                # If the artist is more than an 80% match then we'll say that's a match
                if results >= 0.8:
                    finalGroups.append(group)

            print()
            artist_number = artist_number + 1
            
        # Return the first element in finalGroups because that's probably the correct track
        return finalGroups[0][2]

    else:
        print("Can't get token for", USER_ID)

# Used to compare names
def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()

if __name__== "__main__":
  main()