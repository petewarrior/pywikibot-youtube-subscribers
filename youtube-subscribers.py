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
                  'key': "youtube api key here"}
        r = requests.get(
            "https://youtube.googleapis.com/youtube/v3/channels", params)

        response = r.json()
        res = res + response["items"]

    app = append_statistics(res)

    return map(app, channels)


def main():
    site = pywikibot.Site()

    # pages values can either be the page title as string or a dictionary in the following format:
    # { 'page': '<page title>', channels: [{'channel_direct_url': 'c/omit_if_inapplicable', 'channel_url': 'required'}]}
    pages = []

    for p in pages:
        if isinstance(p, str):
            page_title = p
        if isinstance(p, dict):
            page_title = p["page"]

        page = pywikibot.Page(site, page_title)
        text = page.text

        if isinstance(p, str):
            channel_ids = re.findall(
                r'(?:\{\{Infobox YouTube personality).*?(?:channel_url).*?\=.*?([\w_-]+)', text, flags=re.DOTALL)
            channels = list(map(lambda ch: {"channel_url": ch}, channel_ids))
        else:
            channels = p["channels"]

        stats = get_statistics(channels=channels)

        for s in stats:
            if "channel_direct_url" in s and isinstance(s['channel_direct_url'], str):
                channel_type = 'channel_direct_url'
                id = s["channel_direct_url"]
            else:
                channel_type = 'channel_url'
                id = s["channel_url"]
            viewsInt = int(s["statistics"]["viewCount"])
            views = "{:,}".format(viewsInt)

            subscribersInt = int(s["statistics"]["subscriberCount"])
            subscribers = ('~' if subscribersInt > 100000 else '') + \
                "{:,}".format(subscribersInt)

            subcomp = re.compile(r'(\{\{Infobox YouTube personality.*?' + channel_type + r'.*?\=.*?' +
                                 id + r'.*?subscribers.*?\=.*?)([\w\s\~\.\,]+)[\n\s]*', flags=re.DOTALL)

            # subscribers
            text = subcomp.sub(r'\1 ' + subscribers + r"\n", text)

            # views
            text = re.sub(r'(\{\{Infobox YouTube personality.*?' + channel_type + r'.*?\=.*?' + id +
                          r'.*?views.*?\=.*?)([\w\s\.\,]+)[\n\s]*', r"\1 " + views + r"\n", text, flags=re.DOTALL)

            # stats_update
            text = re.sub(r'(\{\{Infobox YouTube personality.*?' + channel_type + r'.*?\=.*?' + id +
                          r'.*?stats_update.*?\=.*?)({{date\|[\d-]+}})[\n\s]*', r"\1" + datetime.datetime.now().strftime("{{date|%Y-%m-%d}}") + r"\n", text, flags=re.DOTALL)

            page.text = text

        page.save(summary="YouTube subscriber update")


if __name__ == "__main__":
    main()
