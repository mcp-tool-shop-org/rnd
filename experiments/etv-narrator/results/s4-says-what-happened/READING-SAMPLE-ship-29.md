# Reading sample: session 4 ship arm (rulings prompt, candidates, trim, model-card sampling, says-what-happened rules, outcome lead, no repeated opening, no event copy, Brief by stop)

30 slots, 10 per voice. Chosen by rule, not by taste: for each category, the first unused turn in turn-set order whose outcome line was accepted; lengths rotate. The outcome line is shown with the turn facts the model was given and the game's own lines. No reading has been added.


## R&D's reading (2026-11-13), against the s3 combo sample

29 lines (no accepted Uncanny Bearer Rich line exists for either pyrrhic turn).

**What got fixed (it shows on the page).**
- Every ending, death and arrival line now says so: lost endings (2, 12, 22), deaths (1, 11, 21), arrivals (5, 7, 17, 26),
  the hunt (16). The s3 sample had victories that read as weather and a hunt that read "Oxen pause by a river bend".
- No false supply claims. The s3 sample had "No water" on a turn that gained water; none here.
- No outcome line copies the event text.

**What is still wrong or weak.**
1. **Brief lines are often just the lead, restated.** 1 "A traveller died.", 4, 7, 10, 13, 16, 22, 24, 27; and 23
   (Standard) copies the lead word for word. True, but it is our sentence, not narration. 10 of 29.
2. **The pyrrhic ending loses its cost.** 4 "The party reached Copperhill." and 14 say nothing of the dead. The lead
   says "with some of its number lost on the way"; the model drops it, and no rule requires it.
3. **Choices are still not conveyed.** 9 (repair) narrates the break, not the repair; 19 (trade quickly) and 28 (give
   food) don't mention the choice; 18 has the medicine "poured into the fire", an invention. There is no rule for
   choice turns.
4. **The scene slot is untouched by the new rules.** "Mud swells under tires." appears on two turns (1, 4): an
   anachronism, and the same line twice. Most scene lines still open with mud, whatever the biome.
5. Ledger-speak survives in places: 8 "Firewood spent. Food spent. Water spent."

**Reads well and true:** 2, 3, 5, 6, 11, 12, 15, 17, 20, 21, 25, 26, 29, and more plainly 1, 13, 22. About 18 of 29
read well against their facts; s3's combo sample had about 5 of 29.

**What I would change next (prompt and checker only).**
- Pyrrhic: a loss word required on pyrrhic endings (as death words are on death turns).
- Choice turns: the outcome line must reflect the choice taken (its verb or its result), with the lead built from the
  choice's result rather than its label.
- Scene slot: apply the no-repeat-opening and no-event-copy rules there too, and add an anachronism list (tires,
  engine, car, phone, ...).
- Copying the lead: allowed at Brief, but at Standard and Rich the line must add something beyond the lead (measure
  first: the share of outcome lines that equal the lead).

## Chronicler

### 1. Chronicler, brief, death (turn v2-w0-001, attempt 1)

> A traveller died.

- what happened (the lead the model was given): A traveller died.
- event_title: Spinning Compass
- event_text (given to the scene call only): The compass needle spins lazily. It refuses to settle on any heading.
- action: travel
- place: The Long Descent
- biome: swamp
- time_of_day: afternoon
- situation: Swamp terrain. Nearing the halfway mark. A traveller is lost. They have no food. Their doctrine: no debts. Their taboo: no river water.
- party_health_band: steady
- party_morale_band: steady
- resource_directions: distance:travelled, health:fell, morale:fell, time_days:days passed, water:spent
- health_effects: starvation, fell_sick, death, starvation, starvation, starvation
- turn_matters: death=true, injury=true, supply_zero=false, landmark_arrival=false, night_at_camp=false
- the game's own lines: Traveled 3 miles. 13 miles remaining. Thomas has fallen ill. Thomas has died (Starvation).
- scene line this turn (accepted): Mud swells under tires.

### 2. Chronicler, standard, lost ending (turn v2-w0-004, attempt 1)

> Storm breaks. Rain falls. Mud swells. No one moves. The last breath ends.

- what happened (the lead the model was given): The last of the party has died. The journey ends here.
- event_title: Sudden Storm
- event_text (given to the scene call only): Dark clouds mass without warning. The wind picks up sharply.
- action: travel
- place: Broken Bridge
- biome: swamp
- time_of_day: morning
- ending: lost
- situation: Swamp terrain. Well past halfway. None of the party is left. Their doctrine: no debts. Their taboo: no river water.
- party_health_band: dead
- party_morale_band: broken
- resource_directions: distance:travelled, firewood:spent, health:fell, time_days:days passed, water:spent
- health_effects: starvation, death
- turn_matters: death=true, injury=true, supply_zero=true, landmark_arrival=false, night_at_camp=false
- the game's own lines: Traveled 2 miles. 6 miles remaining. Patience has died (Starvation). The journey ends. Cause: Starvation.
- scene line this turn (accepted): Clouds crush the sky. Wind slaps the bridge. Mud swirls. No one moves. Water rises.

### 3. Chronicler, rich, triumphant ending (turn v2-w0-023, attempt 2)

> The party reaches Ravenmoor. The trail ends. The ground is soft, wet, and holds no trace of footprints.

- what happened (the lead the model was given): The party reached Ravenmoor and the end of the trail. The journey is over.
- action: travel
- place: Ravenmoor
- biome: plains
- time_of_day: evening
- ending: triumphant
- situation: Plains terrain. The end of the trail is near. Rations are nearly gone. Their doctrine: travel light. Their taboo: leave nothing behind.
- party_health_band: worn
- party_morale_band: high
- resource_directions: distance:travelled, food:gained, health:fell, morale:fell, parts:spent, time_days:days passed, water:gained
- turn_matters: death=false, injury=true, supply_zero=true, landmark_arrival=true, night_at_camp=false
- the game's own lines: Arrived at Ravenmoor! Found water. +4 water. Traded at the settlement. +3 food. Wagon breakdown! Repaired. Damage: 5 You made it! Victory!
- scene line this turn (accepted): Mud deepens in the west. Wind shifts, carrying dust and the smell of wet earth. A track follows the ridge, unbroken, leading into the low land.

### 4. Chronicler, brief, pyrrhic ending (turn v2-w0-025, attempt 1)

> The party reached Copperhill.

- what happened (the lead the model was given): The party reached Copperhill and the end of the trail, with some of its number lost on the way. The journey is over.
- action: travel
- place: Copperhill
- biome: forest
- time_of_day: afternoon
- ending: pyrrhic
- situation: Forest terrain. The end of the trail is near. Several of the party are lost. They have no food. Their doctrine: no debts. Their taboo: no river water.
- party_health_band: critical
- party_morale_band: low
- resource_directions: distance:travelled, health:fell, time_days:days passed, water:gained
- health_effects: starvation, starvation
- turn_matters: death=false, injury=true, supply_zero=false, landmark_arrival=true, night_at_camp=false
- the game's own lines: Arrived at Copperhill! Found water. +8 water. This is a settlement. Supplies may be available. You made it! Victory!
- scene line this turn (accepted): Mud swells under tires.

### 5. Chronicler, standard, injury, no death (turn v2-w0-015, attempt 1)

> The party arrives at The Scar. Rain slicks the rock. A track leads west.

- what happened (the lead the model was given): The party arrived at The Scar.
- event_title: The Wary Settlement
- event_text (given to the scene call only): The town will trade, but they insist you leave before nightfall. They won't say why.
- action: travel
- place: The Scar
- biome: alpine
- time_of_day: evening
- situation: Alpine terrain. Nearing the halfway mark. Their doctrine: no debts. Their taboo: no river water.
- party_health_band: worn
- party_morale_band: high
- resource_directions: distance:travelled, food:spent, health:fell, time_days:days passed, water:gained
- turn_matters: death=false, injury=true, supply_zero=false, landmark_arrival=true, night_at_camp=false
- the game's own lines: Arrived at The Scar! Found water. +17 water.
- scene line this turn (accepted): Mud thickens. Wind cuts. The trail bends west. A track splits, dry and wrong.

### 6. Chronicler, rich, night camp (turn v2-w0-010, attempt 3)

> The party rested. Mud stains spread under the wagon. A track followed the slope, not of foot, but of something else.

- what happened (the lead the model was given): The party rested.
- action: rest
- place: The Switchback
- biome: plains
- time_of_day: night
- situation: Plains terrain. Early in the journey. Their doctrine: travel light. Their taboo: leave nothing behind.
- party_health_band: steady
- party_morale_band: high
- resource_directions: firewood:spent, food:spent, health:rose, morale:rose, time_days:days passed, water:spent
- health_effects: recovered
- turn_matters: death=false, injury=false, supply_zero=false, landmark_arrival=false, night_at_camp=true
- the game's own lines: The party rests for a day.   Clara has recovered.
- scene line this turn (accepted): Mud swells under the wheel. The river lies far below, dark and still. A track cuts through the mud, not from any known path. No wind stirs the grass.

### 7. Chronicler, brief, landmark arrival (turn v2-w0-007, attempt 1)

> Party arrives at Ashen Bluffs.

- what happened (the lead the model was given): The party arrived at Ashen Bluffs.
- event_title: Refugee Family
- event_text (given to the scene call only): A family sits by the road. Children. They watch your food with hollow eyes.
- action: travel
- place: Ashen Bluffs
- biome: forest
- time_of_day: night
- situation: Forest terrain. Nearing the halfway mark. Their doctrine: travel light. Their taboo: no travel at night.
- party_health_band: steady
- party_morale_band: high
- resource_directions: distance:travelled, firewood:spent, food:spent, morale:rose, parts:spent, time_days:days passed, water:gained
- turn_matters: death=false, injury=false, supply_zero=true, landmark_arrival=true, night_at_camp=false
- the game's own lines: Arrived at Ashen Bluffs! Found water. +6 water. Dark travel mishap! Wagon damage: 8
- scene line this turn (accepted): Mud grips the wheels.

### 8. Chronicler, standard, supply at zero (turn v2-w0-005, attempt 1)

> The party travelled on. Mud deepens. Firewood spent. Food spent. Water spent.

- what happened (the lead the model was given): The party travelled on.
- action: travel
- place: Crow's Perch
- biome: plains
- time_of_day: night
- situation: Plains terrain. Early in the journey. Their doctrine: travel light. Their taboo: no travel at night.
- party_health_band: steady
- party_morale_band: high
- resource_directions: distance:travelled, firewood:spent, food:spent, morale:rose, oil:spent, time_days:days passed, water:spent
- turn_matters: death=false, injury=false, supply_zero=true, landmark_arrival=false, night_at_camp=false
- the game's own lines: Traveled 5 miles. 9 miles remaining.
- scene line this turn (accepted): Mud deepens under wheel. Wind stirs dry grass. No sound but breath and creak.

### 9. Chronicler, rich, choice resolved (turn v2-w0-008, attempt 1)

> The tongue snaps. Mud clings to the wheel. The track bends where no track should be.

- what happened (the lead the model was given): The party chose: Repair the break.
- event_title: Snapped Tongue
- event_text (given to the scene call only): The wagon tongue cracks like a dry bone.
- choice_taken: Repair the break
- place: Fog Hollow
- biome: forest
- time_of_day: evening
- situation: Forest terrain. Nearing the halfway mark. Their doctrine: travel light. Their taboo: no travel at night.
- party_health_band: steady
- party_morale_band: high
- resource_directions: parts:spent, time_days:days passed, tools:spent
- turn_matters: death=false, injury=false, supply_zero=true, landmark_arrival=false, night_at_camp=false
- the game's own lines: -3 parts, -1 tools, 2 time lost
- scene line this turn (rule_reject): The wagon tongue cracks like a dry bone. Mud swells in the wheel grooves. Smoke curls from the fire, thin and gray.

### 10. Chronicler, brief, ordinary travel (turn v2-w0-006, attempt 1)

> The party travelled on.

- what happened (the lead the model was given): The party travelled on.
- event_title: Fellow Travelers
- event_text (given to the scene call only): Another party camps nearby. They share a fire and news of the road ahead.
- action: travel
- place: Salt Flat
- biome: forest
- time_of_day: evening
- situation: Forest terrain. Nearing the halfway mark. Their doctrine: travel light. Their taboo: no travel at night.
- party_health_band: steady
- party_morale_band: high
- resource_directions: distance:travelled, food:spent, morale:rose, time_days:days passed, water:spent
- turn_matters: death=false, injury=false, supply_zero=false, landmark_arrival=false, night_at_camp=false
- the game's own lines: Traveled 5 miles. 15 miles remaining.
- scene line this turn (accepted): Mud grips the wheel.


## Fireside

### 11. Fireside, standard, death (turn v2-w0-002, attempt 1)

> A traveller died. The Long Descent hums low in the swamp.

- what happened (the lead the model was given): A traveller died.
- event_title: Hungry Family
- event_text (given to the scene call only): Small hands reach out beside the rutted path.
- action: travel
- place: The Long Descent
- biome: swamp
- time_of_day: evening
- situation: Swamp terrain. Well past halfway. Several of the party are lost. They have no food. Their doctrine: no debts. Their taboo: no river water.
- party_health_band: worn
- party_morale_band: low
- resource_directions: distance:travelled, health:fell, time_days:days passed, water:spent
- health_effects: starvation, death, starvation, starvation
- turn_matters: death=true, injury=true, supply_zero=false, landmark_arrival=false, night_at_camp=false
- the game's own lines: Traveled 3 miles. 5 miles remaining. Amos has died (Starvation).
- scene line this turn (accepted): Small hands press into the mud beside the rutted path. The air grows thick with the smell of wet earth and old fear.

### 12. Fireside, rich, lost ending (turn v2-w0-047, attempt 1)

> The last of the party has died. The journey ends here. Fog Hollow holds no light, only the slow breath of wet earth and the silence where voices used to be.

- what happened (the lead the model was given): The last of the party has died. The journey ends here.
- action: travel
- place: Fog Hollow
- biome: swamp
- time_of_day: evening
- ending: lost
- situation: Swamp terrain. Nearing the halfway mark. None of the party is left. Their doctrine: no debts. Their taboo: no river water.
- party_health_band: dead
- party_morale_band: broken
- resource_directions: distance:travelled, health:fell, morale:fell, time_days:days passed, water:spent
- health_effects: starvation, death
- turn_matters: death=true, injury=true, supply_zero=false, landmark_arrival=false, night_at_camp=false
- the game's own lines: Traveled 4 miles. 16 miles remaining. Thomas has died (Starvation). The journey ends. Cause: Starvation.
- scene line this turn (accepted): The fog clings to the reeds like old breath. The oxen stand still, shoulders hunched, eyes fixed on the water's edge. No one moves. No one speaks. The silence grows thick as the mud.

### 13. Fireside, brief, triumphant ending (turn v2-w1-020, attempt 1)

> The party reached Ravenmoor.

- what happened (the lead the model was given): The party reached Ravenmoor and the end of the trail. The journey is over.
- action: travel
- place: Ravenmoor
- biome: plains
- time_of_day: evening
- ending: triumphant
- situation: Plains terrain. The end of the trail is near. Rations are nearly gone. Their doctrine: travel light. Their taboo: leave nothing behind.
- party_health_band: worn
- party_morale_band: high
- resource_directions: distance:travelled, food:gained, health:fell, morale:fell, parts:spent, time_days:days passed, water:gained
- turn_matters: death=false, injury=true, supply_zero=true, landmark_arrival=true, night_at_camp=false
- the game's own lines: Arrived at Ravenmoor! Found water. +4 water. Traded at the settlement. +3 food. Wagon breakdown! Repaired. Damage: 5 You made it! Victory!
- scene line this turn (accepted): The wind lifts dust from the plain.

### 14. Fireside, standard, pyrrhic ending (turn v2-w1-022, attempt 3)

> The party reached Copperhill. The trail ends here. They have no food.

- what happened (the lead the model was given): The party reached Copperhill and the end of the trail, with some of its number lost on the way. The journey is over.
- action: travel
- place: Copperhill
- biome: forest
- time_of_day: afternoon
- ending: pyrrhic
- situation: Forest terrain. The end of the trail is near. Several of the party are lost. They have no food. Their doctrine: no debts. Their taboo: no river water.
- party_health_band: critical
- party_morale_band: low
- resource_directions: distance:travelled, health:fell, time_days:days passed, water:gained
- health_effects: starvation, starvation
- turn_matters: death=false, injury=true, supply_zero=false, landmark_arrival=true, night_at_camp=false
- the game's own lines: Arrived at Copperhill! Found water. +8 water. This is a settlement. Supplies may be available. You made it! Victory!
- scene line this turn (rule_reject): Mud grips the boots. The oxen drag through leaves. A hush hangs where the river should be.

### 15. Fireside, rich, injury, no death (turn v2-w0-017, attempt 1)

> The party moves on through the alpine night, shoulders low, steps slow. The wind hums through the rocks, a sound like old bones shifting. River water is not taken, though the ground near the slope breathes with cold memory.

- what happened (the lead the model was given): The party travelled on.
- action: travel
- place: The Scar
- biome: alpine
- time_of_day: night
- situation: Alpine terrain. Nearing the halfway mark. Their doctrine: no debts. Their taboo: no river water.
- party_health_band: worn
- party_morale_band: high
- resource_directions: distance:travelled, food:spent, health:fell, morale:rose, time_days:days passed, water:spent
- turn_matters: death=false, injury=true, supply_zero=false, landmark_arrival=false, night_at_camp=false
- the game's own lines: Traveled 5 miles. 5 miles remaining.
- scene line this turn (accepted): The wind slips through the rock crevices like old breath. Snow gathers in the hollows where the oxen stand still. They drink from their canteens, hands steady, eyes fixed on the dark river below.

### 16. Fireside, brief, night camp (turn v2-w0-011, attempt 1)

> The party hunted and brought back food.

- what happened (the lead the model was given): The party hunted and brought back food.
- action: hunt
- place: The Switchback
- biome: plains
- time_of_day: night
- situation: Plains terrain. Early in the journey. Their doctrine: travel light. Their taboo: leave nothing behind.
- party_health_band: steady
- party_morale_band: high
- resource_directions: ammo:spent, food:gained
- turn_matters: death=false, injury=false, supply_zero=false, landmark_arrival=false, night_at_camp=true
- the game's own lines: Hunt successful! +13 food. -1 ammo.
- scene line this turn (accepted): Mud clings to the oxen hooves as they move through the low grass.

### 17. Fireside, standard, landmark arrival (turn v2-w0-020, attempt 2)

> The party settles at Hazelwick where the wind hums through cracked stone. A single well stands half-buried in dust.

- what happened (the lead the model was given): The party arrived at Hazelwick.
- event_title: The Wary Settlement
- event_text (given to the scene call only): The town will trade, but they insist you leave before nightfall. They won't say why.
- action: travel
- place: Hazelwick
- biome: desert
- time_of_day: morning
- situation: Desert terrain. Well past halfway. Their doctrine: travel light. Their taboo: leave nothing behind.
- party_health_band: worn
- party_morale_band: high
- resource_directions: distance:travelled, food:spent, morale:rose, time_days:days passed, water:spent
- turn_matters: death=false, injury=false, supply_zero=false, landmark_arrival=true, night_at_camp=false
- the game's own lines: Arrived at Hazelwick! This is a settlement. Supplies may be available.
- scene line this turn (accepted): The sun bleeds low over the dunes, dust swirling in the wind like old breath. The oxen move slow, shoulders hunched, eyes fixed on the horizon.

### 18. Fireside, rich, supply at zero (turn v2-w0-009, attempt 3)

> The party settled in the hollow where the trees lean close, their breaths shallow and slow. The medicine was poured into the fire, smoke curling like old words from the earth.

- what happened (the lead the model was given): The party chose: Use all available medicine.
- event_title: Illness Sweeps the Camp
- event_text (given to the scene call only): Half the party is down. The symptoms are unmistakable.
- choice_taken: Use all available medicine.
- place: The Long Descent
- biome: forest
- time_of_day: night
- situation: Forest terrain. Well past halfway. Their doctrine: travel light. Their taboo: no travel at night.
- party_health_band: steady
- party_morale_band: high
- resource_directions: morale:fell, time_days:days passed
- turn_matters: death=false, injury=false, supply_zero=true, landmark_arrival=false, night_at_camp=false
- the game's own lines: -2 meds, morale -3, 1 time lost
- scene line this turn (rule_reject): Mud grips the boots of the oxen as they drag the heavy frame through the darkening forest. A cough rises from the back, thick and wet, like roots pulled from the ground. The fire flickers, holding the shadows in place, just enough to see the way the air shivers near the trees.

### 19. Fireside, brief, choice resolved (turn v2-w0-016, attempt 1)

> The party moves through The Scar.

- what happened (the lead the model was given): The party chose: Trade quickly and leave.
- event_title: The Wary Settlement
- event_text (given to the scene call only): The town will trade, but they insist you leave before nightfall. They won't say why.
- choice_taken: Trade quickly and leave.
- place: The Scar
- biome: alpine
- time_of_day: evening
- situation: Alpine terrain. Nearing the halfway mark. Their doctrine: no debts. Their taboo: no river water.
- party_health_band: worn
- party_morale_band: high
- resource_directions: food:gained, morale:fell, water:gained
- turn_matters: death=false, injury=false, supply_zero=false, landmark_arrival=false, night_at_camp=false
- the game's own lines: +5 food, +5 water, morale -2
- scene line this turn (accepted): Mud clings to the oxen's hooves as they move through the alpine slope.

### 20. Fireside, standard, ordinary travel (turn v2-w0-018, attempt 1)

> The party rested in the thin air of The Scar. Snow melted in the morning light, seeping into the stone beneath their feet.

- what happened (the lead the model was given): The party rested.
- action: rest
- place: The Scar
- biome: alpine
- time_of_day: morning
- situation: Alpine terrain. Nearing the halfway mark. Their doctrine: no debts. Their taboo: no river water.
- party_health_band: worn
- party_morale_band: high
- resource_directions: food:spent, health:rose, morale:rose, time_days:days passed, water:spent
- turn_matters: death=false, injury=false, supply_zero=false, landmark_arrival=false, night_at_camp=false
- the game's own lines: The party rests for a day.
- scene line this turn (accepted): Mud clings to the oxen's hooves as they move through the cracked stone. The river lies far below, silent and unclaimed.


## Uncanny Bearer

### 21. Uncanny Bearer, rich, death (turn v2-w0-003, attempt 1)

> A traveller died. The bridge creaks in a way that does not match the weight of the mud. The air holds a stillness that should not exist after nightfall.

- what happened (the lead the model was given): A traveller died.
- event_title: Fire Gone Out
- event_text (given to the scene call only): The fire has died. The cold presses in. No firewood remains.
- action: travel
- place: Broken Bridge
- biome: swamp
- time_of_day: night
- situation: Swamp terrain. Well past halfway. A lone traveller remains. They have no food. Their doctrine: no debts. Their taboo: no river water.
- party_health_band: worn
- party_morale_band: low
- resource_directions: distance:travelled, health:fell, time_days:days passed, water:spent
- health_effects: starvation, starvation, death
- turn_matters: death=true, injury=true, supply_zero=false, landmark_arrival=false, night_at_camp=false
- the game's own lines: Traveled 3 miles. 7 miles remaining. Nathaniel has died (Starvation).
- scene line this turn (accepted): The bridge groans beneath weight not meant to be borne. Water shifts in wrong angles. The cold spreads through the mud like a slow breath.

### 22. Uncanny Bearer, brief, lost ending (turn v2-w0-075, attempt 1)

> The last of the party has died.

- what happened (the lead the model was given): The last of the party has died. The journey ends here.
- event_title: Fresh Bear Sign
- event_text (given to the scene call only): The prints are wide and deep in the soft earth.
- action: travel
- place: Sunken Meadow
- biome: plains
- time_of_day: afternoon
- ending: lost
- situation: Plains terrain. Early in the journey. None of the party is left. Their doctrine: no debts. Their taboo: no river water.
- party_health_band: dead
- party_morale_band: broken
- resource_directions: distance:travelled, health:fell, time_days:days passed, water:spent
- health_effects: starvation, death, starvation, death, starvation, death
- turn_matters: death=true, injury=true, supply_zero=false, landmark_arrival=false, night_at_camp=false
- the game's own lines: Traveled 4 miles. 5 miles remaining. Thomas has died (Starvation). Amos has died (Starvation). Nathaniel has died (Starvation). The journey ends. Cause: Starvation.
- scene line this turn (accepted): Bear prints stretch wide in mud.

### 23. Uncanny Bearer, standard, triumphant ending (turn v2-w2-008, attempt 1)

> The party reached Copperhill and the end of the trail. The journey is over.

- what happened (the lead the model was given): The party reached Copperhill and the end of the trail. The journey is over.
- action: travel
- place: Copperhill
- biome: plains
- time_of_day: evening
- ending: triumphant
- situation: Plains terrain. The end of the trail is near. Their doctrine: travel light. Their taboo: no travel at night.
- party_health_band: worn
- party_morale_band: high
- resource_directions: distance:travelled, food:gained, health:fell, time_days:days passed, water:gained
- turn_matters: death=false, injury=true, supply_zero=false, landmark_arrival=true, night_at_camp=false
- the game's own lines: Arrived at Copperhill! Found water. +9 water. Traded at the settlement. +9 food. You made it! Victory!
- scene line this turn (accepted): The sky folds into the horizon like a wound that never closes. The wind carries the scent of old iron and wet stone.

### (no accepted line found for pyrrhic ending, rich)

### 24. Uncanny Bearer, brief, injury, no death (turn v2-w0-051, attempt 1)

> The party travelled on.

- what happened (the lead the model was given): The party travelled on.
- action: travel
- place: Shepherd's Rest
- biome: forest
- time_of_day: evening
- situation: Forest terrain. Nearing the halfway mark. They have no food. Their doctrine: travel light. Their taboo: no travel at night.
- party_health_band: steady
- party_morale_band: high
- resource_directions: distance:travelled, food:spent, health:fell, morale:fell, parts:spent, time_days:days passed, water:spent
- health_effects: starvation, starvation, starvation, starvation
- turn_matters: death=false, injury=true, supply_zero=true, landmark_arrival=false, night_at_camp=false
- the game's own lines: Traveled 5 miles. 6 miles remaining. Dark travel mishap! Wagon damage: 5
- scene line this turn (accepted): Mud pools stretch beyond the trees, edges curling inward like old wounds.

### 25. Uncanny Bearer, standard, night camp (turn v2-w0-012, attempt 1)

> The party rested. The air hums with a geometry that does not close.

- what happened (the lead the model was given): The party rested.
- action: rest
- place: Crow's Perch
- biome: swamp
- time_of_day: night
- situation: Swamp terrain. Nearing the halfway mark. Multiple members are sick or injured. Their doctrine: travel light. Their taboo: leave nothing behind.
- party_health_band: worn
- party_morale_band: high
- resource_directions: food:spent, health:rose, time_days:days passed, water:spent
- turn_matters: death=false, injury=false, supply_zero=false, landmark_arrival=false, night_at_camp=true
- the game's own lines: The party rests for a day.
- scene line this turn (accepted): Mud pulls at the edges of the wheel like it knows the shape of the world is wrong.

### 26. Uncanny Bearer, rich, landmark arrival (turn v2-w0-027, attempt 1)

> The party arrived at Fellgate. The wagon groans as the wind slants through the trees, pressing the sides inward like a breath held too long. The path curves left where it should not, and the river runs backward in the mud.

- what happened (the lead the model was given): The party arrived at Fellgate.
- event_title: Gusting North Wind
- event_text (given to the scene call only): The wind carries the scent of snow yet to fall.
- action: travel
- place: Fellgate
- biome: forest
- time_of_day: night
- situation: Forest terrain. Well past halfway. The wagon may not survive another hit. Their doctrine: travel light. Their taboo: no travel at night.
- party_health_band: steady
- party_morale_band: high
- resource_directions: distance:travelled, food:spent, time_days:days passed, water:gained
- turn_matters: death=false, injury=false, supply_zero=false, landmark_arrival=true, night_at_camp=false
- the game's own lines: Arrived at Fellgate! Found water. +20 water. This is a settlement. Supplies may be available.
- scene line this turn (accepted): The wind slants through the pines with a tilt that does not belong to any known angle. Snow has not fallen yet but the air tastes of it, thick and old as riverbeds beneath stone. The wagon groans beneath the pressure of the gusts, its wheels bending slightly in a motion that should not occur.

### 27. Uncanny Bearer, brief, supply at zero (turn v2-w0-048, attempt 1)

> The party travelled on.

- what happened (the lead the model was given): The party travelled on.
- action: travel
- place: Crow's Perch
- biome: plains
- time_of_day: morning
- situation: Plains terrain. Early in the journey. Their doctrine: travel light. Their taboo: no travel at night.
- party_health_band: steady
- party_morale_band: high
- resource_directions: distance:travelled, firewood:spent, food:spent, morale:rose, oil:spent, time_days:days passed, water:spent
- turn_matters: death=false, injury=false, supply_zero=true, landmark_arrival=false, night_at_camp=false
- the game's own lines: Traveled 5 miles. 3 miles remaining.
- scene line this turn (accepted): Mud pools stretch beyond horizon lines.

### 28. Uncanny Bearer, standard, choice resolved (turn v2-w0-014, attempt 1)

> The Long Descent stretches ahead. Mud pools hold no reflection.

- what happened (the lead the model was given): The party chose: Give what you can spare.
- event_title: Hungry Family
- event_text (given to the scene call only): Small hands reach out beside the rutted path.
- choice_taken: Give what you can spare
- place: The Long Descent
- biome: plains
- time_of_day: night
- situation: Plains terrain. Early in the journey. Their doctrine: careful hands. Their taboo: no river water.
- party_health_band: worn
- party_morale_band: high
- resource_directions: food:spent, morale:rose
- turn_matters: death=false, injury=false, supply_zero=false, landmark_arrival=false, night_at_camp=false
- the game's own lines: -4 food, morale +3
- scene line this turn (accepted): Small hands press into the mud beside the rutted path. Their fingers curve like old roots in the dark.

### 29. Uncanny Bearer, rich, ordinary travel (turn v2-w0-022, attempt 1)

> The party travelled on. The sand stretched beyond the edge of vision, folding into itself like a wound that never closes. A single dune rose and fell without cause, its slope shifting in reverse after a breath.

- what happened (the lead the model was given): The party travelled on.
- action: travel
- place: Hazelwick
- biome: desert
- time_of_day: afternoon
- situation: Desert terrain. Well past halfway. Their doctrine: travel light. Their taboo: leave nothing behind.
- party_health_band: worn
- party_morale_band: high
- resource_directions: distance:travelled, food:spent, morale:rose, time_days:days passed, water:spent
- turn_matters: death=false, injury=false, supply_zero=false, landmark_arrival=false, night_at_camp=false
- the game's own lines: Traveled 5 miles. 13 miles remaining.
- scene line this turn (accepted): The dunes curve inward like a wound that does not close. Sand shifts beneath the wheels, not with wind but with a slow, deliberate breath. The horizon blurs into a shape that should not exist.

