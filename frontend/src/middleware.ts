import { NextRequest, NextResponse } from 'next/server'

const PUBLIC_PATHS = ['/login']

export function middleware(req: NextRequest) {
  const { pathname } = req.nextUrl
  if (PUBLIC_PATHS.some(p => pathname.startsWith(p))) return NextResponse.next()

  const token = req.cookies.get('tinhieu_token')?.value
    ?? req.headers.get('authorization')?.replace('Bearer ', '')

  // Token stored in localStorage can't be read server-side;
  // we rely on client-side redirect in api.ts for SPA pages.
  // This middleware guards direct URL access via cookie (optional).
  if (!token) {
    const url = req.nextUrl.clone()
    url.pathname = '/login'
    return NextResponse.redirect(url)
  }
  return NextResponse.next()
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico|login).*)'],
}
