"""
tide736.net から二色浜(代用: 岸和田)の潮汐データを取得し、
tide_data.json としてまとめて保存するスクリプト。

CORSの制約を受けないよう、GitHub Actions上(サーバー側)から実行する前提。
index.html はこの tide_data.json を同一オリジンから読み込むだけにする。
"""

import json
import datetime
import time
import requests

TIDE_PC = 27   # 大阪府
TIDE_HC = 3    # 岸和田(二色浜の代用)
DAYS_AHEAD = 20  # サイト側のforecast_days(16)より少し余裕を持たせる
URL = "https://api.tide736.net/get_tide.php"

OUT_PATH = "tide_data.json"


def date_key(d: datetime.date) -> str:
    return d.strftime("%Y-%m-%d")


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
}


def fetch_day(d: datetime.date):
    params = {
        "pc": TIDE_PC, "hc": TIDE_HC,
        "yr": d.year, "mn": d.month, "dy": d.day,
        "rg": "day",
    }
    resp = requests.get(URL, params=params, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    if data.get("status") != 1:
        print(f"  {d.isoformat()}: 取得失敗 ({data.get('message', '不明')})")
        return None
    key = date_key(d)
    return data["tide"]["chart"].get(key)


def main():
    today = datetime.date.today()
    result = {}

    for offset in range(DAYS_AHEAD):
        d = today + datetime.timedelta(days=offset)
        print(f"取得中: {d.isoformat()}")
        try:
            chart = fetch_day(d)
            if chart is not None:
                result[date_key(d)] = chart
        except Exception as e:
            print(f"  失敗: {e}")
        time.sleep(1)  # サーバー負荷への配慮

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False)

    print(f"\n保存完了: {OUT_PATH} ({len(result)}日分)")


if __name__ == "__main__":
    main()
