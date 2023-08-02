import os
import httpx
import json
import io
import time
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

def sort_data():
    data = dict()
    with open("data_preprocessed2.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    data.sort(key=lambda x: x["주소"]["area1"])
    with open("data_preprocessed2.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

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

def ncp_reverse_geocoding(lat: float, lng: float):
    url = "https://naveropenapi.apigw.ntruss.com/map-reversegeocode/v2/gc"
    params = {
        "request": "coordsToaddr",
        "coords": f"{lng},{lat}",
        "sourcecrs": "epsg:4326",
        "output": "json",
        "orders": "legalcode"
    }
    headers = {
        "X-NCP-APIGW-API-KEY-ID": os.getenv("NCP_REVERSE_GEO_API_KEY_ID"),
        "X-NCP-APIGW-API-KEY": os.getenv("NCP_REVERSE_GEO_API_KEY"),
    }
    with httpx.Client(
        headers=headers,
        transport=httpx.HTTPTransport(retries=100),
    ) as req:
        resp = req.get(url, params=params)
    resp_json = resp.json()
    print(resp_json["status"]["name"])
    print(resp_json["status"]["message"])

    area1 = resp_json["results"][0]["region"]["area1"]["name"]
    area2 = resp_json["results"][0]["region"]["area2"]["name"]
    area3 = resp_json["results"][0]["region"]["area3"]["name"]

    return {
        "area1": area1,
        "area2": area2,
        "area3": area3,
    }



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

def preprocessor2():
    data = dict()
    with open("data_preprocessed.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    
    for i in range(len(data)):
        time.sleep(0.5)
        try:
            print(data[i]["주소"]["위도"],data[i]["주소"]["경도"])
            resp = ncp_reverse_geocoding(data[i]["주소"]["위도"],data[i]["주소"]["경도"])
            data[i]["주소"].update(resp)
        except IndexError:
            pass
    print(json.dumps(data, ensure_ascii=False, indent=4))
    with open("data_preprocessed2.json", "w", encoding="utf-8") as f:
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

def sort_slice_data():
    data = dict()
    with open("data_preprocessed2.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    dictionary = []
    # 행정구역별로 나누기
    for i in range(len(data)):
        if data[i]["주소"]["area1"] not in dictionary:
            dictionary.append(data[i]["주소"]["area1"])
    sliceed = []
    for i in range(len(dictionary)):
        data_sliced = []
        for index in range(len(data)):
            if data[index]["주소"]["area1"] == dictionary[i]:
                data_sliced.append(data[index])
        sliceed.append(data_sliced)
    
    print(len(sliceed))
    for nx in range(len(sliceed)):
        print(sliceed[nx][0]["주소"]["area1"])
        with open(f"data_preprocessed2_{sliceed[nx][0]['주소']['area1']}.json", "w", encoding="utf-8") as f:
            json.dump(sliceed[nx], f, ensure_ascii=False, indent=4)

        


if __name__ == "__main__":
    sort_slice_data()