import json, datetime as dt, time
import yfinance as yf
syms = json.load(open("symbols.json"))
out = {"updated": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), "quotes": {}}
for s in syms:
    for attempt in range(3):
        try:
            t = yf.Ticker(s)
            h = t.history(period="1y", interval="1d", auto_adjust=False)
            if h.empty: raise ValueError("vide")
            closes = {d.strftime("%Y-%m-%d"): round(float(c), 4) for d, c in h["Close"].dropna().items()}
            fi = t.fast_info
            last = float(fi.get("lastPrice") or list(closes.values())[-1])
            out["quotes"][s] = {
                "price": round(last, 4),
                "time": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                "currency": fi.get("currency"),
                "prevClose": round(float(fi.get("previousClose") or 0), 4) or None,
                "closes": closes,
            }
            break
        except Exception as e:
            out["quotes"].setdefault(s, {"error": str(e)[:120]})
            time.sleep(3)
json.dump(out, open("data/cours.json", "w"), ensure_ascii=False, separators=(",", ":"))
print(f"{sum('price' in v for v in out['quotes'].values())}/{len(syms)} cours")
