"use client";

import { useState } from "react";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "https://mahapredict.onrender.com";

const categoryOptions = [
  "GOPEN",
  "GOBSC",
  "GOSC",
  "GOST",
  "LOPEN",
  "LOBSC",
  "LOSC",
  "LOST",
  "EWS",
  "TFWS",
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
  const [formData, setFormData] = useState({
    full_name: "Rahul Patil",
    email: "rahul@example.com",
    city: "Pune",
    domicile: "Maharashtra",
    hsc_percentage: 93.4,
    cet_percentile: 92.5,
    category: "GOPEN",
    preferred_branches: ["Computer Science", "Information Technology"],
  });
  const [result, setResult] = useState<any>(fallbackPrediction);
  const [loading, setLoading] = useState(false);

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
      city: formData.city,
      domicile: formData.domicile,
      hsc_percentage: studentType === "12th" ? Number(formData.hsc_percentage) : null,
      cet_percentile: studentType === "12th" ? Number(formData.cet_percentile) : null,
      diploma_percentage: studentType === "diploma" ? Number(formData.hsc_percentage) : null,
      category: formData.category,
      preferred_branches: formData.preferred_branches,
      preferred_districts: ["Pune", "Mumbai"],
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

            <form onSubmit={handleSubmit} className="mt-8 space-y-5">
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

                <label className="space-y-2">
                  <span className="text-sm font-medium text-slate-700">City / District</span>
                  <input
                    name="city"
                    value={formData.city}
                    onChange={handleChange}
                    className="w-full rounded-xl border border-slate-300 bg-white px-3 py-2.5 outline-none focus:border-emerald-500"
                  />
                </label>

                <label className="space-y-2">
                  <span className="text-sm font-medium text-slate-700">Domicile</span>
                  <select
                    name="domicile"
                    value={formData.domicile}
                    onChange={handleChange}
                    className="w-full rounded-xl border border-slate-300 bg-white px-3 py-2.5 outline-none focus:border-emerald-500"
                  >
                    <option value="Maharashtra">Maharashtra</option>
                    <option value="Non-Maharashtra">Non-Maharashtra</option>
                  </select>
                </label>

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

                <label className="space-y-2 md:col-span-2">
                  <span className="text-sm font-medium text-slate-700">Category</span>
                  <select
                    name="category"
                    value={formData.category}
                    onChange={handleChange}
                    className="w-full rounded-xl border border-slate-300 bg-white px-3 py-2.5 outline-none focus:border-emerald-500"
                  >
                    {categoryOptions.map((category) => (
                      <option key={category} value={category}>{category}</option>
                    ))}
                  </select>
                </label>

                <label className="space-y-2 md:col-span-2">
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
              </div>

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
                  <p className="text-sm text-slate-300">Score used</p>
                  <p className="mt-2 text-3xl font-black text-white">{result?.score_used ?? "--"}</p>
                </div>
                <div className="rounded-2xl bg-white/5 p-4">
                  <p className="text-sm text-slate-300">Category</p>
                  <p className="mt-2 text-2xl font-bold text-white">{result?.category ?? formData.category}</p>
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
            <button className="rounded-full border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700">
              Export shortlist
            </button>
          </div>

          <div className="overflow-hidden rounded-2xl border border-slate-200">
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
                    <td className="px-4 py-3">{college.status ?? "—"}</td>
                    <td className="px-4 py-3">{college.branch}</td>
                    <td className="px-4 py-3">{college.cutoff}%</td>
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
