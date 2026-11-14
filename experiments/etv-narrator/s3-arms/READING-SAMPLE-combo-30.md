# Reading sample: combination arm (rulings prompt + up to 3 candidates + trim, model-card sampling)

Session 3, ETV b12cbb85, turn set v2 095455fb. 30 accepted lines, 10 per voice. Chosen by rule, not by taste: for each
category, the first unused turn in turn-set order whose line was accepted; lengths rotate. The outcome slot is shown
(it carries what happened), with the turn facts the model was given.

## R&D's reading (2026-11-13): accepted is not the same as good

29 lines, not 30: no accepted Uncanny Bearer line exists at Rich for either pyrrhic turn. Read against the turn facts:

**Lines that contradict their facts (the checker passed all of them)**
- 1 (death): "No water." Water was spent, not gone (supply_zero=false).
- 4 (pyrrhic ending): "No water." Water was GAINED on this turn.
- 6 (night camp): "Firewood gone." Firewood was spent, not gone; the turn's real news (a rest, someone recovered) is absent.
- 21 (death): "The wagon planks lie scattered, their edges split and dark." Nothing happened to the wagon.
- 29 (ordinary): "Water is gone from the canteen." Water was spent, not gone.
- 12 (lost ending): the oxen "drag the wagon" on a turn where none of the party is left.
- 2 (lost ending): "Hunger sharpens" after the last traveller has died.

**Lines that don't say what happened**
- All five victory lines (3, 4, 13, 14, 23) describe mud, wind or oxen. None conveys an arrival or an ending.
- Of six death or lost-ending lines, two convey it (2 "No one moves", 22 "No one left."). Lines 1, 11, 12 and 21 don't.
- 16: a successful hunt reads "Oxen pause by a river bend". 18: the party used all its medicine on a sickness; the line
  is about smoke. 19 and 28: the choice taken (giving food; trading quickly) is not in the line.
- 5, 15, 17, 26: an arrival at a landmark; only 17 mentions the town.

**Copying and ledger-speak**
- 11, 19 and 21 open with the event text word for word; 9 opens with it too.
- 7 and 8 read as a ledger: "Firewood spent. Food spent. Water spent."

**Repetition**
- 12 of the 29 lines open with "Mud". "Mud pools stretch beyond the edge of" opens 24 and 25; Fireside opens 9 of its 10
  lines with the oxen.
- Mud appears in alpine and desert-edge turns as readily as in swamp.

**Lines that read well against their facts:** 9, 10, 17, 22, 26.

**What this means.** The checker tests what a line must not do. Nothing tests that a line says what happened, and the
model mostly writes weather. Note that the game prints its own result lines beside the narration ("the game's own
lines" in each entry), so the narration is not the only carrier of the facts; but "no water" on a turn that gained
water is a contradiction a player will see. The 8.1% fallback rate is real; it is a rate of rule-passing lines, not of
good ones.

## Chronicler

### 1. Chronicler, brief, death (turn v2-w0-001, attempt 1)

> Compass spins. Sun hides. Mud swells. No water. No food. No way.

- event_title: Spinning Compass
- event_text: The compass needle spins lazily. It refuses to settle on any heading.
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
- scene line this turn (accepted): Compass spins. Sun hides behind mist. Mud swells. No food. No water. No map.

### 2. Chronicler, standard, lost ending (turn v2-w0-004, attempt 2)

> Dark clouds gather. Wind lashes the mud. No one moves. Water spent. Firewood gone. Hunger sharpens.

- event_title: Sudden Storm
- event_text: Dark clouds mass without warning. The wind picks up sharply.
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
- scene line this turn (accepted): Rain slaps the bridge. Mud swallows the wheel. No one walks. No one breathes.

### 3. Chronicler, rich, triumphant ending (turn v2-w0-023, attempt 2)

> Mud sucks at the heels. Wind stings the face. A track cuts through the grass, not made by foot.

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
- scene line this turn (accepted): Mud swells under wheels. Wind tugs at the trail. The river lies ahead, dark and still. No birds. No breath. Only the pull of the next step.

### 4. Chronicler, brief, pyrrhic ending (turn v2-w0-025, attempt 1)

> Mud swells. Breath falters. No water. No food.

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
- scene line this turn (accepted): Mud swells under wheels. Air thickens. Silence follows the river's bend.

### 5. Chronicler, standard, injury, no death (turn v2-w0-015, attempt 2)

> Mud sucks at the wheels. Wind bites the face. The trail hums with a low, steady sound.

- event_title: The Wary Settlement
- event_text: The town will trade, but they insist you leave before nightfall. They won't say why.
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
- scene line this turn (accepted): Mud stings at knee. Sky bleeds purple. River lies hidden behind rock.

### 6. Chronicler, rich, night camp (turn v2-w0-010, attempt 1)

> Mud sucks at the heels. Firewood gone. Night deepens. Wind hums through the grass. No trace of footprints. The air holds a stillness that does not belong.

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

> Mud grips the wheel. Children watch. Firewood spent. Water gained.

- event_title: Refugee Family
- event_text: A family sits by the road. Children. They watch your food with hollow eyes.
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
- scene line this turn (accepted): Mud grips the wheels. Wind howls through the pines. Children watch with empty eyes.

### 8. Chronicler, standard, supply at zero (turn v2-w0-005, attempt 1)

> Mud grips the wheels. Firewood spent. Food spent. Water spent. Night comes slow.

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

### 9. Chronicler, rich, choice resolved (turn v2-w0-008, attempt 2)

> The wagon tongue cracks like a dry bone. Mud sucks at the iron. Tools lie cold in the satchel.

- event_title: Snapped Tongue
- event_text: The wagon tongue cracks like a dry bone.
- choice_taken: Repair the break
- place: Fog Hollow
- biome: forest
- time_of_day: evening
- situation: Forest terrain. Nearing the halfway mark. Their doctrine: travel light. Their taboo: no travel at night.
- party_health_band: steady
- party_morale_band: high
- resource_directions: parts:spent, time_days:days passed, tools:spent
- turn_matters: death=false, injury=false, supply_zero=true, landmark_arrival=false, night_at_camp=false
- the game's own lines: 
- scene line this turn (accepted): The wagon tongue cracks like a dry bone. Mud swells in the hollows. Smoke curls from the fire, thin and slow.

### 10. Chronicler, brief, ordinary travel (turn v2-w0-006, attempt 1)

> Fire glows low. Smoke curls into the dark. A path splits ahead.

- event_title: Fellow Travelers
- event_text: Another party camps nearby. They share a fire and news of the road ahead.
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
- scene line this turn (accepted): Mud grips the wheels. Fire glows low. Smoke curls west.

## Fireside

### 11. Fireside, standard, death (turn v2-w0-002, attempt 1)

> Small hands reach out beside the rutted path. A child's grip tightens on the wagon rim.

- event_title: Hungry Family
- event_text: Small hands reach out beside the rutted path.
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
- scene line this turn (accepted): Small hands press against the wagon side. Mud stains the oxen's hooves. The river hums low beneath the path.

### 12. Fireside, rich, lost ending (turn v2-w0-047, attempt 1)

> The oxen drag the wagon through thick reeds, mud sucking at the wheels. Smoke curls from the back, not from fire, not from breath. The trail ends where the water has no name.

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
- scene line this turn (accepted): Mud slithers up the wagon wheels like old breath. The oxen step slow, their hooves dragging through the reeds. No one speaks. The air tastes of wet earth and something older.

### 13. Fireside, brief, triumphant ending (turn v2-w1-020, attempt 1)

> Oxen step through tall grass, mud darkening the wheel's edge.

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
- scene line this turn (accepted): Oxen step through dust, shadows long on the plain.

### 14. Fireside, standard, pyrrhic ending (turn v2-w1-022, attempt 1)

> Oxen lag in mud. Smoke curls from the wagon. A river glints in the trees.

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
- scene line this turn (accepted): Oxen drag through mud, breath slow and thin. Sun dips low, shadows stretch long.

### 15. Fireside, rich, injury, no death (turn v2-w0-017, attempt 1)

> The oxen drag the wagon through the mud, their breath puffing in the cold air. One trail wears thin, the path worn by many before, leading to a bend where the river cuts through stone. The men keep their eyes down, hands folded, as if the water might speak if looked upon.

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
- scene line this turn (accepted): The oxen slow in the shadow of the ridge where the river cuts through stone. Rain beads on the wagon's iron rim, each drop catching the wind like a whispered name. A man lifts his flask to his lips, eyes fixed on the slope beyond, as if the land knows what he does not.

### 16. Fireside, brief, night camp (turn v2-w0-011, attempt 1)

> Oxen pause by a river bend, hooves sinking into wet mud.

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
- scene line this turn (accepted): Oxen slow in mud, breath like smoke in the dark.

### 17. Fireside, standard, landmark arrival (turn v2-w0-020, attempt 1)

> The oxen slow in the dust, their breath puffing in the heat. The town stands silent, fingers pressed to the gate.

- event_title: The Wary Settlement
- event_text: The town will trade, but they insist you leave before nightfall. They won't say why.
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
- scene line this turn (accepted): Oxen step through dust, their breath fogging the morning. The town stands quiet, hands on doors, eyes fixed on the path.

### 18. Fireside, rich, supply at zero (turn v2-w0-009, attempt 1)

> Mud pools swallow the wheel tracks. The oxen stand still, breaths slow, eyes fixed on the trees. A thin line of smoke curls from the far ridge, not from fire, not from smoke.

- event_title: Illness Sweeps the Camp
- event_text: Half the party is down. The symptoms are unmistakable.
- choice_taken: Use all available medicine.
- place: The Long Descent
- biome: forest
- time_of_day: night
- situation: Forest terrain. Well past halfway. Their doctrine: travel light. Their taboo: no travel at night.
- party_health_band: steady
- party_morale_band: high
- resource_directions: morale:fell, time_days:days passed
- turn_matters: death=false, injury=false, supply_zero=true, landmark_arrival=false, night_at_camp=false
- the game's own lines: 
- scene line this turn (rule_reject): Mud sucks at the wheels of the wagon as it groans through the forest night. The air tastes of wet leaves and something older, something not of this world. Half the men lie still in the grass, faces pale, breaths shallow.

### 19. Fireside, brief, choice resolved (turn v2-w0-014, attempt 1)

> Small hands reach out beside the rutted path.

- event_title: Hungry Family
- event_text: Small hands reach out beside the rutted path.
- choice_taken: Give what you can spare
- place: The Long Descent
- biome: plains
- time_of_day: night
- situation: Plains terrain. Early in the journey. Their doctrine: careful hands. Their taboo: no river water.
- party_health_band: worn
- party_morale_band: high
- resource_directions: food:spent, morale:rose
- turn_matters: death=false, injury=false, supply_zero=false, landmark_arrival=false, night_at_camp=false
- the game's own lines: 
- scene line this turn (accepted): Small hands press into the mud beside the rutted path.

### 20. Fireside, standard, ordinary travel (turn v2-w0-018, attempt 1)

> Oxen slow in the mist, breath like fog in the hollows. The river bends just beyond the rise, unseen, unclaimed.

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
- scene line this turn (accepted): Oxen slow through misted stone, breath fogging the air. A river glints far below, unseen, unclaimed.

## Uncanny Bearer

### 21. Uncanny Bearer, rich, death (turn v2-w0-003, attempt 1)

> The fire has died. The cold seeps through the mud. The wagon planks lie scattered, their edges split and dark.

- event_title: Fire Gone Out
- event_text: The fire has died. The cold presses in. No firewood remains.
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
- scene line this turn (accepted): The bridge groans beneath weight not meant to be borne. Mud pools in angles that do not close. A cold breath moves through the air before the wind arrives.

### 22. Uncanny Bearer, brief, lost ending (turn v2-w0-075, attempt 1)

> Bear prints stretch wide in the mud. Earth pulls back like breath. No water. No sound. No one left.

- event_title: Fresh Bear Sign
- event_text: The prints are wide and deep in the soft earth.
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
- scene line this turn (accepted): Bear prints split the mud, wide and deep, like a wound in the land.

### 23. Uncanny Bearer, standard, triumphant ending (turn v2-w2-008, attempt 1)

> The path bends where it should not. Mud pools stretch beyond the horizon.

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
- scene line this turn (accepted): The sky folds into the horizon like a wound that never heals. The wind carries the scent of old iron and wet stone.

### (no accepted line found for pyrrhic ending, rich)

### 24. Uncanny Bearer, brief, injury, no death (turn v2-w0-051, attempt 1)

> Mud pools stretch beyond the edge of the forest, deeper than they should be.

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
- scene line this turn (accepted): Mud pools stretch beyond the edge of the path, rising like slow breaths.

### 25. Uncanny Bearer, standard, night camp (turn v2-w0-012, attempt 1)

> Mud pools stretch beyond the edge of the world. The river hums in reverse.

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
- scene line this turn (accepted): Mud pulls at the edges of the wheel like it knows the shape of the sky. The river hums a note beneath the ground, matching the rhythm of breaths.

### 26. Uncanny Bearer, rich, landmark arrival (turn v2-w0-027, attempt 1)

> The wind hums through the pines with a sound that does not belong to any known vibration. The wagon groans as if it has already been struck by something unseen. Snow does not fall yet the air tastes of frost that has not yet reached the ground.

- event_title: Gusting North Wind
- event_text: The wind carries the scent of snow yet to fall.
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
- scene line this turn (accepted): The wind slants through the pines with a tilt that does not belong to any known angle. Snow has not fallen yet but the air tastes of it, thick and old as the roots beneath the soil. The wagon groans in reply, each joint shifting slightly out of alignment.

### 27. Uncanny Bearer, brief, supply at zero (turn v2-w0-048, attempt 1)

> Mud stretches in loops that do not close. Sun rises behind the ridge.

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
- scene line this turn (accepted): The sun spills over the ridge, but the light bends too wide at the edge.

### 28. Uncanny Bearer, standard, choice resolved (turn v2-w0-016, attempt 1)

> The river bends where it shouldn't. Water flows upward in the dusk.

- event_title: The Wary Settlement
- event_text: The town will trade, but they insist you leave before nightfall. They won't say why.
- choice_taken: Trade quickly and leave.
- place: The Scar
- biome: alpine
- time_of_day: evening
- situation: Alpine terrain. Nearing the halfway mark. Their doctrine: no debts. Their taboo: no river water.
- party_health_band: worn
- party_morale_band: high
- resource_directions: food:gained, morale:fell, water:gained
- turn_matters: death=false, injury=false, supply_zero=false, landmark_arrival=false, night_at_camp=false
- the game's own lines: 
- scene line this turn (accepted): The stones curve wrong in the slope. River water glints in the mud, but does not reflect.

### 29. Uncanny Bearer, rich, ordinary travel (turn v2-w0-022, attempt 1)

> The sun dips behind the dune, casting a slant of light that does not follow the curve of the sky. Sand shifts underfoot, each grain moving in a pattern that does not repeat. Water is gone from the canteen, yet the vessel feels full.

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
- scene line this turn (accepted): The dunes curve inward like a wound that does not close. Sand shifts beneath the wheels, not with wind but with a slow, deliberate breath. The horizon stretches in a line that should not exist, yet the sun remains fixed in the sky, too still to be natural.
