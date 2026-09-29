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

def calc_new_total(fund, rate, is_gold):
    base = fund * 0.6 + rate * 0.4
    if is_gold:
        base += 20
    return round(base,1)

def fetch_hkjc(date_str="2026-10-01"):
    session = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "zh-HK,zh;q=0.9",
    }
    all_races = []
    for race_no in range(1, 12):
        url = f"https://racing.hkjc.com/racing/information/Chinese/Racing/RaceCard.aspx?RaceDate={date_str.replace('-','/')}&Racecourse=ST&RaceNo={race_no}"
        try:
            r = session.get(url, headers=headers, timeout=25)
            r.encoding = 'utf-8'
            text = r.text
            if "檔位" not in text:
                print(f"R{race_no} no draw info")
                continue
            soup = BeautifulSoup(text, 'lxml')
            target_table = None
            for tbl in soup.find_all("table"):
                if "檔位" in tbl.get_text():
                    target_table = tbl
                    break
            if not target_table:
                continue
            horses = []
            for tr in target_table.find_all("tr")[1:]:
                tds = tr.find_all("td")
                if len(tds) < 4:
                    continue
                try:
                    t = [td.get_text(strip=True) for td in tds]
                    if not t[0].isdigit():
                        continue
                    no = int(re.search(r'\d+', t[0]).group())
                    name = t[1].split()[0] if len(t) > 1 else ""
                    m = re.search(r'\d+', t[2]) if len(t) > 2 else None
                    if not m:
                        continue
                    draw = int(m.group())
                    rate, is_gold = get_gold_info("沙田", 1200, draw)
                    fund = 70
                    total = calc_new_total(fund, rate, is_gold)
                    grade = "A" if total >= 60 else "B" if total >= 45 else "C"
                    horses.append({
                        "no": no, "name": name, "draw": draw,
                        "jockey": t[3] if len(t) > 3 else "",
                        "trainer": t[4] if len(t) > 4 else "",
                        "fund": fund, "total": total, "grade": grade,
                        "win_odds": 10.0, "t1": 10, "t2": 10, "t3": 10, "drop": 0,
                        "drawRate": rate, "isGoldDraw": is_gold, "isGoldCold": False
                    })
                except Exception:
                    continue
            if horses:
                mm = re.search(r'(\d{3,4})M', text)
                dist = int(mm.group(1)) if mm else 1200
                all_races.append({"race_no": race_no, "venue": "沙田", "distance": dist, "class": "3班", "track": "好地", "horses": horses})
        except Exception as e:
            print(f"R{race_no} fail {e}")
            continue
    now = datetime.datetime.now(ZoneInfo("Asia/Hong_Kong"))
    if not all_races:
        print("0場，保留舊檔")
        try:
            with open('data.json','r',encoding='utf-8') as old:
                old_data = json.load(old)
                if old_data.get("races"):
                    return old_data
        except Exception:
            pass
    return {
        "updated": now.strftime("%Y-%m-%d %H:%M:%S"),
        "version": f"V9.7 Clean {now.strftime('%m-%d %H:%M')}",
        "isEarlyBird": True,
        "races": all_races
    }

if __name__ == "__main__":
    data = fetch_hkjc("2026-10-01")
    with open('data.json','w',encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"完成 {len(data['races'])}場")