import React, { useState } from 'react';
import { api } from '../api/client';
import { SchemeResult } from '../types';
import { Search, BookOpen, Filter, Loader2, Award } from 'lucide-react';

export const SchemesTab: React.FC = () => {
  const [query, setQuery] = useState('seed fund financial assistance for startup');
  const [category, setCategory] = useState<string>('');
  const [results, setResults] = useState<SchemeResult[]>([]);
  const [totalMatches, setTotalMatches] = useState<number | null>(null);
  const [isSearching, setIsSearching] = useState(false);

  const handleSearch = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!query.trim()) return;

    setIsSearching(true);
    try {
      const data = await api.searchSchemes(query, category || undefined, 10);
      setResults(data.results || []);
      setTotalMatches(data.total_matches);
    } catch (err: any) {
      console.error("Scheme search failed", err);
    } finally {
      setIsSearching(false);
    }
  };

  const categories = [
    { label: 'All Categories', value: '' },
    { label: 'Startup & Innovation', value: 'startup' },
    { label: 'Agriculture & Farming', value: 'agriculture' },
    { label: 'Social Welfare & Pension', value: 'welfare' },
    { label: 'Employment & Skilling', value: 'employment' },
  ];

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Search Header */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
        <h2 className="text-lg font-semibold text-slate-900 mb-1">Government Scheme Clause Discovery</h2>
        <p className="text-sm text-slate-500 mb-4">
          Perform semantic vector search backed by verified official guidelines and gazette notifications.
        </p>

        <form onSubmit={handleSearch} className="flex gap-2 mb-4">
          <div className="relative flex-1">
            <Search className="w-5 h-5 absolute left-3 top-3 text-slate-400" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search scheme clauses, benefits, eligibility criteria..."
              className="w-full pl-10 pr-4 py-2.5 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-govblue-500"
            />
          </div>
          <button
            type="submit"
            disabled={isSearching || !query.trim()}
            className="px-5 py-2.5 bg-govblue-600 text-white rounded-lg hover:bg-govblue-700 font-medium text-sm disabled:opacity-50 flex items-center transition-colors shadow-sm"
          >
            {isSearching ? <Loader2 className="w-4 h-4 animate-spin mr-1" /> : <Search className="w-4 h-4 mr-1" />}
            Search
          </button>
        </form>

        {/* Filter Chips */}
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-xs text-slate-500 font-medium flex items-center mr-1">
            <Filter className="w-3.5 h-3.5 mr-1" /> Domain:
          </span>
          {categories.map((cat) => (
            <button
              key={cat.value}
              type="button"
              onClick={() => {
                setCategory(cat.value);
              }}
              className={`text-xs px-3 py-1 rounded-full font-medium transition-colors ${
                category === cat.value
                  ? 'bg-govblue-600 text-white'
                  : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
              }`}
            >
              {cat.label}
            </button>
          ))}
        </div>
      </div>

      {/* Results List */}
      <div className="space-y-4">
        {totalMatches !== null && (
          <div className="text-xs text-slate-500 font-medium px-1">
            Showing {results.length} matches (Vector Similarity Ranked)
          </div>
        )}

        {results.length > 0 ? (
          results.map((res, idx) => (
            <div
              key={idx}
              className="bg-white rounded-xl shadow-sm border border-slate-200 p-5 hover:border-govblue-300 transition-all"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex items-center space-x-2">
                  <div className="w-8 h-8 rounded-lg bg-govblue-50 border border-govblue-100 flex items-center justify-center text-govblue-600">
                    <BookOpen className="w-4 h-4" />
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-slate-900">{res.scheme_name}</h3>
                    <div className="text-xs text-slate-500 mt-0.5">
                      Section: <span className="font-semibold text-slate-700">{res.section}</span> | Page {res.page_number}
                    </div>
                  </div>
                </div>

                <div className="text-right shrink-0">
                  <div className="text-xs font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
                    {Math.round(res.score * 100)}% Match
                  </div>
                </div>
              </div>

              <div className="mt-3 text-xs text-slate-700 leading-relaxed bg-slate-50 p-3.5 rounded-lg border border-slate-200">
                "{res.content}"
              </div>
            </div>
          ))
        ) : isSearching ? (
          <div className="bg-white rounded-xl border border-slate-200 p-12 text-center text-slate-500 flex flex-col items-center justify-center">
            <Loader2 className="w-8 h-8 animate-spin text-govblue-600 mb-2" />
            <span className="text-sm">Querying Qdrant statutory vector collection...</span>
          </div>
        ) : totalMatches === 0 ? (
          <div className="bg-white rounded-xl border border-slate-200 p-12 text-center text-slate-400 text-sm">
            No matching statutory clauses found for this query.
          </div>
        ) : (
          <div className="bg-white rounded-xl border border-slate-200 p-12 text-center text-slate-400 text-sm">
            Enter a search term above to explore official government guidelines.
          </div>
        )}
      </div>
    </div>
  );
};
