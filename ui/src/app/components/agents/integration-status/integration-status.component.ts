import { Component, DestroyRef, inject, signal } from '@angular/core';
import { KeyValuePipe } from '@angular/common';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { IntegrationService } from './integration.service';
import { Integration } from './integration.model';

@Component({
  selector: 'app-integration-status',
  standalone: true,
  imports: [KeyValuePipe],
  templateUrl: './integration-status.component.html',
  styleUrl: './integration-status.component.scss',
})
export class IntegrationStatusComponent {
  private readonly service = inject(IntegrationService);
  private readonly destroyRef = inject(DestroyRef);
  readonly integrations = signal<Integration[]>([]);
  readonly error = signal(false);
  readonly loading = signal(true);

  constructor() {
    this.refresh();
  }

  refresh() {
    this.loading.set(true);
    this.error.set(false);
    this.service
      .discover()
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (integrations) => {
          this.integrations.set(integrations);
          this.loading.set(false);
        },
        error: () => {
          this.error.set(true);
          this.loading.set(false);
        },
      });
  }
}
