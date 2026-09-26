import React, { useState, useEffect } from 'react';
import { api } from '../api/client';
import { DocumentItem } from '../types';
import { Upload, FileText, CheckCircle, AlertTriangle, ShieldAlert, Loader2, RefreshCw } from 'lucide-react';

export const DocumentsTab: React.FC = () => {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [selectedDoc, setSelectedDoc] = useState<DocumentItem | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isLoadingDocs, setIsLoadingDocs] = useState(true);
  const [uploadError, setUploadError] = useState<string | null>(null);

  const fetchDocuments = async () => {
    setIsLoadingDocs(true);
    try {
      const docs = await api.getDocuments();
      setDocuments(docs);
      if (docs.length > 0 && !selectedDoc) {
        loadDocumentDetail(docs[0].document_id);
      }
    } catch (err: any) {
      console.error("Failed to load documents", err);
    } finally {
      setIsLoadingDocs(false);
    }
  };

  const loadDocumentDetail = async (id: number) => {
    try {
      const detail = await api.getDocumentDetail(id);
      setSelectedDoc(detail);
    } catch (err: any) {
      console.error("Failed to load document detail", err);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, []);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploadError(null);
    setIsUploading(true);

    try {
      const uploaded = await api.uploadDocument(file);
      await fetchDocuments();
      setSelectedDoc(uploaded);
    } catch (err: any) {
      setUploadError(err.message || 'Upload failed');
    } finally {
      setIsUploading(false);
      e.target.value = '';
    }
  };

  const getConfidenceBadge = (confidence: number) => {
    if (confidence >= 0.85) {
      return (
        <span className="text-[11px] bg-emerald-100 text-emerald-800 font-semibold px-2 py-0.5 rounded-full border border-emerald-200">
          HIGH ({Math.round(confidence * 100)}%)
        </span>
      );
    } else if (confidence >= 0.60) {
      return (
        <span className="text-[11px] bg-amber-100 text-amber-800 font-semibold px-2 py-0.5 rounded-full border border-amber-200">
          MED ({Math.round(confidence * 100)}%)
        </span>
      );
    } else {
      return (
        <span className="text-[11px] bg-rose-100 text-rose-800 font-semibold px-2 py-0.5 rounded-full border border-rose-200">
          LOW ({Math.round(confidence * 100)}%)
        </span>
      );
    }
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Upload Zone */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
        <h2 className="text-lg font-semibold text-slate-900 mb-1">Citizen Document Locker</h2>
        <p className="text-sm text-slate-500 mb-4">
          Upload certificates (Income, Caste, Startup DPIIT Recognition) to extract verified facts for automated statutory eligibility evaluation.
        </p>

        <div className="border-2 border-dashed border-slate-300 hover:border-govblue-500 rounded-xl p-6 text-center transition-colors bg-slate-50">
          <input
            type="file"
            id="doc-upload"
            onChange={handleFileUpload}
            disabled={isUploading}
            accept=".pdf,.png,.jpg,.jpeg"
            className="hidden"
          />
          <label htmlFor="doc-upload" className="cursor-pointer flex flex-col items-center">
            {isUploading ? (
              <Loader2 className="w-10 h-10 text-govblue-600 animate-spin mb-2" />
            ) : (
              <Upload className="w-10 h-10 text-govblue-600 mb-2" />
            )}
            <span className="text-sm font-semibold text-slate-800">
              {isUploading ? "Uploading & Analyzing Document with Document AI..." : "Click to select or drag & drop document"}
            </span>
            <span className="text-xs text-slate-500 mt-1">
              Supported: PDF, JPEG, PNG (Max 10MB)
            </span>
          </label>
        </div>

        {uploadError && (
          <div className="mt-3 p-3 bg-rose-50 border border-rose-200 rounded-lg flex items-center text-sm text-rose-700">
            <AlertTriangle className="w-4 h-4 mr-2 shrink-0" />
            <span>{uploadError}</span>
          </div>
        )}
      </div>

      {/* Documents Grid / Details */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Document List */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-4">
          <div className="flex justify-between items-center mb-3">
            <h3 className="font-semibold text-slate-900 text-sm">Uploaded Documents</h3>
            <button
              onClick={fetchDocuments}
              className="p-1 text-slate-400 hover:text-slate-600 rounded-md transition-colors"
              title="Refresh"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>

          {isLoadingDocs ? (
            <div className="py-8 text-center text-sm text-slate-500 flex items-center justify-center">
              <Loader2 className="w-4 h-4 animate-spin mr-2" /> Loading documents...
            </div>
          ) : documents.length === 0 ? (
            <div className="py-8 text-center text-sm text-slate-400">
              No documents uploaded yet.
            </div>
          ) : (
            <div className="space-y-2 max-h-[460px] overflow-y-auto">
              {documents.map((doc) => (
                <div
                  key={doc.document_id}
                  onClick={() => loadDocumentDetail(doc.document_id)}
                  className={`p-3 rounded-lg border cursor-pointer transition-all ${
                    selectedDoc?.document_id === doc.document_id
                      ? 'border-govblue-500 bg-govblue-50 shadow-2xs'
                      : 'border-slate-200 hover:bg-slate-50'
                  }`}
                >
                  <div className="flex items-center space-x-2">
                    <FileText className="w-4 h-4 text-govblue-600 shrink-0" />
                    <span className="text-xs font-semibold text-slate-800 truncate">
                      {doc.filename}
                    </span>
                  </div>
                  <div className="mt-1 flex items-center justify-between text-[11px] text-slate-500">
                    <span className="capitalize">{doc.apparent_type || 'Unclassified'}</span>
                    <span>{new Date(doc.uploaded_at).toLocaleDateString()}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Selected Document Details & Facts */}
        <div className="lg:col-span-2 bg-white rounded-xl shadow-sm border border-slate-200 p-6">
          {selectedDoc ? (
            <div className="space-y-4">
              <div className="flex justify-between items-start border-b border-slate-200 pb-4">
                <div>
                  <h3 className="text-base font-bold text-slate-900">{selectedDoc.filename}</h3>
                  <div className="flex items-center space-x-3 mt-1 text-xs text-slate-500">
                    <span>Type: <strong className="text-slate-700 capitalize">{selectedDoc.apparent_type || 'Unknown'}</strong></span>
                    <span>SHA-256: <code className="text-slate-600">{selectedDoc.sha256_hash.substring(0, 12)}...</code></span>
                  </div>
                </div>
                <div className="text-xs text-slate-400">
                  {new Date(selectedDoc.uploaded_at).toLocaleString()}
                </div>
              </div>

              {/* Extracted Structured Facts Table */}
              <div>
                <h4 className="text-sm font-semibold text-slate-800 mb-2">Structured Facts Extracted by Document AI</h4>
                {selectedDoc.extracted_fields && selectedDoc.extracted_fields.length > 0 ? (
                  <div className="border border-slate-200 rounded-lg overflow-hidden">
                    <table className="min-w-full divide-y divide-slate-200 text-xs">
                      <thead className="bg-slate-50">
                        <tr>
                          <th className="px-3 py-2 text-left font-semibold text-slate-700">Attribute</th>
                          <th className="px-3 py-2 text-left font-semibold text-slate-700">Extracted Value</th>
                          <th className="px-3 py-2 text-left font-semibold text-slate-700">Confidence</th>
                          <th className="px-3 py-2 text-left font-semibold text-slate-700">Provenance</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100 bg-white">
                        {selectedDoc.extracted_fields.map((field, idx) => (
                          <tr key={idx} className="hover:bg-slate-50">
                            <td className="px-3 py-2.5 font-medium text-slate-800 capitalize">
                              {field.field_name.replace(/_/g, ' ')}
                            </td>
                            <td className="px-3 py-2.5 text-slate-900 font-mono">
                              {field.field_value}
                            </td>
                            <td className="px-3 py-2.5">
                              {getConfidenceBadge(field.confidence)}
                            </td>
                            <td className="px-3 py-2.5 text-slate-500">
                              {field.provenance_method || 'rule_match'}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <div className="p-4 bg-slate-50 rounded-lg text-xs text-slate-500 text-center">
                    No structured facts extracted for this document.
                  </div>
                )}
              </div>

              {/* Statutory Disclaimer Badge */}
              <div className="p-3.5 bg-amber-50 border border-amber-200 rounded-lg flex items-start space-x-2 text-xs text-amber-900">
                <ShieldAlert className="w-4 h-4 text-amber-600 mt-0.5 shrink-0" />
                <div>
                  <strong>Mandatory Statutory Notice:</strong> Structured facts extracted by Document AI.
                  Does not constitute official government authentication or statutory endorsement.
                </div>
              </div>
            </div>
          ) : (
            <div className="h-64 flex flex-col items-center justify-center text-slate-400 text-sm">
              <FileText className="w-12 h-12 text-slate-300 mb-2" />
              <span>Select a document from the list to view extracted attributes.</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
