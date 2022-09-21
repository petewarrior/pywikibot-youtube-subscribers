import pywikibot
import datetime
import os
import sys
from unicodedata import normalize
from dateutil.parser import parse

from dotenv import load_dotenv

import requests

class Channel:
    def __init__(self, repo, dictionary, item, claim) -> None:
        self.repo = repo
        self.dictionary = dictionary
        self.item = item
        self.claim = claim

    def collect_current_data(self):
        self.channel_id = self.claim.getTarget()
        self.current_channel_name = self.claim.qualifiers['P1810'][0] if u'P1810' in self.claim.qualifiers else None
        
        self.start_date = self.claim.qualifiers['P580'][0] if 'P580' in self.claim.qualifiers else None
        self.subscribers = self.claim.qualifiers['P3744'][0] if 'P3744' in self.claim.qualifiers else None
        self.views = self.claim.qualifiers['P5436'][0] if 'P5436' in self.claim.qualifiers else None
        self.pit = self.claim.qualifiers['P585'][0] if 'P585' in self.claim.qualifiers else None
        self.videos = self.claim.qualifiers['P3740'][0] if 'P3740' in self.claim.qualifiers else None
        self.channel = self.claim.target

        channels = [{'channel_url': self.channel}]

        stats = get_statistics(channels=channels)

        for s in stats: # always one for now
            self.viewsInt = s["statistics"]["viewCount"]
            self.subscribersInt = s["statistics"]["subscriberCount"]
            self.videosInt = s["statistics"]["videoCount"]
            self.channelNameString = s["snippet"]["title"]
            self.publishedAt = parse(s["snippet"]["publishedAt"])
            
            self.subsCount = pywikibot.WbQuantity(amount='+'+self.subscribersInt, site=self.repo)
            self.newSubscribers = pywikibot.Claim(self.repo, u'P3744') # number of subscribers
            self.newSubscribers.setTarget(self.subsCount)
            viewCount = pywikibot.WbQuantity(amount='+'+self.viewsInt, site=self.repo)
            self.newViews = pywikibot.Claim(self.repo, u'P5436') # number of views
            self.newViews.setTarget(viewCount)
            videoCount = pywikibot.WbQuantity(amount='+'+self.videosInt, site=self.repo)
            self.newVideos = pywikibot.Claim(self.repo, u'P3740') # number of videos
            self.newVideos.setTarget(videoCount)
            currTime = datetime.datetime.now()
            self.piTime = pywikibot.WbTime(int(currTime.strftime('%Y')), int(currTime.strftime('%m')), int(currTime.strftime('%d')))
            self.newPit = pywikibot.Claim(self.repo, u'P585') # point in time
            self.newPit.setTarget(self.piTime)

    def check_need_update(self):
        if self.current_channel_name :
            print(self.current_channel_name.getTarget())
        else :
            print(self.channel_id + u' (will populate channel name)')

        if self.claim.getRank() == 'deprecated' :
            print('Skipping deprecated entry')
            return False

        if self.pit :
            if self.pit.getTarget().toTimestr() == self.piTime.toTimestr() :
                print('Last updated today')
                return False
        
        if self.subscribers :
            if(int(self.subscribersInt) < 100000) :
                if abs(int(self.subscribers.getTarget().amount) - int(self.subscribersInt)) < 1000 :
                    print('Subscriber change <1000')
                    return False
            elif(int(self.subscribersInt) < 1000000) :
                if abs(int(self.subscribers.getTarget().amount) - int(self.subscribersInt)) < 5000 :
                    print('Silver, subscriber change <5000')
                    return False
            else :
                if abs(float(self.subscribers.getTarget().amount) - float(self.subscribersInt)) / float(self.subscribers.getTarget().amount) < 0.01 :
                    print('Gold or higher, subscriber change <1%')
                    return False

        return True
        
    def start_update(self, include_deprecated=False):
        if self.claim.getRank() == 'deprecated' and include_deprecated is False :
            print('Skipping deprecated entry')
            return

        try :
            if self.current_channel_name is not None :
                if self.channelNameString.strip() != self.current_channel_name.getTarget().strip() :
                    print('Removing old channel name')
                    self.claim.removeQualifier(self.current_channel_name, summary=u'Remove old channel name')
                    self.current_channel_name = None
        except BaseException as err :
            print(err)

        try :
            if self.current_channel_name is None :
                print('Adding channel name: "' + self.channelNameString + '"')
                newChannelName = pywikibot.Claim(self.repo, u'P1810')
                newChannelName.setTarget(self.channelNameString.strip())
                self.claim.addQualifier(newChannelName, summary=u'Set channel name')
        except BaseException as err :
            print('Adding channel name error, skipped')
            print(err)
            
        if self.start_date is None :
            print('Adding start date')
            start_date_datetime = pywikibot.WbTime(int(self.publishedAt.strftime('%Y')), int(self.publishedAt.strftime('%m')), int(self.publishedAt.strftime('%d')))
            newStartDate = pywikibot.Claim(self.repo, u'P580')
            newStartDate.setTarget(start_date_datetime)
            self.claim.addQualifier(newStartDate, summary=u'Add start time')

        if self.subscribers:
            print('Subscriber change: ' + str(self.subscribers.getTarget().amount) + ' -> ' + str(self.subscribersInt))

        print('Removing old qualifiers')
        qualifiersToRemove = []
        if(self.subscribers) : qualifiersToRemove.append(self.subscribers)
        if(self.views) : qualifiersToRemove.append(self.views)
        if(self.pit) : qualifiersToRemove.append(self.pit)
        if(self.videos) : qualifiersToRemove.append(self.videos)
        self.claim.removeQualifiers(qualifiersToRemove, summary=u"Remove old qualifiers")
        print('Adding updated qualifiers')
        self.claim.addQualifier(self.newSubscribers, summary=u'Update subscriber count')
        self.claim.addQualifier(self.newViews, summary=u'Update view count')
        self.claim.addQualifier(self.newVideos, summary=u'Update videos count')
        self.claim.addQualifier(self.newPit, summary=u'Update point in time')

        # can't use a claim twice, recreate with same value
        channelIdClaim = pywikibot.Claim(self.repo, u'P2397') # Channel ID
        channelIdClaim.setTarget(self.channel_id)
        newPit = pywikibot.Claim(self.repo, u'P585') # point in time
        newPit.setTarget(self.piTime)

        print('Add stats record')
        oldstats = self.dictionary['claims']['P8687'] if u'P8687' in self.dictionary['claims'] else []

        for r in oldstats:
            if u'P2397' in r.qualifiers:
                val = r.qualifiers['P2397'][0].getTarget()
                if val == self.channel_id and r.getRank() == 'preferred':
                    r.changeRank(u'normal')
                    
        record = pywikibot.Claim(self.repo, u'P8687')
        record.setTarget(self.subsCount)
        record.addQualifier(channelIdClaim, summary=u'Set Channel ID')
        record.addQualifier(newPit, summary=u'Set point in time')
        record.setRank(u'preferred')
        self.item.addClaim(record, summary=u'Adding stats as new social media followers')

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
    args = sys.argv[1:]

    load_dotenv()

    wiki = pywikibot.Site("en", "wikipedia")
    site = pywikibot.Site("wikidata", "wikidata")
    repo = site.data_repository()

    force_update = False
    include_deprecated = False
    custom_pages = None

    for a in args :
        if a == '--force-update':
            force_update = True
            continue
        if a == '--include-deprecated':
            include_deprecated = True
            continue
        if a.find('--pages') != -1:
            custom_pages = a.split('=')[1].split(',')
            continue

    if(custom_pages is not None) :
        pages = custom_pages
    else :
        pages = os.environ.get('WIKIDATA_IDS', '').split(',')

    for p in pages:
        item = pywikibot.ItemPage(site, p)

        dictionary = item.get()

        if 'P2397' not in dictionary['claims'] : continue        
        print(dictionary['labels']['en'])
        
        channel_count = len(dictionary['claims']['P2397'])
        channel_objs = []

        for c in range(channel_count): 

            claim = dictionary['claims']['P2397'][c]

            ch = Channel(repo, dictionary, item, claim)
            ch.collect_current_data()
            channel_objs.append(ch)

            continue
            
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

                print('Subscriber change: ' + subscribers.getTarget().amount + ' -> ' + subscribersInt)

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

        must_do_update = False

        if force_update:
            print('Force update')
            must_do_update = True
        else:
            #if one needs update, update all
            for c in channel_objs :
                must_do_update = c.check_need_update()
                if must_do_update :
                    break

        if must_do_update :
            print('Start update')
            for c in channel_objs :
                c.start_update(include_deprecated=include_deprecated)
        else :
            print('No update needed for this item')

if __name__ == "__main__":
    main()
