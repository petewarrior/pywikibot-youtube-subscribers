# pywikibot-youtube-subscribers
A simple script to update YouTube channel stats in a Wikipedia page. 

Basically, this script does three things:
1. Parse a [YouTube personality infobox](https://en.wikipedia.org/wiki/Template:Infobox_YouTube_personality) on a Wikipedia page to obtain the channel ID 
2. Query the statistics for the channel ID to the YouTube API 
3. Update the stats in the infobox

Requires [Pywikibot](https://www.mediawiki.org/wiki/Manual:Pywikibot), Python 3, and a [YouTube API key](https://developers.google.com/youtube/v3/getting-started).

## Page requirements
* The page must have a Wikipedia YouTube personality infobox, either on its own or as a module in another infobox.
* The script can only parse YouTube channel ID in the ```channel_url``` field. If the infobox uses ```channel_direct_url```, both ```channel_id``` and ```channel_direct_url``` must be provided in the script (example in source code). Only one channel per infobox is supported.
* Last update time is printed in the ```stats_update``` field. It must already exist and have a date formatted using the [Wikipedia date template](https://en.wikipedia.org/wiki/Template:Date) with the ```YYYY-MM-DD``` format.

Replace the `subscribers`, `views`, and `stats_update` fields in the Youtube personality infobox as follows:
```
| subscribers = {{#invoke:WikidataIB|getValue|P2397|qo=yes|qual=P3744|list=ubl|fetchwikidata=ALL|onlysourced=no|scale=a|noicon=yes}}
| views = {{#invoke:WikidataIB|getValue|P2397|qo=yes|qual=P5436|list=ubl|fetchwikidata=ALL|onlysourced=no|scale=a|noicon=yes}}
| stats_update = {{#invoke:WikidataIB|getValue|P2397|qo=yes|qual=P585|maxvals=1|list=ubl|fetchwikidata=ALL|onlysourced=no|noicon=no}}
```