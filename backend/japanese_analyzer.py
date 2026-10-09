from fugashi import Tagger
from pykakasi import kakasi


tagger = Tagger()
kks = kakasi()


# =========================================================
# Common Japanese readings
# =========================================================

COMMON_READINGS = {
    "私": "わたし",
    "日本語": "にほんご",
    "日本": "にほん",
}


# =========================================================
# Particle pronunciation
# =========================================================

PARTICLE_ROMAJI = {
    "は": "wa",
    "へ": "e",
    "を": "o",
}


# =========================================================
# Punctuation
# =========================================================

PUNCTUATION = {
    "。",
    "、",
    "！",
    "？",
    "!",
    "?",
    ",",
    ".",
    "，",
    "．",
    "「",
    "」",
    "『",
    "』",
    "（",
    "）",
    "(",
    ")",
}


# =========================================================
# Common noun + する verbs
#
# Fugashi tokenizes:
#
# 勉強します
# ↓
# 勉強 + し + ます
#
# We combine these into:
#
# 勉強します
# =========================================================

SURU_VERBS = {
    "勉強",
    "運動",
    "仕事",
    "料理",
    "練習",
    "電話",
    "買い物",
    "旅行",
    "掃除",
    "洗濯",
    "準備",
    "質問",
    "説明",
    "研究",
    "開発",
    "使用",
    "利用",
    "確認",
    "開始",
    "終了",
}


# =========================================================
# Convert text to Hiragana
# =========================================================

def to_hiragana(text):

    if text is None:
        return ""

    text = str(text).strip()

    if not text:
        return ""

    result = kks.convert(text)

    return "".join(
        item["hira"]
        for item in result
    )


# =========================================================
# Convert text to Romaji
# =========================================================

def to_romaji(text):

    if text is None:
        return ""

    text = str(text).strip()

    if not text:
        return ""

    result = kks.convert(text)

    return "".join(
        item["hepburn"]
        for item in result
    )

# =========================================================
# Get reading
# =========================================================

def get_reading(surface, reading):

    # Use beginner-friendly known readings
    if surface in COMMON_READINGS:
        return COMMON_READINGS[surface]

    return to_hiragana(reading)


# =========================================================
# Get Romaji
# =========================================================

def get_romaji(surface, reading):

    # Japanese particle pronunciation exceptions
    if surface in PARTICLE_ROMAJI:
        return PARTICLE_ROMAJI[surface]

    normalized_reading = get_reading(
        surface,
        reading
    )

    return to_romaji(normalized_reading)


# =========================================================
# Merge multiple tokens
# =========================================================

def merge_items(items):

    word = ""
    reading = ""
    romaji = ""

    for item in items:

        word += item["word"]
        reading += item["reading"]
        romaji += item["romaji"]

    return {
        "word": word,
        "reading": reading,
        "romaji": romaji,
    }


# =========================================================
# Analyze Japanese sentence
# =========================================================

def analyze_japanese(sentence):

    morphemes = []


    # =====================================================
    # STEP 1
    # Tokenize sentence using Fugashi
    # =====================================================

    for token in tagger(sentence):

        surface = token.surface

        # Ignore punctuation
        if surface in PUNCTUATION:
            continue

        feature = token.feature

        reading = feature.kana

        morphemes.append({
            "word": surface,
            "reading": get_reading(
                surface,
                reading
            ),
            "romaji": get_romaji(
                surface,
                reading
            ),
            "pos": feature.pos1
        })


    # =====================================================
    # STEP 2
    # Merge tokens into learner-friendly words
    # =====================================================

    words = []

    i = 0

    while i < len(morphemes):

        current = morphemes[i]


        # =================================================
        # CASE 1
        # Verb + 接続助詞 + Verb + Auxiliary
        #
        # Example:
        #
        # し + て + い + ます
        #
        # →
        #
        # しています
        #
        # This supports:
        #
        # 勉強しています
        # 食べています
        # 行っています
        # =================================================

        if (
            i + 3 < len(morphemes)
            and current["pos"] == "動詞"
            and morphemes[i + 1]["pos"] == "接続助詞"
            and morphemes[i + 2]["pos"] == "動詞"
            and morphemes[i + 3]["pos"] == "助動詞"
        ):

            merged = merge_items([
                current,
                morphemes[i + 1],
                morphemes[i + 2],
                morphemes[i + 3]
            ])

            merged["pos"] = "動詞"

            words.append(merged)

            i += 4

            continue


        # =================================================
        # CASE 2
        # Verb + 接続助詞 + Verb
        #
        # Example:
        #
        # 読み + て + いる
        #
        # →
        #
        # 読みている
        #
        # General support for connected verb forms.
        # =================================================

        if (
            i + 2 < len(morphemes)
            and current["pos"] == "動詞"
            and morphemes[i + 1]["pos"] == "接続助詞"
            and morphemes[i + 2]["pos"] == "動詞"
        ):

            merged = merge_items([
                current,
                morphemes[i + 1],
                morphemes[i + 2]
            ])

            merged["pos"] = "動詞"

            i += 3

            # If an auxiliary follows, merge it too
            while (
                i < len(morphemes)
                and morphemes[i]["pos"] == "助動詞"
            ):

                merged = merge_items([
                    merged,
                    morphemes[i]
                ])

                merged["pos"] = "動詞"

                i += 1

            words.append(merged)

            continue


        # =================================================
        # CASE 3
        # Noun + し + ます
        #
        # THIS IS IMPORTANT
        #
        # Fugashi gives:
        #
        # 勉強 → 名詞
        # し   → 動詞
        # ます → 助動詞
        #
        # We convert:
        #
        # 勉強 + し + ます
        #
        # →
        #
        # 勉強します
        #
        # POS → 動詞
        # =================================================

        if (
            i + 2 < len(morphemes)
            and current["pos"] == "名詞"
            and current["word"] in SURU_VERBS
            and morphemes[i + 1]["word"] == "し"
            and morphemes[i + 1]["pos"] == "動詞"
            and morphemes[i + 2]["word"] == "ます"
            and morphemes[i + 2]["pos"] == "助動詞"
        ):

            merged = merge_items([
                current,
                morphemes[i + 1],
                morphemes[i + 2]
            ])

            merged["pos"] = "動詞"

            words.append(merged)

            i += 3

            continue


        # =================================================
        # CASE 4
        # Verb + Auxiliary
        #
        # Examples:
        #
        # 行き + ます
        # →
        # 行きます
        #
        # 見 + まし + た
        # →
        # 見ました
        #
        # 食べ + まし + た
        # →
        # 食べました
        # =================================================

        if (
            i + 1 < len(morphemes)
            and current["pos"] == "動詞"
            and morphemes[i + 1]["pos"] == "助動詞"
        ):

            merged = merge_items([
                current,
                morphemes[i + 1]
            ])

            merged["pos"] = "動詞"

            i += 2


            # Continue merging auxiliary chain
            while (
                i < len(morphemes)
                and morphemes[i]["pos"] == "助動詞"
            ):

                merged = merge_items([
                    merged,
                    morphemes[i]
                ])

                merged["pos"] = "動詞"

                i += 1

            words.append(merged)

            continue


        # =================================================
        # CASE 5
        # Normal word
        # =================================================

        words.append({
            "word": current["word"],
            "reading": current["reading"],
            "romaji": current["romaji"],
            "pos": current["pos"]
        })

        i += 1


    # =====================================================
    # STEP 3
    # Combine 日本 + 語
    #
    # 日本 + 語
    #
    # →
    #
    # 日本語
    # =====================================================

    combined_words = []

    i = 0

    while i < len(words):

        if (
            i + 1 < len(words)
            and words[i]["word"] == "日本"
            and words[i + 1]["word"] == "語"
        ):

            combined_words.append({
                "word": "日本語",
                "reading": "にほんご",
                "romaji": "nihongo",
                "pos": "名詞"
            })

            i += 2

        else:

            combined_words.append(
                words[i]
            )

            i += 1


    # =====================================================
    # STEP 4
    # Return final result
    # =====================================================

    return {
        "morphemes": morphemes,
        "words": combined_words
    }


# =========================================================
# LOCAL TEST
# =========================================================

if __name__ == "__main__":

    result = analyze_japanese(
        "私は学校で勉強します。"
    )

    print("\nMORPHEMES:")

    for word in result["morphemes"]:
        print(word)


    print("\nWORDS:")

    for word in result["words"]:
        print(word)