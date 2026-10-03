import { Component, input } from '@angular/core';

@Component({
  selector: 'app-icon',
  standalone: true,
  template: `
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      stroke-width="1.7"
      stroke-linecap="round"
      stroke-linejoin="round"
      aria-hidden="true"
      focusable="false"
    >
      @switch (name()) {
        @case ('overview') {
          <rect x="3" y="3" width="7" height="7" rx="1.5" />
          <rect x="14" y="3" width="7" height="7" rx="1.5" />
          <rect x="3" y="14" width="7" height="7" rx="1.5" />
          <rect x="14" y="14" width="7" height="7" rx="1.5" />
        }
        @case ('history') {
          <path d="M3 11a9 9 0 1 1 2.5 7.2M3 4v7h7M12 7v5l3 2" />
        }
        @case ('workflow') {
          <rect x="3" y="9" width="6" height="6" rx="1.5" />
          <rect x="15" y="3" width="6" height="6" rx="1.5" />
          <rect x="15" y="15" width="6" height="6" rx="1.5" />
          <path d="M9 12h3V6h3M12 12v6h3" />
        }
        @case ('settings') {
          <path d="M4 7h16M4 17h16" />
          <rect x="8" y="4" width="4" height="6" rx="1" />
          <rect x="14" y="14" width="4" height="6" rx="1" />
        }
        @case ('refresh') {
          <path d="M20 7v5h-5M4 17v-5h5M6.1 6.1A8 8 0 0 1 20 12M4 12a8 8 0 0 0 13.9 5.9" />
        }
        @case ('fit') {
          <path d="M8 3H3v5M16 3h5v5M3 16v5h5M21 16v5h-5" />
          <rect x="8" y="8" width="8" height="8" rx="1" />
        }
        @case ('previous') {
          <path d="m14 6-6 6 6 6" />
        }
        @case ('next') {
          <path d="m10 6 6 6-6 6" />
        }
      }
    </svg>
  `,
  styles: `
    :host {
      display: inline-flex;
      width: 18px;
      height: 18px;
      flex-shrink: 0;
      vertical-align: middle;
    }
    svg {
      width: 100%;
      height: 100%;
    }
  `,
})
export class AppIconComponent {
  name = input.required<string>();
}
