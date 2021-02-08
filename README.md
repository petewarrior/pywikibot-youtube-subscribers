# pywikibot-youtube-subscribers
A simple script to update YouTube channel stats in a Wikipedia page. 

Basically, this script does three things:
1. Parse a [YouTube personality infobox](https://en.wikipedia.org/wiki/Template:Infobox_YouTube_personality) on a Wikipedia page to obtain the channel ID 
2. Query the statistics for the channel ID to the YouTube API 
3. Update the stats in the infobox

Requires [Pywikibot](https://www.mediawiki.org/wiki/Manual:Pywikibot), Python 3, and a [YouTube API key](https://developers.google.com/youtube/v3/getting-started).

## Page requirements
* The page must have a Wikipedia personality infobox, either on its own or as a module in another infobox.
* The YouTube channel must be stored in the ```channel_id``` field. Custom URL is not yet supported and neither is multiple channels in one infobox.
* Last update time is printed in the ```stats_update``` field. It must already exist and have a date formatted using the [Wikipedia date template](https://en.wikipedia.org/wiki/Template:Date).
