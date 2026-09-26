import React, { useState } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { Header } from './components/Header';
import { AuthModal } from './components/AuthModal';
import { ChatTab } from './components/ChatTab';
import { DocumentsTab } from './components/DocumentsTab';
import { SchemesTab } from './components/SchemesTab';
import { EligibilityTab } from './components/EligibilityTab';
import { ApplicationsTab } from './components/ApplicationsTab';
import { MessageSquare, FileText, Search, ShieldCheck, ClipboardList, Loader2 } from 'lucide-react';

const MainPortal: React.FC = () => {
  const { isAuthenticated, isLoading } = useAuth();
  const [activeTab, setActiveTab] = useState<'chat' | 'docs' | 'schemes' | 'eligibility' | 'applications'>('chat');

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="text-center">
          <Loader2 className="w-10 h-10 animate-spin text-govblue-600 mx-auto mb-3" />
          <p className="text-sm font-semibold text-slate-600">Initializing Citizen Portal...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <AuthModal />;
  }

  const tabs = [
    { id: 'chat', label: 'AI Advisor', icon: MessageSquare },
    { id: 'docs', label: 'Document Locker', icon: FileText },
    { id: 'schemes', label: 'Scheme Discovery', icon: Search },
    { id: 'eligibility', label: 'Statutory Eligibility', icon: ShieldCheck },
    { id: 'applications', label: 'My Applications', icon: ClipboardList },
  ] as const;

  return (
    <div className="min-h-screen bg-slate-100 flex flex-col">
      <Header />

      {/* Main Tab Navigation Bar */}
      <div className="bg-white border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <nav className="flex space-x-1 sm:space-x-4 overflow-x-auto py-2">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center space-x-2 px-3 sm:px-4 py-2 text-xs sm:text-sm font-semibold rounded-lg transition-colors whitespace-nowrap ${
                    isActive
                      ? 'bg-govblue-50 text-govblue-700 shadow-2xs'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
                  }`}
                >
                  <Icon className={`w-4 h-4 ${isActive ? 'text-govblue-600' : 'text-slate-400'}`} />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </nav>
        </div>
      </div>

      {/* Main Tab View Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {activeTab === 'chat' && <ChatTab />}
        {activeTab === 'docs' && <DocumentsTab />}
        {activeTab === 'schemes' && <SchemesTab />}
        {activeTab === 'eligibility' && <EligibilityTab />}
        {activeTab === 'applications' && <ApplicationsTab />}
      </main>

      {/* Government Footer */}
      <footer className="bg-white border-t border-slate-200 py-4 text-center text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4">
          JanSeva AI Citizen Support Portal • Unified Government Financial & Social Assistance Platform • Built with Java 25 & Python AI Engine
        </div>
      </footer>
    </div>
  );
};

export const App: React.FC = () => {
  return (
    <AuthProvider>
      <MainPortal />
    </AuthProvider>
  );
};

export default App;
