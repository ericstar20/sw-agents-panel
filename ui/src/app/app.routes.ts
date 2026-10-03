import { Routes } from '@angular/router';
import { MainLayoutComponent } from './layouts/main-layout/main-layout.component';

export const routes: Routes = [
  {
    path: '',
    component: MainLayoutComponent,
    children: [
      {
        path: 'overview',
        loadComponent: () =>
          import('./components/agents/run-history/run-history.component').then(
            (module) => module.RunHistoryComponent,
          ),
      },
      {
        path: 'history',
        loadComponent: () =>
          import('./components/management/history.component').then((m) => m.HistoryComponent),
      },
      {
        path: 'settings',
        loadComponent: () =>
          import('./components/management/settings.component').then((m) => m.SettingsComponent),
      },
      {
        path: 'workflow',
        loadComponent: () =>
          import('./components/management/workflow.component').then((m) => m.WorkflowComponent),
      },
      { path: '', redirectTo: 'overview', pathMatch: 'full' },
    ],
  },
  { path: '**', redirectTo: 'overview' },
];
