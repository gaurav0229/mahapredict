"use client";

import Link from "next/link";
import { use, useEffect, useState } from "react";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "https://mahapredict.onrender.com";

interface CollegeBranch {
  choice_code: string;
  course_name: string;
  latest_gopen_state_percentile: number | null;
}

interface CollegeDetails {
  id: string;
  name: string;
  status: string | null;
  home_university: string | null;
  website: string | null;
  branches: CollegeBranch[];
}

const emptyCollege: CollegeDetails = {
  id: "",
  name: "Loading college information",
  status: null,
  home_university: null,
  website: null,
  branches: [],
};

export default function CollegeDetailsPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params);
  const [college, setCollege] = useState<CollegeDetails>(emptyCollege);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadCollege = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/colleges/${resolvedParams.id}`);
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

  const percentiles = college.branches
    .map((b) => b.latest_gopen_state_percentile)
    .filter((p): p is number => typeof p === "number");
  const averagePercentile = percentiles.length ? percentiles.reduce((a, b) => a + b, 0) / percentiles.length : null;
  const topPercentile = percentiles.length ? Math.max(...percentiles) : null;

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
                  <p className="mt-2 text-lg text-slate-600">
                    {college.status ?? "Status unavailable"}
                    {college.home_university ? ` • Home University: ${college.home_university}` : ""}
                  </p>
                </div>
                {college.website && (
                  <a
                    href={college.website}
                    target="_blank"
                    rel="noreferrer"
                    className="rounded-full bg-emerald-600 px-5 py-3 text-sm font-semibold text-white shadow-lg shadow-emerald-200"
                  >
                    Visit official website
                  </a>
                )}
              </div>

              <div className="mt-8 grid gap-6 md:grid-cols-3">
                <div className="rounded-2xl bg-slate-50 p-4">
                  <p className="text-sm text-slate-500">Average GOPEN cutoff (State Level)</p>
                  <p className="mt-2 text-2xl font-bold">{averagePercentile ? `${averagePercentile.toFixed(1)}%` : "N/A"}</p>
                </div>
                <div className="rounded-2xl bg-slate-50 p-4">
                  <p className="text-sm text-slate-500">Highest branch cutoff</p>
                  <p className="mt-2 text-2xl font-bold">{topPercentile ? `${topPercentile.toFixed(1)}%` : "N/A"}</p>
                </div>
                <div className="rounded-2xl bg-slate-50 p-4">
                  <p className="text-sm text-slate-500">Branches</p>
                  <p className="mt-2 text-2xl font-bold">{college.branches.length}</p>
                </div>
              </div>
            </div>

            <div className="mt-8 rounded-3xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
              <h2 className="text-xl font-bold">Branches &amp; latest GOPEN cutoff (State Level)</h2>
              <p className="mt-1 text-sm text-slate-500">
                Figures shown are the most recent open-category, state-level percentile for each branch. Use the predictor
                for a chance estimate against your own category and score.
              </p>
              <div className="mt-5 space-y-3">
                {college.branches.map((branch) => (
                  <div key={branch.choice_code} className="flex items-center justify-between rounded-2xl bg-slate-50 px-4 py-3">
                    <div>
                      <p className="font-semibold text-slate-900">{branch.course_name}</p>
                      <p className="text-sm text-slate-500">Choice code: {branch.choice_code}</p>
                    </div>
                    <p className="font-bold text-slate-900">
                      {branch.latest_gopen_state_percentile != null ? `${branch.latest_gopen_state_percentile.toFixed(1)}%` : "N/A"}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          </>
        )}
      </div>
    </main>
  );
}
