import { AppIconComponent } from '../../shared/components/app-icon.component';
import { MatTooltipModule } from '@angular/material/tooltip';
import { Component, inject, signal, viewChild } from '@angular/core';
import { FFlowModule, FCanvasComponent } from '@foblex/flow';
import { MatButtonModule } from '@angular/material/button';
import { ManagementService, Workflow } from './management.service';
import { RunService } from '../agents/run-history/run.service';
import { Run } from '../agents/run-history/run.model';
import { RunDetailComponent } from '../agents/run-history/run-detail/run-detail.component';
@Component({
  standalone: true,
  imports: [FFlowModule, MatButtonModule, RunDetailComponent, AppIconComponent, MatTooltipModule],
  templateUrl: './workflow.component.html',
  styleUrl: './management.scss',
})
export class WorkflowComponent {
  private service = inject(ManagementService);
  private runs = inject(RunService);
  canvas = viewChild(FCanvasComponent);
  data = signal<Workflow>({ nodes: [], links: [] });
  selected = signal<Run | null>(null);
  error = signal('');
  busy = signal(false);
  positions = signal<Record<string, { x: number; y: number }>>({});
  constructor() {
    this.load();
  }
  load() {
    this.busy.set(true);
    this.error.set('');
    this.service.workflow().subscribe({
      next: (data) => {
        const levels: Record<string, number> = {};
        const depth = (id: string, seen = new Set<string>()): number => {
          if (seen.has(id)) return 0;
          seen.add(id);
          const parent = data.links.find((l) => l.target_id === id);
          return parent ? 1 + depth(parent.source_id, seen) : 0;
        };
        const positions: Record<string, { x: number; y: number }> = {};
        for (const node of data.nodes) {
          const level = depth(node.id);
          positions[node.id] = { x: 40 + level * 320, y: 40 + (levels[level] ?? 0) * 160 };
          levels[level] = (levels[level] ?? 0) + 1;
        }
        this.positions.set(positions);
        this.data.set(data);
        this.busy.set(false);
      },
      error: () => {
        this.error.set('Could not load workflow.');
        this.busy.set(false);
      },
    });
  }
  fit() {
    this.canvas()?.fitToScreen({ x: 40, y: 40 }, false);
  }
  open(id: string) {
    this.runs.getById(id).subscribe({
      next: (r) => this.selected.set(r),
      error: () => this.error.set('Could not load run details.'),
    });
  }
}
