import React, { useState, useEffect } from 'react';
import { api } from '../api/client';
import { EligibilityResult, UserProfile } from '../types';
import { CheckCircle2, XCircle, HelpCircle, Loader2, ArrowRight, ShieldCheck, UserCheck } from 'lucide-react';

export const EligibilityTab: React.FC = () => {
  const [selectedScheme, setSelectedScheme] = useState('Startup India Seed Fund Scheme');
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [isEvaluating, setIsEvaluating] = useState(false);
  const [assessment, setAssessment] = useState<EligibilityResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadProfile() {
      try {
        const p = await api.getProfile();
        setProfile(p);
      } catch (err: any) {
        console.error("Could not load profile", err);
      }
    }
    loadProfile();
  }, []);

  const handleEvaluate = async () => {
    setIsEvaluating(true);
    setError(null);
    try {
      const result = await api.checkEligibility(selectedScheme);
      setAssessment(result);
    } catch (err: any) {
      setError(err.message || 'Evaluation failed');
    } finally {
      setIsEvaluating(false);
    }
  };

  const schemes = [
    'Startup India Seed Fund Scheme',
    'PM Kisan Samman Nidhi',
    'Atal Pension Yojana',
  ];

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Assessment Selector Card */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
        <div className="flex items-center space-x-2 text-govblue-600 mb-1">
          <ShieldCheck className="w-5 h-5" />
          <h2 className="text-lg font-semibold text-slate-900">Deterministic Statutory Eligibility Engine</h2>
        </div>
        <p className="text-sm text-slate-500 mb-5">
          Zero-hallucination statutory verification. Evaluates non-negotiable legal criteria using your verified MySQL profile and document evidence.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          <div className="md:col-span-2">
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
              Select Statutory Scheme
            </label>
            <select
              value={selectedScheme}
              onChange={(e) => {
                setSelectedScheme(e.target.value);
                setAssessment(null);
              }}
              className="w-full px-3.5 py-2.5 bg-white border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-govblue-500 font-medium"
            >
              {schemes.map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          </div>

          <div className="flex items-end">
            <button
              onClick={handleEvaluate}
              disabled={isEvaluating}
              className="w-full py-2.5 px-4 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold rounded-lg text-sm flex items-center justify-center transition-colors shadow-sm disabled:opacity-50"
            >
              {isEvaluating ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin mr-2" />
                  Evaluating Rules...
                </>
              ) : (
                <>
                  <UserCheck className="w-4 h-4 mr-2" />
                  Assess Statutory Eligibility
                </>
              )}
            </button>
          </div>
        </div>

        {/* Current Citizen Profile Summary */}
        {profile && (
          <div className="mt-4 pt-4 border-t border-slate-200 grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs bg-slate-50 p-3.5 rounded-lg border border-slate-200">
            <div>
              <span className="text-slate-400 block">Citizen ID:</span>
              <span className="font-semibold text-slate-800">{profile.citizen_id}</span>
            </div>
            <div>
              <span className="text-slate-400 block">DPIIT Recognized:</span>
              <span className="font-semibold text-slate-800">{profile.has_dpiit_recognition ? 'Yes' : 'No'}</span>
            </div>
            <div>
              <span className="text-slate-400 block">Incorporated:</span>
              <span className="font-semibold text-slate-800">{profile.business_incorporated_years ?? 'N/A'} yrs</span>
            </div>
            <div>
              <span className="text-slate-400 block">Annual Income:</span>
              <span className="font-semibold text-slate-800">
                {profile.annual_income != null ? `₹${profile.annual_income.toLocaleString()}` : 'N/A'}
              </span>
            </div>
          </div>
        )}

        {error && (
          <div className="mt-3 p-3 bg-rose-50 border border-rose-200 rounded-lg text-xs text-rose-700">
            {error}
          </div>
        )}
      </div>

      {/* Evaluation Results Card */}
      {assessment && (
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
          {/* Decision Banner */}
          <div
            className={`p-6 border-b flex items-start justify-between ${
              assessment.decision === 'ELIGIBLE'
                ? 'bg-emerald-50 border-emerald-200'
                : assessment.decision === 'INELIGIBLE'
                ? 'bg-rose-50 border-rose-200'
                : 'bg-amber-50 border-amber-200'
            }`}
          >
            <div className="flex items-start space-x-3">
              {assessment.decision === 'ELIGIBLE' && (
                <CheckCircle2 className="w-8 h-8 text-emerald-600 shrink-0 mt-0.5" />
              )}
              {assessment.decision === 'INELIGIBLE' && (
                <XCircle className="w-8 h-8 text-rose-600 shrink-0 mt-0.5" />
              )}
              {assessment.decision === 'INCONCLUSIVE' && (
                <HelpCircle className="w-8 h-8 text-amber-600 shrink-0 mt-0.5" />
              )}

              <div>
                <div className="flex items-center space-x-2">
                  <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
                    Statutory Decision:
                  </span>
                  <span
                    className={`text-sm font-bold px-2.5 py-0.5 rounded-full ${
                      assessment.decision === 'ELIGIBLE'
                        ? 'bg-emerald-600 text-white'
                        : assessment.decision === 'INELIGIBLE'
                        ? 'bg-rose-600 text-white'
                        : 'bg-amber-500 text-white'
                    }`}
                  >
                    {assessment.decision}
                  </span>
                </div>
                <h3 className="text-base font-bold text-slate-900 mt-1">{assessment.scheme_name}</h3>
                <p className="text-xs text-slate-700 mt-1 leading-relaxed">{assessment.explanation}</p>
              </div>
            </div>

            <div className="text-right shrink-0">
              <span className="text-xs text-slate-500 block">Statutory Confidence</span>
              <span className="text-lg font-bold text-slate-900">
                {Math.round(assessment.confidence_score * 100)}%
              </span>
            </div>
          </div>

          {/* Rule Breakdown Checklist */}
          <div className="p-6 space-y-6">
            <div>
              <h4 className="text-sm font-bold text-slate-900 mb-3">Statutory Rule Checklist Breakdown</h4>
              <div className="border border-slate-200 rounded-lg overflow-hidden">
                <table className="min-w-full divide-y divide-slate-200 text-xs">
                  <thead className="bg-slate-50">
                    <tr>
                      <th className="px-3.5 py-2.5 text-left font-semibold text-slate-700">Status</th>
                      <th className="px-3.5 py-2.5 text-left font-semibold text-slate-700">Statutory Rule</th>
                      <th className="px-3.5 py-2.5 text-left font-semibold text-slate-700">Verification Evidence</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 bg-white">
                    {assessment.rule_breakdown.map((rule, idx) => (
                      <tr key={idx} className="hover:bg-slate-50">
                        <td className="px-3.5 py-3 whitespace-nowrap">
                          {rule.status === 'PASSED' && (
                            <span className="inline-flex items-center text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded font-semibold text-[11px] border border-emerald-200">
                              <CheckCircle2 className="w-3 h-3 mr-1 text-emerald-500" /> PASSED
                            </span>
                          )}
                          {rule.status === 'FAILED' && (
                            <span className="inline-flex items-center text-rose-700 bg-rose-50 px-2 py-0.5 rounded font-semibold text-[11px] border border-rose-200">
                              <XCircle className="w-3 h-3 mr-1 text-rose-500" /> FAILED
                            </span>
                          )}
                          {rule.status === 'UNKNOWN' && (
                            <span className="inline-flex items-center text-amber-700 bg-amber-50 px-2 py-0.5 rounded font-semibold text-[11px] border border-amber-200">
                              <HelpCircle className="w-3 h-3 mr-1 text-amber-500" /> UNKNOWN
                            </span>
                          )}
                        </td>
                        <td className="px-3.5 py-3 font-medium text-slate-800">
                          <div>{rule.description}</div>
                          <div className="text-[10px] font-mono text-slate-400 mt-0.5">{rule.rule_id}</div>
                        </td>
                        <td className="px-3.5 py-3 text-slate-600 font-mono text-[11px]">
                          {rule.evidence || 'No evidence supplied'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Next Steps Guidance */}
            {assessment.next_steps && assessment.next_steps.length > 0 && (
              <div>
                <h4 className="text-sm font-bold text-slate-900 mb-2">Statutory Next Steps</h4>
                <div className="space-y-1.5">
                  {assessment.next_steps.map((step, idx) => (
                    <div key={idx} className="flex items-start text-xs text-slate-700 bg-slate-50 p-2.5 rounded-lg border border-slate-200">
                      <ArrowRight className="w-4 h-4 text-govblue-600 mr-2 shrink-0 mt-0.5" />
                      <span>{step}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
