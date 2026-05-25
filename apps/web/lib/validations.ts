import { z } from 'zod';

// -----------------------------------------------------------------------------
// Auth
// -----------------------------------------------------------------------------

export const signupSchema = z.object({
  email: z.string().email('Please enter a valid email address'),
  name: z.string().min(2, 'Name must be at least 2 characters').max(80),
  password: z.string().min(8, 'Password must be at least 8 characters').max(120),
});
export type SignupInput = z.infer<typeof signupSchema>;

export const loginSchema = z.object({
  email: z.string().email(),
  password: z.string().min(1),
});
export type LoginInput = z.infer<typeof loginSchema>;

// -----------------------------------------------------------------------------
// Documents
// -----------------------------------------------------------------------------

export const createDocumentSchema = z.object({
  filename: z.string().min(1).max(200),
  mimeType: z.string().min(1),
  sizeBytes: z.number().int().positive().max(10 * 1024 * 1024), // 10 MB cap
  pageCount: z.number().int().nonnegative().default(0),
  extractedText: z.string().min(1).max(2_000_000), // ~2 MB of text
  ingestionMethod: z.enum(['pdfjs', 'pymupdf', 'tesseract-ocr', 'text-direct']),
});
export type CreateDocumentInput = z.infer<typeof createDocumentSchema>;

// -----------------------------------------------------------------------------
// Analyses
// -----------------------------------------------------------------------------

export const createAnalysisSchema = z.object({
  documentId: z.string().min(1, 'documentId is required'),
});
export type CreateAnalysisInput = z.infer<typeof createAnalysisSchema>;
