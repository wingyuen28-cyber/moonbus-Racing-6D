import requests, json, datetime, os
from zoneinfo import ZoneInfo

# 讀你而家個金檔庫
with open('draw_bias.json','r',encoding='utf-8') as f:
    DRAW_BIAS = json.load(f)

def get_gold_info(venue, distance, draw):
    # venue: 沙田/跑馬地, distance: 1000, draw: 1
    key = f"{venue} {distance}"
    if key in DRAW_BIAS and str(draw) in DRAW_BIAS[key]:
        rate = DRAW_BIAS[key][str(draw)]
        is_gold = rate >= 12 # 12%為金檔門檻
        return rate, is_gold
    return None, False

def fetch_hkjc():
    # 你而家用緊嘅真實API，用返同一個URL
    # 呢個URL喺賽前1日09:00後就會有完整排位+檔位
    url = "https://bet.hkjc.com/racing/getJSON.aspx?type=racecard"
    try:
        r = requests.get(url, timeout=15, headers={"User-Agent":"Mozilla/5.0"})
        races = r.json() # 假設你而家解析方法一樣
    except:
        # 如果當日冇賽，留返舊data
        return None

    now_hk = datetime.datetime.now(ZoneInfo("Asia/Hong_Kong"))
    for race in races:
        for h in race.get('horses',[]):
            rate, is_gold = get_gold_info(race['venue'], race['distance'], h['draw'])
            h['drawRate'] = rate
            h['isGoldDraw'] = is_gold

    # 加早鳥標記
    result = {
        "version": f"V9.4 | 早鳥金檔 {now_hk.strftime('%m-%d %H:%M')}",
        "fetch_time": now_hk.isoformat(),
        "isEarlyBird": True, # 俾index.html識別
        "races": races
    }
    return result

if __name__ == "__main__":
    data = fetch_hkjc()
    if data:
        with open('data.json','w',encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"早鳥更新成功 {len(data['races'])}場")
    else:
        print("今日未有排位，保留舊data")