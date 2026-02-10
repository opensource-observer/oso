import { NextResponse, type NextRequest } from "next/server";
import { createServerClient } from "@/lib/supabase/server";

export async function middleware(request: NextRequest) {
  const client = await createServerClient(request);

  const { data: userData } = await client.auth.getUser();

  if (request.nextUrl.pathname.startsWith("/beta")) {
    if (!userData?.user) {
      return NextResponse.redirect(new URL("/login", request.url));
    }
  }

  return NextResponse.next({
    request: {
      headers: request.headers,
    },
  });
}

export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     */
    "/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)",
  ],
};
