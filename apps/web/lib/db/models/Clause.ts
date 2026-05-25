import mongoose, { Schema, type InferSchemaType, type Model } from 'mongoose';

const TopKSchema = new Schema(
  { label: String, score: Number },
  { _id: false }
);

const EntitySchema = new Schema(
  {
    text: String,
    type: { type: String, enum: ['DATE', 'AMOUNT', 'PARTY', 'RIGHT', 'OBLIGATION', 'CONDITION'] },
    start: Number,
    end: Number,
  },
  { _id: false }
);

const ClauseSchema = new Schema({
  analysisId: { type: Schema.Types.ObjectId, ref: 'Analysis', required: true, index: true },
  documentId: { type: Schema.Types.ObjectId, ref: 'Document', required: true, index: true },
  ordinal: { type: Number, required: true },
  originalText: { type: String, required: true },
  charSpan: { start: Number, end: Number },
  classification: {
    label: String,
    confidence: Number,
    topK: [TopKSchema],
  },
  entities: [EntitySchema],
  rewrite: {
    text: String,
    readabilityScore: Number,
    method: { type: String, enum: ['model', 'template-fallback'] },
  },
  risk: {
    level: { type: String, enum: ['low', 'medium', 'high'] },
    score: Number,
    triggers: [String],
  },
});

ClauseSchema.index({ analysisId: 1, ordinal: 1 });
ClauseSchema.index({ analysisId: 1, 'risk.level': 1 });

export type ClauseDoc = InferSchemaType<typeof ClauseSchema> & {
  _id: mongoose.Types.ObjectId;
};

export const Clause: Model<ClauseDoc> =
  (mongoose.models.Clause as Model<ClauseDoc>) ||
  mongoose.model<ClauseDoc>('Clause', ClauseSchema);
