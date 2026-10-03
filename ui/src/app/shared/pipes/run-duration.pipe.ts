import { Pipe, PipeTransform } from '@angular/core';

@Pipe({ name: 'runDuration', standalone: true })
export class RunDurationPipe implements PipeTransform {
  transform(run: { started_at: string; finished_at: string | null }): string {
    if (!run.finished_at) return 'Unknown';
    const seconds = Math.round((Date.parse(run.finished_at) - Date.parse(run.started_at)) / 1000);
    return Number.isFinite(seconds) && seconds >= 0
      ? `${Math.floor(seconds / 60)}m ${seconds % 60}s`
      : 'Unknown';
  }
}
