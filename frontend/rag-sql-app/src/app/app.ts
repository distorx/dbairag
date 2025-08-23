import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ToastrService } from 'ngx-toastr';
import { ConnectionManagerComponent } from './components/connection-manager/connection-manager.component';
import { NotebookCellComponent } from './components/notebook-cell/notebook-cell.component';
import { EnumManagerComponent } from './components/enum-manager/enum-manager.component';
import { CacheStatsComponent } from './components/cache-stats/cache-stats.component';
import { HintsSearchComponent } from './components/hints-search/hints-search.component';
import { DocumentationViewerComponent } from './components/documentation-viewer/documentation-viewer.component';
import { NotebookService, Cell } from './services/notebook.service';
import { ApiService, QueryHint, Suggestion } from './services/api.service';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    CommonModule, 
    ConnectionManagerComponent, 
    NotebookCellComponent,
    EnumManagerComponent,
    CacheStatsComponent,
    HintsSearchComponent,
    DocumentationViewerComponent
  ],
  template: `
    <div class="min-h-screen bg-gray-100 flex flex-col">
      <header class="bg-white shadow-sm border-b">
        <div class="w-full px-4 sm:px-6 lg:px-8 py-4">
          <h1 class="text-2xl font-bold text-gray-900">RAG SQL Query Notebook</h1>
          <p class="text-sm text-gray-600">Natural language SQL queries with Jupyter-like interface</p>
        </div>
      </header>
      
      <main class="flex-1 w-full px-4 sm:px-6 lg:px-8 py-6">
        <!-- First Row - Connection and Tools -->
        <div class="mb-6">
          <div class="grid grid-cols-1 lg:grid-cols-4 gap-4">
            <!-- Connection Manager -->
            <div class="lg:col-span-1">
              <app-connection-manager 
                (connectionSelected)="onConnectionSelected($event)">
              </app-connection-manager>
            </div>
            
            <!-- Enum Manager -->
            <div class="lg:col-span-1">
              <app-enum-manager 
                *ngIf="currentConnectionId"
                [connectionId]="currentConnectionId">
              </app-enum-manager>
            </div>
            
            <!-- Cache Stats -->
            <div class="lg:col-span-2">
              <app-cache-stats [currentConnectionId]="currentConnectionId"></app-cache-stats>
            </div>
          </div>
        </div>
        
        <!-- Second Row - Hints Search -->
        <div class="mb-6">
          <app-hints-search
            (hintSelected)="onHintSelected($event)"
            (suggestionUsed)="onSuggestionUsed($event)">
          </app-hints-search>
        </div>
        
        <!-- Third Row - Tabbed Section (Notebook and Documentation) -->
        <div class="w-full">
          <div class="bg-white rounded-lg shadow-md">
            <!-- Tab Headers -->
            <div class="border-b border-gray-200">
              <nav class="flex space-x-8 px-6" aria-label="Tabs">
                <button
                  (click)="activeTab = 'notebook'"
                  [class.border-blue-500]="activeTab === 'notebook'"
                  [class.text-blue-600]="activeTab === 'notebook'"
                  [class.border-transparent]="activeTab !== 'notebook'"
                  [class.text-gray-500]="activeTab !== 'notebook'"
                  [class.hover:text-gray-700]="activeTab !== 'notebook'"
                  [class.hover:border-gray-300]="activeTab !== 'notebook'"
                  class="whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm">
                  Query Notebook
                </button>
                <button
                  (click)="activeTab = 'documentation'"
                  [disabled]="!currentConnectionId"
                  [class.border-blue-500]="activeTab === 'documentation'"
                  [class.text-blue-600]="activeTab === 'documentation'"
                  [class.border-transparent]="activeTab !== 'documentation'"
                  [class.text-gray-500]="activeTab !== 'documentation'"
                  [class.hover:text-gray-700]="activeTab !== 'documentation'"
                  [class.hover:border-gray-300]="activeTab !== 'documentation'"
                  [class.opacity-50]="!currentConnectionId"
                  [class.cursor-not-allowed]="!currentConnectionId"
                  class="whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm">
                  Database Documentation
                </button>
              </nav>
            </div>

            <!-- Tab Content -->
            <div class="p-6">
              <!-- Notebook Tab -->
              <div *ngIf="activeTab === 'notebook'">
                <div class="flex justify-between items-center mb-4">
                  <h2 class="text-xl font-bold">Query Notebook</h2>
                  <div class="flex gap-2">
                    <button 
                      (click)="addNewCell()"
                      [disabled]="!currentConnectionId"
                      class="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 disabled:opacity-50">
                      Add Cell
                    </button>
                    <button 
                      (click)="clearNotebook()"
                      [disabled]="cells.length === 0"
                      class="bg-gray-500 text-white px-4 py-2 rounded hover:bg-gray-600 disabled:opacity-50">
                      Clear All
                    </button>
                  </div>
                </div>
                
                <div *ngIf="!currentConnectionId" class="text-center py-8 text-gray-500">
                  Please select a database connection to start querying
                </div>
                
                <div *ngIf="currentConnectionId && cells.length === 0" class="text-center py-8">
                  <p class="text-gray-500 mb-4">No cells yet. Click "Add Cell" to start.</p>
                  <button 
                    (click)="addNewCell()"
                    class="bg-blue-500 text-white px-6 py-3 rounded-lg hover:bg-blue-600">
                    Create First Cell
                  </button>
                </div>
                
                <div *ngIf="currentConnectionId" class="space-y-4">
                  <app-notebook-cell
                    *ngFor="let cell of cells; let i = index"
                    [cell]="cell"
                    [cellIndex]="i"
                    (execute)="executeCell(cell)"
                    (delete)="deleteCell(cell.id)"
                    (update)="updateCell(cell.id, $event)"
                    (executeSuggestion)="executeSuggestedQuery($event)">
                  </app-notebook-cell>
                </div>
                
                <div *ngIf="currentConnectionId && cells.length > 0" class="mt-4">
                  <button 
                    (click)="addNewCell()"
                    class="w-full border-2 border-dashed border-gray-300 rounded-lg py-3 hover:border-blue-400 hover:bg-gray-50">
                    + Add New Cell
                  </button>
                </div>
              </div>

              <!-- Documentation Tab -->
              <div *ngIf="activeTab === 'documentation'">
                <app-documentation-viewer
                  *ngIf="currentConnectionId"
                  [connectionId]="currentConnectionId">
                </app-documentation-viewer>
                <div *ngIf="!currentConnectionId" class="text-center py-8 text-gray-500">
                  Please select a database connection to view documentation
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  `,
  styles: []
})
export class AppComponent implements OnInit {
  title = 'rag-sql-app';
  currentConnectionId: number | null = null;
  cells: Cell[] = [];
  activeTab: 'notebook' | 'documentation' = 'notebook';
  
  constructor(
    private notebookService: NotebookService,
    private apiService: ApiService,
    private toastr: ToastrService
  ) {}
  
  ngOnInit() {
    this.notebookService.session$.subscribe(session => {
      if (session) {
        this.cells = session.cells;
        this.currentConnectionId = session.connection_id || null;
      }
    });
  }
  
  onConnectionSelected(connectionId: number) {
    this.currentConnectionId = connectionId;
    this.notebookService.setConnectionId(connectionId);
    
    // Add a new cell if none exist
    if (this.cells.length === 0) {
      this.addNewCell();
    }
  }
  
  addNewCell() {
    if (!this.currentConnectionId) return;
    this.notebookService.addPromptCell('');
  }
  
  clearNotebook() {
    if (confirm('Are you sure you want to clear all cells?')) {
      this.notebookService.clearSession();
    }
  }
  
  executeCell(cell: Cell) {
    if (!this.currentConnectionId || !cell.content) return;
    
    // Mark cell as executing
    this.notebookService.updateCell(cell.id, { isExecuting: true });
    this.toastr.info('Executing query...', 'Processing');
    
    // Execute query with optimized endpoint for 36x performance improvement
    this.apiService.executeQueryOptimized({
      connection_id: this.currentConnectionId,
      prompt: cell.content
    }).subscribe({
      next: (response) => {
        // Mark cell as not executing
        this.notebookService.updateCell(cell.id, { isExecuting: false });
        
        // Add response cell
        this.notebookService.addResponseCell(
          cell.id,
          response.generated_sql || '',
          response.result_type,
          response.result_data,
          response.execution_time
        );
        
        // Show success notification
        if (response.result_type === 'table' && response.result_data?.row_count !== undefined) {
          this.toastr.success(`Query executed successfully! Retrieved ${response.result_data.row_count} rows in ${response.execution_time}ms`, 'Success');
        } else if (response.result_type === 'text') {
          this.toastr.success(`Query executed successfully in ${response.execution_time}ms`, 'Success');
        } else {
          this.toastr.success('Query executed successfully!', 'Success');
        }
        
        // Add a new prompt cell for convenience
        this.addNewCell();
      },
      error: (err) => {
        // Mark cell as not executing
        this.notebookService.updateCell(cell.id, { isExecuting: false });
        
        // Add error response
        const errorMessage = err.error?.detail || err.message || 'An error occurred';
        this.notebookService.addResponseCell(
          cell.id,
          '',
          'error',
          { error: errorMessage }
        );
        
        // Show error notification
        this.toastr.error(errorMessage, 'Query Failed');
      }
    });
  }
  
  deleteCell(cellId: string) {
    this.notebookService.deleteCell(cellId);
  }
  
  updateCell(cellId: string, updates: Partial<Cell>) {
    this.notebookService.updateCell(cellId, updates);
  }
  
  onHintSelected(hint: QueryHint) {
    // Add a new cell with the hint's example query
    if (!this.currentConnectionId) {
      this.toastr.warning('Please select a connection first', 'No Connection');
      return;
    }
    
    // Add a new cell if none exist or if the last cell has content
    const lastCell = this.cells[this.cells.length - 1];
    if (this.cells.length === 0 || (lastCell && lastCell.content)) {
      this.addNewCell();
    }
    
    // Update the last cell with the hint's example
    const targetCell = this.cells[this.cells.length - 1];
    if (targetCell) {
      this.notebookService.updateCell(targetCell.id, { 
        content: hint.example 
      });
      this.toastr.info(`Hint applied: ${hint.example}`, 'Hint Used');
    }
  }
  
  onSuggestionUsed(suggestion: Suggestion) {
    // Add a new cell with the suggestion
    if (!this.currentConnectionId) {
      this.toastr.warning('Please select a connection first', 'No Connection');
      return;
    }
    
    // Add a new cell if none exist or if the last cell has content
    const lastCell = this.cells[this.cells.length - 1];
    if (this.cells.length === 0 || (lastCell && lastCell.content)) {
      this.addNewCell();
    }
    
    // Update the last cell with the suggestion
    const targetCell = this.cells[this.cells.length - 1];
    if (targetCell) {
      this.notebookService.updateCell(targetCell.id, { 
        content: suggestion.suggestion 
      });
      this.toastr.info(`Suggestion applied: ${suggestion.suggestion}`, 'Suggestion Used');
    }
  }
  
  executeSuggestedQuery(suggestedQuery: string) {
    if (!this.currentConnectionId) {
      this.toastr.warning('Please select a connection first', 'No Connection');
      return;
    }
    
    // Add a new cell with the suggested query
    this.addNewCell();
    
    // Update the new cell with the suggested query
    const targetCell = this.cells[this.cells.length - 1];
    if (targetCell) {
      this.notebookService.updateCell(targetCell.id, { 
        content: suggestedQuery 
      });
      
      // Automatically execute the suggested query
      setTimeout(() => {
        this.executeCell(targetCell);
      }, 100); // Small delay to ensure UI updates
      
      this.toastr.info('Suggested query added and executing...', 'Suggestion Applied');
    }
  }
}