# pywikibot-youtube-subscribers
A simple script to update YouTube channel stats in a Wikidata page. Inspired by Borkbot. 

Basically, this script does three things:
1. Get all YouTube channel ID (P2397) values in a Wikidata page
2. Query the statistics for each channel ID to the YouTube API 
3. Update the stats in Wikidata

Requires [Pywikibot](https://www.mediawiki.org/wiki/Manual:Pywikibot), Python 3, and a [YouTube API key](https://developers.google.com/youtube/v3/getting-started).

## Displaying stats on Wikipedia page
Replace the `subscribers`, `views`, and `stats_update` fields in the Youtube personality infobox as follows. If there are more than one channel, the stats will be displayed as a list.
```
| subscribers = {{#invoke:WikidataIB|getValue|P2397|qo=yes|qual=P3744|list=ubl|fetchwikidata=ALL|onlysourced=no|scale=a|noicon=yes}}
| views = {{#invoke:WikidataIB|getValue|P2397|qo=yes|qual=P5436|list=ubl|fetchwikidata=ALL|onlysourced=no|scale=a|noicon=yes}}
| stats_update = {{#invoke:WikidataIB|getValue|P2397|qo=yes|qual=P585|maxvals=1|list=ubl|fetchwikidata=ALL|onlysourced=no|noicon=no}}
```