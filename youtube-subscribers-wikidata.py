import pywikibot
import datetime
import os
from unicodedata import normalize
from dateutil.parser import parse

from dotenv import load_dotenv

import requests

def append_data(stats, key=['statistics']):
    def f(c):
        s = next((i for i in stats if i["id"] == c["channel_url"]), None)
        if s is not None:
            for k in key :
                c[k] = s[k]
        return c
    return f


def get_statistics(channels=list):
    ids = list(map(lambda c: c["channel_url"], channels))
    idlist = ','.join(ids)

    res = []

    if len(ids) > 0:
        params = {'part': 'snippet,statistics', 'id': idlist,
                  'key': os.environ.get("YOUTUBE_API_KEY")}
        r = requests.get(
            "https://youtube.googleapis.com/youtube/v3/channels", params)

        response = r.json()
        res = res + response["items"]

        app = append_data(res, ['snippet','statistics'])

        return map(app, channels)

    return []

def get_playlist_statistics(playlists=list) :
    ids = list(map(lambda c: c["channel_url"], playlists))
    idlist = ','.join(ids)

    if len(ids) > 0:
        params = {'part': 'snippet,contentDetails,status', 'id': idlist,
                  'key': os.environ.get("YOUTUBE_API_KEY")}
        r = requests.get(
            "https://youtube.googleapis.com/youtube/v3/playlists", params)

        response = r.json()
        res = res + response["items"]

        app = append_data(res, ['snippet','statistics'])

        return map(app, playlists)

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

        if 'P2397' not in dictionary['claims'] : continue        
        print(dictionary['labels']['en'])
        
        for c in range(len(dictionary['claims']['P2397'])):
            claim = dictionary['claims']['P2397'][c]
            channel_id = claim.getTarget()
            current_channel_name = claim.qualifiers['P1810'][0] if u'P1810' in claim.qualifiers else None
            
            if current_channel_name :
                print(current_channel_name.getTarget())
            else :
                print(channel_id + u' (will populate channel name)')
            if claim.getRank() == 'deprecated' :
                print('Skipping deprecated entry')
                continue
            
            start_date = claim.qualifiers['P580'][0] if 'P580' in claim.qualifiers else None
            subscribers = claim.qualifiers['P3744'][0] if 'P3744' in claim.qualifiers else None
            views = claim.qualifiers['P5436'][0] if 'P5436' in claim.qualifiers else None
            pit = claim.qualifiers['P585'][0] if 'P585' in claim.qualifiers else None
            videos = claim.qualifiers['P3740'][0] if 'P3740' in claim.qualifiers else None
            channel = claim.target

            channels = [{'channel_url': channel}]

            stats = get_statistics(channels=channels)

            for s in stats: # always one for now
                viewsInt = s["statistics"]["viewCount"]
                subscribersInt = s["statistics"]["subscriberCount"]
                videosInt = s["statistics"]["videoCount"]
                channelNameString = s["snippet"]["title"]
                publishedAt = parse(s["snippet"]["publishedAt"])
                
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

            if pit :
                if pit.getTarget().toTimestr() == piTime.toTimestr() :
                    print('Last updated today, skipping')
                    continue
            
            if subscribers :
                if(int(subscribersInt) < 100000) :
                    if abs(int(subscribers.getTarget().amount) - int(subscribersInt)) < 1000 :
                        print('Subscriber change <1000, skipping')
                        continue
                elif(int(subscribersInt) < 1000000) :
                    if abs(int(subscribers.getTarget().amount) - int(subscribersInt)) < 5000 :
                        print('Silver, subscriber change <5000, skipping')
                        continue
                else :
                    if abs(float(subscribers.getTarget().amount) - float(subscribersInt)) / float(subscribers.getTarget().amount) < 0.01 :
                        print('Gold or higher, subscriber change <1%, skipping')
                        continue

            try :
                if current_channel_name is not None :
                    if channelNameString.strip() != current_channel_name.getTarget().strip() :
                        print('Removing old channel name')
                        claim.removeQualifier(current_channel_name, summary=u'Remove old channel name')
                        current_channel_name = None
            except BaseException as err :
                print(err)

            try :
                if current_channel_name is None :
                    print('Adding channel name: "' + channelNameString + '"')
                    newChannelName = pywikibot.Claim(repo, u'P1810')
                    newChannelName.setTarget(channelNameString.strip())
                    claim.addQualifier(newChannelName, summary=u'Set channel name')
            except BaseException as err :
                print('Adding channel name error, skipped')
                print(err)
                
            if start_date is None :
                print('Adding start date')
                start_date_datetime = pywikibot.WbTime(int(publishedAt.strftime('%Y')), int(publishedAt.strftime('%m')), int(publishedAt.strftime('%d')))
                newStartDate = pywikibot.Claim(repo, u'P580')
                newStartDate.setTarget(start_date_datetime)
                claim.addQualifier(newStartDate, summary=u'Add start time')

            print('Removing old qualifiers')
            qualifiersToRemove = []
            if(subscribers) : qualifiersToRemove.append(subscribers)
            if(views) : qualifiersToRemove.append(views)
            if(pit) : qualifiersToRemove.append(pit)
            if(videos) : qualifiersToRemove.append(videos)
            claim.removeQualifiers(qualifiersToRemove, summary=u"Remove old qualifiers")
            print('Adding updated qualifiers')
            claim.addQualifier(newSubscribers, summary=u'Update subscriber count')
            claim.addQualifier(newViews, summary=u'Update view count')
            claim.addQualifier(newVideos, summary=u'Update videos count')
            claim.addQualifier(newPit, summary=u'Update point in time')

            # can't use a claim twice, recreate with same value
            channelIdClaim = pywikibot.Claim(repo, u'P2397') # Channel ID
            channelIdClaim.setTarget(channel_id)
            newPit = pywikibot.Claim(repo, u'P585') # point in time
            newPit.setTarget(piTime)

            print('Add stats record')
            oldstats = dictionary['claims']['P8687'] if u'P8687' in dictionary['claims'] else []

            for r in oldstats:
                if u'P2397' in r.qualifiers:
                    val = r.qualifiers['P2397'][0].getTarget()
                    if val == channel_id and r.getRank() == 'preferred':
                        r.changeRank(u'normal')
                        
            record = pywikibot.Claim(repo, u'P8687')
            record.setTarget(subsCount)
            record.addQualifier(channelIdClaim, summary=u'Set Channel ID')
            record.addQualifier(newPit, summary=u'Set point in time')
            record.setRank(u'preferred')
            item.addClaim(record, summary=u'Adding stats as new social media followers')

if __name__ == "__main__":
    main()
