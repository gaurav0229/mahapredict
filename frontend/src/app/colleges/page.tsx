"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "https://mahapredict.onrender.com";
const PAGE_SIZE = 24;

const fallbackColleges = [
  {
    id: "coep-pune",
    name: "COEP Technological University",
    status: "Government Autonomous",
    home_university: "Autonomous Institute",
    website: "https://www.coeptech.ac.in/",
    branches: ["Computer Science", "Information Technology", "Electronics"],
  },
  {
    id: "vjti-mumbai",
    name: "VJTI Mumbai",
    status: "Government Autonomous",
    home_university: "Autonomous Institute",
    website: "https://www.vjti.ac.in/",
    branches: ["Computer Science", "Electronics", "Mechanical"],
  },
  {
    id: "spit-mumbai",
    name: "Sardar Patel Institute of Technology",
    status: "Un-Aided Autonomous",
    home_university: "Mumbai University",
    website: "https://www.spit.ac.in/",
    branches: ["Information Technology", "Computer Science"],
  },
];

export default function CollegesPage() {
  const [colleges, setColleges] = useState(fallbackColleges);
  const [total, setTotal] = useState<number | null>(null);
  const [page, setPage] = useState(0);
  const [branchFilter, setBranchFilter] = useState("");
  const [branchInput, setBranchInput] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const controller = new AbortController();
    const loadColleges = async () => {
      setLoading(true);
      try {
        const params = new URLSearchParams({
          limit: String(PAGE_SIZE),
          offset: String(page * PAGE_SIZE),
        });
        if (branchFilter) params.set("branch", branchFilter);

        const response = await fetch(`${API_BASE_URL}/colleges?${params}`, { signal: controller.signal });
        if (!response.ok) return;
        const data = await response.json();
        if (Array.isArray(data.items)) {
          setColleges(data.items);
          setTotal(typeof data.total === "number" ? data.total : data.items.length);
        }
      } catch (error) {
        if ((error as Error).name !== "AbortError") {
          console.warn("College API not available; using fallback listing.", error);
        }
      } finally {
        setLoading(false);
      }
    };

    loadColleges();
    return () => controller.abort();
  }, [page, branchFilter]);

  const totalPages = total ? Math.max(1, Math.ceil(total / PAGE_SIZE)) : 1;

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(0);
    setBranchFilter(branchInput.trim());
  };

  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(16,185,129,0.18),_transparent_30%),linear-gradient(135deg,#0f172a_0%,#111827_38%,#0f172a_100%)] px-6 py-10 text-slate-900">
      <div className="mx-auto max-w-7xl">
        <div className="mb-8 flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.2em] text-emerald-300">College directory</p>
            <h1 className="mt-3 text-4xl font-black text-white md:text-5xl">Maharashtra Engineering Colleges</h1>
            {total !== null && (
              <p className="mt-2 text-sm text-slate-300">
                {total} college{total === 1 ? "" : "s"}{branchFilter ? ` offering "${branchFilter}"` : ""}
              </p>
            )}
          </div>
          <form onSubmit={handleSearch} className="flex gap-2">
            <input
              value={branchInput}
              onChange={(e) => setBranchInput(e.target.value)}
              placeholder="Search by branch (e.g. Computer)"
              className="w-56 rounded-full border border-white/20 bg-white/10 px-4 py-2.5 text-sm text-white placeholder:text-slate-400 outline-none focus:border-emerald-400"
            />
            <button type="submit" className="rounded-full bg-emerald-500 px-5 py-2.5 text-sm font-semibold text-white hover:bg-emerald-600">
              Search
            </button>
            {branchFilter && (
              <button
                type="button"
                onClick={() => {
                  setBranchInput("");
                  setBranchFilter("");
                  setPage(0);
                }}
                className="rounded-full bg-white/10 px-4 py-2.5 text-sm font-semibold text-white ring-1 ring-white/20 hover:bg-white/20"
              >
                Clear
              </button>
            )}
          </form>
        </div>

        <div className={`grid gap-6 md:grid-cols-2 xl:grid-cols-3 ${loading ? "opacity-50" : ""}`}>
          {colleges.map((college) => (
            <div key={college.id} className="rounded-3xl border border-white/10 bg-white/10 p-5 shadow-xl backdrop-blur-sm">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="text-xl font-bold text-white">{college.name}</p>
                  <p className="mt-2 text-sm text-slate-200">{college.status}</p>
                </div>
              </div>

              <div className="mt-6 space-y-3 text-sm text-slate-200">
                <div className="flex justify-between"><span>Home university</span><strong className="text-white">{college.home_university ?? "—"}</strong></div>
                <div className="flex justify-between"><span>Top branch</span><strong className="text-white">{college.branches?.[0] ?? "—"}</strong></div>
                <div className="flex justify-between"><span>Branches offered</span><strong className="text-white">{college.branches?.length ?? 0}</strong></div>
              </div>

              <div className="mt-6 flex gap-3">
                {college.website && (
                  <a href={college.website} target="_blank" rel="noreferrer" className="flex-1 rounded-xl border border-white/20 bg-white/5 px-3 py-2 text-center text-sm font-semibold text-white hover:bg-white/10">Website</a>
                )}
                <Link href={`/colleges/${college.id}`} className="flex-1 rounded-xl bg-emerald-500 px-3 py-2 text-center text-sm font-semibold text-white hover:bg-emerald-600">View details</Link>
              </div>
            </div>
          ))}
        </div>

        {colleges.length === 0 && !loading && (
          <p className="mt-10 text-center text-slate-300">No colleges found{branchFilter ? ` for "${branchFilter}"` : ""}.</p>
        )}

        {total !== null && totalPages > 1 && (
          <div className="mt-10 flex items-center justify-center gap-4">
            <button
              onClick={() => setPage((p) => Math.max(0, p - 1))}
              disabled={page === 0 || loading}
              className="rounded-full bg-white/10 px-5 py-2.5 text-sm font-semibold text-white ring-1 ring-white/20 hover:bg-white/20 disabled:cursor-not-allowed disabled:opacity-40"
            >
              ← Previous
            </button>
            <span className="text-sm text-slate-300">
              Page {page + 1} of {totalPages}
            </span>
            <button
              onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
              disabled={page + 1 >= totalPages || loading}
              className="rounded-full bg-white/10 px-5 py-2.5 text-sm font-semibold text-white ring-1 ring-white/20 hover:bg-white/20 disabled:cursor-not-allowed disabled:opacity-40"
            >
              Next →
            </button>
          </div>
        )}
      </div>
    </main>
  );
}
