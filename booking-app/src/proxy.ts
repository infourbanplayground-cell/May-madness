import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl

  if (pathname.startsWith('/api/auth')) return NextResponse.next()

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
