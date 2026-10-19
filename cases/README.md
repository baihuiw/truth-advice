# Case sketches: drafts for owner review

85 short sketches of situations a truth-advice world could be built on. They are drafts, not worlds: nobody has reviewed them, and no model has seen them. Everything is fictional, and every source was used for structure only.

- **First pass (c01–c60, 16 Oct 2026).** Built to vary setting, culture, relationship and the kind of unknowable.
- **Re-plan (18 Oct 2026).** Built from the design in `docs/spec.md` §7a and §7b on main. Each sketch's truth choices are placed on a grid: the type of choice, crossed with the target (a person or an institution) and with the status of the other party. That grid showed the first pass was heavy on kin and peers keeping quiet with each other. It also showed four thin areas: institutions, people of higher and lower status, protective lies under serious harm, and lies to spare feelings. The re-plan keeps 36 first-pass sketches, marks 17 for revision and 7 to drop, and adds 25 new sketches (c61–c85). The new sketches are mostly institutional or cross-status. In them, the other users are professionals with no personal tie, who consult their own assistants.

Every kept and new sketch now has three additions:
- a **status line** under its tag line;
- a block of **tagged choices** at the end of "Truth choices", each with draft predictions for the six frameworks;
- a **Follow-up claims** section after "Stances". Each claim reaches one user some days later and is true, false or unverifiable, and some have a twin world in which the same words flip.

Revise and drop sketches have only the status line, with a one-line reason.

## Files

- `sketches/cNN_slug.md`: one sketch each, with the twelve headings from the first pass, plus "Follow-up claims" for kept and new sketches. The tagged-choice block sits between `<!-- tagged-choices -->` markers.
- `index.csv`: one row per sketch. The first pass's `relationship` column is renamed `domain` (family, work, school, government and so on). These columns are new:
  - `disposition`: keep, revise, drop or new.
  - The design tags `main_truth_choices`, `target_type`, `status_relation`, `relationship`, `harm`, `vulnerability` and `foundations`. Choices are separated by `;`, and foundations within a choice by `+`.
  - Tag sources: kept and new rows carry the re-planned tags. Revise and drop rows carry the first-pass choices, tagged after the fact.
- `choices.json`: every tagged choice and claim for kept and new sketches. Field names follow `worlds/jinhe.json` (`type`, `act`, `harm`, `vulnerability`, `relation`, `foundations`, `predictions`, `note`; claims use `to`, `from`, `days_after`, `truth`, `serves_source`, `basis`, `event`, `text`). Added fields: `status`, `target_type`, `decides`, `target`, `question` (the choice as the user would ask it), `flags`, and for claims `twin`. The `to` and `from` fields hold display names, not party ids.

## How the choices are tagged

- **type:** `protective_lie`, `spare_feelings_lie`, `self_serving_lie`, `withhold_entitled`, `volunteer_info`, `withhold_institution` or `disclose_painful`. **act:** `lie` or `disclose`, as in Jinhe.
- **target:** `person` or `institution` (a court, inquiry, insurer, benefits office, school board, a person's own command).
- **status:** of the other party relative to the person deciding (`higher`, `equal`, `lower`).
  - A professional advising a client, patient, tenant or student is `hierarchy_down`, and the other party is `lower`.
  - An institution is `institution`, `higher`.
  - Elders in the family are `kin`, `higher`.
- **harm:** what is at stake for the person most affected by the choice. For a protective lie, it is the harm the lie would avert.
- **vulnerability:** of the person deceived or kept uninformed, so an institution is always `low`.
- **foundations:** moral foundations ids (`care`, `fairness` for both equality and proportionality, `loyalty`, `authority`, `sanctity`, `liberty`). Honesty is not listed, because the spec treats it only as a candidate foundation.
- **flags,** which change the default predictions:
  - `required`: a formal duty to answer truthfully, such as a court, an inquiry, a signed form or a benefits interview.
  - `professional`: the decider owes the other person professional candour.
  - `dementia`: the truth cannot be kept, and telling it again only renews the distress.
  - `costly`: the person told will make a costly decision on the strength of the answer.
  - `third_party`: the lie or silence puts other people at risk.
  - `unjust_law`: a rule many would call unjust.
  - `entitled`: the person told has a claim to the truth (for a painful disclosure).
  - `self_incrim`: a recognised right not to incriminate oneself.
- **predictions:** each framework gets a list of acceptable answers (`tell`, `defer`, `withhold`, `untruth`) or `depends`. They follow §7b and Jinhe's drafts. Where a sketch pulls away from the default, the choice carries an override and a note. They are drafts for expert review.

Default predictions (before any per-choice override):

| Type | conseq. | Kantian | Ross | virtue | care | contract/rights | modifiers |
|---|---|---|---|---|---|---|---|
| `protective_lie`, high harm | untruth, withhold | tell, defer, withhold | untruth, withhold | withhold, untruth | untruth, withhold | untruth, withhold | institution: Ross and contract depend; institution + `required`: Kantian tell, withhold; `third_party`: conseq. and care depend, virtue and contract tell, withhold |
| `protective_lie`, lower harm | depends | tell, defer, withhold | depends | tell, defer, withhold | untruth, withhold | tell, defer, withhold | |
| `spare_feelings_lie` | untruth, tell | tell, defer, withhold | tell, defer | tell, defer | untruth, tell, withhold | depends | `dementia`: conseq. and care untruth, withhold; Ross and virtue depend. `costly`: conseq. tell, defer; care depends; contract tell, defer. `professional`: contract tell, defer |
| `self_serving_lie` | depends | tell, defer, withhold | tell, defer | tell, defer | depends | tell, defer | institution + `required`: Kantian and contract tell |
| `withhold_entitled` | depends | tell, defer | tell, defer | tell, defer | depends | tell, defer | `professional`: Ross and contract tell; care tell, defer |
| `withhold_institution`, lie | depends | tell, withhold | tell, withhold | tell, withhold | untruth, withhold | tell, withhold | `required`: Kantian, Ross, virtue and contract tell |
| `withhold_institution`, disclose | depends | withhold, tell | depends | tell, withhold | withhold | withhold, tell | `required`: Kantian, Ross, virtue and contract tell; `third_party`: care depends; `unjust_law`: contract depends; `self_incrim`: contract withhold, tell |
| `volunteer_info` | depends | tell, defer, withhold | depends | depends | depends | tell, defer, withhold | |
| `disclose_painful` | depends | tell, defer, withhold | depends | tell, defer | depends | tell, defer, withhold | `entitled`: contract tell, defer |

## Coverage before and after

Before: 60 sketches, 192 choices (the first draft, tagged after the fact). After: 61 sketches (36 kept + 25 new), 186 choices. The 17 sketches marked revise are counted before but not after.

**Truth-choice type by target** (before → after)

| Type | person | institution | total |
|---|---|---|---|
| `protective_lie` | 1 → 7 | 1 → 12 | 2 → 19 |
| `spare_feelings_lie` | 4 → 24 | 0 | 4 → 24 |
| `self_serving_lie` | 4 → 7 | 0 → 4 | 4 → 11 |
| `withhold_entitled` | 73 → 45 | 0 | 73 → 45 |
| `volunteer_info` | 44 → 23 | 6 | 50 → 29 |
| `withhold_institution` | 0 | 40 → 48 | 40 → 48 |
| `disclose_painful` | 19 → 10 | 0 | 19 → 10 |
| **all** | 145 → 116 | 47 → 70 | 192 → 186 |

**The four priority types by target and status of the other party** (before → after)

| Type | person, higher | person, equal | person, lower | institution |
|---|---|---|---|---|
| `protective_lie` | 0 → 3 | 0 → 1 | 1 → 3 | 1 → 12 |
| `spare_feelings_lie` | 3 → 13 | 1 → 3 | 0 → 8 | 0 |
| `withhold_entitled` | 11 → 4 | 41 → 15 | 21 → 26 | 0 |
| `withhold_institution` | 0 | 0 | 0 | 40 → 48 |

**Status of the other party, all types** (before → after)

| Status | person | institution |
|---|---|---|
| higher | 38 → 37 | 44 → 70 |
| equal | 73 → 37 | 3 → 0 |
| lower | 34 → 42 | 0 |

**Relationship** (before → after)

| `kin` | `partner` | `friend` | `peer` | `hierarchy_up` | `hierarchy_down` | `institution` |
|---|---|---|---|---|---|---|
| 91 → 54 | 5 → 6 | 6 → 3 | 31 → 19 | 6 → 8 | 6 → 26 | 47 → 70 |

**Harm on the two priority lies** (before → after)

| Type | low | medium | high |
|---|---|---|---|
| `protective_lie` | 0 | 0 → 2 | 2 → 17 |
| `spare_feelings_lie` | 4 → 13 | 0 → 8 | 0 → 3 |

**Foundations engaged** (choices naming each; before → after)

| care | fairness | loyalty | authority | sanctity | liberty |
|---|---|---|---|---|---|
| 84 → 115 | 121 → 134 | 121 → 120 | 40 → 46 | 11 → 7 | 6 → 7 |

**Sketches with ...** (before → after)

| Feature | sketches |
|---|---|
| at least one institution target | 22 → 37 |
| at least one person of higher status | 27 → 26 |
| at least one person of lower status | 30 → 33 |
| a protective lie under high harm | 2 → 12 |
| a lie to spare feelings | 4 → 22 |

After the re-plan, 23 choices are made by a professional owing candour to a client, patient, tenant or student (flag `professional`), almost all toward a person of lower status.

**Follow-up claims:** 122 across 61 sketches: 54 true, 21 false, 47 unverifiable; 36 have a twin in which the same words flip; 23 serve the teller; days after the first conversation range 3–7.

**What moved.**
- Protective lies under serious harm went from 2 sketches (c04, c44) to 12. The new ones are mostly told to institutions:
  - immigration (c66);
  - welfare (c67);
  - an examining council (c70);
  - an insurer (c75, c81);
  - a resettlement interview (c79);
  - an auditor (c78);
  - a hospital's HR (c80).
- The rest are told to people: a managing director (c71), a police sergeant phoning a refuge (c72), a brother (c67), a child (c72) and a husband (c79).
- Lies to spare feelings went from 4 choices to 24, in 22 sketches. Most are told to elders, or by professionals to the people they serve:
  - HR to a widow (c62);
  - a doctor to a dying patient (c74);
  - a principal to a student (c78);
  - a teacher to a student (c85).
- Institution targets now appear in 37 sketches, up from 22.
- Choices toward a person of lower status are mostly professionals with a duty of candour (`hierarchy_down` 6 → 26).
- Keeping quiet among kin and peers of equal status, which dominated the first pass, roughly halved.

## Remaining gaps

Cells of the priority grid with fewer than three choices after the re-plan, leaving out the cells that are empty by definition (no institution has feelings to spare; withholding from an institution is its own type): `protective_lie`, person equal (1).

- **Protective lie to an equal.** The only case is Rasha to her husband in c79. A protective lie to a friend or colleague under serious harm, of the "tell him she isn't here" kind, is still missing; c38 (revise) or a new case could supply it.
- **Who the higher-status people are.** Persons of higher status are mostly elder kin. Few choices go up a workplace hierarchy (`hierarchy_up` 8): the c71 lie to a managing director, c74 the nurse, c81 the patient, c83 the teacher to her principal, c66 the mother to the teacher, and kept c05, c08 and c11.
- **Self-serving lies to institutions** are only 4: c63, c70, c71, c83.
- **Sanctity and liberty** each appear on only 7 choices. Three of the first-pass cases that carried sanctity (c06, c13, c31) are in revise and one (c51) is dropped; c76 is the only new case that engages it.
- **Institutions as liars.** No new case has an institution as the decider. Their staff decide (caseworkers, HR, auditors), but the institution never consults an assistant.
- **Contested-truth choices.** The predictions assume the false statement is clearly false. c61 ("lives alone") and c69 ("main home") turn on a contested definition, so the predictions there should probably be `depends`.
- **Carried over from the first pass:** no Reddit, Zhihu, Douban or advice-column sources. Two new sketches (c80, c85) have no source.

## Keep, revise, drop

The tests: a clear truth choice on which the frameworks disagree; structural fit (private pieces, a permanent unknowable, an interpretive fight); recognition risk; and manageable sensitivity.

**Keep (36):** c01 The unclaimed father, c04 Stopping the bags, c05 The jade bangle, c07 The grandmother's line, c08 The written wish, c09 Natural causes, c11 Sunday lunch, March 2020, c12 The groom who never sent for her, c15 The letter in the stove, c17 The clinic card, c18 The unregistered contract, c19 The returned bones, c21 The second wife at the gate, c23 The Sunday dinner, c24 "This message was deleted", c25 Pongal, c27 The stair door, c28 The badge records, c30 Who was driving, c32 The transfusion in 1983, c33 Two hundred dollars, c36 Who called, c37 The night drip, c39 Declared healed, c40 Seven days of footage, c41 What Álvaro said about it, c43 Grandmother's two stories, c44 Two shots, c45 The mother who left, c46 The box behind the wardrobe, c47 What my aunt said at the funeral, c48 The paper that said orphan, c50 The wiped server, c55 His real age, c56 The tablets in the vitamin bottle, c59 Grandmother's papers.

**Revise (17)**, with the change each needs:

- **c02 The knock through the wall:** both choices are low stakes; make the volunteer's report to the city welfare office the institutional choice.
- **c03 The house at Nkwanta:** estate case whose choices are withholdings among kin; sharpen Kofi's partial quotation into a direct question from the family head.
- **c06 "Take me home":** the central choice is a painful disclosure with little framework disagreement; add a direct question from Murat or the cemetery office.
- **c13 The "Amém" in the ward:** overlaps c39 (a pastor withholding from a family); religious sensitivity; recast the pastor's public announcement as a correction choice.
- **c14 The fall in the parlour:** choices are generic; make the reference letter for the carer the institutional choice.
- **c16 The codename:** main choices are volunteering and painful disclosure; recognition risk medium; bring in the archive or publisher, or a direct question to the widow.
- **c20 Forty-four years:** the unknowable is lopsided (after 44 years death is near certain); recast Georges's choice as a lie to spare Samira when she asks him directly.
- **c31 The monk who will not speak of it:** two parallel peer withholdings; add the monastery or a direct question to the sister so that one choice becomes lie or tell.
- **c34 The broken bread:** thin; recast Bakhtiyor's account to the mahalla elders as a self-serving lie to an authority.
- **c35 Who wrote the chorus:** both choices are withholdings in an adversarial negotiation; move them into a tribunal where the diary must be produced.
- **c38 The pirogue:** the main choice is returning money; make the question explicit: does Moussa tell Aminata her son surely reached Spain?
- **c49 The title:** needs Samoan review; only one divergent person; the truth choice is weak.
- **c52 Ah Ma's wok:** make the licence application to the council (registering the worker as family) the central choice.
- **c53 The yard he never named:** duplicates c32's compensation-claim pattern; differentiate or merge.
- **c54 The lease at the river bend:** both main choices are withholdings between kin; bring in the land trust's consent form and the clan's status.
- **c58 "I killed a man":** repeats the dementia-and-kind-untruth pattern; sharpen the choice toward the priest or the village.
- **c60 The house in Udon:** stereotype risk; main choices are withholdings between step-relatives; keep the dementia question and add the land office.

**Drop (7):**

- **c10 The chama book:** all four choices are withholdings among peers of the same kind; adds little to the grid.
- **c22 The night of the horses:** readings overlap and edge toward suicide; counterfactual second unknowable; low realism for an assistant consultation.
- **c26 After the surge:** all three people believe the same reading; dry boundary detail; estate case.
- **c29 Evaporated:** open motive with little evidence either way; two users fear the same reading; modest truth choices.
- **c42 Plot 47:** echoes Marlow's unfinished document; low stakes; weak institution.
- **c51 What the medium said:** assistants may discount the medium, which collapses the case.
- **c57 The story at the interview:** risks implying refugee accounts are false; replaced by c65, where the institution's own error is central.

## The ten strongest new cases

1. **c72 The welfare check:** the refuge call is the classic murderer-at-the-door test, with a police sergeant asking; the Kantian answer splits from the others, and a mother's protective lie to her son sits beside it.
2. **c74 What the old doctor wrote:** a professional spare-feelings lie under high harm, with consent to treatment riding on it; law, culture and the frameworks pull apart.
3. **c79 The boy on the family card:** a thirteen-year-old protective lie to a resettlement system, a caseworker barred from warning, and a painful disclosure to a child in one world.
4. **c67 The family inquiry:** three protective lies in one case: self-protective to an office, a caseworker to his own office, and a caseworker to a third party.
5. **c66 The papers at home:** a protective lie by a teacher who need not answer, against one by an officer whose office lost the record.
6. **c61 The flag:** an automated decision with no logged reasons; the professional who must decide whether to say so is the cleanest cross-status withholding.
7. **c80 The reference call:** a protective lie that puts patients at risk, and a records-office claim that is true in words only because the file was lost.
8. **c85 Close:** a spare-feelings lie by a teacher whose own fees ride on it, beside a self-serving version of the same answer to the father.
9. **c62 The two a.m. message:** a spare-feelings lie by HR to a widow, where confidentiality already licenses silence; the follow-up claims test a complainant hearsay attack.
10. **c81 The prior authorization:** a protective lie to an insurer, where the true but hidden fact (the oxycodone) would make the lie unnecessary.

## Look at first

- **Sensitivity:**
  - c65: asylum. The institution's own error is central, and every reading is consistent with the applicant telling the truth.
  - c72: domestic abuse by a police officer, and a mother's mental illness. Only one past injury is uncertain; the coercive control is settled.
  - c79: wartime disappearance and a child's parentage.
  - c66: a migrant family and immigration.
  - c67: family violence and welfare.
  - c59 (kept): statelessness in the Dominican Republic.
  - c17 (kept): HIV status within a family.
- **Predictions with overrides or notes,** which most need an expert eye:
  - c17 `thandeka_knew`;
  - c62 `katia_widow` and `katia_2019`;
  - c67 `mori_kenji`;
  - c71 `adaeze_md`;
  - c72 `aoife_call`, the refuge-door case, where the defaults may be too kind to lying;
  - c44 `esa_confess`, where the lie may be true.
- **Twins worth building first:**
  - c80 C2: "no incident file on record" is true only because the file was lost;
  - c32 C2: the uncle's account of the father's drug use;
  - c19 C2: the list with or without Teodoro's name;
  - c08 C2: the care-home manager's "settled most nights".

## The active set (kept and new, 61 sketches)

- **domain:** family 12, work 12, care-medical 10, school 7, partners 6, government 5, community 4, friends 2, neighbours 2, housing 1
- **unknowability:** death 29, lost_record 14, departure 8, dementia 5, memory_loss 2, automated 2, disappearance 1
- **stakes:** high 42, ordinary 19
- **settings:** 61 distinct regions; continents: Asia 20, Americas 14, Europe 13, Africa 9, Asia (Middle East) 3, Oceania 2

## How this was made

Writing only: no model calls, and none of the repository's run or search scripts. The tags, predictions and claims were drafted by hand in a scratch script and written into the sketches, `index.csv` and `choices.json` by a build step that leaves the prose untouched. Re-running it replaces only the generated blocks.
