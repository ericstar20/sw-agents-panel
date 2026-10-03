import { Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { DatePipe, DecimalPipe } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';
import { ManagementService, History, Preview } from './management.service';
import { RunService } from '../agents/run-history/run.service';
import { Run } from '../agents/run-history/run.model';
import { RunDetailComponent } from '../agents/run-history/run-detail/run-detail.component';
@Component({
  standalone: true,
  imports: [FormsModule, DatePipe, DecimalPipe, MatButtonModule, RunDetailComponent],
  templateUrl: './history.component.html',
  styleUrl: './management.scss',
})
export class HistoryComponent {
  private service = inject(ManagementService);
  private runs = inject(RunService);
  data = signal<History | null>(null);
  selected = signal<Run | null>(null);
  preview = signal<Preview | null>(null);
  error = signal('');
  message = signal('');
  busy = signal(false);
  page = 1;
  days = 7;
  filters: Record<string, string> = {
    agent_id: '',
    provider: '',
    model: '',
    status: '',
    project: '',
    from: '',
    to: '',
  };
  constructor() {
    this.load();
  }
  load(reset = false) {
    if (reset) this.page = 1;
    this.busy.set(true);
    this.error.set('');
    this.service.history(this.filters, this.page).subscribe({
      next: (data) => {
        this.data.set(data);
        this.busy.set(false);
      },
      error: () => {
        this.error.set('Could not load history.');
        this.busy.set(false);
      },
    });
  }
  changePage(delta: number) {
    this.page += delta;
    this.load();
  }
  open(id: string) {
    this.runs.getById(id).subscribe({
      next: (run) => this.selected.set(run),
      error: () => this.error.set('Could not load run details.'),
    });
  }
  showPreview(all = false) {
    this.busy.set(true);
    this.preview.set(null);
    this.error.set('');
    this.service.preview(all ? null : Number(this.days)).subscribe({
      next: (p) => {
        this.preview.set(p);
        this.busy.set(false);
      },
      error: (e) => {
        this.error.set(e.error?.error ?? 'Could not preview cleanup.');
        this.busy.set(false);
      },
    });
  }
  cancel() {
    this.preview.set(null);
  }
  confirm() {
    const p = this.preview();
    if (!p) return;
    this.busy.set(true);
    this.service.cleanup(p).subscribe({
      next: () => {
        this.preview.set(null);
        this.selected.set(null);
        this.message.set(`Deleted ${p.runs} finished runs and ${p.events} events.`);
        this.page = 1;
        this.load();
      },
      error: (e) => {
        this.error.set(e.error?.error ?? 'Cleanup failed.');
        this.preview.set(null);
        this.busy.set(false);
      },
    });
  }
}
