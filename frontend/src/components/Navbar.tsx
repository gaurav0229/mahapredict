export default function Navbar() {
  return (
    <header className="sticky top-0 z-50 border-b border-slate-200/80 bg-white/80 backdrop-blur-md">
      <div className="mx-auto flex max-w-7xl items-center justify-between gap-3 px-4 py-3 sm:px-6">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-600 font-black text-white shadow-lg shadow-emerald-200">
            M
          </div>
          <div>
            <p className="text-base font-bold text-slate-900 sm:text-lg">MahaPredict</p>
            <p className="text-[9px] uppercase tracking-[0.22em] text-slate-500 sm:text-[10px]">CAP Advisor</p>
          </div>
        </div>

        <nav className="hidden items-center gap-5 text-sm font-medium text-slate-600 md:flex">
          <a href="/" className="transition hover:text-slate-900">Home</a>
          <a href="#predictor" className="transition hover:text-slate-900">Predictor</a>
          <a href="/about" className="transition hover:text-slate-900">About</a>
          <a href="/dashboard" className="transition hover:text-slate-900">Dashboard</a>
          <a href="/colleges" className="transition hover:text-slate-900">Colleges</a>
          <a href="#guide" className="transition hover:text-slate-900">CAP Guide</a>
        </nav>

        <div className="flex items-center gap-2 sm:gap-3">
          <button className="hidden rounded-full border border-slate-300 px-3 py-2 text-xs font-semibold text-slate-700 sm:inline-flex sm:text-sm">
            Login
          </button>
          <button className="rounded-full bg-emerald-600 px-3 py-2 text-xs font-semibold text-white shadow-lg shadow-emerald-200 transition hover:bg-emerald-700 sm:px-4 sm:text-sm">
            Get Started
          </button>
        </div>
      </div>
    </header>
  );
}
