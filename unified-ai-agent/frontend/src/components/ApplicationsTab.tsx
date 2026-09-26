import React, { useState, useEffect } from 'react';
import { api } from '../api/client';
import { ApplicationItem } from '../types';
import { ClipboardList, PlusCircle, Clock, CheckCircle2, ChevronRight, Loader2, RefreshCw, X } from 'lucide-react';

export const ApplicationsTab: React.FC = () => {
  const [applications, setApplications] = useState<ApplicationItem[]>([]);
  const [selectedApp, setSelectedApp] = useState<ApplicationItem | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // New application form state
  const [schemeName, setSchemeName] = useState('Startup India Seed Fund Scheme');
  const [incubatorPreference, setIncubatorPreference] = useState('IIT Madras Incubation Cell');
  const [milestoneStage, setMilestoneStage] = useState('Prototype Development');
  const [submitError, setSubmitError] = useState<string | null>(null);

  const fetchApplications = async () => {
    setIsLoading(true);
    try {
      const data = await api.getApplications();
      setApplications(data);
      if (data.length > 0 && !selectedApp) {
        loadDetail(data[0].application_id);
      }
    } catch (err: any) {
      console.error("Failed to load applications", err);
    } finally {
      setIsLoading(false);
    }
  };

  const loadDetail = async (id: string) => {
    try {
      const app = await api.getApplication(id);
      setSelectedApp(app);
    } catch (err: any) {
      console.error("Failed to load application detail", err);
    }
  };

  useEffect(() => {
    fetchApplications();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setSubmitError(null);
    try {
      const newApp = await api.createApplication({
        scheme_name: schemeName,
        incubator_preference: incubatorPreference,
        milestone_stage: milestoneStage,
        details: { source: "web_portal" }
      });
      setIsModalOpen(false);
      await fetchApplications();
      setSelectedApp(newApp);
    } catch (err: any) {
      setSubmitError(err.message || 'Application submission failed');
    } finally {
      setIsSubmitting(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status.toUpperCase()) {
      case 'APPROVED':
      case 'SELECTED':
        return 'bg-emerald-100 text-emerald-800 border-emerald-200';
      case 'REJECTED':
        return 'bg-rose-100 text-rose-800 border-rose-200';
      case 'SUBMITTED':
      case 'UNDER_REVIEW':
      case 'IN_PROGRESS':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      default:
        return 'bg-slate-100 text-slate-800 border-slate-200';
    }
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Header Bar */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 flex flex-col sm:flex-row justify-between sm:items-center gap-4">
        <div>
          <h2 className="text-lg font-semibold text-slate-900">Application Tracking & Submissions</h2>
          <p className="text-sm text-slate-500">
            Track statutory application progress, status updates, and milestone disbursements.
          </p>
        </div>

        <button
          onClick={() => setIsModalOpen(true)}
          className="px-4 py-2.5 bg-govblue-600 hover:bg-govblue-700 text-white rounded-lg text-sm font-semibold flex items-center justify-center transition-colors shadow-sm shrink-0"
        >
          <PlusCircle className="w-4 h-4 mr-2" />
          Submit Application
        </button>
      </div>

      {/* Main Content Area */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Applications List */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-4">
          <div className="flex justify-between items-center mb-3">
            <h3 className="font-semibold text-slate-900 text-sm">Submitted Applications</h3>
            <button
              onClick={fetchApplications}
              className="p-1 text-slate-400 hover:text-slate-600 rounded-md transition-colors"
              title="Refresh"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>

          {isLoading ? (
            <div className="py-8 text-center text-sm text-slate-500 flex items-center justify-center">
              <Loader2 className="w-4 h-4 animate-spin mr-2" /> Loading applications...
            </div>
          ) : applications.length === 0 ? (
            <div className="py-8 text-center text-sm text-slate-400">
              No applications submitted yet.
            </div>
          ) : (
            <div className="space-y-2 max-h-[460px] overflow-y-auto">
              {applications.map((app) => (
                <div
                  key={app.application_id}
                  onClick={() => loadDetail(app.application_id)}
                  className={`p-3.5 rounded-lg border cursor-pointer transition-all ${
                    selectedApp?.application_id === app.application_id
                      ? 'border-govblue-500 bg-govblue-50 shadow-2xs'
                      : 'border-slate-200 hover:bg-slate-50'
                  }`}
                >
                  <div className="flex justify-between items-start gap-2">
                    <span className="text-xs font-bold text-slate-900 line-clamp-1">
                      {app.scheme_name}
                    </span>
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${getStatusColor(app.status)}`}>
                      {app.status}
                    </span>
                  </div>
                  <div className="mt-2 flex items-center justify-between text-[11px] text-slate-500 font-mono">
                    <span>{app.application_id}</span>
                    <span>{app.submitted_date || 'Recent'}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Selected Application Timeline & Detail */}
        <div className="lg:col-span-2 bg-white rounded-xl shadow-sm border border-slate-200 p-6">
          {selectedApp ? (
            <div className="space-y-6">
              <div className="flex justify-between items-start border-b border-slate-200 pb-4">
                <div>
                  <div className="flex items-center space-x-2">
                    <span className="font-mono text-xs text-govblue-700 bg-govblue-50 px-2.5 py-0.5 rounded font-bold border border-govblue-200">
                      {selectedApp.application_id}
                    </span>
                    <span className={`text-xs font-bold px-2.5 py-0.5 rounded-full border ${getStatusColor(selectedApp.status)}`}>
                      {selectedApp.status}
                    </span>
                  </div>
                  <h3 className="text-base font-bold text-slate-900 mt-2">{selectedApp.scheme_name}</h3>
                </div>
                <div className="text-xs text-slate-500">
                  Last Updated: {new Date(selectedApp.last_updated).toLocaleDateString()}
                </div>
              </div>

              {/* Application Details Summary */}
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 bg-slate-50 p-4 rounded-lg border border-slate-200 text-xs">
                {selectedApp.incubator_preference && (
                  <div>
                    <span className="text-slate-400 block">Incubator Preference:</span>
                    <span className="font-semibold text-slate-800">{selectedApp.incubator_preference}</span>
                  </div>
                )}
                {selectedApp.milestone_stage && (
                  <div>
                    <span className="text-slate-400 block">Milestone Stage:</span>
                    <span className="font-semibold text-slate-800">{selectedApp.milestone_stage}</span>
                  </div>
                )}
                {selectedApp.pran_status && (
                  <div>
                    <span className="text-slate-400 block">PRAN / Identity Status:</span>
                    <span className="font-semibold text-slate-800">{selectedApp.pran_status}</span>
                  </div>
                )}
              </div>

              {selectedApp.next_step && (
                <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg text-xs text-blue-900">
                  <strong>Next Official Step:</strong> {selectedApp.next_step}
                </div>
              )}

              {/* Status Audit Timeline */}
              <div>
                <h4 className="text-sm font-bold text-slate-900 mb-4 flex items-center">
                  <Clock className="w-4 h-4 mr-1.5 text-govblue-600" />
                  Status Update Timeline
                </h4>

                {selectedApp.status_history && selectedApp.status_history.length > 0 ? (
                  <div className="relative border-l-2 border-slate-200 ml-3 space-y-6 pl-4">
                    {selectedApp.status_history.map((h, idx) => (
                      <div key={idx} className="relative">
                        <div className="absolute -left-[23px] top-0.5 w-3.5 h-3.5 bg-govblue-600 rounded-full border-2 border-white ring-2 ring-govblue-100"></div>
                        <div className="flex items-center space-x-2">
                          <span className={`text-xs font-bold px-2 py-0.5 rounded-full border ${getStatusColor(h.status)}`}>
                            {h.status}
                          </span>
                          <span className="text-[11px] text-slate-400">
                            {new Date(h.created_at).toLocaleString()}
                          </span>
                          <span className="text-[11px] text-slate-500 italic">
                            by {h.changed_by}
                          </span>
                        </div>
                        {h.comment && (
                          <div className="text-xs text-slate-700 mt-1 bg-slate-50 p-2.5 rounded border border-slate-200">
                            {h.comment}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-xs text-slate-400 py-4 text-center">
                    No status history recorded yet.
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="h-64 flex flex-col items-center justify-center text-slate-400 text-sm">
              <ClipboardList className="w-12 h-12 text-slate-300 mb-2" />
              <span>Select an application to view status timeline.</span>
            </div>
          )}
        </div>
      </div>

      {/* Submit New Application Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-xl border border-slate-200 max-w-md w-full p-6 relative">
            <button
              onClick={() => setIsModalOpen(false)}
              className="absolute top-4 right-4 text-slate-400 hover:text-slate-600 p-1"
            >
              <X className="w-5 h-5" />
            </button>

            <h3 className="text-base font-bold text-slate-900 mb-1">Submit Scheme Application</h3>
            <p className="text-xs text-slate-500 mb-4">
              Submit your formal application to the scheme administration.
            </p>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Scheme Name
                </label>
                <select
                  value={schemeName}
                  onChange={(e) => setSchemeName(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-govblue-500"
                >
                  <option value="Startup India Seed Fund Scheme">Startup India Seed Fund Scheme</option>
                  <option value="PM Kisan Samman Nidhi">PM Kisan Samman Nidhi</option>
                  <option value="Atal Pension Yojana">Atal Pension Yojana</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Incubator / Implementing Agency
                </label>
                <input
                  type="text"
                  value={incubatorPreference}
                  onChange={(e) => setIncubatorPreference(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-govblue-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Milestone Stage
                </label>
                <select
                  value={milestoneStage}
                  onChange={(e) => setMilestoneStage(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-govblue-500"
                >
                  <option value="Prototype Development">Prototype Development</option>
                  <option value="Proof of Concept">Proof of Concept</option>
                  <option value="Product Trials & Commercialization">Product Trials & Commercialization</option>
                </select>
              </div>

              {submitError && (
                <div className="p-2.5 bg-rose-50 border border-rose-200 rounded text-xs text-rose-700">
                  {submitError}
                </div>
              )}

              <div className="flex justify-end space-x-2 pt-2">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2 border border-slate-300 rounded-lg text-sm text-slate-700 hover:bg-slate-50 font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-4 py-2 bg-govblue-600 hover:bg-govblue-700 text-white rounded-lg text-sm font-semibold flex items-center disabled:opacity-50"
                >
                  {isSubmitting ? <Loader2 className="w-4 h-4 animate-spin mr-1.5" /> : null}
                  Submit Application
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
