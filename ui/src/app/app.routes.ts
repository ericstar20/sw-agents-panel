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
      { path: '', redirectTo: 'overview', pathMatch: 'full' },
    ],
  },
  { path: '**', redirectTo: 'overview' },
];
