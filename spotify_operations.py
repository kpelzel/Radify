import spotipy
import spotipy.util as util
import spotipy.oauth2 as oauth2

def generate_token(user_id):

    scope = 'playlist-modify-public'
    token = util.prompt_for_user_token(user_id, scope)

    return token

def removeTrackSpotify(track_id, playlist_id, user_id):
    trackIdList = [track_id]
    token = generate_token(user_id)

    if token:
        sp = spotipy.Spotify(auth=token)
        try:
            sp.user_playlist_remove_all_occurrences_of_tracks(user_id, playlist_id, trackIdList, snapshot_id=None)
            print("Track was successfully removed from spotify")
            return True
        except:
            print("Error: Track failed to be removed from spotify")
            return False

    else:
        print("Can't get token for", user_id)
        return False

def addTrackSpotify(track_id, playlist_id, user_id):
    trackIdList = [track_id]
    token = generate_token(user_id)

    if token:
        sp = spotipy.Spotify(auth=token)
        sp.trace = False
        try:
            sp.user_playlist_add_tracks(user_id, playlist_id, trackIdList)
            print("Track was successfully addded to spotify")
            return True
        except:
            print("Error: Track failed to be added to spotify")
            return False

    else:
        print("Can't get token for", user_id)
        return False

