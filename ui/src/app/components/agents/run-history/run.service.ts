import { HttpClient } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';
import { Run } from './run.model';

@Injectable({ providedIn: 'root' })
export class RunService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = `${environment.apiBaseUrl}/runs`;

  getAll(): Observable<Run[]> {
    return this.http.get<Run[]>(this.baseUrl);
  }

  getById(id: string): Observable<Run> {
    return this.http.get<Run>(`${this.baseUrl}/${encodeURIComponent(id)}`);
  }
}
