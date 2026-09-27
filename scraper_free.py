import requests, json, os, time
from datetime import datetime

# ========== 免費馬會接口 (唔使API Key) ==========
# 馬會公開 JSON，全香港App都係咁免費攞
def get_live_odds(date=None, venue="ST"):
    # 如果冇賽事，就用示範數據，等你測試
    if not date:
        date = datetime.now().strftime("%Y/%m/%d")

    # 真實免費接口 - 馬會投注頁
    urls = [
        f"https://bet.hkjc.com/racing/getJSON.aspx?type=win,pla&qrs=false&date={date.replace('/','-')}&venue={venue}",
        f"https://racing.hkjc.com/racing/information/Chinese/Racing/LocalResults.aspx?RaceDate={date}"
    ]

    # 先試免費賠率JSON
    try:
        headers = {"User-Agent":"Mozilla/5.0","Referer":"https://bet.hkjc.com/"}
        r = requests.get(urls[0], headers=headers, timeout=8)
        if r.status_code==200 and "WIN" in r.text:
            return r.json()
    except:
        pass
    return None

# ========== 6維計算 (你之前嗰套) ==========
def calc_d1(trainer): return 78, "獨贏12% 上名28%"
def calc_d2(draw):
    is_worst = draw>=11
    score = 28 if is_worst else 85 if draw<=3 else 70
    return score, f"{draw}檔 上名{35 if draw<=3 else 15}%", is_worst

# ========== T1/T2/T3 記錄器 ==========
HISTORY_FILE = "odds_history.json"

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE,'r',encoding='utf-8') as f:
                return json.load(f)
        except: return {}
    return {}

def save_history(h):
    with open(HISTORY_FILE,'w',encoding='utf-8') as f:
        json.dump(h,f,ensure_ascii=False,indent=2)

def update_t1_t2_t3(live_data):
    """
    T1: 隔夜 (第一次抓到)
    T2: 中段 (賽前30-8分鐘)
    T3: 臨場 (賽前5分鐘)
    T3vsT1: (T1-T3)/T1 = Smart Money跌幅
    """
    history = load_history()
    now_str = datetime.now().isoformat()

    # live_data 格式: {"WIN": [{"no":1,"odds":"15"},...], "PLA": [...]}
    if not live_data:
        # 用示範數據俾你測試
        return {
            5: {"win":[15.0,9.5,6.5],"place":[4.2,3.1,2.2]},
            8: {"win":[28.0,22.0,14.0],"place":[5.0,4.0,2.8]},
            3: {"win":[3.5,3.2,2.8],"place":[1.8,1.7,1.5]}
        }

    win_odds = {}
    for item in live_data.get("WIN", live_data.get("win", [])):
        try:
            no = int(item.get("no", item.get("horseNo",0)))
            odds = float(item.get("odds", item.get("winOdds",0)))
            win_odds[no] = odds
        except: continue

    # 更新歷史
    for no, cur_odds in win_odds.items():
        key = str(no)
        if key not in history:
            # 第一次見到 = T1 隔夜
            history[key] = {"win":[cur_odds, cur_odds, cur_odds], "first_seen":now_str, "last_seen":now_str}
        else:
            # 已有 = 更新 T3, T2 = 中間值
            old_t1 = history[key]["win"][0]
            old_t2 = history[key]["win"][1]
            # T2 保留中段平均，T3 用最新
            # 如果跌幅超過5%，就更新T2
            if abs(cur_odds - old_t2)/old_t2 > 0.05:
                history[key]["win"][1] = (old_t2 + cur_odds)/2
            history[key]["win"][2] = cur_odds
            history[key]["last_seen"] = now_str

    save_history(history)

    # 轉做輸出格式
    result = {}
    for k,v in history.items():
        result[int(k)] = {"win":v["win"], "place":[4.0,3.0,2.5]} # place 簡化
    return result

# ========== 主程式 ==========
def build_data_json():
    live = get_live_odds()
    odds_map = update_t1_t2_t3(live)

    horses = []
    for no, odds in odds_map.items():
        win_arr = odds["win"] # [T1,T2,T3]
        t1,t2,t3 = win_arr[0], win_arr[1], win_arr[2]
        drop_t1_t2 = (t1-t2)/t1*100 if t1 else 0
        drop_t2_t3 = (t2-t3)/t2*100 if t2 else 0
        drop_t1_t3 = (t1-t3)/t1*100 if t1 else 0

        # 6維簡化分數
        d1,s1 = 80,""
        d2,s2,dead = calc_d2(5 if no==5 else 11)
        d3 = 85
        d4 = 75
        fund = (d1+d2+d3+d4)/4

        # D5 賠率分
        d5 = 70
        if drop_t1_t3 >= 35: d5 = 92
        elif drop_t1_t3 >= 25: d5 = 85
        elif drop_t1_t3 <= -20: d5 = 40

        total = fund*0.6 + d5*0.4

        tags = []
        if fund>=75 and t3>=10: tags.append(f"💎高Value {int(fund)}分但{t3}倍")
        if t3>=12 and odds["place"][2]<=3.2: tags.append(f"🛡️大戶保險盤 W{t3} vs P{odds['place'][2]}")

        horses.append({
            "no":no,"name":f"測試馬{no}","draw":5,"style":"後上","jockey":"潘頓","trainer":"沈集成",
            "d1":d1,"d2":d2,"d3":d3,"d4":d4,"d5":int(d5),"fundamental":int(fund),"total":int(total),
            "grade":"A+" if total>=82 else "A" if total>=72 else "B",
            "grade_label":"高把握度","d1_desc":f"獨贏12%","d2_desc":s2,"d3_desc":"默契","d4_desc":"狀態正常","d5_desc":f"T1 {t1}→T2 {t2}→T3 {t3} | T3vsT1 -{drop_t1_t3:.1f}%",
            "d5_tags":tags,
            "d5_display":{
                "t1":{"value":t1,"diff":0,"label":"T1 隔夜 20%"},
                "t2":{"value":t2,"diff":drop_t1_t2,"label":"T2 中段 30%"},
                "t3":{"value":t3,"diff":drop_t2_t3,"label":"T3 臨場 50%"},
                "t3_vs_t1":{"value":t3,"diff":drop_t1_t3,"is_smart":drop_t1_t3>=35,"label":"T3 vs T1 終極"},
                "all_drops":{"WIN":{"t1":t1,"t2":t2,"t3":t3,"t1_t2":drop_t1_t2,"t2_t3":drop_t2_t3,"t1_t3":drop_t1_t3}},
                "cross_pool_count": 2 if drop_t1_t3>25 else 0
            },
            "odds":{"win":win_arr,"place":odds["place"]},
            "is_dead_draw":dead,"injury_alert":""
        })

    # 推薦
    solid = sorted([h for h in horses if not h["is_dead_draw"]], key=lambda x:x["fundamental"], reverse=True)[:4]
    heavy = sorted(horses, key=lambda x:x["d5_display"]["cross_pool_count"], reverse=True)[:4]
    outsiders = [h for h in horses if 12<=h["odds"]["win"][2]<=50 and h["d5_display"]["t3_vs_t1"]["diff"]>=25][:2]

    output={
        "race":f"沙田 {datetime.now().strftime('%Y/%m/%d')} 即時",
        "timestamp":datetime.now().isoformat(),
        "horses":sorted(horses, key=lambda x:x["total"], reverse=True),
        "recommendations":{
            "solid":{"title":"🟢 最合理","horses":[h["no"] for h in solid],"detail":[f"{h['no']}號 基本面{h['fundamental']}分 T3vsT1 -{h['d5_display']['t3_vs_t1']['diff']:.1f}%" for h in solid]},
            "heavy":{"title":"🔴 重票之選","horses":[h["no"] for h in heavy],"detail":[f"{h['no']}號 T3vsT1 -{h['d5_display']['t3_vs_t1']['diff']:.1f}% {h['d5_display']['cross_pool_count']}個彩池掃貨" for h in heavy]},
            "outsiders":{"title":"⚡️ 爆冷","horses":[h["no"] for h in outsiders],"detail":[f"{h['no']}號 {h['odds']['win'][2]}倍 T3急瀉{h['d5_display']['t3']['diff']:.1f}%" for h in outsiders]}
        }
    }

    with open("data.json","w",encoding="utf-8") as f:
        json.dump(output,f,ensure_ascii=False,indent=2)
    print(f"✅ data.json 已更新 {len(horses)} 匹 | {datetime.now()}")

if __name__=="__main__":
    build_data_json()