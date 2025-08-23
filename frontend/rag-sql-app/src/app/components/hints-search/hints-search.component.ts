import { Component, OnInit, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService, QueryHint, Suggestion } from '../../services/api.service';
import { Subject } from 'rxjs';
import { debounceTime, distinctUntilChanged, switchMap } from 'rxjs/operators';
import { ToastrService } from 'ngx-toastr';

@Component({
  selector: 'app-hints-search',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="bg-white rounded-lg shadow-md p-4">
      <div class="mb-3">
        <h3 class="text-lg font-semibold mb-2">Query Hints Library</h3>
        
        <!-- Search Input -->
        <div class="relative">
          <input
            type="text"
            [(ngModel)]="searchQuery"
            (ngModelChange)="onSearchChange($event)"
            (focus)="onFocus()"
            (blur)="onBlur()"
            (keydown)="onKeyDown($event)"
            placeholder="Search hints... (e.g., 'filter', 'join', 'group by')"
            class="w-full px-3 py-2 pl-10 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
          
          <!-- Search Icon -->
          <svg class="absolute left-3 top-2.5 w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
          </svg>
          
          <!-- Clear Button -->
          <button
            *ngIf="searchQuery"
            (click)="clearSearch()"
            class="absolute right-2 top-2.5 text-gray-400 hover:text-gray-600">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
            </svg>
          </button>
        </div>
        
        <!-- Category Filter Pills -->
        <div class="flex flex-wrap gap-2 mt-2">
          <button
            (click)="filterByCategory(null)"
            [class.bg-blue-500]="!selectedCategory"
            [class.text-white]="!selectedCategory"
            [class.bg-gray-200]="selectedCategory"
            class="px-3 py-1 rounded-full text-xs font-medium transition-colors">
            All
          </button>
          <button
            *ngFor="let category of categories"
            (click)="filterByCategory(category)"
            [class.bg-blue-500]="selectedCategory === category"
            [class.text-white]="selectedCategory === category"
            [class.bg-gray-200]="selectedCategory !== category"
            class="px-3 py-1 rounded-full text-xs font-medium transition-colors">
            {{ category }}
          </button>
        </div>
      </div>
      
      <!-- Results Dropdown -->
      <div *ngIf="showResults && (filteredHints.length > 0 || suggestions.length > 0)" 
           class="border border-gray-200 rounded-md max-h-96 overflow-y-auto">
        
        <!-- Suggestions Section -->
        <div *ngIf="suggestions.length > 0" class="border-b border-gray-200">
          <div class="px-3 py-2 bg-gray-50 text-xs font-semibold text-gray-600">
            SUGGESTIONS
          </div>
          <div *ngFor="let suggestion of suggestions; let i = index"
               [class.bg-blue-50]="selectedIndex === i"
               (click)="selectSuggestion(suggestion)"
               (mouseenter)="selectedIndex = i"
               class="px-3 py-2 hover:bg-gray-50 cursor-pointer border-b border-gray-100">
            <div class="flex items-start justify-between">
              <div class="flex-1">
                <div class="font-medium text-sm">{{ suggestion.suggestion }}</div>
                <div class="text-xs text-gray-500 mt-1">
                  <span class="bg-gray-100 px-2 py-0.5 rounded">{{ suggestion.category }}</span>
                  <span class="ml-2">Score: {{ suggestion.score }}</span>
                </div>
              </div>
              <button
                (click)="copySqlPattern(suggestion.sql_pattern, $event)"
                class="ml-2 p-1 hover:bg-gray-200 rounded"
                title="Copy SQL pattern">
                <svg class="w-4 h-4 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"></path>
                </svg>
              </button>
            </div>
            <div class="text-xs text-gray-600 mt-1 font-mono bg-gray-50 p-1 rounded">
              {{ suggestion.sql_pattern | slice:0:100 }}{{ suggestion.sql_pattern.length > 100 ? '...' : '' }}
            </div>
          </div>
        </div>
        
        <!-- Hints Section -->
        <div *ngIf="filteredHints.length > 0">
          <div class="px-3 py-2 bg-gray-50 text-xs font-semibold text-gray-600">
            QUERY HINTS ({{ filteredHints.length }})
          </div>
          <div *ngFor="let hint of filteredHints | slice:0:10; let i = index"
               [class.bg-blue-50]="selectedIndex === suggestions.length + i"
               (click)="selectHint(hint)"
               (mouseenter)="selectedIndex = suggestions.length + i"
               class="px-3 py-2 hover:bg-gray-50 cursor-pointer border-b border-gray-100">
            <div class="flex items-start justify-between">
              <div class="flex-1">
                <div class="font-medium text-sm">{{ hint.example }}</div>
                <div class="text-xs text-gray-500 mt-1">
                  <span class="bg-blue-100 text-blue-700 px-2 py-0.5 rounded">{{ hint.category }}</span>
                  <span class="ml-2" *ngFor="let tag of hint.tags">
                    <span class="bg-gray-100 px-1.5 py-0.5 rounded">{{ tag }}</span>
                  </span>
                  <span class="ml-2 text-gray-400">Used {{ hint.popularity }} times</span>
                </div>
              </div>
              <button
                (click)="copySqlPattern(hint.sql_pattern, $event)"
                class="ml-2 p-1 hover:bg-gray-200 rounded"
                title="Copy SQL pattern">
                <svg class="w-4 h-4 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"></path>
                </svg>
              </button>
            </div>
            <div class="text-xs text-gray-600 mt-1 font-mono bg-gray-50 p-1 rounded">
              {{ hint.sql_pattern }}
            </div>
            <div class="text-xs text-gray-500 mt-1">
              Keywords: {{ hint.keywords.join(', ') }}
            </div>
          </div>
        </div>
      </div>
      
      <!-- No Results -->
      <div *ngIf="showResults && searchQuery && filteredHints.length === 0 && suggestions.length === 0" 
           class="text-center py-4 text-gray-500">
        No hints found for "{{ searchQuery }}"
      </div>
      
      <!-- Stats -->
      <div class="mt-3 text-xs text-gray-500 flex justify-between">
        <span>{{ allHints.length }} hints available</span>
        <button
          (click)="initializeHints()"
          class="text-blue-500 hover:text-blue-700">
          Refresh Hints
        </button>
      </div>
    </div>
  `,
  styles: []
})
export class HintsSearchComponent implements OnInit {
  @Output() hintSelected = new EventEmitter<QueryHint>();
  @Output() suggestionUsed = new EventEmitter<Suggestion>();
  
  searchQuery = '';
  selectedCategory: string | null = null;
  categories: string[] = [];
  allHints: QueryHint[] = [];
  filteredHints: QueryHint[] = [];
  suggestions: Suggestion[] = [];
  showResults = false;
  selectedIndex = -1;
  
  private searchSubject = new Subject<string>();
  
  constructor(
    private apiService: ApiService,
    private toastr: ToastrService
  ) {}
  
  ngOnInit() {
    this.loadCategories();
    this.loadHints();
    
    // Setup debounced search
    this.searchSubject.pipe(
      debounceTime(300),
      distinctUntilChanged(),
      switchMap(query => {
        if (query.length < 2) {
          this.suggestions = [];
          this.filterHints();
          return [];
        }
        return this.apiService.getSuggestions(query, 5);
      })
    ).subscribe(suggestions => {
      this.suggestions = suggestions;
      this.showResults = true;
    });
  }
  
  loadCategories() {
    this.apiService.getHintCategories().subscribe({
      next: (categories) => {
        this.categories = categories;
      },
      error: (err) => {
        console.error('Failed to load categories:', err);
      }
    });
  }
  
  loadHints() {
    this.apiService.getHints().subscribe({
      next: (hints) => {
        this.allHints = hints;
        this.filterHints();
      },
      error: (err) => {
        this.toastr.error('Failed to load hints', 'Error');
      }
    });
  }
  
  onSearchChange(query: string) {
    this.searchQuery = query;
    this.searchSubject.next(query);
    this.filterHints();
    this.selectedIndex = -1;
  }
  
  filterHints() {
    let hints = this.allHints;
    
    // Filter by category
    if (this.selectedCategory) {
      hints = hints.filter(h => h.category === this.selectedCategory);
    }
    
    // Filter by search query
    if (this.searchQuery) {
      const query = this.searchQuery.toLowerCase();
      hints = hints.filter(h => 
        h.example.toLowerCase().includes(query) ||
        h.keywords.some(k => k.toLowerCase().includes(query)) ||
        h.tags.some(t => t.toLowerCase().includes(query)) ||
        h.category.toLowerCase().includes(query)
      );
    }
    
    // Sort by popularity
    this.filteredHints = hints.sort((a, b) => b.popularity - a.popularity);
    this.showResults = this.searchQuery.length > 0 || this.selectedCategory !== null;
  }
  
  filterByCategory(category: string | null) {
    this.selectedCategory = category;
    this.filterHints();
  }
  
  clearSearch() {
    this.searchQuery = '';
    this.suggestions = [];
    this.filterHints();
    this.selectedIndex = -1;
  }
  
  onFocus() {
    if (this.searchQuery || this.selectedCategory) {
      this.showResults = true;
    }
  }
  
  onBlur() {
    // Delay to allow click on results
    setTimeout(() => {
      this.showResults = false;
    }, 200);
  }
  
  onKeyDown(event: KeyboardEvent) {
    const totalItems = this.suggestions.length + Math.min(this.filteredHints.length, 10);
    
    if (!this.showResults || totalItems === 0) return;
    
    switch (event.key) {
      case 'ArrowDown':
        event.preventDefault();
        this.selectedIndex = Math.min(this.selectedIndex + 1, totalItems - 1);
        break;
      case 'ArrowUp':
        event.preventDefault();
        this.selectedIndex = Math.max(this.selectedIndex - 1, 0);
        break;
      case 'Enter':
        event.preventDefault();
        if (this.selectedIndex >= 0) {
          if (this.selectedIndex < this.suggestions.length) {
            this.selectSuggestion(this.suggestions[this.selectedIndex]);
          } else {
            const hintIndex = this.selectedIndex - this.suggestions.length;
            this.selectHint(this.filteredHints[hintIndex]);
          }
        }
        break;
      case 'Escape':
        this.showResults = false;
        this.selectedIndex = -1;
        break;
    }
  }
  
  selectHint(hint: QueryHint) {
    this.hintSelected.emit(hint);
    this.apiService.incrementHintPopularity(hint.id).subscribe();
    this.toastr.success(`Using hint: ${hint.example}`, 'Hint Selected');
    this.showResults = false;
  }
  
  selectSuggestion(suggestion: Suggestion) {
    this.suggestionUsed.emit(suggestion);
    this.toastr.success(`Using suggestion: ${suggestion.suggestion}`, 'Suggestion Selected');
    this.showResults = false;
  }
  
  copySqlPattern(pattern: string, event: Event) {
    event.stopPropagation();
    navigator.clipboard.writeText(pattern).then(() => {
      this.toastr.success('SQL pattern copied to clipboard', 'Copied');
    });
  }
  
  initializeHints() {
    this.apiService.initializeHints().subscribe({
      next: () => {
        this.toastr.success('Hints refreshed', 'Success');
        this.loadHints();
      },
      error: (err) => {
        this.toastr.error('Failed to refresh hints', 'Error');
      }
    });
  }
}