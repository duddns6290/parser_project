import re
from normalize import normalize_int, normalize_company_spacing
from rules import (
    KG_RE, DATE_RE,
    detect_doc_type, find_after_label,
    parse_vehicle_no, customer_from_gwiha, guess_issuer
)

# OCR JSON 구조에서 텍스트 추출
def pick_text(obj: dict) -> str:
    if obj.get("pages") and obj["pages"][0].get("text"):
        return obj["pages"][0]["text"]
    return obj.get("text", "")

# 계근지/계량증명서 OCR 결과 파싱 메인 함수
def parse_weigh_ticket(obj: dict) -> dict:
    raw = pick_text(obj)
    text = re.sub(r'[ ]{2,}', ' ', raw.replace("\t", " "))

    result = {
        "doc_type": detect_doc_type(text),
        "weigh_date": None,
        "vehicle_no": None,
        "customer": None,
        "issuer": None,
        "gross_kg": None,
        "tare_kg": None,
        "net_kg": None,
        "validation": {"net_equals_gross_minus_tare": None, "errors": []},
    }

    # 계량일자 추출
    date_part = find_after_label(text, ["계량일자", "날짜", "일시"])
    dm = DATE_RE.search(date_part or text)
    if dm:
        y, m, d = dm.groups()
        result["weigh_date"] = f"{y}-{int(m):02d}-{int(d):02d}"

    # 차량번호 추출
    veh = find_after_label(text, ["차량번호", "차번호", "차량No", "차량NO"])
    result["vehicle_no"] = parse_vehicle_no(veh)

    # 거래처 추출
    cust = find_after_label(text, ["거래처", "상호"]) or customer_from_gwiha(text)
    if cust:
        result["customer"] = cust.strip()

    # 발급기관 추정
    issuer = guess_issuer(text)
    if issuer:
        result["issuer"] = normalize_company_spacing(issuer)

    # 실중량 추출
    net = find_after_label(text, ["실중량"])
    if net:
        m = KG_RE.search(net)
        if m:
            result["net_kg"] = normalize_int(m.group(1))

    # 중량 조합 추론(gross/tare/net)
    weights = [normalize_int(m.group(1)) for m in KG_RE.finditer(text)]
    uniq = sorted(set(weights), reverse=True)

    if result["net_kg"] is None and len(uniq) >= 3:
        g, t, n = uniq[:3]
        if g - t == n:
            result["gross_kg"], result["tare_kg"], result["net_kg"] = g, t, n
    elif result["net_kg"] is not None:
        rest = [w for w in uniq if w != result["net_kg"]]
        if len(rest) >= 2:
            result["gross_kg"], result["tare_kg"] = rest[:2]

    # 중량 검증
    if all(result[k] is not None for k in ("gross_kg", "tare_kg", "net_kg")):
        ok = result["gross_kg"] - result["tare_kg"] == result["net_kg"]
        result["validation"]["net_equals_gross_minus_tare"] = ok
        if not ok:
            result["validation"]["errors"].append("net != gross - tare")
    else:
        result["validation"]["errors"].append("missing_weight_fields")

    return result
