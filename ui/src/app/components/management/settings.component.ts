import { Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { DatePipe, DecimalPipe } from '@angular/common';
import { RouterLink } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';
import { ManagementService, Storage } from './management.service';
@Component({
  standalone: true,
  imports: [FormsModule, DatePipe, DecimalPipe, RouterLink, MatButtonModule],
  templateUrl: './settings.component.html',
  styleUrl: './management.scss',
})
export class SettingsComponent {
  private service = inject(ManagementService);
  storage = signal<Storage | null>(null);
  error = signal('');
  message = signal('');
  busy = signal(false);
  threshold = 100;
  constructor() {
    this.service.storage().subscribe({
      next: (s) => {
        this.storage.set(s);
        this.threshold = s.warning_bytes / 1000000;
      },
      error: () => this.error.set('Could not load storage settings.'),
    });
  }
  save() {
    this.busy.set(true);
    this.service.settings(Math.round(this.threshold * 1000000)).subscribe({
      next: (s) => {
        this.storage.set(s);
        this.message.set('Warning threshold saved.');
        this.error.set('');
        this.busy.set(false);
      },
      error: (e) => {
        this.error.set(e.error?.error ?? 'Could not save settings.');
        this.busy.set(false);
      },
    });
  }
  compact() {
    this.busy.set(true);
    this.service.compact().subscribe({
      next: (s) => {
        this.storage.set(s);
        this.message.set('Compaction complete. Collection has resumed.');
        this.error.set('');
        this.busy.set(false);
      },
      error: () => {
        this.error.set('Could not compact the database.');
        this.busy.set(false);
      },
    });
  }
}
