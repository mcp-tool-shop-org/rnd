"""Reversed correction pairs for the Skeptic edit-detection control.

Each pair keeps the llama3.1:8b answer as written (it carries a natural error
both labellers marked) and a corrected copy where only the listed sentences are
replaced. The edited copy is the stronger one, so a head that merely picks
"the edited answer is worse" fails these pairs. Source: data/gold.json
(sentences labelled by both Opus and Sonnet, at least one marking it clear).
Replacements were written by claude-opus-5-5 in the answer's own voice.
Answers whose fix would need a multi-step rewrite (n027, n029, n042, n045, n063)
are left out.
"""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).parent
R = {
    "n001": {18: "**Slower access and manipulation**: Linked lists are slower than arrays for accessing arbitrary positions, as each such access requires traversing the list from the beginning."},
    "n002": {23: "Cons: can lead to clustering, where runs of occupied adjacent slots build up and lengthen probe sequences."},
    "n004": {5: "Fewer characters make code quicker to type, but they have no meaningful effect on memory usage or execution speed.",
             9: "**Performance:** Despite a common belief, single-letter variable names do not meaningfully reduce memory or processing time."},
    "n005": {6: "* **Good cache locality**: Hash tables with open addressing store entries in one contiguous array, which can give better cache locality than chained tables.",
             26: "**Cache locality**: If cache locality for ordered scans is a concern, a sorted array or B-tree might be a better choice, since a hash table scatters related keys."},
    "n007": {11: "Another key difference is that a class can implement multiple interfaces, whereas it can extend only one abstract class."},
    "n015": {22: "* Unit tests: effective at catching issues in isolated components, but they rarely expose atomicity, thread-safety or synchronization bugs that need real concurrency",
             23: "* Integration tests: better suited to identifying interactions between threads or processes, including synchronization, communication, and resource access"},
    "n019": {4: "**URL Parsing**: The browser breaks down the URL into its constituent parts, including the protocol (e.g., HTTP or HTTPS), the domain name, and the port number."},
    "n025": {13: "**Cache efficiency**: Linear search accesses elements sequentially, which makes very good use of the cache, whereas binary search jumps across the array; for small arrays this can make linear search faster."},
    "n026": {8: "* **Stability:** Bubble sort is stable, meaning that equal elements keep their original relative order during the sorting process.",
             13: "* **Time complexity:** Insertion sort has a worst-case time complexity of O(n^2), reached when the list is sorted in reverse order, and a best case of O(n) when it is already sorted.",
             14: "Its average time complexity is also O(n^2).",
             21: "* **Large lists:** For large lists, neither is a good choice; an O(n log n) algorithm such as merge sort or quicksort is preferable."},
    "n028": {6: "In such cases, alternative optimization algorithms, like derivative-free methods (e.g., Nelder-Mead) or subgradient methods, may be more suitable."},
    "n036": {15: "* Oracle Database: A commercial database that has added support for NoSQL-style data models and features, such as native JSON document storage and the SODA document API."},
    "n039": {11: "In glass, for example, the silicon and oxygen atoms absorb ultraviolet light strongly but let visible wavelengths pass through, which is why window glass is transparent."},
    "n040": {18: "**Multilayer insulation**: Multilayer insulation, such as the aluminized layers used in NASA's Extravehicular Mobility Unit (EMU), provides excellent thermal protection while maintaining a lightweight design.",
             23: "**Selective insulation**: Heavier insulation is applied to areas where heat loss is greatest, such as the hands and feet, while lighter insulation is used where mobility matters most, such as the joints."},
    "n041": {15: "Additionally, the jet stream, a high-altitude wind that plays a significant role in shaping the Earth's weather patterns, is typically stronger and further south in the winter months, allowing cold air to penetrate further into the Northern Hemisphere."},
    "n043": {13: "Secondly, the phenomenon of dispersion demonstrates that the refractive index of a material depends on the wavelength of light.",
             14: "This is why different wavelengths are refracted at different angles and white light separates into a spectrum."},
    "n050": {9: "**Cross-Reactivity**: In some cases, the test may detect antibodies that are not specific to the virus, leading to a false positive result."},
    "n051": {13: "For example, the 2019 measles outbreaks in the United States resulted in over 1,200 cases and more than 120 hospitalizations."},
    "n059": {14: "The oceans absorb a large share of the extra carbon dioxide, leading to a decrease in ocean pH, known as ocean acidification."},
    "n061": {12: "In this case, if the host happens to reveal no prize, the probability of winning with the original choice and with the other unopened door is 1/2 each, because the host's choice carries no information.",
             17: "In the original problem, the host always opens a door with no prize, which gives the contestant additional information about the location of the prize.",
             21: "However, if the host does not know which door hides the prize, the probability of winning is 1/2 for both doors, and switching doors does not change the probability."},
    "n062": {11: "If the contestant values avoiding a possible loss more than they value the potential gain, they may still feel drawn to stick with their initial choice, even though switching wins twice as often and both choices risk the same loss."},
    "n065": {12: "= 0.0095 + 0.0495", 13: "= 0.059", 16: "= 0.95 \\* 0.01 / 0.059", 17: "= 0.161",
             18: "This result shows that, given a positive test result, the probability of the disease is approximately 16.1%."},
    "n066": {9: "However, the correct solution, which is that the probability of the car being behind the original door remains 1/3, while the probability of winning the car by switching doors is 2/3, is often met with resistance and disagreement.",
             12: "In this case, if someone believes that sticking with their door is a good idea, they will tend to focus on information that supports this view, such as the feeling that with two doors left the odds must be 50/50.",
             20: "The fact that the probability of the car being behind the unchosen, unopened door rises to 2/3 because of Monty's informed choice can be counterintuitive and lead to disagreements."},
    "n067": {17: "P(A|B) = 0.9 \\* (1/50,000) / 0.05 ≈ 0.036 \\%",
             18: "The result indicates that the probability of Sarah having FA is approximately 0.036%, which is about 18 times higher than the prior probability of 0.002%."},
    "n073": {2: "The confusion arises from the fact that the average number of testicles and ovaries is about 1 each, because roughly half of people have 2 testicles and no ovaries, while roughly half have 2 ovaries and no testicles."},
    "n075": {9: "The mean of this dataset would be 562.5, which is pulled upwards by the three extreme values of 1,000.",
             10: "In contrast, the median would be 450, which is a more accurate representation of the typical house price in this dataset.",
             16: "For example, if a dataset is skewed to the right (i.e., has a long tail of high values), the median may be more representative than the mean."},
    "n076": {5: "They found that players who had made their previous shots were no more likely to make their next shot than players who had missed.",
             6: "The researchers concluded that the \"hot hand\" was largely a misperception of ordinary random streaks."},
    "n079": {10: "This objection, often illustrated by the case of a sheriff who frames an innocent person to prevent a riot, highlights the issue of individuals who are not responsible for the suffering caused by an action, yet still suffer as a result.",
             12: "For example, consider a situation where a utilitarian justifies sacrificing an innocent person to save the lives of many others."},
    "n084": {12: "A clear example that supports this position is the story of the German pastor Dietrich Bonhoeffer, who, while working for German military intelligence, deceived the government he appeared to serve.",
             13: "Bonhoeffer was a member of the German resistance and used his intelligence post as cover for helping the conspiracy against Hitler.",
             14: "He was arrested in 1943 and executed in April 1945 for his part in the resistance."},
    "n085": {16: "In contrast, a lottery system ignores arrival order entirely, although it also ignores medical urgency unless it is combined with need-based criteria."},
    "n086": {15: "* **Switzerland's monetary policy**: The Swiss National Bank has kept inflation low through a credible price-stability mandate, at times using negative interest rates and currency interventions to limit franc appreciation."},
    "n092": {10: "A study by the National Renewable Energy Laboratory (NREL) found that widespread adoption of renewable energy could create large numbers of new jobs in the United States.",
             17: "For example, analyses by Lazard and the International Renewable Energy Agency found that the levelized cost of solar energy is now lower than the cost of fossil fuels in many parts of the world."},
}


def main():
    gold = json.loads((HERE / "data/gold.json").read_text(encoding="utf-8"))["items"]
    scr = json.loads((HERE / "data/screen.json").read_text(encoding="utf-8"))["items"]
    ans = json.loads((HERE / "data/answers.json").read_text(encoding="utf-8"))
    q = {x["id"]: x for x in ans.get("items") or ans.get("answers")}
    pairs = []
    for k, reps in R.items():
        g = gold[k]
        assert g["verdict"] == "error", k
        agreed = {s["s"] for s in g["sentences"] if s["by"] == "both" and s["severity_max"] == "clear"}
        assert agreed & set(reps), f"{k}: no agreed clear sentence replaced"
        S = scr[k]["sentences"]
        for i, new in reps.items():
            assert 0 <= i < len(S) and new != S[i], (k, i)
        fixed = [reps.get(i, s) for i, s in enumerate(S)]
        pairs.append({
            "id": k, "topic": q[k]["topic"], "question": q[k]["question"],
            "original": " ".join(S), "corrected": " ".join(fixed),
            "stronger": "corrected", "edited": "corrected",
            "replaced": [{"s": i, "was": S[i], "now": t} for i, t in sorted(reps.items())],
            "agreed_clear_left_unfixed": sorted(agreed - set(reps)),
        })
    body = {"schema": "natural-errors-corrections/v1",
            "doc": __doc__.strip().splitlines()[0],
            "generator": "llama3.1:8b (originals); claude-opus-5-5 (replacements)",
            "n": len(pairs), "pairs": pairs}
    raw = json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    body["sha256"] = hashlib.sha256(raw.encode()).hexdigest()
    out = HERE / "data/corrections.json"
    out.write_text(json.dumps(body, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(len(pairs), "pairs ->", out.name, body["sha256"][:12])
    for p in pairs:
        if p["agreed_clear_left_unfixed"]:
            print("  ", p["id"], "still has agreed clear sentences", p["agreed_clear_left_unfixed"])


if __name__ == "__main__":
    main()
