// next.config.mjs
/** @type {import('next').NextConfig} */
const nextConfig = {
  // Allow these origins to request dev-only assets like /_next/*
  allowedDevOrigins: [
    'localhost',
    '127.0.0.1',
    '192.168.1.68',   // your PC (if you open http://192.168.1.68:3000)
    '192.168.8.70',   // the host you’re actually using per the warning
    '*.local',        // optional: mDNS names like foo.local
    'local-origin.dev',
    '*.local-origin.dev',
  ],
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/api/:path*',
      },
    ]
  },
};

export default nextConfig;
