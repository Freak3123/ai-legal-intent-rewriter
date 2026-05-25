// Shared types between web and ml. Source of truth: ../../docs/api-contract.md
// When changing these, update apps/ml/app/schemas/ to match.

export type IngestionMethod = 'pdfjs' | 'pymupdf' | 'tesseract-ocr' | 'text-direct';

export type ClassificationLabel =
  | 'LIABILITY'
  | 'TERMINATION'
  | 'PAYMENT'
  | 'CONFIDENTIALITY'
  | 'INDEMNIFICATION'
  | 'INTELLECTUAL_PROPERTY'
  | 'GOVERNING_LAW'
  | 'DISPUTE_RESOLUTION'
  | 'DEFINITIONS'
  | 'RENEWAL'
  | 'WARRANTY'
  | 'OTHER';

export type EntityType = 'DATE' | 'AMOUNT' | 'PARTY' | 'RIGHT' | 'OBLIGATION' | 'CONDITION';

export type RiskLevel = 'low' | 'medium' | 'high';

export interface TopK {
  label: ClassificationLabel;
  score: number;
}

export interface Entity {
  text: string;
  type: EntityType;
  start: number;
  end: number;
}

export interface Clause {
  ordinal: number;
  original_text: string;
  char_span: { start: number; end: number };
  classification: {
    label: ClassificationLabel;
    confidence: number;
    top_k: TopK[];
  };
  entities: Entity[];
  rewrite: {
    text: string;
    readability_score: number;
    method: 'model' | 'template-fallback';
  };
  risk: {
    level: RiskLevel;
    score: number;
    triggers: string[];
  };
}

export interface AnalyzeResponse {
  ingestion_method: IngestionMethod;
  page_count: number;
  clauses: Clause[];
  metrics: {
    total_clauses: number;
    high_risk_count: number;
    medium_risk_count: number;
    avg_confidence: number;
  };
  model_versions: {
    classifier: string;
    rewriter: string;
    ner_version: string;
  };
  timing_ms: {
    ingestion: number;
    segmentation: number;
    classification: number;
    ner: number;
    rewriting: number;
    risk_flagging: number;
    total: number;
  };
}

export interface HealthResponse {
  status: 'ready' | 'loading' | 'error';
  models_loaded: {
    classifier: boolean;
    rewriter: boolean;
    ner: boolean;
  };
  uptime_seconds: number;
  version: string;
}
