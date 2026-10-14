import csv
import datetime
import math
import re
import sys
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

DEFAULT_LOG = "data/study_log.csv"
OUTPUT_DIR = Path("output")
DATE_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}")


# 「YYYY-MM-DD」の文字を日付に変える（形が違う・実在しないときは None）
def parse_date(text):
    if not DATE_PATTERN.fullmatch(text):
        return None
    try:
        return datetime.date.fromisoformat(text)
    except ValueError:
        return None


# 学習時間の文字を分（整数）に変える（数字以外・マイナス・0のときは None）
def parse_minutes(text):
    try:
        value = float(text)
    except ValueError:
        return None
    if not math.isfinite(value):
        return None
    minutes = math.floor(value)
    if minutes <= 0:
        return None
    return minutes


# コマンドの引数から、集計する週の月曜日と読むファイルを決める
def parse_args(args):
    if len(args) > 2:
        sys.exit("使い方：python weekly_report.py [日付 YYYY-MM-DD] [ファイル名]")
    if args:
        target = parse_date(args[0])
        if target is None:
            sys.exit("日付の形式が正しくありません")
    else:
        target = datetime.date.today() - datetime.timedelta(days=7)
    monday = target - datetime.timedelta(days=target.weekday())
    log_path = Path(args[1]) if len(args) == 2 else Path(DEFAULT_LOG)
    return monday, log_path


# CSVを読み、対象の週の科目ごとの合計と、スキップ・日付不正の行を集める
def read_log(log_path, monday):
    sunday = monday + datetime.timedelta(days=6)
    totals = {}
    skipped = []
    bad_dates = []
    with open(log_path, encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        next(reader, None)  # 見出し行を飛ばす
        for line_no, row in enumerate(reader, start=1):
            cells = [cell.strip() for cell in row] + ["", "", "", ""]
            if not any(cells):
                continue  # 空っぽの行は無視する
            date = parse_date(cells[0])
            if date is None:
                bad_dates.append((line_no, cells[0]))
                continue
            if not (monday <= date <= sunday):
                continue
            minutes = parse_minutes(cells[2])
            if minutes is None:
                skipped.append(line_no)
                continue
            subject = cells[1] or "未分類"
            totals[subject] = totals.get(subject, 0) + minutes
    return totals, skipped, bad_dates


# 分を「1時間30分」の形の文字にする
def format_minutes(minutes):
    return f"{minutes // 60}時間{minutes % 60}分"


# 全体に占める割合（%）を、小数第1位までの文字にする（四捨五入）
def format_percent(minutes, total):
    ratio = Decimal(minutes) * 100 / Decimal(total)
    return str(ratio.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))


# 一番多い（または少ない）時間の科目を、名前の順に並べた文字にする
def pick_subjects(totals, target_minutes):
    names = sorted(name for name, m in totals.items() if m == target_minutes)
    return f"{'と'.join(names)}（{target_minutes}分）"


# 集計結果からレポートのMarkdownの文字を作る
def build_report(monday, totals):
    sunday = monday + datetime.timedelta(days=6)
    total = sum(totals.values())
    lines = [
        f"# 週間学習レポート（{monday} 〜 {sunday}）",
        "",
        "## 総学習時間",
        "",
        f"{total}分（{format_minutes(total)}）",
        "",
        "## 科目ごとの学習時間",
        "",
        "| 科目名 | 学習時間（分） | 時間換算 | 割合（%） |",
        "|---|---|---|---|",
    ]
    for name in sorted(totals):
        minutes = totals[name]
        lines.append(f"| {name} | {minutes} | {format_minutes(minutes)} "
                     f"| {format_percent(minutes, total)} |")
    lines += [
        "",
        "## 最も時間を割いた科目",
        "",
        pick_subjects(totals, max(totals.values())),
        "",
        "## 最も少なかった科目",
        "",
        pick_subjects(totals, min(totals.values())),
        "",
    ]
    return "\n".join(lines)


# 日付の警告とスキップした行を、ターミナルに表示する
def print_problems(skipped, bad_dates):
    for line_no, text in bad_dates:
        print(f"警告：{line_no}行目の日付「{text}」が正しくないため、無視しました")
    if skipped:
        numbers = ", ".join(f"{n}行目" for n in skipped)
        print(f"スキップ：{len(skipped)}件（{numbers}）")


# 全体の流れ：引数を読み、集計して、レポートを保存する
def main():
    monday, log_path = parse_args(sys.argv[1:])
    if not log_path.is_file():
        sys.exit(f"{log_path.as_posix()} が見つかりません")
    totals, skipped, bad_dates = read_log(log_path, monday)
    print_problems(skipped, bad_dates)
    if not totals:
        sys.exit("ログデータが存在しません")
    OUTPUT_DIR.mkdir(exist_ok=True)
    report_path = OUTPUT_DIR / f"weekly_report_{monday}.md"
    report_path.write_text(build_report(monday, totals), encoding="utf-8")
    print(f"レポートを作成しました：{report_path.as_posix()}")


if __name__ == "__main__":
    main()
