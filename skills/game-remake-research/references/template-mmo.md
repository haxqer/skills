# MMO Template

Use this template when the game's long-term value depends on persistent progression, social dependency, shared economy, and live content cadence.

Read `metrics-mmo.md` when you need measurable baselines for cadence, social gating, and economy durability.

## What Makes The Research Different

- Treat social structure as system truth, not decoration.
- Treat economy durability as a first-class design problem.
- Distinguish solo viability from solo sufficiency.
- Capture why players return after onboarding and after cap.

## Focus By Role

### Product Manager

- Define the audience split between solo, social, competitive, and aspirational players.
- Capture retention spine: daily, weekly, seasonal, expansion, and prestige loops.
- State which live-service burdens should be preserved, simplified, or removed in the remake.

### Professional Game Designer

- Map the macro loop from onboarding to endgame.
- Identify social gates: party size, role dependency, guild requirement, raid schedule, market reliance.
- Separate fantasy pillars from historical friction that only existed to support concurrency.

### Balance Designer

- Document currency creation and removal, inflation controls, and trade restrictions.
- Track progression gates by level, gear, social access, and time cadence.
- Measure how group play changes efficiency, survival, and drop or reward expectations.

### Gameplay Designer

- Capture class or role interdependence, encounter role demands, aggro or support mechanics, and large-group readability.
- Document open-world versus instance behavior changes.

### Art / Animation / Audio

- Capture readability under crowded scenes, effect density, and role signaling.
- Identify assets and telegraphs that exist mainly because multiple players need to parse the battlefield at once.

### Client Architect / Lead Engineer

- Separate client-visible behavior from server-authoritative assumptions.
- Document persistence model, session topology, shard or channel structure, and performance cliffs in crowded content.

## Must Capture

- World topology: hubs, channels, shards, matchmaking, instancing.
- Social dependency graph: solo, party, guild, raid, trade, market.
- Economy durability: sinks, inflation, drop injection, bottlenecks, restrictions.
- Endgame ladder: dungeon, raid, world boss, prestige, seasonal loop.
- Content cadence: event cadence, reset cadence, expansion cadence.

## Additional Deliverables

- Social dependency map.
- Currency and sink matrix.
- Endgame ladder chart.
- Role ecology matrix.
- Live-cadence calendar.

## Common Remake Traps

- Copying grind volume without the missing social cushion.
- Removing trade or group dependency without rebuilding the reward economy.
- Treating live cadence as mere content quantity instead of a pacing system.
- Under-specifying how persistence, matchmaking, and instancing affect architecture.
