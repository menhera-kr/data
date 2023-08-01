import os
import json
import io

import requests
import pandas as pd

def origin_data_csv_to_json():
    response = requests.get("https://cdn.zeroday0619.dev/repo/open/csv/MHPDI_DATA_20220301.csv")
    df = pd.read_csv(io.StringIO(response.text), sep=",", encoding="utf-8") 
    df = df.fillna('')

    origin = []
    for i in df.index:
        origin_cast = dict()
        if (
            (
            df.loc[i, "기관구분"] == "의원"
            ) or (
            df.loc[i, "기관구분"] == "병원"
            ) or (
            df.loc[i, "기관구분"] == "종합병원"
            ) or (
            df.loc[i, "기관구분"] == "상급종합병원"
            ) or (
            df.loc[i, "기관구분"] == "광역정신건강복지센터"
            ) or (
            df.loc[i, "기관구분"] == "기초정신건강복지센터"
            )
        ):
            origin_cast["기관명"] = df.loc[i, "기관명"]
            origin_cast["기관구분"] = df.loc[i, "기관구분"]
            origin_cast["주소"] = df.loc[i, "주소"]
            origin_cast["홈페이지"] = df.loc[i, "홈페이지"]
            origin.append(origin_cast)
    origin.sort(key=lambda x: x["주소"].split(" ")[0])

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(origin, f, ensure_ascii=False, indent=4)

def ncp_geocoding(address: str):
    url = "https://naveropenapi.apigw.ntruss.com/map-geocode/v2/geocode"
    params = {
        "query": address,
    }
    headers = {
        "X-NCP-APIGW-API-KEY-ID": os.getenv("NCP_API_KEY_ID"),
        "X-NCP-APIGW-API-KEY": os.getenv("NCP_API_KEY"),
    }

    resp = requests.get(url, params=params, headers=headers)
    response = resp.json()
    print(response["status"])
    try:
        return response["addresses"][0]
    except IndexError:
        print(address)
        raise IndexError



def preprocessor():
    data = dict()
    with open("data.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    
    preprocessed = []

    for i in range(len(data)):
        try:
            data[i]["주소"] =  {
                "위도": ncp_geocoding(data[i]["주소"])["y"],
                "경도": ncp_geocoding(data[i]["주소"])["x"],
            }
        except IndexError:
            pass
    print(json.dumps(data, ensure_ascii=False, indent=4))
    with open("data_preprocessed.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def self_preprocessor():
    data = dict()
    with open("data_preprocessed.json", "r+", encoding="utf-8") as f:
        data = json.load(f)
        for i in range(len(data)):
            if not isinstance(data[i]["주소"], dict):
                print(data[i]["기관명"])
                print(data[i]["주소"])
                data[i]["주소"] = input("수정된 주소를 입력해주세요: ")
                try:
                    data[i]["주소"] =  {
                        "위도": ncp_geocoding(data[i]["주소"])["y"],
                        "경도": ncp_geocoding(data[i]["주소"])["x"],
                    }
                except IndexError:
                    print("주소를 찾을 수 없습니다.")
                print()
        f.seek(0)
        json.dump(data, f, ensure_ascii=False, indent=4)
        f.truncate()


if __name__ == "__main__":
    self_preprocessor()