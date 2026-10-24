import rss from '@astrojs/rss';
import type { APIContext } from 'astro';
import { getCollection } from 'astro:content';
import sanitizeHtml from 'sanitize-html';
import chartPngs from '../../../public/charts/png-manifest.json';

// The newsletter's RSS 2.0 feed, at /rnd/newsletter/rss.xml: one item per issue, newest first, with the full issue
// in content:encoded so it reads in a feed reader. The HTML is the same render Starlight shows on the site
// (asides included), sanitised, with every link and image made absolute. Charts point at their PNG copies, since
// Gmail and Outlook don't show SVG and Buttondown sends this feed as email; scripts/render_chart_pngs.py makes them.
// For the same reason the HTML carries its own inline styles (asides, tables) and no classless <div>s, which
// Buttondown's editor can reject.
const TITLE = 'Research and Development: the newsletter';
const DESCRIPTION =
  "The studio's research newsletter: what we measured, and what it means. Each issue reports our experiments in " +
  'plain language, with the numbers, the charts, what held up and what didn\'t.';

type ChartPng = { png: string; width: number; height: number };
const CHART_PNGS: Record<string, ChartPng> = chartPngs;
// Shown at half the PNG's width: 600 px, an email column, so the 1200 px PNG is sharp on high-density screens.
const EMAIL_WIDTH = 600;

// A chart SVG under /charts/ becomes its PNG, sized for email; any other image is left as it is.
export function emailImage(src: string): { src: string; width?: string; height?: string } {
  const url = new URL(src);
  const match = url.pathname.match(/\/charts\/([^/]+\.svg)$/);
  const entry = match && CHART_PNGS[match[1]];
  if (!entry) return { src };
  url.pathname = url.pathname.replace(/[^/]+\.svg$/, entry.png);
  const height = Math.round((entry.height * EMAIL_WIDTH) / entry.width);
  return { src: url.href, width: String(EMAIL_WIDTH), height: String(height) };
}

// Inline styles for email, where the site's CSS doesn't travel. Text colour is set wherever a background is, so a
// client's dark mode can't put light text on the light tint.
const ASIDE_COLOURS: Record<string, [string, string]> = {
  note: ['#3b6fb6', '#eef3fa'],
  tip: ['#2f7d5b', '#edf6f1'],
  caution: ['#b4532a', '#fbf3ee'],
  danger: ['#b42a2a', '#fbeeee'],
};
const CELL = 'border:1px solid #c9ced6;padding:6px 10px;vertical-align:top';
const STYLES = {
  table: 'border-collapse:collapse;margin:12px 0',
  th: `${CELL};text-align:left;background:#f3f4f6;color:#1f2430`,
  td: CELL,
  asideTitle: 'margin:0 0 6px;font-weight:bold',
};

function asideStyle(className = ''): string {
  const kind = className.match(/starlight-aside--(\w+)/)?.[1] ?? 'note';
  const [edge, tint] = ASIDE_COLOURS[kind] ?? ASIDE_COLOURS.note;
  return `margin:16px 0;padding:10px 14px;border-left:4px solid ${edge};background:${tint};color:#1f2430`;
}

// pubDate: the end of the issue's day in UTC, or the build time if that is earlier, so a new issue is dated when
// it goes up and is never dated in the future.
export function issuePubDate(date: string, now: Date = new Date()): Date {
  const endOfDay = new Date(`${date}T23:59:59Z`);
  return endOfDay < now ? endOfDay : now;
}

export function absolutise(html: string, pageUrl: string): string {
  const fix = (url: string) => (url ? new URL(url, pageUrl).href : url);
  // Starlight's heading anchors carry screen-reader text ("Section titled …") that a feed reader would show.
  const bare = html.replace(/<a class="sl-anchor-link"[^>]*>[\s\S]*?<\/a>/g, '');
  return sanitizeHtml(bare, {
    // div is left out, so its wrappers (around headings, inside asides) are unwrapped and their content kept.
    allowedTags: sanitizeHtml.defaults.allowedTags.filter((t) => t !== 'div').concat(['img']),
    allowedAttributes: {
      ...sanitizeHtml.defaults.allowedAttributes,
      img: ['src', 'alt', 'title', 'width', 'height'],
      table: ['style'],
      th: ['align', 'colspan', 'rowspan', 'style'],
      td: ['align', 'colspan', 'rowspan', 'style'],
      aside: ['style'],
      p: ['style'],
      '*': ['id'],
    },
    transformTags: {
      table: (tagName, attribs) => ({ tagName, attribs: { ...attribs, style: STYLES.table } }),
      th: (tagName, attribs) => ({ tagName, attribs: { ...attribs, style: STYLES.th } }),
      td: (tagName, attribs) => ({ tagName, attribs: { ...attribs, style: STYLES.td } }),
      aside: (tagName, attribs) => ({ tagName, attribs: { ...attribs, style: asideStyle(attribs.class) } }),
      p: (tagName, attribs) => {
        const { style: _style, ...rest } = attribs;
        return (attribs.class ?? '').includes('starlight-aside__title')
          ? { tagName, attribs: { ...rest, style: STYLES.asideTitle } }
          : { tagName, attribs: rest };
      },
      a: (tagName, attribs) => ({ tagName, attribs: { ...attribs, href: fix(attribs.href) } }),
      img: (tagName, attribs) => ({
        tagName,
        attribs: attribs.src ? { ...attribs, ...emailImage(fix(attribs.src)) } : attribs,
      }),
    },
  });
}

export async function GET(context: APIContext) {
  // BASE_URL is '/rnd' with no trailing slash; without one, relative URLs below would resolve past it.
  const site = new URL(import.meta.env.BASE_URL.replace(/\/?$/, '/'), context.site);
  const feedUrl = new URL('newsletter/rss.xml', site).href;
  const issues = (await getCollection('docs'))
    .filter((d) => d.id.startsWith('newsletter/') && d.data.issue)
    .sort((a, b) => (b.data.issue ?? 0) - (a.data.issue ?? 0));

  return rss({
    title: TITLE,
    description: DESCRIPTION,
    site: site.href,
    xmlns: { atom: 'http://www.w3.org/2005/Atom', dc: 'http://purl.org/dc/elements/1.1/' },
    customData: [
      `<atom:link href="${feedUrl}" rel="self" type="application/rss+xml"/>`,
      '<language>en</language>',
      `<lastBuildDate>${new Date().toUTCString()}</lastBuildDate>`,
      '<ttl>720</ttl>',
      `<image><url>${new URL('rss-logo.png', site).href}</url><title>${TITLE}</title><link>${site.href}</link>` +
        '<width>144</width><height>144</height></image>',
    ].join(''),
    items: issues.map((issue) => {
      const link = new URL(`${issue.id}/`, site).href;
      return {
        title: `Issue ${issue.data.issue}: ${issue.data.title}`,
        link,
        pubDate: issuePubDate(issue.data.date),
        description: issue.data.description,
        content: absolutise(issue.rendered?.html ?? '', link),
        customData: '<dc:creator>mcp-tool-shop</dc:creator>',
      };
    }),
  });
}
