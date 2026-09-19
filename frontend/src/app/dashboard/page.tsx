"use client";

import { useEffect, useState } from "react";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "https://mahapredict.onrender.com";

// Illustrative profile used to populate this overview page with real, live
// recommendations. The predictor page lets a student use their own numbers.
const SAMPLE_PROFILE = {
  full_name: "Rahul Patil",
  email: "rahul@example.com",
  student_type: "12th" as const,
  city: "Pune",
  domicile: "Maharashtra" as const,
  hsc_percentage: 93.4,
  cet_percentile: 92.5,
  category: "GOPEN",
  preferred_branches: ["Computer Science", "Information Technology"],
  preferred_districts: ["Pune", "Mumbai"],
};

const fallbackStats = {
  total_colleges: 402,
  total_branches: 2511,
  top_colleges: 95,
  data_year: 2026,
};

const fallbackColleges = [
  { id: "coep-pune", college_name: "COEP Technological University", branch: "Computer Science", cutoff: 96.8, chance: "HIGH" },
  { id: "vjti-mumbai", college_name: "VJTI Mumbai", branch: "Computer Science", cutoff: 94.9, chance: "HIGH" },
  { id: "walchand-sangli", college_name: "Walchand College of Engineering", branch: "Computer Science", cutoff: 89.7, chance: "MODERATE" },
  { id: "gcoen-nagpur", college_name: "Government College of Engineering, Nagpur", branch: "Electrical", cutoff: 84.0, chance: "LOW" },
];

export default function DashboardPage() {
  const [stats, setStats] = useState(fallbackStats);
  const [colleges, setColleges] = useState(fallbackColleges);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadDashboard = async () => {
      try {
        const [dashboardRes, predictRes] = await Promise.all([
          fetch(`${API_BASE_URL}/dashboard`),
          fetch(`${API_BASE_URL}/predict`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(SAMPLE_PROFILE),
          }),
        ]);

        if (dashboardRes.ok) {
          const dashboardData = await dashboardRes.json();
          setStats({
            total_colleges: dashboardData.total_colleges ?? fallbackStats.total_colleges,
            total_branches: dashboardData.total_branches ?? fallbackStats.total_branches,
            top_colleges: dashboardData.top_colleges ?? fallbackStats.top_colleges,
            data_year: dashboardData.data_year ?? fallbackStats.data_year,
          });
        }

        if (predictRes.ok) {
          const predictData = await predictRes.json();
          const mapped = (predictData.recommended ?? []).map((college: any) => ({
            id: college.id,
            college_name: college.college_name,
            branch: college.branch,
            cutoff: college.cutoff,
            chance: college.chance,
          }));
          if (mapped.length > 0) setColleges(mapped.slice(0, 4));
        }
      } catch (error) {
        console.warn("Dashboard backend not available; using fallback data.", error);
      } finally {
        setLoading(false);
      }
    };

    loadDashboard();
  }, []);

  const statCards = [
    { label: "Total Colleges", value: stats.total_colleges },
    { label: "Top Colleges (85%+)", value: stats.top_colleges },
    { label: "Branches", value: stats.total_branches },
    { label: "Data Year", value: stats.data_year },
  ];

  return (
    <main className="min-h-screen bg-slate-50 px-6 py-10 text-slate-900">
      <div className="mx-auto max-w-7xl">
        <div className="mb-8">
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-emerald-600">Student dashboard</p>
          <h1 className="mt-3 text-4xl font-black">Admission performance overview</h1>
        </div>

        <div className="grid gap-6 md:grid-cols-4">
          {statCards.map((card) => (
            <div key={card.label} className="rounded-3xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
              <p className="text-sm text-slate-500">{card.label}</p>
              <p className="mt-3 text-3xl font-bold text-slate-900">{card.value}</p>
            </div>
          ))}
        </div>

        <div className="mt-10 grid gap-8 lg:grid-cols-[1.3fr_0.7fr]">
          <div className="rounded-3xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-xl font-bold">Recommended colleges</h2>
              <button className="rounded-full border border-slate-300 px-3 py-1.5 text-sm font-medium">Export PDF</button>
            </div>

            {loading ? (
              <div className="rounded-2xl bg-slate-50 p-4 text-sm text-slate-500">Loading live recommendations…</div>
            ) : (
              <div className="space-y-4">
                {colleges.map((college, index) => (
                  <div key={college.id ?? college.college_name} className="flex items-center justify-between rounded-2xl bg-slate-50 p-4">
                    <div>
                      <p className="font-semibold text-slate-900">{index + 1}. {college.college_name}</p>
                      <p className="text-sm text-slate-500">{college.branch}</p>
                    </div>
                    <div className="text-right">
                      <p className="font-bold text-slate-900">{college.cutoff.toFixed ? `${college.cutoff.toFixed(1)}%` : `${college.cutoff}%`}</p>
                      <span className="rounded-full bg-emerald-100 px-2 py-1 text-xs font-bold text-emerald-700">
                        {college.chance}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="space-y-6">
            <div className="rounded-3xl bg-slate-900 p-6 text-white shadow-xl">
              <p className="text-sm uppercase tracking-[0.2em] text-emerald-300">Sample profile</p>
              <h3 className="mt-3 text-2xl font-bold">{SAMPLE_PROFILE.full_name}</h3>
              <ul className="mt-4 space-y-2 text-sm text-slate-300">
                <li>HSC: {SAMPLE_PROFILE.hsc_percentage}%</li>
                <li>CET Percentile: {SAMPLE_PROFILE.cet_percentile}</li>
                <li>Category: {SAMPLE_PROFILE.category}</li>
              </ul>
            </div>

            <div className="rounded-3xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
              <p className="text-sm uppercase tracking-[0.2em] text-slate-500">Want your own numbers?</p>
              <p className="mt-3 text-sm text-slate-700">
                This overview uses a sample profile. Head to the predictor to enter your own percentile, category and
                preferred branches for a personal shortlist.
              </p>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
