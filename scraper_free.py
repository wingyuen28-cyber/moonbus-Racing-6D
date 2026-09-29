import requests, json, re, datetime
from zoneinfo import ZoneInfo
from bs4 import BeautifulSoup

with open('draw_bias.json','r',encoding='utf-8') as f:
    DRAW_BIAS = json.load(f)

def get_gold_info(venue, distance, draw):
    key = f"{venue} {distance}"
    if key in DRAW_BIAS and str(draw) in DRAW_BIAS[key]:
        rate = DRAW_BIAS[key][str(draw)]
        return rate, rate >= 12 # >=12% 就係金檔
    return 8.0, False

def calc_new_total(fund_score, draw_rate, is_gold):
    # 你張圖嘅公式：新總分 = 基金分*0.6 + (檔位勝率*100)*0.4
    # draw_rate本身已經係 %，例如 15
    base = fund_score * 0.6 + draw_rate * 0.4
    if is_gold:
        base += 20 # 金檔額外+20分，由B升A
    return round(base, 1)

def fetch_hkjc(date_str="2026-10-01"):
    session = requests.Session()
    headers = {"User-Agent":"Mozilla/5.0", "Accept-Language":"zh-HK"}
    all_races = []

    for race_no in range(1, 13): # 國慶係11場，開到12保險啲
        url = f"https://racing.hkjc.com/racing/information/Chinese/Racing/RaceCard.aspx?RaceDate={date_str.replace('-','/')}&Racecourse=ST&RaceNo={race_no}"
        try:
            r = session.get(url, headers=headers, timeout=20)
            r.encoding = 'utf-8'
            soup = BeautifulSoup(r.text, 'lxml')
            m = re.search(r'(\d{3,4})M', r.text)
            distance = int(m.group(1)) if m else 1200

            table = soup.find("table", class_="f_tac")
            if not table: continue
            horses = []
            for tr in table.find_all("tr")[1:]:
                tds = tr.find_all("td")
                if len(tds) < 6: continue
                try:
                    no = tds[0].get_text(strip=True)
                    name = tds[1].get_text(strip=True).split("\n")[0]
                    draw = int(re.search(r'\d+', tds[2].get_text(strip=True)).group())
                    jockey = tds[4].get_text(strip=True)
                    trainer = tds[5].get_text(strip=True)

                    rate, is_gold = get_gold_info("沙田", distance, draw)
                    fund = 70 # 暫時用基金分70做例子，你之後可接返真正基金分
                    total = calc_new_total(fund, rate, is_gold)
                    grade = "A" if total >= 60 else "B" if total >= 45 else "C"

                    horses.append({
                        "no": int(no) if no.isdigit() else len(horses)+1,
                        "name": name, "draw": draw, "jockey": jockey, "trainer": trainer,
                        "fund": fund, "total": total, "grade": grade,
                        "win_odds": 10.0, "t1": 10, "t2": 10, "t3": 10, "drop": 0,
                        "drawRate": rate, "isGoldDraw": is_gold, "isGoldCold": False
                    })
                except: continue
            if horses:
                all_races.append({"race_no": race_no, "venue": "沙田", "distance": distance, "class": "3班", "track": "好地", "horses": horses})
        except Exception as e:
            print(f"R{race_no} fail {e}")
            continue

    now = datetime.datetime.now(ZoneInfo("Asia/Hong_Kong"))
    return {"updated": now.strftime("%Y-%m-%d %H:%M:%S"), "version": f"V9.5 | 新計分 {now.strftime('%m-%d %H:%M')}", "isEarlyBird": True, "races": all_races}

if __name__ == "__main__":
    data = fetch_hkjc("2026-10-01")
    with open('data.json','w',encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"完成 {len(data['races'])}場")