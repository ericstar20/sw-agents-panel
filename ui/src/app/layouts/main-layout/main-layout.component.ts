import { AppIconComponent } from '../../shared/components/app-icon.component';
import { interval } from 'rxjs';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { ManagementService, Storage } from '../../components/management/management.service';
import { Component, inject, signal, DestroyRef } from '@angular/core';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';
import { MatChipsModule } from '@angular/material/chips';

@Component({
  selector: 'app-main-layout',
  standalone: true,
  imports: [
    RouterOutlet,
    RouterLink,
    RouterLinkActive,
    MatButtonModule,
    MatChipsModule,
    AppIconComponent,
  ],
  templateUrl: './main-layout.component.html',
  styleUrl: './main-layout.component.scss',
})
export class MainLayoutComponent {
  storage = signal<Storage | null>(null);
  private service = inject(ManagementService);
  private destroy = inject(DestroyRef);
  constructor() {
    this.refresh();
    interval(10000)
      .pipe(takeUntilDestroyed(this.destroy))
      .subscribe(() => this.refresh());
  }
  private refresh() {
    this.service
      .storage()
      .pipe(takeUntilDestroyed(this.destroy))
      .subscribe({ next: (s) => this.storage.set(s), error: () => {} });
  }
}
