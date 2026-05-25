import type { NextAuthConfig } from 'next-auth';

/**
 * Edge-runtime safe Auth.js config (no DB calls, no bcrypt).
 * Imported by middleware which runs on the Edge runtime.
 * The full config in auth.ts spreads this and adds the credentials provider.
 */
export const authConfig: NextAuthConfig = {
  pages: { signIn: '/login' },
  callbacks: {
    authorized({ auth, request: { nextUrl } }) {
      const isLoggedIn = !!auth?.user;
      const protectedPaths = ['/dashboard', '/upload'];
      const isProtected = protectedPaths.some((p) => nextUrl.pathname.startsWith(p));

      if (isProtected) {
        if (isLoggedIn) return true;
        return false; // redirect to /login
      }

      // If logged in, bounce away from auth pages
      if (isLoggedIn && (nextUrl.pathname === '/login' || nextUrl.pathname === '/signup')) {
        return Response.redirect(new URL('/dashboard', nextUrl));
      }

      return true;
    },
  },
  providers: [], // populated in auth.ts
};
