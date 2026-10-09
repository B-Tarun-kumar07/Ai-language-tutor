from ollama import chat
from pydantic import BaseModel


# ============================================================
# FIXED VOCABULARY
# ============================================================

VOCABULARY = {

    # ========================================================
    # PRONOUNS
    # ========================================================

    "私": "I / me",
    "あなた": "you",
    "彼": "he / him",
    "彼女": "she / her",
    "私たち": "we / us",
    "みんな": "everyone",
    "誰": "who",
    "何": "what",
    "これ": "this",
    "それ": "that",
    "あれ": "that over there",


    # ========================================================
    # PLACES
    # ========================================================

    "学校": "school",
    "会社": "company / workplace",
    "駅": "station",
    "家": "home / house",
    "図書館": "library",
    "店": "shop / store",
    "病院": "hospital",
    "大学": "university",
    "部屋": "room",
    "公園": "park",
    "銀行": "bank",
    "レストラン": "restaurant",
    "コンビニ": "convenience store",
    "映画館": "movie theater",


    # ========================================================
    # PEOPLE
    # ========================================================

    "友達": "friend",
    "先生": "teacher",
    "学生": "student",
    "家族": "family",
    "母": "mother",
    "父": "father",
    "兄": "older brother",
    "姉": "older sister",
    "弟": "younger brother",
    "妹": "younger sister",
    "男": "man / male",
    "女": "woman / female",
    "子供": "child",
    "人": "person",


    # ========================================================
    # OBJECTS
    # ========================================================

    "本": "book",
    "映画": "movie",
    "水": "water",
    "食べ物": "food",
    "車": "car",
    "電話": "phone",
    "時計": "clock / watch",
    "机": "desk",
    "椅子": "chair",
    "写真": "photo",
    "音楽": "music",
    "名前": "name",
    "お金": "money",
    "鍵": "key",
    "傘": "umbrella",


    # ========================================================
    # COUNTRIES / LANGUAGES
    # ========================================================

    "日本": "Japan",
    "日本語": "Japanese language",
    "英語": "English language",
    "中国": "China",
    "中国語": "Chinese language",
    "韓国": "Korea",
    "韓国語": "Korean language",
    "言語": "language",


    # ========================================================
    # STUDY
    # ========================================================

    "勉強": "study",
    "宿題": "homework",
    "授業": "class / lesson",
    "試験": "exam",
    "テスト": "test",
    "質問": "question",
    "答え": "answer",
    "問題": "problem / question",
    "練習": "practice",
    "仕事": "work / job",


    # ========================================================
    # TIME
    # ========================================================

    "今日": "today",
    "昨日": "yesterday",
    "明日": "tomorrow",
    "今": "now",
    "朝": "morning",
    "昼": "afternoon / noon",
    "夜": "night / evening",
    "毎日": "every day",
    "毎週": "every week",
    "毎月": "every month",
    "毎年": "every year",
    "時間": "time / hour",
    "週": "week",
    "月": "month",
    "年": "year",


    # ========================================================
    # FOOD
    # ========================================================

    "ラーメン": "ramen",
    "ご飯": "rice / meal",
    "パン": "bread",
    "肉": "meat",
    "魚": "fish",
    "野菜": "vegetables",
    "果物": "fruit",
    "りんご": "apple",
    "コーヒー": "coffee",
    "お茶": "tea",
    "水": "water",
    "料理": "cooking / cuisine",


    # ========================================================
    # VERBS - DICTIONARY FORMS
    # ========================================================

    "行く": "go",
    "来る": "come",
    "帰る": "return / go home",
    "見る": "watch / see",
    "食べる": "eat",
    "飲む": "drink",
    "する": "do",
    "勉強する": "study",
    "読む": "read",
    "書く": "write",
    "聞く": "listen / hear / ask",
    "話す": "speak / talk",
    "買う": "buy",
    "使う": "use",
    "作る": "make",
    "会う": "meet",
    "住む": "live",
    "働く": "work",
    "休む": "rest / take a break",
    "起きる": "wake up / get up",
    "寝る": "sleep / go to bed",
    "分かる": "understand",
    "思う": "think",
    "知る": "know",
    "持つ": "have / hold",
    "待つ": "wait",
    "入る": "enter",
    "出る": "leave / exit",
    "歩く": "walk",
    "走る": "run",
    "開ける": "open",
    "閉める": "close",


    # ========================================================
    # VERBS - POLITE PRESENT
    # ========================================================

    "行きます": "go",
    "来ます": "come",
    "帰ります": "return / go home",
    "見ます": "watch / see",
    "食べます": "eat",
    "飲みます": "drink",
    "します": "do",
    "勉強します": "study",
    "読みます": "read",
    "書きます": "write",
    "聞きます": "listen / hear / ask",
    "話します": "speak / talk",
    "買います": "buy",
    "使います": "use",
    "作ります": "make",
    "会います": "meet",
    "住みます": "live",
    "働きます": "work",
    "休みます": "rest",
    "起きます": "wake up / get up",
    "寝ます": "sleep / go to bed",
    "分かります": "understand",
    "思います": "think",
    "知ります": "know",
    "持ちます": "have / hold",
    "待ちます": "wait",
    "入ります": "enter",
    "出ます": "leave / exit",
    "歩きます": "walk",
    "走ります": "run",
    "開けます": "open",
    "閉めます": "close",


    # ========================================================
    # VERBS - POLITE PAST
    # ========================================================

    "行きました": "went",
    "来ました": "came",
    "帰りました": "returned / went home",
    "見ました": "watched / saw",
    "食べました": "ate",
    "飲みました": "drank",
    "しました": "did",
    "勉強しました": "studied",
    "読みました": "read",
    "書きました": "wrote",
    "聞きました": "listened / heard / asked",
    "話しました": "spoke / talked",
    "買いました": "bought",
    "使いました": "used",
    "作りました": "made",
    "会いました": "met",
    "住みました": "lived",
    "働きました": "worked",
    "休みました": "rested",
    "起きました": "woke up / got up",
    "寝ました": "slept / went to bed",
    "分かりました": "understood",
    "思いました": "thought",
    "知りました": "found out / learned",
    "持ちました": "had / held",
    "待ちました": "waited",
    "入りました": "entered",
    "出ました": "left / exited",
    "歩きました": "walked",
    "走りました": "ran",
    "開けました": "opened",
    "閉めました": "closed",


    # ========================================================
    # VERBS - POLITE NEGATIVE
    # ========================================================

    "行きません": "do not go",
    "来ません": "do not come",
    "帰りません": "do not return / do not go home",
    "見ません": "do not watch / do not see",
    "食べません": "do not eat",
    "飲みません": "do not drink",
    "しません": "do not do",
    "勉強しません": "do not study",
    "読みません": "do not read",
    "書きません": "do not write",
    "聞きません": "do not listen / do not hear",
    "話しません": "do not speak / do not talk",
    "買いません": "do not buy",
    "使いません": "do not use",
    "作りません": "do not make",
    "会いません": "do not meet",
    "住みません": "do not live",
    "働きません": "do not work",
    "休みません": "do not rest",
    "起きません": "do not wake up",
    "寝ません": "do not sleep",
    "分かりません": "do not understand",
    "思いません": "do not think",
    "知りません": "do not know",
    "待ちません": "do not wait",


    # ========================================================
    # VERBS - POLITE PAST NEGATIVE
    # ========================================================

    "行きませんでした": "did not go",
    "来ませんでした": "did not come",
    "帰りませんでした": "did not return / did not go home",
    "見ませんでした": "did not watch / did not see",
    "食べませんでした": "did not eat",
    "飲みませんでした": "did not drink",
    "しませんでした": "did not do",
    "勉強しませんでした": "did not study",
    "読みませんでした": "did not read",
    "書きませんでした": "did not write",
    "聞きませんでした": "did not listen / did not hear",
    "話しませんでした": "did not speak / did not talk",


    # ========================================================
    # ている FORMS
    # ========================================================

    "食べています": "am eating / are eating",
    "飲んでいます": "am drinking / are drinking",
    "見ています": "am watching / are watching",
    "読んでいます": "am reading / are reading",
    "書いています": "am writing / are writing",
    "聞いています": "am listening / are listening",
    "話しています": "am speaking / are speaking",
    "勉強しています": "am studying / are studying",
    "働いています": "am working / are working",
    "住んでいます": "live / am living",
    "待っています": "am waiting / are waiting",
    "使っています": "am using / are using",
    "しています": "am doing / are doing",


    # ========================================================
    # ている NEGATIVE
    # ========================================================

    "食べていません": "am not eating",
    "飲んでいません": "am not drinking",
    "見ていません": "am not watching",
    "読んでいません": "am not reading",
    "書いていません": "am not writing",
    "聞いていません": "am not listening",
    "話していません": "am not speaking",
    "勉強していません": "am not studying",
    "働いていません": "am not working",
    "使っていません": "am not using",
    "していません": "am not doing",


    # ========================================================
    # たい FORMS
    # ========================================================

    "食べたいです": "want to eat",
    "飲みたいです": "want to drink",
    "見たいです": "want to watch / want to see",
    "行きたいです": "want to go",
    "来たいです": "want to come",
    "帰りたいです": "want to return / want to go home",
    "勉強したいです": "want to study",
    "読みたいです": "want to read",
    "書きたいです": "want to write",
    "話したいです": "want to speak / want to talk",
    "買いたいです": "want to buy",
    "使いたいです": "want to use",


    # ========================================================
    # たくない FORMS
    # ========================================================

    "食べたくないです": "do not want to eat",
    "飲みたくないです": "do not want to drink",
    "見たくないです": "do not want to watch / do not want to see",
    "行きたくないです": "do not want to go",
    "帰りたくないです": "do not want to return / do not want to go home",
    "勉強したくないです": "do not want to study",
    "読みたくないです": "do not want to read",
    "話したくないです": "do not want to speak / do not want to talk",


    # ========================================================
    # ADJECTIVES
    # ========================================================

    "新しい": "new",
    "古い": "old",
    "大きい": "big",
    "小さい": "small",
    "面白い": "interesting",
    "楽しい": "fun / enjoyable",
    "難しい": "difficult",
    "易しい": "easy",
    "簡単": "easy / simple",
    "忙しい": "busy",
    "高い": "expensive / high",
    "安い": "cheap / inexpensive",
    "暑い": "hot",
    "寒い": "cold",
    "熱い": "hot to the touch",
    "冷たい": "cold to the touch",
    "美味しい": "delicious",
    "美しい": "beautiful",
    "早い": "early / fast",
    "遅い": "late / slow",
    "長い": "long",
    "短い": "short",
    "近い": "near",
    "遠い": "far",
    "良い": "good",
    "悪い": "bad",
    "可愛い": "cute",
    "好き": "like / favorite",
    "嫌い": "dislike / hate",
    "元気": "healthy / energetic",
    "静か": "quiet",
    "綺麗": "beautiful / clean",
}


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
# PYDANTIC MODELS
# ============================================================

class VocabularyMeaning(BaseModel):

    word: str

    meaning: str


class VocabularyResponse(BaseModel):

    meanings: list[VocabularyMeaning]


# ============================================================
# LOCAL LOOKUP
# ============================================================

def get_local_meaning(word):

    return VOCABULARY.get(word)


# ============================================================
# UNKNOWN WORD LOOKUP USING OLLAMA
# ============================================================

def get_unknown_word_meanings(words):

    if not words:

        return {}


    # Remove duplicates while preserving order

    unique_words = list(
        dict.fromkeys(words)
    )


    word_list = "\n".join(
        f"- {word}"
        for word in unique_words
    )


    prompt = f"""
You are a Japanese-English dictionary assistant.

Give a simple English meaning for each Japanese word.

Japanese words:

{word_list}

Rules:

1. Return exactly one meaning for every word.
2. Keep the Japanese word EXACTLY as provided.
3. Do not modify or normalize the Japanese word.
4. Give a concise beginner-friendly English meaning.
5. If the word is a conjugated verb, translate the specific form.
6. Do not explain grammar.
7. Do not add extra words.
8. Return ONLY valid JSON matching the requested schema.

Examples:

食べました → ate
行きました → went
飲みました → drank
食べません → do not eat
勉強しています → am studying
食べたいです → want to eat
"""


    try:

        response = chat(

            model="llama3.2",

            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],

            format=VocabularyResponse.model_json_schema()

        )


        data = VocabularyResponse.model_validate_json(
            response.message.content
        )


        return {

            item.word: item.meaning

            for item in data.meanings

        }


    except Exception as error:

        print(
            f"Vocabulary lookup failed: {error}"
        )

        return {}


# ============================================================
# MAIN VOCABULARY FUNCTION
# ============================================================

def get_vocabulary_meanings(words):

    meanings = {}

    unknown_words = []


    for word in words:

        # ====================================================
        # 1. PARTICLES
        # ====================================================

        if word in PARTICLE_MEANINGS:

            meanings[word] = (
                PARTICLE_MEANINGS[word]
            )

            continue


        # ====================================================
        # 2. LOCAL VOCABULARY
        # ====================================================

        local_meaning = get_local_meaning(word)


        if local_meaning:

            meanings[word] = local_meaning

        else:

            unknown_words.append(word)


    # ========================================================
    # 3. OLLAMA FALLBACK
    # ========================================================

    if unknown_words:

        ollama_meanings = (
            get_unknown_word_meanings(
                unknown_words
            )
        )

        meanings.update(
            ollama_meanings
        )


    # ========================================================
    # 4. FINAL FALLBACK
    # ========================================================

    # If Ollama fails for a word, don't crash the
    # analyzer. Give a neutral fallback.

    for word in unknown_words:

        if word not in meanings:

            meanings[word] = (
                "Meaning not available"
            )


    return meanings