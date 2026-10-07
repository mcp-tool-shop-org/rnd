import type { SiteConfig } from '@mcptoolshop/site-theme';

export const config: SiteConfig = {
  title: 'Research and Development',
  description:
    "The studio's research bench: tiered-source Markdown entries, rig experiments, a searchable SQLite index, an instrument registry and rated external catalogues.",
  logoBadge: 'RD',
  brandName: 'rnd',
  repoUrl: 'https://github.com/mcp-tool-shop-org/rnd',
  footerText:
    'MIT Licensed (code) · CC BY 4.0 (entries) — built by <a href="https://mcp-tool-shop.github.io/" style="color:var(--color-muted);text-decoration:underline">MCP Tool Shop</a>',

  hero: {
    badge: 'Open research · Python 3.10+, no dependencies',
    headline: 'The research bench.',
    headlineAccent: 'Readouts is the shelf.',
    description:
      'Findings from any field land here fast, with every source tagged by tier and every claim marked as checked or not. Rig experiments sit beside the entries they test. When a topic holds up, it moves on to <a href="https://github.com/mcp-tool-shop-org/readouts">readouts</a>, the verified knowledge bases.',
    primaryCta: { href: '#use-it', label: 'See the commands' },
    secondaryCta: { href: 'handbook/', label: 'Read the Handbook' },
    previews: [
      { label: 'Search', code: 'python -m rnd search cuda graphs' },
      { label: 'Both stores', code: 'python -m rnd readouts splice glitch --any' },
      { label: 'File', code: 'python -m rnd new "Paper title" --kind paper --field audio' },
    ],
  },

  sections: [
    {
      kind: 'features',
      id: 'features',
      title: 'What it holds',
      subtitle: 'Messy on purpose, and honest about it.',
      features: [
        {
          title: 'Tiered sources',
          desc: 'Every source is primary, secondary, aggregator, user or rig. AI search output is never passed off as primary.',
        },
        {
          title: 'Claims carry their checks',
          desc: 'A claim is unverified until something checks it, and a verified claim names what did. Disputed and wrong claims stay visible.',
        },
        {
          title: 'Rig experiments',
          desc: 'Measurements made on our own machines keep their harness, pinned inputs and result receipts under experiments/.',
        },
        {
          title: 'One search, two stores',
          desc: 'rnd searches the bench, and rnd readouts searches every verified knowledge base, read-only, from the same seat.',
        },
        {
          title: 'Instrument registry',
          desc: 'The studio tools research can call on (study swarms, evidence packs, local models, rented GPUs) with how to invoke each.',
        },
        {
          title: 'Rated catalogues',
          desc: 'External catalogues such as NVIDIA’s 398 agent skills, pinned to a commit and rated for studio fit.',
        },
      ],
    },
    {
      kind: 'data-table',
      id: 'pipeline',
      title: 'From bench to shelf',
      subtitle: 'Knowledge moves one way.',
      columns: ['Stage', 'Where', 'What happens'],
      rows: [
        ['Bench', 'rnd (this repo)', 'A finding lands as an entry; claims start unverified; rig measurements get a harness.'],
        ['Internal shelf', 'readouts, private working repo', 'A topic whose load-bearing claims hold up is built into a knowledge base, or added to one.'],
        ['Public shelf', 'readouts, public repo', 'A knowledge base is published when it joins the export allow-list.'],
      ],
    },
    {
      kind: 'code-cards',
      id: 'use-it',
      title: 'Use it',
      cards: [
        {
          title: 'Search before you research',
          code: 'python -m rnd search cuda graphs\npython -m rnd readouts listener --any\npython -m rnd tools',
        },
        {
          title: 'File and validate',
          code: 'python -m rnd new "Title" --kind finding --field audio\npython -m rnd check   # exit 1 on any error',
        },
        {
          title: 'Ask the index',
          code: 'python -m rnd list --relevance act\npython -m rnd stats --json\npython -m rnd sql "SELECT tier, count(*) FROM sources GROUP BY tier"',
        },
        {
          title: 'Verify the repo',
          code: 'bash verify.sh   # tests, check, build, smoke',
        },
      ],
    },
  ],
};
