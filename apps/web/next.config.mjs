/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: 'standalone',
  poweredByHeader: false,
  eslint: {
    ignoreDuringBuilds: false,
  },
  typescript: {
    ignoreBuildErrors: false,
  },
  // Security headers for production clinical platform
  async headers() {
    return [
      {
        source: '/:path*',
        headers: [
          { key: 'X-DNS-Prefetch-Control', value: 'on' },
          { key: 'Strict-Transport-Security', value: 'max-age=63072000; includeSubDomains; preload' },
          { key: 'X-Frame-Options', value: 'DENY' },
          { key: 'X-Content-Type-Options', value: 'nosniff' },
          { key: 'X-XSS-Protection', value: '1; mode=block' },
          { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
          {
            key: 'Permissions-Policy',
            value: 'camera=(), microphone=(), geolocation=(), interest-cohort=()',
          },
          // CSP - hardened reference. 'unsafe-inline'/'unsafe-eval' required for Next.js + Tailwind in current setup.
          // Enterprise prod: implement nonce-based CSP via custom server/middleware or next-safe or strict-dynamic.
          // Remove 'http://localhost:*' and ws: for real deployments behind ALB/CloudFront + HTTPS only.
          {
            key: 'Content-Security-Policy',
            value: "default-src 'self'; script-src 'self' 'unsafe-eval' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self' https: http://localhost:* ws: wss:; frame-ancestors 'none'; base-uri 'self'; form-action 'self';",
          },
          // Report CSP violations in prod (set up /api/csp-report endpoint or external collector)
          // { key: 'Content-Security-Policy-Report-Only', value: "..." },
        ],
      },
    ];
  },
};

export default nextConfig;
