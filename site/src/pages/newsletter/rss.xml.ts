import rss from '@astrojs/rss';
import type { APIContext } from 'astro';
import { getCollection } from 'astro:content';
import sanitizeHtml from 'sanitize-html';

// The newsletter's RSS 2.0 feed, at /rnd/newsletter/rss.xml: one item per issue, newest first, with the full issue
// in content:encoded so it reads in a feed reader. The HTML is the same render Starlight shows on the site
// (asides included), sanitised, with every link and image made absolute.
const TITLE = 'Research and Development: the newsletter';
const DESCRIPTION =
  "The studio's research newsletter: what we measured, and what it means. Each issue reports our experiments in " +
  'plain language, with the numbers, the charts, what held up and what didn\'t.';
// RSS 2.0 wants an email address here; this is the studio's public no-reply address, not a person's.
const EDITOR = '64996768+mcp-tool-shop@users.noreply.github.com (mcp-tool-shop)';

export function absolutise(html: string, pageUrl: string): string {
  const fix = (url: string) => (url ? new URL(url, pageUrl).href : url);
  // Starlight's heading anchors carry screen-reader text ("Section titled …") that a feed reader would show.
  const bare = html.replace(/<a class="sl-anchor-link"[^>]*>[\s\S]*?<\/a>/g, '');
  return sanitizeHtml(bare, {
    allowedTags: sanitizeHtml.defaults.allowedTags.concat(['img']),
    allowedAttributes: {
      ...sanitizeHtml.defaults.allowedAttributes,
      img: ['src', 'alt', 'title', 'width', 'height'],
      th: ['align', 'colspan', 'rowspan'],
      td: ['align', 'colspan', 'rowspan'],
      '*': ['id'],
    },
    transformTags: {
      a: (tagName, attribs) => ({ tagName, attribs: { ...attribs, href: fix(attribs.href) } }),
      img: (tagName, attribs) => ({ tagName, attribs: { ...attribs, src: fix(attribs.src) } }),
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
      `<managingEditor>${EDITOR}</managingEditor>`,
      `<webMaster>${EDITOR}</webMaster>`,
      `<image><url>${new URL('rss-logo.png', site).href}</url><title>${TITLE}</title><link>${site.href}</link>` +
        '<width>144</width><height>144</height></image>',
    ].join(''),
    items: issues.map((issue) => {
      const link = new URL(`${issue.id}/`, site).href;
      return {
        title: `Issue ${issue.data.issue}: ${issue.data.title}`,
        link,
        pubDate: new Date(`${issue.data.date}T00:00:00Z`),
        description: issue.data.description,
        content: absolutise(issue.rendered?.html ?? '', link),
        customData: '<dc:creator>mcp-tool-shop</dc:creator>',
      };
    }),
  });
}
