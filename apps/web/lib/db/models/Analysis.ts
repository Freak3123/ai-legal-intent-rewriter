import mongoose, { Schema, type InferSchemaType, type Model } from 'mongoose';

const AnalysisSchema = new Schema(
  {
    documentId: { type: Schema.Types.ObjectId, ref: 'Document', required: true, index: true },
    userId: { type: Schema.Types.ObjectId, ref: 'User', required: true, index: true },
    status: {
      type: String,
      enum: ['queued', 'processing', 'completed', 'failed'],
      default: 'queued',
      index: true,
    },
    progress: { type: Number, default: 0, min: 0, max: 100 },
    modelVersions: {
      classifier: { type: String, default: '' },
      rewriter: { type: String, default: '' },
      nerVersion: { type: String, default: '' },
    },
    metrics: {
      totalClauses: { type: Number, default: 0 },
      highRiskCount: { type: Number, default: 0 },
      mediumRiskCount: { type: Number, default: 0 },
      avgConfidence: { type: Number, default: 0 },
    },
    startedAt: { type: Date, default: Date.now },
    completedAt: { type: Date },
    errorMessage: { type: String },
  },
  { timestamps: true }
);

AnalysisSchema.index({ documentId: 1, startedAt: -1 });

export type AnalysisDoc = InferSchemaType<typeof AnalysisSchema> & {
  _id: mongoose.Types.ObjectId;
};

export const Analysis: Model<AnalysisDoc> =
  (mongoose.models.Analysis as Model<AnalysisDoc>) ||
  mongoose.model<AnalysisDoc>('Analysis', AnalysisSchema);
