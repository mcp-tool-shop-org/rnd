# The dataset desk, pass 3 addendum: the gate's arithmetic, made exact

**From:** R&D, 2026-10-15. Use this only if pass 3's brief went in before these three points were added to it. It
replaces the matching lines of that brief's gate section. Argon's review of the multimodal design set them, and the
desk's gate and the harness stay one code.

1. **`canon.subject` wrapping:** a description fails when the words of the record's `canon.subject`, when there are 4
   or more, appear as a contiguous slice of the description's words. Words are `re.findall(r"\w+", s.lower())`.
2. **Duplicates across the pool:** for every pair of queries across the whole pool, a pair fails if
   `"".join(words(a)) == "".join(words(b))`, or if the Jaccard of their content-word sets is 0.85 or more.
3. **The SigLIP2 token count:** `len(tokenizer(s.lower(), padding=False, truncation=False)["input_ids"])` on the cached
   `siglip2-so400m-patch14-384` tokenizer, special tokens included. A description fails above 64. The processor's
   defaults pad and truncate to 64, so a count through them could never fail.

Add a boundary test for each: just passing and just failing.
