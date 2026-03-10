import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

/**
 * Next.js Edge Middleware
 *
 * WHY IS THIS PASS-THROUGH?
 * The refresh_token cookie has path="/auth" (so it's only sent to backend
 * /auth/* endpoints). The Edge Middleware runs on ALL routes and can't
 * see that cookie. Rather than widening the cookie scope (which is a
 * security anti-pattern), we let the client-side AuthContext + ProtectedRoute
 * handle all auth redirects.
 *
 * Auth flow:
 *   1. AuthContext does a silent refresh on mount → sets in-memory token
 *   2. ProtectedRoute checks the AuthContext → redirects to /login if no user
 *   3. Axios interceptor retries 401s with a token refresh
 */
export function middleware(request: NextRequest) {
  // Pass through — auth is handled client-side
  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!_next|favicon.ico|api).*)"],
};
