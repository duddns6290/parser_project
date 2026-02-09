import re

# OCR 숫자 오탈자(O→0, l/I→1) 보정 후 정수 변환
def normalize_int(num_str: str) -> int:
    s = (num_str or "").translate({
        ord("O"): "0", ord("o"): "0",
        ord("I"): "1", ord("i"): "1",
        ord("l"): "1",
    })
    s = re.sub(r'[,\s]', '', s)
    s = re.sub(r'[^0-9]', '', s)
    return int(s)

# OCR 텍스트를 줄 단위로 정리(빈 줄 제거)
def normalize_lines(text: str):
    return [ln.strip() for ln in text.splitlines() if ln.strip()]

# 라벨 비교용 텍스트 정규화(소문자, 기호 제거)
def normalize_text(s: str) -> str:
    if not s:
        return ""
    return re.sub(r'[^0-9a-z가-힣]', '', s.lower())

# 회사명 공백 및 '(주)' 표기 정규화
def normalize_company_spacing(s: str) -> str:
    if not s:
        return s

    s = re.sub(r'\(\s*주\s*\)', '(주)', s.strip())

    prev = None
    while prev != s:
        prev = s
        s = re.sub(r'([가-힣A-Za-z])\s+([가-힣A-Za-z])', r'\1\2', s)

    return s
