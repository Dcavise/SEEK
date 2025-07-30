import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { resolve } from 'path';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],

  // Path resolution to match tsconfig.json paths
  resolve: {
    alias: {
      '@': resolve(__dirname, './src'),
      '@/components': resolve(__dirname, './src/components'),
      '@/hooks': resolve(__dirname, './src/hooks'),
      '@/utils': resolve(__dirname, './src/utils'),
      '@/types': resolve(__dirname, './src/types'),
      '@/services': resolve(__dirname, './src/services'),
      '@/stores': resolve(__dirname, './src/stores'),
    },
  },

  // Development server configuration
  server: {
    port: 3000,
    host: true, // Allow external connections
    open: true, // Open browser on startup
    strictPort: true, // Exit if port is in use
    hmr: true, // Enable Hot Module Replacement
  },

  // Preview server configuration (for production builds)
  preview: {
    port: 3000,
    host: true,
    strictPort: true,
  },

  // Build configuration
  build: {
    target: 'ES2020',
    outDir: 'dist',
    sourcemap: true,

    // Rollup options for optimization
    rollupOptions: {
      output: {
        // Manual chunk splitting for better caching
        manualChunks: {
          vendor: ['react', 'react-dom'],
        },
      },
    },

    // Build optimizations
    minify: 'esbuild',
    chunkSizeWarningLimit: 1000,
  },

  // Define global constants (useful for environment variables)
  define: {
    __DEV__: JSON.stringify(process.env.NODE_ENV === 'development'),
  },

  // Optimize dependencies
  optimizeDeps: {
    include: ['react', 'react-dom'],
  },

  // CSS configuration for future Tailwind integration
  css: {
    devSourcemap: true,
  },
});
