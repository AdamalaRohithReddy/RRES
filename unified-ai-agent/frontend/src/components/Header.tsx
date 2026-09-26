import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { api } from '../api/client';
import { Shield, User, LogOut, CheckCircle2, AlertTriangle } from 'lucide-react';

export const Header: React.FC = () => {
  const { name, citizen_id, username, logout } = useAuth();
  const [healthStatus, setHealthStatus] = useState<'UP' | 'DEGRADED' | 'DOWN' | 'CHECKING'>('CHECKING');

  useEffect(() => {
    async function checkHealth() {
      try {
        const res = await api.getHealthReady();
        if (res.status === 'UP') {
          setHealthStatus('UP');
        } else {
          setHealthStatus('DEGRADED');
        }
      } catch {
        setHealthStatus('DOWN');
      }
    }
    checkHealth();
    const interval = setInterval(checkHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="bg-white border-b border-slate-200 sticky top-0 z-30 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo and Portal Title */}
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-lg bg-govblue-600 flex items-center justify-center text-white font-bold shadow">
              <Shield className="w-6 h-6 text-amber-400" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-bold text-lg text-govblue-700 tracking-tight">JanSeva AI</span>
                <span className="text-xs bg-govblue-100 text-govblue-700 font-semibold px-2 py-0.5 rounded-full">
                  Citizen Support
                </span>
              </div>
              <p className="text-xs text-slate-500">Unified Financial & Social Support Assistant</p>
            </div>
          </div>

          {/* Right Header Status & Profile */}
          <div className="flex items-center space-x-4">
            {/* System Health Badge */}
            <div className="hidden md:flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-medium border border-slate-200 bg-slate-50">
              {healthStatus === 'UP' && (
                <>
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
                  <span className="text-emerald-700">Services Active</span>
                </>
              )}
              {healthStatus === 'DEGRADED' && (
                <>
                  <AlertTriangle className="w-3.5 h-3.5 text-amber-500" />
                  <span className="text-amber-700">Tool Fallback Mode</span>
                </>
              )}
              {healthStatus === 'DOWN' && (
                <>
                  <span className="w-2 h-2 rounded-full bg-rose-500 animate-pulse"></span>
                  <span className="text-rose-700">Service Offline</span>
                </>
              )}
              {healthStatus === 'CHECKING' && (
                <span className="text-slate-500">Checking...</span>
              )}
            </div>

            {/* Citizen Identity */}
            <div className="flex items-center space-x-2 border-l border-slate-200 pl-4">
              <div className="w-8 h-8 rounded-full bg-slate-100 border border-slate-200 flex items-center justify-center text-slate-600">
                <User className="w-4 h-4" />
              </div>
              <div className="text-left hidden sm:block">
                <div className="text-sm font-semibold text-slate-800 leading-none">{name || username}</div>
                <div className="text-xs font-mono text-slate-500 mt-1">ID: {citizen_id}</div>
              </div>
              <button
                onClick={logout}
                title="Sign Out"
                className="ml-2 p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-md transition-colors"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};
