# Research Workflow

## Contents

- `1. Lock Scope First`
- `2. Build The Source Map`
- `3. Run An Observation Pass`
- `4. Work In Role Order`
- `5. Separate Four Layers In Every Section`
- `6. Convert Research Into Replica Specs`
- `7. Handle Gaps Explicitly`
- `8. Keep The Pack Coherent`
- `9. Finish With Buildable Next Steps`

## 1. Lock Scope First

Do not begin with generic notes. Start by pinning:

- game title
- edition or era
- platform set
- region or service variant
- time slice with exact dates where relevant
- deliverable target: benchmark memo, vertical-slice spec, or full remake pack

For live-service or frequently patched games, separate:

- `historical baseline`
- `current live baseline`
- `chosen remake baseline`

If the user is vague, make the narrowest defensible assumption and state it clearly.

## 2. Build The Source Map

Gather sources in this order:

1. official site, manuals, patch notes, storefront descriptions
2. developer interviews, postmortems, event pages
3. direct gameplay footage covering onboarding, midgame, endgame, bosses, UI, menus, progression, social loops, monetization, and failure states
4. reputable community wikis, spreadsheets, datamines
5. secondary commentary only when needed to fill gaps

Useful search patterns:

- `"<game> patch notes <region>"`
- `"<game> manual pdf"`
- `site:youtube.com "<game>" boss fight`
- `site:wiki.gg "<game>" mechanics`
- `"<game>" beginner gameplay`
- `"<game>" endgame build`

Do not let one creator video define the whole game.

## 3. Run An Observation Pass

Before writing conclusions, observe the game as a player would:

- first 10 minutes
- first hour
- representative midgame
- representative endgame
- one boss or failure-heavy encounter
- one economy or inventory interaction loop
- one progression upgrade loop

For action games, inspect:

- anticipation, active, and recovery timing
- air vs ground rules
- hit confirm and cancel behavior
- enemy telegraph clarity
- camera motion and screen shake
- feedback stack: VFX, SFX, numbers, hit pause

For RPG or strategy games, inspect:

- stat reveal cadence
- build commitment timing
- resource sinks and recovery
- content gating logic
- mission or map selection grammar

## 4. Work In Role Order

Use this order unless the task is intentionally narrower:

1. product manager
2. professional game designer
3. gameplay designer
4. balance designer
5. art
6. animation
7. music/audio
8. copywriting
9. narrative
10. client architect
11. lead engineer

Reason:

- product and macro design define the target experience
- gameplay and balance define system truth
- content disciplines define presentation and production cost
- architecture and engineering turn the spec into a buildable plan

## 5. Separate Four Layers In Every Section

For each major topic, keep these distinct:

1. `Confirmed facts`
2. `Inferred model`
3. `Remake decisions`
4. `Open questions`

This prevents speculative reconstruction from masquerading as evidence.

## 6. Convert Research Into Replica Specs

Do not stop at description. Convert findings into:

- loop diagrams
- progression bands
- formulas with variables
- state lists and timelines
- asset taxonomies
- content tables
- pipeline boundaries
- milestone plans
- acceptance criteria

When the original game uses opaque server logic or hidden formulas, provide:

- best-known external behavior
- likely internal model
- proposed remake approximation
- validation method

## 7. Handle Gaps Explicitly

When evidence is missing:

- mark the gap as `Open`
- estimate the impact on remake risk: low, medium, or high
- propose the smallest validation experiment
- avoid filling the gap with genre defaults unless you label them as a proposal

Examples of validation:

- frame-count a skill cast from video
- sample multiple level bands for drop rates
- compare UI states across regions
- inspect multiple patch snapshots for system drift

## 8. Keep The Pack Coherent

Do not allow contradictions such as:

- product positioning promising accessibility while gameplay specs demand expert execution
- art readability goals conflicting with effect density
- balance pacing assuming grind volumes that production scope cannot support
- architecture promising data-driven content while documents hardcode logic into scenes

If later findings invalidate earlier sections, update the earlier sections.

## 9. Finish With Buildable Next Steps

Every complete pack should end with:

- vertical-slice scope
- full-production scope
- highest-risk unknowns
- recommended prototype order
- acceptance criteria for each milestone
