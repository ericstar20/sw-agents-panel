import { inject, Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { environment } from '../../../environments/environment';
import { Run } from '../agents/run-history/run.model';
export interface Storage {
  database: number;
  wal: number;
  journal: number;
  total_bytes: number;
  runs: number;
  events: number;
  oldest: string | null;
  warning_bytes: number;
  warning: boolean;
}
export interface Preview {
  cutoff: string | null;
  runs: number;
  events: number;
  token: string;
}
export interface History {
  items: Run[];
  total: number;
  page: number;
  options: Record<string, string[]>;
  agents: { id: string; name: string }[];
}
export interface Workflow {
  nodes: Run[];
  links: { source_id: string; target_id: string; kind: string }[];
}
@Injectable({ providedIn: 'root' })
export class ManagementService {
  private http = inject(HttpClient);
  private base = environment.apiBaseUrl;
  history(filters: Record<string, string>, page: number) {
    return this.http.get<History>(this.base + '/history', {
      params: new HttpParams({ fromObject: { ...filters, page: String(page) } }),
    });
  }
  storage() {
    return this.http.get<Storage>(this.base + '/storage');
  }
  settings(warning_bytes: number) {
    return this.http.post<Storage>(this.base + '/settings', { warning_bytes });
  }
  preview(days: number | null) {
    return this.http.post<Preview>(this.base + '/cleanup/preview', { days });
  }
  cleanup(preview: Preview) {
    return this.http.post(this.base + '/cleanup', preview);
  }
  compact() {
    return this.http.post<Storage>(this.base + '/storage/compact', {});
  }
  workflow() {
    return this.http.get<Workflow>(this.base + '/workflow');
  }
}
