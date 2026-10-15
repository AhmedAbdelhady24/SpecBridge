import { defineCollection } from 'astro:content';
import { glob } from 'astro/loaders';
import { docsSchema } from '@astrojs/starlight/schema';

export const collections = {
  docs: defineCollection({
    // Only plain Markdown is an export input; never compile generated MDX.
    loader: glob({ pattern: '**/[^_]*.md', base: './src/content/docs' }),
    schema: docsSchema(),
  }),
};
