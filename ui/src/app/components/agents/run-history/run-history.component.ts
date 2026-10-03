import { Component, DestroyRef, signal, computed, inject } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { DatePipe, DecimalPipe } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatCardModule } from '@angular/material/card';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { Run } from './run.model';
import { RunService } from './run.service';
import { RunDetailComponent } from './run-detail/run-detail.component';
import { RunDurationPipe } from '../../../shared/pipes/run-duration.pipe';

@Component({
  selector: 'app-run-history',
  standalone: true,
  imports: [
    DatePipe,
    DecimalPipe,
    MatButtonModule,
    MatIconModule,
    MatTooltipModule,
    MatCardModule,
    MatProgressBarModule,
    RunDetailComponent,
    RunDurationPipe,
  ],
  templateUrl: './run-history.component.html',
  styleUrl: './run-history.component.scss',
})
export class RunHistoryComponent {
  private runsService = inject(RunService);
  private destroyRef = inject(DestroyRef);
  runs = signal<Run[]>([]);
  selected = signal<Run | null>(null);
  loading = signal(false);
  detailLoading = signal(false);
  error = signal('');
  filter = signal('all');
  readonly statuses = [
    { value: 'all', label: 'All' },
    { value: 'running', label: 'Running' },
    { value: 'completed', label: 'Completed' },
    { value: 'failed', label: 'Failed' },
  ];
  hasSamples = computed(() => this.runs().some((r) => r.sample));
  activeCount = computed(() => this.runs().filter((r) => r.status === 'running').length);
  completedCount = computed(() => this.runs().filter((r) => r.status === 'completed').length);
  filtered = computed(() =>
    this.runs().filter((r) => this.filter() === 'all' || r.status === this.filter()),
  );
  private detailRequest = 0;
  constructor() {
    this.load();
  }
  load() {
    this.loading.set(true);
    this.error.set('');
    this.runsService
      .getAll()
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (rows) => {
          this.runs.set(rows);
          this.loading.set(false);
        },
        error: () => {
          this.error.set('Could not reach the local API. Check that both services are running.');
          this.loading.set(false);
        },
      });
  }
  open(id: string) {
    const request = ++this.detailRequest;
    this.selected.set(null);
    this.detailLoading.set(true);
    this.runsService
      .getById(id)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (run) => {
          if (request === this.detailRequest) {
            this.selected.set(run);
            this.detailLoading.set(false);
          }
        },
        error: () => {
          if (request === this.detailRequest) {
            this.error.set('Could not load this run. Try again.');
            this.detailLoading.set(false);
          }
        },
      });
  }
}
