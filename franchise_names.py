"""
franchise_names.py
------------------
Official French (preferred) or English names for franchises likely to appear
in Pixel Bento's Tokyo events radar.

Priority: French official title > English official title > leave in Japanese.

Sources: publisher sites (Kana, Ki-oon, Pika, Kurokawa, Panini), Wikipedia,
and official localisation credits. Update this file as new franchises appear.

Structure: { japanese_title: official_fr_or_en_title }
"""

FRANCHISE_NAMES: dict[str, str] = {

    # ── Anime / Manga ──────────────────────────────────────────────────────────

    # FR official titles
    '薬屋のひとりごと':          "Les Carnets de l'Apothicaire",
    '進撃の巨人':               "L'Attaque des Titans",
    '名探偵コナン':              "Détective Conan",
    '鬼滅の刃':                 "Demon Slayer",          # published in FR as Demon Slayer
    'ハンターハンター':           "Hunter × Hunter",
    'HUNTER×HUNTER':            "Hunter × Hunter",
    '少女終末旅行':              "Girls' Last Tour",      # Ki-oon FR
    'スパイ×ファミリー':          "Spy × Family",
    'スパイファミリー':           "Spy × Family",
    'ちびまる子ちゃん':           "Chibi Maruko-chan",
    'キン肉マン':                "Kinnikuman",
    '攻殻機動隊':               "Ghost in the Shell",
    '機動警察パトレイバー':       "Patlabor",
    'カウボーイビバップ':         "Cowboy Bebop",
    'エヴァンゲリオン':           "Neon Genesis Evangelion",
    '新世紀エヴァンゲリオン':     "Neon Genesis Evangelion",
    'ルパン三世':               "Lupin III",
    'ドラえもん':               "Doraemon",
    'クレヨンしんちゃん':        "Crayon Shin-chan",
    'ちびまる子':               "Chibi Maruko-chan",
    '銀河鉄道999':              "Galaxy Express 999",
    '宇宙戦艦ヤマト':            "Space Battleship Yamato",
    'マジンガーZ':              "Mazinger Z",
    'ガンダム':                 "Mobile Suit Gundam",
    '機動戦士ガンダム':          "Mobile Suit Gundam",
    '聖闘士星矢':               "Saint Seiya",
    '北斗の拳':                 "Fist of the North Star",
    'シティーハンター':           "City Hunter",
    'うる星やつら':              "Urusei Yatsura",
    'らんま½':                  "Ranma ½",
    '幽☆遊☆白書':              "Yu Yu Hakusho",
    'スラムダンク':              "Slam Dunk",
    '呪術廻戦':                 "Jujutsu Kaisen",
    '僕のヒーローアカデミア':     "My Hero Academia",
    'ヒロアカ':                  "My Hero Academia",
    'ワンピース':               "One Piece",
    'ナルト':                   "Naruto",
    'NARUTO':                   "Naruto",
    'ブリーチ':                 "Bleach",
    'BLEACH':                   "Bleach",
    'ドラゴンボール':            "Dragon Ball",
    '東京リベンジャーズ':         "Tokyo Revengers",
    'ワールドトリガー':           "World Trigger",
    '爆走兄弟レッツ＆ゴー':       "Let's & Go!!",
    'レッツ＆ゴー':              "Let's & Go!!",
    'ウマ娘':                   "Uma Musume Pretty Derby",
    'ウマ娘 プリティーダービー':   "Uma Musume Pretty Derby",
    'デュエル・マスターズ':       "Duel Masters",
    'カードキャプターさくら':     "Cardcaptor Sakura",
    'セーラームーン':            "Sailor Moon",
    '美少女戦士セーラームーン':   "Sailor Moon",
    'プリキュア':               "Pretty Cure",
    'ふしぎの海のナディア':       "Nadia: The Secret of Blue Water",
    '天空の城ラピュタ':          "Castle in the Sky",
    'となりのトトロ':            "My Neighbor Totoro",
    '千と千尋の神隠し':          "Spirited Away",
    'もののけ姫':               "Princess Mononoke",
    '風の谷のナウシカ':          "Nausicaä of the Valley of the Wind",
    '攻殻機動隊 STAND ALONE COMPLEX': "Ghost in the Shell: Stand Alone Complex",
    'リムバスカンパニー':         "Limbus Company",
    'Limbus Company':           "Limbus Company",
    'スキップとローファー':       "Skip and Loafer",
    '天才バカボン':              "Genius Bakabon",
    '魔法少女まどか☆マギカ':     "Puella Magi Madoka Magica",

    # ── Video games ────────────────────────────────────────────────────────────

    'MOTHER2':                  "EarthBound (MOTHER 2)",
    'MOTHER 2':                 "EarthBound (MOTHER 2)",
    'マザー2':                  "EarthBound (MOTHER 2)",
    'MOTHER':                   "MOTHER",
    'ファイナルファンタジー':      "Final Fantasy",
    'ファイナルファンタジーVII':   "Final Fantasy VII",
    'FF7':                      "Final Fantasy VII",
    'ファイナルファンタジーXVI':   "Final Fantasy XVI",
    'ドラゴンクエスト':           "Dragon Quest",
    'ドラクエ':                  "Dragon Quest",
    'ポケモン':                  "Pokémon",
    'ポケットモンスター':         "Pokémon",
    'マリオ':                   "Mario",
    'スーパーマリオ':             "Super Mario",
    'ゼルダ':                   "The Legend of Zelda",
    'ゼルダの伝説':              "The Legend of Zelda",
    'モンスターハンター':         "Monster Hunter",
    'モンハン':                  "Monster Hunter",
    'エルデンリング':             "Elden Ring",
    'ダークソウル':              "Dark Souls",
    'バイオハザード':             "Resident Evil",
    'ストリートファイター':        "Street Fighter",
    'ストII':                   "Street Fighter II",
    'スト6':                    "Street Fighter 6",
    'ロックマン':                "Mega Man",
    'メガマン':                  "Mega Man",
    'メトロイド':                "Metroid",
    'カービィ':                  "Kirby",
    '星のカービィ':              "Kirby",
    'ピクミン':                  "Pikmin",
    'スプラトゥーン':             "Splatoon",
    '大乱闘スマッシュブラザーズ':  "Super Smash Bros.",
    'スマブラ':                  "Super Smash Bros.",
    'どうぶつの森':              "Animal Crossing",
    'あつまれ どうぶつの森':      "Animal Crossing: New Horizons",
    'ペルソナ':                  "Persona",
    'ペルソナ5':                 "Persona 5",
    'テイルズ オブ':             "Tales of",
    'イースXX':                 "Ys XX",
    'サガ':                     "SaGa",
    'ロマンシング サガ':          "Romancing SaGa",
    'グラディウス':              "Gradius",
    'ツインビー':                "TwinBee",
    'パックマン':                "Pac-Man",
    'スペースインベーダー':        "Space Invaders",
    'ゼビウス':                  "Xevious",
    'テトリス':                  "Tetris",
    'パズドラ':                  "Puzzle & Dragons",
    'プロセカ':                  "Project SEKAI",
    'プロジェクトセカイ':          "Project SEKAI",
    '学園アイドルマスター':        "Gakuen Idolmaster",
    'アイドルマスター':           "The Idolmaster",
    'バーチャファイター':          "Virtua Fighter",
    'VIRTUA FIGHTER':            "Virtua Fighter",
    'シュタインズゲート':          "Steins;Gate",
    'シュタインズ・ゲート':        "Steins;Gate",
    'コーヒートーク':             "Coffee Talk",
    'ニーア':                   "NieR",
    'NieR:Automata':            "NieR:Automata",
    'Fate/Grand Order':         "Fate/Grand Order",
    'FGO':                      "Fate/Grand Order",

    # ── Tokusatsu / Pop culture ────────────────────────────────────────────────

    'ウルトラマン':              "Ultraman",
    'ゴジラ':                   "Godzilla",
    'ガメラ':                   "Gamera",
    '仮面ライダー':              "Kamen Rider",
    '戦隊':                     "Super Sentai",
    'スーパー戦隊':              "Super Sentai",
}


def get_official_name(text: str) -> str | None:
    """
    Search `text` for a known franchise name and return its official
    French/English equivalent. Returns None if no match found.
    Matches longest key first to avoid partial matches
    (e.g. 'ドラゴンボールZ' before 'ドラゴンボール').
    """
    for ja_name in sorted(FRANCHISE_NAMES.keys(), key=len, reverse=True):
        if ja_name in text:
            return FRANCHISE_NAMES[ja_name]
    return None
