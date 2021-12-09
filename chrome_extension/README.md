## Chrome extension installation instructions

Installing the chrome extension on your browser is fairly straigh forward, below is a link that will cover the process in detail:
`https://developer.chrome.com/docs/extensions/mv3/getstarted/`

The basic steps are as follows:
1. Open the Extension Management page by navigating to chrome://extensions.
    Alternatively, open this page by clicking on the Extensions menu button and selecting Manage Extensions at the bottom of the menu.
    Alternatively, open this page by clicking on the Chrome menu, hovering over More Tools then selecting Extensions

2. Enable Developer Mode by clicking the toggle switch next to Developer mode.

3. Click the Load unpacked button and select the extension directory.


### Usage

The extension works off of IMDb, so you must navigate to their website and search for a movie. Once on a movie page, the extension
will pull the `tconst` identifier from the URL and search our database for the movie. More about this is covered in the server and
database READMEs.

After the movie is found, the extension will then request 20 of the most similar movies. These will be then displayed on cards with
their picture, title, and rating. The user can then click on any title to be taken to the movie's IMDb page if desired.


### Notes

The `baseurl` const in popup.js gives the user the option to swap between making local requests or requests to an external server.
The local option requires the user to be running the server, while the remote option will work from anywhere without need for a local
server instance.
