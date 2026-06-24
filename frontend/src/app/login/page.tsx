'use client'
import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { TrendingUp, Mail, KeyRound, ArrowRight, Loader2 } from 'lucide-react'
import { requestOTP, verifyOTP } from '@/lib/auth'

type Step = 'email' | 'otp'

export default function LoginPage() {
  const router = useRouter()
  const [step, setStep] = useState<Step>('email')
  const [email, setEmail] = useState('phuongnst@gmail.com')
  const [otp, setOtp] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [info, setInfo] = useState('')
  const [countdown, setCountdown] = useState(0)

  const startCountdown = () => {
    setCountdown(60)
    const t = setInterval(() => {
      setCountdown(c => {
        if (c <= 1) { clearInterval(t); return 0 }
        return c - 1
      })
    }, 1000)
  }

  const handleRequestOTP = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const msg = await requestOTP(email)
      setInfo(msg)
      setStep('otp')
      startCountdown()
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleVerifyOTP = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await verifyOTP(email, otp)
      router.push('/')
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleResend = async () => {
    if (countdown > 0) return
    setError('')
    setOtp('')
    setLoading(true)
    try {
      const msg = await requestOTP(email)
      setInfo(msg)
      startCountdown()
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-14 h-14 bg-green-500/10 rounded-2xl mb-4">
            <TrendingUp size={28} className="text-green-400" />
          </div>
          <h1 className="text-2xl font-bold text-white">TínHiệuCK</h1>
          <p className="text-sm text-gray-500 mt-1">Hệ thống tín hiệu chứng khoán VN</p>
        </div>

        <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6 shadow-xl">
          {step === 'email' ? (
            <>
              <h2 className="text-lg font-semibold mb-1">Đăng nhập</h2>
              <p className="text-sm text-gray-500 mb-5">
                Nhập email để nhận mã OTP xác thực.
              </p>
              <form onSubmit={handleRequestOTP} className="space-y-4">
                <div>
                  <label className="text-xs text-gray-500 block mb-1.5">Email</label>
                  <div className="relative">
                    <Mail size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
                    <input
                      type="email"
                      value={email}
                      onChange={e => setEmail(e.target.value)}
                      required
                      className="w-full pl-9 pr-4 py-2.5 bg-gray-800 border border-gray-700 rounded-lg text-sm focus:outline-none focus:border-green-500 transition-colors"
                      placeholder="email@gmail.com"
                    />
                  </div>
                </div>
                {error && <p className="text-red-400 text-sm">{error}</p>}
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full flex items-center justify-center gap-2 py-2.5 bg-green-600 hover:bg-green-500 disabled:opacity-50 rounded-lg text-sm font-semibold transition-colors"
                >
                  {loading
                    ? <><Loader2 size={15} className="animate-spin" /> Đang gửi...</>
                    : <><ArrowRight size={15} /> Gửi mã OTP</>
                  }
                </button>
              </form>
            </>
          ) : (
            <>
              <h2 className="text-lg font-semibold mb-1">Nhập mã OTP</h2>
              <p className="text-sm text-gray-500 mb-1">
                Mã 6 số đã được gửi tới
              </p>
              <p className="text-sm text-green-400 font-medium mb-5">{email}</p>
              {info && <p className="text-xs text-gray-500 bg-gray-800 rounded-lg px-3 py-2 mb-4">{info}</p>}
              <form onSubmit={handleVerifyOTP} className="space-y-4">
                <div>
                  <label className="text-xs text-gray-500 block mb-1.5">Mã OTP (6 số)</label>
                  <div className="relative">
                    <KeyRound size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
                    <input
                      type="text"
                      inputMode="numeric"
                      pattern="\d{6}"
                      maxLength={6}
                      value={otp}
                      onChange={e => setOtp(e.target.value.replace(/\D/g, ''))}
                      required
                      autoFocus
                      className="w-full pl-9 pr-4 py-2.5 bg-gray-800 border border-gray-700 rounded-lg text-sm font-mono tracking-[0.3em] focus:outline-none focus:border-green-500 transition-colors"
                      placeholder="000000"
                    />
                  </div>
                </div>
                {error && <p className="text-red-400 text-sm">{error}</p>}
                <button
                  type="submit"
                  disabled={loading || otp.length !== 6}
                  className="w-full flex items-center justify-center gap-2 py-2.5 bg-green-600 hover:bg-green-500 disabled:opacity-50 rounded-lg text-sm font-semibold transition-colors"
                >
                  {loading
                    ? <><Loader2 size={15} className="animate-spin" /> Đang xác thực...</>
                    : <><ArrowRight size={15} /> Đăng nhập</>
                  }
                </button>
                <div className="flex items-center justify-between text-xs text-gray-500">
                  <button
                    type="button"
                    onClick={() => { setStep('email'); setOtp(''); setError('') }}
                    className="hover:text-white transition-colors"
                  >
                    ← Đổi email
                  </button>
                  <button
                    type="button"
                    onClick={handleResend}
                    disabled={countdown > 0}
                    className="hover:text-white disabled:opacity-40 transition-colors"
                  >
                    {countdown > 0 ? `Gửi lại sau ${countdown}s` : 'Gửi lại mã'}
                  </button>
                </div>
              </form>
            </>
          )}
        </div>

        <p className="text-center text-xs text-gray-600 mt-6">
          Chỉ tài khoản được cấp quyền mới có thể đăng nhập.
        </p>
      </div>
    </div>
  )
}
