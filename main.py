import json
from pathlib import Path
from parser import parse_weigh_ticket

# OCR 샘플 폴더를 순회하며 파싱 결과 저장
def run_folder(samples_dir="[2026 ICT_리코] smaple_data_ocr", out_json="output/result.json"):
    results = []
    for fp in sorted(Path(samples_dir).glob("*.json")):
        if fp.name.startswith("._"):
            continue
        obj = json.loads(fp.read_text(encoding="utf-8"))
        results.append({"file": fp.name, "parsed": parse_weigh_ticket(obj)})

    Path(out_json).parent.mkdir(parents=True, exist_ok=True)
    Path(out_json).write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"saved: {out_json}")

if __name__ == "__main__":
    run_folder()
