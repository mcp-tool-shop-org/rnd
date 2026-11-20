<p align="center">
  <a href="README.ja.md">日本語</a> | <a href="README.zh.md">中文</a> | <a href="README.es.md">Español</a> | <a href="README.fr.md">Français</a> | <a href="README.md">English</a> | <a href="README.it.md">Italiano</a> | <a href="README.pt-BR.md">Português (BR)</a>
</p>

<p align="center">
  <img src="https://raw.githubusercontent.com/mcp-tool-shop-org/brand/main/logos/rnd/readme.png" alt="Research and Development" width="400">
</p>

<p align="center">
  <a href="https://github.com/mcp-tool-shop-org/rnd/actions/workflows/ci.yml"><img src="https://github.com/mcp-tool-shop-org/rnd/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="https://codecov.io/gh/mcp-tool-shop-org/rnd"><img src="https://codecov.io/gh/mcp-tool-shop-org/rnd/branch/main/graph/badge.svg" alt="Coverage"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="MIT License"></a>
  <a href="https://mcp-tool-shop-org.github.io/rnd/"><img src="https://img.shields.io/badge/Landing_Page-live-blue" alt="Landing Page"></a>
</p>

स्टूडियो का अनुसंधान बेंच। किसी भी क्षेत्र से प्राप्त निष्कर्षों को संक्षिप्त
मार्कडाउन प्रविष्टियों के रूप में तेजी से दर्ज किया जाता है, जिसमें प्रत्येक स्रोत को टैग किया जाता है और प्रत्येक दावे को जांचा गया या
नहीं के रूप में चिह्नित किया जाता है। प्रयोग उन प्रविष्टियों के बगल में रखे जाते हैं जिनका वे परीक्षण करते हैं। बाहरी कैटलॉग को
दर्शाया और मूल्यांकित किया जाता है, और एक रजिस्ट्री में स्टूडियो के उन उपकरणों की सूची होती है जिनका अनुसंधान उपयोग कर सकता है।
एक कमांड से यह सब खोजा जा सकता है।

## यह कहाँ स्थित है: readouts से पहले बेंच

दो भंडार स्टूडियो के ज्ञान को संग्रहीत करते हैं, और वे अलग-अलग कार्य करते हैं।

| | अनुसंधान और विकास (यह भंडार) | [readouts](https://github.com/mcp-tool-shop-org/readouts) |
|---|---|---|
| भूमिका | बेंच: जानकारी प्राप्त करना, प्रयोग, खुले प्रश्न | शेल्फ: सत्यापित ज्ञान आधार |
| गति | एक प्रविष्टि मिनटों में, दावे `unverified` से शुरू होते हैं | अध्ययन समूहों द्वारा निर्मित और जांचा गया |
| आकार | मार्कडाउन प्रविष्टियाँ, प्रत्येक में एक विषय | प्रत्येक डोमेन के लिए एक SQLite ज्ञान आधार |
| कितना अव्यवस्थित | जानबूझकर अव्यवस्थित: विवादित दावे, मृत अंत और अस्थायी परिणाम दृश्यमान रहते हैं | बिल्कुल भी अव्यवस्थित नहीं: प्रत्येक पंक्ति का स्रोत और सत्यापन किया गया है |

ज्ञान एक दिशा में बढ़ता है:

1. **बेंच।** एक निष्कर्ष यहां एक प्रविष्टि के रूप में दर्ज होता है। इसके दावे `[unverified]` से शुरू होते हैं, और उन्हें `[verified]` केवल इस नोट के साथ चिह्नित किया जाता है कि किस चीज़ ने उनकी जांच की।
हमारी अपनी मशीनों पर किए गए माप `rig` स्रोतों के रूप में दर्ज किए जाते हैं, और उनका हार्नेस `experiments/` के अंतर्गत होता है।
2. **आंतरिक शेल्फ।** एक बार जब किसी विषय के महत्वपूर्ण दावों का समर्थन किया जाता है, तो इसे
readouts के निजी कार्य भंडार में एक ज्ञान आधार के रूप में बनाया जाता है, या इसमें जोड़ा जाता है।
**प्रमोशन (शेल्फ में आगे बढ़ाना) किसी प्रयोग को समाप्त करने का एक हिस्सा है** (निदेशक, 2026-10-09)। जब
किसी प्रयोग का परिणाम यहां दर्ज किया जाता है, तो इसका readouts-internal अपडेट उसी सत्र में या अगले सत्र में, इसके चार्ट के साथ होता है। बेंच पर एक सप्ताह से अधिक समय तक कुछ भी नहीं रहता है। नियमित छोटे अपडेट, एक बड़े अपडेट से बेहतर होते हैं। किसी प्रयोग के README में इसके प्रमोशन को इसके परिणाम के नीचे एक पंक्ति के रूप में दर्ज किया जाता है: "प्रमोटेड: readouts-internal `<kb>` वेव `<n>`, `<date>`", या यदि अभी तक नहीं हुआ है, तो इसका कारण।
3. **सार्वजनिक शेल्फ।** जब किसी ज्ञान आधार को निर्यात अनुमति सूची में जोड़ा जाता है, तो इसे सार्वजनिक readouts भंडार में प्रकाशित किया जाता है।

`rnd readouts` यहां से प्रत्येक readouts ज्ञान आधार को खोजता है, इसलिए एक सीट दोनों भंडारों तक पहुंच प्रदान करती है। पहले बेंच को खोजें, फिर शेल्फ को, और फिर बची हुई कमी का अनुसंधान करें।

यहां किया गया अनुसंधान केवल स्टूडियो के अपने क्षेत्रों तक ही सीमित नहीं है। प्रत्येक प्रविष्टि दो चीजों को अलग-अलग रूप से दर्ज करती है: ज्ञान क्या है, और इसका स्टूडियो के लिए क्या अर्थ है (`relevance: act | watch | reference`)। `reference` एक अच्छा निष्कर्ष है।

## इसका उपयोग करें

इसके लिए पायथन 3.10 या उसके बाद का संस्करण और कुछ भी नहीं (केवल मानक लाइब्रेरी) की आवश्यकता होती है। यह विंडोज, macOS और लिनक्स पर चलता है। भंडार की रूट निर्देशिका से:

```bash
python -m rnd search cuda graphs            # full-text over entries + catalogues (stemmed: pair finds pairs)
python -m rnd search --exact PAIR           # whole words, same case: the product, not the word
python -m rnd probe https://github.com/NVIDIA/NeMo-Relay   # licence, release, telemetry hits, already in rnd?
python -m rnd show 2026-10-07-cuda-graphs   # one entry, with backlinks
python -m rnd list --relevance act          # what needs doing
python -m rnd tools                         # instruments this seat can use
python -m rnd readouts splice glitch --any  # search the readouts knowledge bases too
python -m rnd catalog lanes                 # NVIDIA skills by lane, with studio fit
python -m rnd catalog list --fit adjacent   # skills worth using when the need arises
python -m rnd new "Paper title" --kind paper --field audio --tag pitch
python -m rnd new-question "Why does X happen?" --field audio
python -m rnd sync --check                  # verify numbers bound to experiments/<id>/results.json
python -m rnd check                         # validate every file (exit 1 on errors)
python -m rnd sql "SELECT tier, count(*) FROM sources GROUP BY tier"
python -m rnd change "what changed"         # add a changelog fragment under changes/ (nano by default)
python -m rnd bump --note "release note"    # release PR: apply changes/ fragments, bump version + CHANGELOG
```

प्रत्येक लिस्टिंग कमांड एजेंटों के लिए `--json` स्वीकार करता है। `rnd.cmd` (विंडोज) और
`rnd.sh` (POSIX शेल) पतले रैपर हैं, इसलिए कमांड किसी भी निर्देशिका से काम करता है।

अन्य परियोजनाओं से उपकरण का उपयोग करने के लिए, इसे PyPI से स्थापित करें:

```bash
pip install mcptoolshop-rnd
```

यह `rnd` कमांड स्थापित करता है, लाइब्रेरी नहीं: प्रविष्टियाँ इस भंडार में मौजूद हैं। कमांड इस क्रम में एक लाइब्रेरी ढूंढता है: `--library DIR`, फिर
`$RND_ROOT`, फिर वर्तमान निर्देशिका से ऊपर या उसके बराबर निकटतम फ़ोल्डर जिसमें `entries/` और `instruments/` हों। लाइब्रेरी के बाहर, यह `NO_LIBRARY` के साथ समाप्त हो जाता है;
केवल `rnd readouts` इसके बिना काम करता है।

पायथन में, `mcptoolshop_rnd` आयात करें: यह नाम हमेशा काम करता है। `rnd` को संगतता उपनाम के रूप में रखा गया है, लेकिन एक असंबंधित PyPI पैकेज को भी `rnd` कहा जाता है, और यदि दोनों स्थापित हैं, तो यह उपनाम को बदल सकता है। `rnd` कमांड और
`python -m mcptoolshop_rnd` किसी भी तरह से काम करते रहते हैं।

लाइब्रेरी प्रतिदिन बदलती है, इसलिए संस्करणों में पांच खंड होते हैं, `MAJOR.MINOR.PATCH.MICRO.NANO`। पहले तीन खंड `rnd` उपकरण का संस्करण तय करते हैं; MICRO एक संरचनात्मक लाइब्रेरी परिवर्तन को दर्शाता है और NANO एक सामान्य अपडेट को। सामान्य अपडेट `rnd change` के माध्यम से `changes/` के अंतर्गत एक परिवर्तन लॉग अंश जोड़ते हैं; रिलीज़ के समय, `rnd bump` सभी अंशों का उपभोग करता है, उच्चतम अंश स्तर के अनुसार संस्करण को एक बार आगे बढ़ाता है, और एक CHANGELOG अनुभाग लिखता है।

निकास कोड: `0` ठीक · `1` अमान्य लाइब्रेरी फ़ाइलें · `2` उपयोग त्रुटि या नहीं मिला ·
`3` रनटाइम विफलता (एक बाहरी उपकरण, या एक अप्रत्याशित त्रुटि)। त्रुटियां एक कोड, एक संदेश और एक संकेत प्रिंट करती हैं; `--debug` ट्रेसबैक जोड़ता है।

## लेआउट

| पथ | क्या | कौन संपादित करता है |
|------|------|-----------|
| `entries/YYYY/*.md` | अनुसंधान प्रविष्टियाँ: सत्य का स्रोत | लोग और एजेंट |
| `questions/*.md` | खुले और उत्तरित अनुसंधान प्रश्न | लोग और एजेंट |
| `changes/*.md` | अप्रकाशित परिवर्तन लॉग खंड (`rnd change`) | लोग और एजेंट (`rnd bump` उपभोग करते हैं) |
| `experiments/<name>/` | हार्नेस, पिन किए गए इनपुट, `results.json`, और परिणाम रसीदें | लोग और एजेंट |
| `experiments/<name>/collect.json` | एक उपकरण भंडार से पिन किए गए कमिट पर एकत्र किए गए रिकॉर्ड (`rnd collect`) | लोग |
| `instruments/*.md` | स्टूडियो उपकरण और प्रोटोकॉल जिनका सीट उपयोग कर सकता है (`kind: instrument`) | केवल अनुसंधान और विकास सीट (समीक्षित अंतर) |
| `catalogs/<name>/source.json` | कैटलॉग कहां से आता है | लोग |
| `catalogs/<name>/catalog.json` | `rnd catalog sync` से पिन किया गया स्नैपशॉट | उत्पन्न; कभी भी हाथ से संपादित न करें |
| `catalogs/<name>/review.json` | परिवार और आइटम के अनुसार स्टूडियो फिट और नोट्स | लोग |
| `datapacks/<name>/spec.json` | एक डेटा पैक में क्या है: शामिल ग्लोब, लाइसेंस, जनरेटर, होस्ट | लोग |
| `datapacks/<name>/datapack.json` | `rnd datapack build` से मेनिफेस्ट: प्रत्येक फ़ाइल का SHA-256, लाइसेंस, पिन | उत्पन्न; कभी भी हाथ से संपादित न करें |
| `datapacks/<name>/hosted.json` | अपलोड कहां हुआ (भंडार संशोधन) | अपलोड के बाद |
| `mcptoolshop_rnd/` | सीएलआई | कोड |
| `rnd/` | `mcptoolshop_rnd` के लिए संगतता उपनाम | कोड |
| `rnd.db` | SQLite FTS5 इंडेक्स, जब फ़ाइलें बदलती हैं तो स्वचालित रूप से पुनर्निर्मित | उत्पन्न; गिट में नहीं |
| `rnd.misses.jsonl` | `rnd.db` के बगल में स्थानीय शून्य-हिट खोज लॉग (`RND_NO_USAGE=1` अक्षम करता है) | उत्पन्न; गिट में नहीं |

## प्रविष्टि प्रारूप

```markdown
---
id: 2026-10-07-cuda-graphs        # defaults to the file name
title: CUDA Graphs
date: 2026-10-07
kind: concept                     # finding concept release paper tool catalog rig-fact event question decision instrument
relevance: reference              # act | watch | reference
fields: [gpu-computing]           # any research field, open vocabulary
tags: [cuda-graphs, pytorch]
---

## Summary
## Key points
## Studio relevance
## Claims
- [unverified] A checkable statement.
- [verified] [c-a1b2c3d4] A checked statement. (via: what checked it, date)
## Sources
- [primary] https://… — publisher
```

- **स्रोत स्तर:** `primary` (विक्रेता दस्तावेज़, पेपर, भंडार), `secondary`
(विश्वसनीय लेख), `aggregator` (सारांश साइटें, एआई खोज आउटपुट),
`user` (किसी व्यक्ति द्वारा प्रदान किया गया: स्लाइड, नोट्स), `rig` (हमारे मशीनों पर मापा गया)।
- **दावे का आत्मविश्वास:** `unverified`, `verified`, `disputed`, `wrong`,
`superseded`। `verified` या `wrong` दावे को यह बताना चाहिए कि `(via: …)` के साथ इसकी जांच किसने की।
- `[[entry-id]]` प्रविष्टियों को जोड़ता है; `rnd show` बैकलिंक सूचीबद्ध करता है।

## परिवर्तन लॉग खंड

अपडेट `mcptoolshop_rnd/__init__.py` या `CHANGELOG.md` को सीधे संपादित नहीं करते हैं, इसलिए
समानांतर शाखाएँ संस्करण पंक्ति पर कभी भी टकराती नहीं हैं:

```bash
python -m rnd change "Add study of XYZ"                # writes changes/YYYY-MM-DD-<hex>-<slug>.md (level: nano)
python -m rnd change "New tool feature" --level minor  # levels: nano | micro | patch | minor | major
python -m rnd bump --dry-run                           # preview version bump from changes/ fragments
python -m rnd bump                                     # release PR: bump once, update CHANGELOG.md, delete fragments
```

`changes/` के अंतर्गत कोई फ़ाइलें नहीं होने पर, `rnd bump [nano|micro|…] [--note …]` अपनी
git-diff व्यवहार को बनाए रखता है। `rnd check` किसी भी गलत स्वरूपित अंश को त्रुटि के रूप में रिपोर्ट करता है।

## बाउंड संख्याएँ

एक प्रयोग सार्वजनिक रूप से सुरक्षित सारांश संख्याओं को `experiments/<id>/results.json` में रख सकता है और प्रविष्टियों, संक्षिप्त विवरणों या प्रयोग नोट्स में संख्याओं को सीधे शाब्दिक के बाद बांध सकता है:

```markdown
The judge scored 84.2%<!-- rnd:experiments/e4b/results.json#accuracy:.1% --> on the held-out split.
```

- रॉ मार्कडाउन, `grep` और SQLite इंडेक्स सादे शाब्दिक (`84.2%`) को बनाए रखते हैं; GitHub और स्टार्लाइट `84.2%` को बिना किसी दृश्यमान मार्कर या लिंक के प्रस्तुत करते हैं।
- `rnd sync [paths…]` `results.json` से बाउंड लिटरल को पायथन प्रारूप विनिर्देश का उपयोग करके फिर से लिखता है; यदि कोई भी शाब्दिक भिन्न है तो `rnd sync --check` कुछ भी लिखे बिना निकास कोड `1` के साथ समाप्त हो जाता है।
- `rnd check` किसी भी असंगत बाउंड शाब्दिक, गुम फ़ाइल या गुम कुंजी को त्रुटि के रूप में मानता है, और `[verified]` दावों पर चेतावनी देता है जिनके `(via: …)` नाम एक रिपो प्रयोग को इंगित करते हैं, जबकि अभी भी अनबाउंड संख्याएँ मौजूद हैं।

## दावा आईडी और लिंक

दावे स्थिर, नियतात्मक `c-<hex>` आईडी और आईडी द्वारा पुराने दावों के लिए स्पष्ट संबंध (`supersedes`, `contradicts`, `supports`) रख सकते हैं:

```bash
python -m rnd claims                               # list indexed claims (--state superseded, --json)
python -m rnd claims assign <entry>                # add deterministic c-<hex> ids to one entry's claims
python -m rnd reconcile <entry>                    # mark older claims (superseded / disputed / supported-by)
```

`rnd reconcile <entry>` केवल आईडी (यदि गुम है), अद्यतन स्थिति और व्युत्क्रम संबंध (`superseded-by`, `contradicted-by`, `supported-by`) को उस पुराने दावे की अपनी फ़ाइल में उसकी पंक्ति पर लिखता है, उसके वाक्य या किसी अन्य पंक्ति को स्पर्श किए बिना। `rnd check` टूटे हुए लक्ष्य आईडी या एकतरफा लिंक पर त्रुटि देता है और `rnd reconcile` चलाने का संकेत देता है। `rnd search` और `rnd show` `superseded` और `disputed` दावों को चिह्नित करते हैं और उस दावे का नाम बताते हैं जिसने उन्हें प्रतिस्थापित या खंडित किया।

## खुले प्रश्न

खुले प्रश्न `questions/` के अंतर्गत अलग-अलग मार्कडाउन फ़ाइलों के रूप में स्थिति `open`, `investigating`, `answered` या `parked` के साथ मौजूद हैं:

```bash
python -m rnd new-question "Does X hold on Y?" --field systems
python -m rnd questions --status open --json
```

जब किसी प्रश्न का `status` `answered` होता है, तो इसके फ्रंटमैटर `answered_by` सूची में कम से कम एक मौजूदा दावा आईडी का नाम होना चाहिए; `rnd check` मौजूदा दावा आईडी के बिना `answered` प्रश्न को त्रुटि के रूप में मानता है। प्रश्नों को `rnd.db` में अनुक्रमित किया जाता है और `rnd search` और `rnd show` द्वारा लौटाया जाता है।

## स्थानीय खोज-मिस लॉग

जब `rnd search` कोई मिलान नहीं लौटाता है, तो यह एक JSON पंक्ति (`time` और `query`) को `rnd.db` के बगल में एक स्थानीय `.misses.jsonl` फ़ाइल में जोड़ता है (`rnd.misses.jsonl` रिपो रूट में, git-अनदेखा; या `<db>.misses.jsonl` `--db` / `RND_DB` के बगल में)।
कुछ और रिकॉर्ड नहीं किया जाता है, कुछ भी नेटवर्क पर नहीं भेजा जाता है, `RND_NO_USAGE=1` लॉगिंग को बंद कर देता है, और फ़ाइल को हटाने से यह पूरी तरह से हट जाती है। `rnd stats --usage` कुल मिस गणना और सबसे अधिक बार बिना मिलान वाले (मिस हुए) प्रश्नों को प्रिंट करता है।

## उपकरण फ़ाइलें और वैकल्पिक अतिरिक्त

- **उपकरण फ़ाइलें (`instruments/*.md`):** केवल आर एंड डी सीट द्वारा एक समीक्षा किए गए अंतर में संपादित की जाती हैं, जिसके विवरण में प्रत्येक बदली गई उपकरण फ़ाइल सूचीबद्ध होती है, कभी भी किसी चरण या कमांड द्वारा नहीं जो बाहरी सामग्री का सारांश देता है (`rnd watch`, `rnd probe`, `rnd collect`, `rnd catalog sync`)।
- **मुख्य निर्भरताएँ और अतिरिक्त:** `rnd` का मुख्य भाग केवल पायथन मानक लाइब्रेरी है। कोई भी वैकल्पिक अतिरिक्त एक ऑप्ट-इन समूह में मौजूद होता है और आलसी रूप से आयात किया जाता है; एक कमांड जिसे किसी गुम अतिरिक्त की आवश्यकता होती है, वह `MISSING_EXTRA` और एक इंस्टॉलेशन संकेत के साथ विफल हो जाता है।

## डेटा पैक

प्रसंस्कृत डेटा जो क्लोन के लिए बहुत बड़ा या बहुत भारी है, उसे **डेटा पैक** के रूप में पेश किया जाता है: बाइट्स एक हगिंग फेस डेटासेट रिपो (प्रकाशित होने तक निजी) पर मौजूद होते हैं, और लाइब्रेरी केवल एक छोटा सा मेनिफेस्ट रखती है। अखंडता मॉडल [research-packs](https://github.com/mcp-tool-shop-org/research-packs) से आता है: एक मेनिफेस्ट, प्रत्येक फ़ाइल के लिए एक SHA-256, एक-कमांड सत्यापन और एक सूची।

```bash
rnd datapack build natural-errors --source experiments/natural-errors  # reads datapacks/natural-errors/spec.json
rnd datapack list
hf download mcp-tool-shop/rnd-natural-errors --repo-type dataset --local-dir ne
rnd datapack verify natural-errors --copy ne/files                      # PASS when every byte matches
```

- **प्रत्येक फ़ाइल को विनिर्देश में एक लाइसेंस की आवश्यकता होती है।** मॉडल आउटपुट अपने मॉडल की शर्तों को वहन करते हैं (उदाहरण के लिए, "लामा 3.1 आउटपुट के लिए 'लामा के साथ निर्मित' ")। `rnd datapack build` उस पैक को अस्वीकार कर देता है जो किसी फ़ाइल को बिना कवर के छोड़ देता है।
- **प्रत्येक जनरेटिंग मॉडल को पिन किया जाता है** (Ollama डाइजेस्ट, एचएफ संशोधन या एपीआई मॉडल आईडी), इसकी भूमिका के साथ।
- **`rnd check` प्रत्येक मेनिफेस्ट को मान्य करता है** और हाथ से संपादित किए गए पर विफल हो जाता है।
- अपलोड फ़ाइलों के बगल में `datapack.json` ले जाता है, ताकि कोई भी इस रिपो के बिना सत्यापित कर सके: `pip install mcptoolshop-rnd`।

## एकत्रित प्रयोग रिकॉर्ड

एक उपकरण रिपॉजिटरी अपने स्वयं के पूर्व-पंजीकृत विनिर्देशों और रन रिकॉर्ड (interlock की रसीदें) को प्रतिबद्ध करता है, जिस तरह से प्रत्येक रिपॉजिटरी अपने एटलस मानचित्र को प्रतिबद्ध करता है। लाइब्रेरी केवल संख्याओं की एक ट्रिम की गई प्रति प्रकाशित करती है, जिसे `rnd collect` द्वारा उपकरण रिपॉजिटरी से पिन किए गए कमिट पर बनाया जाता है:

```bash
rnd collect                 # list the experiments that collect records
rnd collect e4b             # read each source with git show, trim it, write experiments/e4b/results/
rnd collect e4b --check     # recompute every output; exit 1 if any differs from the committed file
```

- **`experiments/<name>/collect.json`** रिपॉजिटरी, उस सिबलिंग क्लोन का नाम देता है जिससे इसे पढ़ा जाता है (`--clone` ओवरराइड करता है), और प्रत्येक स्रोत: इसका पथ, कमिट, इसके बाइट्स का SHA-256, आउटपुट और प्रयोग के `extract.py` में ट्रिम फ़ंक्शन।
- **एक पिन किया गया स्रोत कभी नहीं बदलता है।** बाइट्स जो अब पिन से मेल नहीं खाते हैं, उन्हें अस्वीकार कर दिया जाता है।
- **प्रत्येक रिकॉर्ड में उत्पत्ति होती है:** रिपॉजिटरी, स्रोत पथ और ट्रिम किए गए बाइट्स का SHA-256।
- **प्रत्येक आउटपुट को लिखने से पहले सार्वजनिक रूप से सुरक्षित किया जाता है।** कोई भी मशीन पथ, होम निर्देशिका या पर्यावरण फ़ील्ड नहीं बचता है, और एक प्रयोग का मॉड्यूल एक सख्त गार्ड जोड़ सकता है। किसी भी इनकार पर कुछ भी नहीं लिखा जाता है।

## परीक्षण से पहले एक उपकरण की जांच करना

`rnd probe <url> …` प्रत्येक स्रोत के अपने एपीआई से एक उपकरण या मॉडल के बारे में पहले प्रश्नों का उत्तर देता है, न कि वेब पेज के सारांश से:

- **GitHub** (`gh api` के माध्यम से, इसलिए यह आपके GitHub CLI लॉगिन का उपयोग करता है): लाइसेंस, यह संग्रहीत है या नहीं, अंतिम पुश, नवीनतम रिलीज़ और "टेलीमेट्री" के लिए एक कोड खोज। एक हिट पढ़ने के लिए एक सुराग है, कभी भी प्रमाण नहीं; शून्य हिट भी प्रमाण नहीं है।
- **हगिंग फेस:** लाइसेंस टैग, या "अन्य" के लिए कार्ड का लाइसेंस नाम और लिंक; गेटिंग; अंतिम परिवर्तन।
- **PyPI और npm:** लाइसेंस, नवीनतम संस्करण और यह कब प्रकाशित किया गया था।
- **rnd स्वयं:** नाम के लिए एक सटीक-शब्द खोज, ताकि आप जान सकें कि लाइब्रेरी में यह पहले से मौजूद है या नहीं।

एक स्रोत जिसे नहीं पहुँचा जा सकता है, उसे अज्ञात के रूप में रिपोर्ट किया जाता है, साथ में इसका कारण भी।

## सूत्रों की निगरानी करना

`rnd watch` [docs/watchlist.json](docs/watchlist.json) में स्रोतों की जांच करता है और पिछली जांच के बाद से क्या नया है, इसकी रिपोर्ट करता है:

- एनवीडिया का तकनीकी ब्लॉग;
- CUDA टूलकिट संस्करण;
- एनवीडिया के नए हगिंग फेस मॉडल;
- एनवीडिया कौशल कैटलॉग;
- स्टूडियो द्वारा चलाए जा रहे इंजनों और उपकरणों की रिलीज़, जैसे Ollama, OpenVINO, PyTorch, ComfyUI और Claude Code।

```bash
python -m rnd watch                  # what's new; records what it saw
python -m rnd watch --no-save --json # look without recording
python -m rnd watch --only ollama    # one source
```

यह जो कुछ भी देखता है, उसे रिपॉजिटरी के बाहर एक स्टेट फ़ाइल में रखा जाता है (`$RND_WATCH_STATE`, अन्यथा `~/.rnd/watch-state.json`)।
किसी स्रोत की पहली जाँच एक आधारभूत जाँच होती है: यह वर्तमान आइटमों को रिकॉर्ड करता है और किसी भी नए आइटम की सूचना नहीं देता है। किसी प्री-रिलीज़ को कभी भी स्रोत के नवीनतम संस्करण के रूप में नहीं बताया जाता है; यदि कोई नया प्री-रिलीज़ हो तो उसे नवीनतम संस्करण के बगल में दिखाया जाता है। GitHub रिलीज़ नोट्स और कमिट संदेश JSON आउटपुट में रखे जाते हैं, ताकि पाठक को प्रत्येक पृष्ठ को अलग से प्राप्त न करना पड़े। एक ऐसा स्रोत जिसे
पहुंचा नहीं जा सकता है, उसे अज्ञात के रूप में बताया जाता है, और इसकी स्थिति को अपरिवर्तित छोड़ दिया जाता है ताकि चुपचाप कुछ भी छोड़ न दिया जाए।

यह कमांड एक साप्ताहिक अनुष्ठान का निश्चित हिस्सा है (निदेशक, 2026-10-13)। एक स्काउट नए आइटमों को पढ़ता है, किसी भी संभावित टूल का `rnd probe` के साथ परीक्षण करता है, `rnd search --exact` के साथ लाइब्रेरी की जाँच करता है, और एक संक्षिप्त क्रमबद्ध रिपोर्ट लिखता है: किसे प्रविष्टि के रूप में दर्ज करना है, किसे आज़माना है, और किसे छोड़ना है। पुल अनुरोध के माध्यम से एक स्रोत जोड़ें, और बताएं कि यह क्यों
महत्वपूर्ण है।

## अन्य स्टूडियो टूल से संबंध

- **readouts** वह सत्यापित शेल्फ है जिसे यह बेंच जानकारी प्रदान करता है (ऊपर देखें)।
- **research-os** एक विषय के लिए एक गेटेड, स्थिर साक्ष्य पैक बनाता है। एक विषय जिस पर
कोई निर्णय निर्भर करता है, वह research-os पैक में विकसित हो सकता है, जो प्रविष्टि से जुड़ा होता है।
- **repo-knowledge** स्टूडियो के अपने रिपॉजिटरी को अनुक्रमित करता है; यह लाइब्रेरी उन रिपॉजिटरी के बाहर के ज्ञान को कवर करती है।
- कुछ डिज़ाइन करते समय एकत्र की गई जानकारी भी यहाँ रखी जाती है, ताकि वे उस सत्र से भी अधिक समय तक मौजूद रहें जिसने उन्हें उत्पन्न किया।

पूर्ण उपकरण रजिस्ट्री के लिए `python -m rnd tools` देखें, और
स्टूडियो के वर्कफ़्लो मानकों के विरुद्ध वर्कफ़्लो कैसे स्कोर करता है, इसके लिए [docs/standards.md](docs/standards.md) देखें।

## सुरक्षा और विश्वास

- **उपयोग किया गया डेटा:** इस रिपॉजिटरी के अंदर की फ़ाइलें (`entries/`, `questions/`, `changes/`,
`instruments/`, `catalogs/`, `experiments/`), इंडेक्स `rnd.db` और इसका
संबंधित स्थानीय मिस लॉग `rnd.misses.jsonl`। `rnd readouts` readouts
ज्ञान आधारों को **केवल-पढ़ने के लिए** खोलता है। `rnd sql` केवल-पढ़ने के कनेक्शन पर चलता है।
- **उपयोग नहीं किया गया डेटा:** रिपॉजिटरी और readouts चेकआउट के बाहर कुछ भी नहीं। यह कोई क्रेडेंशियल संग्रहीत नहीं करता है और न ही कोई क्रेडेंशियल पढ़ता है।
- **नेटवर्क:** कोई नहीं, सिवाय `rnd catalog sync`, `rnd probe` और `rnd watch` के,
जो सार्वजनिक मेटाडेटा पढ़ते हैं या आपके अपने `gh` CLI लॉगिन के माध्यम से GitHub API को कॉल करते हैं जब आप उन्हें चलाते हैं।
- **अनुमतियाँ:** सामान्य फ़ाइल एक्सेस। कोई उन्नत अधिकार नहीं, कोई पृष्ठभूमि सेवा नहीं।
- **केवल-स्थानीय उपयोग लॉग:** कुछ भी एकत्र या कहीं भी नहीं भेजा जाता है। जब `rnd search`
कोई मिलान नहीं लौटाता है, तो यह `rnd.misses.jsonl` में एक पंक्ति (UTC समय और क्वेरी) जोड़ता है
`rnd.db` के बगल में (रिपॉजिटरी में git-ignored, या `<db>.misses.jsonl` `--db` /
`$RND_DB` के बगल में)। इसे बंद करने के लिए `RND_NO_USAGE=1` सेट करें, और किसी भी समय इसे साफ़ करने के लिए `.misses.jsonl` को हटा दें। कोई अन्य उपयोग डेटा रिकॉर्ड नहीं किया गया है।
- **सार्वजनिक रिपॉजिटरी स्वच्छता:** प्रत्येक पुश से पहले, होम-डायरेक्टरी पथ और ऑपरेटर पहचान के लिए ट्री को स्कैन किया जाता है।

[SECURITY.md](SECURITY.md) में वर्णित अनुसार कमजोरियों की रिपोर्ट करें।

## परीक्षण

```bash
bash verify.sh                               # tests, library check, index build, smoke
python -m unittest discover -s tests -t .    # tests only
```

## स्थिति और लाइसेंस

स्टूडियो द्वारा अनुरक्षित और दैनिक उपयोग में। कोड: [MIT](LICENSE)। प्रविष्टियाँ: CC BY 4.0। `catalogs/nvidia-skills/catalog.json` में NVIDIA कौशल दर्पण, उस परियोजना के लाइसेंसों के तहत [NVIDIA/skills](https://github.com/NVIDIA/skills) से कौशल नामों और विवरणों को पुन: प्रस्तुत करता है (कोड के लिए Apache-2.0, कौशल पाठ के लिए CC-BY-4.0)।

---

<p align="center">Built by <a href="https://mcp-tool-shop.github.io/">MCP Tool Shop</a></p>
