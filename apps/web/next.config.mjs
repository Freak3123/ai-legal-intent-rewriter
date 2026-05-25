/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // pdfjs-dist 5.x ESM is rejected by Next's default treatment of node_modules;
  // running it through the standard transpile pipeline avoids the
  // "Object.defineProperty called on non-object" error during init.
  transpilePackages: ['pdfjs-dist'],
  experimental: {
    // Allow large file uploads to API routes (for OCR fallback path)
    serverActions: {
      bodySizeLimit: '10mb',
    },
  },
};

export default nextConfig;
