export interface Integration {
  tool: string;
  status: 'detected' | 'not_found';
  collection: string;
  configured_model: string | null;
  configured_provider: string | null;
  paths: Record<string, { path: string; exists: boolean }>;
  session_file_count: number | null;
  errors: string[];
}
