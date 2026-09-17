"use client";

import Link from "next/link";
import { use, useEffect, useState } from "react";

interface CollegeDetails {
  id: string;
  name: string;
  city: string;
  district: string;
  college_type: string;
  official_website: string;
  total_seats: number;
  average_cutoff: number;
  branches: string[];
  cutoff_history: Array<{
    year: string;
    category: string;
    branch: string;
    cutoff: number;
    trend: string;
  }>;
}

const emptyCollege: CollegeDetails = {
  id: "",
  name: "Loading college information",
  city: "",
  district: "",
  college_type: "",
  official_website: "",
  total_seats: 0,
  average_cutoff: 0,
  branches: [],
  cutoff_history: [],
};

export default function CollegeDetailsPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params);
  const [college, setCollege] = useState<CollegeDetails>(emptyCollege);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadCollege = async () => {
      try {
        const response = await fetch(`http://127.0.0.1:8000/colleges/${resolvedParams.id}`);
        if (!response.ok) return;
        const data = await response.json();
        setCollege(data);
      } catch (error) {
        console.warn("College detail API not available.", error);
      } finally {
        setLoading(false);
      }
    };

    loadCollege();
  }, [resolvedParams.id]);

  const latestCutoff = college.cutoff_history?.[college.cutoff_history.length - 1];

  return (
    <main className="min-h-screen bg-slate-50 px-6 py-10 text-slate-900">
      <div className="mx-auto max-w-6xl">
        <Link href="/colleges" className="mb-6 inline-flex items-center text-sm font-semibold text-emerald-700 hover:text-emerald-800">
          ← Back to colleges
        </Link>

        {loading ? (
          <div className="rounded-3xl bg-white p-8 shadow-sm ring-1 ring-slate-200">Loading college profile…</div>
        ) : (
          <>
            <div className="rounded-3xl bg-white p-8 shadow-sm ring-1 ring-slate-200">
              <div className="flex flex-col gap-6 lg:flex-row lg:items-start lg:justify-between">
                <div>
                  <p className="text-sm font-semibold uppercase tracking-[0.2em] text-emerald-600">College profile</p>
                  <h1 className="mt-3 text-4xl font-black">{college.name}</h1>
                  <p className="mt-2 text-lg text-slate-600">{college.city}, {college.district} • {college.college_type}</p>
                </div>
                <a
                  href={college.official_website}
                  target="_blank"
                  rel="noreferrer"
                  className="rounded-full bg-emerald-600 px-5 py-3 text-sm font-semibold text-white shadow-lg shadow-emerald-200"
                >
                  Visit official website
                </a>
              </div>

              <div className="mt-8 grid gap-6 md:grid-cols-4">
                <div className="rounded-2xl bg-slate-50 p-4">
                  <p className="text-sm text-slate-500">Average cutoff</p>
                  <p className="mt-2 text-2xl font-bold">{college.average_cutoff.toFixed(1)}%</p>
                </div>
                <div className="rounded-2xl bg-slate-50 p-4">
                  <p className="text-sm text-slate-500">Total seats</p>
                  <p className="mt-2 text-2xl font-bold">{college.total_seats}</p>
                </div>
                <div className="rounded-2xl bg-slate-50 p-4">
                  <p className="text-sm text-slate-500">Latest cutoff</p>
                  <p className="mt-2 text-2xl font-bold">{latestCutoff ? `${latestCutoff.cutoff.toFixed(1)}%` : "N/A"}</p>
                </div>
                <div className="rounded-2xl bg-slate-50 p-4">
                  <p className="text-sm text-slate-500">Branches</p>
                  <p className="mt-2 text-2xl font-bold">{college.branches.length}</p>
                </div>
              </div>
            </div>

            <div className="mt-8 grid gap-8 lg:grid-cols-[0.9fr_1.1fr]">
              <div className="rounded-3xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
                <h2 className="text-xl font-bold">Available branches</h2>
                <div className="mt-5 flex flex-wrap gap-2">
                  {college.branches.map((branch) => (
                    <span key={branch} className="rounded-full bg-emerald-100 px-3 py-1.5 text-sm font-medium text-emerald-800">
                      {branch}
                    </span>
                  ))}
                </div>
              </div>

              <div className="rounded-3xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
                <h2 className="text-xl font-bold">Cutoff trend</h2>
                <div className="mt-5 space-y-4">
                  {college.cutoff_history?.map((entry) => (
                    <div key={`${entry.year}-${entry.category}-${entry.branch}`} className="flex items-center justify-between rounded-2xl bg-slate-50 px-4 py-3">
                      <div>
                        <p className="font-semibold text-slate-900">{entry.year}</p>
                        <p className="text-sm text-slate-500">{entry.category} • {entry.branch}</p>
                      </div>
                      <div className="text-right">
                        <p className="font-bold text-slate-900">{entry.cutoff.toFixed(1)}%</p>
                        <p className="text-xs uppercase tracking-[0.12em] text-emerald-600">{entry.trend}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </main>
  );
}
