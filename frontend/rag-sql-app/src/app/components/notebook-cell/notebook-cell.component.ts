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
            
            <!-- Execution Time -->
            <div *ngIf="cell.execution_time" class="text-sm text-gray-500 mb-2">
              Executed in {{ cell.execution_time }}ms
            </div>
            
            <!-- Error Display -->
            <div *ngIf="cell.result_type === 'error'" class="bg-red-50 border border-red-200 rounded p-3">
              <div class="text-red-800">
                {{ cell.result_data?.error || cell.result_data }}
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
  
  @ViewChild('promptInput') promptInput?: ElementRef<HTMLTextAreaElement>;
  
  maxDisplayRows = 100;
  showAllRows = false;
  
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
}