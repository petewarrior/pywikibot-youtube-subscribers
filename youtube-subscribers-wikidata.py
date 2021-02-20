import time
import pywikibot
import re
import datetime

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
                  'key': "youtube_api_key"}
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

    pages = []

    for p in pages:
        page = pywikibot.Page(wiki, p)
        item = pywikibot.ItemPage.fromPage(page)

        dictionary = item.get()

        if dictionary['claims']['P2397'] is None : continue
        claim = dictionary['claims']['P2397'][0]

        subscribers = claim.qualifiers['P3744'][0] if claim.qualifiers['P3744'] else None
        views = claim.qualifiers['P5436'][0] if claim.qualifiers['P5436'] else None
        pit = claim.qualifiers['P585'][0] if claim.qualifiers['P585'] else None
        channel = claim.target

        channels = [{'channel_url': channel}]

        stats = get_statistics(channels=channels)
        
        for s in stats:

          viewsInt = s["statistics"]["viewCount"]
          subscribersInt = s["statistics"]["subscriberCount"]
          
          subsCount = pywikibot.WbQuantity(amount='+'+subscribersInt, site=repo)
          newSubscribers = pywikibot.Claim(repo, u'P3744') # number of subscribers
          newSubscribers.setTarget(subsCount)
          viewCount = pywikibot.WbQuantity(amount='+'+viewsInt, site=repo)
          newViews = pywikibot.Claim(repo, u'P5436') # number of subscribers
          newViews.setTarget(viewCount)
          currTime = datetime.datetime.now()
          piTime = pywikibot.WbTime(int(currTime.strftime('%Y')), int(currTime.strftime('%m')), int(currTime.strftime('%d')))
          newPit = pywikibot.Claim(repo, u'P585') # number of subscribers
          newPit.setTarget(piTime)
          

          claim.removeQualifiers([subscribers, views, pit])
          claim.addQualifier(newSubscribers, summary=u'Update subscriber count')
          claim.addQualifier(newViews, summary=u'Update view count')
          claim.addQualifier(newPit, summary=u'update point in time')

if __name__ == "__main__":
    main()
