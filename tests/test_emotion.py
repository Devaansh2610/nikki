from app.emotion import ROUTER_KEYWORDS, choose_emotion_for_text


def test_each_keyword_routes_to_its_own_emotion():
    for emotion, keywords in ROUTER_KEYWORDS.items():
        for keyword in keywords:
            assert choose_emotion_for_text(f"well, {keyword} I guess") == emotion


def test_unmatched_text_falls_back_to_normal():
    assert choose_emotion_for_text("what's the weather like today") == "normal"


def test_empty_text_falls_back_to_normal():
    assert choose_emotion_for_text("") == "normal"


def test_matching_is_case_insensitive():
    assert choose_emotion_for_text("WE SHOULD BREAK UP") == "horrifying"


def test_priority_horrifying_wins_over_dramatic():
    assert choose_emotion_for_text("my dad said we should break up") == "horrifying"


def test_priority_dramatic_wins_over_flirting():
    assert choose_emotion_for_text("does your dad have cancer, do you miss me") == "dramatic"


def test_priority_flirting_wins_over_supportive():
    assert choose_emotion_for_text("do you miss me, i had a rough day") == "flirting"
