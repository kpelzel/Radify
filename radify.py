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
import os


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
        SPOTIFY_CLIENT_ID = (config["spotify_info"]["spotify_client_id"])
        SPOTIFY_CLIENT_SECRET = (config["spotify_info"]["spotify_client_secret"])
        SPOTIFY_REDIRECT_URI = (config["spotify_info"]["spotify_redirect_uri"])


        os.environ['SPOTIPY_CLIENT_ID'] = SPOTIFY_CLIENT_ID
        os.environ['SPOTIPY_CLIENT_SECRET'] = SPOTIFY_CLIENT_SECRET
        os.environ['SPOTIPY_REDIRECT_URI'] = SPOTIFY_REDIRECT_URI

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
        searchResults = sp.search(q=track_name, limit=10, type='track')

        # Track objects format:
        #   Track object:
        #       index 0 = track id
        #       index 1 = track name
        #       index 2 = list of artists names
        track_objects = []
        final_track_ids = []
        items = (searchResults["tracks"]["items"])
        for item in items:
            track = []
            track.append(item["id"])
            track.append(item["name"])
            artists = (item["artists"])
            artists_list = []
            for artist in artists:
                artists_list.append(artist["name"])
            track.append(artists_list)
            
            track_objects.append(track)
        

        for track in track_objects:
            for spotify_artist in track[2]:
                for website_artist in track_artists:
                    spotify_artist_compare = "".join(spotify_artist.split()).upper().replace("'","")
                    website_artist_compare = "".join(website_artist.split()).upper().replace("'","")
                    results = similar(spotify_artist_compare, website_artist_compare)
                    print("{:.2f} = {} vs {}".format(results, spotify_artist_compare, website_artist_compare))
                    if results >= 0.8:
                        # add the track id to final_track_ids
                        final_track_ids.append(track[0])

        print()
            
        # Return the first element in final_track_ids because that's probably the correct track
        return final_track_ids[0]

    else:
        print("Can't get token for", USER_ID)

# Used to compare names
def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()

if __name__== "__main__":
  main()