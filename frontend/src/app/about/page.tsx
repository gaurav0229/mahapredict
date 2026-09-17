export default function AboutPage() {
  return (
    <main className="min-h-screen bg-slate-50 px-4 py-16 text-slate-900 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-5xl">
        <div className="rounded-[2rem] bg-white p-6 shadow-sm ring-1 ring-slate-200 sm:p-8 lg:p-12">
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-emerald-600">About</p>
          <h1 className="mt-4 text-4xl font-black tracking-tight text-slate-900 md:text-5xl">
            Maharashtra engineering choices made simpler.
          </h1>

          <div className="mt-8 space-y-6 text-lg leading-8 text-slate-600">
            <p>
              MahaPredict is designed to help students understand their engineering admission path with more clarity.
              Instead of guessing based only on rank or score, the platform brings together cutoff trends, branch preferences,
              and category awareness in one place.
            </p>
            <p>
              Whether a student is targeting a top government college or planning a safe backup, the goal is to make each
              decision more informed, transparent, and less stressful during the CAP counseling cycle.
            </p>
            <p>
              The project is built for future growth with AI-assisted recommendation logic, stronger analytics, and clearer
              dashboards for students and counselors.
            </p>
          </div>

          <div className="mt-10 grid gap-6 md:grid-cols-3">
            {[
              ["Transparent", "Quick visibility into target, safe, and aspirational college choices."],
              ["Data-backed", "Built around previous year trends and realistic Maharashtra college patterns."],
              ["Future-ready", "Prepared for smarter recommendation layers and predictive admission intelligence."],
            ].map(([title, text]) => (
              <div key={title} className="rounded-2xl bg-emerald-50 p-5 ring-1 ring-emerald-100">
                <h2 className="text-xl font-bold text-slate-900">{title}</h2>
                <p className="mt-2 text-slate-600">{text}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </main>
  );
}
