import json, requests, datetime
# V9.2 金檔表
DRAW_BIAS = {
  "沙田 1000": {"12":15,"13":15,"14":14},
  "沙田 1200": {"9":13,"10":13.5,"11":13},
  "沙田 1400": {"10":14.2,"11":13.8,"9":13},
  "跑馬地 1650": {"1":21,"2":19,"3":18},
  "跑馬地 1200": {"1":15,"2":14}
}
def get_gold_info(track, dist, draw):
    key = f"{track} {dist}"
    rate = DRAW_BIAS.get(key, {}).get(str(draw), 8)
    return rate, rate >= 12

# 1. 攞真實賽程 + 賠率 (你而家嗰段保留)
#...你原本scraper攞HKJC odds嘅code...

# 2. 計金檔分
for race in data["races"]:
    track = race["track"] # 沙田 / 跑馬地
    dist = race["dist"] # 1000
    for horse in race["horses"]:
        rate, isGold = get_gold_info(track, dist, horse["draw"])
        horse["drawRate"] = rate
        horse["isGoldDraw"] = isGold
        horse["isGoldCold"] = horse["odds"]>=30 and isGold and horse["drop"]>=25

# 3. WhatsApp分流警報
def send_whatsapp(msg, apikey):
    # 你CallMeBot key
    url = f"https://api.callmebot.com/whatsapp.php?phone=YOURPHONE&text={msg}&apikey={apikey}"
    requests.get(url)

gold_colds = [h for r in data["races"] for h in r["horses"] if h.get("isGoldCold")]
if gold_colds:
    msg = "💎金檔冷馬警報\n" + "\n".join([f"第{r}場 {h['no']}號 {h['draw']}檔勝率{h['drawRate']}% {h['odds']}倍" for h in gold_colds[:3]])
    send_whatsapp(msg, "YOUR_APIKEY")

with open("data.json","w",encoding="utf-8") as f:
    json.dump(data,f,ensure_ascii=False)