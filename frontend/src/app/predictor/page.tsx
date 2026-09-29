"use client";

import { useEffect, useState } from "react";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "https://mahapredict.onrender.com";

const categoryOptions = [
  { value: "GOPEN", label: "GOPEN — General, Open" },
  { value: "GOBSC", label: "GOBSC — General, OBC" },
  { value: "GOSC", label: "GOSC — General, SC" },
  { value: "GOST", label: "GOST — General, ST" },
  { value: "GVJ", label: "GVJ — General, VJ/DT" },
  { value: "GNT1", label: "GNT1 — General, NT-B" },
  { value: "GNT2", label: "GNT2 — General, NT-C" },
  { value: "GNT3", label: "GNT3 — General, NT-D" },
  { value: "GSEBC", label: "GSEBC — General, SEBC" },
  { value: "LOPEN", label: "LOPEN — Ladies, Open" },
  { value: "LOBSC", label: "LOBSC — Ladies, OBC" },
  { value: "LOSC", label: "LOSC — Ladies, SC" },
  { value: "LOST", label: "LOST — Ladies, ST" },
  { value: "LVJ", label: "LVJ — Ladies, VJ/DT" },
  { value: "LNT1", label: "LNT1 — Ladies, NT-B" },
  { value: "LNT2", label: "LNT2 — Ladies, NT-C" },
  { value: "LNT3", label: "LNT3 — Ladies, NT-D" },
  { value: "LSEBC", label: "LSEBC — Ladies, SEBC" },
  { value: "EWS", label: "EWS — Economically Weaker Section" },
  { value: "TFWS", label: "TFWS — Tuition Fee Waiver Scheme" },
];

const branchOptions = [
  "Computer Science",
  "Information Technology",
  "Electronics",
  "Mechanical",
  "Civil",
  "Electrical",
  "AI & Data Science",
];

const fallbackPrediction = {
  student_name: "Rahul Patil",
  category: "GOPEN",
  score_used: 91.8,
  summary: {
    total_colleges: 18,
    high_chance: 7,
    moderate_chance: 8,
    low_chance: 3,
    not_eligible: 0,
  },
  recommended: [
    { id: "coep-pune", college_name: "COEP Technological University", branch: "Computer Science", chance: "HIGH", cutoff: 96.0 },
    { id: "vjti-mumbai", college_name: "VJTI Mumbai", branch: "Computer Science", chance: "HIGH", cutoff: 94.4 },
    { id: "walchand-sangli", college_name: "Walchand College of Engineering", branch: "Mechanical", chance: "MODERATE", cutoff: 88.7 },
  ],
  colleges: [
    { id: "coep-pune", college_name: "COEP Technological University", status: "Government Autonomous", branch: "Computer Science", cutoff: 96.0, chance: "HIGH" },
    { id: "vjti-mumbai", college_name: "VJTI Mumbai", status: "Government Autonomous", branch: "Computer Science", cutoff: 94.4, chance: "HIGH" },
    { id: "walchand-sangli", college_name: "Walchand College of Engineering", status: "Government Aided", branch: "Mechanical", cutoff: 88.7, chance: "MODERATE" },
  ],
};

export default function PredictorPage() {
  const [studentType, setStudentType] = useState<"12th" | "diploma">("12th");
  const [quota, setQuota] = useState<"MH" | "AI">("MH");
  const [homeUniversity, setHomeUniversity] = useState("");
  const [universities, setUniversities] = useState<{ name: string; college_count: number }[]>([]);
  const [formData, setFormData] = useState({
    full_name: "Rahul Patil",
    email: "rahul@example.com",
    hsc_percentage: 93.4,
    cet_percentile: 92.5,
    jee_percentile: "",
    category: "GOPEN",
    preferred_branches: ["Computer Science", "Information Technology"],
  });
  const [result, setResult] = useState<any>(fallbackPrediction);
  const [loading, setLoading] = useState(false);
  const [preferredColleges, setPreferredColleges] = useState<{ id: string; name: string; status: string | null }[]>([]);
  const [collegeSearch, setCollegeSearch] = useState("");
  const [collegeResults, setCollegeResults] = useState<{ id: string; name: string; status: string | null }[]>([]);
  const [collegeSearchLoading, setCollegeSearchLoading] = useState(false);
  const [preferredDistricts, setPreferredDistricts] = useState<string[]>([]);
  const [districts, setDistricts] = useState<{ name: string; college_count: number }[]>([]);

  useEffect(() => {
    fetch(`${API_BASE_URL}/universities`)
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (data?.items?.length) setUniversities(data.items);
      })
      .catch((error) => console.warn("Universities API unavailable.", error));

    fetch(`${API_BASE_URL}/districts`)
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (data?.items?.length) setDistricts(data.items);
      })
      .catch((error) => console.warn("Districts API unavailable.", error));
  }, []);

  useEffect(() => {
    const query = collegeSearch.trim();
    if (query.length < 3) {
      setCollegeResults([]);
      return;
    }
    setCollegeSearchLoading(true);
    const controller = new AbortController();
    const timer = setTimeout(() => {
      fetch(`${API_BASE_URL}/colleges?name=${encodeURIComponent(query)}&limit=8`, { signal: controller.signal })
        .then((res) => (res.ok ? res.json() : null))
        .then((data) => setCollegeResults(data?.items ?? []))
        .catch((error) => {
          if ((error as Error).name !== "AbortError") console.warn("College search unavailable.", error);
        })
        .finally(() => setCollegeSearchLoading(false));
    }, 300);
    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, [collegeSearch]);

  const addPreferredCollege = (college: { id: string; name: string; status: string | null }) => {
    setPreferredColleges((prev) => (prev.some((c) => c.id === college.id) ? prev : [...prev, college]));
    setCollegeSearch("");
    setCollegeResults([]);
  };

  const removePreferredCollege = (id: string) => {
    setPreferredColleges((prev) => prev.filter((c) => c.id !== id));
  };

  const exportShortlistCsv = () => {
    const rows: any[] = result?.colleges ?? fallbackPrediction.colleges;
    if (!rows.length) return;
    const header = ["College", "Status", "Branch", "Cutoff %", "Chance"];
    const csvLines = [
      header.join(","),
      ...rows.map((c) =>
        [c.college_name, c.status ?? "", c.branch, c.cutoff, c.chance]
          .map((value) => `"${String(value ?? "").replace(/"/g, '""')}"`)
          .join(",")
      ),
    ];
    const blob = new Blob([csvLines.join("\n")], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "mahapredict-shortlist.csv";
    link.click();
    URL.revokeObjectURL(url);
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    const payload = {
      full_name: formData.full_name,
      email: formData.email,
      student_type: studentType,
      hsc_percentage: studentType === "12th" ? Number(formData.hsc_percentage) : null,
      cet_percentile: studentType === "12th" && formData.cet_percentile ? Number(formData.cet_percentile) : null,
      jee_percentile: studentType === "12th" && quota === "AI" && formData.jee_percentile ? Number(formData.jee_percentile) : null,
      diploma_percentage: studentType === "diploma" ? Number(formData.hsc_percentage) : null,
      category: formData.category,
      quota: studentType === "12th" ? quota : "MH",
      home_university: quota === "MH" && homeUniversity ? homeUniversity : null,
      preferred_branches: formData.preferred_branches,
      preferred_colleges: preferredColleges.map((c) => c.id),
      preferred_districts: preferredDistricts,
    };

    try {
      const response = await fetch(`${API_BASE_URL}/predict`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        throw new Error("Prediction failed");
      }

      const data = await response.json();
      setResult(data);
    } catch (error) {
      console.warn("Prediction API unavailable; using sample result.", error);
      setResult(fallbackPrediction);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-slate-50 text-slate-900">
      <section className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:py-16">
        <div className="grid gap-8 lg:grid-cols-[1.05fr_0.95fr] lg:items-start">
          <div className="rounded-[2rem] bg-white p-6 shadow-sm ring-1 ring-slate-200 sm:p-8">
            <p className="text-sm font-semibold uppercase tracking-[0.2em] text-emerald-600">College predictor</p>
            <h1 className="mt-3 text-4xl font-black tracking-tight text-slate-900 md:text-5xl">
              Find your best-fit engineering colleges in Maharashtra.
            </h1>
            <p className="mt-4 max-w-xl text-lg text-slate-600">
              Enter your profile, choose preferred branches, and compare your chances against historical CAP cutoff trends.
            </p>

            <form onSubmit={handleSubmit} className="mt-8 space-y-8">
              <fieldset className="space-y-5">
                <legend className="text-xs font-bold uppercase tracking-[0.18em] text-emerald-700">1. Your details</legend>
                <div className="grid gap-5 md:grid-cols-2">
                  <label className="space-y-2 md:col-span-2">
                    <span className="text-sm font-medium text-slate-700">Full Name</span>
                    <input
                      name="full_name"
                      value={formData.full_name}
                      onChange={handleChange}
                      className="w-full rounded-xl border border-slate-300 bg-white px-3 py-2.5 outline-none focus:border-emerald-500"
                    />
                  </label>

                  <label className="space-y-2">
                    <span className="text-sm font-medium text-slate-700">Email</span>
                    <input
                      type="email"
                      name="email"
                      value={formData.email}
                      onChange={handleChange}
                      className="w-full rounded-xl border border-slate-300 bg-white px-3 py-2.5 outline-none focus:border-emerald-500"
                    />
                  </label>

                  <label className="space-y-2">
                    <span className="text-sm font-medium text-slate-700">Student Type</span>
                    <select
                      value={studentType}
                      onChange={(e) => setStudentType(e.target.value as "12th" | "diploma")}
                      className="w-full rounded-xl border border-slate-300 bg-white px-3 py-2.5 outline-none focus:border-emerald-500"
                    >
                      <option value="12th">12th Pass</option>
                      <option value="diploma">Diploma</option>
                    </select>
                  </label>
                </div>
              </fieldset>

              <fieldset className="space-y-5">
                <legend className="text-xs font-bold uppercase tracking-[0.18em] text-emerald-700">2. Scores &amp; category</legend>
                <div className="grid gap-5 md:grid-cols-2">
                  <label className="space-y-2">
                    <span className="text-sm font-medium text-slate-700">
                      {studentType === "12th" ? "HSC Percentage" : "Diploma Aggregate"}
                    </span>
                    <input
                      type="number"
                      name="hsc_percentage"
                      value={formData.hsc_percentage}
                      onChange={handleChange}
                      className="w-full rounded-xl border border-slate-300 bg-white px-3 py-2.5 outline-none focus:border-emerald-500"
                    />
                  </label>

                  <label className="space-y-2">
                    <span className="text-sm font-medium text-slate-700">
                      {studentType === "12th" ? "MHT CET Percentile" : "Diploma Score"}
                    </span>
                    <input
                      type="number"
                      min={0}
                      max={100}
                      step={0.01}
                      name="cet_percentile"
                      value={formData.cet_percentile}
                      onChange={handleChange}
                      className="w-full rounded-xl border border-slate-300 bg-white px-3 py-2.5 outline-none focus:border-emerald-500"
                    />
                  </label>

                  <label className="space-y-2">
                    <span className="text-sm font-medium text-slate-700">Category</span>
                    <select
                      name="category"
                      value={formData.category}
                      onChange={handleChange}
                      disabled={studentType === "12th" && quota === "AI"}
                      className="w-full rounded-xl border border-slate-300 bg-white px-3 py-2.5 outline-none focus:border-emerald-500 disabled:bg-slate-100 disabled:text-slate-400"
                    >
                      {categoryOptions.map((category) => (
                        <option key={category.value} value={category.value}>{category.label}</option>
                      ))}
                    </select>
                  </label>

                  {studentType === "12th" && (
                    <label className="space-y-2">
                      <span className="text-sm font-medium text-slate-700">Quota</span>
                      <select
                        value={quota}
                        onChange={(e) => setQuota(e.target.value as "MH" | "AI")}
                        className="w-full rounded-xl border border-slate-300 bg-white px-3 py-2.5 outline-none focus:border-emerald-500"
                      >
                        <option value="MH">Maharashtra State (category-based)</option>
                        <option value="AI">All India (merit-based, JEE or CET)</option>
                      </select>
                    </label>
                  )}

                  {studentType === "12th" && quota === "AI" && (
                    <label className="space-y-2 md:col-span-2">
                      <span className="text-sm font-medium text-slate-700">JEE (Main) Percentile</span>
                      <input
                        type="number"
                        min={0}
                        max={100}
                        step={0.01}
                        name="jee_percentile"
                        placeholder="Optional if you filled MHT CET Percentile above"
                        value={formData.jee_percentile}
                        onChange={handleChange}
                        className="w-full rounded-xl border border-slate-300 bg-white px-3 py-2.5 outline-none focus:border-emerald-500"
                      />
                      <span className="block text-xs text-slate-500">
                        All-India quota seats are filled by JEE or MHT-CET merit depending on the seat - fill in
                        whichever percentile you have (or both).
                      </span>
                    </label>
                  )}

                  {studentType === "12th" && quota === "MH" && (
                    <label className="space-y-2 md:col-span-2">
                      <span className="text-sm font-medium text-slate-700">Home University (where you passed 12th)</span>
                      <select
                        value={homeUniversity}
                        onChange={(e) => setHomeUniversity(e.target.value)}
                        className="w-full rounded-xl border border-slate-300 bg-white px-3 py-2.5 outline-none focus:border-emerald-500"
                      >
                        <option value="">Not sure / skip (State Level comparison only)</option>
                        {universities.map((u) => (
                          <option key={u.name} value={u.name}>{u.name}</option>
                        ))}
                      </select>
                      <span className="block text-xs text-slate-500">
                        Colleges reserve seats for candidates from their own university region, often at an easier
                        cutoff than the open State Level list - telling us yours lets us check both.
                      </span>
                    </label>
                  )}
                </div>
              </fieldset>

              <fieldset className="space-y-5">
                <legend className="text-xs font-bold uppercase tracking-[0.18em] text-emerald-700">3. Preferences (optional)</legend>
                <div className="grid gap-5">
                  <label className="space-y-2">
                    <span className="text-sm font-medium text-slate-700">Preferred Branches</span>
                    <div className="flex flex-wrap gap-2">
                      {branchOptions.map((branch) => {
                        const selected = formData.preferred_branches.includes(branch);
                        return (
                          <button
                            key={branch}
                            type="button"
                            onClick={() => {
                              setFormData((prev) => ({
                                ...prev,
                                preferred_branches: selected
                                  ? prev.preferred_branches.filter((item) => item !== branch)
                                  : [...prev.preferred_branches, branch],
                              }));
                            }}
                            className={`rounded-full border px-3 py-1.5 text-sm font-medium ${
                              selected
                                ? "border-emerald-500 bg-emerald-100 text-emerald-700"
                                : "border-slate-300 bg-slate-50 text-slate-700"
                            }`}
                          >
                            {branch}
                          </button>
                        );
                      })}
                    </div>
                  </label>

                  <label className="relative space-y-2">
                    <span className="text-sm font-medium text-slate-700">Specific Colleges</span>
                    <input
                      type="text"
                      value={collegeSearch}
                      onChange={(e) => setCollegeSearch(e.target.value)}
                      placeholder="Search by college name, e.g. COEP, VJTI, Pune..."
                      className="w-full rounded-xl border border-slate-300 bg-white px-3 py-2.5 outline-none focus:border-emerald-500"
                    />
                    {collegeSearch.trim().length >= 3 && (
                      <div className="absolute z-10 mt-1 max-h-64 w-full overflow-y-auto rounded-xl border border-slate-200 bg-white shadow-lg">
                        {collegeSearchLoading ? (
                          <p className="px-3 py-2.5 text-sm text-slate-500">Searching…</p>
                        ) : collegeResults.length > 0 ? (
                          collegeResults.map((college) => (
                            <button
                              key={college.id}
                              type="button"
                              onClick={() => addPreferredCollege(college)}
                              className="block w-full border-b border-slate-100 px-3 py-2.5 text-left text-sm last:border-0 hover:bg-emerald-50"
                            >
                              <span className="font-medium text-slate-900">{college.name}</span>
                              {college.status && <span className="block text-xs text-slate-500">{college.status}</span>}
                            </button>
                          ))
                        ) : (
                          <p className="px-3 py-2.5 text-sm text-slate-500">No colleges found.</p>
                        )}
                      </div>
                    )}
                    {preferredColleges.length > 0 && (
                      <div className="flex flex-wrap gap-2 pt-1">
                        {preferredColleges.map((college) => (
                          <span
                            key={college.id}
                            className="inline-flex items-center gap-2 rounded-full border border-emerald-500 bg-emerald-100 px-3 py-1.5 text-sm font-medium text-emerald-700"
                          >
                            {college.name}
                            <button
                              type="button"
                              onClick={() => removePreferredCollege(college.id)}
                              className="text-emerald-700 hover:text-emerald-900"
                              aria-label={`Remove ${college.name}`}
                            >
                              ×
                            </button>
                          </span>
                        ))}
                      </div>
                    )}
                    <span className="block text-xs text-slate-500">
                      Leave empty to check all colleges. If you add colleges here, results are limited to just these
                      (still narrowed by Preferred Branches above).
                    </span>
                  </label>

                  <label className="space-y-2">
                    <span className="text-sm font-medium text-slate-700">Preferred Districts</span>
                    <div className="flex flex-wrap gap-2">
                      {districts.slice(0, 12).map((d) => {
                        const selected = preferredDistricts.includes(d.name);
                        return (
                          <button
                            key={d.name}
                            type="button"
                            onClick={() => {
                              setPreferredDistricts((prev) =>
                                selected ? prev.filter((item) => item !== d.name) : [...prev, d.name]
                              );
                            }}
                            className={`rounded-full border px-3 py-1.5 text-sm font-medium ${
                              selected
                                ? "border-emerald-500 bg-emerald-100 text-emerald-700"
                                : "border-slate-300 bg-slate-50 text-slate-700"
                            }`}
                          >
                            {d.name}
                          </button>
                        );
                      })}
                    </div>
                    <span className="block text-xs text-slate-500">
                      Doesn't hide other colleges - just ranks colleges in your preferred districts higher within each
                      chance tier. District is best-effort (parsed from college names, not all colleges have one yet).
                    </span>
                  </label>
                </div>
              </fieldset>

              <button
                type="submit"
                disabled={loading}
                className="inline-flex w-full items-center justify-center rounded-xl bg-emerald-600 px-5 py-3 font-semibold text-white shadow-lg shadow-emerald-200 transition hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {loading ? "Predicting your matches..." : "Predict my colleges"}
              </button>
            </form>
          </div>

          <div className="space-y-5">
            <div className="rounded-[2rem] bg-slate-900 p-6 text-white shadow-xl sm:p-8">
              <p className="text-sm font-semibold uppercase tracking-[0.2em] text-emerald-300">Prediction summary</p>
              <h2 className="mt-3 text-2xl font-bold">{result?.student_name ?? formData.full_name}</h2>

              <div className="mt-6 grid gap-4 sm:grid-cols-2">
                <div className="rounded-2xl bg-white/5 p-4">
                  <p className="text-sm text-slate-300">{result?.score_label ?? "Score used"}</p>
                  <p className="mt-2 text-3xl font-black text-white">{result?.score_used ?? "--"}</p>
                </div>
                <div className="rounded-2xl bg-white/5 p-4">
                  <p className="text-sm text-slate-300">{result?.quota === "AI" ? "Quota / Exam" : "Category"}</p>
                  <p className="mt-2 text-2xl font-bold text-white">
                    {result?.quota === "AI" ? `All India (${result?.merit_exam})` : (result?.category ?? formData.category)}
                  </p>
                </div>
                <div className="rounded-2xl bg-white/5 p-4">
                  <p className="text-sm text-slate-300">High chance</p>
                  <p className="mt-2 text-3xl font-black text-emerald-300">{result?.summary?.high_chance ?? 0}</p>
                </div>
                <div className="rounded-2xl bg-white/5 p-4">
                  <p className="text-sm text-slate-300">Total matches</p>
                  <p className="mt-2 text-3xl font-black text-white">{result?.summary?.total_colleges ?? 0}</p>
                </div>
              </div>
            </div>

            <div className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
              <p className="text-sm font-semibold uppercase tracking-[0.2em] text-slate-500">Recommended now</p>
              <div className="mt-5 space-y-3">
                {(result?.recommended ?? fallbackPrediction.recommended).map((college: any) => (
                  <div key={college.id} className="rounded-2xl bg-slate-50 p-4">
                    <div className="flex items-center justify-between gap-3">
                      <div>
                        <p className="font-bold text-slate-900">{college.college_name}</p>
                        <p className="text-sm text-slate-500">{college.branch}</p>
                      </div>
                      <span
                        className={`rounded-full px-2 py-1 text-xs font-bold ${
                          college.chance === "HIGH"
                            ? "bg-emerald-100 text-emerald-700"
                            : college.chance === "MODERATE"
                              ? "bg-amber-100 text-amber-700"
                              : "bg-red-100 text-red-700"
                        }`}
                      >
                        {college.chance}
                      </span>
                    </div>
                    <p className="mt-3 text-sm text-slate-600">Cutoff: {college.cutoff}%</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-4 pb-20 sm:px-6">
        <div className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
          <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.2em] text-emerald-600">Results</p>
              <h2 className="mt-2 text-3xl font-bold text-slate-900">Best college matches</h2>
            </div>
            <button
              type="button"
              onClick={exportShortlistCsv}
              className="rounded-full border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 transition hover:border-emerald-400 hover:text-emerald-700"
            >
              Export shortlist (CSV)
            </button>
          </div>

          <div className="overflow-x-auto rounded-2xl border border-slate-200">
            <table className="min-w-full text-left text-sm">
              <thead className="bg-slate-100 text-slate-600">
                <tr>
                  <th className="px-4 py-3 font-semibold">College</th>
                  <th className="px-4 py-3 font-semibold">Status</th>
                  <th className="px-4 py-3 font-semibold">Branch</th>
                  <th className="px-4 py-3 font-semibold">Cutoff</th>
                  <th className="px-4 py-3 font-semibold">Chance</th>
                </tr>
              </thead>
              <tbody>
                {(result?.colleges ?? fallbackPrediction.colleges).map((college: any) => (
                  <tr key={college.id} className="border-t border-slate-200 text-slate-700">
                    <td className="px-4 py-3 font-semibold text-slate-900">{college.college_name}</td>
                    <td className="px-4 py-3">
                      {college.status ?? "—"}
                      {college.district && <span className="block text-xs text-slate-400">{college.district}</span>}
                    </td>
                    <td className="px-4 py-3">{college.branch}</td>
                    <td className="px-4 py-3">
                      {college.cutoff}%
                      {college.cutoff_level && college.cutoff_level !== "State Level" && (
                        <span className="ml-2 rounded-full bg-blue-100 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide text-blue-700">
                          {college.cutoff_level.startsWith("Home") ? "Home Univ" : "Other Univ"}
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`rounded-full px-2 py-1 text-xs font-bold ${
                          college.chance === "HIGH"
                            ? "bg-emerald-100 text-emerald-700"
                            : college.chance === "MODERATE"
                              ? "bg-amber-100 text-amber-700"
                              : "bg-red-100 text-red-700"
                        }`}
                      >
                        {college.chance}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>
    </main>
  );
}
