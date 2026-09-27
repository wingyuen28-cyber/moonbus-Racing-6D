import requests, json, re
from datetime import datetime

def get_today_races():
    date_str = datetime.now().strftime("%Y-%m-%d")
    # 香港馬會公開賽日表
    url = f"https://bet.hkjc.com/racing/pages/odds_wp.aspx?lang=ch&date={date_str}"
    headers = {"User-Agent":"Mozilla/5.0","Referer":"https://bet.hkjc.com/"}
    try:
        r = requests.get(url, headers=headers, timeout=15)
        # 用正則數有幾多場
        race_count = len(re.findall(r'Race (\d+)', r.text))
        if race_count == 0:
            race_count = 10 # 預設10場
        races=[]
        for i in range(1, race_count+1):
            horses=[]
            # 暫時每場14匹，等賠率接口有數據會覆蓋真馬名
            for j in range(1,15):
                horses.append({
                    "no":j,"name":f"待定{i}-{j}","draw":j,"jockey":"待定","trainer":"待定",
                    "weight":126,"age":4,"gear":"--","last6":"--",
                    "fund":70,"total":70,"grade":"B","t1":10.0,"t2":10.0,"t3":10.0,"drop":0,"smart":False
                })
            races.append({"race_no":i,"venue":"ST","distance":1200,"class":"待定","track":"好地","horses":horses})
        return races
    except:
        return None

def main():
    races = get_today_races()
    if not races:
        # 冇賽日就顯示10場示範
        races=[]
        for i in range(1,11):
            races.append({"race_no":i,"venue":"ST","distance":1200 if i%2==0 else 1400,"class":"3","track":"好地","horses":[
                {"no":1,"name":f"示範馬{i}-1","draw":1,"jockey":"潘頓","trainer":"沈集成","weight":133,"age":5,"gear":"B","last6":"1-1-2","fund":85,"total":85,"grade":"A","t1":5.0,"t2":4.5,"t3":4.0,"drop":20,"smart":False},
                {"no":2,"name":f"示範馬{i}-2","draw":2,"jockey":"田泰安","trainer":"呂健威","weight":126,"age":4,"gear":"--","last6":"2-1-1","fund":88,"total":88,"grade":"A+","t1":15,"t2":9.5,"t3":6.5,"drop":56.6,"smart":True}
            ]})

    final={"updated":datetime.now().strftime("%Y-%m-%d %H:%M"),"races":races,"race_count":len(races)}
    with open("data.json","w",encoding="utf-8") as f:
        json.dump(final,f,ensure_ascii=False,indent=2)
    print(f"完成 {len(races)} 場")

if __name__=="__main__":
    main()