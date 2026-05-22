"""
TourAPI 전국 관광지 마스터 데이터 수집
- 목적: 관광지 위경도·카테고리·행정구역 확보 (레이어 4 기준 마스터)
- API: 한국관광공사 TourAPI v2
- 출력: tour_master.csv (관광지 전체 목록)
"""

import requests
import pandas as pd
import time
import os
from urllib.parse import quote

# ── 설정 ──────────────────────────────────────────────
SERVICE_KEY = os.environ.get("TOUR_API_KEY", "YOUR_API_KEY_HERE")
# 환경변수로 설정 권장: export TOUR_API_KEY="발급받은키"

BASE_URL = "http://apis.data.go.kr/B551011/KorService1"

# 관광지 콘텐츠 타입 (필요한 것만 선택)
CONTENT_TYPES = {
    12: "관광지",
    14: "문화시설",
    15: "축제공연행사",
    25: "여행코스",
    28: "레포츠",
    32: "숙박",
    38: "쇼핑",
    39: "음식점",
}

# 수집 대상 (관광지 + 문화시설 중심)
TARGET_TYPES = [12, 14, 28]  # 관광지, 문화시설, 레포츠

# ── 함수 ──────────────────────────────────────────────

def get_area_based_list(content_type_id: int, page_no: int = 1, num_of_rows: int = 1000) -> dict:
    """지역기반 관광정보 조회"""
    url = f"{BASE_URL}/areaBasedList1"
    params = {
        "serviceKey": SERVICE_KEY,
        "numOfRows": num_of_rows,
        "pageNo": page_no,
        "MobileOS": "ETC",
        "MobileApp": "TourRecommender",
        "_type": "json",
        "listYN": "Y",
        "arrange": "A",          # 제목순
        "contentTypeId": content_type_id,
    }
    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


def collect_all_by_type(content_type_id: int) -> list[dict]:
    """특정 콘텐츠 타입 전체 페이지 수집"""
    print(f"\n[{CONTENT_TYPES[content_type_id]}] 수집 시작...")
    
    # 1페이지로 전체 건수 파악
    first = get_area_based_list(content_type_id, page_no=1, num_of_rows=1000)
    body = first["response"]["body"]
    total_count = int(body["totalCount"])
    num_of_rows = 1000
    total_pages = (total_count + num_of_rows - 1) // num_of_rows
    
    print(f"  총 {total_count}건 / {total_pages}페이지")
    
    items = []
    for page in range(1, total_pages + 1):
        try:
            data = get_area_based_list(content_type_id, page_no=page, num_of_rows=num_of_rows)
            page_items = data["response"]["body"]["items"]
            if not page_items:
                break
            item_list = page_items.get("item", [])
            if isinstance(item_list, dict):   # 1건일 때 dict로 오는 경우 처리
                item_list = [item_list]
            items.extend(item_list)
            print(f"  페이지 {page}/{total_pages} 완료 ({len(item_list)}건)")
            time.sleep(0.3)  # API 부하 방지
        except Exception as e:
            print(f"  페이지 {page} 오류: {e}")
            time.sleep(1)
    
    return items


def enrich_with_detail(content_id: str, content_type_id: int) -> dict:
    """공통정보조회 — 전화번호, 운영시간 등 추가 정보"""
    url = f"{BASE_URL}/detailCommon1"
    params = {
        "serviceKey": SERVICE_KEY,
        "contentId": content_id,
        "contentTypeId": content_type_id,
        "MobileOS": "ETC",
        "MobileApp": "TourRecommender",
        "_type": "json",
        "defaultYN": "Y",
        "firstImageYN": "Y",
        "areacodeYN": "Y",
        "catcodeYN": "Y",
        "addrinfoYN": "Y",
        "mapinfoYN": "Y",
        "overviewYN": "N",  # 개요는 용량 커서 제외
    }
    resp = requests.get(url, params=params, timeout=15)
    data = resp.json()
    items = data["response"]["body"]["items"]
    if not items:
        return {}
    item = items["item"]
    if isinstance(item, list):
        item = item[0]
    return item


# ── 메인 수집 ──────────────────────────────────────────

def main():
    all_items = []
    
    for ct_id in TARGET_TYPES:
        items = collect_all_by_type(ct_id)
        for item in items:
            item["content_type_name"] = CONTENT_TYPES[ct_id]
        all_items.extend(items)
    
    print(f"\n전체 수집 완료: {len(all_items)}건")
    
    # DataFrame 변환
    df = pd.DataFrame(all_items)
    
    # 핵심 컬럼만 정리
    keep_cols = {
        "contentid": "content_id",
        "contenttypeid": "content_type_id",
        "content_type_name": "content_type_name",
        "title": "name",
        "addr1": "address",
        "addr2": "address_detail",
        "areacode": "area_code",
        "sigungucode": "sigungu_code",
        "cat1": "cat1",
        "cat2": "cat2",
        "cat3": "cat3",
        "mapx": "longitude",
        "mapy": "latitude",
        "tel": "tel",
        "firstimage": "image_url",
        "createdtime": "created_time",
        "modifiedtime": "modified_time",
    }
    
    # 존재하는 컬럼만 선택
    available = {k: v for k, v in keep_cols.items() if k in df.columns}
    df = df[list(available.keys())].rename(columns=available)
    
    # 위경도 숫자 변환
    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
    
    # 위경도 없는 것 제거 (KDTree 매칭에 필수)
    before = len(df)
    df = df.dropna(subset=["latitude", "longitude"])
    print(f"위경도 없는 항목 제거: {before - len(df)}건 → 최종 {len(df)}건")
    
    # 저장
    output_path = "tour_master.csv"
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"\n✅ 저장 완료: {output_path}")
    print(df.head())
    print(f"\n컬럼: {list(df.columns)}")
    print(f"콘텐츠 타입 분포:\n{df['content_type_name'].value_counts()}")
    print(f"시도 코드 분포:\n{df['area_code'].value_counts().head(20)}")
    
    return df


if __name__ == "__main__":
    df = main()
