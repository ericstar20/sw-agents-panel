import { HttpClient } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { environment } from '../../../../environments/environment';
import { Integration } from './integration.model';

@Injectable({ providedIn: 'root' })
export class IntegrationService {
  private readonly http = inject(HttpClient);

  discover() {
    return this.http.get<Integration[]>(`${environment.apiBaseUrl}/integrations`);
  }
}
