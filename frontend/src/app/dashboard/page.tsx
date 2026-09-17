"use client";

import { useEffect, useState } from "react";

const fallbackStats = {
  total_colleges: 16,
  total_branches: 18,
  top_colleges: 6,
  districts: 9,
};

const fallbackColleges = [
  { id: "coep-pune", college_name: "COEP Technological University", city: "Pune", branch: "Computer Science", cutoff: 96.8, chance: "HIGH" },
  { id: "vjti-mumbai", college_name: "VJTI Mumbai", city: "Mumbai", branch: "Computer Science", cutoff: 94.9, chance: "HIGH" },
  { id: "walchand-sangli", college_name: "Walchand College of Engineering", city: "Sangli", branch: "Computer Science", cutoff: 89.7, chance: "MODERATE" },
  { id: "gcoen-nagpur", college_name: "Government College of Engineering, Nagpur", city: "Nagpur", branch: "Electrical", cutoff: 84.0, chance: "LOW" },
];

export default function DashboardPage() {
  const [stats, setStats] = useState(fallbackStats);
  const [colleges, setColleges] = useState(fallbackColleges);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadDashboard = async () => {
      try {
        const [dashboardRes, collegeRes] = await Promise.all([
          fetch("http://127.0.0.1:8000/dashboard"),
          fetch("http://127.0.0.1:8000/colleges?limit=5"),
        ]);

        if (dashboardRes.ok) {
          const dashboardData = await dashboardRes.json();
          setStats({
            total_colleges: dashboardData.total_colleges ?? fallbackStats.total_colleges,
            total_branches: dashboardData.total_branches ?? fallbackStats.total_branches,
            top_colleges: dashboardData.top_colleges ?? fallbackStats.top_colleges,
            districts: dashboardData.districts ?? fallbackStats.districts,
          });
        }

        if (collegeRes.ok) {
          const collegeData = await collegeRes.json();
          const mapped = (collegeData.items ?? fallbackColleges).map((college: any) => ({
            id: college.id,
            college_name: college.name,
            city: college.city,
            branch: college.branches?.[0] ?? "Computer Science",
            cutoff: college.latest_cutoff ?? college.average_cutoff ?? 0,
            chance: college.average_cutoff >= 90 ? "HIGH" : college.average_cutoff >= 80 ? "MODERATE" : "LOW",
          }));
          setColleges(mapped.slice(0, 4));
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
    { label: "Top Colleges", value: stats.top_colleges },
    { label: "Districts", value: stats.districts },
    { label: "Branches", value: stats.total_branches },
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
                      <p className="text-sm text-slate-500">{college.city} • {college.branch}</p>
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
              <p className="text-sm uppercase tracking-[0.2em] text-emerald-300">Profile</p>
              <h3 className="mt-3 text-2xl font-bold">Rahul Patil</h3>
              <ul className="mt-4 space-y-2 text-sm text-slate-300">
                <li>HSC: 93.4%</li>
                <li>CET: 168</li>
                <li>Category: GOPEN</li>
              </ul>
            </div>

            <div className="rounded-3xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
              <p className="text-sm uppercase tracking-[0.2em] text-slate-500">Decision guide</p>
              <ul className="mt-4 space-y-3 text-sm text-slate-700">
                <li>• Must apply: 3 colleges</li>
                <li>• Target: 5 colleges</li>
                <li>• Backup: 8 colleges</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
