"""
tide736.net から複数スポット分の潮汐データを取得し、
tide_data.json としてまとめて保存するスクリプト。

出力形式: { "pcの値_hcの値": { "YYYY-MM-DD": {...潮汐データ...}, ... }, ... }
index.html 側は `${SPOTS[currentSpot].tidePc}_${SPOTS[currentSpot].tideHc}` を
キーとして参照する(hc番号は都道府県ごとに独立して振られているため、
pcとhcを組み合わせてキー化することで将来の衝突を防いでいる)。

CORSの制約を受けないよう、GitHub Actions上(サーバー側)から実行する前提。
"""

import json
import datetime
import time
import requests

# 取得対象の港。(pc, hc): 表示用ラベル(ログ用)
HARBORS = {
    (27, 3): "岸和田(二色浜の代用)",
    (27, 1): "深日(岬町)",
    (30, 11): "和歌山(浜の宮の代用)",
}
DAYS_AHEAD = 20  # サイト側のforecast_days(16)より少し余裕を持たせる
URL = "https://api.tide736.net/get_tide.php"

OUT_PATH = "tide_data.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
}


def date_key(d: datetime.date) -> str:
    return d.strftime("%Y-%m-%d")


def fetch_day(pc: int, hc: int, d: datetime.date):
    params = {
        "pc": pc, "hc": hc,
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


def fetch_harbor(pc: int, hc: int, label: str) -> dict:
    today = datetime.date.today()
    result = {}
    for offset in range(DAYS_AHEAD):
        d = today + datetime.timedelta(days=offset)
        print(f"取得中[{label} pc={pc} hc={hc}]: {d.isoformat()}")
        try:
            chart = fetch_day(pc, hc, d)
            if chart is not None:
                result[date_key(d)] = chart
        except Exception as e:
            print(f"  失敗: {e}")
        time.sleep(1)  # サーバー負荷への配慮
    return result


def main():
    all_result = {}
    for (pc, hc), label in HARBORS.items():
        key = f"{pc}_{hc}"
        all_result[key] = fetch_harbor(pc, hc, label)

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(all_result, f, ensure_ascii=False)

    for key, data in all_result.items():
        print(f"{key}: {len(data)}日分")
    print(f"\n保存完了: {OUT_PATH}")


if __name__ == "__main__":
    main()
