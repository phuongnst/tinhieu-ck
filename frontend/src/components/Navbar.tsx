'use client'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { TrendingUp } from 'lucide-react'
import clsx from 'clsx'

const links = [
  { href: '/', label: 'Dashboard' },
  { href: '/stocks', label: 'Cổ phiếu' },
  { href: '/backtest', label: 'Backtest' },
  { href: '/settings', label: 'Cài đặt' },
]

export default function Navbar() {
  const path = usePathname()
  return (
    <nav className="border-b border-gray-800 bg-gray-900">
      <div className="max-w-7xl mx-auto px-4 flex items-center gap-8 h-14">
        <Link href="/" className="flex items-center gap-2 font-bold text-green-400 text-lg">
          <TrendingUp size={22} />
          TínHiệuCK
        </Link>
        <div className="flex gap-1">
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
      </div>
    </nav>
  )
}
