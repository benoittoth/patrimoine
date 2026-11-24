import json, os, re, datetime as dt, urllib.request
os.makedirs("data", exist_ok=True)
from youtube_transcript_api import YouTubeTranscriptApi
chans = json.load(open("channels.json"))
try: old = json.load(open("data/videos.json"))
except Exception: old = {"videos": {}}
vids = old.get("videos", {})
ua = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36", "Accept-Language": "fr-FR,fr;q=0.9", "Cookie": "SOCS=CAI; CONSENT=YES+cb"}
for c in chans:
    try:
        html = urllib.request.urlopen(urllib.request.Request(f"https://www.youtube.com/@{c['handle']}", headers=ua), timeout=20).read().decode("utf8", "ignore")
        m = re.search(r'"(?:channelId|externalId)":"(UC[\w-]{22})"', html) or re.search(r'channel/(UC[\w-]{22})', html)
        if not m: raise ValueError("id de chaîne introuvable")
        cid = m.group(1)
        rss = urllib.request.urlopen(urllib.request.Request(f"https://www.youtube.com/feeds/videos.xml?channel_id={cid}", headers=ua), timeout=20).read().decode("utf8", "ignore")
    except Exception as e:
        print(c["name"], "erreur", e); continue
    for vid, title, pub in re.findall(r"<yt:videoId>([\w-]+)</yt:videoId>.*?<title>(.*?)</title>.*?<published>(.*?)</published>", rss, re.S)[:5]:
        if vid in vids and vids[vid].get("transcript"): continue
        item = vids.get(vid, {"channel": c["name"], "title": title, "date": pub[:10], "url": f"https://www.youtube.com/watch?v={vid}"})
        try:
            tr = YouTubeTranscriptApi().fetch(vid, languages=["fr", "en"])
            item["transcript"] = " ".join(s.text for s in tr)[:60000]
        except Exception as e:
            item["error"] = str(e)[:120]
        vids[vid] = item
cut = (dt.date.today() - dt.timedelta(days=21)).isoformat()
vids = {k: v for k, v in vids.items() if v.get("date", "") >= cut}
json.dump({"updated": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), "videos": vids}, open("data/videos.json", "w"), ensure_ascii=False)
print(len(vids), "vidéos")
