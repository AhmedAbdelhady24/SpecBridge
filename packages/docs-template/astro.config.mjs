import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';

export default defineConfig({
  output: 'static',
  devToolbar: { enabled: false },
  vite: {
    server: {
      watch: {
        ignored: ['**/*.log'],
      },
    },
  },
  integrations: [
    starlight({
      title: 'Project documentation',
    }),
  ],
});
