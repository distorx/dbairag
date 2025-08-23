import { Component, Input, Output, EventEmitter, ViewChild, ElementRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ToastrService } from 'ngx-toastr';
import { Cell } from '../../services/notebook.service';
import { saveAs } from 'file-saver';
import { QueryAutocompleteComponent } from '../query-autocomplete/query-autocomplete.component';

@Component({
  selector: 'app-notebook-cell',
  standalone: true,
  imports: [CommonModule, FormsModule, QueryAutocompleteComponent],
  template: `
    <div class="mb-4 bg-white rounded-lg shadow-sm border border-gray-200">
      <!-- Prompt Cell -->
      <div *ngIf="cell.type === 'prompt'" class="p-4">
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
              class="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600 disabled:opacity-50">
              {{ cell.isExecuting ? 'Running...' : 'Run' }}
            </button>
            <button 
              (click)="delete.emit()"
              [disabled]="cell.isExecuting || false"
              class="bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600 disabled:opacity-50">
              Delete
            </button>
          </div>
        </div>
      </div>
      
      <!-- Response Cell -->
      <div *ngIf="cell.type === 'response'" class="p-4">
        <div class="flex items-start gap-2">
          <span class="text-gray-500 font-mono text-sm">Out[{{ cellIndex }}]</span>
          
          <div class="flex-1">
            <!-- SQL Query Display -->
            <div *ngIf="cell.content" class="mb-3">
              <div class="text-sm text-gray-600 mb-1">Generated SQL:</div>
              <pre class="bg-gray-100 p-2 rounded text-sm overflow-x-auto">{{ cell.content }}</pre>
            </div>
            
            <!-- Execution Time and Retry Info -->
            <div class="flex items-center gap-3 text-sm text-gray-500 mb-2">
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
                 class="mb-4 bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h4 class="text-sm font-semibold text-blue-800 mb-3">
                🔄 Retry Analysis - {{ getRetryAttempts() }} Total Attempts
              </h4>
              <div class="space-y-3">
                <div *ngFor="let attempt of getRetryLog(); let i = index" 
                     class="flex items-start gap-3 text-sm p-3 rounded border"
                     [class.bg-white]="attempt.status === 'success'"
                     [class.bg-red-50]="attempt.status === 'failed'"
                     [class.border-green-200]="attempt.status === 'success'"
                     [class.border-red-200]="attempt.status === 'failed'">
                  
                  <!-- Status Icon -->
                  <div class="flex-shrink-0 mt-0.5">
                    <span *ngIf="attempt.status === 'success'" class="text-green-500 text-lg">✓</span>
                    <span *ngIf="attempt.status === 'failed'" class="text-red-500 text-lg">✗</span>
                  </div>
                  
                  <!-- Attempt Details -->
                  <div class="flex-1">
                    <div class="flex items-center gap-2 mb-1">
                      <span class="font-medium text-gray-900">Attempt {{ attempt.attempt }}</span>
                      <span class="text-xs px-2 py-1 rounded font-medium"
                            [class.bg-green-100]="attempt.status === 'success'"
                            [class.text-green-700]="attempt.status === 'success'"
                            [class.bg-red-100]="attempt.status === 'failed'"
                            [class.text-red-700]="attempt.status === 'failed'">
                        {{ attempt.status | uppercase }}
                      </span>
                      <span *ngIf="attempt.error_type" 
                            class="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded">
                        {{ formatErrorType(attempt.error_type) }}
                      </span>
                    </div>
                    
                    <div *ngIf="attempt.error_message" class="text-red-700 text-xs mb-2 font-mono bg-red-50 p-2 rounded">
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
            <div *ngIf="cell.result_type === 'error'" class="bg-red-50 border border-red-200 rounded p-3">
              <div class="text-red-800 mb-3">
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
                          <div class="mt-2 bg-gray-100 p-2 rounded text-xs font-mono overflow-x-auto">
                            {{ suggestion.query }}
                          </div>
                          <div class="mt-1 text-xs text-gray-600">
                            Confidence: {{ (suggestion.confidence * 100) | number:'1.0-0' }}%
                          </div>
                        </div>
                        <button 
                          (click)="executeSuggestedQuery(suggestion.query)"
                          class="ml-3 bg-green-500 text-white px-3 py-1 rounded text-xs hover:bg-green-600 flex items-center gap-1">
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
                <span class="text-sm text-gray-600">
                  {{ cell.result_data.row_count || 0 }} rows
                </span>
                <button 
                  (click)="exportToCSV()"
                  class="bg-blue-500 text-white px-3 py-1 rounded text-sm hover:bg-blue-600">
                  Export CSV
                </button>
              </div>
              
              <div class="overflow-x-auto max-w-full border border-gray-300 rounded">
                <table class="w-full border-collapse">
                  <thead class="sticky top-0 bg-gray-100 z-10">
                    <tr>
                      <th *ngFor="let col of cell.result_data.columns" 
                          class="border-b border-r border-gray-300 px-3 py-2 text-left text-xs font-semibold text-gray-700 whitespace-nowrap">
                        {{ col }}
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr *ngFor="let row of getDisplayRows()" class="hover:bg-gray-50">
                      <td *ngFor="let col of cell.result_data.columns" 
                          class="border-b border-r border-gray-300 px-3 py-2 text-sm whitespace-nowrap">
                        <span [title]="formatCellValue(row[col])">
                          {{ formatCellValueWithLookup(row, col) }}
                        </span>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
              
              <div *ngIf="cell.result_data.data?.length > maxDisplayRows" class="mt-2 text-sm text-gray-600">
                Showing {{ maxDisplayRows }} of {{ cell.result_data.data.length }} rows
                <button 
                  (click)="showAllRows = !showAllRows"
                  class="ml-2 text-blue-500 hover:underline">
                  {{ showAllRows ? 'Show less' : 'Show all' }}
                </button>
              </div>
            </div>
          </div>
          
          <button 
            (click)="delete.emit()"
            class="text-red-500 hover:text-red-700">
            ×
          </button>
        </div>
      </div>
    </div>
  `,
  styles: []
})
export class NotebookCellComponent {
  @Input() cell!: Cell;
  @Input() cellIndex: number = 0;
  @Output() execute = new EventEmitter<void>();
  @Output() delete = new EventEmitter<void>();
  @Output() update = new EventEmitter<Partial<Cell>>();
  @Output() executeSuggestion = new EventEmitter<string>();
  
  @ViewChild('promptInput') promptInput?: ElementRef<HTMLTextAreaElement>;
  
  maxDisplayRows = 100;
  showAllRows = false;
  showRetryDetails = false;
  
  constructor(private toastr: ToastrService) {}
  
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
    
    if (this.showAllRows) {
      return this.cell.result_data.data;
    }
    
    return this.cell.result_data.data.slice(0, this.maxDisplayRows);
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
    if (!this.cell.result_data?.columns || !this.cell.result_data?.data) {
      this.toastr.warning('No data to export', 'Warning');
      return;
    }
    
    const columns = this.cell.result_data.columns;
    const data = this.cell.result_data.data;
    
    // Create CSV content
    const csvRows = [];
    
    // Header
    csvRows.push(columns.map((col: string) => `"${col}"`).join(','));
    
    // Data rows
    for (const row of data) {
      const values = columns.map((col: string) => {
        const value = row[col];
        if (value === null || value === undefined) {
          return '""';
        }
        // Escape quotes and wrap in quotes
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