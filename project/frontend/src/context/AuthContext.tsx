"use client";

import React, { createContext, useContext, useState, useEffect, ReactNode } from "react";
import { useRouter } from "next/navigation";
import { api, setAccessToken } from "@/lib/api";
import { jwtDecode } from "jwt-decode";
import { logout } from "@/lib/auth";

interface User {
    username: string;
    role: string;
}

interface AuthContextType {
    user: User | null;
    loading: boolean;
    handleLogout: () => void;
    setUser: React.Dispatch<React.SetStateAction<User | null>>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
    const [user, setUser] = useState<User | null>(null);
    const [loading, setLoading] = useState(true);
    const router = useRouter();

    // 1. Silent Refresh on Mount
    useEffect(() => {
        const silentRefresh = async () => {
            try {
                const res = await api.post("/auth/refresh");
                const { access_token } = res.data;

                setAccessToken(access_token);

                // Decode to set user context
                const decoded: any = jwtDecode(access_token);
                setUser({
                    username: decoded.sub,
                    role: decoded.role
                });

                // Update fast-render storage
                localStorage.setItem("username", decoded.sub);
                localStorage.setItem("role", decoded.role);

            } catch (err) {
                // If silent refresh fails, no problem, they just aren't logged in.
                console.log("No valid session found.");
            } finally {
                setLoading(false);
            }
        };

        silentRefresh();
    }, []);

    // 2. Listen for Auth Expiry Events (from axios interceptor)
    useEffect(() => {
        const handleAuthExpired = () => {
            setUser(null);
            localStorage.removeItem("username");
            localStorage.removeItem("role");
            router.push("/login"); // Force redirect to login
        };

        window.addEventListener("auth-expired", handleAuthExpired);
        return () => window.removeEventListener("auth-expired", handleAuthExpired);
    }, [router]);

    const handleLogout = async () => {
        await logout();
        setUser(null);
        router.push("/login");
    };

    return (
        <AuthContext.Provider value={{ user, loading, handleLogout, setUser }}>
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error("useAuth must be used within an AuthProvider");
    }
    return context;
}
