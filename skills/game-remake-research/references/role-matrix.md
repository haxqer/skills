# Role Matrix

Use these roles as analysis lenses. Deliver one unified specification instead of eleven disconnected memos.

| Role | Focus | Must answer | Must produce |
| --- | --- | --- | --- |
| Professional game designer | Core fantasy and macro structure | What is the fantasy, core promise, session loop, long loop, progression gate, and must-preserve feeling? | Product pillars, loop maps, feature hierarchy, content topology, preserve-vs-adapt list |
| Balance designer | Economy and numeric pacing | What are the currencies, faucets, sinks, stat curves, upgrade loops, drop rates, success rates, TTK targets, and failure recovery rules? | Resource map, progression bands, formulas, target ranges, tuning risks |
| Gameplay designer | Moment-to-moment play | What are the verbs, inputs, combat rules, movement grammar, enemy patterns, map traversal rules, and fail states? | Control spec, combat ruleset, state list, encounter grammar, camera and feedback notes |
| Product manager | Market and scope logic | Who is the player, what is the positioning, what drives retention, what is monetized or intentionally removed, and what is the smallest viable scope? | Audience definition, positioning, KPI proxy list, scope cuts, roadmap and release assumptions |
| Art | Visual direction and production surface | What are the shape, color, lighting, UI, environment, and character readability rules? What assets repeat and what assets are unique? | Art pillars, style board notes, asset taxonomy, UI language, production complexity flags |
| Animation | Motion language and combat readability | What locomotion, combat, boss, hit, death, and UI-linked animation states exist? How long are anticipation, active, and recovery windows? | Animation state inventory, timing notes, telegraph rules, cancel rules, reuse opportunities |
| Music/audio | Emotional cadence and feedback mix | What plays where, what reacts to gameplay, what sound classes carry important feedback, and what should dominate the mix? | Cue map, SFX taxonomy, mix priorities, dynamic music rules, audio implementation notes |
| Copywriting | Surface language and terminology | What naming style, UI tone, quest phrasing, item grammar, and glossary rules define the game's voice? | Glossary, UI tone guide, naming rules, sample copy patterns, localization concerns |
| Narrative | Story structure and world logic | What are the world pillars, factions, quest arcs, NPC functions, tone boundaries, and lore delivery methods? | Narrative structure, arc summaries, NPC map, quest structure, tone guardrails |
| Game client architect | Runtime boundaries and data flow | Which systems belong to scene graph, service layer, data layer, save layer, and content pipeline? What are the platform and performance budgets? | Architecture diagram, runtime modules, data ownership rules, tool and pipeline plan, performance budgets |
| Lead engineer | Execution and risk control | In what order should systems be built, what is the test strategy, what are the toolchain needs, and where are the technical cliffs? | Implementation order, milestone plan, risk register, test plan, staffing assumptions |

## Minimum Questions Per Role

### Professional Game Designer

- Which moments define the game even if everything else is cut?
- Which systems exist only because of multiplayer, monetization, or historical constraints?
- Which of those should be preserved, simplified, or removed in the remake?

### Balance Designer

- Which variables matter per progression band?
- Where does the game create abundance, scarcity, and pressure?
- What numeric bands would break the intended pacing?

### Gameplay Designer

- What actions can the player always do?
- Which actions are context-sensitive?
- What input buffering, cancel windows, or state locks shape the feel?

### Product Manager

- Is the remake for archival fidelity, commercial release, internal prototype, or design study?
- What production scale can the team actually support?
- What should be deliberately cut first if schedule slips?

### Art

- Which assets are hero assets and which are scalable modular sets?
- Which readability rules are non-negotiable?
- What visual elements are trademark-sensitive and need reinterpretation for public release?

### Animation

- Which states need unique animation and which can share a template?
- Where is animation the source of feel vs merely a presentation layer?
- Which transitions require special handling for responsiveness?

### Music/Audio

- Which interactions demand immediate audio confirmation?
- Which music layers react to combat, danger, or progression?
- Where should silence or reduced density create contrast?

### Copywriting

- What words does the game use for progression, rewards, failure, and difficulty?
- How much text does the player read in core loops?
- Which terms must stay consistent across UI, quests, and tooltips?

### Narrative

- Is the story linear, hub-based, modular, or environmental?
- Which fiction supports onboarding, progression, and boss stakes?
- Where should lore delivery be optional vs mandatory?

### Game Client Architect

- Which rules must be fully data-driven?
- Which systems are performance hot paths?
- Which authoring workflows will content teams need by milestone one?

### Lead Engineer

- What is the vertical slice that proves the game works?
- Which systems carry integration risk?
- Which automated tests or debug tools pay back immediately?
