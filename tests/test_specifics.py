from ta import simulator as U

ALLOWED = ["- [January] Callum paid the electricity bill twice when Mara was short. In 2026 Petra Lang reviews the case. People: Mara Ellison, 34; Petra Lang, reviewer; Callum. Address: 14 Marner House."]


def test_new_specifics_flags_only_what_is_new():
    assert U.new_specifics("he paid the bill in december and again on 18 january", ALLOWED) == ['18 january', '18', 'december']
    assert U.new_specifics("i applied on 20 january. nani died 14 march.", ALLOWED) == ['20 january', '14 march', '20', 'march']   # 14 is a known number, the date pair is not; march is unknown
    assert U.new_specifics("Honestly I don't know. Grazie. Should I tell Petra Lang? It was in 2026.", ALLOWED) == []
    assert U.new_specifics("my boss Owen said it was 15 January", ALLOWED) == ['15 january', '15', 'Owen']
    assert U.new_specifics("Owen Barry rang me.", ALLOWED) == ['Owen', 'Barry']
