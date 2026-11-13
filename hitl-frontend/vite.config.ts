

import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig(({ mode }) => {
  // Load env file based on `mode` in the current working directory.
  const env = loadEnv(mode, process.cwd(), "");

  return {
    plugins: [react()],
    base: env.VITE_BASE_PATH || '/ai-workspace/',
    server: {
      host: "0.0.0.0",
      port: 5173,
      strictPort: true,
      allowedHosts: true,
      proxy: {
        "/api": {
          target: env.VITE_API_URL || "http://127.0.0.1:8012",
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api/, ""),
        },
      },
    },
  };
});

// import { defineConfig, loadEnv } from "vite";
// import react from "@vitejs/plugin-react";


// export default defineConfig({
//   plugins: [react()],
//   base: '/ai-workspace/',
//   server: {
//     host: "0.0.0.0",
//     port: 5173,
//     strictPort: true,
//     // Development only. Restrict this further when deploying.
//     allowedHosts: true,
//     proxy: {
//       "/api": {
//         target: "http://127.0.0.1:8012",
//         changeOrigin: true,
//         rewrite: (path) => path.replace(/^\/api/, ""),
//       },
//     },
//   },
// });


