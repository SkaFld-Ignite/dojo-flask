/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    appDir: true,
  },
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
    NEXT_PUBLIC_WS_URL: process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000',
  },
  // Static export for DigitalOcean App Platform
  output: 'standalone', // For Kubernetes deployment
  trailingSlash: true,
  images: {
    unoptimized: true, // Required for static export
  },
  async rewrites() {
    // Only use rewrites in development for local API proxying
    if (process.env.NODE_ENV === 'development') {
      return [
        {
          source: '/api/:path*',
          destination: `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/:path*`,
        },
        {
          source: '/socket.io/:path*',
          destination: `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/socket.io/:path*`,
        },
      ];
    }
    return [];
  },
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          {
            key: 'X-Frame-Options',
            value: 'DENY',
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
          {
            key: 'Referrer-Policy',
            value: 'strict-origin-when-cross-origin',
          },
        ],
      },
    ];
  },
  // Optimize for production
  poweredByHeader: false,
  compress: true,
  images: {
    domains: ['localhost'],
    unoptimized: false,
  },
  // Support for AI model files if needed
  webpack: (config, { isServer }) => {
    // Ignore large model files during build
    config.module.rules.push({
      test: /\.(bin|pt|safetensors)$/,
      use: {
        loader: 'ignore-loader',
      },
    });

    return config;
  },
}

module.exports = nextConfig
