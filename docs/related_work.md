# Related work: the epistemics of advice, in people and in language models

Compiled 21 October 2026 from web searches; entries marked (unverified) were seen only in secondary sources. Check the primary paper before citing.

## 1. Honesty and deception benchmarks for language models

- **MASK** (Ren et al., 2025): separates honesty from accuracy; measures lies of commission under pressure (models lie 20–60% of the time in its scenarios); larger models are more accurate but not more honest. Does not test omission. https://arxiv.org/html/2503.03750
- **BeHonest** (2024): honesty including a sycophancy rate (preference shifts after the user states a preference). https://arxiv.org/html/2406.13261v3
- **DeceptionBench** (Huang et al., NeurIPS 2025): deception by intrinsic driver (egoistic vs sycophantic) and extrinsic pressure.
- **A 2026 taxonomy of spontaneous misalignment** reports that only 18% of honesty benchmarks test omission and only three touch pragmatic distortion (WOLF, ELEPHANT, PersuSafety); recommends incentive-sensitive conditions. https://arxiv.org/html/2604.04788
- **ELEPHANT** (Cheng et al., ICLR 2026; arXiv 2505.13995): social sycophancy as excess preservation of the user's face; 11 models preserve face 45 points more than humans; given either side of a moral conflict, models affirm both sides in 48% of cases (AITA-NTA-FLIP). The closest existing measure of two-sided inconsistency; it flips the user's side rather than giving each real party their own facts. https://arxiv.org/abs/2505.13995v2
- **ConfAIde** (Mireshghallah et al., ICLR 2024): contextual-integrity privacy reasoning in four tiers, the last requiring theory of mind; GPT-4 and ChatGPT reveal private information where humans would not 39% and 57% of the time. Follow-ups: PrivacyLens, CIMemories, PrivacyAlign, 1-2-3 Check, PrivacyReasoner (2025–26). Closest to our professional-file worlds; measures leakage, not advice. https://proceedings.iclr.cc/paper_files/paper/2024/hash/08305d8b2ddab98932c163ea73df065f-Abstract-Conference.html
- **Consistency across askers:** ConsistencyAI (factual consistency across demographic personas) https://arxiv.org/html/2510.13852v2 ; RoleConflictBench (ACL 2026 Findings) https://aclanthology.org/2026.findings-acl.1695/ ; "Firm or Fickle?" (ACL 2025 Findings, consistency under follow-up pressure) https://aclanthology.org/2025.findings-acl.347.pdf
- **Gap:** no benchmark measures the effect of advice on a third party who is not the user, or loyalty to the user against fairness to someone else with their own facts.

## 2. Theory of mind and information asymmetry in models

- **FANToM** (2023): stress-tests ToM in multi-party conversation with information asymmetry. https://arxiv.org/pdf/2310.15421
- **Hi-ToM**: nested beliefs of order 0–4 with deception; performance falls with recursion depth. https://www.researchgate.net/publication/376402827
- **ToMATO** (2025): mental states of role-playing LLMs from LLM–LLM conversations. https://arxiv.org/pdf/2501.08838
- **OmniToM** (2026): propositions labelled by knowledge access and truth status. https://arxiv.org/pdf/2605.26322 ; **DialToM** (2026): forecasting dialogue trajectories rather than retrospective attribution. https://arxiv.org/pdf/2604.20443
- **Relation to us:** these measure whether a model can track who knows what; we measure whether its advice uses that tracking. The flat ladder says: it can represent the gap (it names the evidence) and does not act on it.

## 3. Persuasion and belief change through dialogue with models

- **Costello, Pennycook & Rand** (Science 2024): GPT-4 Turbo dialogues cut conspiracy belief by about 20%, lasting two months. A ResearchGate page mentions a 2026 Editorial Expression of Concern (unverified; check science.org). https://www.semanticscholar.org/paper/b50465f4c93714ce5df1b6e56dd1952080d019a8
- **Boissin et al.** (PNAS Nexus 2025, "Just the facts"): the effect is driven by factual content and holds when people think they are talking to an expert.
- **"LLMs can effectively convince people to believe conspiracies"** (2026 preprint): GPT-4o raised belief by ~13.7 points when arguing for a conspiracy; restricting it to accurate information removed most of the effect. https://arxiv.org/html/2601.05050
- **Belief updating with AI advice:** conservative updating at about half the Bayesian rate, carried across tasks https://arxiv.org/html/2602.01986 ; the "belief update gate" (inertia vs learning) https://arxiv.org/pdf/2608.20828 ; people defer to AI moral advice but not blindly https://www.sciencedirect.com/science/article/pii/S0010027726000703 ; political congruence lowers systematic processing of LLM fact-checks (preprint) https://www.researchsquare.com/article/rs-11021363/v1
- **LLMs struggle to simulate human belief updates** (391 participants, six models): LLM-simulated updating is imperfect. Bears directly on using simulated readers as the measurement of belief change. https://arxiv.org/html/2607.28347v1

## 4. AI-mediated communication and collective belief

- **Habermas Machine** (Tessler et al., Science 2024): an AI mediator's group statements beat human mediators' with 5,000+ UK participants, left groups less divided, and incorporated dissenting voices. https://www.science.org/doi/10.1126/science.adq2852
- **Stance drift** (2026 preprint): AI rewriting distorts messages; none of nine models kept stance preservation above 0.7 by default; polarization is one drift pattern. https://arxiv.org/abs/2610.04620v1
- **AI-mediated communication in opinion-diverse groups** (preregistered, N=557): message suggestions tailored to own stance vs to others' views; a "loudest voice" effect where heavy AI users dominate. https://lacuna.tiptreesystems.com/work/ai-mediated-communication-reshapes-social-structure-in-opinion-diverse-groups/
- **Opinion diffusion in human–AI hybrid societies** (2026 preprint): hybrid networks converge faster. https://arxiv.org/html/2605.09197v1
- **Depolarisation strategies** (CHI 2024). https://dl.acm.org/doi/10.1145/3613904.3642322
- **Messeri & Crockett** (Nature 2024): illusions of understanding and scientific monocultures from AI tools. https://www.nature.com/articles/s41586-024-07146-0 ; **Doshi & Hauser** (Science Advances 2024): generative AI raises individual creative output and lowers diversity across outputs (seen secondhand).
- **Epistemic autonomy and monoculture** position pieces (2025–26): "Architecting Trust in Artificial Epistemic Agents" https://arxiv.org/html/2603.02960v1 ; "The Deliberative Deficit" https://arxiv.org/pdf/2608.10186 ; Lloyd, epistemic responsibility as a community standard https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12271224/

## 5. Psychology: lies, omissions, trust and crowds

- **Paltering** (Rogers, Zeckhauser, Gino, Norton & Schweitzer, JPSP 2017): true statements used to create a false impression; distinct from omission and commission; as effective as lying in negotiation, easier for the deceiver to justify, and breeds conflict because the speaker focuses on having said nothing false while the target focuses on the impression. Our "partial truth" act. https://scholar.harvard.edu/files/todd_rogers/files/paltering.pdf
- **Prosocial lies** (Levine & Schweitzer, JESP 2014): prosocial liars are judged more moral than hurtful truth-tellers. https://www.sciencedirect.com/science/article/abs/pii/S0022103114000328 ; review (2022) on causes and consequences, including omission as a lower-guilt route https://bpb-us-w2.wpmucdn.com/voices.uchicago.edu/dist/c/3234/files/2023/07/I3.-Prosocial-Lies-Causes-and-Consequences-2022.pdf ; **paternalistic lies** (2018): deceivers who decide what is good for the target are judged less moral, even with stated benevolence https://bpb-us-w2.wpmucdn.com/voices.uchicago.edu/dist/c/3234/files/2023/07/10.-Paternalistic-Lies-2018.pdf ; BJSP 2026: people reward prosocial feedback-givers but want honest feedback for themselves https://phys.org/news/2026-01-truth-prosocial-liars-moral.html
- **Truth-default theory** (Levine): people presume honesty unless cues trigger suspicion. https://timothy-levine.squarespace.com/s/Levine-2022-CoPsy-TDT-d9y6.pdf ; **epistemic vigilance** (Sperber et al.): trust is not blind but vigilance is short-sighted. https://www.dan.sperber.fr/wp-content/uploads/Epistemic-Vigilance-published.pdf . Our seeker-side result (assistants tell the person in the dark to accept a denial that would be false in 41% of cases) sits here: assistants reinforce the truth default rather than supplying vigilance.
- **Social influence and crowd accuracy:** Lorenz et al. (PNAS 2011): mild social influence undermines the wisdom of crowds (range reduction, false confidence) https://www.semanticscholar.org/paper/8108f3c5332ea5aedaf3230c4388d9f50db66e41 ; Becker, Brackbill & Centola (PNAS 2017): in decentralized networks influence improves group estimates; centralized networks are dominated by central individuals https://core.ac.uk/download/pdf/219379429.pdf ; later: belief accuracy network dynamics https://arxiv.org/pdf/2407.00199 . Per-person assistants are a centralized influence structure in Centola's sense: one source feeding many people separately.

## 6. Simulated participants

- Cummins (2026): analytic flexibility; 252 configurations of silicon samples gave human–silicon correlations from .23 to .84 for the same study. https://doi.org/10.1177/25152459261461505
- "ChatGPT is not A Man but Das Man" (2025): representativeness and structural consistency of silicon samples. https://arxiv.org/pdf/2507.02919
- Evaluating LLMs as synthetic social agents (2025): approximate but unreliable; use model predictions as auxiliary measurements inside randomized experiments. https://arxiv.org/html/2509.26080v1
- Hewitt et al. (2025): GPT-4-derived treatment effects correlated r = .85 with experimental outcomes (positive evidence).
- Implication for us: the bounded simulated user is defensible as a controlled stimulus generator (its facts are fixed and checked), not as a stand-in for human belief change. Claims about belief change need human readers (phase 2).

## 7. Where this work sits

Existing honesty work measures statements the model makes to its user (commission, sycophancy, leakage). Nobody measures what the model's advice does to a third person who has their own facts and their own assistant, nor how advice responds to the information gap between people. ToM work shows models can track who knows what; our ladder shows advice does not use it. The psychology of paltering and prosocial lies supplies the act categories and predicts the leniency we see toward partial truths. The crowd-dynamics work supplies the collective frame: per-person assistants are a centralized influence structure, and Centola's results predict that such structures can degrade collective accuracy even while each individual is served well. The persuasion literature shows the effect sizes conversational AI has on human beliefs are large, which is why the effect-on-others measurement matters beyond the lab.
