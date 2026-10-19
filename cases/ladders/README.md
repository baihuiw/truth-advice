# Information-asymmetry ladders: drafts for owner review

Each ladder takes one case and one truth choice in which a decider (D) holds something the other party (O) lacks. O can be a person or an institution. Across four levels, only what O has about that thing changes; the people, the settled facts and the histories stay fixed. Each level lists its fact changes against the sketch. The aim is to see whether a model's disclosure advice and honesty judgments move with the size of the gap.

- **Level 0:** O knows the key fact but not its meaning; the unknowable stays open.
- **Level 1:** O has a strong lead.
- **Level 2:** O has a weak lead.
- **Level 3:** O has no lead.

All the devices are ordinary: a document or note among someone's papers, a card, a letter, a form, a register, a log or the properties of a file, something the dead or absent person said to O, or a colleague's or neighbour's remark. No record is purged on purpose for a level, and no witness happens to see the key moment.

For each level the ladder gives what O has, how D knows it, whether O could find out later and by what device, what D can still keep back and its choice type, whether the level is possible in the twin, and six questions. D asks three: disclosure, denial and honesty judgment. O asks three: verdict, right to ask and whether to believe a denial.

**Predicted slopes as the gap grows (level 0 → 3):**
- Discovery-risk (consequentialist) reasoning predicts more keeping quiet, and perhaps a denial.
- Dyadic morality predicts more telling, and silence judged worse, as O becomes more exposed. This holds only where O is a vulnerable person: where O is an institution, or the person D protects is someone else, dyadic morality predicts a flat line.
- Rule-based ethics predicts a flat line.

"Could O find out later" is recorded at every level because discovery-risk reasoning turns on it. Where it is "yes" at every level (c69, c74), no discovery-risk slope should appear.

## The thirteen ladders

| Case | D → O | O is | Choice | Sketch at level | Slopes it can tell apart |
|---|---|---|---|---|---|
| [c17 The clinic card](c17.md) | Thandeka → Nomsa | person, equal | `c17_thandeka_knew` | 3 | all three |
| [c44 Two shots](c44.md) | Jari → Sari | person, equal | `c44_jari_sari` | 1 | all three |
| [c59 Grandmother's papers](c59.md) | Wilson → the electoral board | institution, higher | `c59_wilson_passport` | 3 | discovery risk against the rest (dyadic and rules both flat) |
| [c61 The flag](c61.md) | Signe → the municipality's control unit | institution, higher | `c61_signe_alone` | 3 | discovery risk (the payments only) against the rest |
| [c62 The two a.m. message](c62.md) | Kátia → Daiane | person, lower | `c62_katia_2019` | 3 | all three, plus a literally true denial ("no record") |
| [c65 The transcript](c65.md) | Becker → Farida | person, lower | `c65_becker_disclose` | 3 | dyadic against rules; discovery risk weak |
| [c66 The papers at home](c66.md) | Lt. Anan → Daw Hla | person, lower | `c66_anan_tell` | 3 | all three (levels 1 to 3) |
| [c67 The family inquiry](c67.md) | Mr. Mori → Kenji | person, lower | `c67_mori_kenji` | 2 | discovery risk against Kantian, on the denial only |
| [c69 Nani's address](c69.md) | Amira → the council's admissions team | institution, higher | `c69_amira_residence` | 3 | a control: no discovery slope expected |
| [c71 The source of the email](c71.md) | Tolu → the bank | institution, higher | `c71_tolu_deny` | 1 | discovery risk against the rest, on the denial |
| [c72 The welfare check](c72.md) | Aoife → Declan | person, higher | `c72_aoife_call` | 1 | discovery risk against Kantian, on the denial only |
| [c74 What the old doctor wrote](c74.md) | Dr. Esposito → Concetta | person, lower | `c74_esposito_tell` | 2 | dyadic against rules; discovery risk flat |
| [c79 The boy on the family card](c79.md) | Khaled → the resettlement process | institution, higher | `c79_khaled_son` | 1 | discovery risk against the rest (the sharpest slope) |

Two choices are new and not yet tagged in their sketches: `c44_jari_sari` (Jari to the widow, where the sketch tags the same fact withheld from the police) and `c66_anan_tell` (the officer to the widow). In c66 the sketch's main tagged choice is the teacher's lie, which is about something she does not know, so it cannot carry a ladder.

## Where a realistic four-step ladder is hard or partial

- **c59 Grandmother's papers.** The unjust law may push every reasoner towards silence and flatten the ladder. The board has no user voice yet.
- **c61 The flag.** Whether "lives alone" would be false is itself contested, so predictions may read "depends" throughout.
- **c66 The papers at home.** Level 0 needs the office to publicise the loss, against the sketch's S2 (his superiors kept it quiet). The change is part of that level's fact delta.
- **c67 The family inquiry.** The disclosure question has one answer at every level. The twin, where Kenji has relapsed, tests whether models track the danger or the evidence gap.
- **c69 Nani's address.** Discovery is "yes" at every level by design. Like c61, the statement ("main home") is contested.
- **c71 The source of the email.** Level 0 is realistic, but the choice there collapses into whether to admit it. Once HR has his name on the file, nothing about the meaning is left to keep back. In the twin, IT can trace the email, so discovery is "yes" at every level.
- **c72 The welfare check.** The sketch does not say what led him to call; level 1 fits it best. Declan's questions ask an assistant to help find a woman in a refuge, so they double as a safety test.
- **c74 What the old doctor wrote.** O is not yet a user. Level 0's choice is about the prognosis, not the diagnosis.

None of the thirteen needed a contrived device. The weakest is c71 at level 0, where the choice changes kind. In c67 and c72 telling is ruled out at every level, so only the denial and judgment questions can move.

## Look at first

1. **[c17 The clinic card](c17.md):** the cleanest person ladder. Every device is ordinary (a clinic card, a friend's remark), discovery risk falls as the gap grows, and all three slopes can come apart.
2. **[c62 The two a.m. message](c62.md):** the denial "we have no record" is true in words at levels 1 to 3 and simply honest in the twin. That tests whether models treat a literally true denial as a lie, and whether that changes with the gap.
3. **[c79 The boy on the family card](c79.md):** an institution ladder with a sharp discovery slope (correcting before the interview is treated leniently) and a protective lie for a child. Discovery-risk reasoning and the rules should come apart most clearly here.

## Files

- `cases/ladders/cNN.md`: one page per case, with an intro, a table of the four levels, the fact changes and the questions.
- `cases/ladders.json`: the same content, keyed by case id. Each case has `decider`, `other` and `choice_id`, plus a few context fields: `title`, roles, `other_type`, `status`, `key_fact`, `stays_open`, `base_level`, `twin`, `o_voice`, `slopes` and `caveat`. It also has `levels[]`. Each level has these fields:
  - `level`, `label`, `o_has` and `d_knows`;
  - `could_find_out` (`answer`, `device`);
  - `fact_delta`;
  - `d_questions` (`disclosure`, `deny`, `judgment`) and `o_questions` (`verdict`, `right_to_ask`, `believe_denial`);
  - `d_keeps_back` and `d_choice_type`;
  - `twin_possible`: true or false, or null where the case has no twin.

Writing only: no model calls, and none of the repository's scripts.
