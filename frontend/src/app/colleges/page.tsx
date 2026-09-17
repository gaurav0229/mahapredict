"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

const fallbackColleges = [
  {
    id: "coep-pune",
    name: "COEP Technological University",
    city: "Pune",
    district: "Pune",
    type: "Government",
    website: "https://www.coeptech.ac.in/",
    seats: 1200,
    average_cutoff: 95.4,
    latest_cutoff: 96.8,
    branches: ["Computer Science", "Information Technology", "Electronics"],
  },
  {
    id: "vjti-mumbai",
    name: "VJTI Mumbai",
    city: "Mumbai",
    district: "Mumbai",
    type: "Government",
    website: "https://www.vjti.ac.in/",
    seats: 1080,
    average_cutoff: 93.5,
    latest_cutoff: 94.9,
    branches: ["Computer Science", "Electronics", "Mechanical"],
  },
  {
    id: "spit-mumbai",
    name: "Sardar Patel Institute of Technology",
    city: "Mumbai",
    district: "Mumbai",
    type: "Private Autonomous",
    website: "https://www.spit.ac.in/",
    seats: 720,
    average_cutoff: 91.8,
    latest_cutoff: 92.6,
    branches: ["Information Technology", "Computer Science"],
  },
];

export default function CollegesPage() {
  const [colleges, setColleges] = useState(fallbackColleges);

  useEffect(() => {
    const loadColleges = async () => {
      try {
        const response = await fetch("http://127.0.0.1:8000/colleges?limit=20");
        if (!response.ok) return;
        const data = await response.json();
        if (Array.isArray(data.items) && data.items.length > 0) {
          setColleges(data.items);
        }
      } catch (error) {
        console.warn("College API not available; using fallback listing.", error);
      }
    };

    loadColleges();
  }, []);

  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(16,185,129,0.18),_transparent_30%),linear-gradient(135deg,#0f172a_0%,#111827_38%,#0f172a_100%)] px-6 py-10 text-slate-900">
      <div className="mx-auto max-w-7xl">
        <div className="mb-8 flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.2em] text-emerald-300">College directory</p>
            <h1 className="mt-3 text-4xl font-black text-white md:text-5xl">Maharashtra Engineering Colleges</h1>
          </div>
          <button className="rounded-full bg-white/10 px-5 py-2.5 text-sm font-semibold text-white ring-1 ring-white/20 backdrop-blur-sm">Filter & sort</button>
        </div>

        <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-3">
          {colleges.map((college) => (
            <div key={college.id} className="rounded-3xl border border-white/10 bg-white/10 p-5 shadow-xl backdrop-blur-sm">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="text-xl font-bold text-white">{college.name}</p>
                  <p className="mt-2 text-sm text-slate-200">{college.city} • {college.type}</p>
                </div>
                <span className="rounded-full bg-emerald-500/20 px-2 py-1 text-xs font-bold text-emerald-200">High</span>
              </div>

              <div className="mt-6 space-y-3 text-sm text-slate-200">
                <div className="flex justify-between"><span>Top branch</span><strong className="text-white">{college.branches?.[0] ?? "Computer Science"}</strong></div>
                <div className="flex justify-between"><span>Cutoff</span><strong className="text-white">{(college.latest_cutoff ?? college.average_cutoff ?? 0).toFixed(1)}%</strong></div>
                <div className="flex justify-between"><span>Seats</span><strong className="text-white">{college.seats ?? 0}</strong></div>
                <div className="flex justify-between"><span>Trend</span><strong className="text-white">{college.average_cutoff >= 90 ? "Up trending" : "Stable"}</strong></div>
              </div>

              <div className="mt-6 flex gap-3">
                <a href={college.website} target="_blank" rel="noreferrer" className="flex-1 rounded-xl border border-white/20 bg-white/5 px-3 py-2 text-center text-sm font-semibold text-white hover:bg-white/10">Website</a>
                <Link href={`/colleges/${college.id}`} className="flex-1 rounded-xl bg-emerald-500 px-3 py-2 text-center text-sm font-semibold text-white hover:bg-emerald-600">View details</Link>
              </div>
            </div>
          ))}
        </div>
      </div>
    </main>
  );
}
