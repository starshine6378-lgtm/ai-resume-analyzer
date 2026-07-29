export interface Education {
  school: string | null;
  degree: string | null;
  major: string | null;
  start_date: string | null;
  end_date: string | null;
}

export interface Project {
  name: string | null;
  description: string | null;
  technologies: string[];
}

export interface CandidateProfile {
  name: string | null;
  phone: string | null;
  email: string | null;
  address: string | null;
  job_intention: string | null;
  expected_salary: string | null;
  years_of_experience: number | null;
  education: Education[];
  skills: string[];
  projects: Project[];
  work_experience: string[];
}

export interface ResumeAnalysis {
  resume_id: string;
  cached: boolean;
  filename: string;
  page_count: number;
  raw_text_length: number;
  extraction_mode: "ai" | "rules" | "hybrid";
  candidate: CandidateProfile;
  text_preview: string;
  warnings: string[];
}

export interface JobRequirements {
  title: string | null;
  required_skills: string[];
  preferred_skills: string[];
  minimum_years: number | null;
  minimum_degree: string | null;
  responsibilities: string[];
}

export interface MatchResult {
  resume_id: string;
  cached: boolean;
  score: number;
  recommendation:
    | "strongly_recommended"
    | "recommended"
    | "consider"
    | "not_recommended";
  score_details: {
    skill_score: number;
    experience_score: number;
    education_score: number;
    semantic_score: number | null;
  };
  job_requirements: JobRequirements;
  matched_keywords: string[];
  missing_keywords: string[];
  strengths: string[];
  risks: string[];
  summary: string;
  scoring_mode: "ai_hybrid" | "deterministic";
}

export interface AnalyzeAndMatchResponse {
  analysis: ResumeAnalysis;
  match: MatchResult;
}

export interface HealthResponse {
  status: "ok";
  service: string;
  environment: string;
  ai_enabled: boolean;
  cache_backend: string;
}
