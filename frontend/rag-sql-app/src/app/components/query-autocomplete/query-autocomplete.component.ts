import { Component, Input, Output, EventEmitter, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService, Suggestion } from '../../services/api.service';
import { Subject } from 'rxjs';
import { debounceTime, distinctUntilChanged, switchMap } from 'rxjs/operators';

@Component({
  selector: 'app-query-autocomplete',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="relative">
      <textarea
        [(ngModel)]="queryText"
        (ngModelChange)="onQueryChange($event)"
        (focus)="onFocus()"
        (blur)="onBlur()"
        (keydown)="onKeyDown($event)"
        [placeholder]="placeholder"
        class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
        [rows]="rows">
      </textarea>
      
      <!-- Suggestions dropdown -->
      <div *ngIf="showSuggestions && suggestions.length > 0" 
           class="absolute z-10 w-full mt-1 bg-white border border-gray-200 rounded-md shadow-lg max-h-60 overflow-auto">
        <div *ngFor="let suggestion of suggestions; let i = index"
             [class.bg-blue-50]="i === selectedIndex"
             (mousedown)="selectSuggestion(suggestion)"
             (mouseenter)="selectedIndex = i"
             class="px-4 py-2 hover:bg-gray-50 cursor-pointer">
          <div class="flex items-center justify-between">
            <div class="flex-1">
              <span class="font-medium">{{ suggestion.suggestion }}</span>
              <span class="ml-2 text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
                {{ suggestion.category }}
              </span>
            </div>
            <span class="text-xs text-gray-400">
              {{ suggestion.type === 'hint' ? '💡' : '📝' }}
            </span>
          </div>
          <div class="text-xs text-gray-600 mt-1 font-mono">
            {{ suggestion.sql_pattern | slice:0:100 }}{{ suggestion.sql_pattern.length > 100 ? '...' : '' }}
          </div>
        </div>
      </div>
      
      <!-- Hints helper -->
      <div class="mt-2 text-xs text-gray-500">
        <span class="font-medium">Tips:</span>
        Try phrases like "show top", "filter by", "group by", "order by date", etc.
      </div>
    </div>
  `
})
export class QueryAutocompleteComponent implements OnInit, OnDestroy {
  @Input() placeholder = 'Enter your query in natural language...';
  @Input() rows = 3;
  @Input() value = '';
  @Output() valueChange = new EventEmitter<string>();
  @Output() suggestionSelected = new EventEmitter<Suggestion>();
  
  queryText = '';
  suggestions: Suggestion[] = [];
  showSuggestions = false;
  selectedIndex = -1;
  
  private searchSubject = new Subject<string>();
  private destroy$ = new Subject<void>();
  
  constructor(private apiService: ApiService) {}
  
  ngOnInit() {
    this.queryText = this.value;
    
    // Setup debounced search
    this.searchSubject.pipe(
      debounceTime(300),
      distinctUntilChanged(),
      switchMap(query => {
        if (query.length < 2) {
          this.suggestions = [];
          return [];
        }
        return this.apiService.getSuggestions(query, 10);
      })
    ).subscribe(suggestions => {
      this.suggestions = suggestions;
      this.showSuggestions = suggestions.length > 0;
    });
  }
  
  ngOnDestroy() {
    this.destroy$.next();
    this.destroy$.complete();
  }
  
  onQueryChange(value: string) {
    this.queryText = value;
    this.valueChange.emit(value);
    this.searchSubject.next(value);
    this.selectedIndex = -1;
  }
  
  onFocus() {
    if (this.suggestions.length > 0) {
      this.showSuggestions = true;
    }
  }
  
  onBlur() {
    // Delay to allow click on suggestion
    setTimeout(() => {
      this.showSuggestions = false;
    }, 200);
  }
  
  onKeyDown(event: KeyboardEvent) {
    if (!this.showSuggestions || this.suggestions.length === 0) return;
    
    switch (event.key) {
      case 'ArrowDown':
        event.preventDefault();
        this.selectedIndex = Math.min(this.selectedIndex + 1, this.suggestions.length - 1);
        break;
      case 'ArrowUp':
        event.preventDefault();
        this.selectedIndex = Math.max(this.selectedIndex - 1, 0);
        break;
      case 'Enter':
        if (this.selectedIndex >= 0) {
          event.preventDefault();
          this.selectSuggestion(this.suggestions[this.selectedIndex]);
        }
        break;
      case 'Escape':
        this.showSuggestions = false;
        this.selectedIndex = -1;
        break;
    }
  }
  
  selectSuggestion(suggestion: Suggestion) {
    this.queryText = suggestion.suggestion;
    this.valueChange.emit(suggestion.suggestion);
    this.suggestionSelected.emit(suggestion);
    this.showSuggestions = false;
    this.selectedIndex = -1;
    
    // Increment popularity
    if (suggestion.type === 'hint') {
      // Note: We need the hint ID which isn't in the Suggestion interface
      // This would need to be added to properly track popularity
    }
  }
}