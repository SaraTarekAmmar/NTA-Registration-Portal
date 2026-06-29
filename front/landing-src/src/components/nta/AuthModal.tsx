import React, { useEffect, useState } from 'react';
import {
  ArrowLeft,
  ArrowRight,
  CheckCircle2,
  GraduationCap,
  Loader2,
  LogIn,
  ShieldCheck,
  UserRound,
  X,
} from 'lucide-react';
import { useLang } from '../../i18n';

type AuthMode = 'login' | 'signup';
type LoginRole = 'trainee' | 'trainer';

type AuthModalProps = {
  open: boolean;
  mode: AuthMode;
  loginRole: LoginRole;
  onClose: () => void;
  onLoginRoleChange: (role: LoginRole) => void;
};

type SignupState = {
  nationalId: string;
  fullName: string;
  phone: string;
  email: string;
  password: string;
  confirmPassword: string;
};

const emptySignup: SignupState = {
  nationalId: '',
  fullName: '',
  phone: '',
  email: '',
  password: '',
  confirmPassword: '',
};

export function AuthModal({
  open,
  mode,
  loginRole,
  onClose,
  onLoginRoleChange,
}: AuthModalProps) {
  const { t, lang } = useLang();
  const auth = t.auth;
  const [step, setStep] = useState(1);
  const [loginNationalId, setLoginNationalId] = useState('');
  const [loginPassword, setLoginPassword] = useState('');
  const [signup, setSignup] = useState<SignupState>(emptySignup);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const stepTitles = [
    auth.signupNationalId,
    auth.signupFullName,
    auth.signupPhone,
    auth.signupPassword,
  ];
  const stepHints = auth.signupHints;

  useEffect(() => {
    if (!open) return;
    setError('');
    setLoading(false);
    if (mode === 'signup') setStep(1);
  }, [mode, open]);

  useEffect(() => {
    if (!open) return;
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [onClose, open]);

  if (!open) return null;

  const resetAndClose = () => {
    setError('');
    setLoading(false);
    onClose();
  };

  const validateNationalId = async (nationalId: string) => {
    if (!/^\d{10,20}$/.test(nationalId)) {
      throw new Error(auth.nationalIdError);
    }

    const response = await fetch(`/api/signup/check/${nationalId}`);
    if (!response.ok) {
      throw new Error(auth.nationalIdValidationError);
    }

    const data = await response.json();
    if (!data.available) {
      throw new Error(auth.nationalIdTakenError);
    }
  };

  const handleLogin = async (event: React.FormEvent) => {
    event.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          national_id: loginNationalId.trim(),
          password: loginPassword,
          role: loginRole,
        }),
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || auth.loginFailed);
      }

      window.location.href = data.redirect_url;
    } catch (err) {
      setError(err instanceof Error ? err.message : auth.loginFailed);
      setLoading(false);
    }
  };

  const handleSignupNext = async () => {
    setError('');

    try {
      if (step === 1) {
        await validateNationalId(signup.nationalId.trim());
      } else if (step === 2) {
        if (signup.fullName.trim().length < 3) throw new Error(auth.fullNameError);
      } else if (step === 3) {
        if (signup.phone.trim().length < 7) throw new Error(auth.phoneError);
      } else if (step === 4) {
        if (signup.password.length < 6) throw new Error(auth.passwordError);
        if (signup.password !== signup.confirmPassword) throw new Error(auth.passwordMismatch);

        setLoading(true);
        const response = await fetch('/api/signup', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            national_id: signup.nationalId.trim(),
            full_name: signup.fullName.trim(),
            phone: signup.phone.trim(),
            email: signup.email.trim() || null,
            password: signup.password,
          }),
        });
        await response.json();
        if (!response.ok) throw new Error(auth.signupFailed);

        window.location.href = '/registration/index.html';
        return;
      }

      setStep((current) => Math.min(current + 1, 4));
    } catch (err) {
      setError(err instanceof Error ? err.message : auth.signupFailed);
    } finally {
      setLoading(false);
    }
  };

  const handleSignupBack = () => {
    if (step > 1) {
      setError('');
      setStep((current) => current - 1);
    }
  };

  const isSignup = mode === 'signup';

  return (
    <div
      className="fixed inset-0 z-[80] bg-[#081827]/70 backdrop-blur-sm flex items-center justify-center px-4 py-6"
      onClick={(event) => {
        if (event.target === event.currentTarget) resetAndClose();
      }}
    >
      <div className="w-full max-w-2xl overflow-hidden rounded-[28px] border border-white/10 bg-white shadow-2xl shadow-black/20">
        <div className="flex items-start justify-between gap-4 border-b border-gray-100 px-6 py-5">
          <div>
            <p className="inline-flex items-center gap-2 rounded-full bg-[#E51B2B]/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] text-[#E51B2B]">
              {isSignup ? auth.publicRegistration : auth.portalAccess}
            </p>
            <h2 className="mt-3 text-2xl font-bold tracking-tight text-[#081827]">
              {isSignup ? auth.signupTitle : auth.loginTitle}
            </h2>
            <p className="mt-2 text-sm leading-6 text-[#081827]/70">
              {isSignup ? auth.signupSubtitle : auth.loginSubtitle}
            </p>
          </div>
          <button
            type="button"
            onClick={resetAndClose}
            className="grid h-10 w-10 place-items-center rounded-full border border-gray-200 text-[#081827] transition hover:bg-gray-50"
            aria-label={auth.closeDialog}
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {isSignup ? (
          <div className="grid gap-0 md:grid-cols-[1.1fr_1.4fr]">
            <aside className="border-b border-gray-100 bg-[#F8FAFC] px-6 py-6 md:border-b-0 md:border-r">
              <div className="flex items-center gap-3">
                <span className="grid h-11 w-11 place-items-center rounded-2xl bg-[#E51B2B]/10 text-[#E51B2B]">
                  <ShieldCheck className="h-5 w-5" />
                </span>
                <div>
                  <p className="text-sm font-semibold text-[#081827]">
                    {auth.signupStep} {step} {auth.signupOf} 4
                  </p>
                  <p className="text-xs text-[#081827]/60">{stepTitles[step - 1]}</p>
                </div>
              </div>

              <div className="mt-6 h-1.5 rounded-full bg-gray-200">
                <div
                  className="h-full rounded-full bg-[#E51B2B] transition-all duration-300"
                  style={{ width: `${(step / 4) * 100}%` }}
                />
              </div>

              <div className="mt-6 space-y-3 text-sm text-[#081827]/70">
                {stepHints.map((hint, index) => {
                  const active = index + 1 === step;
                  return (
                    <div
                      key={hint}
                      className={`rounded-2xl border px-4 py-3 transition ${
                        active
                          ? 'border-[#E51B2B]/30 bg-[#E51B2B]/5 text-[#081827]'
                          : 'border-gray-200 bg-white'
                      }`}
                    >
                      <span className="mr-2 inline-flex h-5 w-5 items-center justify-center rounded-full bg-[#081827]/5 text-[11px] font-semibold">
                        {index + 1}
                      </span>
                      {hint}
                    </div>
                  );
                })}
              </div>
            </aside>

            <div className="px-6 py-6">
              <div className="min-h-[280px]">
                {step === 1 && (
                  <div className="space-y-4">
                    <label className="block">
                      <span className="mb-2 block text-sm font-semibold text-[#081827]">
                        {auth.signupNationalId}
                      </span>
                      <input
                        type="text"
                        inputMode="numeric"
                        value={signup.nationalId}
                        onChange={(event) =>
                          setSignup((current) => ({
                            ...current,
                            nationalId: event.target.value,
                          }))
                        }
                        className="h-12 w-full rounded-2xl border border-gray-200 px-4 text-[#081827] outline-none transition focus:border-[#E51B2B] focus:ring-4 focus:ring-[#E51B2B]/10"
                        placeholder={lang === 'ar' ? 'مثال: 29505051234567' : 'e.g. 29505051234567'}
                      />
                    </label>
                  </div>
                )}

                {step === 2 && (
                  <label className="block">
                    <span className="mb-2 block text-sm font-semibold text-[#081827]">
                      {auth.signupFullName}
                    </span>
                    <input
                      type="text"
                      value={signup.fullName}
                      onChange={(event) =>
                        setSignup((current) => ({
                          ...current,
                          fullName: event.target.value,
                        }))
                      }
                      className="h-12 w-full rounded-2xl border border-gray-200 px-4 text-[#081827] outline-none transition focus:border-[#E51B2B] focus:ring-4 focus:ring-[#E51B2B]/10"
                      placeholder={lang === 'ar' ? 'اسمك الكامل' : 'Your full name'}
                    />
                  </label>
                )}

                {step === 3 && (
                  <label className="block">
                    <span className="mb-2 block text-sm font-semibold text-[#081827]">
                      {auth.signupPhone}
                    </span>
                    <input
                      type="tel"
                      value={signup.phone}
                      onChange={(event) =>
                        setSignup((current) => ({
                          ...current,
                          phone: event.target.value,
                        }))
                      }
                      className="h-12 w-full rounded-2xl border border-gray-200 px-4 text-[#081827] outline-none transition focus:border-[#E51B2B] focus:ring-4 focus:ring-[#E51B2B]/10"
                      placeholder={lang === 'ar' ? 'مثال: 01012345678' : 'e.g. 01012345678'}
                    />
                  </label>
                )}

                {step === 4 && (
                  <div className="space-y-4">
                    <label className="block">
                      <span className="mb-2 block text-sm font-semibold text-[#081827]">
                        {lang === 'ar' ? 'البريد الإلكتروني' : 'Email address'}{' '}
                        <span className="font-normal text-[#081827]/50">({lang === 'ar' ? 'اختياري' : 'optional'})</span>
                      </span>
                      <input
                        type="email"
                        value={signup.email}
                        onChange={(event) =>
                          setSignup((current) => ({
                            ...current,
                            email: event.target.value,
                          }))
                        }
                        className="h-12 w-full rounded-2xl border border-gray-200 px-4 text-[#081827] outline-none transition focus:border-[#E51B2B] focus:ring-4 focus:ring-[#E51B2B]/10"
                        placeholder={lang === 'ar' ? 'you@example.com' : 'you@example.com'}
                      />
                    </label>

                    <div className="grid gap-4 sm:grid-cols-2">
                      <label className="block">
                        <span className="mb-2 block text-sm font-semibold text-[#081827]">
                          {auth.signupPassword}
                        </span>
                        <input
                          type="password"
                          value={signup.password}
                          onChange={(event) =>
                            setSignup((current) => ({
                              ...current,
                              password: event.target.value,
                            }))
                          }
                          className="h-12 w-full rounded-2xl border border-gray-200 px-4 text-[#081827] outline-none transition focus:border-[#E51B2B] focus:ring-4 focus:ring-[#E51B2B]/10"
                          placeholder="••••••••"
                        />
                      </label>
                      <label className="block">
                        <span className="mb-2 block text-sm font-semibold text-[#081827]">
                          {lang === 'ar' ? 'تأكيد كلمة المرور' : 'Confirm password'}
                        </span>
                        <input
                          type="password"
                          value={signup.confirmPassword}
                          onChange={(event) =>
                            setSignup((current) => ({
                              ...current,
                              confirmPassword: event.target.value,
                            }))
                          }
                          className="h-12 w-full rounded-2xl border border-gray-200 px-4 text-[#081827] outline-none transition focus:border-[#E51B2B] focus:ring-4 focus:ring-[#E51B2B]/10"
                          placeholder="••••••••"
                        />
                      </label>
                    </div>
                  </div>
                )}
              </div>

              {error ? (
                <div className="mt-4 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                  {error}
                </div>
              ) : null}

              <div className="mt-6 flex items-center gap-3">
                <button
                  type="button"
                  onClick={handleSignupBack}
                  disabled={step === 1 || loading}
                  className="inline-flex h-11 items-center gap-2 rounded-full border border-gray-200 px-4 text-sm font-semibold text-[#081827] transition hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-40"
                >
                  <ArrowLeft className="h-4 w-4" />
                  {auth.backButton}
                </button>
                <button
                  type="button"
                  onClick={handleSignupNext}
                  disabled={loading}
                  className="inline-flex h-11 flex-1 items-center justify-center gap-2 rounded-full bg-[#E51B2B] px-5 text-sm font-semibold text-white transition hover:bg-[#c4131f] disabled:cursor-not-allowed disabled:opacity-70"
                >
                  {loading ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : step === 4 ? (
                    <CheckCircle2 className="h-4 w-4" />
                  ) : (
                    <ArrowRight className="h-4 w-4" />
                  )}
                  {step === 4 ? auth.submitButton : auth.continueButton}
                </button>
              </div>
            </div>
          </div>
        ) : (
          <div className="grid gap-0 md:grid-cols-[0.95fr_1.05fr]">
            <aside className="border-b border-gray-100 bg-[#F8FAFC] px-6 py-6 md:border-b-0 md:border-r">
              <div className="space-y-4">
                <div className="rounded-3xl bg-white p-4 shadow-sm">
                  <div className="flex items-center gap-3">
                    <span className="grid h-11 w-11 place-items-center rounded-2xl bg-[#E51B2B]/10 text-[#E51B2B]">
                      {loginRole === 'trainer' ? <GraduationCap className="h-5 w-5" /> : <UserRound className="h-5 w-5" />}
                    </span>
                    <div>
                      <p className="text-sm font-semibold text-[#081827]">{auth.rolePrompt}</p>
                      <p className="text-xs text-[#081827]/60">
                        {loginRole === 'trainer' ? auth.roleTrainer : auth.roleTrainee}
                      </p>
                    </div>
                  </div>
                </div>
                <div className="space-y-2">
                  <button
                    type="button"
                    onClick={() => onLoginRoleChange('trainee')}
                    className={`flex w-full items-center justify-between rounded-2xl border px-4 py-3 text-left text-sm font-semibold transition ${
                      loginRole === 'trainee'
                        ? 'border-[#E51B2B] bg-[#E51B2B]/5 text-[#E51B2B]'
                        : 'border-gray-200 text-[#081827] hover:bg-white'
                    }`}
                  >
                    <span>{auth.roleTrainee}</span>
                    <UserRound className="h-4 w-4" />
                  </button>
                  <button
                    type="button"
                    onClick={() => onLoginRoleChange('trainer')}
                    className={`flex w-full items-center justify-between rounded-2xl border px-4 py-3 text-left text-sm font-semibold transition ${
                      loginRole === 'trainer'
                        ? 'border-[#E51B2B] bg-[#E51B2B]/5 text-[#E51B2B]'
                        : 'border-gray-200 text-[#081827] hover:bg-white'
                    }`}
                  >
                    <span>{auth.roleTrainer}</span>
                    <GraduationCap className="h-4 w-4" />
                  </button>
                </div>
              </div>
            </aside>

            <form onSubmit={handleLogin} className="px-6 py-6">
              <div className="space-y-4">
                <label className="block">
                  <span className="mb-2 block text-sm font-semibold text-[#081827]">
                    {auth.loginNationalId}
                  </span>
                  <input
                    type="text"
                    inputMode="numeric"
                    value={loginNationalId}
                    onChange={(event) => setLoginNationalId(event.target.value)}
                    className="h-12 w-full rounded-2xl border border-gray-200 px-4 text-[#081827] outline-none transition focus:border-[#E51B2B] focus:ring-4 focus:ring-[#E51B2B]/10"
                    placeholder={lang === 'ar' ? 'مثال: 1234567890' : 'e.g. 1234567890'}
                  />
                </label>
                <label className="block">
                  <span className="mb-2 block text-sm font-semibold text-[#081827]">
                    {auth.loginPassword}
                  </span>
                  <input
                    type="password"
                    value={loginPassword}
                    onChange={(event) => setLoginPassword(event.target.value)}
                    className="h-12 w-full rounded-2xl border border-gray-200 px-4 text-[#081827] outline-none transition focus:border-[#E51B2B] focus:ring-4 focus:ring-[#E51B2B]/10"
                    placeholder="••••••••"
                  />
                </label>

                {error ? (
                  <div className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                    {error}
                  </div>
                ) : null}

                <button
                  type="submit"
                  disabled={loading}
                  className="inline-flex h-12 w-full items-center justify-center gap-2 rounded-full bg-[#E51B2B] px-5 text-sm font-semibold text-white transition hover:bg-[#c4131f] disabled:cursor-not-allowed disabled:opacity-70"
                >
                  {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <LogIn className="h-4 w-4" />}
                  {auth.loginButton}
                </button>
              </div>
            </form>
          </div>
        )}
      </div>
    </div>
  );
}
