import { Component, computed, input, output } from '@angular/core';
import { DecimalPipe } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';
import { Run } from '../run.model';

@Component({
  selector: 'app-run-detail',
  standalone: true,
  imports: [DecimalPipe, MatButtonModule],
  templateUrl: './run-detail.component.html',
  styleUrl: './run-detail.component.scss',
})
export class RunDetailComponent {
  readonly run = input.required<Run>();
  readonly closed = output<void>();
  readonly actions = computed(() =>
    (this.run().events ?? []).filter(
      (event) => event.type === 'action' && event.payload.description,
    ),
  );
}
