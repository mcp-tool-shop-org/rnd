# Reading sample, side by side: ship, haiku, opus, fable

Standard length only. 10 turns per voice, chosen by rule, not by taste: for each category, the first unused turn in turn-set order whose outcome line was accepted by every model listed; if there is none, the first unused turn accepted by the most models. Every model was given the same turn facts, shown under the lines. A line marked "fell back" was rejected by the checker (the rule is named) and the player would have seen the game's own line instead. No reading has been added.


## Chronicler

### 1. Chronicler, death (turn v2-w0-001)

- **ship** (attempt 1): A traveller died. Mud swells. The compass spins. No river water. No food.
- **haiku** (attempt 1): A traveller died in the swamp this afternoon, with no food left in the wagon. The compass needle spins without rest in the wet grey light at The Long Descent.
- **opus** (attempt 1): A traveller dies in the afternoon on The Long Descent, hollow from hunger and fever. The swamp water stands black and still, and the compass needle will not settle.
- **fable** (attempt 1): A traveller dies of hunger and fever on The Long Descent, and the wagon rolls on. The afternoon swamp is very quiet, and the compass needle will not settle.

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

- **ship** (attempt 1): Storm breaks. Rain falls. Mud swells. No one moves. The last breath ends.
- **haiku** (attempt 1): The last of the party is dead and the journey ends here at the Broken Bridge in the swamp. Mud holds the wagon and the water rises slowly over the planks.
- **opus** (attempt 1): The last of the party dies in the morning storm, and the journey ends here at Broken Bridge. Rain fills the swamp around the empty wheel ruts and the split timbers hang over brown water.
- **fable** (attempt 1): The last of the party dies in the storm, and the journey ends here. Rain falls on the swamp near Broken Bridge, and the wagon sits in the mud.

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

### 3. Chronicler, triumphant ending (turn v2-w2-008)

- **ship** (attempt 1): The party reaches Copperhill. Evening wind stirs the grass. No one speaks.
- **haiku** (attempt 1): The wagon rolled into Copperhill at evening with the wheels grinding in the mud. The party is worn but in good spirits, and the trail ends here.
- **opus** (attempt 2): The party reaches Copperhill at evening, and the trail ends here in the plains grass. Worn and limping, they take on food and water while the light holds and smoke rises from the chimneys.
- **fable** fell back after 3 attempt(s) (repeated_opening); last rejected text: The wagon rolls into Copperhill at evening and the trail ends here, the journey done. The plains wind drops, and sore limbs climb down into dry grass, grinning.

Turn facts:

- what happened (the lead every model was given): The party reached Copperhill and the end of the trail. The journey is over.
- action: travel
- place: Copperhill; biome: plains; time_of_day: evening
- ending: triumphant
- situation: Plains terrain. The end of the trail is near. Their doctrine: travel light. Their taboo: no travel at night.
- party_health_band: worn
- party_morale_band: high
- resource_directions: distance:travelled, food:gained, health:fell, time_days:days passed, water:gained
- turn_matters: death=false, injury=true, supply_zero=false, landmark_arrival=true, night_at_camp=false
- the game's own lines: Arrived at Copperhill! Found water. +9 water. Traded at the settlement. +9 food. You made it! Victory!

### 4. Chronicler, pyrrhic ending (turn v2-w0-025)

- **ship** fell back after 3 attempt(s) (supply_state_contradiction); last rejected text: Party reaches Copperhill. Some lost. No food. No water. Trail ends.
- **haiku** fell back after 3 attempt(s) (personal_pronoun); last rejected text: The party reached Copperhill at last, the trail ended and the journey is over. Some of the company did not come through the forest with us.
- **opus** (attempt 1): The party reaches Copperhill and the end of the trail, fewer than set out, and the journey is over. Afternoon light falls thin through the pines, and the hungry wagon stops in mud beside a full water cask.
- **fable** fell back after 3 attempt(s) (repeated_opening); last rejected text: The wagon rolls into Copperhill and the trail ends, with fewer aboard than set out. The pines stand close and dripping in the afternoon light, and the hungry climb down slowly.

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

### 5. Chronicler, injury, no death (turn v2-w0-017)

- **ship** (attempt 1): The party travelled on. Snow drifts shift in the wind. A path cuts left. Footprints vanish.
- **haiku** (attempt 1): The party travelled on through the alpine cold and mud. Someone was hurt on the rough ground, and the camp at The Scar was reached in the dark.
- **opus** (attempt 2): The party travels on through the night, the wagon jolting over frozen stone toward The Scar, the last of the food and water passed hand to hand. Someone limps beside the wheel, worn and bruised, yet a low song rises against the cold wind.
- **fable** (attempt 1): The party travels on through the dark, eating and drinking from the stores, sore in every joint but oddly cheerful. The Scar offers thin air and loose stone underfoot.

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

### 6. Chronicler, night camp (turn v2-w0-010)

- **ship** (attempt 1): The party rested. Mud stains spread in the dark.
- **haiku** (attempt 1): The party rested at The Switchback through the night. Cold mud soaked the bedrolls and the fire burned low.
- **opus** (attempt 1): The party rests at The Switchback, burning firewood low and taking food and water by the wagon wheel. Wind combs the plains grass flat, and by morning the stiffness has eased from tired legs.
- **fable** (attempt 1): The party rests the night at The Switchback, burning firewood and eating well, and wakes the stronger for it. The river runs quiet below the grass, quieter than it ought.

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

- **ship** (attempt 1): Party arrives at Ashen Bluffs. Night wind stirs leaves. Firewood spent. Water gained.
- **haiku** (attempt 1): The party reached Ashen Bluffs at night under low cloud and steady drizzle. The forest opened onto a bare shelf of grey stone above the river.
- **opus** (attempt 1): The wagon reaches Ashen Bluffs in the dark, wheels sucking through cold mud beneath pale stone. Water is drawn from a seep, and the last kindling smokes low against an oddly quiet wood.
- **fable** (attempt 1): The wagon reaches Ashen Bluffs after dark, against the party's own rule, and nobody mentions it. Pale rock stands over the pines, and the water casks ride heavier than they did.

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

- **ship** (attempt 1): The party travelled on. Mud deepens. Firewood spent. Food spent. Water spent.
- **haiku** (attempt 1): The party travelled on through the night across the plains. Crow's Perch lay somewhere ahead in the dark.
- **opus** (attempt 1): The party travels on across the open plains near Crow's Perch, the wagon creaking through cold dark grass. Food, water, firewood and oil run thin, yet spirits hold strangely high.
- **fable** (attempt 1): The wagon rolls on across the flat dark grass toward Crow's Perch, wheels soft in the ruts. The wind drops and the plain goes quiet, and spirits hold well enough.

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

- **ship** (attempt 3): Medicine used. Camp stirs. Wind shifts. No sound from the west.
- **haiku** (attempt 1): The party used all the medicine at night in the forest at The Long Descent. Morale fell as the days wore on.
- **opus** (attempt 2): The camp spends the medicine down to the last of it, and the sick lie quiet beneath dripping pines on the long descent. Spirits sag as the days pass slowly in the wet forest dark.
- **fable** (attempt 1): All the medicine in camp is given out, and the box sits empty in the mud. The sickness eases slowly under dripping pines, and spirits sink.

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

- **ship** (attempt 1): The party travels on. Mud deepens. A leg moves in the track.
- **haiku** (attempt 1): The party travelled on through the evening mud at Widow's Pass. Spirits held despite the lame animal, and the plains stretched grey and wide ahead.
- **opus** (attempt 1): The party travels on toward Widow's Pass, chewing dry food and rationing water while the wheels grind through evening mud. A draught animal favors one foreleg, yet spirits hold, and someone hums low against the wind off the plains.
- **fable** (attempt 1): The wagon rolls on through the evening grass toward Widow's Pass, one animal favoring a foreleg. Food and water go down, and spirits somehow go up.

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

- **ship** (attempt 1): A traveller died. The Long Descent hums low in the swamp.
- **haiku** (attempt 2): A traveller has died in the swamp at The Long Descent this evening, and the rest of the party carries the loss in their shoulders. Mud sucks at the wheels and the oxen lean into the harness while the hungry family says little.
- **opus** (attempt 1): A traveller dies at evening on the road through The Long Descent, worn thin by hunger, and the party stands close around the wagon. Swamp water rises black along the ruts while someone straightens a collar that will not need straightening again.
- **fable** (attempt 1): A traveller dies of hunger on The Long Descent as evening settles over the swamp. The others walk on beside the wheels with shoulders drawn in, and nobody speaks of it.

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

- **ship** (attempt 1): The last of the party has died. Fog Hollow holds no light now.
- **haiku** (attempt 1): The last of the party has died and the trail ends here in Fog Hollow as evening settles over the swamp. Black water stands between the reeds and the oxen stand still in the mud, their breath rising in the damp air.
- **opus** (attempt 2): The last of the party is dead, and the journey ends here in Fog Hollow. Evening settles over the swamp, and the wheels sink quietly into the mud where no one walks beside the oxen.
- **fable** (attempt 1): The last of the party dies in the evening mud of Fog Hollow, and the journey ends here. The wagon sits quiet in the reeds while the fog settles low over the ruts.

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

### 13. Fireside, triumphant ending (turn v2-w0-023)

- **ship** fell back after 3 attempt(s) (ending_not_conveyed); last rejected text: The party stands at the edge of Ravenmoor where the plain ends and the sky turns deep. The oxen breathe slow in the wind.
- **haiku** (attempt 1): The party reached Ravenmoor at evening, the trail finally ending in the plains mud. Oxen leaned into their harness one last time as the wagon rolled past the first gate.
- **opus** fell back after 3 attempt(s) (unauthorised_resource_noun); last rejected text: The party rolls into Ravenmoor at evening, and the long trail ends beneath a low gold sky. The travellers ease down from the wagon, sore shoulders loosening, while the oxen stand quiet as if they know.
- **fable** (attempt 1): The wagon rolls into Ravenmoor at dusk and the trail ends here, the travellers limping but upright, shoulders finally coming down. Someone presses warm food and water into sore hands, and the old grass behind them keeps its own counsel.

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

- **ship** (attempt 3): The party reached Copperhill. The trail ends here. They have no food.
- **haiku** (attempt 1): The party reached Copperhill at the end of the trail, though some of its number were lost along the way and the journey is over.
- **opus** (attempt 1): The party reaches Copperhill in the afternoon, fewer than they set out, and the trail ends here among the dark pines. The travellers stand with hollow cheeks and bowed shoulders, and no one speaks of those left behind.
- **fable** fell back after 3 attempt(s) (repeated_opening); last rejected text: The wagon rolls into Copperhill and the trail ends here, with fewer travellers walking beside the wheels than set out. Afternoon light falls through the pines on thin shoulders, and nobody speaks of the empty places.

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

### 15. Fireside, injury, no death (turn v2-w0-073)

- **ship** (attempt 1): The party moves through Blind Canyon. The wind carries dust and silence.
- **haiku** (attempt 1): The party travelled on through the evening, wheels grinding in the damp plains soil at Blind Canyon. The oxen leaned into their yokes while the hungry travellers walked beside them, each one holding their shoulders against the cold wind.
- **opus** (attempt 1): The party travels on toward Blind Canyon, the oxen heavy-footed in the evening mud, hunger pressing hard on every traveller. Someone passes the last of the water hand to hand, and nobody mentions the empty place where a familiar voice should be.
- **fable** (attempt 1): The party travels on through the evening grass near Blind Canyon, shoulders bowed, bellies hollow, the water passed hand to hand without a word. The old rule says a hungry road listens, so the travellers keep their voices low.

Turn facts:

- what happened (the lead every model was given): The party travelled on.
- action: travel
- place: Blind Canyon; biome: plains; time_of_day: evening
- situation: Plains terrain. Early in the journey. A traveller is lost. They have no food. Their doctrine: no debts. Their taboo: no river water.
- party_health_band: critical
- party_morale_band: low
- resource_directions: distance:travelled, health:fell, morale:fell, time_days:days passed, water:spent
- health_effects: starvation, starvation, starvation
- turn_matters: death=false, injury=true, supply_zero=false, landmark_arrival=false, night_at_camp=false
- the game's own lines: Traveled 4 miles. 2 miles remaining.

### 16. Fireside, night camp (turn v2-w0-011)

- **ship** (attempt 1): The party hunted and brought back food. The Switchback holds a stillness that lingers in the wind.
- **haiku** (attempt 1): The hunt brought back meat tonight, and the spent cartridge still smells sharp in the cold air at The Switchback. The oxen stand close to the fire, and the party eats quietly, no one saying what they are all thinking about the river.
- **opus** (attempt 1): The party comes back from the hunt with food slung low and less ammunition in their pouches, shoulders loose and easy in the firelight.
- **fable** (attempt 1): The hunters come back to camp at The Switchback with meat across their shoulders and powder spent, laughing low in the dark. Every scrap is carried in from the grass, as the old rule asks, and the river keeps its own counsel nearby.

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

- **ship** (attempt 2): The party settles at Hazelwick where the wind hums through cracked stone. A single well stands half-buried in dust.
- **haiku** (attempt 1): The party reached Hazelwick in the morning, oxen steaming in the cool desert air. Their shoulders eased at the sight of the river-fed settlement, though the townsfolk watch them carefully.
- **opus** (attempt 1): The party rolls into Hazelwick under a pale morning sun, the oxen lowering their heads as the wheels grind through dry dust.
- **fable** (attempt 1): The party rolls into Hazelwick in the morning glare, tired in the shoulders but smiling, the oxen blowing dust. Shutters ease open a hand's width, and the townsfolk watch the wheels the way old folk watch a stranger's shadow.

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

- **ship** (attempt 1): The oxen move forward through the dry grass. Morning light stretches over the plain.
- **haiku** (attempt 1): The party travelled on through the morning, and the wagon wheels sank deep into the grey plains mud. Crow's Perch sits low on the grass, and the oxen leaned into the traces without complaint.
- **opus** (attempt 1): The party travels on through the morning grass toward Crow's Perch, the oxen leaning steady into their yokes. Spirits lift among the travellers as they spend the last of the lamp oil, and someone hums an old river tune.
- **fable** (attempt 1): The party travels on from Crow's Perch in the grey of morning, shoulders loose, the oxen leaning easy into wet grass. Somebody hums behind the wagon, though the last of the firewood is ash now and nobody says so.

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

### 19. Fireside, choice resolved (turn v2-w0-041)

- **ship** (attempt 1): Crows gather on the old pine. Their eyes hold no light.
- **haiku** (attempt 1): The party waved off the crows as idle talk and pressed on, but the shared unease sat heavy on every shoulder in Widow's Pass.
- **opus** (attempt 1): The party waves off the old crow-counting rule as superstition, yet shoulders stiffen and the laughter around the morning fire thins. Above Widow's Pass the black birds keep their places on the pine limbs, patient as neighbors who remember.
- **fable** (attempt 1): The travellers wave off the crows as old superstition and go back to breaking camp, though the laughter thins and shoulders stay tight. Above Widow's Pass the birds keep to the pines, quiet as the morning mist.

Turn facts:

- what happened (the lead every model was given): The party chose: Dismiss it as superstition.
- event_title: Counting Crows
- event_text: A line of crows watches from a fence. Someone counts them and goes pale.
- choice_taken: Dismiss it as superstition.
- place: Widow's Pass; biome: forest; time_of_day: morning
- situation: Forest terrain. Early in the journey. Their doctrine: travel light. Their taboo: leave nothing behind.
- party_health_band: steady
- party_morale_band: high
- resource_directions: morale:fell
- turn_matters: death=false, injury=false, supply_zero=false, landmark_arrival=false, night_at_camp=false
- the game's own lines: morale -2

### 20. Fireside, ordinary travel (turn v2-w0-018)

- **ship** (attempt 1): The party rested in the thin air of The Scar. Snow melted in the morning light, seeping into the stone beneath their feet.
- **haiku** (attempt 1): The party rested through the morning at The Scar while the oxen stood steaming in the thin alpine air. Food and water were drawn down, and by midday shoulders had loosened and a little colour returned to tired faces.
- **opus** (attempt 1): The party rests at The Scar this morning, sharing out food and water slowly while sore limbs loosen by the low fire. Cold alpine wind combs the rock above them, and the travellers sit a little straighter as the ache eases.
- **fable** (attempt 1): The party rests at The Scar through the cold morning, sharing food and water while sore shoulders loosen and quiet laughter returns. Thin alpine wind combs the stones above the wagon, patient as an old watcher.

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

- **ship** (attempt 1): A traveller died. The bridge shivers. The water holds no echo.
- **haiku** (attempt 1): A traveller has died on the swamp track at Broken Bridge, and the mud takes the sound of it without a ripple. The night holds the fire low and the crossing waits in black water.
- **opus** (attempt 1): A traveller dies in the night at Broken Bridge, thin from starvation, and the wheels sit still in the black swamp mud. The cold ash of the fire keeps its shape, and the water spent beside it ripples a moment before the wind arrives.
- **fable** (attempt 1): A traveller dies in the night, hunger finishing what the cold began. Near Broken Bridge the fire is out, and the swamp holds the dark close around the stilled wheels.

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

- **ship** (attempt 1): The last of the party has died. Sunken Meadow holds no echo of movement.
- **haiku** (attempt 1): The last of the party has died in the wet grass of Sunken Meadow, and the journey ends here. The plain stretches away under low grey cloud, and the mud keeps its own counsel.
- **opus** (attempt 1): The last of the party has died, and the journey ends here in the Sunken Meadow. The grass stands level all around the wagon, and the wind moves through it a moment before it arrives.
- **fable** (attempt 1): The last of the party has died of hunger, and the journey ends here in Sunken Meadow. The afternoon wind moves through the grass, and the wagon stands still in the mud.

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

### 23. Uncanny Bearer, triumphant ending (turn v2-w3-009)

- **ship** (attempt 1): The party reached Copperhill and the end of the trail. The journey is over.
- **haiku** (attempt 1): The party reaches Copperhill at evening, the end of the trail, and the wagon wheels finally stop turning in the mud.
- **opus** (attempt 2): The wagon rolls into Copperhill at evening and the trail ends here, the journey finished, the worn party lifted by it. The mud under the wheel holds still, and the last light lies flat across the plains a little longer than it should.
- **fable** fell back after 3 attempt(s) (repeated_opening); last rejected text: The wagon rolls into Copperhill at evening and the trail ends here, the journey finished, the party sore and worn but glad. The flat grass lies very still around the last ruts.

Turn facts:

- what happened (the lead every model was given): The party reached Copperhill and the end of the trail. The journey is over.
- action: travel
- place: Copperhill; biome: plains; time_of_day: evening
- ending: triumphant
- situation: Plains terrain. The end of the trail is near. Their doctrine: travel light. Their taboo: no travel at night.
- party_health_band: worn
- party_morale_band: high
- resource_directions: distance:travelled, food:gained, health:fell, time_days:days passed, water:gained
- turn_matters: death=false, injury=true, supply_zero=false, landmark_arrival=true, night_at_camp=false
- the game's own lines: Arrived at Copperhill! Found water. +9 water. Traded at the settlement. +9 food. You made it! Victory!

### (no turn found for pyrrhic ending)

### 24. Uncanny Bearer, injury, no death (turn v2-w0-015)

- **ship** (attempt 1): The party arrived at The Scar. The river bends in a way that does not match the map.
- **haiku** (attempt 3): The party arrived at The Scar as evening settled over the alpine slopes. Cold river wind cut across the wet stone and the locals watched from behind their doors.
- **opus** (attempt 1): The party arrives at The Scar in the evening, wheels grinding through cold mud, the gash in the mountainside lying open and slightly too straight for stone to have made it alone.
- **fable** (attempt 2): The wagon rolls into The Scar at evening, the party sore and limping but in good spirits, less food in the packs and fresh water in the casks.

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

### 25. Uncanny Bearer, night camp (turn v2-w0-012)

- **ship** (attempt 1): The party rested. The air hums with a geometry that does not close.
- **haiku** (attempt 1): The party rested through the night at Crow's Perch while the swamp breathed slow and wet around them. Food and water were drawn down, and by morning the sick ones looked a little less grey.
- **opus** (attempt 1): The party rests at Crow's Perch through the night, eating and drinking from their stores while the sick slowly mend. Swamp water laps the wheels with a sound that seems to finish just before it begins.
- **fable** (attempt 1): The party rests through the night at Crow's Perch, eating and drinking a little, and the sick breathe easier by morning. The swamp water lies flat around the camp, and the rain sounds slightly ahead of itself.

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

### 26. Uncanny Bearer, landmark arrival (turn v2-w0-027)

- **ship** (attempt 1): The party entered Fellgate. Trees bent in reverse, their trunks curving upward into the sky.
- **haiku** (attempt 1): The party arrived at Fellgate as the night wind gusted hard from the north. Mud clung to the wheels and the forest pressed close on every side.
- **opus** (attempt 1): The party arrives at Fellgate, the wagon creaking under the north wind, with less food in the sacks and fresh water sloshing in the casks. Beneath the pines the gate's shadow leans the wrong way, toward the wind instead of from the moon.
- **fable** (attempt 1): The wagon creaks into Fellgate after dark, lighter in food and heavier in water, the north wind gusting through the trees. The river below sounds closer than the slope allows.

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

### 27. Uncanny Bearer, supply at zero (turn v2-w0-050)

- **ship** (attempt 1): The party travelled on. The path curved where trees did not belong.
- **haiku** (attempt 1): The party travelled on through the forest at Fog Hollow as the morning mist thinned along the muddy track. Food and water ran low, and the fog kept pace beside them, pressing close without ever quite arriving.
- **opus** (attempt 2): The party travels on through Fog Hollow, wheels sinking in morning mud while the last of the food, water, and firewood goes. Mist hangs between the trunks at a height that does not match the ground beneath it.
- **fable** (attempt 2): The wagon rolls on through Fog Hollow in the grey morning, the last of the food eaten and the firewood and water drawn down. Between the trunks the mist hangs level as a shelf, and the wheels pass under it.

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

### 28. Uncanny Bearer, choice resolved (turn v2-w0-033)

- **ship** (attempt 1): The party passed Widow's Pass with no supplies. The forest breathed in reverse.
- **haiku** (attempt 1): The party hands over their supplies and the bandits melt back into the forest at Widow's Pass.
- **opus** (attempt 1): The party hands over ammunition, food, and water to the men blocking the road, and the wagon rolls on through Widow's Pass with spirits sinking. Morning light slants between the pines at an angle that seems borrowed from evening.
- **fable** (attempt 1): The party hands over food, water, and ammo to the men blocking the road, and the wagon rolls on lighter and quieter. At Widow's Pass the morning pines lean the same way, though the wind comes from the other side.

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

### 29. Uncanny Bearer, ordinary travel (turn v2-w0-022)

- **ship** (attempt 1): The party travelled on. The sun dipped low, bending light into slivers that did not meet the ground.
- **haiku** (attempt 1): The party travelled on through the desert afternoon, the wheels sinking and lifting in the pale sand. Hazelwick lies somewhere ahead, its roofs flickering in the heat like a reflection that arrived before the thing it reflects.
- **opus** (attempt 1): The party travels on through the dry afternoon, wheels grinding sand, food and water spent while spirits lift. Near Hazelwick the dunes lean slightly downhill in every direction at once.
- **fable** (attempt 1): The wagon rolls on through the sand past Hazelwick, food and water going down as the wheels turn. The afternoon shadows lean a little the wrong way, and spirits lift anyway.

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


---

## R&D reading (2026-11-13 20:58 ET, all 29 turns read against their facts)

- **The cloud models write the length that Standard asks for; the ship (qwen3:4b) often doesn't.** Ship lines are
  often Brief-length or clipped ("A leg moves in the track", "Mud deepens. Firewood spent."), and several say nothing
  about the turn: #15 (injury not conveyed), #18 (supply at zero not conveyed), #19 (the choice not conveyed: "Crows
  gather on the old pine"). This is what the fixes PR's "Standard adds 2 content words beyond the lead" and "choices
  conveyed" rules are for. Ship's Uncanny lines carry the voice well (#25, #26, #27).
- **Opus and Fable read best.** They carry the fact, place, time and the party's state in one or two sentences. Fable
  uses the party's taboo and doctrine correctly twice: #7 notes night travel "against the party's own rule" (taboo: no
  travel at night), and #16 has every scrap carried in "as the old rule asks" (taboo: leave nothing behind). Opus #15's
  "empty place where a familiar voice should be" is right: the facts list a traveller already lost.
- **Small inventions in the cloud lines,** none of them a false fact the checker forbids today: Fable #6 and Haiku #17
  add a river; Fable #15 invents an "old rule" (a hungry road listens) that isn't the party's doctrine; Haiku #13 adds
  "the first gate"; Haiku #5 says camp was reached (night_at_camp is false). Opus #7 "water drawn from a seep" is a
  detail, not a contradiction (water gained).
- **Fable's own repetition:** it opens "The wagon rolls into …" on most arrivals, so all 4 of its fallbacks here are
  repeated_opening (#3, #4, #14, #23). The 3-word rule in the fixes PR still catches this; that is a real habit, not a
  checker defect.
- **Haiku writes in the past tense** against the present-tense prompt, and is plainest of the three cloud models.
- **Count (my judgement, good = says what happened, true to the facts, reads well):** ship about 15/29, Haiku about
  22/29, Opus about 26/29, Fable about 24/29 shown (plus 4 good lines it lost to fallbacks). Direction only, n = 29.
