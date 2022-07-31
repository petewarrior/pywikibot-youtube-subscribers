import time
import pywikibot
import re
import datetime
import os

from dotenv import load_dotenv

import requests

def append_statistics(stats):
    def f(c):
        s = next((i for i in stats if i["id"] == c["channel_url"]), None)
        if s is not None:
            c['statistics'] = s['statistics']
        return c
    return f


def get_statistics(channels=list):
    ids = list(map(lambda c: c["channel_url"], channels))
    idlist = ','.join(ids)

    res = []

    if len(ids) > 0:
        params = {'part': 'statistics,status', 'id': idlist,
                  'key': os.environ.get("YOUTUBE_API_KEY")}
        r = requests.get(
            "https://youtube.googleapis.com/youtube/v3/channels", params)

        response = r.json()
        res = res + response["items"]

        app = append_statistics(res)

        return map(app, channels)

    return []


def main():
    wiki = pywikibot.Site("en", "wikipedia")
    site = pywikibot.Site("wikidata", "wikidata")
    repo = site.data_repository()

    load_dotenv()

    pages = os.environ.get('WIKIDATA_IDS', '').split(',')

    for p in pages:
        item = pywikibot.ItemPage(site, p)

        dictionary = item.get()

        if dictionary['claims']['P2397'] is None : continue        

        for c in range(len(dictionary['claims']['P2397'])):
            claim = dictionary['claims']['P2397'][c]

            subscribers = claim.qualifiers['P3744'][0] if 'P3744' in claim.qualifiers else None
            views = claim.qualifiers['P5436'][0] if 'P5436' in claim.qualifiers else None
            pit = claim.qualifiers['P585'][0] if 'P585' in claim.qualifiers else None
            videos = claim.qualifiers['P3740'][0] if 'P3740' in claim.qualifiers else None
            channel = claim.target

            channels = [{'channel_url': channel}]

            stats = get_statistics(channels=channels)
            
            for s in stats:

                viewsInt = s["statistics"]["viewCount"]
                subscribersInt = s["statistics"]["subscriberCount"]
                videosInt = s["statistics"]["videoCount"]
                
                subsCount = pywikibot.WbQuantity(amount='+'+subscribersInt, site=repo)
                newSubscribers = pywikibot.Claim(repo, u'P3744') # number of subscribers
                newSubscribers.setTarget(subsCount)
                viewCount = pywikibot.WbQuantity(amount='+'+viewsInt, site=repo)
                newViews = pywikibot.Claim(repo, u'P5436') # number of views
                newViews.setTarget(viewCount)
                videoCount = pywikibot.WbQuantity(amount='+'+videosInt, site=repo)
                newVideos = pywikibot.Claim(repo, u'P3740') # number of videos
                newVideos.setTarget(videoCount)
                currTime = datetime.datetime.now()
                piTime = pywikibot.WbTime(int(currTime.strftime('%Y')), int(currTime.strftime('%m')), int(currTime.strftime('%d')))
                newPit = pywikibot.Claim(repo, u'P585') # point in time
                newPit.setTarget(piTime)
            
            if subscribers: claim.removeQualifier(subscribers)
            if views: claim.removeQualifier(views)
            if pit: claim.removeQualifier(pit)
            if videos: claim.removeQualifier(videos)
            claim.addQualifier(newSubscribers, summary=u'Update subscriber count')
            claim.addQualifier(newViews, summary=u'Update view count')
            claim.addQualifier(newVideos, summary=u'update videos count')
            claim.addQualifier(newPit, summary=u'update point in time')

if __name__ == "__main__":
    main()
