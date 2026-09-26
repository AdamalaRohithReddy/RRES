export interface Citation {
  scheme_name: string;
  section: string;
  page_number: number;
  relevance_score: number;
  clause_text: string;
}

export interface DetectedNeed {
  category: string;
  urgency: string;
  need_type: string;
  statement: string;
}

export interface ToolCall {
  tool: string;
  input: any;
  result_snippet: string;
}

export interface ChatMessage {
  id: string;
  sender: 'citizen' | 'agent';
  text: string;
  thought_trace_summary?: string;
  citations?: Citation[];
  detected_needs?: DetectedNeed[];
  tool_calls?: ToolCall[];
  timestamp: string;
}

export interface ExtractedField {
  field_id?: number;
  field_name: string;
  field_value: string;
  confidence: number;
  provenance_method?: string;
}

export interface DocumentItem {
  document_id: number;
  citizen_id: string;
  filename: string;
  apparent_type?: string;
  sha256_hash: string;
  uploaded_at: string;
  extracted_text?: string;
  extracted_fields?: ExtractedField[];
}

export interface SchemeResult {
  scheme_name: string;
  section: string;
  page_number: number;
  score: number;
  content: string;
}

export interface RuleEvaluation {
  rule_id: string;
  description: string;
  status: string; // PASSED, FAILED, UNKNOWN
  evidence: string;
}

export interface EligibilityResult {
  scheme_name: string;
  decision: 'ELIGIBLE' | 'INELIGIBLE' | 'INCONCLUSIVE';
  explanation: string;
  confidence_score: number;
  rule_breakdown: RuleEvaluation[];
  missing_evidence: string[];
  next_steps: string[];
}

export interface ApplicationHistory {
  history_id: number;
  status: string;
  comment: string;
  changed_by: string;
  created_at: string;
}

export interface ApplicationItem {
  application_id: string;
  citizen_id: string;
  scheme_name: string;
  status: string;
  submitted_date?: string;
  last_updated: string;
  incubator_preference?: string;
  milestone_stage?: string;
  pran_status?: string;
  next_step?: string;
  status_history?: ApplicationHistory[];
}

export interface UserProfile {
  citizen_id: string;
  name: string;
  date_of_birth?: string;
  age?: number;
  gender?: string;
  phone?: string;
  state?: string;
  district?: string;
  annual_income?: number;
  occupation?: string;
  category?: string;
  is_taxpayer?: boolean;
  has_dpiit_recognition?: boolean;
  business_incorporated_years?: number;
  landholding_acres?: number;
  is_differently_abled?: boolean;
  disability_percentage?: number;
}

export interface AuthState {
  token: string | null;
  citizen_id: string | null;
  username: string | null;
  name: string | null;
  role: string | null;
  isAuthenticated: boolean;
}

export interface AuthResponse {
  token: string;
  citizen_id: string;
  username: string;
  name: string;
  role: string;
}

