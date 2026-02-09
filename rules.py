import re
import difflib
from normalize import normalize_text, normalize_lines

# 중량 숫자 + kg 단위(OCR 오탈자 포함) 패턴
KG_RE = re.compile(
    r'([0-9OoIl]{1,3}(?:[,\s][0-9OoIl]{3})+|[0-9OoIl]+)\s*(?:k\s*[\-\.]?\s*[g9]|㎏)',
    re.IGNORECASE
)

# 날짜 패턴(YYYY-MM-DD / YYYY.MM.DD / YYYY/MM/DD)
DATE_RE = re.compile(r'(\d{4})[./-](\d{1,2})[./-](\d{1,2})')

# 좌표 형식(issuer 오인 방지용)
COORD_RE = re.compile(r'^\s*-?\d{1,3}\.\d+\s*,\s*(-?\d{1,3}\.\d+)\s*$')

# 문서 타입 후보 목록
DOC_TYPE_KEYWORDS = ["계량증명서", "계량확인서", "계근표"]

# 문자열 유사도 계산
def similarity(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, a, b).ratio()

# 문서 앞부분 기준 문서 타입 추정
def detect_doc_type(text: str):
    compact = normalize_text(text)
    head = compact[:10]

    best, score = None, 0.0
    for kw in DOC_TYPE_KEYWORDS:
        kw_n = normalize_text(kw)
        if kw_n in head:
            return kw
        s = similarity(head, kw_n)
        if s > score:
            best, score = kw, s
    return best

# 라벨이 포함된 줄에서 라벨 뒤 값 추출
def find_after_label(text: str, labels: list):
    label_norms = [normalize_text(l) for l in labels]

    for ln in normalize_lines(text):
        ln_norm = normalize_text(ln)
        if any(l in ln_norm for l in label_norms):
            if ":" in ln:
                return ln.split(":", 1)[1].strip()
            if "：" in ln:
                return ln.split("：", 1)[1].strip()
            for lab in labels:
                if lab in ln:
                    return ln.replace(lab, "").strip()
            return ln.strip()
    return None

# 차량번호 형식 추출
def parse_vehicle_no(s):
    if not s:
        return None
    s = s.replace(" ", "")
    m = re.search(r'([0-9]{2,3}[가-힣][0-9]{4}|[0-9]{4,})', s)
    return m.group(1) if m else None

# 'OOO 귀하' 형태에서 거래처 추출
def customer_from_gwiha(text: str):
    for ln in normalize_lines(text):
        if "귀하" in ln:
            return ln.split("귀하")[0].strip()
    return None

# 휴리스틱 기반 발급기관 추정
def guess_issuer(text: str):
    for ln in normalize_lines(text):
        if "(주)" in ln or "주)" in ln:
            return ln.strip()

    noise = ["TEL", "FAX", "증명", "확인", "계량", "차량", "거래", "상호", "ID", "NO", "kg"]
    for ln in reversed(normalize_lines(text)):
        if DATE_RE.search(ln):
            continue
        if COORD_RE.match(ln):
            continue
        if any(n.lower() in ln.lower() for n in noise):
            continue
        digits = sum(c.isdigit() for c in ln)
        if digits / max(len(ln), 1) >= 0.35:
            continue
        if 2 <= len(ln) <= 30:
            return ln
    return None
