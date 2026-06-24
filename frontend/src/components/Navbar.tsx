'use client'
import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import { TrendingUp, LogOut, User } from 'lucide-react'
import clsx from 'clsx'
import { useEffect, useState } from 'react'
import { getUser, clearSession, type User as AuthUser } from '@/lib/auth'

const links = [
  { href: '/', label: 'Dashboard' },
  { href: '/stocks', label: 'Cổ phiếu' },
  { href: '/backtest', label: 'Backtest' },
  { href: '/settings', label: 'Cài đặt' },
]

export default function Navbar() {
  const path = usePathname()
  const router = useRouter()
  const [user, setUser] = useState<AuthUser | null>(null)

  useEffect(() => { setUser(getUser()) }, [])

  const logout = () => {
    clearSession()
    router.push('/login')
  }

  if (path === '/login') return null

  return (
    <nav className="border-b border-gray-800 bg-gray-900">
      <div className="max-w-7xl mx-auto px-4 flex items-center gap-8 h-14">
        <Link href="/" className="flex items-center gap-2 font-bold text-green-400 text-lg shrink-0">
          <TrendingUp size={22} />
          TínHiệuCK
        </Link>
        <div className="flex gap-1 flex-1">
          {links.map(l => (
            <Link
              key={l.href}
              href={l.href}
              className={clsx(
                'px-3 py-1.5 rounded-md text-sm font-medium transition-colors',
                path === l.href
                  ? 'bg-gray-800 text-white'
                  : 'text-gray-400 hover:text-white hover:bg-gray-800'
              )}
            >
              {l.label}
            </Link>
          ))}
        </div>
        {user && (
          <div className="flex items-center gap-3 shrink-0">
            <div className="flex items-center gap-2 text-sm text-gray-400">
              <div className="w-7 h-7 rounded-full bg-green-500/20 flex items-center justify-center">
                <User size={14} className="text-green-400" />
              </div>
              <span className="hidden sm:block">{user.name}</span>
            </div>
            <button
              onClick={logout}
              className="flex items-center gap-1.5 px-2.5 py-1.5 text-xs text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg transition-colors"
            >
              <LogOut size={13} />
              Đăng xuất
            </button>
          </div>
        )}
      </div>
    </nav>
  )
}
