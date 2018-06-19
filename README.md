Radify
=======

Radify parses live radio websites and adds the current playing song to your spotify playlist.


Dependencies
------------
- [Python 3](https://www.python.org/downloads/) 
- Selenium (Install using pip)
- spotipy (Install using pip)
- pyyaml (Install using pip)


Installation & Setup
--------------------
Once all dependencies are installed you can clone the repo and go through this setup process:

1. Clone the repo: 
 
		git clone https://github.com/kpelzel0522/Radify.git

2. Add the following lines to your ~/.bashrc. To get these items you'll need to create a spotify for developers account (developer.spotify.com) and click "create an app". This will give you a client ID and a client secret. You'll also need to set a redirect URI (I set mine to the url of one of my playlists).

		export SPOTIPY_CLIENT_ID='your-spotify-client-id'  
    	export SPOTIPY_CLIENT_SECRET='your-spotify-client-secret'  
    	export SPOTIPY_REDIRECT_URI='your-app-redirect-url'  

3. Download the chrome (or whatever browser) driver. This application is needed to pull up and control the web browser. You can find the chrome browser here: http://chromedriver.chromium.org/. I am running my server on a raspberry pi 3 so I was required to use chromium. If you want to do this, skip down to the chromium instructions below.

1. Setup the config.yml file wth the required variables. Your user and playlist ID can be found in the spotify url if you go to one of your playlists on the web player. Next you'll have to input the nessesary information to parse the website you want. Using Chromes inspect feature will help you find the element class name.

5. The first time you run radify you'll get a prompt from spotipy. It should have opened a chrome browser in which you'll need to grant radify access to your spotify account. Then it will forward you to a webpage. Copy the url and paste it into the terminal running radify where spotipy is prompting for input.

6. Enjoy!


Chromium with Raspberry Pi Instuctions
---------------
1.  Install chromium. you'll have to look up how to do this if you don't know how.
2.  Go to [this website](https://launchpad.net/ubuntu/trusty/+package/chromium-chromedriver) and click on the latest release for armhf.
3.  On the next page download the .deb file that can be found on the right side of the page.
4.  Now you can double click the .deb file in raspbian and install it using the regular package installer.
5.  The chromedriver will be located in /usr/lib/chromium-browser/chromedriver so make sure you point there in the config.yml file.
