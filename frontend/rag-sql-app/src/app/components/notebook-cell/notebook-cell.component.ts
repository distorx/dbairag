import { Component, Input, Output, EventEmitter, ViewChild, ElementRef, OnChanges, OnInit, ViewEncapsulation } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ToastrService } from 'ngx-toastr';
import { Cell } from '../../services/notebook.service';
import { saveAs } from 'file-saver';
import { QueryAutocompleteComponent } from '../query-autocomplete/query-autocomplete.component';
import { StorageService } from '../../services/storage.service';
import { AgGridAngular } from 'ag-grid-angular';
import { ColDef, GridOptions, GridApi, GridReadyEvent, ModuleRegistry, AllCommunityModule, themeQuartz } from 'ag-grid-community';

// Register AG-Grid modules
ModuleRegistry.registerModules([AllCommunityModule]);

@Component({
  selector: 'app-notebook-cell',
  standalone: true,
  imports: [CommonModule, FormsModule, QueryAutocompleteComponent, AgGridAngular],
  encapsulation: ViewEncapsulation.None,
  styles: [`
    /* Modern AG-Grid UI Enhancement */
    .notebook-cell-grid.ag-theme-quartz {
      /* Modern color palette */
      --ag-header-background-color: #6366f1;
      --ag-header-foreground-color: #ffffff;
      --ag-header-text-color: #ffffff;
      --ag-odd-row-background-color: #ffffff;
      --ag-row-hover-color: #f0f9ff;
      --ag-selected-row-background-color: #e0e7ff;
      --ag-border-color: #e2e8f0;
      --ag-font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }
    
    /* Beautiful gradient header with subtle animation */
    .notebook-cell-grid .ag-header {
      background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #a855f7 100%) !important;
      border-bottom: 2px solid #5b21b6 !important;
      box-shadow: 0 2px 4px rgba(99, 102, 241, 0.2) !important;
    }
    
    /* Enhanced header cells */
    .notebook-cell-grid .ag-header-cell {
      border-right: 1px solid rgba(255, 255, 255, 0.15) !important;
      transition: background-color 0.2s ease !important;
    }
    
    .notebook-cell-grid .ag-header-cell:hover {
      background-color: rgba(255, 255, 255, 0.1) !important;
    }
    
    /* Header text styling */
    .notebook-cell-grid .ag-header-cell,
    .notebook-cell-grid .ag-header-cell-label,
    .notebook-cell-grid .ag-header-cell-text {
      color: #ffffff !important;
      font-weight: 600 !important;
      font-size: 0.875rem !important;
      letter-spacing: 0.025em !important;
      text-transform: uppercase !important;
    }
    
    /* Sort indicators */
    .notebook-cell-grid .ag-header-cell-sorted-asc .ag-sort-ascending-icon,
    .notebook-cell-grid .ag-header-cell-sorted-desc .ag-sort-descending-icon {
      color: #fbbf24 !important;
    }
    
    /* Row styling with subtle backgrounds */
    .notebook-cell-grid .ag-row {
      transition: background-color 0.15s ease, box-shadow 0.15s ease !important;
      border-bottom: 1px solid #f1f5f9 !important;
    }
    
    .notebook-cell-grid .ag-row-even {
      background-color: #fafbfc !important;
    }
    
    .notebook-cell-grid .ag-row-odd {
      background-color: #ffffff !important;
    }
    
    /* Enhanced hover effect - smooth without movement */
    .notebook-cell-grid .ag-row:hover {
      background: linear-gradient(90deg, #f0f9ff 0%, #e0f2fe 100%) !important;
      box-shadow: inset 3px 0 0 #6366f1, 0 1px 3px rgba(99, 102, 241, 0.08) !important;
    }
    
    /* Selected row */
    .notebook-cell-grid .ag-row-selected {
      background: linear-gradient(90deg, #e0e7ff 0%, #c7d2fe 100%) !important;
      font-weight: 500 !important;
    }
    
    /* Cell styling */
    .notebook-cell-grid .ag-cell {
      padding: 0 16px !important;
      font-size: 0.875rem !important;
      color: #1e293b !important;
      border-right: 1px solid #f1f5f9 !important;
    }
    
    /* Special cell types */
    .notebook-cell-grid .ag-cell[col-id*="id"],
    .notebook-cell-grid .ag-cell[col-id*="Id"] {
      font-family: 'Monaco', 'Courier New', monospace !important;
      color: #6366f1 !important;
      font-size: 0.813rem !important;
    }
    
    .notebook-cell-grid .ag-cell[col-id*="date"],
    .notebook-cell-grid .ag-cell[col-id*="Date"] {
      color: #7c3aed !important;
      font-weight: 500 !important;
    }
    
    .notebook-cell-grid .ag-cell[col-id*="email"],
    .notebook-cell-grid .ag-cell[col-id*="Email"] {
      color: #0891b2 !important;
    }
    
    /* Grid wrapper with modern card design */
    .notebook-cell-grid .ag-root-wrapper {
      border: 1px solid #e2e8f0;
      border-radius: 0.75rem;
      box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
      overflow: hidden;
    }
    
    /* Pagination styling */
    .notebook-cell-grid .ag-paging-panel {
      background: linear-gradient(to right, #f8fafc, #f1f5f9) !important;
      border-top: 2px solid #e2e8f0 !important;
      padding: 12px 16px !important;
    }
    
    /* Scrollbar styling */
    .notebook-cell-grid .ag-body-viewport::-webkit-scrollbar,
    .notebook-cell-grid .ag-body-horizontal-scroll::-webkit-scrollbar {
      height: 8px;
      width: 8px;
    }
    
    .notebook-cell-grid .ag-body-viewport::-webkit-scrollbar-track,
    .notebook-cell-grid .ag-body-horizontal-scroll::-webkit-scrollbar-track {
      background: #f1f5f9;
      border-radius: 4px;
    }
    
    .notebook-cell-grid .ag-body-viewport::-webkit-scrollbar-thumb,
    .notebook-cell-grid .ag-body-horizontal-scroll::-webkit-scrollbar-thumb {
      background: #cbd5e1;
      border-radius: 4px;
    }
    
    .notebook-cell-grid .ag-body-viewport::-webkit-scrollbar-thumb:hover,
    .notebook-cell-grid .ag-body-horizontal-scroll::-webkit-scrollbar-thumb:hover {
      background: #6366f1;
    }
  `],
  template: `
    <div class="mb-2 bg-white rounded shadow-sm border border-gray-200">
      <!-- Prompt Cell -->
      <div *ngIf="cell.type === 'prompt'" class="p-3">
        <div class="flex items-start gap-2">
          <span class="text-gray-500 font-mono text-sm mt-2">[{{ cellIndex + 1 }}]</span>
          <app-query-autocomplete
            class="flex-1"
            [(value)]="cell.content"
            [placeholder]="'Enter your query in natural language...'"
            [rows]="3"
            (suggestionSelected)="onSuggestionSelected($event)">
          </app-query-autocomplete>
          <div class="flex flex-col gap-2">
            <button 
              (click)="execute.emit()"
              [disabled]="!cell.content || (cell.isExecuting || false)"
              class="bg-green-500 text-white px-3 py-1.5 rounded hover:bg-green-600 disabled:opacity-50 text-sm">
              {{ cell.isExecuting ? 'Running...' : 'Run' }}
            </button>
            <button 
              (click)="delete.emit()"
              [disabled]="cell.isExecuting || false"
              class="bg-gray-500 text-white px-3 py-1.5 rounded hover:bg-gray-600 disabled:opacity-50 text-sm">
              Delete
            </button>
          </div>
        </div>
      </div>
      
      <!-- Response Cell -->
      <div *ngIf="cell.type === 'response'" class="p-3">
        <div class="flex items-start gap-2">
          <span class="text-gray-500 font-mono text-sm">Out[{{ cellIndex }}]</span>
          
          <div class="flex-1">
            <!-- SQL Query Display -->
            <div *ngIf="cell.content" class="mb-2">
              <div class="text-xs text-gray-600 mb-1">Generated SQL:</div>
              <pre class="bg-gray-100 p-2 rounded text-xs whitespace-pre-wrap break-words font-mono">{{ cell.content }}</pre>
            </div>
            
            <!-- Execution Time, Pattern Method, and Retry Info -->
            <div class="flex items-center gap-2 text-xs text-gray-500 mb-2">
              <span *ngIf="cell.execution_time">
                Executed in {{ cell.execution_time }}ms
              </span>
              <span *ngIf="cell.metadata?.method" 
                    [class]="getMethodBadgeClass(cell.metadata.method)"
                    class="px-2 py-1 rounded text-xs">
                {{ getMethodLabel(cell.metadata.method) }}
              </span>
              <span *ngIf="hasRetryInfo()" 
                    class="bg-blue-100 text-blue-700 px-2 py-1 rounded text-xs">
                {{ getRetryAttempts() }} {{ getRetryAttempts() === 1 ? 'attempt' : 'attempts' }}
              </span>
              <button *ngIf="hasRetryInfo()"
                      (click)="toggleRetryDetails()"
                      class="text-blue-600 hover:text-blue-800 text-xs underline">
                {{ showRetryDetails ? 'Hide' : 'Show' }} retry details
              </button>
            </div>
            
            <!-- Retry Details Panel -->
            <div *ngIf="showRetryDetails && hasRetryInfo()" 
                 class="mb-3 bg-blue-50 border border-blue-200 rounded p-3">
              <h4 class="text-xs font-semibold text-blue-800 mb-2">
                🔄 Retry Analysis - {{ getRetryAttempts() }} Total Attempts
              </h4>
              <div class="space-y-3">
                <div *ngFor="let attempt of getRetryLog(); let i = index" 
                     class="flex items-start gap-3 text-sm p-3 rounded border"
                     [class.bg-white]="attempt.status === 'success'"
                     [class.bg-gray-50]="attempt.status === 'failed'"
                     [class.border-green-200]="attempt.status === 'success'"
                     [class.border-gray-300]="attempt.status === 'failed'">
                  
                  <!-- Status Icon -->
                  <div class="flex-shrink-0 mt-0.5">
                    <span *ngIf="attempt.status === 'success'" class="text-green-500 text-lg">✓</span>
                    <span *ngIf="attempt.status === 'failed'" class="text-gray-500 text-lg">✗</span>
                  </div>
                  
                  <!-- Attempt Details -->
                  <div class="flex-1">
                    <div class="flex items-center gap-2 mb-1">
                      <span class="font-medium text-gray-900">Attempt {{ attempt.attempt }}</span>
                      <span class="text-xs px-2 py-1 rounded font-medium"
                            [class.bg-green-100]="attempt.status === 'success'"
                            [class.text-green-700]="attempt.status === 'success'"
                            [class.bg-gray-100]="attempt.status === 'failed'"
                            [class.text-gray-700]="attempt.status === 'failed'">
                        {{ attempt.status | uppercase }}
                      </span>
                      <span *ngIf="attempt.error_type" 
                            class="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded">
                        {{ formatErrorType(attempt.error_type) }}
                      </span>
                    </div>
                    
                    <div *ngIf="attempt.error_message" class="text-gray-700 text-xs mb-2 font-mono bg-gray-50 p-2 rounded">
                      {{ attempt.error_message }}
                    </div>
                    
                    <div class="flex items-center gap-4 text-xs text-gray-600">
                      <span class="flex items-center gap-1">
                        ⏱️ {{ attempt.execution_time_ms }}ms
                      </span>
                      <span *ngIf="attempt.metadata_refreshed" class="text-blue-700 flex items-center gap-1">
                        🔄 DB metadata refreshed
                      </span>
                      <span *ngIf="attempt.refresh_time_ms" class="text-blue-600">
                        ({{ attempt.refresh_time_ms }}ms)
                      </span>
                      <span *ngIf="attempt.next_retry_delay_s" class="text-orange-700 flex items-center gap-1">
                        ⏳ Retry in {{ attempt.next_retry_delay_s }}s
                      </span>
                    </div>
                    
                    <div *ngIf="attempt.message" class="text-xs text-gray-700 mt-2 italic">
                      {{ attempt.message }}
                    </div>
                  </div>
                </div>
              </div>
              
              <!-- Summary -->
              <div class="mt-4 pt-3 border-t border-blue-200 text-xs text-blue-700">
                <div class="grid grid-cols-2 gap-4">
                  <div>
                    <span class="font-medium">Total Time:</span> 
                    {{ getTotalRetryTime() }}ms
                  </div>
                  <div>
                    <span class="font-medium">Metadata Refreshes:</span>
                    {{ getMetadataRefreshCount() }}
                  </div>
                </div>
              </div>
            </div>
            
            <!-- Error Display -->
            <div *ngIf="cell.result_type === 'error'" class="bg-gray-50 border border-gray-300 rounded p-2">
              <div class="text-gray-800 mb-2 text-sm">
                {{ cell.result_data?.error || cell.result_data }}
              </div>
              
              <!-- Table Suggestions -->
              <div *ngIf="hasTableSuggestions()" class="mt-4 bg-blue-50 border border-blue-200 rounded-lg p-4">
                <h4 class="text-sm font-semibold text-blue-800 mb-3 flex items-center">
                  💡 Table Suggestions
                </h4>
                
                <!-- Ready-to-run suggestions -->
                <div *ngIf="cell.result_data.suggested_queries?.length > 0" class="mb-4">
                  <p class="text-sm text-blue-700 mb-2 font-medium">🔧 Ready-to-run suggestions:</p>
                  <div class="space-y-2">
                    <div *ngFor="let suggestion of cell.result_data.suggested_queries; let i = index"
                         class="bg-white border border-blue-200 rounded p-3">
                      <div class="flex justify-between items-start">
                        <div class="flex-1">
                          <p class="text-sm text-blue-800 font-medium">{{ suggestion.description }}</p>
                          <div class="mt-2 bg-gray-100 p-2 rounded text-xs font-mono whitespace-pre-wrap break-words">
                            {{ suggestion.query }}
                          </div>
                          <div class="mt-1 text-xs text-gray-600">
                            Confidence: {{ (suggestion.confidence * 100) | number:'1.0-0' }}%
                          </div>
                        </div>
                        <button 
                          (click)="executeSuggestedQuery(suggestion.query)"
                          class="ml-2 bg-green-500 text-white px-2 py-1 rounded text-xs hover:bg-green-600 flex items-center gap-1">
                          ▶️ Run
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
                
                <!-- Detailed suggestions by table -->
                <div *ngIf="getTableSuggestionEntries().length > 0" class="mt-4">
                  <p class="text-sm text-blue-700 mb-2 font-medium">📋 Detailed suggestions:</p>
                  <div class="space-y-3">
                    <div *ngFor="let entry of getTableSuggestionEntries()" class="bg-white border border-blue-200 rounded p-3">
                      <p class="text-sm font-medium text-blue-800">Instead of "{{ entry.missingTable }}", try:</p>
                      <div class="mt-2 space-y-1">
                        <div *ngFor="let suggestion of entry.suggestions" 
                             class="flex items-center justify-between text-sm">
                          <div class="flex items-center gap-2">
                            <span class="font-mono bg-gray-100 px-2 py-1 rounded text-xs">{{ suggestion.table_name }}</span>
                            <span class="text-gray-600">- {{ suggestion.reason }}</span>
                            <span class="text-xs text-gray-500">({{ (suggestion.similarity * 100) | number:'1.0-0' }}% match)</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
                
                <!-- Field Insights -->
                <div *ngIf="hasFieldInsights()" class="mt-4">
                  <p class="text-sm text-blue-700 mb-2 font-medium">🏷️ Available Data Insights:</p>
                  <div class="space-y-3">
                    <div *ngFor="let insight of getFieldInsights()" class="bg-white border border-blue-200 rounded p-3">
                      <div class="flex items-center gap-2 mb-2">
                        <span class="font-mono bg-blue-100 px-2 py-1 rounded text-xs font-medium">{{ insight.table_name }}</span>
                        <span *ngIf="insight.entity_type" class="bg-green-100 text-green-700 px-2 py-1 rounded text-xs">{{ insight.entity_type }}</span>
                      </div>
                      <div class="text-xs text-gray-600 mb-2">
                        {{ insight.field_count }} fields available
                      </div>
                      <div class="flex flex-wrap gap-1 mb-2">
                        <span *ngFor="let domain of insight.available_data_domains" 
                              class="bg-gray-100 text-gray-700 px-2 py-1 rounded text-xs">{{ domain }}</span>
                      </div>
                      <div class="text-xs text-gray-600">
                        <span class="font-medium">Example fields:</span> 
                        {{ insight.example_fields.join(', ') }}
                      </div>
                    </div>
                  </div>
                </div>
                
                <!-- Data Availability Summary -->
                <div *ngIf="hasDataAvailability()" class="mt-4">
                  <p class="text-sm text-blue-700 mb-2 font-medium">📊 What you can query:</p>
                  <div class="bg-white border border-blue-200 rounded p-3">
                    <div *ngFor="let entity of getEntitySummary()" class="mb-2 last:mb-0">
                      <div class="flex items-center gap-2 mb-1">
                        <span class="font-medium text-blue-800 text-sm">{{ entity.type | titlecase }}:</span>
                        <span class="text-xs text-gray-600">{{ entity.tables.length }} table(s)</span>
                      </div>
                      <div class="text-xs text-gray-600 ml-2">
                        {{ entity.tables.join(', ') }}
                      </div>
                    </div>
                  </div>
                </div>
                
                <!-- Query Capabilities -->
                <div *ngIf="hasQueryCapabilities()" class="mt-4">
                  <p class="text-sm text-blue-700 mb-2 font-medium">💡 Suggested queries you can try:</p>
                  <div class="space-y-2">
                    <div *ngFor="let capability of getQueryCapabilities()" 
                         class="bg-white border border-blue-200 rounded p-2">
                      <div class="text-sm font-medium text-blue-800">{{ capability.description }}</div>
                      <div class="text-xs text-gray-600 italic mt-1">"{{ capability.example }}"</div>
                      <div class="text-xs text-blue-600 mt-1">Confidence: {{ (capability.confidence * 100) | number:'1.0-0' }}%</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            <!-- Text Result -->
            <div *ngIf="cell.result_type === 'text'" class="bg-gray-50 p-3 rounded">
              {{ cell.result_data }}
            </div>
            
            <!-- Table Result -->
            <div *ngIf="cell.result_type === 'table' && cell.result_data">
              <div class="mb-2 flex justify-between items-center">
                <span class="text-sm text-gray-600 font-medium">
                  Total: {{ getTotalRows() }} rows
                </span>
                <button 
                  (click)="exportToCSV()"
                  class="bg-blue-500 text-white px-3 py-1 rounded text-sm hover:bg-blue-600">
                  Export CSV
                </button>
              </div>
              
              <!-- AG-Grid Table -->
              <ag-grid-angular
                style="width: 100%; height: 500px; overflow-x: auto;"
                class="ag-theme-quartz notebook-cell-grid"
                [rowData]="cell.result_data.data"
                [columnDefs]="columnDefs"
                [defaultColDef]="defaultColDef"
                [gridOptions]="gridOptions"
                (gridReady)="onGridReady($event)">
              </ag-grid-angular>
            </div>
          </div>
          
          <button 
            (click)="delete.emit()"
            class="text-gray-500 hover:text-gray-700">
            ×
          </button>
        </div>
      </div>
    </div>
  `
})
export class NotebookCellComponent implements OnChanges, OnInit {
  @Input() cell!: Cell;
  @Input() cellIndex: number = 0;
  @Output() execute = new EventEmitter<void>();
  @Output() delete = new EventEmitter<void>();
  @Output() update = new EventEmitter<Partial<Cell>>();
  @Output() executeSuggestion = new EventEmitter<string>();
  
  @ViewChild('promptInput') promptInput?: ElementRef<HTMLTextAreaElement>;
  
  // Pagination properties
  currentPage = 1;
  pageSize = 25;
  pageSizeOptions = [10, 25, 50, 100];
  showRetryDetails = false;
  
  // AG-Grid properties
  columnDefs: ColDef[] = [];
  defaultColDef: ColDef = {
    sortable: true,
    filter: false,
    resizable: true,
    minWidth: 80,
    maxWidth: 500,
    floatingFilter: false,
    wrapText: false,
    autoHeight: false
  };
  gridOptions: GridOptions = {
    theme: themeQuartz,
    enableCellTextSelection: true,
    ensureDomOrder: true,
    animateRows: true,
    pagination: true,
    paginationPageSize: 25,
    paginationPageSizeSelector: [10, 25, 50, 100],
    suppressMenuHide: true,
    domLayout: 'normal',
    rowHeight: 40,
    headerHeight: 45,
    autoSizeStrategy: {
      type: 'fitCellContents',
      defaultMinWidth: 80,
      defaultMaxWidth: 400
    }
  };
  private gridApi!: GridApi;
  
  constructor(
    private toastr: ToastrService,
    private storageService: StorageService
  ) {}
  
  ngOnInit() {
    // Load user preferences
    const preferences = this.storageService.getPreferences();
    if (preferences && preferences.pageSize) {
      this.pageSize = preferences.pageSize;
    }
  }
  
  ngOnChanges() {
    // Reset pagination when result data changes
    if (this.cell.result_data) {
      this.currentPage = 1;
      
      // Set up AG-Grid column definitions
      if (this.cell.result_data.columns) {
        this.columnDefs = this.cell.result_data.columns.map((col: string) => {
          // Check if this column contains dates
          const isDateColumn = this.isDateColumn(col, this.cell.result_data.data);
          
          // Convert field name to readable header
          const headerName = this.formatHeaderName(col);
          
          // Calculate appropriate width based on header name and sample data
          const headerLength = headerName.length * 8; // Approximate pixel width per character
          let maxDataLength = 100; // Default minimum
          
          // For date columns, use a standard width
          if (isDateColumn) {
            maxDataLength = 150; // Standard width for date columns
          } else {
            // Sample first 10 rows to estimate content width
            if (this.cell.result_data.data && this.cell.result_data.data.length > 0) {
              const sampleSize = Math.min(10, this.cell.result_data.data.length);
              for (let i = 0; i < sampleSize; i++) {
                const value = String(this.cell.result_data.data[i][col] || '');
                maxDataLength = Math.max(maxDataLength, value.length * 7);
              }
            }
          }
          
          // Set appropriate width with reasonable limits
          const suggestedWidth = Math.max(headerLength + 40, Math.min(maxDataLength, 300));
          
          return {
            field: col,
            headerName: headerName,
            width: suggestedWidth,
            minWidth: 80,
            maxWidth: 400,
            cellRenderer: (params: any) => {
              return this.formatCellValueWithLookup(params.data, col);
            }
          };
        });
        
        // Refresh grid if it's already initialized
        if (this.gridApi) {
          this.gridApi.setGridOption('columnDefs', this.columnDefs);
          this.gridApi.setGridOption('rowData', this.cell.result_data.data);
          
          // Apply styles after data update
          setTimeout(() => {
            this.applyGridStyles();
          }, 100);
        }
      }
    }
  }
  
  onKeyDown(event: KeyboardEvent) {
    // Shift+Enter to execute
    if (event.shiftKey && event.key === 'Enter') {
      event.preventDefault();
      if (this.cell.content && !this.cell.isExecuting) {
        this.execute.emit();
      }
    }
  }
  
  onSuggestionSelected(suggestion: any) {
    // The value is already updated through two-way binding
    // You can add additional logic here if needed
    console.log('Suggestion selected:', suggestion);
  }
  
  getDisplayRows() {
    if (!this.cell.result_data?.data) return [];
    
    const startIndex = (this.currentPage - 1) * this.pageSize;
    const endIndex = startIndex + this.pageSize;
    
    return this.cell.result_data.data.slice(startIndex, endIndex);
  }
  
  getTotalPages(): number {
    if (!this.cell.result_data?.data) return 0;
    return Math.ceil(this.cell.result_data.data.length / this.pageSize);
  }
  
  getTotalRows(): number {
    return this.cell.result_data?.data?.length || 0;
  }
  
  getPageNumbers(): number[] {
    const totalPages = this.getTotalPages();
    const maxPagesToShow = 5;
    const pages: number[] = [];
    
    if (totalPages <= maxPagesToShow) {
      for (let i = 1; i <= totalPages; i++) {
        pages.push(i);
      }
    } else {
      // Show first page, last page, current page and neighbors
      const startPage = Math.max(1, this.currentPage - 2);
      const endPage = Math.min(totalPages, this.currentPage + 2);
      
      for (let i = startPage; i <= endPage; i++) {
        pages.push(i);
      }
      
      // Add first page if not included
      if (startPage > 1) {
        pages.unshift(1);
        if (startPage > 2) {
          pages.splice(1, 0, -1); // -1 represents ellipsis
        }
      }
      
      // Add last page if not included
      if (endPage < totalPages) {
        if (endPage < totalPages - 1) {
          pages.push(-1); // -1 represents ellipsis
        }
        pages.push(totalPages);
      }
    }
    
    return pages;
  }
  
  goToPage(page: number) {
    if (page > 0 && page <= this.getTotalPages()) {
      this.currentPage = page;
    }
  }
  
  nextPage() {
    if (this.currentPage < this.getTotalPages()) {
      this.currentPage++;
    }
  }
  
  previousPage() {
    if (this.currentPage > 1) {
      this.currentPage--;
    }
  }
  
  onPageSizeChange(newSize: number) {
    this.pageSize = newSize;
    this.currentPage = 1;
    
    // Update AG-Grid page size
    if (this.gridApi) {
      this.gridOptions.paginationPageSize = newSize;
      this.gridApi.setGridOption('paginationPageSize', newSize);
    }
    
    // Save user preference
    const preferences = this.storageService.getPreferences();
    preferences.pageSize = newSize;
    this.storageService.savePreferences(preferences);
  }
  
  getDisplayRange(): string {
    const start = (this.currentPage - 1) * this.pageSize + 1;
    const end = Math.min(this.currentPage * this.pageSize, this.getTotalRows());
    return `${start}-${end}`;
  }
  
  formatCellValue(value: any, columnName?: string): string {
    if (value === null || value === undefined) {
      return 'NULL';
    }
    
    // Check if it's a boolean/bit field (0 or 1)
    if ((value === 0 || value === 1 || value === true || value === false) && 
        columnName && this.isBooleanColumn(columnName)) {
      return value === 1 || value === true ? 'true' : 'false';
    }
    
    // Check if it's a date string
    if (typeof value === 'string' && this.isDateString(value)) {
      return this.formatDate(value, columnName);
    }
    
    if (typeof value === 'object') {
      return JSON.stringify(value);
    }
    return String(value);
  }
  
  isDateString(value: string): boolean {
    // Check for common date formats
    // ISO format: 2024-01-15T10:30:00
    // SQL Date: 2024-01-15
    // SQL DateTime: 2024-01-15 10:30:00
    const datePatterns = [
      /^\d{4}-\d{2}-\d{2}$/,  // YYYY-MM-DD
      /^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}/,  // YYYY-MM-DD HH:MM:SS or ISO
      /^\d{2}\/\d{2}\/\d{4}$/,  // MM/DD/YYYY
    ];
    
    if (datePatterns.some(pattern => pattern.test(value))) {
      const date = new Date(value);
      return !isNaN(date.getTime());
    }
    return false;
  }
  
  formatDate(dateString: string, columnName?: string): string {
    const date = new Date(dateString);
    
    // Check if this is a date-only field based on column name
    const dateOnlyColumns = ['dob', 'birth', 'birthday', 'hire', 'start', 'end', 'expire', 'due'];
    const isDateOnlyColumn = columnName && dateOnlyColumns.some(term => 
      columnName.toLowerCase().includes(term)
    );
    
    // Check if it has a meaningful time component (not midnight)
    const hasTime = dateString.includes('T') || dateString.includes(':');
    const hours = date.getHours();
    const minutes = date.getMinutes();
    const seconds = date.getSeconds();
    const isMidnight = hours === 0 && minutes === 0 && seconds === 0;
    
    // Show date only if: it's a date-only column, or has no time, or time is midnight
    if (isDateOnlyColumn || !hasTime || isMidnight) {
      // Format as: Jan 15, 2024
      return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric'
      });
    } else {
      // Format as: Jan 15, 2024 10:30 AM
      return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: 'numeric',
        minute: '2-digit',
        hour12: true
      });
    }
  }
  
  formatHeaderName(fieldName: string): string {
    // Handle common SQL naming patterns and convert to readable format
    
    // Handle snake_case (e.g., first_name -> First Name)
    if (fieldName.includes('_')) {
      return fieldName
        .split('_')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
        .join(' ');
    }
    
    // Handle PascalCase and camelCase (e.g., FirstName -> First Name, firstName -> First Name)
    const result = fieldName.replace(/([a-z])([A-Z])/g, '$1 $2')
                           .replace(/([A-Z])([A-Z][a-z])/g, '$1 $2');
    
    // Capitalize first letter
    return result.charAt(0).toUpperCase() + result.slice(1);
  }
  
  isDateColumn(columnName: string, data: any[]): boolean {
    // Check if column name suggests it's a date
    const dateColumnNames = ['date', 'created', 'updated', 'modified', 'timestamp', 'time', 'dob', 'birth', 'expire', 'start', 'end'];
    const colLower = columnName.toLowerCase();
    
    if (dateColumnNames.some(name => colLower.includes(name))) {
      return true;
    }
    
    // Check actual data to see if values are dates
    if (data && data.length > 0) {
      // Sample first few non-null values
      let sampledCount = 0;
      let dateCount = 0;
      
      for (let i = 0; i < Math.min(5, data.length); i++) {
        const value = data[i][columnName];
        if (value !== null && value !== undefined) {
          sampledCount++;
          if (typeof value === 'string' && this.isDateString(value)) {
            dateCount++;
          }
        }
      }
      
      // If most sampled values are dates, consider it a date column
      return sampledCount > 0 && dateCount / sampledCount >= 0.5;
    }
    
    return false;
  }
  
  isBooleanColumn(columnName: string): boolean {
    // Check if column name suggests it's a boolean/bit field
    const colLower = columnName.toLowerCase();
    
    // Common boolean column patterns
    const booleanPatterns = [
      /^is[A-Z_]/i,           // IsActive, IsDeleted, Is_Valid
      /^has[A-Z_]/i,          // HasAccess, HasPermission
      /^can[A-Z_]/i,          // CanEdit, CanDelete
      /^should[A-Z_]/i,       // ShouldNotify
      /^allow[A-Z_]/i,        // AllowLogin
      /^enable[A-Z_]/i,       // EnableNotifications
      /_flag$/i,              // active_flag, deleted_flag
      /^flag_/i,              // flag_active
      /active|enabled|deleted|approved|completed|verified|locked|published|visible|hidden/i
    ];
    
    return booleanPatterns.some(pattern => pattern.test(colLower));
  }
  
  formatCellValueWithLookup(row: any, col: string): string {
    const value = row[col];
    
    // If column is cityid or city_id, try to show city name if available
    if ((col.toLowerCase() === 'cityid' || col.toLowerCase() === 'city_id')) {
      // Check if there's a corresponding city_name or cityname column in the same row
      const cityName = row['city_name'] || row['cityname'] || row['CityName'] || row['CITY_NAME'];
      if (cityName) {
        return `${value} (${cityName})`;
      }
      // You could also maintain a city lookup map here if needed
      // For now, just return the ID
    }
    
    // Add more lookup logic for other ID fields as needed
    // e.g., userid -> username, productid -> product_name, etc.
    
    return this.formatCellValue(value, col);
  }
  
  exportToCSV() {
    if (this.gridApi) {
      // Use AG-Grid's built-in CSV export
      this.gridApi.exportDataAsCsv({
        fileName: `query_result_${new Date().toISOString().replace(/[:.]/g, '-')}.csv`,
        allColumns: true
      });
      this.toastr.success('Data exported to CSV', 'Export Successful');
    } else if (this.cell.result_data?.columns && this.cell.result_data?.data) {
      // Fallback to manual CSV generation
      const columns = this.cell.result_data.columns;
      const data = this.cell.result_data.data;
      
      const csvRows = [];
      csvRows.push(columns.map((col: string) => `"${col}"`).join(','));
      
      for (const row of data) {
        const values = columns.map((col: string) => {
          const value = row[col];
          if (value === null || value === undefined) {
            return '""';
          }
          return `"${String(value).replace(/"/g, '""')}"`;
        });
        csvRows.push(values.join(','));
      }
      
      const csvContent = csvRows.join('\n');
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8' });
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
      const filename = `query_result_${timestamp}.csv`;
      saveAs(blob, filename);
      
      this.toastr.success(`Exported ${data.length} rows to ${filename}`, 'Export Successful');
    } else {
      this.toastr.warning('No data to export', 'Warning');
    }
  }
  
  onGridReady(params: GridReadyEvent) {
    this.gridApi = params.api;
    
    // Apply custom styles after grid is ready
    this.applyGridStyles();
    
    // Auto-size columns based on content, not container width
    setTimeout(() => {
      // Don't use sizeColumnsToFit() as it expands columns to fill width
      // Instead, let the column widths be determined by content
      // The autoSizeStrategy in gridOptions will handle this
      this.gridApi.autoSizeAllColumns(false);
      
      // Re-apply styles after sizing
      this.applyGridStyles();
    }, 100);
    
    // Set initial page size from preferences
    if (this.pageSize) {
      this.gridApi.setGridOption('paginationPageSize', this.pageSize);
    }
  }
  
  private applyGridStyles() {
    // Force apply styles to AG-Grid elements after grid creation
    setTimeout(() => {
      const gridElement = document.querySelector('.notebook-cell-grid');
      if (gridElement) {
        // Force repaint to ensure styles are applied
        (gridElement as HTMLElement).style.display = 'none';
        (gridElement as HTMLElement).offsetHeight; // Trigger reflow
        (gridElement as HTMLElement).style.display = '';
        
        // Also ensure the CSS variables are applied
        const gridWrapper = gridElement.querySelector('.ag-root-wrapper');
        if (gridWrapper) {
          (gridWrapper as HTMLElement).style.setProperty('--ag-header-background-color', '#667eea');
        }
      }
    }, 0);
  }
  
  // Retry information helper methods
  hasRetryInfo(): boolean {
    return this.cell.result_data && 
           typeof this.cell.result_data === 'object' && 
           this.cell.result_data.retry_info &&
           Array.isArray(this.cell.result_data.retry_info.retry_log) &&
           this.cell.result_data.retry_info.retry_log.length > 0;
  }
  
  getRetryAttempts(): number {
    if (!this.hasRetryInfo()) return 1;
    return this.cell.result_data.retry_info.attempts || 1;
  }
  
  getRetryLog(): any[] {
    if (!this.hasRetryInfo()) return [];
    return this.cell.result_data.retry_info.retry_log || [];
  }
  
  toggleRetryDetails(): void {
    this.showRetryDetails = !this.showRetryDetails;
  }
  
  formatErrorType(errorType: string): string {
    if (!errorType) return '';
    return errorType.replace(/_/g, ' ')
                   .split(' ')
                   .map(word => word.charAt(0).toUpperCase() + word.slice(1))
                   .join(' ');
  }
  
  getTotalRetryTime(): number {
    const retryLog = this.getRetryLog();
    return retryLog.reduce((total, attempt) => {
      return total + (attempt.execution_time_ms || 0) + (attempt.refresh_time_ms || 0);
    }, 0);
  }
  
  getMetadataRefreshCount(): number {
    const retryLog = this.getRetryLog();
    return retryLog.filter(attempt => attempt.metadata_refreshed).length;
  }
  
  // Pattern matching method helpers
  getMethodLabel(method: string): string {
    if (!method) return '';
    
    const methodLabels: { [key: string]: string } = {
      'pattern_match': '⚡ Pattern Match',
      'vocabulary_pattern': '📚 Vocabulary Pattern',
      'column_intelligence': '🧠 Column Intelligence',
      'dynamic_pattern': '🎯 Dynamic Pattern',
      'fallback_pattern': '🔄 Fallback Pattern',
      'llm_generation': '🤖 AI Generated',
      'raw_sql_passthrough': '📝 Raw SQL',
      'cached': '💾 Cached',
      'optimized': '⚙️ Optimized'
    };
    
    return methodLabels[method] || method;
  }
  
  getMethodBadgeClass(method: string): string {
    if (!method) return '';
    
    const methodClasses: { [key: string]: string } = {
      'pattern_match': 'bg-green-100 text-green-700',
      'vocabulary_pattern': 'bg-purple-100 text-purple-700',
      'column_intelligence': 'bg-indigo-100 text-indigo-700',
      'dynamic_pattern': 'bg-blue-100 text-blue-700',
      'fallback_pattern': 'bg-yellow-100 text-yellow-700',
      'llm_generation': 'bg-orange-100 text-orange-700',
      'raw_sql_passthrough': 'bg-gray-100 text-gray-700',
      'cached': 'bg-teal-100 text-teal-700',
      'optimized': 'bg-pink-100 text-pink-700'
    };
    
    return methodClasses[method] || 'bg-gray-100 text-gray-700';
  }
  
  // Table suggestion helper methods
  hasTableSuggestions(): boolean {
    return this.cell.result_data && 
           typeof this.cell.result_data === 'object' && 
           (this.cell.result_data.has_suggestions || 
            this.cell.result_data.suggested_queries?.length > 0 ||
            this.cell.result_data.suggestions);
  }
  
  getTableSuggestionEntries(): any[] {
    if (!this.hasTableSuggestions() || !this.cell.result_data.suggestions) {
      return [];
    }
    
    return Object.entries(this.cell.result_data.suggestions).map(([missingTable, suggestions]) => ({
      missingTable,
      suggestions
    }));
  }
  
  executeSuggestedQuery(query: string): void {
    // Emit the suggested query to be executed
    this.executeSuggestion.emit(query);
  }
  
  // Field insights helper methods
  hasFieldInsights(): boolean {
    return this.cell.result_data && 
           typeof this.cell.result_data === 'object' && 
           this.cell.result_data.field_insights &&
           Object.keys(this.cell.result_data.field_insights).length > 0;
  }
  
  getFieldInsights(): any[] {
    if (!this.hasFieldInsights()) {
      return [];
    }
    
    return Object.entries(this.cell.result_data.field_insights).map(([table_name, insight]: [string, any]) => ({
      table_name,
      entity_type: insight?.entity_type,
      primary_concept: insight?.primary_concept,
      available_data_domains: insight?.available_data_domains || [],
      field_count: insight?.field_count || 0,
      example_fields: insight?.example_fields || []
    }));
  }
  
  hasDataAvailability(): boolean {
    return this.cell.result_data && 
           typeof this.cell.result_data === 'object' && 
           this.cell.result_data.data_availability &&
           this.cell.result_data.data_availability.entities &&
           Object.keys(this.cell.result_data.data_availability.entities).length > 0;
  }
  
  getEntitySummary(): any[] {
    if (!this.hasDataAvailability()) {
      return [];
    }
    
    const entities = this.cell.result_data.data_availability.entities;
    return Object.entries(entities).map(([type, info]: [string, any]) => ({
      type,
      tables: Array.isArray(info) ? info.map((i: any) => i.table) : [info.table].filter(Boolean)
    }));
  }
  
  hasQueryCapabilities(): boolean {
    return this.cell.result_data && 
           typeof this.cell.result_data === 'object' && 
           this.cell.result_data.query_capabilities &&
           Array.isArray(this.cell.result_data.query_capabilities) &&
           this.cell.result_data.query_capabilities.length > 0;
  }
  
  getQueryCapabilities(): any[] {
    if (!this.hasQueryCapabilities()) {
      return [];
    }
    
    return this.cell.result_data.query_capabilities;
  }
}