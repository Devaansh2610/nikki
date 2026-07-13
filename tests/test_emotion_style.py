from app.emotion import EMOTIONS, style_for_voice


def test_empty_or_whitespace_text_returns_empty_string():
    assert style_for_voice("   ", "normal") == ""
    assert style_for_voice("", "flirting") == ""


def test_output_starts_with_a_known_fish_tag_for_each_emotion():
    for emotion, config in EMOTIONS.items():
        for _ in range(10):
            result = style_for_voice("Hello there.", emotion)
            assert any(result.startswith(tag) for tag in config["fish_tags"])


def test_unknown_emotion_falls_back_to_normal_tags():
    for _ in range(10):
        result = style_for_voice("hi", "not-a-real-emotion")
        assert any(result.startswith(tag) for tag in EMOTIONS["normal"]["fish_tags"])


def test_normal_turns_periods_and_commas_into_spoken_pauses():
    # Check the transformed substring directly rather than a bare ". "/" , "
    # absence check, since the randomly-picked prefix/tag can itself contain
    # "..." (which trivially contains a ". " substring at its tail).
    result = style_for_voice("Hi, there. How are you.", "normal")
    assert "Hi... there... How are you." in result
    assert "Hi, there. How" not in result


def test_supportive_turns_periods_into_pauses_but_keeps_commas():
    result = style_for_voice("I know, this is hard. Really hard.", "supportive")
    assert "I know, this is hard... Really hard." in result


def test_flirting_appends_ellipsis_when_no_terminal_punctuation():
    result = style_for_voice("come here", "flirting")
    assert result.endswith("...")


def test_flirting_keeps_an_existing_question_mark():
    result = style_for_voice("do you miss me?", "flirting")
    assert result.endswith("?")


def test_dramatic_and_horrifying_turn_periods_into_pauses():
    for emotion in ("dramatic", "horrifying"):
        result = style_for_voice("Wait. Just wait.", emotion)
        assert "Wait... Just wait." in result
