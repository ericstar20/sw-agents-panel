import { Component, DestroyRef, signal, computed, inject } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { DatePipe, DecimalPipe } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatCardModule } from '@angular/material/card';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatSnackBar } from '@angular/material/snack-bar';
import { finalize, interval } from 'rxjs';
import { IntegrationStatusComponent } from '../integration-status/integration-status.component';
import { Run } from './run.model';
import { RunService } from './run.service';
import { RunDetailComponent } from './run-detail/run-detail.component';
import { RunDurationPipe } from '../../../shared/pipes/run-duration.pipe';

const REFRESH_INTERVAL_MS = 3000;

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
    IntegrationStatusComponent,
    RunDurationPipe,
  ],
  templateUrl: './run-history.component.html',
  styleUrl: './run-history.component.scss',
})
export class RunHistoryComponent {
  private runsService = inject(RunService);
  private destroyRef = inject(DestroyRef);
  private snackBar = inject(MatSnackBar);
  private hasLoaded = false;
  private requestPending = false;
  runs = signal<Run[]>([]);
  selected = signal<Run | null>(null);
  loading = signal(false);
  detailLoading = signal(false);
  error = signal('');
  filter = signal('all');
  readonly statuses = [
    { value: 'all', label: 'All' },
    { value: 'running', label: 'Running' },
    { value: 'idle', label: 'Idle' },
    { value: 'completed', label: 'Completed' },
    { value: 'interrupted', label: 'Interrupted' },
    { value: 'failed', label: 'Failed' },
  ];
  hasSamples = computed(() => this.runs().some((r) => r.sample));
  activeCount = computed(() => this.runs().filter((r) => r.status === 'running').length);
  completedCount = computed(() => this.runs().filter((r) => r.status === 'completed').length);
  filtered = computed(() =>
    this.runs().filter((r) => this.filter() === 'all' || r.status === this.filter()),
  );
  private detailRequest = 0;
  detailError = signal('');
  constructor() {
    this.load();
    interval(REFRESH_INTERVAL_MS)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe(() => this.load(true));
  }
  load(background = false) {
    if (this.requestPending) return;
    this.requestPending = true;
    if (!background) this.loading.set(true);
    this.runsService
      .getAll()
      .pipe(
        takeUntilDestroyed(this.destroyRef),
        finalize(() => {
          this.requestPending = false;
          this.loading.set(false);
        }),
      )
      .subscribe({
        next: (rows) => {
          const known = new Set(this.runs().map((run) => run.id));
          const added = rows.filter((run) => !run.sample && !known.has(run.id));
          if (this.hasLoaded && added.length) {
            this.snackBar.open(
              `${added.length} new Codex session${added.length === 1 ? '' : 's'} detected`,
              'Dismiss',
              { duration: 5000 },
            );
          }
          this.hasLoaded = true;
          this.error.set('');
          this.runs.set(rows);
        },
        error: () => {
          this.error.set('Could not reach the local API. Check that both services are running.');
        },
      });
  }
  open(id: string) {
    const request = ++this.detailRequest;
    this.selected.set(null);
    this.detailError.set('');
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
            this.detailError.set('Could not load this run. Try again.');
            this.detailLoading.set(false);
          }
        },
      });
  }
}
