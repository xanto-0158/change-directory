import csv
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent
INPUT_FILE = BASE_DIR / "data" / "mock_results.csv"
OUTPUT_FILE = BASE_DIR / "output" / "review_list.csv"
COLUMNS = ["exam", "date", "subject", "question", "unit", "full", "score", "reason", "done"]
REASONS = ["計算ミス", "知識不足", "読み間違い", "時間不足", "その他"]
DONE_MARK = "★"
TOP_COUNT = 10


# 文字を0以上の整数に変える（空欄・数字以外・マイナスのときは None）
def parse_points(text):
    try:
        value = int(text)
    except ValueError:
        return None
    if value < 0:
        return None
    return value


# CSV を読み込んで行のリストを返す（ファイルがない・列が足りないときは終了する）
def read_rows(path):
    if not path.exists():
        print("data/mock_results.csv が見つかりません")
        sys.exit(1)
    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        missing = [name for name in COLUMNS if name not in (reader.fieldnames or [])]
        if missing:
            print(f"列が足りません：{', '.join(missing)}")
            sys.exit(1)
        return list(reader)


# 1行を調べて問題の情報を返す（使えない行は理由を表示して None を返す）
def check_row(row, line):
    item = {name: (row.get(name) or "").strip() for name in COLUMNS}
    full = parse_points(item["full"])
    score = parse_points(item["score"])
    if full is None or score is None:
        print(f"{line}行目：配点か得点が数字ではないので飛ばします")
        return None
    if score > full:
        print(f"{line}行目：得点が配点より大きいので飛ばします（入力ミス？）")
        return None
    item["loss"] = full - score
    if item["loss"] == 0:
        return item
    if item["reason"] not in REASONS:
        print(f"{line}行目：理由「{item['reason']}」は選択肢にないので「その他」にします")
        item["reason"] = "その他"
    if item["done"] not in ("", DONE_MARK):
        print(f"{line}行目：done の「{item['done']}」は★ではないので未復習にします")
        item["done"] = ""
    return item


# 復習が必要な問題のリストと、復習済み（★）の件数を集める
def collect_items(rows):
    todo = []
    done_count = 0
    for index, row in enumerate(rows):
        item = check_row(row, index + 2)  # 1行目は列名なので、データは2行目から
        if item is None or item["loss"] == 0:
            continue
        if item["done"] == DONE_MARK:
            done_count += 1
        else:
            todo.append(item)
    return todo, done_count


# 失点が大きい順、失点が同じなら日付が新しい順に並べる
def sort_items(items):
    return sorted(items, key=lambda item: (item["loss"], item["date"]), reverse=True)


# 要復習リストを CSV に保存する
def write_list(items, path):
    path.parent.mkdir(exist_ok=True)
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["順位", "教科", "単元", "問題", "模試名", "失点", "理由"])
        for rank, item in enumerate(items, start=1):
            writer.writerow([rank, item["subject"], item["unit"], item["question"],
                             item["exam"], item["loss"], item["reason"]])


# 上位の問題・復習の進み具合・理由ごとの件数を画面に表示する
def show_summary(items, done_count):
    if not items:
        print("復習が必要な問題はありません")
    else:
        print(f"【要復習リスト 上位{TOP_COUNT}件】")
        for rank, item in enumerate(items[:TOP_COUNT], start=1):
            print(f"{rank:>2}. [{item['subject']}] {item['unit']} {item['question']}"
                  f"（{item['exam']}） 失点 {item['loss']} ・{item['reason']}")
    print()
    print(f"復習済み（★）：{done_count}件 / 残り：{len(items)}件")
    print("【理由ごとの件数（残りの問題）】")
    for reason in REASONS:
        count = sum(1 for item in items if item["reason"] == reason)
        print(f"  {reason}：{count}件")


# 全体の流れ：読む → 調べる → 並べる → 保存・表示
def main():
    rows = read_rows(INPUT_FILE)
    items, done_count = collect_items(rows)
    items = sort_items(items)
    write_list(items, OUTPUT_FILE)
    show_summary(items, done_count)
    print()
    print("output/review_list.csv に保存しました")


if __name__ == "__main__":
    main()
