"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/context/AuthContext";
import { toast } from "react-hot-toast";
import { api } from "@/lib/api";

interface User {
    id: string;
    username: string;
    email: string;
    role: string;
    created_at: string;
}

interface Role {
    id: string;
    name: string;
    description: string;
}

export default function AdminPage() {
    const { user } = useAuth();
    const [users, setUsers] = useState<User[]>([]);
    const [availableRoles, setAvailableRoles] = useState<Role[]>([]);
    const [loading, setLoading] = useState(true);

    const fetchUsers = async () => {
        try {
            const res = await api.get("/admin/users");
            setUsers(res.data);
        } catch (err: any) {
            toast.error(err.response?.data?.detail || err.message);
        }
    };

    const fetchRoles = async () => {
        try {
            const res = await api.get("/admin/roles");
            setAvailableRoles(res.data);
        } catch (err: any) {
            toast.error(err.response?.data?.detail || err.message);
        }
    };

    useEffect(() => {
        if (user) {
            Promise.all([fetchUsers(), fetchRoles()]).finally(() => setLoading(false));
        }
    }, [user]);

    const handleRoleChange = async (userId: string, targetRole: string) => {
        try {
            await api.post("/admin/assign-role", {
                user_id: userId,
                role_name: targetRole
            });

            toast.success("Role updated successfully");
            fetchUsers(); // Refresh the list
        } catch (err: any) {
            toast.error(err.response?.data?.detail || err.message);
        }
    };

    if (loading) return <div className="p-8">Loading administrative data...</div>;

    return (
        <div className="p-8">
            <header className="mb-8">
                <h1 className="text-3xl font-bold text-gray-800">User Management</h1>
                <p className="text-gray-600">Assign and manage system-wide roles and permissions.</p>
            </header>

            <div className="bg-white shadow-xl rounded-2xl overflow-hidden border border-gray-100">
                <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                        <tr>
                            <th className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Username</th>
                            <th className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Email</th>
                            <th className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Current Role</th>
                            <th className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Change Role</th>
                        </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                        {users.map((u) => (
                            <tr key={u.id} className="hover:bg-gray-50 transition-colors">
                                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{u.username}</td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{u.email}</td>
                                <td className="px-6 py-4 whitespace-nowrap">
                                    <span className={`px-2.5 py-1 text-xs font-medium rounded-full ${u.role === 'SuperAdmin' ? 'bg-purple-100 text-purple-800' :
                                        u.role === 'Admin' ? 'bg-blue-100 text-blue-800' :
                                            'bg-gray-100 text-gray-800'
                                        }`}>
                                        {u.role}
                                    </span>
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                    <select
                                        className="block w-full px-3 py-1.5 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                                        value={u.role}
                                        onChange={(e) => handleRoleChange(u.id, e.target.value)}
                                    >
                                        {availableRoles.map((r) => (
                                            <option key={r.id} value={r.name}>
                                                {r.name}
                                            </option>
                                        ))}
                                    </select>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
