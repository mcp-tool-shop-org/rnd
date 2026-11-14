# Reading sample, side by side: local qwen3 4B (session 4 ship), Claude Haiku 5.5, Claude Opus 5.5

Standard length only. 10 turns per voice, chosen by rule, not by taste: for each category, the first unused turn in turn-set order whose outcome line was accepted by every model listed; if there is none, the first unused turn accepted by the most models. Every model was given the same turn facts, shown under the lines. A line marked "fell back" was rejected by the checker (the rule is named) and the player would have seen the game's own line instead. No reading has been added.


## R&D's reading (2026-11-13)

28 turns (the first 114 turns hold no triumphant or pyrrhic ending for the Uncanny Bearer), three models per turn, the
same facts.

**On the page the gap is large, though the good-line rates are close (ship 83.8, Haiku 77.9, Opus 80.8).** The
checker measures whether a line is allowed, not whether it is good narration.
- **Opus reads like a narrator.** It conveys the choice (19 the toll paid in food, 9 the medicine spent, 27 supplies
  surrendered), the cost of a pyrrhic ending (4 and 14, "fewer than set out"), and human detail that fits the facts
  (11 "someone straightens a collar that will not need straightening again"). Its uncanny lines are restrained and
  specific (25, 26, 28). It keeps the present tense throughout.
- **Haiku is plainer but complete:** it usually carries the fact and the choice (19, 27), in the past tense, sometimes
  wordy. It slipped into "us" once (4, rightly rejected).
- **The local 4B is terse and often a ledger** (7, 8 "Firewood spent. Food spent. Water spent."), misses choices (19
  narrates the oxen at a bridge; 27 says the party passed "with no supplies"), and drops the pyrrhic cost (14). Its
  uncanny voice is its strength (25 "Trees bent in reverse", 24).

**Two checker problems this sample exposes.**
1. **The choice-parroting rule fights the new "convey the choice" requirement.** It is the largest reject for every
   Claude model (Opus 55, Haiku 43; local 1): good lines that name what the party did are rejected for echoing the
   choice's words. Proposal: reject only a verbatim copy of the choice label, not a line that uses its verb or noun.
2. **The repeated-opening rule rejects good lines** (3 Opus, 13 Haiku: "The party reached Ravenmoor…" after a line
   that also began "The party"). Proposal: compare the first three words, not two, or exempt the lead's subject.

**Cost and time, for the Director.** Opus at this length is about $0.0068 a call, about 1.5 calls a line and 2 lines a
turn: about $0.02 a turn, about $2 for a 100-turn run; Haiku about $0.0003 a turn. Per turn p50: local 0.4 s, Haiku
4.3 s, Opus 7.3 s (cells in parallel). With the adaptive design (generate early, while the player reads and chooses),
much of that wait can be hidden.

## Chronicler

### 1. Chronicler, death (turn v2-w0-001)

- **local qwen3 4B (session 4 ship)** (attempt 1): A traveller died. Mud swells. The compass spins. No river water. No food.
- **Claude Haiku 5.5** (attempt 1): A traveller died in the swamp this afternoon, with no food left in the wagon. The compass needle spins without rest in the wet grey light at The Long Descent.
- **Claude Opus 5.5** (attempt 1): A traveller dies in the afternoon on The Long Descent, hollow from hunger and fever. The swamp water stands black and still, and the compass needle will not settle.

Turn facts:

- what happened (the lead every model was given): A traveller died.
- event_title: Spinning Compass
- event_text: The compass needle spins lazily. It refuses to settle on any heading.
- action: travel
- place: The Long Descent; biome: swamp; time_of_day: afternoon
- situation: Swamp terrain. Nearing the halfway mark. A traveller is lost. They have no food. Their doctrine: no debts. Their taboo: no river water.
- party_health_band: steady
- party_morale_band: steady
- resource_directions: distance:travelled, health:fell, morale:fell, time_days:days passed, water:spent
- health_effects: starvation, fell_sick, death, starvation, starvation, starvation
- turn_matters: death=true, injury=true, supply_zero=false, landmark_arrival=false, night_at_camp=false
- the game's own lines: Traveled 3 miles. 13 miles remaining. Thomas has fallen ill. Thomas has died (Starvation).

### 2. Chronicler, lost ending (turn v2-w0-004)

- **local qwen3 4B (session 4 ship)** (attempt 1): Storm breaks. Rain falls. Mud swells. No one moves. The last breath ends.
- **Claude Haiku 5.5** (attempt 1): The last of the party is dead and the journey ends here at the Broken Bridge in the swamp. Mud holds the wagon and the water rises slowly over the planks.
- **Claude Opus 5.5** (attempt 1): The last of the party dies in the morning storm, and the journey ends here at Broken Bridge. Rain fills the swamp around the empty wheel ruts and the split timbers hang over brown water.

Turn facts:

- what happened (the lead every model was given): The last of the party has died. The journey ends here.
- event_title: Sudden Storm
- event_text: Dark clouds mass without warning. The wind picks up sharply.
- action: travel
- place: Broken Bridge; biome: swamp; time_of_day: morning
- ending: lost
- situation: Swamp terrain. Well past halfway. None of the party is left. Their doctrine: no debts. Their taboo: no river water.
- party_health_band: dead
- party_morale_band: broken
- resource_directions: distance:travelled, firewood:spent, health:fell, time_days:days passed, water:spent
- health_effects: starvation, death
- turn_matters: death=true, injury=true, supply_zero=true, landmark_arrival=false, night_at_camp=false
- the game's own lines: Traveled 2 miles. 6 miles remaining. Patience has died (Starvation). The journey ends. Cause: Starvation.

### 3. Chronicler, triumphant ending (turn v2-w0-023)

- **local qwen3 4B (session 4 ship)** (attempt 2): The trail ends at Ravenmoor. Mud holds the wheel. Rations grow thin.
- **Claude Haiku 5.5** (attempt 3): The party reached Ravenmoor at evening, and the trail is finished. Mud clings to every wheel and the rations are nearly gone.
- **Claude Opus 5.5** fell back after 3 attempt(s) (repeated_opening); last rejected text: The wagon rolls into Ravenmoor at evening and the trail ends here, worn axles groaning in the last of the mud. Low light lies flat across the plains, and the wheels at last stand still.

Turn facts:

- what happened (the lead every model was given): The party reached Ravenmoor and the end of the trail. The journey is over.
- action: travel
- place: Ravenmoor; biome: plains; time_of_day: evening
- ending: triumphant
- situation: Plains terrain. The end of the trail is near. Rations are nearly gone. Their doctrine: travel light. Their taboo: leave nothing behind.
- party_health_band: worn
- party_morale_band: high
- resource_directions: distance:travelled, food:gained, health:fell, morale:fell, parts:spent, time_days:days passed, water:gained
- turn_matters: death=false, injury=true, supply_zero=true, landmark_arrival=true, night_at_camp=false
- the game's own lines: Arrived at Ravenmoor! Found water. +4 water. Traded at the settlement. +3 food. Wagon breakdown! Repaired. Damage: 5 You made it! Victory!

### 4. Chronicler, pyrrhic ending (turn v2-w0-025)

- **local qwen3 4B (session 4 ship)** fell back after 3 attempt(s) (supply_state_contradiction); last rejected text: Party reaches Copperhill. Some lost. No food. No water. Trail ends.
- **Claude Haiku 5.5** fell back after 3 attempt(s) (personal_pronoun); last rejected text: The party reached Copperhill at last, the trail ended and the journey is over. Some of the company did not come through the forest with us.
- **Claude Opus 5.5** (attempt 1): The party reaches Copperhill and the end of the trail, fewer than set out, and the journey is over. Afternoon light falls thin through the pines, and the hungry wagon stops in mud beside a full water cask.

Turn facts:

- what happened (the lead every model was given): The party reached Copperhill and the end of the trail, with some of its number lost on the way. The journey is over.
- action: travel
- place: Copperhill; biome: forest; time_of_day: afternoon
- ending: pyrrhic
- situation: Forest terrain. The end of the trail is near. Several of the party are lost. They have no food. Their doctrine: no debts. Their taboo: no river water.
- party_health_band: critical
- party_morale_band: low
- resource_directions: distance:travelled, health:fell, time_days:days passed, water:gained
- health_effects: starvation, starvation
- turn_matters: death=false, injury=true, supply_zero=false, landmark_arrival=true, night_at_camp=false
- the game's own lines: Arrived at Copperhill! Found water. +8 water. This is a settlement. Supplies may be available. You made it! Victory!

### 5. Chronicler, injury, no death (turn v2-w0-015)

- **local qwen3 4B (session 4 ship)** (attempt 1): The party arrives at The Scar. Rain slicks the rock. A track leads west.
- **Claude Haiku 5.5** (attempt 1): The party reached The Scar in the evening rain. Wet alpine mud sucks at the wheels and the injured walk slowly behind the wagon.
- **Claude Opus 5.5** (attempt 1): The party reaches The Scar at evening, worn and limping, with less food in the packs and fresh water drawn from a cold spring. Shutters close along the street as the wagon passes, and nobody offers credit.

Turn facts:

- what happened (the lead every model was given): The party arrived at The Scar.
- event_title: The Wary Settlement
- event_text: The town will trade, but they insist you leave before nightfall. They won't say why.
- action: travel
- place: The Scar; biome: alpine; time_of_day: evening
- situation: Alpine terrain. Nearing the halfway mark. Their doctrine: no debts. Their taboo: no river water.
- party_health_band: worn
- party_morale_band: high
- resource_directions: distance:travelled, food:spent, health:fell, time_days:days passed, water:gained
- turn_matters: death=false, injury=true, supply_zero=false, landmark_arrival=true, night_at_camp=false
- the game's own lines: Arrived at The Scar! Found water. +17 water.

### 6. Chronicler, night camp (turn v2-w0-010)

- **local qwen3 4B (session 4 ship)** (attempt 1): The party rested. Mud stains spread in the dark.
- **Claude Haiku 5.5** (attempt 1): The party rested at The Switchback through the night. Cold mud soaked the bedrolls and the fire burned low.
- **Claude Opus 5.5** (attempt 1): The party rests at The Switchback, burning firewood low and taking food and water by the wagon wheel. Wind combs the plains grass flat, and by morning the stiffness has eased from tired legs.

Turn facts:

- what happened (the lead every model was given): The party rested.
- action: rest
- place: The Switchback; biome: plains; time_of_day: night
- situation: Plains terrain. Early in the journey. Their doctrine: travel light. Their taboo: leave nothing behind.
- party_health_band: steady
- party_morale_band: high
- resource_directions: firewood:spent, food:spent, health:rose, morale:rose, time_days:days passed, water:spent
- health_effects: recovered
- turn_matters: death=false, injury=false, supply_zero=false, landmark_arrival=false, night_at_camp=true
- the game's own lines: The party rests for a day.   Clara has recovered.

### 7. Chronicler, landmark arrival (turn v2-w0-007)

- **local qwen3 4B (session 4 ship)** (attempt 1): Party arrives at Ashen Bluffs. Night wind stirs leaves. Firewood spent. Water gained.
- **Claude Haiku 5.5** (attempt 1): The party reached Ashen Bluffs at night under low cloud and steady drizzle. The forest opened onto a bare shelf of grey stone above the river.
- **Claude Opus 5.5** (attempt 1): The wagon reaches Ashen Bluffs in the dark, wheels sucking through cold mud beneath pale stone. Water is drawn from a seep, and the last kindling smokes low against an oddly quiet wood.

Turn facts:

- what happened (the lead every model was given): The party arrived at Ashen Bluffs.
- event_title: Refugee Family
- event_text: A family sits by the road. Children. They watch your food with hollow eyes.
- action: travel
- place: Ashen Bluffs; biome: forest; time_of_day: night
- situation: Forest terrain. Nearing the halfway mark. Their doctrine: travel light. Their taboo: no travel at night.
- party_health_band: steady
- party_morale_band: high
- resource_directions: distance:travelled, firewood:spent, food:spent, morale:rose, parts:spent, time_days:days passed, water:gained
- turn_matters: death=false, injury=false, supply_zero=true, landmark_arrival=true, night_at_camp=false
- the game's own lines: Arrived at Ashen Bluffs! Found water. +6 water. Dark travel mishap! Wagon damage: 8

### 8. Chronicler, supply at zero (turn v2-w0-005)

- **local qwen3 4B (session 4 ship)** (attempt 1): The party travelled on. Mud deepens. Firewood spent. Food spent. Water spent.
- **Claude Haiku 5.5** (attempt 1): The party travelled on through the night across the plains. Crow's Perch lay somewhere ahead in the dark.
- **Claude Opus 5.5** (attempt 1): The party travels on across the open plains near Crow's Perch, the wagon creaking through cold dark grass. Food, water, firewood and oil run thin, yet spirits hold strangely high.

Turn facts:

- what happened (the lead every model was given): The party travelled on.
- action: travel
- place: Crow's Perch; biome: plains; time_of_day: night
- situation: Plains terrain. Early in the journey. Their doctrine: travel light. Their taboo: no travel at night.
- party_health_band: steady
- party_morale_band: high
- resource_directions: distance:travelled, firewood:spent, food:spent, morale:rose, oil:spent, time_days:days passed, water:spent
- turn_matters: death=false, injury=false, supply_zero=true, landmark_arrival=false, night_at_camp=false
- the game's own lines: Traveled 5 miles. 9 miles remaining.

### 9. Chronicler, choice resolved (turn v2-w0-009)

- **local qwen3 4B (session 4 ship)** (attempt 3): Medicine used. Camp stirs. Wind shifts. No sound from the west.
- **Claude Haiku 5.5** (attempt 1): The party used all the medicine at night in the forest at The Long Descent. Morale fell as the days wore on.
- **Claude Opus 5.5** (attempt 2): The camp spends the medicine down to the last of it, and the sick lie quiet beneath dripping pines on the long descent. Spirits sag as the days pass slowly in the wet forest dark.

Turn facts:

- what happened (the lead every model was given): The party chose: Use all available medicine.
- event_title: Illness Sweeps the Camp
- event_text: Half the party is down. The symptoms are unmistakable.
- choice_taken: Use all available medicine.
- place: The Long Descent; biome: forest; time_of_day: night
- situation: Forest terrain. Well past halfway. Their doctrine: travel light. Their taboo: no travel at night.
- party_health_band: steady
- party_morale_band: high
- resource_directions: morale:fell, time_days:days passed
- turn_matters: death=false, injury=false, supply_zero=true, landmark_arrival=false, night_at_camp=false
- the game's own lines: -2 meds, morale -3, 1 time lost

### 10. Chronicler, ordinary travel (turn v2-w0-024)

- **local qwen3 4B (session 4 ship)** (attempt 1): The party travels on. Mud deepens. A leg moves in the track.
- **Claude Haiku 5.5** (attempt 1): The party travelled on through the evening mud at Widow's Pass. Spirits held despite the lame animal, and the plains stretched grey and wide ahead.
- **Claude Opus 5.5** (attempt 1): The party travels on toward Widow's Pass, chewing dry food and rationing water while the wheels grind through evening mud. A draught animal favors one foreleg, yet spirits hold, and someone hums low against the wind off the plains.

Turn facts:

- what happened (the lead every model was given): The party travelled on.
- event_title: Lame Animal
- event_text: One of the draft animals is favoring its left foreleg badly.
- action: travel
- place: Widow's Pass; biome: plains; time_of_day: evening
- situation: Plains terrain. Early in the journey. Their doctrine: no debts. Their taboo: no river water.
- party_health_band: worn
- party_morale_band: high
- resource_directions: distance:travelled, food:spent, morale:rose, time_days:days passed, water:spent
- turn_matters: death=false, injury=false, supply_zero=false, landmark_arrival=false, night_at_camp=false
- the game's own lines: Traveled 5 miles. 15 miles remaining.


## Fireside

### 11. Fireside, death (turn v2-w0-002)

- **local qwen3 4B (session 4 ship)** (attempt 1): A traveller died. The Long Descent hums low in the swamp.
- **Claude Haiku 5.5** (attempt 2): A traveller has died in the swamp at The Long Descent this evening, and the rest of the party carries the loss in their shoulders. Mud sucks at the wheels and the oxen lean into the harness while the hungry family says little.
- **Claude Opus 5.5** (attempt 1): A traveller dies at evening on the road through The Long Descent, worn thin by hunger, and the party stands close around the wagon. Swamp water rises black along the ruts while someone straightens a collar that will not need straightening again.

Turn facts:

- what happened (the lead every model was given): A traveller died.
- event_title: Hungry Family
- event_text: Small hands reach out beside the rutted path.
- action: travel
- place: The Long Descent; biome: swamp; time_of_day: evening
- situation: Swamp terrain. Well past halfway. Several of the party are lost. They have no food. Their doctrine: no debts. Their taboo: no river water.
- party_health_band: worn
- party_morale_band: low
- resource_directions: distance:travelled, health:fell, time_days:days passed, water:spent
- health_effects: starvation, death, starvation, starvation
- turn_matters: death=true, injury=true, supply_zero=false, landmark_arrival=false, night_at_camp=false
- the game's own lines: Traveled 3 miles. 5 miles remaining. Amos has died (Starvation).

### 12. Fireside, lost ending (turn v2-w0-047)

- **local qwen3 4B (session 4 ship)** (attempt 1): The last of the party has died. Fog Hollow holds no light now.
- **Claude Haiku 5.5** (attempt 1): The last of the party has died and the trail ends here in Fog Hollow as evening settles over the swamp. Black water stands between the reeds and the oxen stand still in the mud, their breath rising in the damp air.
- **Claude Opus 5.5** (attempt 2): The last of the party is dead, and the journey ends here in Fog Hollow. Evening settles over the swamp, and the wheels sink quietly into the mud where no one walks beside the oxen.

Turn facts:

- what happened (the lead every model was given): The last of the party has died. The journey ends here.
- action: travel
- place: Fog Hollow; biome: swamp; time_of_day: evening
- ending: lost
- situation: Swamp terrain. Nearing the halfway mark. None of the party is left. Their doctrine: no debts. Their taboo: no river water.
- party_health_band: dead
- party_morale_band: broken
- resource_directions: distance:travelled, health:fell, morale:fell, time_days:days passed, water:spent
- health_effects: starvation, death
- turn_matters: death=true, injury=true, supply_zero=false, landmark_arrival=false, night_at_camp=false
- the game's own lines: Traveled 4 miles. 16 miles remaining. Thomas has died (Starvation). The journey ends. Cause: Starvation.

### 13. Fireside, triumphant ending (turn v2-w1-020)

- **local qwen3 4B (session 4 ship)** fell back after 3 attempt(s) (ending_not_conveyed); last rejected text: The party stands at the edge of Ravenmoor where the plain ends and the sky turns deep. The oxen breathe slow in the wind.
- **Claude Haiku 5.5** fell back after 3 attempt(s) (repeated_opening); last rejected text: The party reached Ravenmoor at evening, and the long trail is finally over. Oxen stand steaming in the last light, and the travellers lower their shoulders at last.
- **Claude Opus 5.5** (attempt 2): The party rolls into Ravenmoor at evening, and the long trail ends beneath a low sky. The travellers ease down from the wagon slowly, sore and smiling, while the oxen lower their heads to the cool plains grass.

Turn facts:

- what happened (the lead every model was given): The party reached Ravenmoor and the end of the trail. The journey is over.
- action: travel
- place: Ravenmoor; biome: plains; time_of_day: evening
- ending: triumphant
- situation: Plains terrain. The end of the trail is near. Rations are nearly gone. Their doctrine: travel light. Their taboo: leave nothing behind.
- party_health_band: worn
- party_morale_band: high
- resource_directions: distance:travelled, food:gained, health:fell, morale:fell, parts:spent, time_days:days passed, water:gained
- turn_matters: death=false, injury=true, supply_zero=true, landmark_arrival=true, night_at_camp=false
- the game's own lines: Arrived at Ravenmoor! Found water. +4 water. Traded at the settlement. +3 food. Wagon breakdown! Repaired. Damage: 5 You made it! Victory!

### 14. Fireside, pyrrhic ending (turn v2-w1-022)

- **local qwen3 4B (session 4 ship)** (attempt 3): The party reached Copperhill. The trail ends here. They have no food.
- **Claude Haiku 5.5** (attempt 1): The party reached Copperhill at the end of the trail, though some of its number were lost along the way and the journey is over.
- **Claude Opus 5.5** (attempt 1): The party reaches Copperhill in the afternoon, fewer than they set out, and the trail ends here among the dark pines. The travellers stand with hollow cheeks and bowed shoulders, and no one speaks of those left behind.

Turn facts:

- what happened (the lead every model was given): The party reached Copperhill and the end of the trail, with some of its number lost on the way. The journey is over.
- action: travel
- place: Copperhill; biome: forest; time_of_day: afternoon
- ending: pyrrhic
- situation: Forest terrain. The end of the trail is near. Several of the party are lost. They have no food. Their doctrine: no debts. Their taboo: no river water.
- party_health_band: critical
- party_morale_band: low
- resource_directions: distance:travelled, health:fell, time_days:days passed, water:gained
- health_effects: starvation, starvation
- turn_matters: death=false, injury=true, supply_zero=false, landmark_arrival=true, night_at_camp=false
- the game's own lines: Arrived at Copperhill! Found water. +8 water. This is a settlement. Supplies may be available. You made it! Victory!

### 15. Fireside, injury, no death (turn v2-w0-017)

- **local qwen3 4B (session 4 ship)** (attempt 2): The oxen step through the thin snow, shoulders hunched, breath fogging the air. The river lies ahead, silent and unclaimed.
- **Claude Haiku 5.5** (attempt 1): The party travelled on through the cold alpine dark, wheels grinding in the mud while the oxen leaned into their harness.
- **Claude Opus 5.5** (attempt 1): The party travels on through The Scar, the oxen leaning hard into the cold dark while the travellers share their food and water, smiling through new hurts.

Turn facts:

- what happened (the lead every model was given): The party travelled on.
- action: travel
- place: The Scar; biome: alpine; time_of_day: night
- situation: Alpine terrain. Nearing the halfway mark. Their doctrine: no debts. Their taboo: no river water.
- party_health_band: worn
- party_morale_band: high
- resource_directions: distance:travelled, food:spent, health:fell, morale:rose, time_days:days passed, water:spent
- turn_matters: death=false, injury=true, supply_zero=false, landmark_arrival=false, night_at_camp=false
- the game's own lines: Traveled 5 miles. 5 miles remaining.

### 16. Fireside, night camp (turn v2-w0-011)

- **local qwen3 4B (session 4 ship)** (attempt 1): The party hunted and brought back food. The Switchback holds a stillness that lingers in the wind.
- **Claude Haiku 5.5** (attempt 1): The hunt brought back meat tonight, and the spent cartridge still smells sharp in the cold air at The Switchback. The oxen stand close to the fire, and the party eats quietly, no one saying what they are all thinking about the river.
- **Claude Opus 5.5** (attempt 1): The party comes back from the hunt with food slung low and less ammunition in their pouches, shoulders loose and easy in the firelight.

Turn facts:

- what happened (the lead every model was given): The party hunted and brought back food.
- action: hunt
- place: The Switchback; biome: plains; time_of_day: night
- situation: Plains terrain. Early in the journey. Their doctrine: travel light. Their taboo: leave nothing behind.
- party_health_band: steady
- party_morale_band: high
- resource_directions: ammo:spent, food:gained
- turn_matters: death=false, injury=false, supply_zero=false, landmark_arrival=false, night_at_camp=true
- the game's own lines: Hunt successful! +13 food. -1 ammo.

### 17. Fireside, landmark arrival (turn v2-w0-020)

- **local qwen3 4B (session 4 ship)** (attempt 2): The party settles at Hazelwick where the wind hums through cracked stone. A single well stands half-buried in dust.
- **Claude Haiku 5.5** (attempt 1): The party reached Hazelwick in the morning, oxen steaming in the cool desert air. Their shoulders eased at the sight of the river-fed settlement, though the townsfolk watch them carefully.
- **Claude Opus 5.5** (attempt 1): The party rolls into Hazelwick under a pale morning sun, the oxen lowering their heads as the wheels grind through dry dust.

Turn facts:

- what happened (the lead every model was given): The party arrived at Hazelwick.
- event_title: The Wary Settlement
- event_text: The town will trade, but they insist you leave before nightfall. They won't say why.
- action: travel
- place: Hazelwick; biome: desert; time_of_day: morning
- situation: Desert terrain. Well past halfway. Their doctrine: travel light. Their taboo: leave nothing behind.
- party_health_band: worn
- party_morale_band: high
- resource_directions: distance:travelled, food:spent, morale:rose, time_days:days passed, water:spent
- turn_matters: death=false, injury=false, supply_zero=false, landmark_arrival=true, night_at_camp=false
- the game's own lines: Arrived at Hazelwick! This is a settlement. Supplies may be available.

### 18. Fireside, supply at zero (turn v2-w0-048)

- **local qwen3 4B (session 4 ship)** (attempt 1): The oxen move forward through the dry grass. Morning light stretches over the plain.
- **Claude Haiku 5.5** (attempt 1): The party travelled on through the morning, and the wagon wheels sank deep into the grey plains mud. Crow's Perch sits low on the grass, and the oxen leaned into the traces without complaint.
- **Claude Opus 5.5** (attempt 1): The party travels on through the morning grass toward Crow's Perch, the oxen leaning steady into their yokes. Spirits lift among the travellers as they spend the last of the lamp oil, and someone hums an old river tune.

Turn facts:

- what happened (the lead every model was given): The party travelled on.
- action: travel
- place: Crow's Perch; biome: plains; time_of_day: morning
- situation: Plains terrain. Early in the journey. Their doctrine: travel light. Their taboo: no travel at night.
- party_health_band: steady
- party_morale_band: high
- resource_directions: distance:travelled, firewood:spent, food:spent, morale:rose, oil:spent, time_days:days passed, water:spent
- turn_matters: death=false, injury=false, supply_zero=true, landmark_arrival=false, night_at_camp=false
- the game's own lines: Traveled 5 miles. 3 miles remaining.

### 19. Fireside, choice resolved (turn v2-w0-034)

- **local qwen3 4B (session 4 ship)** (attempt 1): The oxen pause by the bridge. Mud clings to their hooves. A shadow stretches long in the dusk.
- **Claude Haiku 5.5** (attempt 1): The party paid the toll at Moss Landing and handed over the food without complaint as evening settled over the plains. The ferryman counted the sacks slowly, and the oxen stood patient in the damp grass while the travellers watched the river slide past.
- **Claude Opus 5.5** (attempt 3): The party hands over food at the toll bridge, and the keeper weighs each sack in his palm before lifting the rail.

Turn facts:

- what happened (the lead every model was given): The party chose: Pay the toll (5 food).
- event_title: Toll Bridge
- event_text: A man sits at the near end of a narrow bridge. He does not move aside.
- choice_taken: Pay the toll (5 food).
- place: Moss Landing; biome: plains; time_of_day: evening
- situation: Plains terrain. Early in the journey. Their doctrine: travel light. Their taboo: no travel at night.
- party_health_band: steady
- party_morale_band: high
- resource_directions: food:spent
- turn_matters: death=false, injury=false, supply_zero=false, landmark_arrival=false, night_at_camp=false
- the game's own lines: -5 food

### 20. Fireside, ordinary travel (turn v2-w0-018)

- **local qwen3 4B (session 4 ship)** (attempt 1): The party rested in the thin air of The Scar. Snow melted in the morning light, seeping into the stone beneath their feet.
- **Claude Haiku 5.5** (attempt 1): The party rested through the morning at The Scar while the oxen stood steaming in the thin alpine air. Food and water were drawn down, and by midday shoulders had loosened and a little colour returned to tired faces.
- **Claude Opus 5.5** (attempt 1): The party rests at The Scar this morning, sharing out food and water slowly while sore limbs loosen by the low fire. Cold alpine wind combs the rock above them, and the travellers sit a little straighter as the ache eases.

Turn facts:

- what happened (the lead every model was given): The party rested.
- action: rest
- place: The Scar; biome: alpine; time_of_day: morning
- situation: Alpine terrain. Nearing the halfway mark. Their doctrine: no debts. Their taboo: no river water.
- party_health_band: worn
- party_morale_band: high
- resource_directions: food:spent, health:rose, morale:rose, time_days:days passed, water:spent
- turn_matters: death=false, injury=false, supply_zero=false, landmark_arrival=false, night_at_camp=false
- the game's own lines: The party rests for a day.


## Uncanny Bearer

### 21. Uncanny Bearer, death (turn v2-w0-003)

- **local qwen3 4B (session 4 ship)** (attempt 1): A traveller died. The bridge shivers. The water holds no echo.
- **Claude Haiku 5.5** (attempt 1): A traveller has died on the swamp track at Broken Bridge, and the mud takes the sound of it without a ripple. The night holds the fire low and the crossing waits in black water.
- **Claude Opus 5.5** (attempt 1): A traveller dies in the night at Broken Bridge, thin from starvation, and the wheels sit still in the black swamp mud. The cold ash of the fire keeps its shape, and the water spent beside it ripples a moment before the wind arrives.

Turn facts:

- what happened (the lead every model was given): A traveller died.
- event_title: Fire Gone Out
- event_text: The fire has died. The cold presses in. No firewood remains.
- action: travel
- place: Broken Bridge; biome: swamp; time_of_day: night
- situation: Swamp terrain. Well past halfway. A lone traveller remains. They have no food. Their doctrine: no debts. Their taboo: no river water.
- party_health_band: worn
- party_morale_band: low
- resource_directions: distance:travelled, health:fell, time_days:days passed, water:spent
- health_effects: starvation, starvation, death
- turn_matters: death=true, injury=true, supply_zero=false, landmark_arrival=false, night_at_camp=false
- the game's own lines: Traveled 3 miles. 7 miles remaining. Nathaniel has died (Starvation).

### 22. Uncanny Bearer, lost ending (turn v2-w0-075)

- **local qwen3 4B (session 4 ship)** (attempt 1): The last of the party has died. Sunken Meadow holds no echo of movement.
- **Claude Haiku 5.5** (attempt 1): The last of the party has died in the wet grass of Sunken Meadow, and the journey ends here. The plain stretches away under low grey cloud, and the mud keeps its own counsel.
- **Claude Opus 5.5** (attempt 1): The last of the party has died, and the journey ends here in the Sunken Meadow. The grass stands level all around the wagon, and the wind moves through it a moment before it arrives.

Turn facts:

- what happened (the lead every model was given): The last of the party has died. The journey ends here.
- event_title: Fresh Bear Sign
- event_text: The prints are wide and deep in the soft earth.
- action: travel
- place: Sunken Meadow; biome: plains; time_of_day: afternoon
- ending: lost
- situation: Plains terrain. Early in the journey. None of the party is left. Their doctrine: no debts. Their taboo: no river water.
- party_health_band: dead
- party_morale_band: broken
- resource_directions: distance:travelled, health:fell, time_days:days passed, water:spent
- health_effects: starvation, death, starvation, death, starvation, death
- turn_matters: death=true, injury=true, supply_zero=false, landmark_arrival=false, night_at_camp=false
- the game's own lines: Traveled 4 miles. 5 miles remaining. Thomas has died (Starvation). Amos has died (Starvation). Nathaniel has died (Starvation). The journey ends. Cause: Starvation.

### (no turn found for triumphant ending)

### (no turn found for pyrrhic ending)

### 23. Uncanny Bearer, injury, no death (turn v2-w0-051)

- **local qwen3 4B (session 4 ship)** (attempt 1): The party travelled on. The path curved into a valley that did not exist in the map.
- **Claude Haiku 5.5** (attempt 1): The party travelled on through the wet forest as evening settled over Shepherd's Rest, the mud sucking at every step. Their stores are empty and their bodies feel the hunger, slowing each stride as the trail bends toward the river.
- **Claude Opus 5.5** (attempt 1): The party travels on beneath the evening pines toward Shepherd's Rest, the last of the food and water spent, hunger pulling at every step.

Turn facts:

- what happened (the lead every model was given): The party travelled on.
- action: travel
- place: Shepherd's Rest; biome: forest; time_of_day: evening
- situation: Forest terrain. Nearing the halfway mark. They have no food. Their doctrine: travel light. Their taboo: no travel at night.
- party_health_band: steady
- party_morale_band: high
- resource_directions: distance:travelled, food:spent, health:fell, morale:fell, parts:spent, time_days:days passed, water:spent
- health_effects: starvation, starvation, starvation, starvation
- turn_matters: death=false, injury=true, supply_zero=true, landmark_arrival=false, night_at_camp=false
- the game's own lines: Traveled 5 miles. 6 miles remaining. Dark travel mishap! Wagon damage: 5

### 24. Uncanny Bearer, night camp (turn v2-w0-012)

- **local qwen3 4B (session 4 ship)** (attempt 1): The party rested. The air hums with a geometry that does not close.
- **Claude Haiku 5.5** (attempt 1): The party rested through the night at Crow's Perch while the swamp breathed slow and wet around them. Food and water were drawn down, and by morning the sick ones looked a little less grey.
- **Claude Opus 5.5** (attempt 1): The party rests at Crow's Perch through the night, eating and drinking from their stores while the sick slowly mend. Swamp water laps the wheels with a sound that seems to finish just before it begins.

Turn facts:

- what happened (the lead every model was given): The party rested.
- action: rest
- place: Crow's Perch; biome: swamp; time_of_day: night
- situation: Swamp terrain. Nearing the halfway mark. Multiple members are sick or injured. Their doctrine: travel light. Their taboo: leave nothing behind.
- party_health_band: worn
- party_morale_band: high
- resource_directions: food:spent, health:rose, time_days:days passed, water:spent
- turn_matters: death=false, injury=false, supply_zero=false, landmark_arrival=false, night_at_camp=true
- the game's own lines: The party rests for a day.

### 25. Uncanny Bearer, landmark arrival (turn v2-w0-027)

- **local qwen3 4B (session 4 ship)** (attempt 1): The party entered Fellgate. Trees bent in reverse, their trunks curving upward into the sky.
- **Claude Haiku 5.5** (attempt 1): The party arrived at Fellgate as the night wind gusted hard from the north. Mud clung to the wheels and the forest pressed close on every side.
- **Claude Opus 5.5** (attempt 1): The party arrives at Fellgate, the wagon creaking under the north wind, with less food in the sacks and fresh water sloshing in the casks. Beneath the pines the gate's shadow leans the wrong way, toward the wind instead of from the moon.

Turn facts:

- what happened (the lead every model was given): The party arrived at Fellgate.
- event_title: Gusting North Wind
- event_text: The wind carries the scent of snow yet to fall.
- action: travel
- place: Fellgate; biome: forest; time_of_day: night
- situation: Forest terrain. Well past halfway. The wagon may not survive another hit. Their doctrine: travel light. Their taboo: no travel at night.
- party_health_band: steady
- party_morale_band: high
- resource_directions: distance:travelled, food:spent, time_days:days passed, water:gained
- turn_matters: death=false, injury=false, supply_zero=false, landmark_arrival=true, night_at_camp=false
- the game's own lines: Arrived at Fellgate! Found water. +20 water. This is a settlement. Supplies may be available.

### 26. Uncanny Bearer, supply at zero (turn v2-w0-050)

- **local qwen3 4B (session 4 ship)** (attempt 1): The party travelled on. The path curved where trees did not belong.
- **Claude Haiku 5.5** (attempt 1): The party travelled on through the forest at Fog Hollow as the morning mist thinned along the muddy track. Food and water ran low, and the fog kept pace beside them, pressing close without ever quite arriving.
- **Claude Opus 5.5** (attempt 2): The party travels on through Fog Hollow, wheels sinking in morning mud while the last of the food, water, and firewood goes. Mist hangs between the trunks at a height that does not match the ground beneath it.

Turn facts:

- what happened (the lead every model was given): The party travelled on.
- action: travel
- place: Fog Hollow; biome: forest; time_of_day: morning
- situation: Forest terrain. Nearing the halfway mark. Their doctrine: travel light. Their taboo: no travel at night.
- party_health_band: steady
- party_morale_band: high
- resource_directions: distance:travelled, firewood:spent, food:spent, time_days:days passed, water:spent
- turn_matters: death=false, injury=false, supply_zero=true, landmark_arrival=false, night_at_camp=false
- the game's own lines: Traveled 5 miles. 3 miles remaining.

### 27. Uncanny Bearer, choice resolved (turn v2-w0-033)

- **local qwen3 4B (session 4 ship)** (attempt 1): The party passed Widow's Pass with no supplies. The forest breathed in reverse.
- **Claude Haiku 5.5** (attempt 1): The party hands over their supplies and the bandits melt back into the forest at Widow's Pass.
- **Claude Opus 5.5** (attempt 1): The party hands over ammunition, food, and water to the men blocking the road, and the wagon rolls on through Widow's Pass with spirits sinking. Morning light slants between the pines at an angle that seems borrowed from evening.

Turn facts:

- what happened (the lead every model was given): The party chose: Surrender supplies to pass.
- event_title: Bandits on the Road
- event_text: Armed figures step onto the trail ahead. They are not smiling.
- choice_taken: Surrender supplies to pass.
- place: Widow's Pass; biome: forest; time_of_day: morning
- situation: Forest terrain. The end of the trail is near. Their doctrine: travel light. Their taboo: leave nothing behind.
- party_health_band: worn
- party_morale_band: high
- resource_directions: ammo:spent, food:spent, morale:fell, water:spent
- turn_matters: death=false, injury=false, supply_zero=false, landmark_arrival=false, night_at_camp=false
- the game's own lines: -10 food, -5 water, -5 ammo, morale -8

### 28. Uncanny Bearer, ordinary travel (turn v2-w0-022)

- **local qwen3 4B (session 4 ship)** (attempt 1): The party travelled on. The sun dipped low, bending light into slivers that did not meet the ground.
- **Claude Haiku 5.5** (attempt 1): The party travelled on through the desert afternoon, the wheels sinking and lifting in the pale sand. Hazelwick lies somewhere ahead, its roofs flickering in the heat like a reflection that arrived before the thing it reflects.
- **Claude Opus 5.5** (attempt 1): The party travels on through the dry afternoon, wheels grinding sand, food and water spent while spirits lift. Near Hazelwick the dunes lean slightly downhill in every direction at once.

Turn facts:

- what happened (the lead every model was given): The party travelled on.
- action: travel
- place: Hazelwick; biome: desert; time_of_day: afternoon
- situation: Desert terrain. Well past halfway. Their doctrine: travel light. Their taboo: leave nothing behind.
- party_health_band: worn
- party_morale_band: high
- resource_directions: distance:travelled, food:spent, morale:rose, time_days:days passed, water:spent
- turn_matters: death=false, injury=false, supply_zero=false, landmark_arrival=false, night_at_camp=false
- the game's own lines: Traveled 5 miles. 13 miles remaining.

