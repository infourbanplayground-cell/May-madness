import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl

  // Public routes — no auth required
  if (
    pathname.startsWith('/book') ||
    pathname === '/account/login' ||
    pathname === '/account/register' ||
    pathname.startsWith('/api/account/') ||
    pathname.startsWith('/api/courts/') ||
    pathname.startsWith('/api/auth/')
  ) {
    return NextResponse.next()
  }

  // Member-only routes
  if (pathname.startsWith('/account')) {
    const memberSession = request.cookies.get('member_session')
    if (!memberSession) {
      return NextResponse.redirect(
        new URL(`/account/login?next=${encodeURIComponent(pathname)}`, request.url)
      )
    }
    return NextResponse.next()
  }

  // Admin routes — everything else
  const session = request.cookies.get('admin_session')
  if (!session || session.value !== 'authenticated') {
    if (pathname !== '/login') {
      return NextResponse.redirect(new URL('/login', request.url))
    }
  } else if (pathname === '/login') {
    return NextResponse.redirect(new URL('/', request.url))
  }

  return NextResponse.next()
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico).*)'],
}
