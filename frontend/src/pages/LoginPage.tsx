import React, { useState } from 'react';
import { useAuthStore } from '../stores';
import { Hexagon, Shield, Eye, EyeOff, Lock, Mail, ArrowRight, AlertTriangle } from 'lucide-react';

export const LoginPage: React.FC = () => {
  const { login, verifyMFA, mfaPendingUser, setMfaPending } = useAuthStore();
  const [email, setEmail] = useState('lakshaysoni@cybercrime.gov.in');
  const [password, setPassword] = useState('SecurePass@2026');
  const [showPassword, setShowPassword] = useState(false);
  const [otpDigits, setOtpDigits] = useState<string[]>(['', '', '', '', '', '']);
  const [activeSlot, setActiveSlot] = useState<number>(0);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const inputRefs = React.useRef<(HTMLInputElement | null)[]>([]);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim() || !password.trim()) {
      setError('Please enter both email address and password.');
      return;
    }

    setIsLoading(true);
    setError('');

    const success = await login(email, password);
    if (!success) {
      setError('Invalid officer credentials. Enter lakshaysoni@cybercrime.gov.in and SecurePass@2026.');
    }
    setIsLoading(false);
  };

  const handleDigitChange = (index: number, value: string) => {
    const cleanVal = value.replace(/\D/g, '');
    if (!cleanVal) {
      const nextDigits = [...otpDigits];
      nextDigits[index] = '';
      setOtpDigits(nextDigits);
      return;
    }

    if (cleanVal.length > 1) {
      // Pasted full OTP
      const pasted = cleanVal.slice(0, 6).split('');
      const nextDigits = ['', '', '', '', '', ''];
      pasted.forEach((ch, idx) => { nextDigits[idx] = ch; });
      setOtpDigits(nextDigits);
      const targetIdx = Math.min(pasted.length, 5);
      inputRefs.current[targetIdx]?.focus();
      return;
    }

    const nextDigits = [...otpDigits];
    nextDigits[index] = cleanVal;
    setOtpDigits(nextDigits);

    if (index < 5) {
      inputRefs.current[index + 1]?.focus();
    }
  };

  const handleKeyDown = (index: number, e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Backspace' && !otpDigits[index] && index > 0) {
      inputRefs.current[index - 1]?.focus();
    }
  };

  const handleFillCode = () => {
    const code = ['1', '2', '3', '4', '5', '6'];
    setOtpDigits(['', '', '', '', '', '']);

    code.forEach((char, idx) => {
      setTimeout(() => {
        setOtpDigits((prev) => {
          const next = [...prev];
          next[idx] = char;
          return next;
        });
        setActiveSlot(idx);
        inputRefs.current[idx]?.focus();
      }, idx * 12);
    });

    setTimeout(() => {
      handleVerifyCode('123456');
    }, 6 * 12 + 20);
  };

  const handleVerifyCode = async (codeToVerify?: string) => {
    const code = (codeToVerify !== undefined ? codeToVerify : otpDigits.join('')).trim();
    if (!code || code.length < 6) {
      setError('Please enter the full 6-digit OTP code (123456).');
      return;
    }

    setIsLoading(true);
    setError('');

    const success = await verifyMFA(code);
    if (!success) {
      setError('Invalid 6-digit verification code. Please enter 123456.');
    }
    setIsLoading(false);
  };

  const handleFormVerify = (e: React.FormEvent) => {
    e.preventDefault();
    handleVerifyCode();
  };

  const handleOAuthLogin = async (provider: string) => {
    setIsLoading(true);
    setError('');

    const simulatedEmail = `officer.${provider}@cybercrime.gov.in`;
    await login(simulatedEmail, 'SecurePass@2026', true);
    setIsLoading(false);
  };

  return (
    <div className="min-h-[100dvh] bg-dark-950 grid-bg flex items-center justify-center p-3 sm:p-6 relative overflow-hidden">
      {/* Background Effects */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-72 sm:w-96 h-72 sm:h-96 bg-primary-500/5 rounded-full blur-3xl animate-pulse-slow" />
        <div className="absolute bottom-1/4 right-1/4 w-72 sm:w-96 h-72 sm:h-96 bg-accent-purple/5 rounded-full blur-3xl animate-pulse-slow" style={{ animationDelay: '1s' }} />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] sm:w-[900px] h-[600px] sm:h-[900px] rounded-full border border-primary-500/5" />
      </div>

      <div className="relative w-full max-w-md my-auto">
        {/* LEATrace Top Logo Header */}
        <div className="text-center mb-5 sm:mb-6 animate-slide-down">
          <div className="w-14 h-14 sm:w-16 sm:h-16 mx-auto mb-3 rounded-2xl bg-gradient-to-br from-primary-500 via-cyber-teal to-primary-600 flex items-center justify-center shadow-[0_0_25px_rgba(0,212,255,0.4)] border border-cyan-400/40">
            <Hexagon size={32} className="text-white animate-pulse" />
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">LEAtTrace</h1>
          <p className="text-xs text-dark-400 mt-1">National Cybercrime Investigation Platform (I4C & CBI)</p>
        </div>

        {/* OTP Screen or Login Card */}
        {mfaPendingUser ? (
          <div className="animate-slide-up space-y-5">
            {/* Header Tag */}
            <div className="text-center">
              <span className="text-[10px] font-semibold uppercase tracking-widest text-primary-400/80 font-mono">
                SECURITY VERIFICATION · COMPONENT 78
              </span>
              <h1 className="text-3xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-white via-primary-200 to-primary-400 mt-1 tracking-tight">
                OTP Verification
              </h1>
            </div>

            {/* Glass Card */}
            <div className="glass-card p-6 sm:p-8 bg-dark-900/90 border border-primary-500/20 shadow-2xl backdrop-blur-2xl">
              <div className="text-center mb-6">
                <h2 className="text-lg font-bold text-white tracking-wide">Verify your identity</h2>
                <p className="text-xs text-dark-300 mt-1">
                  Enter the 6-digit code sent to <span className="text-white font-medium">{mfaPendingUser.email}</span>
                </p>
                <div className="mt-2.5 px-3 py-1.5 bg-primary-500/10 border border-primary-500/30 rounded-lg inline-block text-[11px] text-primary-300 font-mono">
                  📌 Instruction: Everyone must enter OTP <span className="font-bold text-white underline">123456</span> to login.
                </div>
              </div>

              <form onSubmit={handleFormVerify} className="space-y-6">
                {/* 6 Digit Input Slots */}
                <div className="flex items-center justify-center gap-2 sm:gap-3">
                  {otpDigits.map((digit, idx) => (
                    <div key={idx} className="relative">
                      <input
                        ref={(el) => (inputRefs.current[idx] = el)}
                        type="text"
                        maxLength={1}
                        value={digit}
                        onFocus={() => setActiveSlot(idx)}
                        onChange={(e) => handleDigitChange(idx, e.target.value)}
                        onKeyDown={(e) => handleKeyDown(idx, e)}
                        className={`w-11 h-14 sm:w-13 sm:h-16 text-center text-xl sm:text-2xl font-bold font-mono rounded-xl transition-all duration-200 focus:outline-none cursor-pointer ${
                          digit
                            ? 'bg-primary-500/20 border-primary-400 text-white shadow-[0_0_20px_rgba(0,212,255,0.4)] animate-pop-digit'
                            : activeSlot === idx
                            ? 'bg-dark-950 border-cyan-400 text-white animate-pulse-glow translate-y-[-2px]'
                            : 'bg-dark-950/80 border-dark-700 text-dark-400 hover:border-dark-600'
                        }`}
                        placeholder="•"
                      />
                    </div>
                  ))}
                </div>

                {/* Message Toast Banner */}
                <div className="p-3 bg-dark-950/90 border border-dark-700/60 rounded-xl flex items-center justify-between gap-3 shadow-lg">
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="w-8 h-8 rounded-lg bg-accent-purple/20 border border-accent-purple/30 flex items-center justify-center flex-shrink-0 text-accent-purple">
                      💬
                    </div>
                    <div className="min-w-0">
                      <p className="text-[9px] uppercase tracking-wider text-dark-400 font-bold font-mono">
                        MESSAGE · LEATTRACE SECURITY
                      </p>
                      <p className="text-xs text-dark-200 truncate">
                        <strong className="text-white font-mono text-sm">123456</strong> is your verification code.
                      </p>
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={handleFillCode}
                    className="px-4 py-1.5 bg-white hover:bg-primary-300 text-dark-950 font-bold text-xs rounded-full transition-all active:scale-95 shadow-md flex-shrink-0 cursor-pointer"
                  >
                    Fill
                  </button>
                </div>

                <p className="text-[10px] text-dark-400 text-center font-mono">
                  Type it, paste it, or let the message fill it — <span className="text-primary-300 font-bold">123456</span> is the valid one.
                </p>

                {error && (
                  <div className="p-3 rounded-lg bg-accent-red/10 border border-accent-red/20 text-center">
                    <p className="text-xs text-accent-red">{error}</p>
                  </div>
                )}

                <button
                  type="submit"
                  disabled={isLoading}
                  className="w-full py-3.5 bg-gradient-to-r from-primary-500 to-cyber-teal text-white font-bold rounded-xl
                    hover:brightness-110 transition-all duration-200 shadow-glow-cyan
                    disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 text-sm cursor-pointer"
                >
                  {isLoading ? (
                    <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  ) : (
                    <>Verify & Authorize <ArrowRight size={16} /></>
                  )}
                </button>

                <button
                  type="button"
                  onClick={() => setMfaPending(null, null)}
                  className="w-full text-center text-xs text-dark-400 hover:text-white transition-colors pt-1 cursor-pointer block"
                >
                  Back to Login
                </button>
              </form>
            </div>
          </div>
        ) : (
          <div className="glass-card p-5 sm:p-8 animate-slide-up">
            <div className="flex items-center gap-2 mb-4">
              <Shield size={16} className="text-primary-400" />
              <h2 className="text-base sm:text-lg font-semibold text-white">Secure Authentication</h2>
            </div>

            {/* Security Notice */}
            <div className="flex items-start gap-2 p-2.5 rounded-lg bg-accent-gold/5 border border-accent-gold/20 mb-4">
              <AlertTriangle size={14} className="text-accent-gold mt-0.5 flex-shrink-0" />
              <p className="text-[11px] text-dark-300">Authorized law enforcement portal. Access is audited and monitored.</p>
            </div>

            {/* Credentials Guide Card */}
            <div className="p-3 rounded-lg bg-primary-500/10 border border-primary-500/30 mb-5 space-y-1 text-xs text-dark-300">
              <span className="font-bold text-white block uppercase tracking-wider text-[10px]">Preset Officer Credentials:</span>
              <div className="flex justify-between border-b border-dark-800 pb-1">
                <span className="text-dark-400">Email:</span>
                <code className="text-primary-300 select-all font-mono text-[11px]">lakshaysoni@cybercrime.gov.in</code>
              </div>
              <div className="flex justify-between">
                <span className="text-dark-400">Password:</span>
                <code className="text-primary-300 select-all font-mono text-[11px]">SecurePass@2026</code>
              </div>
            </div>

            <form onSubmit={handleLogin} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-dark-300 mb-1.5">Email Address</label>
                <div className="relative">
                  <Mail size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-dark-400" />
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="input-field pl-10 text-sm"
                    placeholder="officer@cybercrime.gov.in"
                    required
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-dark-300 mb-1.5">Password</label>
                <div className="relative">
                  <Lock size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-dark-400" />
                  <input
                    type={showPassword ? 'text' : 'password'}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="input-field pl-10 pr-10 text-sm"
                    placeholder="••••••••••"
                    required
                  />
                  <button type="button" onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-dark-400 hover:text-white p-1">
                    {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                  </button>
                </div>
              </div>

              {error && (
                <div className="p-3 rounded-lg bg-accent-red/10 border border-accent-red/20">
                  <p className="text-xs text-accent-red">{error}</p>
                </div>
              )}

              <button
                type="submit"
                disabled={isLoading}
                className={`door-login-btn w-full h-11 py-2.5 px-5 bg-gradient-to-r from-primary-600 via-cyber-teal to-primary-500 text-white font-semibold rounded-xl
                  hover:brightness-110 transition-all duration-300 shadow-[0_4px_18px_rgba(0,212,255,0.3)] hover:shadow-glow-cyan border border-cyan-400/40
                  disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-between text-sm cursor-pointer ${
                    isLoading ? 'is-submitting' : ''
                  }`}
              >
                <span className="tracking-wide">Access Platform</span>

                {/* 3D Door Animated Icon */}
                <div className="door-container">
                  <div className="door-frame">
                    <svg className="door-person" viewBox="0 0 24 36" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <circle cx="12" cy="6" r="4" fill="#00d4ff" />
                      <line x1="12" y1="10" x2="12" y2="22" stroke="#00d4ff" strokeWidth="2.5" strokeLinecap="round" />
                      <line x1="12" y1="13" x2="6" y2="18" stroke="#00d4ff" strokeWidth="2" strokeLinecap="round" />
                      <line x1="12" y1="13" x2="18" y2="17" stroke="#00d4ff" strokeWidth="2" strokeLinecap="round" />
                      <g className="door-person-leg">
                        <line x1="12" y1="22" x2="7" y2="32" stroke="#00d4ff" strokeWidth="2.5" strokeLinecap="round" />
                      </g>
                      <line x1="12" y1="22" x2="16" y2="31" stroke="#00d4ff" strokeWidth="2.5" strokeLinecap="round" />
                    </svg>

                    <div className="door-panel">
                      <div className="door-knob" />
                    </div>
                  </div>
                </div>
              </button>
            </form>

            <div className="mt-5 pt-3 border-t border-dark-800 text-center">
              <p className="text-[10px] text-dark-500">Session secured with AES-256 encryption</p>
              <p className="text-[10px] text-dark-500 mt-0.5">NIST SP 800-53 Compliant • OWASP ASVS Level 2</p>
            </div>
          </div>
        )}

        {/* Footer */}
        <div className="text-center mt-5">
          <p className="text-[10px] text-dark-500">Government of India • Cyber Crime Investigation Cell</p>
          <p className="text-[10px] text-dark-600 mt-0.5">© 2026 LEAtTrace Forensics Portal. Joint Agency System (I4C, CBI, NIA, Cyber Crime Cell).</p>
        </div>
      </div>
    </div>
  );
};
