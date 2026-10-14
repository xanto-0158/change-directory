import csv
import os
import random

WORDS_PATH = os.path.join("data", "words.csv")
MISTAKES_PATH = os.path.join("output", "mistakes.csv")
COLUMNS = ["level", "word", "reading", "meaning"]
LEVEL_NAMES = {"1": "小学生", "2": "中学生", "3": "高校生", "4": "大学生"}
QUESTION_COUNT = 5


# 単語リストを読み込み、正しい行だけをリストにして返す
def load_words(path):
    words = []
    with open(path, encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        for row in reader:
            values = [(row.get(name) or "").strip() for name in COLUMNS]
            if "" in values or values[0] not in LEVEL_NAMES:
                print(f"{reader.line_num}行目は形がおかしいので飛ばしました")
                continue
            words.append(dict(zip(COLUMNS, values)))
    return words


# 間違えた単語の記録を読み込む（ファイルが無ければ空のリスト）
def load_mistakes(path):
    if not os.path.exists(path):
        return []
    return load_words(path)


# 間違えた単語の記録をファイルに書き込む
def save_mistakes(path, mistakes):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(mistakes)


# モードの番号（1〜5）を、正しく入力されるまで聞く
def ask_mode():
    print("英単語 読み方テスト")
    print("1: 小学生  2: 中学生  3: 高校生  4: 大学生  5: 復習（間違えた単語）")
    while True:
        mode = input("番号を入力してください > ").strip()
        if mode in ["1", "2", "3", "4", "5"]:
            return mode
        print("1〜5 の番号を入力してください")


# 空白を取り除き、ひらがなをカタカナに変えて答えを整える
def normalize(text):
    text = "".join(text.split())
    result = ""
    for char in text:
        if "ぁ" <= char <= "ゖ":
            char = chr(ord(char) + 0x60)
        result += char
    return result


# 答えが正解の読み方のどれか1つと一致するかを調べる
def is_correct(answer, reading):
    readings = [normalize(r) for r in reading.split("/")]
    return normalize(answer) in readings


# 1問出題して、○なら True、×なら False を返す
def ask_question(number, item):
    print()
    print(f"第{number}問  {item['word']}")
    answer = input("読み方 > ")
    if is_correct(answer, item["reading"]):
        print(f"○  意味：{item['meaning']}")
        return True
    correct = item["reading"].replace("/", " / ")
    print(f"×  正解：{correct}  意味：{item['meaning']}")
    return False


# 答えの結果に合わせて、間違えた単語の記録を更新する
def update_mistakes(mistakes, item, correct, review):
    recorded = [m["word"] for m in mistakes]
    if review and correct:
        mistakes[:] = [m for m in mistakes if m["word"] != item["word"]]
    elif not review and not correct and item["word"] not in recorded:
        mistakes.append(item)
    else:
        return
    save_mistakes(MISTAKES_PATH, mistakes)


# 出題する単語を選んでテストを1回行う
def run_test(mode, words, mistakes):
    review = mode == "5"
    if review:
        pool = list(mistakes)
        if not pool:
            print("間違えた単語はありません")
            return
    else:
        pool = [w for w in words if w["level"] == mode]
    questions = random.sample(pool, min(QUESTION_COUNT, len(pool)))
    for number, item in enumerate(questions, start=1):
        correct = ask_question(number, item)
        update_mistakes(mistakes, item, correct, review)
    print()
    print("テスト終了")


# プログラム全体の流れ
def main():
    if not os.path.exists(WORDS_PATH):
        print("data/words.csv が見つかりません")
        return
    try:
        words = load_words(WORDS_PATH)
        mistakes = load_mistakes(MISTAKES_PATH)
        mode = ask_mode()
        run_test(mode, words, mistakes)
    except (KeyboardInterrupt, EOFError):
        print()
        print("中断しました")


if __name__ == "__main__":
    main()
