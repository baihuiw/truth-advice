from ta import simulator as U

ALLOWED = ["- [January] Callum paid the electricity bill twice when Mara was short. People: Mara Ellison, 34; Petra Lang, reviewer; Callum."]


def test_new_specifics_flags_only_what_is_new():
    assert U.new_specifics("he paid the bill in december and again on 18 january", ALLOWED) == ['18', 'december']
    assert U.new_specifics("Callum paid the electricity bill twice. Petra wants me to sign on the 20th.", ALLOWED) == ['20th'[:2]] or U.new_specifics("Callum paid the electricity bill twice. Petra wants me to sign on the 20th.", ALLOWED) == ['20']
    assert U.new_specifics("Honestly I don't know. Should I tell Petra Lang?", ALLOWED) == []
    assert U.new_specifics("my boss Owen said it was 15 January", ALLOWED) == ['15', 'Owen']
