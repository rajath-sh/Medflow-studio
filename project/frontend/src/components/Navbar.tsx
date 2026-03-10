"use client";

import Link from "next/link";
import { useAuth } from "@/context/AuthContext";

export default function Navbar() {
  const { user, handleLogout } = useAuth();

  // Safe fallback if user state hasn't painted yet
  const role = user?.role || (typeof window !== "undefined" ? localStorage.getItem("role") : null);

  return (
    <nav className="bg-white shadow-md px-6 py-3 flex justify-between items-center">
      <h1 className="text-xl font-bold text-blue-600">MedFlow</h1>

      <div className="flex items-center gap-4">
        <Link href="/dashboard" className="hover:text-blue-600">
          Dashboard
        </Link>

        <Link href="/patients" className="hover:text-blue-600">
          Patients
        </Link>

        <Link href="/datasets" className="hover:text-blue-600">
          Datasets
        </Link>


        <Link href="/workflow" className="hover:text-blue-600">
          Workflow Builder
        </Link>

        <Link href="/jobs" className="hover:text-blue-600">
          Jobs
        </Link>

        <Link href="/ai" className="hover:text-blue-600">
          AI
        </Link>

        {(role === "SuperAdmin" || role === "Admin") && (
          <Link href="/admin" className="hover:text-blue-600 font-semibold text-purple-600">
            Admin
          </Link>
        )}

        <button
          onClick={handleLogout}
          className="bg-red-500 text-white px-3 py-1 rounded hover:bg-red-600"
        >
          Logout
        </button>
      </div>
    </nav>
  );
}
