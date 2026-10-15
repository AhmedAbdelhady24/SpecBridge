import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';

export default defineConfig({
  output: 'static',
  devToolbar: { enabled: false },
  integrations: [
    starlight({
      title: 'Project documentation',
    }),
  ],
});
