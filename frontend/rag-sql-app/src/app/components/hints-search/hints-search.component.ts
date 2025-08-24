import { Component, OnInit, OnChanges, SimpleChanges, Output, EventEmitter, Input } from '@angular/core';
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
    <div class="bg-white rounded-xl shadow-lg border border-gray-100 overflow-hidden">
      <!-- Header -->
      <div class="bg-gradient-to-r from-teal-600 to-cyan-600 px-3 py-2">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2">
            <svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"></path>
            </svg>
            <h3 class="text-sm font-semibold text-white">Database Tables</h3>
          </div>
          <span class="bg-white/20 text-white px-2 py-0.5 rounded-full text-xs">
            {{ tables.length }} Tables
          </span>
        </div>
      </div>
      
      <div class="p-5">
        <!-- Search Input -->
        <div class="relative mb-4">
          <input
            type="text"
            [(ngModel)]="searchQuery"
            (ngModelChange)="onSearchChange($event)"
            (focus)="onFocus()"
            (blur)="onBlur()"
            (keydown)="onKeyDown($event)"
            placeholder="Search tables... (e.g., 'Students', 'Applications', 'Scholarships')"
            class="w-full px-4 py-3 pl-12 pr-12 bg-gray-50 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent transition-all duration-200 placeholder-gray-400">
          
          <!-- Search Icon / Loading Spinner -->
          <div class="absolute left-4 top-3.5">
            <svg *ngIf="!isSearching" class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
            </svg>
            <svg *ngIf="isSearching" class="animate-spin w-5 h-5 text-teal-500" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="m4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
          </div>
          
          <!-- Clear Button -->
          <button
            *ngIf="searchQuery && !isSearching"
            (click)="clearSearch()"
            class="absolute right-4 top-3.5 text-gray-400 hover:text-gray-600 transition-colors duration-200">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
            </svg>
          </button>
        </div>
        
        <!-- Category Filter Pills -->
        <div class="flex flex-wrap gap-2 mb-4">
          <button
            (click)="filterByCategory(null)"
            [class.bg-gradient-to-r]="!selectedCategory"
            [class.from-teal-600]="!selectedCategory"
            [class.to-cyan-600]="!selectedCategory"
            [class.text-white]="!selectedCategory"
            [class.shadow-md]="!selectedCategory"
            [class.bg-gray-100]="selectedCategory"
            [class.text-gray-700]="selectedCategory"
            class="px-4 py-2 rounded-full text-sm font-medium transition-all duration-200 hover:shadow-md">
            All Categories
          </button>
          <button
            *ngFor="let category of categories"
            (click)="filterByCategory(category)"
            [class.bg-gradient-to-r]="selectedCategory === category"
            [class.from-teal-600]="selectedCategory === category"
            [class.to-cyan-600]="selectedCategory === category"
            [class.text-white]="selectedCategory === category"
            [class.shadow-md]="selectedCategory === category"
            [class.bg-gray-100]="selectedCategory !== category"
            [class.text-gray-700]="selectedCategory !== category"
            class="px-4 py-2 rounded-full text-sm font-medium transition-all duration-200 hover:shadow-md">
            {{ category }}
          </button>
        </div>
      
        <!-- Results Dropdown -->
        <div *ngIf="showResults && (filteredTables.length > 0 || filteredHints.length > 0 || suggestions.length > 0)" 
             class="border border-gray-200 rounded-lg max-h-96 overflow-y-auto shadow-inner bg-gray-50">
          
          <!-- Smart Suggestions for Count -->
          <div *ngIf="searchQuery.toLowerCase().includes('count') && filteredTables.length > 0" class="border-b border-gray-200">
            <div class="px-4 py-2 bg-gradient-to-r from-green-50 to-emerald-50 text-xs font-bold text-green-700 uppercase tracking-wider">
              💡 Quick Count Queries (Top Tables by Importance)
            </div>
            <div class="divide-y divide-gray-100">
              <div *ngFor="let table of filteredTables.slice(0, 5); let idx = index"
                   (click)="selectCountQuery(table)"
                   class="px-4 py-2 hover:bg-green-50 cursor-pointer transition-colors duration-150 group">
                <div class="flex items-center justify-between">
                  <div>
                    <span class="text-sm font-medium text-gray-900">Count {{ table.name }}</span>
                    <span class="text-xs text-gray-500 ml-2">→ "count {{ table.name.toLowerCase() }}"</span>
                  </div>
                  <span *ngIf="table.row_count" class="text-xs text-gray-400 group-hover:text-gray-600">
                    ~{{ table.row_count | number }} rows
                  </span>
                </div>
              </div>
            </div>
          </div>
          
          <!-- Database Tables Section -->
          <div *ngIf="filteredTables.length > 0" class="border-b border-gray-200">
            <div class="px-4 py-2 bg-gradient-to-r from-indigo-50 to-purple-50 text-xs font-bold text-indigo-700 uppercase tracking-wider">
              Database Tables ({{ filteredTables.length }}) - Sorted by Importance
            </div>
            <div *ngFor="let table of filteredTables | slice:0:10; let i = index"
                 [class.bg-indigo-50]="selectedIndex === i"
                 (click)="selectTable(table)"
                 (mouseenter)="selectedIndex = i"
                 class="px-4 py-3 hover:bg-indigo-50 cursor-pointer border-b border-gray-100 transition-colors duration-200">
              <div class="flex items-start justify-between">
                <div class="flex-1">
                  <div class="font-semibold text-sm text-gray-800">{{ table.name }}</div>
                  <div class="flex items-center gap-2 mt-1">
                    <span class="bg-indigo-100 text-indigo-700 px-2 py-0.5 rounded-full text-xs font-medium">
                      {{ table.columns?.length || 0 }} columns
                    </span>
                    <span class="text-xs text-gray-500">{{ table.row_count | number }} rows</span>
                    <span *ngIf="table.primary_keys?.length > 0" class="text-xs text-amber-600">
                      PK: {{ table.primary_keys.join(', ') }}
                    </span>
                  </div>
                  <div class="text-xs text-gray-600 mt-1">
                    Columns: {{ getTableColumnNames(table).slice(0, 5).join(', ') }}{{ getTableColumnNames(table).length > 5 ? '...' : '' }}
                  </div>
                </div>
                <button
                  (click)="useTableQuery(table, $event)"
                  class="ml-2 p-1.5 hover:bg-indigo-100 rounded-lg transition-colors duration-200"
                  title="Use in query">
                  <svg class="w-4 h-4 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path>
                  </svg>
                </button>
              </div>
            </div>
          </div>
          
          <!-- Suggestions Section -->
          <div *ngIf="suggestions.length > 0" class="border-b border-gray-200">
            <div class="px-4 py-2 bg-gradient-to-r from-teal-50 to-cyan-50 text-xs font-bold text-teal-700 uppercase tracking-wider">
              AI Suggestions
            </div>
            <div *ngFor="let suggestion of suggestions; let i = index"
                 [class.bg-teal-50]="selectedIndex === filteredTables.length + i"
                 (click)="selectSuggestion(suggestion)"
                 (mouseenter)="selectedIndex = i"
                 class="px-4 py-3 hover:bg-teal-50 cursor-pointer border-b border-gray-100 transition-colors duration-200">
              <div class="flex items-start justify-between">
                <div class="flex-1">
                  <div class="font-semibold text-sm text-gray-800">{{ suggestion.suggestion }}</div>
                  <div class="flex items-center gap-2 mt-1">
                    <span class="bg-teal-100 text-teal-700 px-2 py-0.5 rounded-full text-xs font-medium">{{ suggestion.category }}</span>
                    <span class="text-xs text-gray-500">Score: {{ suggestion.score }}</span>
                  </div>
                </div>
                <button
                  (click)="copySqlPattern(suggestion.sql_pattern, $event)"
                  class="ml-2 p-1.5 hover:bg-teal-100 rounded-lg transition-colors duration-200"
                  title="Copy SQL pattern">
                  <svg class="w-4 h-4 text-teal-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"></path>
                  </svg>
                </button>
              </div>
              <div class="text-xs text-gray-600 mt-2 font-mono bg-white p-2 rounded border border-gray-200">
                {{ suggestion.sql_pattern | slice:0:100 }}{{ suggestion.sql_pattern.length > 100 ? '...' : '' }}
              </div>
            </div>
          </div>
          
          <!-- Hints Section -->
          <div *ngIf="filteredHints.length > 0">
            <div class="px-4 py-2 bg-gradient-to-r from-blue-50 to-indigo-50 text-xs font-bold text-blue-700 uppercase tracking-wider">
              Query Hints ({{ filteredHints.length }})
            </div>
            <div *ngFor="let hint of filteredHints | slice:0:10; let i = index"
                 [class.bg-blue-50]="selectedIndex === filteredTables.length + suggestions.length + i"
                 (click)="selectHint(hint)"
                 (mouseenter)="selectedIndex = filteredTables.length + suggestions.length + i"
                 class="px-4 py-3 hover:bg-blue-50 cursor-pointer border-b border-gray-100 transition-colors duration-200">
              <div class="flex items-start justify-between">
                <div class="flex-1">
                  <div class="font-semibold text-sm text-gray-800">{{ hint.example }}</div>
                  <div class="flex flex-wrap items-center gap-2 mt-1">
                    <span class="bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full text-xs font-medium">{{ hint.category }}</span>
                    <span *ngFor="let tag of hint.tags">
                      <span class="bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full text-xs">{{ tag }}</span>
                    </span>
                    <span class="text-xs text-gray-400">Used {{ hint.popularity }} times</span>
                  </div>
                </div>
                <button
                  (click)="copySqlPattern(hint.sql_pattern, $event)"
                  class="ml-2 p-1.5 hover:bg-blue-100 rounded-lg transition-colors duration-200"
                  title="Copy SQL pattern">
                  <svg class="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"></path>
                  </svg>
                </button>
              </div>
              <div class="text-xs text-gray-600 mt-2 font-mono bg-white p-2 rounded border border-gray-200">
                {{ hint.sql_pattern }}
              </div>
              <div class="text-xs text-gray-500 mt-1">
                <span class="font-medium">Keywords:</span> {{ hint.keywords.join(', ') }}
              </div>
            </div>
          </div>
        </div>
        
        <!-- No Results -->
        <div *ngIf="showResults && searchQuery && filteredHints.length === 0 && suggestions.length === 0" 
             class="bg-gray-50 rounded-lg p-8 text-center">
          <svg class="w-12 h-12 text-gray-300 mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
          </svg>
          <p class="text-gray-500 text-sm">No hints found for "{{ searchQuery }}"</p>
          <p class="text-gray-400 text-xs mt-1">Try different keywords or browse categories</p>
        </div>
        
        <!-- No Connection Message -->
        <div *ngIf="!connectionId" class="bg-amber-50 border border-amber-200 rounded-lg p-4 text-center">
          <p class="text-amber-800 text-sm font-medium">Please select a database connection to view tables</p>
        </div>
        
        <!-- Stats -->
        <div *ngIf="connectionId" class="mt-4 flex justify-between items-center">
          <span class="text-sm text-gray-500">
            <span class="font-semibold">{{ tables.length }}</span> tables • 
            <span class="font-semibold">{{ getTotalColumns() }}</span> columns
          </span>
          <button
            (click)="initializeHints()"
            class="flex items-center gap-1 text-sm text-teal-600 hover:text-teal-700 font-medium transition-colors duration-200">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
            </svg>
            Refresh
          </button>
        </div>
      </div>
    </div>
  `,
  styles: []
})
export class HintsSearchComponent implements OnInit, OnChanges {
  @Input() connectionId: number | null = null;
  @Output() hintSelected = new EventEmitter<QueryHint>();
  @Output() suggestionUsed = new EventEmitter<Suggestion>();
  
  searchQuery = '';
  selectedCategory: string | null = null;
  categories: string[] = ['Tables', 'Views', 'Relationships'];
  allHints: QueryHint[] = [];
  filteredHints: QueryHint[] = [];
  suggestions: Suggestion[] = [];
  showResults = false;
  selectedIndex = -1;
  isSearching = false;
  
  // Database schema
  tables: any[] = [];
  filteredTables: any[] = [];
  documentation: any = null;
  
  private searchSubject = new Subject<string>();
  private filterSubject = new Subject<string>();
  
  constructor(
    private apiService: ApiService,
    private toastr: ToastrService
  ) {}
  
  ngOnChanges(changes: SimpleChanges) {
    if (changes['connectionId'] && !changes['connectionId'].firstChange) {
      this.loadDatabaseSchema();
    }
  }
  
  ngOnInit() {
    this.loadDatabaseSchema();
    this.loadHints();
    
    // Setup debounced search for API suggestions
    this.searchSubject.pipe(
      debounceTime(1000), // Increased to 1 second to stop the spam
      distinctUntilChanged(),
      switchMap(query => {
        console.log('🔍 Debounced API call triggered for:', query);
        if (query.length < 2) {
          this.suggestions = [];
          this.isSearching = false;
          return [];
        }
        this.isSearching = true;
        return this.apiService.getSuggestions(query, 5);
      })
    ).subscribe({
      next: (suggestions) => {
        this.suggestions = suggestions;
        this.isSearching = false;
        this.showResults = true;
      },
      error: (err) => {
        console.error('Search suggestions error:', err);
        this.isSearching = false;
        this.suggestions = [];
        // Still show results with local hints
        this.showResults = true;
      }
    });

    // Setup debounced local filtering for better performance
    this.filterSubject.pipe(
      debounceTime(300), // Increased debounce for local filtering
      distinctUntilChanged()
    ).subscribe(query => {
      console.log('🏠 Local filtering triggered for:', query);
      this.filterHints();
      this.showResults = query.length > 0 || this.selectedCategory !== null;
    });
  }
  
  loadDatabaseSchema() {
    console.log('Loading database schema for connection:', this.connectionId);
    if (!this.connectionId) {
      console.log('No connection ID, skipping schema load');
      return;
    }
    
    this.apiService.getDocumentation(this.connectionId, 'json').subscribe({
      next: (doc) => {
        console.log('Documentation received:', doc);
        this.documentation = doc;
        if (doc && doc.tables) {
          this.tables = Object.values(doc.tables);
          console.log('Tables loaded:', this.tables.length);
          this.filterTables();
        }
      },
      error: (err) => {
        console.error('Failed to load database schema:', err);
        // Try to load a basic schema at least
        this.tables = [];
        this.filteredTables = [];
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
    console.log('⌨️ Search change triggered:', query);
    this.searchQuery = query;
    // Only trigger the debounced subjects, don't make immediate API calls
    this.searchSubject.next(query); // For API suggestions (debounced)
    this.filterSubject.next(query); // For local filtering (debounced)
    this.selectedIndex = -1;
  }
  
  filterHints() {
    this.filterTables();
    
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
  }
  
  filterTables() {
    if (!this.tables) {
      this.filteredTables = [];
      return;
    }
    
    let tables = this.tables;
    
    // Filter by category
    if (this.selectedCategory === 'Tables') {
      tables = tables.filter(t => !t.name.includes('vw_'));
    } else if (this.selectedCategory === 'Views') {
      tables = tables.filter(t => t.name.includes('vw_'));
    }
    
    // Smart filtering based on search query
    if (this.searchQuery) {
      const query = this.searchQuery.toLowerCase();
      
      // Smart keywords that should show all tables with priority sorting
      const smartKeywords = ['count', 'show', 'select', 'list', 'get', 'find', 'search', 'all'];
      const isSmartQuery = smartKeywords.some(keyword => query.includes(keyword));
      
      if (isSmartQuery) {
        // Don't filter, but prioritize important tables
        tables = [...this.tables];
      } else {
        // Regular filtering
        tables = tables.filter(t => 
          t.name.toLowerCase().includes(query) ||
          t.columns.some((c: any) => c.name.toLowerCase().includes(query))
        );
      }
    }
    
    // Smart sorting by importance and relevance
    this.filteredTables = tables.sort((a, b) => {
      // Define importance scores for tables
      const importanceMap: { [key: string]: number } = {
        'Students': 100,
        'ScholarshipApplications': 95,
        'Scholarships': 90,
        'Cities': 85,
        'HighSchools': 80,
        'Addresses': 75,
        'Universities': 70,
        'Colleges': 65,
        'Programs': 60,
        'Awards': 55,
        'Donors': 50,
        'DonorAddresses': 45,
        'StudentAddresses': 40,
        'ApplicationStatus': 35
      };
      
      // Get importance scores
      const aImportance = importanceMap[a.name] || 0;
      const bImportance = importanceMap[b.name] || 0;
      
      // For "count" queries, prioritize by importance
      const query = this.searchQuery.toLowerCase();
      if (query.includes('count')) {
        if (aImportance !== bImportance) {
          return bImportance - aImportance;
        }
      }
      
      // Then sort by exact match
      const aExactMatch = a.name.toLowerCase() === query;
      const bExactMatch = b.name.toLowerCase() === query;
      if (aExactMatch && !bExactMatch) return -1;
      if (!aExactMatch && bExactMatch) return 1;
      
      // Then by starts with
      const aStartsWith = a.name.toLowerCase().startsWith(query);
      const bStartsWith = b.name.toLowerCase().startsWith(query);
      if (aStartsWith && !bStartsWith) return -1;
      if (!aStartsWith && bStartsWith) return 1;
      
      // Finally by row count
      return (b.row_count || 0) - (a.row_count || 0);
    });
    
    // Limit to top 15 most relevant tables
    if (this.searchQuery && this.searchQuery.toLowerCase().includes('count')) {
      this.filteredTables = this.filteredTables.slice(0, 15);
    }
  }
  
  filterByCategory(category: string | null) {
    this.selectedCategory = category;
    this.filterSubject.next(this.searchQuery); // Trigger debounced filtering
  }
  
  clearSearch() {
    this.searchQuery = '';
    this.suggestions = [];
    this.filterSubject.next(''); // Trigger debounced filtering
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
    const tablesCount = Math.min(this.filteredTables.length, 10);
    const suggestionsCount = this.suggestions.length;
    const hintsCount = Math.min(this.filteredHints.length, 10);
    const totalItems = tablesCount + suggestionsCount + hintsCount;
    
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
          if (this.selectedIndex < tablesCount) {
            this.selectTable(this.filteredTables[this.selectedIndex]);
          } else if (this.selectedIndex < tablesCount + suggestionsCount) {
            this.selectSuggestion(this.suggestions[this.selectedIndex - tablesCount]);
          } else {
            const hintIndex = this.selectedIndex - tablesCount - suggestionsCount;
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
    this.loadDatabaseSchema();
    this.apiService.initializeHints().subscribe({
      next: () => {
        this.toastr.success('Schema refreshed', 'Success');
        this.loadHints();
      },
      error: (err) => {
        this.toastr.error('Failed to refresh schema', 'Error');
      }
    });
  }
  
  selectTable(table: any) {
    const query = `Show all data from ${table.name}`;
    this.hintSelected.emit({
      id: 0,
      example: query,
      sql_pattern: `SELECT * FROM ${table.name}`,
      keywords: [table.name.toLowerCase(), 'select', 'all'],
      tags: ['table', 'query'],
      category: 'Tables',
      popularity: 0
    });
    this.toastr.success(`Using table: ${table.name}`, 'Table Selected');
    this.showResults = false;
  }
  
  selectCountQuery(table: any) {
    const query = `count ${table.name.toLowerCase()}`;
    this.suggestionUsed.emit({
      type: 'pattern',
      category: 'count',
      suggestion: query,
      sql_pattern: `SELECT COUNT(*) FROM ${table.name}`,
      score: 100
    });
    this.toastr.success(`Count query for ${table.name} added`, 'Query Suggestion');
    this.showResults = false;
  }
  
  useTableQuery(table: any, event: Event) {
    event.stopPropagation();
    const query = `SELECT * FROM ${table.name}`;
    navigator.clipboard.writeText(query).then(() => {
      this.toastr.success('Query copied to clipboard', 'Copied');
    });
  }
  
  getTableColumnNames(table: any): string[] {
    if (!table.columns) return [];
    return table.columns.map((c: any) => c.name);
  }
  
  getTotalColumns(): number {
    if (!this.tables) return 0;
    return this.tables.reduce((sum, table) => sum + (table.columns?.length || 0), 0);
  }
}