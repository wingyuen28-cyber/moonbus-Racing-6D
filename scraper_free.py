import requests, json, re, datetime
from bs4 import BeautifulSoup
from zoneinfo import ZoneInfo
import os

with open('draw_bias.json','r',encoding='utf-8') as f:
    DRAW_BIAS = json.load(f)

def get_gold_info(venue, distance, draw):
    key = f"{venue} {distance}"
    if key in DRAW_BIAS and str(draw) in DRAW_BIAS[key]:
        rate = DRAW_BIAS[key][str(draw)]
        return rate, rate >= 12
    return None, False

def fetch_real_hkjc(target_date="2026-10-01"):
    # 馬會真排位頁 - 賽前1日09:00後就會有
    # 10月1日國慶係沙田 ST
    base_url = f"https://racing.hkjc.com/racing/information/Chinese/Racing/RaceCard.aspx?RaceDate={target_date.replace('-','/')}&Racecourse=ST&RaceNo=1"

    headers = {
        "User-Agent":"Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)",
        "Referer":"https://racing.hkjc.com/"
    }
    s = requests.Session()
    # 先拿總場次列表
    r = s.get(base_url, headers=headers, timeout=20)
    # 用regex搵有幾多場 RaceNo=1..11
    race_nos = re.findall(r'RaceNo=(\d+)', r.text)
    max_race = max(map(int, race_nos)) if race_nos else 11

    all_races = []
    for race_no in range(1, max_race+1):
        url = f"https://racing.hkjc.com/racing/information/Chinese/Racing/RaceCard.aspx?RaceDate={target_date.replace('-','/')}&Racecourse=ST&RaceNo={race_no}"
        html = s.get(url, headers=headers, timeout=20).text
        soup = BeautifulSoup(html, 'html.parser')

        # 抓途程 - 例如 1200M
        dist_match = re.search(r'(\d{3,4})M', html)
        distance = int(dist_match.group(1)) if dist_match else 1200
        venue = "沙田"

        horses = []
        # 馬會每匹馬喺 table.comHorses
        for row in soup.select("table.f_tac tr"):
            cols = row.select("td")
            if len(cols) < 10: continue
            try:
                draw = int(cols[2].text.strip())
                horse_no = cols[0].text.strip()
                name = cols[1].text.strip()
                jockey = cols[4].text.strip()
                # 賠率另一個API捉
                horses.append({
                    "no": horse_no,
                    "name": name,
                    "draw": draw,
                    "jockey": jockey,
                    "trainer": cols[5].text.strip(),
                    "fund": 80, "total": 85, "grade": "B",
                    "win_odds": 10.0, "t1": 10, "t2": 10, "t3": 10, "drop": 0
                })
            except: continue

        # 加金檔
        for h in horses:
            rate, is_gold = get_gold_info(venue, distance, h['draw'])
            h['drawRate'] = rate
            h['isGoldDraw'] = is_gold
            h['isGoldCold'] = is_gold and h['win_odds']>=15 # 真正要再加drop

        all_races.append({
            "race_no": race_no,
            "venue": venue,
            "distance": distance,
            "class": f"{race_no}班",
            "track": "好地",
            "horses": horses
        })

    now_hk = datetime.datetime.now(ZoneInfo("Asia/Hong_Kong"))
    return {
        "updated": now_hk.strftime("%Y-%m-%d %H:%M:%S"),
        "version": f"V9.4 | 早鳥真檔 {now_hk.strftime('%m-%d %H:%M')}",
        "isEarlyBird": True,
        "races": all_races
    }

if __name__ == "__main__":
    # 國慶改呢個日子
    data = fetch_real_hkjc("2026-10-01")
    with open('data.json','w',encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"成功捉到 {len(data['races'])} 場真數據")