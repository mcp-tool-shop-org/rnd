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

स्टूडियो का अनुसंधान बेंच। किसी भी क्षेत्र से प्राप्त निष्कर्षों को संक्षिप्त मार्कडाउन प्रविष्टियों के रूप में तेजी से दर्ज किया जाता है, जिसमें प्रत्येक स्रोत को टैग किया जाता है और प्रत्येक दावे को जांचा गया या नहीं, के रूप में चिह्नित किया जाता है। प्रयोग उन प्रविष्टियों के बगल में रखे जाते हैं जिनका वे परीक्षण करते हैं। बाहरी कैटलॉग को मिरर किया जाता है और रेट किया जाता है, और एक रजिस्ट्री में स्टूडियो के उन उपकरणों की सूची होती है जिनका उपयोग अनुसंधान के लिए किया जा सकता है। एक कमांड से यह सब खोजा जा सकता है।

## यह कहाँ स्थित है: रीडिंग से पहले बेंच

दो भंडार स्टूडियो के ज्ञान को संग्रहीत करते हैं, और वे अलग-अलग कार्य करते हैं।

| | अनुसंधान और विकास (यह रिपॉजिटरी) | [readouts](https://github.com/mcp-tool-shop-org/readouts) |
|---|---|---|
| भूमिका | बेंच: इनपुट, प्रयोग, खुले प्रश्न | शेल्फ: सत्यापित ज्ञान आधार |
| गति | एक प्रविष्टि मिनटों में, दावे `unverified` से शुरू होते हैं | अध्ययन समूहों द्वारा निर्मित और जांचा गया |
| आकार | मार्कडाउन प्रविष्टियाँ, प्रत्येक में एक विषय | प्रत्येक डोमेन के लिए एक SQLite ज्ञान आधार |
| अव्यवस्था | अपेक्षित: विवादित दावे, मृत अंत और अंतरिम परिणाम दृश्यमान रहते हैं | कोई नहीं: पंक्तियों को स्रोत से प्राप्त किया जाता है और सत्यापित किया जाता है |

ज्ञान एक दिशा में आगे बढ़ता है:

1. **बेंच।** एक निष्कर्ष यहां एक प्रविष्टि के रूप में दर्ज होता है। इसके दावे `[unverified]` से शुरू होते हैं, और केवल यह नोट करके `[verified]` के रूप में चिह्नित किए जाते हैं कि उन्हें किसने जांचा। हमारे अपने मशीनों पर किए गए माप `rig` स्रोतों के रूप में दर्ज किए जाते हैं, और उनका उपयोग `experiments/` के तहत किया जाता है।
2. **आंतरिक शेल्फ।** एक बार जब किसी विषय के महत्वपूर्ण दावों का समर्थन किया जाता है, तो इसे रीडिंग के निजी कार्य रिपॉजिटरी में एक ज्ञान आधार के रूप में बनाया जाता है, या इसमें जोड़ा जाता है।
3. **सार्वजनिक शेल्फ।** जब किसी ज्ञान आधार को निर्यात अनुमति सूची में जोड़ा जाता है, तो इसे सार्वजनिक रीडिंग रिपॉजिटरी में प्रकाशित किया जाता है।

`rnd readouts` यहां से प्रत्येक रीडिंग ज्ञान आधार को खोजता है, इसलिए एक सीट दोनों भंडारों तक पहुंचती है। पहले बेंच खोजें, फिर शेल्फ, और फिर अंतर का अनुसंधान करें।

यहां किया गया अनुसंधान स्टूडियो के अपने क्षेत्रों तक सीमित नहीं है। प्रत्येक प्रविष्टि दो चीजों को अलग-अलग रिकॉर्ड करती है: ज्ञान क्या है, और इसका स्टूडियो के लिए क्या अर्थ है (`relevance: act | watch | reference`)। `reference` एक सटीक निष्कर्ष है।

## इसका उपयोग करें

इसके लिए पायथन 3.10 या उसके बाद का संस्करण और कुछ भी नहीं (केवल मानक लाइब्रेरी) की आवश्यकता होती है। यह विंडोज, मैकओएस और लिनक्स पर चलता है। रिपॉजिटरी रूट से:

```bash
python -m rnd search cuda graphs            # full-text over entries + catalogues
python -m rnd show 2026-10-07-cuda-graphs   # one entry, with backlinks
python -m rnd list --relevance act          # what needs doing
python -m rnd tools                         # instruments this seat can use
python -m rnd readouts splice glitch --any  # search the readouts knowledge bases too
python -m rnd catalog lanes                 # NVIDIA skills by lane, with studio fit
python -m rnd catalog list --fit adjacent   # skills worth using when the need arises
python -m rnd new "Paper title" --kind paper --field audio --tag pitch
python -m rnd check                         # validate every file (exit 1 on errors)
python -m rnd sql "SELECT tier, count(*) FROM sources GROUP BY tier"
```

प्रत्येक लिस्टिंग कमांड `--json` एजेंटों के लिए लेता है। `rnd.cmd` (विंडोज) और `rnd.sh` (POSIX शेल) पतले रैपर हैं, इसलिए कमांड किसी भी निर्देशिका से काम करता है।

निकास कोड: `0` ठीक · `1` अमान्य लाइब्रेरी फ़ाइलें · `2` उपयोग त्रुटि या नहीं मिला · `3` रनटाइम विफलता (एक बाहरी उपकरण, या एक अप्रत्याशित त्रुटि)। त्रुटियां एक कोड, एक संदेश और एक संकेत प्रिंट करती हैं; `--debug` ट्रेसबैक जोड़ता है।

## लेआउट

| पथ | क्या | कौन संपादित करता है |
|------|------|-----------|
| `entries/YYYY/*.md` | अनुसंधान प्रविष्टियाँ: सत्य का स्रोत | लोग और एजेंट |
| `experiments/<name>/` | उपकरण, पिन किए गए इनपुट और रिग माप के लिए परिणाम रसीदें | लोग और एजेंट |
| `instruments/*.md` | स्टूडियो उपकरण और प्रोटोकॉल जिनका उपयोग सीट कर सकती है (`kind: instrument`) | लोग और एजेंट |
| `catalogs/<name>/source.json` | कैटलॉग कहां से आता है | लोग |
| `catalogs/<name>/catalog.json` | `rnd catalog sync` से पिन किया गया स्नैपशॉट | उत्पन्न; कभी भी हाथ से संपादित नहीं किया जाता |
| `catalogs/<name>/review.json` | परिवार और आइटम के अनुसार स्टूडियो फिट और नोट्स | लोग |
| `rnd/` | सीएलआई | कोड |
| `rnd.db` | SQLite FTS5 इंडेक्स, जब फ़ाइलें बदलती हैं तो स्वचालित रूप से पुनर्निर्मित | उत्पन्न; गिट में नहीं |

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
- [verified] A checked statement. (via: what checked it, date)
## Sources
- [primary] https://… — publisher
```

- **स्रोत स्तर:** `primary` (विक्रेता दस्तावेज़, पेपर, रिपॉजिटरी), `secondary` (विश्वसनीय लेख), `aggregator` (सारांश साइटें, एआई खोज आउटपुट), `user` (किसी व्यक्ति द्वारा प्रदान किया गया: स्लाइड, नोट्स), `rig` (हमारे मशीनों पर मापा गया)।
- **दावे का आत्मविश्वास:** `unverified`, `verified`, `disputed`, `wrong`। `verified` या `wrong` दावे को यह बताना चाहिए कि `(via: …)` के साथ इसे किसने जांचा।
- `[[entry-id]]` प्रविष्टियों को जोड़ता है; `rnd show` बैकलिंक सूचीबद्ध करता है।

## अन्य स्टूडियो उपकरणों से संबंध

- **रीडिंग** वह सत्यापित शेल्फ है जिससे यह बेंच डेटा प्राप्त करता है (ऊपर देखें)।
- **रिसर्च-ओएस** एक विषय के लिए एक गेटेड, स्थिर साक्ष्य पैक बनाता है। एक ऐसा विषय जिस पर किसी निर्णय पर निर्भर है, वह एक रिसर्च-ओएस पैक में विकसित हो सकता है, जो प्रविष्टि से जुड़ा होता है।
- **रिपो-नॉलेज** स्टूडियो के अपने रिपॉजिटरी को अनुक्रमित करता है; यह लाइब्रेरी उनके बाहर के ज्ञान को कवर करती है।
- कुछ डिजाइन करते समय एकत्र किए गए निष्कर्ष भी यहां हैं, ताकि वे उस सत्र से आगे भी बने रहें जिसने उन्हें उत्पन्न किया।

पूर्ण उपकरण रजिस्ट्री के लिए `python -m rnd tools` देखें, और स्टूडियो के वर्कफ़्लो मानकों के खिलाफ वर्कफ़्लो कैसे स्कोर करता है, इसके लिए [docs/standards.md](docs/standards.md) देखें।

## सुरक्षा और विश्वास

- **स्पर्श किया गया डेटा:** इस रिपॉजिटरी के अंदर की फ़ाइलें (`entries/`, `instruments/`, `catalogs/`, `experiments/`) और इंडेक्स `rnd.db`, जिसे यह पुनर्निर्मित करता है। `rnd readings` opens the readouts knowledge bases **read-only**. `rnd sql` एक रीड-ओनली कनेक्शन के खिलाफ चलता है।
- **स्पर्श नहीं किया गया डेटा:** रिपॉजिटरी और रीडिंग चेकआउट के बाहर कुछ भी नहीं। यह कोई क्रेडेंशियल संग्रहीत नहीं करता है और कोई भी नहीं पढ़ता है।
- **नेटवर्क:** कोई नहीं, `rnd catalog sync` को छोड़कर, जो आपके अपने `gh` सीएलआई लॉगिन के माध्यम से जब आप इसे चलाते हैं तो GitHub API को कॉल करता है।
- **अनुमतियाँ:** सामान्य फ़ाइल एक्सेस। कोई उन्नत अधिकार नहीं, कोई पृष्ठभूमि सेवा नहीं।
- **कोई टेलीमेट्री नहीं।** कुछ भी एकत्र या भेजा नहीं जाता है।
- **सार्वजनिक रिपॉजिटरी स्वच्छता:** प्रत्येक पुश से पहले, होम-डायरेक्टरी पथ और ऑपरेटर पहचान के लिए ट्री को स्कैन किया जाता है।

[SECURITY.md](SECURITY.md) में वर्णित अनुसार कमजोरियों की रिपोर्ट करें।

## परीक्षण

```bash
bash verify.sh                               # tests, library check, index build, smoke
python -m unittest discover -s tests -t .    # tests only
```

## स्थिति और लाइसेंस

स्टूडियो द्वारा बनाए रखा गया और दैनिक उपयोग में। कोड: [MIT](LICENSE)। प्रविष्टियाँ: सीसी बीवाई 4.0। `catalogs/nvidia-skills/catalog.json` में NVIDIA कौशल दर्पण, उस परियोजना के लाइसेंसों के तहत [NVIDIA/skills](https://github.com/NVIDIA/skills) से कौशल नाम और विवरण को पुन: प्रस्तुत करता है (कोड के लिए Apache-2.0, कौशल पाठ के लिए CC-BY-4.0)।

---

<p align="center">Built by <a href="https://mcp-tool-shop.github.io/">MCP Tool Shop</a></p>
