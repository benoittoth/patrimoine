"""Prépare la mise à jour de l'app depuis data/cours.json.
Usage : python app_sync.py lines.json > updates.json
lines.json = liste [{id, version, yf, yfFx, price, priceDate, watch}] lue dans les collections lines et watch (watch:true pour ces dernières, jamais modifiées).
Sortie : {"lines":[{id, ifVersion, price, priceDate}], "quotes":[{id, closes, h6, h5, at, src}]}"""
import json, sys, datetime as dt
cours = json.load(open("data/cours.json"))["quotes"]
lines = json.load(open(sys.argv[1]))
fx = cours.get("EURUSD=X", {})
fxd, fxw = fx.get("closes", {}), fx.get("weekly", {})
def conv(series, rates):
    ks = sorted(rates); out = {}
    for d, v in series.items():
        r = rates.get(d) or next((rates[k] for k in reversed(ks) if k <= d), None)
        if r: out[d] = round(v / r, 4)
    return out
def enc(series, days):
    ks = sorted(series)[-days:]
    if not ks: return None
    d0 = dt.date.fromisoformat(ks[0])
    def b36(n):
        a = "0123456789abcdefghijklmnopqrstuvwxyz"; r = ""
        while True:
            n, k = divmod(n, 36); r = a[k] + r
            if not n: return r
    return {"d": ks[0], "o": ",".join(b36((dt.date.fromisoformat(k) - d0).days) for k in ks), "v": ",".join(f"{series[k]:.4g}" for k in ks)}
now = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
res = {"lines": [], "quotes": []}; done = set()
for l in lines:
    q = cours.get(l.get("yf") or "")
    if not q or "price" not in q: continue
    usd = q.get("currency") == "USD" if q.get("currency") else bool(l.get("yfFx"))
    closes = conv(q["closes"], fxd) if usd else q["closes"]
    weekly = conv(q.get("weekly", {}), fxw) if usd else q.get("weekly", {})
    price = round(q["price"] / fx["price"], 4) if usd else q["price"]
    date = max(closes) if closes else dt.date.today().isoformat()
    closes[date] = price
    old = l.get("price") or price
    if not l.get("watch") and abs(price - old) / old < 0.25 and (price != l.get("price") or date != l.get("priceDate")):
        res["lines"].append({"id": l["id"], "ifVersion": l["version"], "price": price, "priceDate": date})
    qid = "yf_" + "".join(c if c.isalnum() else "_" for c in l["yf"])
    if qid not in done:
        done.add(qid)
        last45 = dict(sorted(closes.items())[-45:])
        res["quotes"].append({"id": qid, "src": "yahoo-github", "at": now, "closes": last45, "h6": enc(closes, 130), "h5": enc(weekly, 270)})
print(json.dumps(res, ensure_ascii=False))
