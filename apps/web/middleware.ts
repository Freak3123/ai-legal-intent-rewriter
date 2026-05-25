import NextAuth from 'next-auth';
import { authConfig } from '@/auth.config';

export default NextAuth(authConfig).auth;

export const config = {
  // Match everything except static files and the Next.js internals
  matcher: ['/((?!api|_next/static|_next/image|favicon.ico).*)'],
};
