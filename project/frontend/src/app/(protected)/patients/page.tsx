"use client";
import React from "react";

import { useState } from "react";
import {
  usePatients,
  useCreatePatient,
  useUpdatePatient,
  useDeletePatient,
} from "@/hooks/usePatients";
import { Patient } from "@/lib/types";
import { FileText, ChevronDown, ChevronUp } from "lucide-react";
import PatientDatasets from "@/components/PatientDatasets";

export default function PatientsPage() {
  const { data: patients = [], isLoading } = usePatients();
  const createMutation = useCreatePatient();
  const updateMutation = useUpdatePatient();
  const deleteMutation = useDeletePatient();

  const [search, setSearch] = useState("");
  const [genderFilter, setGenderFilter] = useState("");
  const [editingId, setEditingId] = useState<string | null>(null);
  const [expandedId, setExpandedId] = useState<string | null>(null);


  const [form, setForm] = useState({
    name: "",
    age: "",
    gender: "",
    height_cm: "",
  });

  const handleSubmit = async () => {
    const payload = {
      name: form.name,
      age: Number(form.age),
      gender: form.gender,
      height_cm: Number(form.height_cm),
    };

    if (editingId) {
      await updateMutation.mutateAsync({ id: editingId, patient: payload });
    } else {
      await createMutation.mutateAsync(payload);
    }

    setForm({ name: "", age: "", gender: "", height_cm: "" });
    setEditingId(null);
  };

  const handleEdit = (p: Patient) => {
    setEditingId(p.patient_id);
    setForm({
      name: p.name,
      age: p.age.toString(),
      gender: p.gender,
      height_cm: p.height_cm.toString(),
    });
  };

  const handleDelete = async (id: string) => {
    await deleteMutation.mutateAsync(id);
  };

  const filteredPatients = patients
    .filter((p) => p.name.toLowerCase().includes(search.toLowerCase()))
    .filter((p) => (genderFilter ? p.gender === genderFilter : true));

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">Patients</h1>

      {/* ADD / EDIT FORM */}
      <div className="bg-white p-4 rounded shadow mb-6">
        <h2 className="font-semibold mb-3">
          {editingId ? "Edit Patient" : "Add Patient"}
        </h2>

        <div className="grid grid-cols-2 gap-4 mb-4">
          <input
            className="border p-2 rounded"
            placeholder="Name"
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
          />
          <input
            type="number"
            className="border p-2 rounded"
            placeholder="Age"
            value={form.age}
            onChange={(e) => setForm({ ...form, age: e.target.value })}
          />
          <input
            className="border p-2 rounded"
            placeholder="Gender"
            value={form.gender}
            onChange={(e) => setForm({ ...form, gender: e.target.value })}
          />
          <input
            type="number"
            className="border p-2 rounded"
            placeholder="Height (cm)"
            value={form.height_cm}
            onChange={(e) => setForm({ ...form, height_cm: e.target.value })}
          />
        </div>

        <button
          onClick={handleSubmit}
          className="bg-blue-600 text-white px-4 py-2 rounded"
        >
          {editingId ? "Update Patient" : "Add Patient"}
        </button>
      </div>

      {/* SEARCH */}
      <div className="mb-4 flex gap-4">
        <input
          className="border p-2 rounded w-1/2"
          placeholder="Search by name"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />

        <select
          className="border p-2 rounded"
          value={genderFilter}
          onChange={(e) => setGenderFilter(e.target.value)}
        >
          <option value="">All</option>
          <option value="male">Male</option>
          <option value="female">Female</option>
        </select>
      </div>

      {/* TABLE */}
      <table className="w-full border">
        <thead>
          <tr className="bg-gray-100">
            <th className="p-2 border">Name</th>
            <th className="p-2 border">Age</th>
            <th className="p-2 border">Gender</th>
            <th className="p-2 border">Height</th>
            <th className="p-2 border">Actions</th>
          </tr>
        </thead>
        <tbody>
          {filteredPatients.map((p) => (
            <React.Fragment key={p.patient_id}>
              <tr className="hover:bg-gray-50 transition-colors">
                <td className="border p-2">{p.name}</td>
                <td className="border p-2">{p.age}</td>
                <td className="border p-2">{p.gender}</td>
                <td className="border p-2">{p.height_cm}</td>
                <td className="border p-2 space-x-2">
                  <button
                    className="text-indigo-600 hover:text-indigo-800 font-medium flex inline-flex items-center gap-1"
                    onClick={() => setExpandedId(expandedId === p.patient_id ? null : p.patient_id)}
                  >
                    <FileText size={16} />
                    Datasets
                    {expandedId === p.patient_id ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                  </button>
                  <button
                    className="text-blue-600 ml-4 hover:underline"
                    onClick={() => handleEdit(p)}
                  >
                    Edit
                  </button>
                  <button
                    className="text-red-600 hover:underline"
                    onClick={() => handleDelete(p.patient_id)}
                  >
                    Delete
                  </button>
                </td>
              </tr>
              {expandedId === p.patient_id && (
                <tr>
                  <td colSpan={5} className="p-0 border-b border-gray-200">
                    <PatientDatasets patientId={p.patient_id} />
                  </td>
                </tr>
              )}
            </React.Fragment>
          ))}
        </tbody>
      </table>
    </div>
  );
}
