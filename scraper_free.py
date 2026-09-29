import requests, json, re, datetime
from zoneinfo import ZoneInfo
from bs4 import BeautifulSoup

with open('draw_bias.json','r',encoding='utf-8') as f:
    DRAW_BIAS = json.load(f)

def get_gold_info(venue, distance, draw):
    key = f"{venue} {distance}"
    if key in DRAW_BIAS and str(draw) in DRAW_BIAS[key]:
        rate = DRAW_BIAS[key][str(draw)]
        return rate, rate >= 12
    return 8.0, False

def fetch_hkjc(date_str="2026-10-01"):
    session = requests.Session()
    headers = {"User-Agent":"Mozilla/5.0", "Accept-Language":"zh-HK"}
    all_races = []

    for race_no in range(1, 12):
        url = f"https://racing.hkjc.com/racing/information/Chinese/Racing/RaceCard.aspx?RaceDate={date_str.replace('-','/')}&Racecourse=ST&RaceNo={race_no}"
        try:
            r = session.get(url, headers=headers, timeout=20)
            r.encoding = 'utf-8'
            soup = BeautifulSoup(r.text, 'lxml')

            # 捉途程
            m = re.search(r'(\d{3,4})M', r.text)
            distance = int(m.group(1)) if m else 1200

            horses = []
            # 馬會排位表個table
            table = soup.find("table", class_="f_tac")
            if not table:
                continue

            for tr in table.find_all("tr")[1:]: # 跳過header
                tds = tr.find_all("td")
                if len(tds) < 6: continue
                try:
                    no = tds[0].get_text(strip=True)
                    name = tds[1].get_text(strip=True).split("\n")[0]
                    draw = int(tds[2].get_text(strip=True))
                    jockey = tds[4].get_text(strip=True)
                    trainer = tds[5].get_text(strip=True)

                    rate, is_gold = get_gold_info("沙田", distance, draw)
                    horses.append({
                        "no": int(no) if no.isdigit() else len(horses)+1,
                        "name": name,
                        "draw": draw,
                        "jockey": jockey,
                        "trainer": trainer,
                        "fund": 80, "total": 85, "grade": "B",
                        "win_odds": 10.0, "t1": 10, "t2": 10, "t3": 10, "drop": 0,
                        "drawRate": rate,
                        "isGoldDraw": is_gold,
                        "isGoldCold": False
                    })
                except:
                    continue

            if horses:
                all_races.append({
                    "race_no": race_no,
                    "venue": "沙田",
                    "distance": distance,
                    "class": "3班",
                    "track": "好地",
                    "horses": horses
                })
        except Exception as e:
            print(f"R{race_no} fail {e}")
            continue

    now = datetime.datetime.now(ZoneInfo("Asia/Hong_Kong"))
    return {
        "updated": now.strftime("%Y-%m-%d %H:%M:%S"),
        "version": f"V9.4 | 早鳥真檔 {now.strftime('%m-%d %H:%M')}",
        "isEarlyBird": True,
        "races": all_races
    }

if __name__ == "__main__":
    data = fetch_hkjc("2026-10-01")
    with open('data.json','w',encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"完成 {len(data['races'])}場")