import { defineCollection } from 'astro:content';
import { z } from 'astro/zod';
import { docsLoader } from '@astrojs/starlight/loaders';
import { docsSchema } from '@astrojs/starlight/schema';

// Newsletter issues and research briefs carry a little extra front matter, read by the landing page.
export const collections = {
  docs: defineCollection({
    loader: docsLoader(),
    schema: docsSchema({
      extend: z.object({
        issue: z.number().optional(),
        // YAML reads 2026-10-09 as a Date; keep it as the plain ISO day.
        date: z
          .union([z.string(), z.date()])
          .transform((d) => (typeof d === 'string' ? d : d.toISOString().slice(0, 10)))
          .optional(),
        highlights: z.array(z.string()).optional(),
        status: z.string().optional(),
        shelf: z.string().optional(),
      }),
    }),
  }),
};
