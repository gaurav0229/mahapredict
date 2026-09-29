"use client";

const howItWorks = [
  {
    step: "STEP 01",
    title: "Enter your percentile",
    text: "Add your MHT CET percentile, category, and preferred branch to start comparing with real cutoffs.",
  },
  {
    step: "STEP 02",
    title: "Select preferences",
    text: "Filter by district, branch, college type, and safety level to shorten the perfect choice list.",
  },
  {
    step: "STEP 03",
    title: "Get predictions",
    text: "See which colleges fall into safe, target, and dream buckets with quick recommendations.",
  },
];

const topColleges = [
  {
    name: "COEP Technological University",
    city: "Pune",
    type: "Government",
    branches: 7,
    score: "Top Choice",
  },
  {
    name: "VJTI Mumbai",
    city: "Mumbai",
    type: "Government",
    branches: 8,
    score: "Top Choice",
  },
  {
    name: "Walchand College of Engineering",
    city: "Sangli",
    type: "Government Aided",
    branches: 10,
    score: "Strong Option",
  },
  {
    name: "SGGSIE&T Nanded",
    city: "Nanded",
    type: "Government",
    branches: 6,
    score: "Strong Option",
  },
  {
    name: "Government College of Engineering, Aurangabad",
    city: "Aurangabad",
    type: "Government",
    branches: 7,
    score: "Balanced",
  },
  {
    name: "Government College of Engineering, Amravati",
    city: "Amravati",
    type: "Government",
    branches: 7,
    score: "Balanced",
  },
];

export default function HomePage() {
  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(16,185,129,0.12),_transparent_25%),linear-gradient(180deg,#f8fafc_0%,#edfdf5_30%,#f8fafc_100%)] text-slate-900">
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 bg-[url('https://images.unsplash.com/photo-1523240795612-9a054b0db644?auto=format&fit=crop&w=1600&q=80')] bg-cover bg-center opacity-10" />
        <div className="absolute inset-0 bg-gradient-to-r from-emerald-50/80 via-white/60 to-sky-50/70" />

        <div className="relative mx-auto grid max-w-7xl gap-8 px-4 py-12 sm:px-6 lg:grid-cols-[1.2fr_0.8fr] lg:items-center lg:gap-10 lg:py-20">
          <div>
            <span className="inline-flex rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-emerald-700">
              Maharashtra Engineering Admission Predictor
            </span>
            <h1 className="mt-6 text-4xl font-black tracking-tight text-slate-900 md:text-6xl">
              Predict your college match with real cutoff trends.
            </h1>
            <p className="mt-5 max-w-xl text-lg text-slate-600">
              Compare your MHT CET / diploma profile against previous CAP cutoff data and find high-probability colleges, branch options, and safe backup choices.
            </p>

            <div className="mt-8 flex flex-wrap gap-4">
              <a
                href="/predictor"
                className="rounded-full bg-emerald-500 px-6 py-3 font-semibold text-white shadow-lg shadow-emerald-200 transition hover:bg-emerald-600"
              >
                Start Prediction
              </a>
              <a
                href="/colleges"
                className="rounded-full border border-slate-300 bg-white px-6 py-3 font-semibold text-slate-700 transition hover:border-slate-400 hover:bg-slate-100"
              >
                Browse Colleges
              </a>
            </div>

            <div className="mt-10 grid max-w-lg grid-cols-3 gap-4">
              <div className="rounded-2xl bg-white p-4 shadow-sm ring-1 ring-slate-200">
                <p className="text-2xl font-bold text-slate-900">344+</p>
                <p className="text-xs text-slate-500">Colleges</p>
              </div>
              <div className="rounded-2xl bg-white p-4 shadow-sm ring-1 ring-slate-200">
                <p className="text-2xl font-bold text-slate-900">3Y</p>
                <p className="text-xs text-slate-500">Cutoff Data</p>
              </div>
              <div className="rounded-2xl bg-white p-4 shadow-sm ring-1 ring-slate-200">
                <p className="text-2xl font-bold text-slate-900">4 R</p>
                <p className="text-xs text-slate-500">CAP Rounds</p>
              </div>
            </div>
          </div>

          <div className="rounded-3xl border border-white/10 bg-slate-900/80 p-6 text-white shadow-2xl shadow-slate-500/20 backdrop-blur-md">
            <p className="text-sm uppercase tracking-[0.2em] text-emerald-300">Smart Profile Snapshot</p>
            <div className="mt-6 space-y-4">
              <div className="rounded-2xl bg-slate-800 p-4">
                <p className="text-sm text-slate-400">Best-fit score</p>
                <p className="mt-1 text-3xl font-bold">91.8%</p>
              </div>
              <div className="flex items-center justify-between rounded-2xl bg-slate-800 p-4">
                <span>Eligibility</span>
                <span className="rounded-full bg-emerald-500 px-2 py-1 text-xs font-bold text-white">High Chance</span>
              </div>
              <div className="flex items-center justify-between rounded-2xl bg-slate-800 p-4">
                <span>Top target</span>
                <span className="font-semibold">COEP / VJTI</span>
              </div>
              <div className="rounded-2xl bg-slate-800 p-4">
                <p className="text-sm text-slate-400">Official colleges included</p>
                <p className="mt-1 text-lg font-semibold">16+ Maharashtra colleges</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section id="features" className="mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:py-20">
        <div className="text-center">
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-emerald-600">How it works</p>
          <h2 className="mt-3 text-3xl font-bold text-slate-900">Three simple steps to find your ideal engineering college</h2>
        </div>

        <div className="mt-10 grid gap-6 md:grid-cols-3">
          {howItWorks.map((item, index) => (
            <div key={item.step} className="rounded-3xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
              <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-emerald-100 text-sm font-bold text-emerald-700">
                {index + 1}
              </div>
              <p className="text-xs font-semibold uppercase tracking-[0.24em] text-slate-500">{item.step}</p>
              <h3 className="mt-3 text-xl font-bold text-slate-900">{item.title}</h3>
              <p className="mt-3 text-slate-600">{item.text}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="bg-slate-900 py-16 text-white sm:py-20">
        <div className="mx-auto max-w-7xl px-4 sm:px-6">
          <div className="mb-8 flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.2em] text-emerald-300">Top government colleges</p>
              <h2 className="mt-3 text-3xl font-bold">Maharashtra’s most sought-after institutes</h2>
            </div>
            <a href="/colleges" className="inline-flex items-center justify-center rounded-full border border-white/20 bg-white/5 px-4 py-2 text-sm font-semibold text-white transition hover:bg-white/10">
              View all colleges →
            </a>
          </div>

          <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-3">
            {topColleges.map((college) => (
              <div key={college.name} className="rounded-3xl border border-white/10 bg-white/5 p-5 shadow-xl backdrop-blur-sm">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <p className="text-xl font-bold text-white">{college.name}</p>
                    <p className="mt-2 text-sm text-slate-300">{college.city} • {college.type}</p>
                  </div>
                  <span className="rounded-full bg-emerald-500/20 px-2 py-1 text-[10px] font-bold uppercase tracking-[0.18em] text-emerald-200">
                    {college.score}
                  </span>
                </div>

                <div className="mt-5 flex items-center justify-between text-sm text-slate-200">
                  <span>{college.branches} branches</span>
                  <span className="font-semibold text-emerald-300">Popular</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section id="predictor" className="bg-white py-16 sm:py-20">
        <div className="mx-auto max-w-5xl px-4 text-center sm:px-6">
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-emerald-600">Prediction tool</p>
          <h2 className="mt-3 text-3xl font-bold text-slate-900">Check your admission chances</h2>
          <p className="mx-auto mt-4 max-w-2xl text-lg text-slate-600">
            Enter your percentile, category, quota, and preferences in the full predictor to see real colleges
            ranked by chance — high, moderate, or low — based on actual CAP cutoff history.
          </p>
          <a
            href="/predictor"
            className="mt-8 inline-flex items-center justify-center rounded-full bg-emerald-500 px-8 py-3.5 font-semibold text-white shadow-lg shadow-emerald-200 transition hover:bg-emerald-600"
          >
            Open the Predictor →
          </a>
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:py-20">
        <div className="text-center">
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-emerald-600">Why use MahaPredict</p>
          <h2 className="mt-3 text-3xl font-bold text-slate-900">Everything you need to navigate Maharashtra engineering admissions</h2>
        </div>

        <div className="mt-10 grid gap-6 md:grid-cols-2 xl:grid-cols-4">
          {[
            ["Predictor", "Enter your percentile, category, and preference list to see colleges that fit your profile."],
            ["Detailed data", "Explore branch-wise cutoffs, location, seat trends, and college status in one view."],
            ["NIRF insight", "Balance rank-fit with institutional quality, reputation, and placement outcomes."],
            ["Plan smarter", "Build a clean list of safe, target, and dream options before CAP rounds begin."],
          ].map(([title, text]) => (
            <div key={title} className="rounded-3xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
              <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-emerald-100 text-xl text-emerald-700">✦</div>
              <h3 className="text-xl font-bold text-slate-900">{title}</h3>
              <p className="mt-3 text-slate-600">{text}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-4 pb-16 sm:px-6 lg:pb-20">
        <div className="rounded-[2rem] bg-gradient-to-r from-emerald-600 via-emerald-500 to-teal-500 p-8 text-white shadow-2xl shadow-emerald-200 sm:p-10">
          <div className="flex flex-col gap-6 md:flex-row md:items-center md:justify-between">
            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.2em] text-emerald-100">Ready to find your college?</p>
              <h3 className="mt-3 text-3xl font-black">Enter your percentile and get instant predictions.</h3>
            </div>
            <a href="/predictor" className="inline-flex items-center justify-center rounded-full bg-white px-6 py-3 font-semibold text-emerald-700 transition hover:bg-emerald-50">
              Start Prediction →
            </a>
          </div>
        </div>
      </section>

      <section id="about" className="mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:py-20">
        <div className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-sm sm:p-8 lg:p-10">
          <div className="grid gap-8 lg:grid-cols-[1fr_1.1fr] lg:items-center">
            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.2em] text-emerald-600">About us</p>
              <h2 className="mt-3 text-3xl font-bold text-slate-900">Built for Maharashtra students who want a clear CAP plan.</h2>
            </div>
            <div className="space-y-4 text-slate-600">
              <p>
                MahaPredict helps students understand where they stand before CAP counseling begins. We combine real cutoff trends,
                branch interest, and category-based analysis into a simple decision-making experience.
              </p>
              <p>
                The platform is designed for students, parents, and counselors who want a faster, easier way to explore target,
                safe, and dream colleges based on actual Maharashtra engineering admission patterns.
              </p>
            </div>
          </div>
        </div>
      </section>

      <section id="guide" className="bg-slate-900 py-16 text-white sm:py-20">
        <div className="mx-auto max-w-7xl px-4 sm:px-6">
          <div className="text-center">
            <p className="text-sm font-semibold uppercase tracking-[0.2em] text-emerald-300">CAP guide</p>
            <h2 className="mt-3 text-3xl font-bold">How the counseling process works</h2>
          </div>

          <div className="mt-10 grid gap-6 md:grid-cols-3">
            {[
              ["Round 1", "Fill your college and branch preferences early and review seat movement data."],
              ["Freeze / Float / Slide", "Use these choices strategically based on your target and backup colleges."],
              ["Seat confirmation", "Report to the allotted institution and complete document verification on time."],
            ].map(([title, text], index) => (
              <div key={title} className="rounded-3xl bg-white/5 p-6 ring-1 ring-white/10">
                <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-full bg-emerald-500 text-sm font-bold text-white">
                  0{index + 1}
                </div>
                <h3 className="text-xl font-bold">{title}</h3>
                <p className="mt-3 text-slate-300">{text}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <footer className="border-t border-slate-200 bg-slate-50 py-10 text-slate-700">
        <div className="mx-auto grid max-w-7xl gap-10 px-4 sm:px-6 lg:grid-cols-[1.1fr_0.8fr_0.8fr_0.8fr]">
          <div>
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-600 font-black text-white">M</div>
              <div>
                <p className="text-base font-bold text-slate-900">MahaPredict</p>
                <p className="text-[9px] uppercase tracking-[0.22em] text-slate-500">CAP Advisor</p>
              </div>
            </div>
            <p className="mt-4 max-w-sm text-sm text-slate-600">
              Helping Maharashtra engineering aspirants make smarter, data-backed admission choices.
            </p>
          </div>

          <div>
            <p className="text-sm font-bold uppercase tracking-[0.2em] text-slate-500">Tools</p>
            <ul className="mt-4 space-y-2 text-sm">
              <li><a href="#predictor" className="hover:text-emerald-700">College Predictor</a></li>
              <li><a href="/colleges" className="hover:text-emerald-700">All Colleges</a></li>
              <li><a href="/dashboard" className="hover:text-emerald-700">Dashboard</a></li>
            </ul>
          </div>

          <div>
            <p className="text-sm font-bold uppercase tracking-[0.2em] text-slate-500">Resources</p>
            <ul className="mt-4 space-y-2 text-sm">
              <li><a href="/about" className="hover:text-emerald-700">About</a></li>
              <li><a href="#guide" className="hover:text-emerald-700">CAP Guide</a></li>
              <li><a href="/colleges" className="hover:text-emerald-700">Top Colleges</a></li>
            </ul>
          </div>

          <div>
            <p className="text-sm font-bold uppercase tracking-[0.2em] text-slate-500">Legal</p>
            <ul className="mt-4 space-y-2 text-sm">
              <li><a href="/about" className="hover:text-emerald-700">Privacy Policy</a></li>
              <li><a href="/about" className="hover:text-emerald-700">Terms of Service</a></li>
              <li className="text-slate-500">Disclaimer: educational guidance only.</li>
            </ul>
          </div>
        </div>
      </footer>
    </main>
  );
}
