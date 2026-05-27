# layer1_clean/clean_rules.py
# 清洗規則庫 — 遇到新的髒資料就在這裡加規則
# 所有規則都是純函數（輸入字串 → 輸出乾淨字串）
# 供 excel_cleaner.py 呼叫，不直接執行

import re

# ===== 1. 基本字串清洗 =====

def clean_str(v) -> str:
    """去掉首尾空白、None/NaN 轉空字串"""
    if v is None:
        return ""
    import pandas as pd
    if pd.isna(v):
        return ""
    return str(v).strip()


def clean_str_fullwidth(v) -> str:
    """全形轉半形（數字、英文、空格）"""
    s = clean_str(v)
    result = []
    for ch in s:
        code = ord(ch)
        # 全形英數：FF01~FF5E → 對應半形 21~7E
        if 0xFF01 <= code <= 0xFF5E:
            result.append(chr(code - 0xFEE0))
        # 全形空格
        elif code == 0x3000:
            result.append(' ')
        else:
            result.append(ch)
    return ''.join(result).strip()


# ===== 2. 名稱清洗 =====

# 台灣縣市名稱清單（用來去除名稱前綴）
COUNTY_NAMES = [
    "臺北市", "台北市", "新北市", "桃園市", "臺中市", "台中市",
    "臺南市", "台南市", "高雄市", "基隆市", "新竹市", "嘉義市",
    "新竹縣", "苗栗縣", "彰化縣", "南投縣", "雲林縣", "嘉義縣",
    "屏東縣", "宜蘭縣", "花蓮縣", "臺東縣", "台東縣",
    "澎湖縣", "金門縣", "連江縣",
]

# 行政區後綴（去縣市之後還要去的區名前綴）
DISTRICT_PATTERN = re.compile(r'^.{2,4}[區鎮市鄉]')

def clean_name_prefix(v) -> str:
    """
    去掉名稱前面的縣市區前綴。
    例：「臺北市中正區螢橋國小」→「螢橋國小」
    例：「新北市立三峽幼兒園」→「三峽幼兒園」（去縣市後「立」也去掉？不處理，保留）
    """
    s = clean_str(v)
    # 先去縣市
    for county in COUNTY_NAMES:
        if s.startswith(county):
            s = s[len(county):]
            break
    # 再去行政區（如「中正區」「板橋區」）
    m = DISTRICT_PATTERN.match(s)
    if m:
        s = s[m.end():]
    return s.strip()


# ===== 3. 縣市區清洗 =====

# 縣市名稱標準化對照（簡寫→標準名）
COUNTY_NORMALIZE = {
    "台北":  "臺北市",
    "台北市": "臺北市",
    "新北":  "新北市",
    "桃園":  "桃園市",
    "台中":  "臺中市",
    "台中市": "臺中市",
    "台南":  "臺南市",
    "台南市": "臺南市",
    "高雄":  "高雄市",
}

def clean_county(v) -> str:
    """縣市名稱標準化，台→臺，去掉多餘空白"""
    s = clean_str(v)
    # 查對照表
    if s in COUNTY_NORMALIZE:
        return COUNTY_NORMALIZE[s]
    # 一律台→臺（台北市→臺北市）
    s = s.replace("台北", "臺北").replace("台中", "臺中").replace("台南", "臺南").replace("台東", "臺東")
    return s


# ===== 4. 電話清洗 =====

def clean_phone(v) -> str:
    """
    電話號碼清洗：
    - 去掉全形字元
    - 統一分隔符號為 -
    - 去掉多餘空白
    - 保留分機（例：02-1234-5678#123）
    """
    s = clean_str_fullwidth(v)
    if not s:
        return ""
    # 去掉空白
    s = s.replace(" ", "").replace("　", "")
    # 統一分隔符：／/ 都改成 -
    s = s.replace("/", "-").replace("／", "-").replace("~", "-")
    # 去掉連續的 -
    s = re.sub(r'-+', '-', s)
    # 去掉開頭結尾的 -
    s = s.strip('-')
    return s


# ===== 5. 地址清洗 =====

# 去掉常見的前綴編碼（例：「[01]」「[234]」）
ADDRESS_PREFIX_PATTERN = re.compile(r'^\[\d+\]')

def clean_address(v) -> str:
    """
    地址清洗：
    - 去掉 [01] 這類前綴編碼
    - 全形轉半形
    - 去掉首尾空白
    """
    s = clean_str_fullwidth(v)
    # 去前綴碼
    s = ADDRESS_PREFIX_PATTERN.sub("", s).strip()
    return s


# ===== 6. Email 清洗 =====

def clean_email(v) -> str:
    """Email 清洗：轉小寫、去空白"""
    s = clean_str(v)
    return s.lower().strip()


# ===== 7. 網址清洗 =====

def clean_url(v) -> str:
    """
    網址清洗：
    - 去空白
    - 過濾掉 http:// 或 https:// 這種空網址
    """
    s = clean_str(v)
    if s in ("http://", "https://", "http", "https"):
        return ""
    return s
