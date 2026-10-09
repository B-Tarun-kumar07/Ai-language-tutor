from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from ollama import chat
import random
from japanese_analyzer import analyze_japanese
from vocabulary import get_unknown_word_meanings
from vocabulary_db import (
    initialize_database,
    save_vocabulary,
    get_all_vocabulary,
    repair_missing_meanings,
    record_review_result,
    get_weak_vocabulary,
    get_vocabulary_stats,
)
import re
import json


class ListeningRequest(BaseModel):
    level: str = "N5"
    count: int = 5

# ============================================================
# APP
# ============================================================

app = FastAPI(title="AI Language Tutor")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

initialize_database()


# ============================================================
# ROMAJI DETECTION
# ============================================================

def is_romaji(text: str) -> bool:
    """
    Detect whether the input is primarily Romaji.
    """

    text = text.strip()

    if not text:
        return False

    # Already Japanese
    if re.search(r"[\u3040-\u30ff\u3400-\u9fff]", text):
        return False

    latin_chars = len(
        re.findall(r"[a-zA-Z]", text)
    )

    total_chars = len(
        re.sub(r"\s+", "", text)
    )

    if total_chars == 0:
        return False

    return latin_chars / total_chars > 0.6


# ============================================================
# ROMAJI -> HIRAGANA
# ============================================================

ROMAJI_MAP = {
    # combinations
    "kya": "きゃ",
    "kyu": "きゅ",
    "kyo": "きょ",
    "gya": "ぎゃ",
    "gyu": "ぎゅ",
    "gyo": "ぎょ",
    "sha": "しゃ",
    "shu": "しゅ",
    "sho": "しょ",
    "ja": "じゃ",
    "ju": "じゅ",
    "jo": "じょ",
    "cha": "ちゃ",
    "chu": "ちゅ",
    "cho": "ちょ",
    "nya": "にゃ",
    "nyu": "にゅ",
    "nyo": "にょ",
    "hya": "ひゃ",
    "hyu": "ひゅ",
    "hyo": "ひょ",
    "bya": "びゃ",
    "byu": "びゅ",
    "byo": "びょ",
    "pya": "ぴゃ",
    "pyu": "ぴゅ",
    "pyo": "ぴょ",
    "mya": "みゃ",
    "myu": "みゅ",
    "myo": "みょ",
    "rya": "りゃ",
    "ryu": "りゅ",
    "ryo": "りょ",

    "fa": "ふぁ",
    "fi": "ふぃ",
    "fe": "ふぇ",
    "fo": "ふぉ",

    "va": "ゔぁ",
    "vi": "ゔぃ",
    "vu": "ゔ",
    "ve": "ゔぇ",
    "vo": "ゔぉ",

    "ti": "てぃ",
    "di": "でぃ",
    "tu": "とぅ",
    "du": "どぅ",

    "she": "しぇ",
    "je": "じぇ",
    "che": "ちぇ",

    # vowels
    "a": "あ",
    "i": "い",
    "u": "う",
    "e": "え",
    "o": "お",

    # k
    "ka": "か",
    "ki": "き",
    "ku": "く",
    "ke": "け",
    "ko": "こ",

    # g
    "ga": "が",
    "gi": "ぎ",
    "gu": "ぐ",
    "ge": "げ",
    "go": "ご",

    # s
    "sa": "さ",
    "si": "し",
    "shi": "し",
    "su": "す",
    "se": "せ",
    "so": "そ",

    # z
    "za": "ざ",
    "zi": "じ",
    "ji": "じ",
    "zu": "ず",
    "ze": "ぜ",
    "zo": "ぞ",

    # t
    "ta": "た",
    "chi": "ち",
    "tsu": "つ",
    "te": "て",
    "to": "と",

    # d
    "da": "だ",
    "di": "ぢ",
    "du": "づ",
    "de": "で",
    "do": "ど",

    # n
    "na": "な",
    "ni": "に",
    "nu": "ぬ",
    "ne": "ね",
    "no": "の",

    # h
    "ha": "は",
    "hi": "ひ",
    "fu": "ふ",
    "hu": "ふ",
    "he": "へ",
    "ho": "ほ",

    # b
    "ba": "ば",
    "bi": "び",
    "bu": "ぶ",
    "be": "べ",
    "bo": "ぼ",

    # p
    "pa": "ぱ",
    "pi": "ぴ",
    "pu": "ぷ",
    "pe": "ぺ",
    "po": "ぽ",

    # m
    "ma": "ま",
    "mi": "み",
    "mu": "む",
    "me": "め",
    "mo": "も",

    # y
    "ya": "や",
    "yu": "ゆ",
    "yo": "よ",

    # r
    "ra": "ら",
    "ri": "り",
    "ru": "る",
    "re": "れ",
    "ro": "ろ",

    # w
    "wa": "わ",
    "wi": "ゐ",
    "we": "ゑ",
    "wo": "を",

    "n": "ん",
}


# ============================================================
# COMMON ROMAJI WORDS
# ============================================================

ROMAJI_WORD_OVERRIDES = {
    "watashi": "私",
    "watashitachi": "私たち",
    "anata": "あなた",
    "onamae": "お名前",
"namae": "名前",
"nan": "何",
"desu": "です",
"deshita": "でした",
"ka": "か",
    "gakkou": "学校",
    "gakko": "学校",
    "daigaku": "大学",
    "kaisha": "会社",

    "ie": "家",
    "uchi": "家",
    "eki": "駅",
    "toshokan": "図書館",

    "nihon": "日本",
    "nihongo": "日本語",
    "eigo": "英語",

    "tomodachi": "友達",
    "sensei": "先生",
    "gakusei": "学生",

    "chichi": "父",
    "haha": "母",
    "kazoku": "家族",

    "hon": "本",
    "eiga": "映画",
    "terebi": "テレビ",

    "raamen": "ラーメン",
    "ramen": "ラーメン",

    "mizu": "水",
    "gohan": "ご飯",

    "benkyou": "勉強",
    "benkyo": "勉強",

    "undou": "運動",
    "ryouri": "料理",
    "renshuu": "練習",
    "ryokou": "旅行",

    # verbs
    "ikimasu": "行きます",
    "ikimashita": "行きました",
    "ikimasen": "行きません",
    "ikimasendeshita": "行きませんでした",

    "kimasu": "来ます",
    "kimashita": "来ました",

    "kaerimasu": "帰ります",
    "kaerimashita": "帰りました",

    "mimasu": "見ます",
    "mimashita": "見ました",
    "mimasen": "見ません",
    "mimashitadeshita": "見ませんでした",

    "tabemasu": "食べます",
    "tabemashita": "食べました",
    "tabemasen": "食べません",
    "tabemasendeshita": "食べませんでした",

    "nomimasu": "飲みます",
    "nomimashita": "飲みました",

    "yomimasu": "読みます",
    "yomimashita": "読みました",

    "kakimasu": "書きます",
    "kakimashita": "書きました",

    "kikimasu": "聞きます",
    "hanashimasu": "話します",

    "shimasu": "します",

    "benkyoushimasu": "勉強します",
    "undoushimasu": "運動します",
    "ryourishimasu": "料理します",
    "renshuushimasu": "練習します",
}


def romaji_syllable_to_hiragana(text: str) -> str:

    text = text.lower().strip()

    result = []

    i = 0

    while i < len(text):

        # punctuation / spaces
        if not text[i].isalpha():
            result.append(text[i])
            i += 1
            continue

        # double consonant
        if (
            i + 1 < len(text)
            and text[i] == text[i + 1]
            and text[i] in "bcdfghjklmpqrstvwxyz"
            and text[i] != "n"
        ):
            result.append("っ")
            i += 1
            continue

        # n
        if (
            text[i] == "n"
            and (
                i + 1 == len(text)
                or text[i + 1] not in "aeiouy"
            )
        ):
            result.append("ん")
            i += 1
            continue

        matched = False

        for length in (3, 2, 1):

            part = text[i:i + length]

            if part in ROMAJI_MAP:

                result.append(
                    ROMAJI_MAP[part]
                )

                i += length

                matched = True

                break

        if not matched:

            result.append(text[i])
            i += 1

    return "".join(result)
def is_valid_romaji_token(token):
    """
    Check whether the entire token can actually be interpreted
    as valid Japanese Romaji.

    This prevents garbage such as:
        sh
        xyz
        random
    from being treated as a Japanese/foreign-name token.
    """

    token = token.lower()

    if not token or not re.fullmatch(r"[a-z]+", token):
        return False

    i = 0

    while i < len(token):

        # Double consonant
        if (
            i + 1 < len(token)
            and token[i] == token[i + 1]
            and token[i] not in "aeioun"
        ):
            i += 1
            continue

        # ん
        if token[i] == "n":

            if i + 1 == len(token):
                i += 1
                continue

            if token[i + 1] in "bmp":
                i += 1
                continue

            if token[i + 1] not in "aeiouyn":
                i += 1
                continue

        matched = False

        # Longest Romaji patterns first
        for length in [3, 2, 1]:

            part = token[i:i + length]

            if part in ROMAJI_MAP:
                i += length
                matched = True
                break

        if not matched:
            return False

    return True


def looks_like_foreign_name(token):

    """
    Detect whether a Romaji token is likely to be
    a foreign name rather than normal Japanese vocabulary.
    """

    lower = token.lower()

    # Already known Japanese vocabulary
    if lower in ROMAJI_WORD_OVERRIDES:
        return False

    # Japanese particles
    if lower in {
        "wa",
        "ga",
        "wo",
        "o",
        "ni",
        "de",
        "to",
        "e",
        "no",
        "mo",
        "kara",
        "made",
    }:
        return False

    # Common grammatical words
    if lower in {
        "desu",
        "masu",
        "deshita",
        "masen",
        "janai",
    }:
        return False

    # Very short tokens are not useful name candidates
    if len(lower) < 3:
        return False

    # It must actually be valid Romaji
    return is_valid_romaji_token(lower)
def hiragana_to_katakana(text):
    """
    Convert Hiragana characters to Katakana.
    """

    result = []

    for char in text:

        code = ord(char)

        # Hiragana range → Katakana range
        if 0x3041 <= code <= 0x3096:
            result.append(
                chr(code + 0x60)
            )
        else:
            result.append(char)

    return "".join(result)

def romaji_to_japanese(text: str) -> str:

    text = text.strip()

    if not text:
        return text

    converted = []

    tokens = text.split()

    for token in tokens:

        lower = token.lower()

        # -----------------------------------------
        # Japanese particles
        # -----------------------------------------

        if lower == "wa":
            converted.append("は")

        elif lower == "wo":
            converted.append("を")

        elif lower == "o":
            converted.append("を")

        elif lower == "e":
            converted.append("へ")

        # -----------------------------------------
        # Known Japanese vocabulary
        # -----------------------------------------

        elif lower in ROMAJI_WORD_OVERRIDES:

            converted.append(
                ROMAJI_WORD_OVERRIDES[lower]
            )

        # -----------------------------------------
        # Possible foreign name
        # -----------------------------------------

        elif looks_like_foreign_name(token):

            hiragana = romaji_syllable_to_hiragana(
                token
            )

            katakana = hiragana_to_katakana(
                hiragana
            )

            converted.append(katakana)

        # -----------------------------------------
        # Normal Romaji
        # -----------------------------------------

        else:

            converted.append(
                romaji_syllable_to_hiragana(
                    token
                )
            )

    return "".join(converted)
def get_foreign_name_surfaces(text):
    """
    Get Katakana forms of unknown Romaji tokens
    that are being treated as foreign names.

    These names can appear in the analysis,
    but they will not automatically become vocabulary.
    """

    surfaces = set()

    tokens = text.strip().split()

    for token in tokens:

        if not looks_like_foreign_name(token):
            continue

        try:

            hiragana = romaji_syllable_to_hiragana(
                token
            )

            if not hiragana:
                continue

            katakana = hiragana_to_katakana(
                hiragana
            )

            if katakana:
                surfaces.add(katakana)

        except Exception:
            continue

    return surfaces
def get_foreign_name_surfaces(text):
    """
    Return the Katakana surfaces generated from unknown
    Romaji tokens that are being treated as foreign names.

    These names can still appear in the analyzed sentence,
    but they should NOT automatically become vocabulary.
    """

    surfaces = set()

    tokens = text.strip().split()

    for token in tokens:

        lower = token.lower()

        if not looks_like_foreign_name(token):
            continue

        try:
            hira = romaji_syllable_to_hiragana(token)

            if not hira:
                continue

            katakana = hiragana_to_katakana(hira)

            if katakana:
                surfaces.add(katakana)

        except Exception:
            continue

    return surfaces
# ============================================================
# REQUEST MODELS
# ============================================================

class LanguageRequest(BaseModel):

    target_language: str

    known_language: str

    text: str

class ReviewResultRequest(BaseModel):
    vocabulary_id: int
    correct: bool
class VocabularyRequest(BaseModel):

    word: str

    reading: str

    romaji: str

    meaning: str

    part_of_speech: str

    role: str

    target_language: str

    known_language: str


# ============================================================
# PARTICLES
# ============================================================

PARTICLE_MEANINGS = {

    "は": "topic marker",
    "が": "subject marker",
    "を": "object marker",
    "に": "destination / target",
    "で": "location of an action",
    "と": "with / and",
    "へ": "direction / destination",
    "も": "also / too",
    "の": "possession / connection",
    "から": "from",
    "まで": "until / up to",

}


# ============================================================
# COMMON WORDS
# ============================================================

COMMON_WORD_MEANINGS = {

    "私": "I / me",
    "私たち": "we / us",
    "あなた": "you",

    "学校": "school",
    "大学": "university",
    "会社": "company / workplace",
    "家": "home / house",
    "駅": "station",
    "図書館": "library",

    "日本": "Japan",
    "日本語": "Japanese language",
    "英語": "English language",

    "友達": "friend",
    "先生": "teacher",
    "学生": "student",

    "父": "father",
    "母": "mother",
    "家族": "family",

    "本": "book",
    "映画": "movie",
    "テレビ": "television",

    "ラーメン": "ramen",
    "水": "water",
    "ご飯": "meal / rice",

    "勉強": "study",
    "運動": "exercise",
    "料理": "cooking",
    "練習": "practice",
    "旅行": "travel",

}


# ============================================================
# VERBS
# ============================================================

VERB_MEANINGS = {

    "行きます": "go",
    "行く": "go",

    "来ます": "come",
    "来る": "come",

    "帰ります": "return / go home",
    "帰る": "return / go home",

    "見ます": "watch / see",
    "見る": "watch / see",

    "食べます": "eat",
    "食べる": "eat",

    "飲みます": "drink",
    "飲む": "drink",

    "読みます": "read",
    "読む": "read",

    "書きます": "write",
    "書く": "write",

    "聞きます": "listen / hear / ask",
    "聞く": "listen / hear / ask",

    "話します": "speak / talk",
    "話す": "speak / talk",

    "します": "do",
    "する": "do",

    "勉強します": "study",
    "勉強する": "study",

    "運動します": "exercise",
    "運動する": "exercise",

    "料理します": "cook",
    "料理する": "cook",

    "練習します": "practice",
    "練習する": "practice",

    "行きません": "do not go",
    "行きませんでした": "did not go",

    "食べません": "do not eat",
    "食べませんでした": "did not eat",

    "見ません": "do not watch / see",
    "見ませんでした": "did not watch / see",

    "飲みません": "do not drink",
    "飲みませんでした": "did not drink",

}


# ============================================================
# ADJECTIVES
# ============================================================

ADJECTIVE_MEANINGS = {

    "大きい": "big",
    "小さい": "small",
    "新しい": "new",
    "古い": "old",
    "良い": "good",
    "いい": "good",
    "悪い": "bad",
    "高い": "expensive / high",
    "安い": "cheap",
    "面白い": "interesting / funny",
    "楽しい": "fun / enjoyable",

}


# ============================================================
# MEANING
# ============================================================

def get_basic_meaning(word):

    if word in PARTICLE_MEANINGS:
        return PARTICLE_MEANINGS[word]

    if word in COMMON_WORD_MEANINGS:
        return COMMON_WORD_MEANINGS[word]

    if word in VERB_MEANINGS:
        return VERB_MEANINGS[word]

    if word in ADJECTIVE_MEANINGS:
        return ADJECTIVE_MEANINGS[word]

    return None


# ============================================================
# ROLE
# ============================================================

def get_basic_role(word, pos, words):

    word_list = [
        w["word"]
        for w in words
    ]

    if word == "は":
        return "topic marker"

    if word == "が":
        return "subject marker"

    if word == "を":
        return "object marker"

    if word == "に":
        return "destination / target"

    if word == "で":
        return "location of action"

    if word == "と":
        return "companion / conjunction"

    if word == "へ":
        return "direction / destination"

    if word == "も":
        return "also / too"

    if word == "の":
        return "possession / connection"

    if word == "から":
        return "starting point"

    if word == "まで":
        return "ending point"

    if pos == "動詞":
        return "predicate"

    try:

        current_index = word_list.index(word)

        if "は" in word_list:

            wa_index = word_list.index("は")

            if current_index == wa_index - 1:
                return "topic"

        if "を" in word_list:

            wo_index = word_list.index("を")

            if current_index == wo_index - 1:
                return "object"

        if "に" in word_list:

            ni_index = word_list.index("に")

            if current_index == ni_index - 1:
                return "destination"

        if "で" in word_list:

            de_index = word_list.index("で")

            if current_index == de_index - 1:
                return "location"

    except ValueError:
        pass

    if pos in ["名詞", "代名詞"]:
        return "noun"

    return "other"


# ============================================================
# DATABASE
# ============================================================

repair_missing_meanings({
    **PARTICLE_MEANINGS,
    **COMMON_WORD_MEANINGS,
    **VERB_MEANINGS,
    **ADJECTIVE_MEANINGS,
})


@app.post("/vocabulary")

@app.post("/vocabulary")
def add_vocabulary(request: VocabularyRequest):

    saved = save_vocabulary(
        word=request.word,
        reading=request.reading,
        romaji=request.romaji,
        meaning=request.meaning,
        part_of_speech=request.part_of_speech,
        role=request.role,
        learning_language=request.target_language,
        support_language=request.known_language,
    )

    return {
        "success": True,
        "message": (
            "Word saved successfully"
            if saved
            else "Word already exists in vocabulary"
        ),
        "word": request.word,
    }



@app.get("/vocabulary")
def get_vocabulary():

    return {
        "vocabulary": get_all_vocabulary()
    }


# ============================================================
# WORD HELPERS
# ============================================================

def is_verb(word):

    return word["pos"] == "動詞"


def is_noun(word):

    return word["pos"] in [
        "名詞",
        "代名詞",
    ]


def is_polite_present(word):

    return (
        word["pos"] == "動詞"
        and word["word"].endswith("ます")
        and not word["word"].endswith("ません")
    )


def is_polite_past(word):

    return (
        word["pos"] == "動詞"
        and word["word"].endswith("ました")
    )


def is_polite_negative(word):

    return (
        word["pos"] == "動詞"
        and word["word"].endswith("ません")
        and not word["word"].endswith("ませんでした")
    )


def is_polite_negative_past(word):

    return (
        word["pos"] == "動詞"
        and word["word"].endswith("ませんでした")
    )


def is_teiru(word):

    return (
        word["pos"] == "動詞"
        and word["word"].endswith("ています")
    )


def is_teiru_negative(word):

    return (
        word["pos"] == "動詞"
        and word["word"].endswith("ていません")
    )


def is_tai(word):

    return (
        word["pos"] == "動詞"
        and word["word"].endswith("たいです")
    )


def is_takunai(word):

    return (
        word["pos"] == "動詞"
        and word["word"].endswith("たくないです")
    )


# ============================================================
# GRAMMAR
# ============================================================

GRAMMAR_INFO = {

    "N は N に Vます": {
        "meaning": "Topic + destination + polite present verb",
        "structure": "topic → destination → polite present action",
    },

    "N は N に Vました": {
        "meaning": "Topic + destination + polite past verb",
        "structure": "topic → destination → polite past action",
    },

    "N は N を Vます": {
        "meaning": "Topic + object + polite present verb",
        "structure": "topic → object → polite present action",
    },

    "N は N を Vました": {
        "meaning": "Topic + object + polite past verb",
        "structure": "topic → object → polite past action",
    },

    "N は N で Vます": {
        "meaning": "Topic + location of action + polite present verb",
        "structure": "topic → action location → polite present action",
    },

    "N は N で Vました": {
        "meaning": "Topic + location of action + polite past verb",
        "structure": "topic → action location → polite past action",
    },

    "N と Vます": {
        "meaning": "With someone + polite present verb",
        "structure": "companion → action",
    },

    "N と Vました": {
        "meaning": "With someone + polite past verb",
        "structure": "companion → past action",
    },

    "N の N": {
        "meaning": "Noun + possession / connection + noun",
        "structure": "possessor / connection → の → noun",
    },

    "N が Vます": {
        "meaning": "Subject + polite present verb",
        "structure": "subject → polite present action",
    },

    "N が Vました": {
        "meaning": "Subject + polite past verb",
        "structure": "subject → polite past action",
    },

    "N は Vません": {
        "meaning": "Topic + polite negative verb",
        "structure": "topic → does not perform the action",
    },

    "N は Vませんでした": {
        "meaning": "Topic + polite negative past verb",
        "structure": "topic → did not perform the action",
    },

    "N は Vています": {
        "meaning": "Topic + action in progress",
        "structure": "topic → action currently in progress",
    },

    "N は Vていません": {
        "meaning": "Topic + negative action in progress",
        "structure": "topic → action is not currently happening",
    },

    "N は Vたいです": {
        "meaning": "Topic + wants to perform an action",
        "structure": "topic → wants to do something",
    },

    "N は Vたくないです": {
        "meaning": "Topic + does not want to perform an action",
        "structure": "topic → does not want to do something",
    },

    "N から V": {
        "meaning": "Starting point + action",
        "structure": "starting point → action",
    },

    "N まで V": {
        "meaning": "Ending point + action",
        "structure": "ending point → action",
    },

    "N も V": {
        "meaning": "Also / too + action",
        "structure": "additional topic → action",
    },

    "N へ V": {
        "meaning": "Direction + action",
        "structure": "direction / destination → action",
    },

}


def detect_grammar(words):

    detected = []

    n = len(words)

    def add_pattern(pattern, indexes):

        if pattern not in [
            item["pattern"]
            for item in detected
        ]:

            detected.append({
                "pattern": pattern,
                "meaning": GRAMMAR_INFO[pattern]["meaning"],
                "structure": GRAMMAR_INFO[pattern]["structure"],
                "indexes": indexes,
            })

    for i in range(n):

        # N は N に V
        if (
            i + 3 < n
            and is_noun(words[i])
            and words[i + 1]["word"] == "は"
            and is_noun(words[i + 2])
            and words[i + 3]["word"] == "に"
        ):

            for j in range(i + 4, n):

                if is_verb(words[j]):

                    if is_polite_past(words[j]):

                        add_pattern(
                            "N は N に Vました",
                            [i, i + 1, i + 2, i + 3, j],
                        )

                    elif is_polite_present(words[j]):

                        add_pattern(
                            "N は N に Vます",
                            [i, i + 1, i + 2, i + 3, j],
                        )

                    break

        # N は N を V
        if (
            i + 3 < n
            and is_noun(words[i])
            and words[i + 1]["word"] == "は"
            and is_noun(words[i + 2])
            and words[i + 3]["word"] == "を"
        ):

            for j in range(i + 4, n):

                if is_verb(words[j]):

                    if is_polite_past(words[j]):

                        add_pattern(
                            "N は N を Vました",
                            [i, i + 1, i + 2, i + 3, j],
                        )

                    elif is_polite_present(words[j]):

                        add_pattern(
                            "N は N を Vます",
                            [i, i + 1, i + 2, i + 3, j],
                        )

                    break

        # N は N で V
        if (
            i + 3 < n
            and is_noun(words[i])
            and words[i + 1]["word"] == "は"
            and is_noun(words[i + 2])
            and words[i + 3]["word"] == "で"
        ):

            for j in range(i + 4, n):

                if is_verb(words[j]):

                    if is_polite_past(words[j]):

                        add_pattern(
                            "N は N で Vました",
                            [i, i + 1, i + 2, i + 3, j],
                        )

                    elif is_polite_present(words[j]):

                        add_pattern(
                            "N は N で Vます",
                            [i, i + 1, i + 2, i + 3, j],
                        )

                    break

        # N は V
        if (
            i + 2 < n
            and is_noun(words[i])
            and words[i + 1]["word"] == "は"
            and is_verb(words[i + 2])
        ):

            verb = words[i + 2]

            if is_polite_negative_past(verb):

                add_pattern(
                    "N は Vませんでした",
                    [i, i + 1, i + 2],
                )

            elif is_polite_negative(verb):

                add_pattern(
                    "N は Vません",
                    [i, i + 1, i + 2],
                )

            elif is_teiru_negative(verb):

                add_pattern(
                    "N は Vていません",
                    [i, i + 1, i + 2],
                )

            elif is_teiru(verb):

                add_pattern(
                    "N は Vています",
                    [i, i + 1, i + 2],
                )

            elif is_takunai(verb):

                add_pattern(
                    "N は Vたくないです",
                    [i, i + 1, i + 2],
                )

            elif is_tai(verb):

                add_pattern(
                    "N は Vたいです",
                    [i, i + 1, i + 2],
                )

        # N が V
        if (
            i + 2 < n
            and is_noun(words[i])
            and words[i + 1]["word"] == "が"
            and is_verb(words[i + 2])
        ):

            verb = words[i + 2]

            if is_polite_past(verb):

                add_pattern(
                    "N が Vました",
                    [i, i + 1, i + 2],
                )

            elif is_polite_present(verb):

                add_pattern(
                    "N が Vます",
                    [i, i + 1, i + 2],
                )

        # N の N
        if (
            i + 2 < n
            and is_noun(words[i])
            and words[i + 1]["word"] == "の"
            and is_noun(words[i + 2])
        ):

            add_pattern(
                "N の N",
                [i, i + 1, i + 2],
            )

        # N から V
        if (
            i + 2 < n
            and is_noun(words[i])
            and words[i + 1]["word"] == "から"
            and is_verb(words[i + 2])
        ):

            add_pattern(
                "N から V",
                [i, i + 1, i + 2],
            )

        # N まで V
        if (
            i + 2 < n
            and is_noun(words[i])
            and words[i + 1]["word"] == "まで"
            and is_verb(words[i + 2])
        ):

            add_pattern(
                "N まで V",
                [i, i + 1, i + 2],
            )

        # N も V
        if (
            i + 2 < n
            and is_noun(words[i])
            and words[i + 1]["word"] == "も"
            and is_verb(words[i + 2])
        ):

            add_pattern(
                "N も V",
                [i, i + 1, i + 2],
            )

        # N へ V
        if (
            i + 2 < n
            and is_noun(words[i])
            and words[i + 1]["word"] == "へ"
            and is_verb(words[i + 2])
        ):

            add_pattern(
                "N へ V",
                [i, i + 1, i + 2],
            )

        # N と V
        if (
            i + 1 < n
            and is_noun(words[i])
            and words[i + 1]["word"] == "と"
        ):

            for j in range(i + 2, n):

                if is_verb(words[j]):

                    if is_polite_past(words[j]):

                        add_pattern(
                            "N と Vました",
                            [i, i + 1, j],
                        )

                    elif is_polite_present(words[j]):

                        add_pattern(
                            "N と Vます",
                            [i, i + 1, j],
                        )

                    break

    return detected


# ============================================================
# NATURALNESS
# ============================================================

def detect_sentence_issue(words):

    word_list = [
        word["word"]
        for word in words
    ]

    movement_verbs = {
        "行きます",
        "行きました",
        "来ます",
        "来ました",
        "帰ります",
        "帰りました",
    }

    if (
        "で" in word_list
        and any(
            verb in word_list
            for verb in movement_verbs
        )
    ):

        return {
            "natural": False,
            "reason": (
                "With movement verbs such as 行く, 来る, "
                "and 帰る, に or へ normally marks the "
                "destination."
            ),
        }

    return {
        "natural": True,
        "reason": "",
    }


# ============================================================
# CORRECTION
# ============================================================

def get_correction(text, words):

    word_list = [
        word["word"]
        for word in words
    ]

    movement_verbs = {
        "行きます",
        "行きました",
        "来ます",
        "来ました",
        "帰ります",
        "帰りました",
    }

    if (
        "で" in word_list
        and any(
            verb in word_list
            for verb in movement_verbs
        )
    ):

        corrected = text

        corrected = corrected.replace(
            "で行きます",
            "に行きます",
        )

        corrected = corrected.replace(
            "で行きました",
            "に行きました",
        )

        corrected = corrected.replace(
            "で来ます",
            "に来ます",
        )

        corrected = corrected.replace(
            "で来ました",
            "に来ました",
        )

        corrected = corrected.replace(
            "で帰ります",
            "に帰ります",
        )

        corrected = corrected.replace(
            "で帰りました",
            "に帰りました",
        )

        return {
            "correction": corrected,
            "explanation": (
                "Use に or へ to mark the destination "
                "with movement verbs such as 行く, 来る, "
                "and 帰る."
            ),
        }

    return {
        "correction": "",
        "explanation": "",
    }


# ============================================================
# TRANSLATION
# ============================================================

def build_basic_translation(words):

    word_list = [
        word["word"]
        for word in words
    ]

    if (
        "私" in word_list
        and "は" in word_list
        and "学校" in word_list
        and "に" in word_list
        and "行きます" in word_list
    ):
        return "I go to school."

    if (
        "私" in word_list
        and "は" in word_list
        and "学校" in word_list
        and "で" in word_list
        and "勉強します" in word_list
    ):
        return "I study at school."

    if (
        "私" in word_list
        and "は" in word_list
        and "日本語" in word_list
        and "を" in word_list
        and "勉強しています" in word_list
    ):
        return "I am studying Japanese."

    if (
        "友達" in word_list
        and "と" in word_list
        and "映画" in word_list
        and "を" in word_list
        and "見ました" in word_list
    ):
        return "I watched a movie with my friend."

    if (
        "私" in word_list
        and "は" in word_list
        and "ラーメン" in word_list
        and "を" in word_list
        and "食べました" in word_list
    ):
        return "I ate ramen."

    if (
        "私" in word_list
        and "は" in word_list
        and "学校" in word_list
        and "で" in word_list
        and "行きます" in word_list
    ):
        return "I go to school."
    
    if (
        "お名前" in word_list
        or (
            "名前" in word_list
            and "何" in word_list
        )
    ):
        return "What is your name?"

    return None


def clean_translation(text):
    """
    Remove common LLM conversational wrappers and keep
    only the actual translation.
    """

    if not text:
        return ""

    text = text.strip()

    # Remove markdown code fences
    text = text.replace("```text", "")
    text = text.replace("```", "")
    text = text.strip()

    # Remove common labels
    prefixes = [
        "Translation:",
        "translation:",
        "English:",
        "english:",
        "Japanese translation:",
        "Japanese Translation:",
        "Here is the translation:",
        "Here is the translation",
        "The translation is:",
        "The translation is",
    ]

    for prefix in prefixes:
        if text.lower().startswith(prefix.lower()):
            text = text[len(prefix):].strip()

    # Remove common conversational sentences
    unwanted_lines = [
        "I will translate this sentence.",
        "I will translate the sentence.",
        "Here is the translation.",
        "Here is the translation:",
        "Sure, here is the translation.",
        "Sure, I can translate that.",
        "The translation is:",
    ]

    lines = text.splitlines()

    cleaned_lines = []

    for line in lines:

        line = line.strip()

        if not line:
            continue

        if line.lower() in [
            unwanted.lower()
            for unwanted in unwanted_lines
        ]:
            continue

        cleaned_lines.append(line)

    text = " ".join(cleaned_lines).strip()

    # Remove quotation marks if the entire translation is quoted
    if (
        len(text) >= 2
        and text[0] == '"'
        and text[-1] == '"'
    ):
        text = text[1:-1].strip()

    return text


def generate_translation(sentence, known_language):
    sentence = sentence.strip()

    if not sentence:
        return ""

    prompt = f"""
You are an accurate Japanese-to-{known_language} translation engine.

Translate the Japanese text below into natural {known_language}.

IMPORTANT:
- Translate the exact meaning of the input.
- Do not answer the question or respond to the sentence.
- Do not substitute a different sentence.
- Preserve names, tense, negation, questions, and politeness.
- If the Japanese is a question, translate it as a question.
- Return only the translation.
- Do not include explanations, labels, or quotation marks.

Japanese text:
<text>
{sentence}
</text>

Translation in {known_language}:
"""

    
    try:
        response = chat(
            model="llama3.2",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a precise translator. "
                        "Translate the provided text faithfully. "
                        "Never answer or react to the text."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            options={"temperature": 0},
        )

        result = response["message"]["content"].strip()
        print("Raw Ollama translation:", repr(result))

        cleaned_result = clean_translation(result)
        print("Cleaned translation:", repr(cleaned_result))

        return cleaned_result

    except Exception as error:
        print("Translation error:", repr(error))
        return ""


# ============================================================
# GRAMMAR EXPLANATION
# ============================================================

def generate_grammar_explanation(
    sentence,
    grammar,
    words,
):

    relevant_indexes = grammar["indexes"]

    relevant_words = [
        words[i]
        for i in relevant_indexes
        if i < len(words)
    ]

    word_details = []

    for word in relevant_words:

        word_details.append({
            "word": word["word"],
            "reading": word["reading"],
            "meaning": get_basic_meaning(
                word["word"]
            ),
            "role": get_basic_role(
                word["word"],
                word["pos"],
                words,
            ),
        })

    prompt = f"""
You are a Japanese language teacher.

Sentence:
{sentence}

Grammar pattern:
{grammar["pattern"]}

Grammar meaning:
{grammar["meaning"]}

Structure:
{grammar["structure"]}

Actual words:
{json.dumps(
    word_details,
    ensure_ascii=False,
    indent=2
)}

Write a SHORT beginner-friendly explanation.

Rules:

1. Explain the exact grammar pattern.
2. Use only words that actually occur.
3. Do not invent words.
4. Do not introduce another grammar pattern.
5. Explain important particles individually.
6. Explain the verb individually.
7. Keep the explanation concise.

Return plain text only.
"""

    response = chat(
        model="llama3.2",
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
    )

    return response["message"]["content"].strip()


# ============================================================
# EXAMPLES
# ============================================================

EXAMPLES = {

    "N は N に Vます": [
        {
            "sentence": "私は会社に行きます。",
            "translation": "I go to work.",
            "explanation": (
                "会社 に marks the destination, "
                "and 行きます is the polite present form."
            ),
        },
        {
            "sentence": "私は図書館に行きます。",
            "translation": "I go to the library.",
            "explanation": (
                "図書館 に marks the destination."
            ),
        },
    ],

    "N は N に Vました": [
        {
            "sentence": "私は学校に行きました。",
            "translation": "I went to school.",
            "explanation": (
                "学校 に marks the destination, "
                "and 行きました is the polite past form."
            ),
        },
        {
            "sentence": "私は駅に行きました。",
            "translation": "I went to the station.",
            "explanation": (
                "駅 に marks the destination."
            ),
        },
    ],

    "N は N で Vます": [
        {
            "sentence": "私は図書館で本を読みます。",
            "translation": "I read a book at the library.",
            "explanation": (
                "図書館 で marks the location "
                "where the action happens."
            ),
        },
        {
            "sentence": "私は家でテレビを見ます。",
            "translation": "I watch television at home.",
            "explanation": (
                "家 で marks the location of the action."
            ),
        },
    ],

    "N は N で Vました": [
        {
            "sentence": "私は図書館で本を読みました。",
            "translation": "I read a book at the library.",
            "explanation": (
                "図書館 で marks the location "
                "of the action."
            ),
        },
        {
            "sentence": "私は家で映画を見ました。",
            "translation": "I watched a movie at home.",
            "explanation": (
                "家 で marks the location of the action."
            ),
        },
    ],

    "N は N を Vます": [
        {
            "sentence": "私は本を読みます。",
            "translation": "I read a book.",
            "explanation": (
                "本 を marks the object."
            ),
        },
        {
            "sentence": "私は映画を見ます。",
            "translation": "I watch a movie.",
            "explanation": (
                "映画 を marks the object."
            ),
        },
    ],

    "N は N を Vました": [
        {
            "sentence": "私は本を読みました。",
            "translation": "I read a book.",
            "explanation": (
                "本 を marks the object."
            ),
        },
        {
            "sentence": "私は映画を見ました。",
            "translation": "I watched a movie.",
            "explanation": (
                "映画 を marks the object."
            ),
        },
    ],

    "N と Vます": [
        {
            "sentence": "友達と映画を見ます。",
            "translation": "I watch a movie with my friend.",
            "explanation": (
                "友達 と indicates the companion."
            ),
        },
        {
            "sentence": "先生と話します。",
            "translation": "I talk with my teacher.",
            "explanation": (
                "先生 と indicates the companion."
            ),
        },
    ],

    "N と Vました": [
        {
            "sentence": "友達と映画を見ました。",
            "translation": "I watched a movie with my friend.",
            "explanation": (
                "友達 と indicates the companion."
            ),
        },
        {
            "sentence": "先生と話しました。",
            "translation": "I talked with my teacher.",
            "explanation": (
                "先生 と indicates the companion."
            ),
        },
    ],

    "N の N": [
        {
            "sentence": "私の本です。",
            "translation": "It is my book.",
            "explanation": (
                "私 の connects the owner to 本."
            ),
        },
        {
            "sentence": "日本語の先生です。",
            "translation": "He/She is a Japanese teacher.",
            "explanation": (
                "日本語 の describes the type of teacher."
            ),
        },
    ],

    "N が Vます": [
        {
            "sentence": "友達が来ます。",
            "translation": "My friend is coming.",
            "explanation": (
                "友達 が marks the subject."
            ),
        },
        {
            "sentence": "先生が話します。",
            "translation": "The teacher speaks.",
            "explanation": (
                "先生 が marks the subject."
            ),
        },
    ],

    "N が Vました": [
        {
            "sentence": "友達が来ました。",
            "translation": "My friend came.",
            "explanation": (
                "友達 が marks the subject."
            ),
        },
        {
            "sentence": "先生が話しました。",
            "translation": "The teacher spoke.",
            "explanation": (
                "先生 が marks the subject."
            ),
        },
    ],

    "N は Vません": [
        {
            "sentence": "私は学校に行きません。",
            "translation": "I do not go to school.",
            "explanation": (
                "行きません is the polite negative form."
            ),
        },
        {
            "sentence": "私は肉を食べません。",
            "translation": "I do not eat meat.",
            "explanation": (
                "食べません expresses a negative action."
            ),
        },
    ],

    "N は Vませんでした": [
        {
            "sentence": "私は学校に行きませんでした。",
            "translation": "I did not go to school.",
            "explanation": (
                "行きませんでした expresses a past negative action."
            ),
        },
        {
            "sentence": "私は映画を見ませんでした。",
            "translation": "I did not watch the movie.",
            "explanation": (
                "見ませんでした expresses a past negative action."
            ),
        },
    ],

    "N は Vています": [
        {
            "sentence": "私は本を読んでいます。",
            "translation": "I am reading a book.",
            "explanation": (
                "読んでいます describes an action in progress."
            ),
        },
        {
            "sentence": "私は日本語を勉強しています。",
            "translation": "I am studying Japanese.",
            "explanation": (
                "勉強しています describes an ongoing action."
            ),
        },
    ],

    "N は Vていません": [
        {
            "sentence": "私はテレビを見ていません。",
            "translation": "I am not watching television.",
            "explanation": (
                "見ていません describes an action that "
                "is not currently happening."
            ),
        },
        {
            "sentence": "私は今勉強していません。",
            "translation": "I am not studying now.",
            "explanation": (
                "勉強していません describes an action "
                "that is not currently happening."
            ),
        },
    ],

    "N は Vたいです": [
        {
            "sentence": "私は日本に行きたいです。",
            "translation": "I want to go to Japan.",
            "explanation": (
                "行きたいです expresses desire."
            ),
        },
        {
            "sentence": "私はラーメンを食べたいです。",
            "translation": "I want to eat ramen.",
            "explanation": (
                "食べたいです expresses desire."
            ),
        },
    ],

    "N は Vたくないです": [
        {
            "sentence": "私は学校に行きたくないです。",
            "translation": "I do not want to go to school.",
            "explanation": (
                "行きたくないです expresses a desire not to go."
            ),
        },
        {
            "sentence": "私は魚を食べたくないです。",
            "translation": "I do not want to eat fish.",
            "explanation": (
                "食べたくないです expresses a desire not to eat."
            ),
        },
    ],

    "N から V": [
        {
            "sentence": "学校から帰ります。",
            "translation": "I return from school.",
            "explanation": (
                "学校 から marks the starting point."
            ),
        },
        {
            "sentence": "家から駅に行きます。",
            "translation": "I go to the station from home.",
            "explanation": (
                "家 から marks the starting point."
            ),
        },
    ],

    "N まで V": [
        {
            "sentence": "駅まで歩きます。",
            "translation": "I walk to the station.",
            "explanation": (
                "駅 まで marks the endpoint."
            ),
        },
        {
            "sentence": "学校まで行きます。",
            "translation": "I go as far as the school.",
            "explanation": (
                "学校 まで marks the endpoint."
            ),
        },
    ],

    "N も V": [
        {
            "sentence": "私も行きます。",
            "translation": "I will go too.",
            "explanation": (
                "私 も indicates an additional person."
            ),
        },
        {
            "sentence": "友達も勉強します。",
            "translation": "My friend studies too.",
            "explanation": (
                "友達 も indicates that the friend also acts."
            ),
        },
    ],

    "N へ V": [
        {
            "sentence": "学校へ行きます。",
            "translation": "I go to school.",
            "explanation": (
                "学校 へ indicates direction or destination."
            ),
        },
        {
            "sentence": "日本へ行きます。",
            "translation": "I go to Japan.",
            "explanation": (
                "日本 へ indicates the destination."
            ),
        },
    ],
}


def get_examples(pattern):

    return EXAMPLES.get(
        pattern,
        [],
    )


# ============================================================
# MAIN
# ============================================================

@app.get("/")
def home():

    return {
        "message": "AI Language Tutor is running!"
    }


@app.post("/analyze")
def analyze(request: LanguageRequest):

    # --------------------------------------------------------
    # 1. ROMAJI CONVERSION
    # --------------------------------------------------------

    original_text = request.text

    foreign_name_surfaces = set()

    if (
        request.target_language.lower() == "japanese"
        and is_romaji(request.text)
    ):

        foreign_name_surfaces = get_foreign_name_surfaces(
            request.text
        )

        request.text = romaji_to_japanese(
            request.text
        )

    # --------------------------------------------------------
    # 2. JAPANESE ANALYSIS
    # --------------------------------------------------------

    if request.target_language.lower() != "japanese":

        return {
            "error": (
                "Only Japanese analysis is currently implemented."
            )
        }

    linguistic_data = analyze_japanese(
        request.text
    )

    analyzed_words = linguistic_data["words"]

    # --------------------------------------------------------
    # 3. WORD INFORMATION
    # --------------------------------------------------------

    final_words = []

    unknown_words = []

    for word in analyzed_words:

        surface = word["word"]
        pos = word["pos"]

        meaning = get_basic_meaning(
            surface
        )

        # Foreign names should not receive
        # an invented dictionary meaning.
        if surface in foreign_name_surfaces:

            meaning = "foreign name"

        if (
            meaning is None
            and pos != "助詞"
            and surface not in foreign_name_surfaces
        ):

            unknown_words.append(
                surface
            )

        final_words.append({

            "word": surface,

            "reading": word["reading"],

            "romaji": word["romaji"],

            "meaning": meaning,

            "part_of_speech": pos,

            "role": get_basic_role(
                surface,
                pos,
                analyzed_words,
            ),

        })
    # --------------------------------------------------------
    # 4. UNKNOWN WORDS
    # --------------------------------------------------------

    if unknown_words:

        try:

            unknown_meanings = (
                get_unknown_word_meanings(
                    unknown_words
                )
            )

            if unknown_meanings:

                for word in final_words:

                    if (
                        word["word"]
                        in unknown_meanings
                    ):

                        word["meaning"] = (
                            unknown_meanings[
                                word["word"]
                            ]
                        )

        except Exception as error:

            print(
                "Unknown vocabulary error:",
                error,
            )

    # --------------------------------------------------------
    # 5. NATURALNESS
    # --------------------------------------------------------

    sentence_check = detect_sentence_issue(
        analyzed_words
    )

    # --------------------------------------------------------
    # 6. GRAMMAR
    # --------------------------------------------------------

    detected_grammar = detect_grammar(
        analyzed_words
    )

    if not sentence_check["natural"]:

        detected_grammar = [
            grammar
            for grammar in detected_grammar
            if grammar["pattern"] not in [
                "N は N で Vます",
                "N は N で Vました",
            ]
        ]

    # --------------------------------------------------------
    # 7. TRANSLATION
    # --------------------------------------------------------

    translation = build_basic_translation(
        analyzed_words
    )

    if translation is None:

        try:

            translation = generate_translation(
    request.text if any(
        "\u3040" <= char <= "\u30ff"
        or "\u4e00" <= char <= "\u9fff"
        for char in request.text
    ) else romaji_to_japanese(request.text),
    request.known_language,
)

        except Exception as error:

            print(
                "Translation error:",
                error,
            )

            translation = ""

    # --------------------------------------------------------
    # 8. GRAMMAR EXPLANATION
    # --------------------------------------------------------

    final_grammar = []

    for grammar in detected_grammar:

        try:

            explanation = (
                generate_grammar_explanation(
                    request.text,
                    grammar,
                    analyzed_words,
                )
            )

        except Exception:

            explanation = (
                f"{grammar['pattern']} means "
                f"{grammar['meaning']}."
            )

        final_grammar.append({

            "pattern": grammar["pattern"],

            "meaning": grammar["meaning"],

            "explanation": explanation,

        })

    # --------------------------------------------------------
    # 9. EXAMPLES
    # --------------------------------------------------------

    final_examples = []

    for grammar in detected_grammar:

        pattern = grammar["pattern"]

        examples = get_examples(
            pattern
        )

        final_examples.extend(
            examples
        )

        if len(final_examples) >= 2:
            break

    final_examples = final_examples[:2]

    # --------------------------------------------------------
    # 10. CORRECTION
    # --------------------------------------------------------

    correction_data = get_correction(
        request.text,
        analyzed_words,
    )

    
    # --------------------------------------------------------
    # 11. SAVE VOCABULARY
    # --------------------------------------------------------

    for word in final_words:

        try:
            word_text = (word.get("word") or "").strip()
            reading = (word.get("reading") or "").strip()
            romaji = (word.get("romaji") or "").strip()
            meaning = (word.get("meaning") or "").strip()
            pos = (word.get("part_of_speech") or "").strip()

            if not word_text:
                continue

            if not meaning:
                continue

            if not reading:
                continue

            if word_text in foreign_name_surfaces:
                continue

            if (
                len(word_text) <= 2
                and re.fullmatch(r"[a-zA-Z]+", word_text)
            ):
                continue

            
            save_vocabulary(
                word=word_text,
                reading=reading,
                romaji=romaji,
                meaning=meaning,
                part_of_speech=pos,
                role=word.get("role", ""),
                learning_language=request.target_language,
                support_language=request.known_language,
            )


        except Exception as error:
            print(
                "Vocabulary save error:",
                error,
            )

    # --------------------------------------------------------
    # 12. RESPONSE
    # --------------------------------------------------------

    return {

        "input": original_text,

        "sentence": request.text,

        "input_was_romaji": (
            original_text != request.text
        ),

        "words": final_words,

        "translation": translation,

        "grammar": final_grammar,

        "examples": final_examples,

        "natural": sentence_check["natural"],

        "correction": (
            correction_data["correction"]
        ),

        "correction_explanation": (
            correction_data["explanation"]
        ),

    }
# ============================================================
# SMART REVIEW - SUBMIT RESULT
# ============================================================

@app.post("/vocabulary/review")
def submit_review(request: ReviewResultRequest):

    success = record_review_result(
        request.vocabulary_id,
        request.correct
    )

    if not success:
        return {
            "success": False,
            "message": "Vocabulary word not found"
        }

    return {
        "success": True,
        "vocabulary_id": request.vocabulary_id,
        "correct": request.correct
    }


# ============================================================
# SMART REVIEW - GET WEAK WORDS
# ============================================================

@app.get("/vocabulary/weak")
def get_weak_words():

    vocabulary = get_weak_vocabulary(limit=10)

    return {
        "vocabulary": vocabulary
    }


# ============================================================
# VOCABULARY STATISTICS
# ============================================================

@app.get("/vocabulary/stats")
def get_vocabulary_statistics():

    return get_vocabulary_stats()

# ============================================================
# JLPT LISTENING PRACTICE
# ============================================================

class ListeningGenerateRequest(BaseModel):
    level: str = "N5"
    count: int = 5



# Curated N5 listening exercises.
# Keep these sentences and translations together so they cannot
# accidentally disagree with each other.
#@app.post("/listening/generate")
N5_LISTENING_QUESTIONS = [
    {
        "sentence": "私は毎朝七時に起きます。",
        "translation": "I get up at seven every morning.",
        "options": [
            "I get up at seven every morning.",
            "I go to bed at seven every night.",
            "I eat breakfast at eight every morning.",
            "I go to school at seven every evening.",
        ],
        "answer": "I get up at seven every morning.",
        "explanation": "毎朝 means every morning, 七時 means seven o'clock, and 起きます means get up.",
    },
    {
        "sentence": "駅の前に銀行があります。",
        "translation": "There is a bank in front of the station.",
        "options": [
            "There is a bank in front of the station.",
            "There is a hospital behind the station.",
            "There is a school inside the station.",
            "There is a restaurant next to the airport.",
        ],
        "answer": "There is a bank in front of the station.",
        "explanation": "駅 means station, 前 means in front, and あります expresses the existence of a thing.",
    },
    {
        "sentence": "昨日、友達と映画を見ました。",
        "translation": "I watched a movie with a friend yesterday.",
        "options": [
            "I watched a movie with a friend yesterday.",
            "I read a book with my teacher today.",
            "I watched television with my family tomorrow.",
            "I bought a movie ticket this morning.",
        ],
        "answer": "I watched a movie with a friend yesterday.",
        "explanation": "昨日 means yesterday, 友達と means with a friend, and 映画を見ました means watched a movie.",
    },
    {
        "sentence": "このりんごは一つ百円です。",
        "translation": "These apples cost 100 yen each.",
        "options": [
            "These apples cost 100 yen each.",
            "This orange costs 200 yen.",
            "These apples cost 1000 yen each.",
            "I bought one apple yesterday.",
        ],
        "answer": "These apples cost 100 yen each.",
        "explanation": "この means this, りんご means apple, and 一つ百円 means 100 yen for one.",
    },
    {
        "sentence": "日曜日は家で日本語を勉強します。",
        "translation": "I study Japanese at home on Sundays.",
        "options": [
            "I study Japanese at home on Sundays.",
            "I teach English at school on Mondays.",
            "I study mathematics at the library every day.",
            "I speak Japanese at work on Saturdays.",
        ],
        "answer": "I study Japanese at home on Sundays.",
        "explanation": "日曜日 means Sunday, 家で means at home, and 日本語を勉強します means study Japanese.",
    },
    {
        "sentence": "水を一杯ください。",
        "translation": "A glass of water, please.",
        "options": [
            "A glass of water, please.",
            "A cup of coffee, please.",
            "Two bottles of milk, please.",
            "A glass of juice, please.",
        ],
        "answer": "A glass of water, please.",
        "explanation": "水 means water, 一杯 is a counter used for a cup or glass, and ください is a polite request.",
    },
    {
        "sentence": "田中さんはバスで会社へ行きます。",
        "translation": "Mr. or Ms. Tanaka goes to work by bus.",
        "options": [
            "Mr. or Ms. Tanaka goes to work by bus.",
            "Tanaka goes home by train.",
            "Tanaka walks to school.",
            "Tanaka goes to the station by taxi.",
        ],
        "answer": "Mr. or Ms. Tanaka goes to work by bus.",
        "explanation": "バスで indicates the means of transportation, and 会社へ行きます means go to the company or workplace.",
    },
    {
        "sentence": "今日はとても寒いです。",
        "translation": "It is very cold today.",
        "options": [
            "It is very cold today.",
            "It is very hot today.",
            "It was cold yesterday.",
            "It is raining heavily today.",
        ],
        "answer": "It is very cold today.",
        "explanation": "今日 means today, とても means very, and 寒い means cold when describing the weather or temperature.",
    },
    {
        "sentence": "妹は部屋で音楽を聞いています。",
        "translation": "My younger sister is listening to music in her room.",
        "options": [
            "My younger sister is listening to music in her room.",
            "My older brother is reading a book in the library.",
            "My younger sister is watching television in the kitchen.",
            "My mother is listening to music at work.",
        ],
        "answer": "My younger sister is listening to music in her room.",
        "explanation": "妹 means younger sister, 部屋で means in the room, and 音楽を聞いています means is listening to music.",
    },
    {
        "sentence": "すみません、トイレはどこですか。",
        "translation": "Excuse me, where is the restroom?",
        "options": [
            "Excuse me, where is the restroom?",
            "Excuse me, what time is it?",
            "Where is the train station?",
            "May I have some water, please?",
        ],
        "answer": "Excuse me, where is the restroom?",
        "explanation": "すみません is a polite way to get someone's attention or say excuse me. どこ means where.",
    },
    
    {
        "sentence": "毎朝、コーヒーを飲んでから会社へ行きます。",
        "translation": "Every morning, I go to work after drinking coffee.",
        "options": [
            "I go to work before drinking coffee.",
            "I go to work after drinking coffee every morning.",
            "I drink coffee at work every evening.",
            "I don't drink coffee in the morning."
        ],
        "answer": "I go to work after drinking coffee every morning.",
        "explanation": "毎朝 means every morning, and ～てから means after doing something."
    },
    {
        "sentence": "来週の月曜日に友達と買い物に行きます。",
        "translation": "I will go shopping with a friend next Monday.",
        "options": [
            "I went shopping with a friend last Monday.",
            "I will go shopping alone tomorrow.",
            "I will go shopping with a friend next Monday.",
            "I will meet my friend at school next week."
        ],
        "answer": "I will go shopping with a friend next Monday.",
        "explanation": "来週 means next week, 月曜日 means Monday, and 買い物に行きます means go shopping."
    },
    {
        "sentence": "この部屋は広くて、とても明るいです。",
        "translation": "This room is spacious and very bright.",
        "options": [
            "This room is small and dark.",
            "This room is spacious and very bright.",
            "This room is clean but cold.",
            "This room is noisy and crowded."
        ],
        "answer": "This room is spacious and very bright.",
        "explanation": "広い means spacious, and 明るい means bright."
    },
    {
        "sentence": "すみません、次のバスは何時に来ますか。",
        "translation": "Excuse me, what time does the next bus arrive?",
        "options": [
            "Where does the next bus go?",
            "What time did the last bus leave?",
            "What time does the next bus arrive?",
            "How much is a bus ticket?"
        ],
        "answer": "What time does the next bus arrive?",
        "explanation": "次 means next, バス means bus, and 何時 means what time."
    },
    {
        "sentence": "私は魚が好きですが、肉はあまり食べません。",
        "translation": "I like fish, but I don't eat meat very often.",
        "options": [
            "I like meat but never eat fish.",
            "I like fish but don't eat meat very often.",
            "I eat fish and meat every day.",
            "I don't like fish or meat."
        ],
        "answer": "I like fish but don't eat meat very often.",
        "explanation": "好き means like, ですが expresses contrast, and あまり with a negative means not very often or not much."
    },
    {
        "sentence": "昨日は疲れていたので、早く寝ました。",
        "translation": "I was tired yesterday, so I went to bed early.",
        "options": [
            "I went to bed late because I was busy.",
            "I slept early because I was tired yesterday.",
            "I woke up early yesterday.",
            "I was tired but went shopping."
        ],
        "answer": "I slept early because I was tired yesterday.",
        "explanation": "疲れていた means was tired, ので gives a reason, and 早く寝ました means went to bed early."
    },
    {
        "sentence": "図書館では静かにしてください。",
        "translation": "Please be quiet in the library.",
        "options": [
            "Please eat quietly in the library.",
            "Please speak loudly in the library.",
            "Please be quiet in the library.",
            "Please return the books tomorrow."
        ],
        "answer": "Please be quiet in the library.",
        "explanation": "図書館 means library, and 静かにしてください is a request to be quiet."
    },
    {
        "sentence": "駅から会社まで歩いて十五分かかります。",
        "translation": "It takes fifteen minutes to walk from the station to the office.",
        "options": [
            "It takes fifteen minutes to walk from the station to the office.",
            "The office is fifteen minutes away by train.",
            "It takes fifty minutes to walk to the station.",
            "The station is next to the office."
        ],
        "answer": "It takes fifteen minutes to walk from the station to the office.",
        "explanation": "駅から means from the station, まで means to, and ～分かかります expresses how long something takes."
    },
    {
        "sentence": "窓を開けてもいいですか。",
        "translation": "May I open the window?",
        "options": [
            "Should I close the door?",
            "May I open the window?",
            "Can you clean the window?",
            "Did you open the door?"
        ],
        "answer": "May I open the window?",
        "explanation": "窓 means window, 開ける means open, and ～てもいいですか asks permission."
    },
    {
        "sentence": "母はスーパーで野菜と卵を買いました。",
        "translation": "My mother bought vegetables and eggs at the supermarket.",
        "options": [
            "My mother bought vegetables and eggs at the supermarket.",
            "My father bought fruit at the market.",
            "My mother cooked fish and rice at home.",
            "My sister bought eggs at school."
        ],
        "answer": "My mother bought vegetables and eggs at the supermarket.",
        "explanation": "母 means mother, スーパー means supermarket, and 買いました means bought."
    },

]



N4_LISTENING_QUESTIONS = [
    {
        "sentence": "もし明日雨が降ったら、試合は中止になるそうです。",
        "translation": "I hear that if it rains tomorrow, the match will be cancelled.",
        "options": [
            "The match will be cancelled if it rains tomorrow.",
            "The match was cancelled yesterday.",
            "The match will continue even if it rains.",
            "The match has already finished."
        ],
        "answer": "The match will be cancelled if it rains tomorrow.",
        "explanation": "もし〜たら expresses a condition, and そうです can report information you have heard."
    },
    {
        "sentence": "財布を忘れてしまったので、友達にお金を借りました。",
        "translation": "Because I had forgotten my wallet, I borrowed money from a friend.",
        "options": [
            "I lent my friend some money.",
            "I borrowed money from a friend because I forgot my wallet.",
            "I found my wallet at a shop.",
            "My friend borrowed my wallet."
        ],
        "answer": "I borrowed money from a friend because I forgot my wallet.",
        "explanation": "忘れてしまった expresses an unfortunate completed action; 借りました means borrowed."
    },
    {
        "sentence": "この機械の使い方が分からなければ、説明書を読んでください。",
        "translation": "If you don't understand how to use this machine, please read the instructions.",
        "options": [
            "Please buy a new machine.",
            "Read the instructions if you don't understand how to use the machine.",
            "The machine is broken, so stop using it.",
            "You should lend the instructions to someone."
        ],
        "answer": "Read the instructions if you don't understand how to use the machine.",
        "explanation": "使い方 means how to use something, and 分からなければ means if you don't understand."
    },
    {
        "sentence": "田中さんは忙しいと言っていたので、あとで電話することにしました。",
        "translation": "Since Tanaka said they were busy, I decided to call later.",
        "options": [
            "Tanaka called me because they were free.",
            "I decided to call Tanaka later because they said they were busy.",
            "I met Tanaka this morning.",
            "Tanaka asked me to visit tomorrow."
        ],
        "answer": "I decided to call Tanaka later because they said they were busy.",
        "explanation": "と言っていた reports what someone said; ことにしました means decided to do something."
    },
    {
        "sentence": "駅まで歩いて行くつもりでしたが、雨が強くなったのでバスに乗りました。",
        "translation": "I intended to walk to the station, but the rain got heavier, so I took the bus.",
        "options": [
            "I walked to the station because the weather was nice.",
            "I planned to walk, but took the bus because the rain got heavier.",
            "I took the train because the bus was late.",
            "I waited at the station for the rain to stop."
        ],
        "answer": "I planned to walk, but took the bus because the rain got heavier.",
        "explanation": "つもりでした indicates a past intention, while が contrasts the plan with what actually happened."
    },
    {
        "sentence": "日本に住んでいる間に、富士山に登ってみたいです。",
        "translation": "While living in Japan, I would like to try climbing Mount Fuji.",
        "options": [
            "I climbed Mount Fuji before moving to Japan.",
            "I want to try climbing Mount Fuji while living in Japan.",
            "I don't want to live in Japan.",
            "I will move away from Japan tomorrow."
        ],
        "answer": "I want to try climbing Mount Fuji while living in Japan.",
        "explanation": "間に means while or during, and 〜てみたい means want to try doing something."
    },
    {
        "sentence": "会議に遅れないように、いつもより早く家を出ました。",
        "translation": "I left home earlier than usual so that I wouldn't be late for the meeting.",
        "options": [
            "I left home late because the meeting was cancelled.",
            "I left home earlier than usual to avoid being late for the meeting.",
            "I arrived early and cancelled the meeting.",
            "I forgot where the meeting was."
        ],
        "answer": "I left home earlier than usual to avoid being late for the meeting.",
        "explanation": "〜ないように expresses doing something to avoid an unwanted result."
    },
    {
        "sentence": "この町に引っ越してきてから、近所の人たちと仲良くなりました。",
        "translation": "Since moving to this town, I have become friendly with the neighbors.",
        "options": [
            "I have become friendly with the neighbors since moving here.",
            "I moved away from this town yesterday.",
            "My neighbors are moving to another country.",
            "I have never spoken to anyone in this town."
        ],
        "answer": "I have become friendly with the neighbors since moving here.",
        "explanation": "引っ越してきてから means since moving here, and 仲良くなりました means became friendly."
    },
    {
        "sentence": "母に頼まれたので、仕事の帰りに牛乳を買って帰りました。",
        "translation": "Because my mother asked me to, I bought milk on my way home from work.",
        "options": [
            "My mother bought milk on her way to work.",
            "I bought milk on my way home from work because my mother asked me to.",
            "I forgot to go to work.",
            "I asked my mother to buy a new car."
        ],
        "answer": "I bought milk on my way home from work because my mother asked me to.",
        "explanation": "頼まれた means was asked, and 仕事の帰りに means on the way home from work."
    },
    {
        "sentence": "このアプリを使えば、漢字の読み方を簡単に調べられます。",
        "translation": "If you use this app, you can easily look up how to read kanji.",
        "options": [
            "This app teaches you how to cook Japanese food.",
            "You can easily look up kanji readings using this app.",
            "You must write every kanji from memory.",
            "This app only works without internet."
        ],
        "answer": "You can easily look up kanji readings using this app.",
        "explanation": "使えば expresses a condition, and 調べられます means can look up or check."
    },
    
    {
        "sentence": "電車の中に傘を忘れたことに気づきました。",
        "translation": "I realized that I had left my umbrella on the train.",
        "options": [
            "I bought an umbrella at the station.",
            "I realized that I had left my umbrella on the train.",
            "I found an umbrella outside.",
            "I forgot my ticket on the bus."
        ],
        "answer": "I realized that I had left my umbrella on the train.",
        "explanation": "忘れた means forgot or left behind, and 気づきました means realized or noticed."
    },
    {
        "sentence": "体の調子が悪いので、今日は早く帰ることにしました。",
        "translation": "I don't feel well, so I decided to go home early today.",
        "options": [
            "I decided to stay at work late today.",
            "I went home early because I wasn't feeling well.",
            "I felt better and went shopping.",
            "I decided to visit a friend tomorrow."
        ],
        "answer": "I went home early because I wasn't feeling well.",
        "explanation": "調子が悪い means to feel unwell, and ことにしました means decided to do something."
    },
    {
        "sentence": "この道をまっすぐ行けば、右側に郵便局があります。",
        "translation": "If you go straight along this road, the post office will be on your right.",
        "options": [
            "The post office is on the left after turning.",
            "Go straight and the post office will be on your right.",
            "The post office is behind the station.",
            "Turn right immediately to find the hospital."
        ],
        "answer": "Go straight and the post office will be on your right.",
        "explanation": "まっすぐ means straight, 右側 means right side, and ～ば expresses a condition."
    },
    {
        "sentence": "雨が降っていたため、試合は体育館で行われました。",
        "translation": "Because it was raining, the match was held in the gymnasium.",
        "options": [
            "The match was cancelled because of the rain.",
            "The match was held outdoors.",
            "The match was held in the gym because it was raining.",
            "The match was postponed until next week."
        ],
        "answer": "The match was held in the gym because it was raining.",
        "explanation": "ため indicates a reason, and 体育館 means gymnasium."
    },
    {
        "sentence": "旅行に行く前に、ホテルを予約しておきました。",
        "translation": "I booked a hotel in advance before going on the trip.",
        "options": [
            "I booked a hotel in advance before the trip.",
            "I cancelled my hotel after the trip.",
            "I decided not to travel.",
            "I booked a flight after arriving."
        ],
        "answer": "I booked a hotel in advance before the trip.",
        "explanation": "前に means before, and ～ておく describes doing something in preparation."
    },
    {
        "sentence": "この料理は見た目より辛くなかったです。",
        "translation": "This dish wasn't as spicy as it looked.",
        "options": [
            "The dish was much spicier than expected.",
            "The dish wasn't as spicy as it looked.",
            "The dish looked delicious but tasted sweet.",
            "The dish was too hot to eat."
        ],
        "answer": "The dish wasn't as spicy as it looked.",
        "explanation": "より compares things, and 辛くなかった means was not spicy."
    },
    {
        "sentence": "先生に質問したところ、分かりやすく説明してくれました。",
        "translation": "When I asked the teacher a question, they explained it clearly for me.",
        "options": [
            "The teacher refused to answer.",
            "The teacher gave a clear explanation when I asked.",
            "I explained the lesson to the teacher.",
            "The teacher asked me to leave."
        ],
        "answer": "The teacher gave a clear explanation when I asked.",
        "explanation": "質問した means asked a question, and 説明してくれました means explained it for me."
    },
    {
        "sentence": "電気を消さないまま、部屋を出てしまいました。",
        "translation": "I left the room without turning off the light.",
        "options": [
            "I turned off the light before leaving.",
            "I left the room without turning off the light.",
            "I forgot to open the window.",
            "I stayed in the room all night."
        ],
        "answer": "I left the room without turning off the light.",
        "explanation": "～ないまま means without doing something, and 出てしまいました describes a completed action that may be regrettable."
    },
    {
        "sentence": "来月から新しい仕事を始めることになっています。",
        "translation": "It has been decided that I will start a new job next month.",
        "options": [
            "I quit my job last month.",
            "I will start a new job next month as planned.",
            "I am looking for a job next year.",
            "I started a new job yesterday."
        ],
        "answer": "I will start a new job next month as planned.",
        "explanation": "来月 means next month, and ことになっています expresses an established arrangement or decision."
    },
    {
        "sentence": "道が混んでいたので、約束の時間に遅れてしまいました。",
        "translation": "Because the roads were congested, I ended up being late for the appointment.",
        "options": [
            "I arrived early because the roads were empty.",
            "The appointment was cancelled.",
            "I was late because of traffic congestion.",
            "I forgot the location of the appointment."
        ],
        "answer": "I was late because of traffic congestion.",
        "explanation": "道が混んでいた means the roads were congested, and 遅れてしまいました means ended up being late."
    },

]

N3_LISTENING_QUESTIONS = [
    {
        "sentence": "会議が終わったら、資料を送ってください。",
        "translation": "Please send me the documents after the meeting ends.",
        "options": [
            "Send the documents before the meeting.",
            "Send the documents after the meeting.",
            "Cancel the meeting.",
            "Print the documents tomorrow."
        ],
        "answer": "Send the documents after the meeting.",
        "explanation": "終わったら means 'after something finishes'."
    },
    {
        "sentence": "電車が遅れたため、会議に間に合いませんでした。",
        "translation": "Because the train was delayed, I didn't make it to the meeting on time.",
        "options": [
            "The meeting was cancelled.",
            "The train arrived early.",
            "The train delay made me late for the meeting.",
            "The meeting started late."
        ],
        "answer": "The train delay made me late for the meeting.",
        "explanation": "ため indicates a reason or cause."
    },
    {
        "sentence": "この店は値段が安いだけでなく、料理もおいしいです。",
        "translation": "This restaurant is not only inexpensive, but its food is also delicious.",
        "options": [
            "The restaurant is expensive.",
            "The food is cheap but unpleasant.",
            "The restaurant is cheap and the food is tasty.",
            "The restaurant only sells drinks."
        ],
        "answer": "The restaurant is cheap and the food is tasty.",
        "explanation": "だけでなく means 'not only ... but also'."
    },
    {
        "sentence": "雨が降りそうなので、傘を持っていきます。",
        "translation": "It looks like it will rain, so I'll take an umbrella.",
        "options": [
            "It has stopped raining.",
            "The speaker will take an umbrella because rain seems likely.",
            "The speaker lost an umbrella.",
            "It will be sunny."
        ],
        "answer": "The speaker will take an umbrella because rain seems likely.",
        "explanation": "降りそう means 'looks likely to rain'."
    },
    {
        "sentence": "田中さんは忙しいと言っていましたが、あとで電話すると約束しました。",
        "translation": "Tanaka said they were busy, but promised to call later.",
        "options": [
            "Tanaka promised to visit tomorrow.",
            "Tanaka refused to call.",
            "Tanaka promised to call later.",
            "Tanaka called before the conversation."
        ],
        "answer": "Tanaka promised to call later.",
        "explanation": "約束しました means 'promised'."
    },
    {
        "sentence": "説明を聞いても、使い方がよく分かりません。",
        "translation": "Even after listening to the explanation, I still don't understand how to use it.",
        "options": [
            "The speaker understands everything.",
            "The speaker still doesn't understand how to use it.",
            "Nobody gave an explanation.",
            "The item cannot be used."
        ],
        "answer": "The speaker still doesn't understand how to use it.",
        "explanation": "聞いても expresses 'even after listening'."
    },
    {
        "sentence": "健康のために、毎朝三十分歩くことにしています。",
        "translation": "For my health, I make a habit of walking for thirty minutes every morning.",
        "options": [
            "The speaker walks for thirty minutes every morning for health.",
            "The speaker runs for three hours.",
            "The speaker walks only on weekends.",
            "The speaker stopped exercising."
        ],
        "answer": "The speaker walks for thirty minutes every morning for health.",
        "explanation": "ことにしています describes a personal habit or routine."
    },
    {
        "sentence": "予約しておいたのに、店は休みでした。",
        "translation": "Even though I had made a reservation, the restaurant was closed.",
        "options": [
            "The restaurant was crowded.",
            "The reservation was for tomorrow.",
            "The restaurant was closed despite the reservation.",
            "The speaker forgot to make a reservation."
        ],
        "answer": "The restaurant was closed despite the reservation.",
        "explanation": "のに expresses an unexpected result or contrast."
    },
    {
        "sentence": "この仕事は思ったより時間がかかりました。",
        "translation": "This work took more time than I expected.",
        "options": [
            "The work finished early.",
            "The work took longer than expected.",
            "The work was cancelled.",
            "The work was easier than expected."
        ],
        "answer": "The work took longer than expected.",
        "explanation": "思ったより means 'more than I thought or expected'."
    },
    {
        "sentence": "道に迷ったときは、近くの人に聞くといいですよ。",
        "translation": "When you get lost, it's a good idea to ask someone nearby.",
        "options": [
            "You should keep walking without help.",
            "You should call the restaurant.",
            "You should ask someone nearby when lost.",
            "You should wait until morning."
        ],
        "answer": "You should ask someone nearby when lost.",
        "explanation": "といいですよ gives friendly advice."
    },
    
    {
        "sentence": "新しい仕事に慣れるまで、少し時間がかかりました。",
        "translation": "It took a little time to get used to the new job.",
        "options": [
            "I immediately enjoyed my new job.",
            "It took a little time to get used to the new job.",
            "I decided to leave my job.",
            "My new job was cancelled."
        ],
        "answer": "It took a little time to get used to the new job.",
        "explanation": "慣れる means to get used to something, and ～まで means until."
    },
    {
        "sentence": "電車に乗っている間に、友達からメッセージが届きました。",
        "translation": "While I was on the train, I received a message from a friend.",
        "options": [
            "I sent a message before boarding the train.",
            "I received a message from a friend while on the train.",
            "My friend missed the train.",
            "I called my friend after arriving."
        ],
        "answer": "I received a message from a friend while on the train.",
        "explanation": "～ている間に means while doing something, and 届きました means arrived or was received."
    },
    {
        "sentence": "健康のために、甘い飲み物を飲むのを控えています。",
        "translation": "For my health, I am cutting back on sugary drinks.",
        "options": [
            "I drink sugary drinks more often now.",
            "I have stopped eating all meals.",
            "I am cutting back on sugary drinks for my health.",
            "I only drink coffee for breakfast."
        ],
        "answer": "I am cutting back on sugary drinks for my health.",
        "explanation": "控える means to refrain from or cut back on something."
    },
    {
        "sentence": "会議の資料を準備しておいたおかげで、発表はうまくいきました。",
        "translation": "Thanks to preparing the meeting materials in advance, the presentation went well.",
        "options": [
            "The presentation went badly because the materials were missing.",
            "Preparing the materials in advance helped the presentation go well.",
            "The meeting was cancelled.",
            "The materials were prepared after the presentation."
        ],
        "answer": "Preparing the materials in advance helped the presentation go well.",
        "explanation": "～ておく means to do something in advance, and おかげで expresses a positive result thanks to something."
    },
    {
        "sentence": "この道具は使い方さえ分かれば、誰でも簡単に使えます。",
        "translation": "As long as you know how to use this tool, anyone can use it easily.",
        "options": [
            "Only experts can use this tool.",
            "The tool is too difficult for everyone.",
            "Anyone can use it easily if they know how to use it.",
            "The tool cannot be used without electricity."
        ],
        "answer": "Anyone can use it easily if they know how to use it.",
        "explanation": "～さえ～ば means as long as a necessary condition is met."
    },
    {
        "sentence": "説明を聞いたうえで、参加するかどうか決めてください。",
        "translation": "After listening to the explanation, please decide whether to participate.",
        "options": [
            "Decide whether to participate before hearing anything.",
            "Listen to the explanation and then decide whether to participate.",
            "Participate without asking any questions.",
            "Explain the rules to the organizer."
        ],
        "answer": "Listen to the explanation and then decide whether to participate.",
        "explanation": "～たうえで means after doing something, with the action serving as a basis for the next decision."
    },
    {
        "sentence": "彼は忙しいにもかかわらず、私の相談に乗ってくれました。",
        "translation": "Despite being busy, he listened to my concerns and helped me.",
        "options": [
            "He refused to speak to me because he was busy.",
            "He asked me to solve his problem.",
            "He helped me despite being busy.",
            "He cancelled all his plans."
        ],
        "answer": "He helped me despite being busy.",
        "explanation": "にもかかわらず means despite or even though."
    },
    {
        "sentence": "雨が止み次第、出発する予定です。",
        "translation": "We plan to leave as soon as the rain stops.",
        "options": [
            "We plan to leave before the rain starts.",
            "We will leave as soon as the rain stops.",
            "We cancelled the trip because of rain.",
            "We will wait until tomorrow regardless of the weather."
        ],
        "answer": "We will leave as soon as the rain stops.",
        "explanation": "～次第 means as soon as a particular event occurs."
    },
    {
        "sentence": "何度も練習した結果、以前より上手に話せるようになりました。",
        "translation": "As a result of practicing many times, I became able to speak better than before.",
        "options": [
            "I stopped practicing and forgot how to speak.",
            "I could speak better after practicing repeatedly.",
            "I spoke well without any practice.",
            "My speaking ability became worse."
        ],
        "answer": "I could speak better after practicing repeatedly.",
        "explanation": "結果 means result, and ～ようになる expresses a change in ability or state."
    },
    {
        "sentence": "忘れ物をしないように、出かける前にかばんの中を確認します。",
        "translation": "I check inside my bag before leaving so that I don't forget anything.",
        "options": [
            "I check my bag before leaving to avoid forgetting things.",
            "I leave my bag at home every day.",
            "I check my bag only after returning.",
            "I buy a new bag before every trip."
        ],
        "answer": "I check my bag before leaving to avoid forgetting things.",
        "explanation": "～ないように expresses taking action to avoid an unwanted result."
    },

]

N2_LISTENING_QUESTIONS = [
    {
        "sentence": "会議の開始時間が変更になったことを、参加者全員に知らせておいてください。",
        "translation": "Please make sure all participants are informed that the meeting's start time has changed.",
        "options": [
            "Cancel the meeting.",
            "Inform all participants of the changed start time.",
            "Change the meeting location.",
            "Ask participants to arrive a day early."
        ],
        "answer": "Inform all participants of the changed start time.",
        "explanation": "知らせておく means to inform someone in advance."
    },
    {
        "sentence": "彼は経験が豊富なだけあって、難しい問題にも落ち着いて対応した。",
        "translation": "As expected of someone with extensive experience, he handled the difficult problem calmly.",
        "options": [
            "He ignored the difficult problem.",
            "He panicked because he lacked experience.",
            "He handled the difficult problem calmly.",
            "He asked someone else to solve it."
        ],
        "answer": "He handled the difficult problem calmly.",
        "explanation": "だけあって indicates that the result is fitting or expected."
    },
    {
        "sentence": "予算が限られている以上、優先順位を決めざるを得ない。",
        "translation": "Since the budget is limited, we have no choice but to set priorities.",
        "options": [
            "Increase the budget immediately.",
            "Ignore all the tasks.",
            "Set priorities because the budget is limited.",
            "Postpone every decision indefinitely."
        ],
        "answer": "Set priorities because the budget is limited.",
        "explanation": "ざるを得ない means 'have no choice but to'."
    },
    {
        "sentence": "彼女は忙しいにもかかわらず、最後まで相談に乗ってくれた。",
        "translation": "Despite being busy, she stayed and listened to my concerns until the end.",
        "options": [
            "She refused to help.",
            "She helped despite being busy.",
            "She finished work early.",
            "She asked for advice instead."
        ],
        "answer": "She helped despite being busy.",
        "explanation": "にもかかわらず means 'despite' or 'even though'."
    },
    {
        "sentence": "新しい制度を導入するにあたって、社員の意見を集めることになった。",
        "translation": "When introducing the new system, it was decided that employees' opinions would be collected.",
        "options": [
            "The system was abandoned.",
            "Employees were told not to comment.",
            "Employee opinions would be collected before introducing the system.",
            "The system had already been removed."
        ],
        "answer": "Employee opinions would be collected before introducing the system.",
        "explanation": "にあたって means 'when undertaking or beginning something'."
    },
    {
        "sentence": "この結果は、長年の研究の積み重ねによるものだ。",
        "translation": "This result is due to years of accumulated research.",
        "options": [
            "The result was accidental.",
            "The result came from years of research.",
            "The research began yesterday.",
            "The result has no explanation."
        ],
        "answer": "The result came from years of research.",
        "explanation": "積み重ね means accumulation over time."
    },
    {
        "sentence": "説明書を読んだものの、機械を正しく操作できなかった。",
        "translation": "Although I read the instructions, I couldn't operate the machine correctly.",
        "options": [
            "The machine worked perfectly.",
            "The speaker did not read the instructions.",
            "The speaker couldn't operate the machine correctly despite reading the instructions.",
            "The instructions were never provided."
        ],
        "answer": "The speaker couldn't operate the machine correctly despite reading the instructions.",
        "explanation": "ものの expresses a contrast between expectation and outcome."
    },
    {
        "sentence": "交通渋滞を考慮して、予定より早く出発することにした。",
        "translation": "Taking traffic congestion into account, we decided to leave earlier than planned.",
        "options": [
            "Leave later than planned.",
            "Cancel the trip because of traffic.",
            "Leave earlier because traffic congestion was considered.",
            "Change the destination."
        ],
        "answer": "Leave earlier because traffic congestion was considered.",
        "explanation": "考慮して means 'taking into consideration'."
    },
    {
        "sentence": "彼の発言は誤解を招きかねないので、表現を見直したほうがいい。",
        "translation": "His statement could cause a misunderstanding, so he should reconsider the wording.",
        "options": [
            "His statement is impossible to understand.",
            "His wording may cause misunderstanding and should be reviewed.",
            "His statement should be published immediately.",
            "His statement has already been corrected by everyone."
        ],
        "answer": "His wording may cause misunderstanding and should be reviewed.",
        "explanation": "かねない indicates a possibility of an undesirable outcome."
    },
    {
        "sentence": "締め切りに間に合わせるために、作業の進み具合を毎日確認している。",
        "translation": "To meet the deadline, we check the progress of the work every day.",
        "options": [
            "The deadline has been cancelled.",
            "The work is no longer monitored.",
            "Progress is checked daily to meet the deadline.",
            "The work will begin after the deadline."
        ],
        "answer": "Progress is checked daily to meet the deadline.",
        "explanation": "進み具合 means the state or degree of progress."
    },
    
    {
        "sentence": "予想に反して、会議は予定より早く終わった。",
        "translation": "Contrary to expectations, the meeting ended earlier than scheduled.",
        "options": [
            "The meeting lasted much longer than expected.",
            "The meeting was cancelled before it began.",
            "The meeting ended earlier than scheduled, contrary to expectations.",
            "The meeting started later than planned."
        ],
        "answer": "The meeting ended earlier than scheduled, contrary to expectations.",
        "explanation": "予想に反して means contrary to expectations, and 予定より早く means earlier than scheduled."
    },
    {
        "sentence": "彼の提案は、費用を抑えるという点では効果的だった。",
        "translation": "His proposal was effective in terms of keeping costs down.",
        "options": [
            "His proposal increased expenses significantly.",
            "His proposal was effective at reducing costs.",
            "His proposal was rejected because it was expensive.",
            "His proposal focused only on improving quality."
        ],
        "answer": "His proposal was effective at reducing costs.",
        "explanation": "費用を抑える means to keep costs down, and ～という点では means in terms of."
    },
    {
        "sentence": "十分な説明がなかったため、参加者の間で誤解が生じた。",
        "translation": "Because there was not enough explanation, a misunderstanding arose among the participants.",
        "options": [
            "Everyone understood the instructions perfectly.",
            "The participants arrived too early.",
            "A misunderstanding arose because the explanation was insufficient.",
            "The explanation was repeated until everyone agreed."
        ],
        "answer": "A misunderstanding arose because the explanation was insufficient.",
        "explanation": "十分な means sufficient, and 誤解が生じた means a misunderstanding arose."
    },
    {
        "sentence": "彼女は周囲の反対を押し切って、自分の計画を実行した。",
        "translation": "She went ahead with her plan despite opposition from those around her.",
        "options": [
            "She abandoned her plan after receiving advice.",
            "She followed everyone's wishes instead of her own.",
            "She carried out her plan despite opposition.",
            "She asked others to make the plan for her."
        ],
        "answer": "She carried out her plan despite opposition.",
        "explanation": "反対を押し切って means pushing ahead despite opposition."
    },
    {
        "sentence": "この問題については、関係者と相談したうえで判断したい。",
        "translation": "I would like to make a decision about this issue after consulting the people involved.",
        "options": [
            "I want to decide immediately without consulting anyone.",
            "I want to decide after consulting the people involved.",
            "I have already rejected every suggestion.",
            "I want someone else to solve the issue."
        ],
        "answer": "I want to decide after consulting the people involved.",
        "explanation": "関係者 means people involved, and ～たうえで means after doing something."
    },
    {
        "sentence": "予算が削減されたにもかかわらず、サービスの質は維持された。",
        "translation": "Despite the budget being reduced, the quality of the service was maintained.",
        "options": [
            "The service quality declined after the budget increased.",
            "The service was discontinued because of budget cuts.",
            "The service quality was maintained despite the budget reduction.",
            "The budget was increased to improve the service."
        ],
        "answer": "The service quality was maintained despite the budget reduction.",
        "explanation": "削減された means was reduced, while 維持された means was maintained."
    },
    {
        "sentence": "彼は責任者として、問題の原因を明らかにするべきだ。",
        "translation": "As the person responsible, he should clarify the cause of the problem.",
        "options": [
            "He should ignore the cause of the problem.",
            "He should clarify the cause of the problem as the person responsible.",
            "He should transfer all responsibility to someone else.",
            "He should prevent anyone from discussing the problem."
        ],
        "answer": "He should clarify the cause of the problem as the person responsible.",
        "explanation": "責任者 means the person responsible, and 原因を明らかにする means to clarify the cause."
    },
    {
        "sentence": "新しい制度を導入するにあたり、利用者の意見を参考にした。",
        "translation": "When introducing the new system, we took users' opinions into consideration.",
        "options": [
            "We ignored all users' opinions when introducing the system.",
            "We cancelled the system before consulting anyone.",
            "We considered users' opinions when introducing the system.",
            "We asked users to design a completely different system."
        ],
        "answer": "We considered users' opinions when introducing the system.",
        "explanation": "導入するにあたり means when undertaking or introducing something, and 参考にした means took into consideration."
    },
    {
        "sentence": "説明が不十分だったことから、計画の変更を求める声が上がった。",
        "translation": "Because the explanation was insufficient, calls for a change to the plan arose.",
        "options": [
            "Everyone supported the plan without questions.",
            "Calls for changing the plan arose because the explanation was insufficient.",
            "The plan was completed earlier than expected.",
            "The explanation was considered completely unnecessary."
        ],
        "answer": "Calls for changing the plan arose because the explanation was insufficient.",
        "explanation": "不十分 means insufficient, and 声が上がった means voices or calls arose."
    },
    {
        "sentence": "状況に応じて、対応の方法を柔軟に変える必要がある。",
        "translation": "It is necessary to change the response method flexibly according to the situation.",
        "options": [
            "The same response must always be used.",
            "Responses should be delayed in every situation.",
            "The response method needs to change flexibly according to the situation.",
            "The situation should be ignored when deciding how to respond."
        ],
        "answer": "The response method needs to change flexibly according to the situation.",
        "explanation": "状況に応じて means according to the situation, and 柔軟に means flexibly."
    },

]

N1_LISTENING_QUESTIONS = [
    {
        "sentence": "彼の説明は一見もっともらしいが、肝心な点については何も明らかにしていない。",
        "translation": "His explanation seems plausible at first glance, but it reveals nothing about the crucial point.",
        "options": [
            "His explanation answers every important question.",
            "His explanation sounds plausible but avoids the crucial point.",
            "His explanation is completely unrelated to the topic.",
            "His explanation was never given."
        ],
        "answer": "His explanation sounds plausible but avoids the crucial point.",
        "explanation": "一見 means 'at first glance', and 肝心な点 means 'the crucial point'."
    },
    {
        "sentence": "計画の見直しを余儀なくされたのは、当初の想定を大幅に上回る費用が判明したためだ。",
        "translation": "The plan had to be reviewed because the costs turned out to be far higher than initially anticipated.",
        "options": [
            "The plan succeeded under budget.",
            "The plan was reviewed because costs greatly exceeded expectations.",
            "The costs were lower than expected.",
            "The plan was never evaluated."
        ],
        "answer": "The plan was reviewed because costs greatly exceeded expectations.",
        "explanation": "余儀なくされた means 'was forced to'; 想定を上回る means 'exceed expectations'."
    },
    {
        "sentence": "彼女は批判をものともせず、自らの信念を貫き通した。",
        "translation": "She was undeterred by criticism and held firmly to her convictions.",
        "options": [
            "She abandoned her beliefs after criticism.",
            "She criticized everyone around her.",
            "She remained committed to her beliefs despite criticism.",
            "She avoided expressing her opinion."
        ],
        "answer": "She remained committed to her beliefs despite criticism.",
        "explanation": "ものともせず means 'without being deterred by'."
    },
    {
        "sentence": "この提案は理想的ではあるものの、実現可能性という点では課題が残る。",
        "translation": "Although this proposal is ideal, challenges remain regarding its feasibility.",
        "options": [
            "The proposal is ideal and has no challenges.",
            "The proposal is impossible to understand.",
            "The proposal is appealing but still has feasibility issues.",
            "The proposal has already been implemented successfully."
        ],
        "answer": "The proposal is appealing but still has feasibility issues.",
        "explanation": "実現可能性 refers to feasibility or the possibility of implementation."
    },
    {
        "sentence": "彼の功績は、単に売り上げを伸ばしたことにとどまらず、組織全体の意識改革を促した点にもある。",
        "translation": "His achievement lies not only in increasing sales but also in encouraging a change in mindset throughout the organization.",
        "options": [
            "His only achievement was reducing costs.",
            "He increased sales and encouraged an organizational mindset change.",
            "He opposed all organizational changes.",
            "He left the organization before making an impact."
        ],
        "answer": "He increased sales and encouraged an organizational mindset change.",
        "explanation": "にとどまらず means 'not limited to'; 促した means 'encouraged or prompted'."
    },
    {
        "sentence": "状況が改善する兆しが見えない以上、別の対応策を講じる必要がある。",
        "translation": "Since there are no signs of improvement, we need to take alternative measures.",
        "options": [
            "Continue without changing anything.",
            "Wait because improvement is certain.",
            "Take alternative measures because there are no signs of improvement.",
            "Cancel every existing measure without replacement."
        ],
        "answer": "Take alternative measures because there are no signs of improvement.",
        "explanation": "兆し means 'signs'; 講じる means 'to take or implement measures'."
    },
    {
        "sentence": "彼は責任を問われることを恐れるあまり、問題の存在そのものを認めようとしなかった。",
        "translation": "Because he was so afraid of being held responsible, he refused to acknowledge that the problem existed at all.",
        "options": [
            "He immediately accepted responsibility.",
            "He solved the problem and reported it.",
            "His fear of accountability led him to deny the problem existed.",
            "He asked others to investigate the issue."
        ],
        "answer": "His fear of accountability led him to deny the problem existed.",
        "explanation": "あまり expresses an excessive degree that leads to a consequence."
    },
    {
        "sentence": "その判断は、短期的な利益を優先するあまり、長期的な信頼を損なうおそれがある。",
        "translation": "That decision risks damaging long-term trust by placing too much priority on short-term profit.",
        "options": [
            "The decision guarantees long-term trust.",
            "The decision balances every concern perfectly.",
            "Prioritizing short-term profit may damage long-term trust.",
            "The decision has no financial implications."
        ],
        "answer": "Prioritizing short-term profit may damage long-term trust.",
        "explanation": "おそれがある means 'there is a risk or possibility of'."
    },
    {
        "sentence": "関係者の理解を得ることなしには、この改革を円滑に進めることは難しい。",
        "translation": "Without gaining the understanding of those involved, it will be difficult to carry out this reform smoothly.",
        "options": [
            "The reform can proceed without anyone's understanding.",
            "The reform requires the understanding of the people involved.",
            "The reform has already ended.",
            "Only outsiders need to approve the reform."
        ],
        "answer": "The reform requires the understanding of the people involved.",
        "explanation": "ことなしには means 'without doing something'; 円滑に means 'smoothly'."
    },
    {
        "sentence": "彼の発言を額面どおりに受け取るのではなく、その背景にある意図を考えるべきだ。",
        "translation": "Rather than taking his words at face value, we should consider the intention behind them.",
        "options": [
            "Believe every word without question.",
            "Ignore everything he says.",
            "Consider the underlying intention instead of taking his words literally.",
            "Repeat his words to everyone."
        ],
        "answer": "Consider the underlying intention instead of taking his words literally.",
        "explanation": "額面どおり means 'at face value'; 背景にある意図 means 'the underlying intention'."
    },
    
    {
        "sentence": "改革の必要性は認めるものの、実施時期については慎重に検討すべきだ。",
        "translation": "Although the need for reform is acknowledged, the timing of its implementation should be considered carefully.",
        "options": [
            "The reform is unnecessary and should be cancelled.",
            "The reform should be implemented immediately without discussion.",
            "The need for reform is accepted, but its timing requires careful consideration.",
            "The timing of the reform has already been decided."
        ],
        "answer": "The need for reform is accepted, but its timing requires careful consideration.",
        "explanation": "ものの expresses contrast, and 慎重に検討する means to consider carefully."
    },
    {
        "sentence": "彼の発言は、事実関係を十分に確認しないままなされたと言わざるを得ない。",
        "translation": "We cannot help but conclude that his remarks were made without sufficiently verifying the facts.",
        "options": [
            "He carefully verified every fact before speaking.",
            "His remarks were made without sufficient fact-checking.",
            "His remarks were completely unrelated to the facts.",
            "He refused to make any public statements."
        ],
        "answer": "His remarks were made without sufficient fact-checking.",
        "explanation": "と言わざるを得ない means cannot help but say or conclude, and 事実関係 means the facts of a matter."
    },
    {
        "sentence": "経済状況の変化いかんによっては、計画そのものを見直す必要がある。",
        "translation": "Depending on changes in economic conditions, the plan itself may need to be reconsidered.",
        "options": [
            "The plan must continue regardless of economic conditions.",
            "The economy will remain unchanged throughout the project.",
            "Changes in economic conditions may require reconsidering the plan itself.",
            "The plan has already solved every economic problem."
        ],
        "answer": "Changes in economic conditions may require reconsidering the plan itself.",
        "explanation": "いかんによっては means depending on, and 見直す means to review or reconsider."
    },
    {
        "sentence": "彼女は周囲の期待に応えるべく、長年にわたって努力を重ねてきた。",
        "translation": "She has worked hard for many years in order to live up to the expectations of those around her.",
        "options": [
            "She ignored everyone's expectations for many years.",
            "She worked hard over many years to meet others' expectations.",
            "She gave up because the expectations were too low.",
            "She expected everyone else to do the work."
        ],
        "answer": "She worked hard over many years to meet others' expectations.",
        "explanation": "～べく expresses purpose, and 努力を重ねる means to make sustained efforts."
    },
    {
        "sentence": "十分な証拠がない以上、彼が関与したと断定することはできない。",
        "translation": "Given the lack of sufficient evidence, we cannot conclude that he was involved.",
        "options": [
            "The evidence proves beyond doubt that he was involved.",
            "He has already admitted his involvement.",
            "Without sufficient evidence, we cannot conclude that he was involved.",
            "The investigation has been cancelled permanently."
        ],
        "answer": "Without sufficient evidence, we cannot conclude that he was involved.",
        "explanation": "以上 means given that or since in this context, and 断定する means to conclude definitively."
    },
    {
        "sentence": "この政策は、短期的な成果のみならず、将来への影響も考慮に入れるべきだ。",
        "translation": "This policy should take into account not only short-term results but also its future impact.",
        "options": [
            "The policy should focus exclusively on immediate results.",
            "Only future effects matter when evaluating the policy.",
            "The policy should consider both short-term results and future impact.",
            "The policy has no effect on the future."
        ],
        "answer": "The policy should consider both short-term results and future impact.",
        "explanation": "のみならず means not only, and 考慮に入れる means to take into consideration."
    },
    {
        "sentence": "彼の説明は一貫性に欠けており、聞き手を納得させるには至らなかった。",
        "translation": "His explanation lacked consistency and failed to convince the listeners.",
        "options": [
            "His explanation was consistent and convinced everyone.",
            "His explanation lacked consistency and did not persuade the listeners.",
            "His explanation was too short to be heard.",
            "The listeners agreed before he began speaking."
        ],
        "answer": "His explanation lacked consistency and did not persuade the listeners.",
        "explanation": "一貫性に欠ける means to lack consistency, and ～には至らなかった means did not reach the point of achieving something."
    },
    {
        "sentence": "予算の制約を踏まえたうえで、最も効果的な解決策を模索する必要がある。",
        "translation": "We need to search for the most effective solution while taking budget constraints into account.",
        "options": [
            "We should ignore the budget when choosing a solution.",
            "We need to find an effective solution while considering budget constraints.",
            "We must increase the budget before discussing solutions.",
            "We have already found a solution that has no cost."
        ],
        "answer": "We need to find an effective solution while considering budget constraints.",
        "explanation": "踏まえたうえで means taking something into account, and 模索する means to search for or explore."
    },
    {
        "sentence": "彼の功績を評価するにあたって、結果だけでなく過程にも目を向けるべきだ。",
        "translation": "When evaluating his achievements, attention should be paid to the process as well as the results.",
        "options": [
            "Only the final results should be evaluated.",
            "His achievements should not be evaluated at all.",
            "Both the process and the results should be considered when evaluating his achievements.",
            "The process matters only if the results are poor."
        ],
        "answer": "Both the process and the results should be considered when evaluating his achievements.",
        "explanation": "にあたって means when undertaking something, and 目を向ける means to turn one's attention toward."
    },
    {
        "sentence": "事態の深刻さを考えれば、迅速かつ適切な対応が求められる。",
        "translation": "Considering the seriousness of the situation, a prompt and appropriate response is required.",
        "options": [
            "The situation is minor and requires no response.",
            "A slow response is preferable in this situation.",
            "The seriousness of the situation calls for a prompt and appropriate response.",
            "The situation has resolved itself without any action."
        ],
        "answer": "The seriousness of the situation calls for a prompt and appropriate response.",
        "explanation": "深刻さ means seriousness, 迅速 means prompt or swift, and 求められる means is required."
    },

]



def is_valid_japanese_sentence(sentence: str) -> bool:
    if not isinstance(sentence, str) or not sentence.strip():
        return False

    sentence = sentence.strip()

    if len(sentence) > 120:
        return False

    # Reject CJK Extension A and compatibility ideographs.
    if re.search(r"[\u3400-\u4DBF\uF900-\uFAFF]", sentence):
        return False

    # Require hiragana or katakana, not kanji alone.
    kana_count = len(re.findall(r"[\u3041-\u3096\u30A1-\u30FA]", sentence))
    if kana_count < 2:
        return False

    # Require Japanese characters and reject obvious romaji output.
    if not re.search(r"[\u3040-\u30FF\u4E00-\u9FFF]", sentence):
        return False

    # Reject Latin letters in the sentence to avoid romaji output.
    if re.search(r"[A-Za-z]", sentence):
        return False

    # Allow Japanese characters, whitespace, punctuation, and digits.
    if re.search(
        r"[^\u3040-\u30FF\u4E00-\u9FFF"
        r"\s。、！？「」『』（）・ー〜…０-９0-9]",
        sentence,
    ):
        return False

    return True



def generate_ai_listening_questions(level: str, count: int) -> list:
    """
    Generate questions independently. Retry each question up to three
    times, then use the curated bank for that question when available.
    """
  
    if count < 1 or count > 10:
        raise ValueError("Count must be between 1 and 10.")

    question_banks = {
        "N5": N5_LISTENING_QUESTIONS,
        "N4": N4_LISTENING_QUESTIONS,
        "N3": N3_LISTENING_QUESTIONS,
        "N2": N2_LISTENING_QUESTIONS,
        "N1": N1_LISTENING_QUESTIONS,
    }

    question_bank = question_banks.get(level)

    if question_bank is None:
        raise ValueError(f"No listening question bank configured for {level}")

    fallback_questions = (
        random.sample(
            question_bank,
            k=min(count, len(question_bank))
        )
        if question_bank
        else []
    )


    fallback_index = 0
    results = []
    used_sentences = set()
    ai_count = 0
    fallback_count = 0

    def generate_one_question():
        
        previous_sentences = "\n".join(
            f"- {sentence}" for sentence in used_sentences
        ) or "- None yet"

        
        level_guidance = {
            "N5": "Beginner Japanese. Basic vocabulary, particles, and short everyday sentences.",
            "N4": "Elementary Japanese. Common daily conversations, basic grammar, and connected sentences.",
            "N3": "Intermediate Japanese. Longer conversations, implied meaning, varied grammar, and everyday situations.",
            "N2": "Upper-intermediate Japanese. Natural conversations, nuanced expressions, formal situations, and complex sentences.",
            "N1": "Advanced Japanese. Subtle implications, sophisticated vocabulary, idiomatic expressions, and complex natural speech.",
        }

        previous_sentences = "\n".join(
            f"- {sentence}" for sentence in used_sentences
        ) or "- None yet"

        prompt = f"""
Create ONE Japanese listening comprehension question for JLPT {level}.

Difficulty requirements:
{level_guidance[level]}

Do not repeat or closely paraphrase these sentences:
{previous_sentences}

Requirements:
- Write natural Japanese using Japanese characters, never romaji.
- Match the vocabulary and grammar to JLPT {level}.
- Create a realistic listening situation.
- Provide an accurate English translation.
- Give exactly four distinct English answer choices.
- The answer must exactly match one choice.
- Explain briefly why the answer is correct.
- Return valid JSON only.

Use this schema:
{{
  "sentence": "Japanese sentence",
  "translation": "English translation",
  "options": [
    "Choice A",
    "Choice B",
    "Choice C",
    "Choice D"
  ],
  "answer": "Exact correct choice",
  "explanation": "Brief explanation in English"
}}
"""



        response = chat(
            model="llama3.2:latest",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a careful Japanese language teacher. "
                        "Generate one natural Japanese exercise and "
                        "return only JSON matching the requested schema."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            format="json",
            options={"temperature": 0.3},
        )

        data = json.loads(response.message.content)

        if not isinstance(data, dict):
            raise ValueError("AI response is not a JSON object.")

        sentence = data.get("sentence")
        translation = data.get("translation")
        options = data.get("options")
        answer = data.get("answer")
        explanation = data.get("explanation")

        required_fields = {
            "sentence": sentence,
            "translation": translation,
            "answer": answer,
            "explanation": explanation,
        }

        missing = [
            field
            for field, value in required_fields.items()
            if not isinstance(value, str) or not value.strip()
        ]

        if missing:
            raise ValueError(f"Missing or empty fields: {missing}")

        sentence = sentence.strip()
        translation = translation.strip()
        answer = answer.strip()
        explanation = explanation.strip()

        if not is_valid_japanese_sentence(sentence):
            raise ValueError(
                f"Invalid Japanese sentence: {sentence!r}"
            )

        if (
            not isinstance(options, list)
            or len(options) != 4
            or not all(
                isinstance(option, str) and option.strip()
                for option in options
            )
        ):
            raise ValueError("AI returned invalid answer choices.")

        options = [option.strip() for option in options]

        if len(set(option.casefold() for option in options)) != 4:
            raise ValueError("AI returned duplicate answer choices.")

        matching_option = next(
            (
                option for option in options
                if option.casefold() == answer.casefold()
            ),
            None,
        )

        if matching_option is None:
            raise ValueError("Answer does not match any option.")

        # Reject sentences already used in this question set.
        sentence_key = re.sub(
            r"[\s。、！？「」『』（）・ー]",
            "",
            sentence,
        )

        if sentence_key in used_sentences:
            raise ValueError(
                f"Duplicate Japanese sentence: {sentence!r}"
            )

        reading_data = build_listening_reading(sentence)

        if not reading_data["romaji"] or not reading_data["reading"]:
            raise ValueError("Could not generate reading and romaji.")

        used_sentences.add(sentence_key)

        return {
            "sentence": sentence,
            "reading": reading_data["reading"],
            "romaji": reading_data["romaji"],
            "translation": translation,
            "options": options,
            "answer": matching_option,
            "explanation": explanation,
        }

    # Generate each question, retrying failures up to three times.
    
    # FAST MODE: use curated questions without calling Ollama.
    selected_questions = random.sample(
        question_bank,
        k=min(count, len(question_bank))
    )

    results = []

    for item in selected_questions:
        reading_data = build_listening_reading(item["sentence"])

        results.append({
            **item,
            "reading": reading_data["reading"],
            "romaji": reading_data["romaji"],
            "_source": "fallback",
        })

    print(
        f"Fast listening mode for {level}: "
        f"{len(results)} curated questions; no AI calls."
    )

    return results






@app.post("/listening/generate")
def generate_listening(request: ListeningRequest):
    level = request.level.upper()

    if level not in ["N5", "N4", "N3", "N2", "N1"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid JLPT level. Choose N5, N4, N3, N2, or N1.",
        )

    count = request.count

    if count < 1 or count > 10:
        raise HTTPException(
            status_code=400,
            detail="Count must be between 1 and 10.",
        )

    try:
        questions = generate_ai_listening_questions(level, count)

    except Exception as error:
        print(f"Listening generation failed for {level}: {error}")

        raise HTTPException(
            status_code=503,
            detail=(
                f"Could not generate enough valid {level} questions. "
                "This level has no curated fallback bank available "
                "for every requested question. Try again."
            ),
        )

    sources = {question["_source"] for question in questions}

    source = (
    "ai" if sources == {"ai"}
    else "fallback" if sources == {"fallback"}
    else "mixed"
)

    clean_questions = [
    {key: value for key, value in question.items() if key != "_source"}
    for question in questions
]
    return {
    "level": level,
    "count": len(clean_questions),
    "source": source,
    "questions": clean_questions,
}


def build_listening_reading(sentence: str) -> dict:
    """
    Build reading and romaji from the existing Japanese analyzer.
    """
    analysis = analyze_japanese(sentence)

    words = analysis.get("words", [])

    reading = "".join(
        word.get("reading", "")
        for word in words
        if word.get("reading")
    )

    romaji_parts = [
        word.get("romaji", "").strip()
        for word in words
        if word.get("romaji", "").strip()
    ]

    romaji = " ".join(romaji_parts)

    return {
        "reading": reading,
        "romaji": romaji
    }
