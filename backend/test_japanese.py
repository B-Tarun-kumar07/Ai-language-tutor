from japanese_analyzer import analyze_japanese


sentences = [
    "私は学校に行きます。",
    "私は学校で勉強します。",
    "日本語を勉強しています。",
    "友達と映画を見ました。"
]


for sentence in sentences:

    print("\n" + "=" * 50)
    print(sentence)
    print("=" * 50)

    result = analyze_japanese(sentence)

    print("\nLearner words:")

    for word in result["words"]:
        print(
            f'{word["word"]} '
            f'→ {word["reading"]} '
            f'→ {word["romaji"]}'
        )

    print("\nInternal morphemes:")

    for word in result["morphemes"]:
        print(
            f'{word["word"]} '
            f'→ {word["reading"]} '
            f'→ {word["romaji"]}'
        )