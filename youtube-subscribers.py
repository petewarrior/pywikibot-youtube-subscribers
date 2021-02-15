import pywikibot
import re
import datetime

import requests

def get_statistics(ids=list, names=list):
    idlist = ','.join(ids)

    res = []

    if len(ids) > 0 :
      params = {'part': 'statistics,status', 'id': idlist, 'key': "YOUR YOUTUBE API KEY HERE"}
      r = requests.get("https://youtube.googleapis.com/youtube/v3/channels", params)

      response = r.json()
      res = res + response["items"]
    
    return res 

def main() :
  site = pywikibot.Site()

  # PAGE NAMES TO MONITOR HERE
  pages = []

  for p in pages:
    page = pywikibot.Page(site, p)
    text = page.text

    channel_ids = re.findall(r'(?:\{\{Infobox YouTube personality).*?(?:channel_url).*?\=.*?([\w_-]+)', text, flags=re.DOTALL)

    stats = get_statistics(ids= channel_ids)

  for s in stats:
      id = s["id"]
      viewsInt = int(s["statistics"]["viewCount"])
      views =  "{:,}".format(viewsInt)

      subscribersInt = int(s["statistics"]["subscriberCount"])
      subscribers = ('~' if subscribersInt > 100000 else '') + "{:,}".format(subscribersInt)

      subcomp = re.compile(r'(\{\{Infobox YouTube personality.*?channel_url.*?\=.*?'+ id +r'.*?subscribers.*?\=.*?)([\w\s\~\.\,]+)[\n\s]*', flags=re.DOTALL)

      # subscribers
      text = subcomp.sub(r'\1 ' + subscribers + r"\n", text)

      # views
      text = re.sub(r'(\{\{Infobox YouTube personality.*?channel_url.*?\=.*?'+ id + r'.*?views.*?\=.*?)([\w\s\.\,]+)[\n\s]*', r"\1 " + views + r"\n", text, flags=re.DOTALL)

      # stats_update
      text = re.sub(r'(\{\{Infobox YouTube personality.*?channel_url.*?\=.*?' + id + r'.*?stats_update.*?\=.*?)({{date\|[\d-]+}})[\n\s]*', r"\1" + datetime.datetime.now().strftime("{{date|%Y-%m-%d}}") + r"\n", text, flags=re.DOTALL)

      page.text = text

    page.save(summary= "YouTube subscriber update script, ran manually")

if __name__ == "__main__":
  main()
