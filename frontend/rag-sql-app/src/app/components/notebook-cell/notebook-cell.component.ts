import { Component, Input, Output, EventEmitter, ViewChild, ElementRef, OnChanges, OnInit } from '@angular/core';
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
            
            <!-- Execution Time and Retry Info -->
            <div class="flex items-center gap-2 text-xs text-gray-500 mb-2">
              <span *ngIf="cell.execution_time">
                Executed in {{ cell.execution_time }}ms
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
                style="width: 100%; height: 500px;"
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
  `,
  styles: []
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
    filter: true,
    resizable: true,
    minWidth: 100,
    floatingFilter: false
  };
  gridOptions: GridOptions = {
    theme: themeQuartz,
    enableCellTextSelection: true,
    ensureDomOrder: true,
    rowSelection: {
      mode: 'multiRow',
      enableClickSelection: false,
      enableSelectionWithoutKeys: true
    },
    animateRows: true,
    pagination: true,
    paginationPageSize: 25,
    paginationPageSizeSelector: [10, 25, 50, 100],
    suppressMenuHide: true,
    domLayout: 'normal',
    rowHeight: 40,
    headerHeight: 45
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
        this.columnDefs = this.cell.result_data.columns.map((col: string) => ({
          field: col,
          headerName: col,
          filter: 'agTextColumnFilter',
          floatingFilter: true,
          cellRenderer: (params: any) => {
            return this.formatCellValueWithLookup(params.data, col);
          }
        }));
        
        // Refresh grid if it's already initialized
        if (this.gridApi) {
          this.gridApi.setGridOption('columnDefs', this.columnDefs);
          this.gridApi.setGridOption('rowData', this.cell.result_data.data);
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
  
  formatCellValue(value: any): string {
    if (value === null || value === undefined) {
      return 'NULL';
    }
    if (typeof value === 'object') {
      return JSON.stringify(value);
    }
    return String(value);
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
    
    return this.formatCellValue(value);
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
    
    // Auto-size columns to fit content
    setTimeout(() => {
      this.gridApi.sizeColumnsToFit();
    }, 100);
    
    // Set initial page size from preferences
    if (this.pageSize) {
      this.gridApi.setGridOption('paginationPageSize', this.pageSize);
    }
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