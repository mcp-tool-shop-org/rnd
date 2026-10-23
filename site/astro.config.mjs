// @ts-check
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';
import tailwindcss from '@tailwindcss/vite';

// https://astro.build/config
export default defineConfig({
  site: 'https://mcp-tool-shop-org.github.io',
  base: '/rnd',
  integrations: [
    starlight({
      title: 'Research and Development',
      description: "The studio's research bench: entries, experiments, instruments and catalogues.",
      logo: {
        src: './src/assets/logo.png',
        alt: 'Research and Development',
        href: '/rnd/',
        replacesTitle: false,
      },
      disable404Route: true,
      // Lets feed readers and browsers find the newsletter feed from any page.
      head: [
        {
          tag: 'link',
          attrs: {
            rel: 'alternate',
            type: 'application/rss+xml',
            title: 'Research and Development: the newsletter',
            href: '/rnd/newsletter/rss.xml',
          },
        },
      ],
      social: [
        { icon: 'github', label: 'GitHub', href: 'https://github.com/mcp-tool-shop-org/rnd' },
      ],
      sidebar: [
        {
          label: 'Research briefs',
          items: [{ autogenerate: { directory: 'briefs' } }],
        },
        {
          label: 'Newsletter',
          items: [{ autogenerate: { directory: 'newsletter' } }],
        },
        {
          label: 'The watch (weekly)',
          items: [{ autogenerate: { directory: 'watch' } }],
        },
        {
          label: 'Using the bench',
          items: [{ autogenerate: { directory: 'handbook' } }],
        },
      ],
      customCss: ['./src/styles/starlight-custom.css'],
    }),
  ],
  vite: {
    plugins: [tailwindcss()],
  },
});
