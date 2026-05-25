import mongoose, { Schema, type InferSchemaType, type Model } from 'mongoose';

const DocumentSchema = new Schema(
  {
    userId: { type: Schema.Types.ObjectId, ref: 'User', required: true, index: true },
    filename: { type: String, required: true, trim: true },
    mimeType: { type: String, required: true },
    sizeBytes: { type: Number, required: true },
    pageCount: { type: Number, default: 0 },
    extractedText: { type: String, required: true },
    ingestionMethod: {
      type: String,
      enum: ['pdfjs', 'pymupdf', 'tesseract-ocr', 'text-direct'],
      required: true,
    },
    hash: { type: String, required: true, index: true }, // sha256 of text, for de-dup
  },
  { timestamps: { createdAt: 'uploadedAt', updatedAt: 'updatedAt' } }
);

DocumentSchema.index({ userId: 1, uploadedAt: -1 });

export type DocumentDoc = InferSchemaType<typeof DocumentSchema> & {
  _id: mongoose.Types.ObjectId;
  uploadedAt: Date;
};

export const DocumentModel: Model<DocumentDoc> =
  (mongoose.models.Document as Model<DocumentDoc>) ||
  mongoose.model<DocumentDoc>('Document', DocumentSchema);
