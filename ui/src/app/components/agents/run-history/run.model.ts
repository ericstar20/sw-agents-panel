export interface Run {
  id: string;
  agent_name: string;
  ownership: string;
  tool: string;
  task: string;
  project: string;
  status: string;
  started_at: string;
  finished_at: string | null;
  provider: string | null;
  model: string | null;
  first_response_ms: number | null;
  input_tokens: number | null;
  output_tokens: number | null;
  cached_tokens: number | null;
  usage_scope: string | null;
  sample: number;
  events?: { id: number; type: string; payload: { description?: string; outcome?: string } }[];
}
