export type ArtifactType = 'markdown' | 'html' | 'essay';

export type ArtifactTab = 'preview' | 'code' | 'split';

export interface Artifact {
  id: string;
  title: string;
  type: ArtifactType;
  content: string;
  createdAt: string;
  isDemonstration?: boolean;
  metadata?: {
    wordCount?: number;
    description?: string;
  };
}
