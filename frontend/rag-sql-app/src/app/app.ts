import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ToastrService } from 'ngx-toastr';
import { ConnectionManagerComponent } from './components/connection-manager/connection-manager.component';
import { NotebookCellComponent } from './components/notebook-cell/notebook-cell.component';
import { EnumManagerComponent } from './components/enum-manager/enum-manager.component';
import { CacheStatsComponent } from './components/cache-stats/cache-stats.component';
import { HintsSearchComponent } from './components/hints-search/hints-search.component';
import { DocumentationViewerComponent } from './components/documentation-viewer/documentation-viewer.component';
import { VocabularyInsightsComponent } from './components/vocabulary-insights/vocabulary-insights';
import { NotebookService, Cell } from './services/notebook.service';
import { ApiService, QueryHint, Suggestion } from './services/api.service';
import { StorageService } from './services/storage.service';

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
    DocumentationViewerComponent,
    VocabularyInsightsComponent
  ],
  template: `
    <div class="min-h-screen bg-gradient-to-br from-slate-50 via-white to-blue-50 flex flex-col">
      <!-- Modern Header with Better Proportions -->
      <header class="bg-white/90 backdrop-blur-lg shadow-lg border-b border-gray-100">
        <div class="w-full px-8 py-5">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-4">
              <!-- Modern Icon Container -->
              <div class="relative">
                <div class="absolute inset-0 bg-gradient-to-br from-blue-400 to-indigo-600 rounded-2xl blur-lg opacity-75"></div>
                <div class="relative bg-gradient-to-br from-blue-500 to-indigo-600 p-3 rounded-2xl shadow-xl">
                  <svg class="w-7 h-7 text-white" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" 
                          d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4"></path>
                  </svg>
                </div>
              </div>
              <div>
                <h1 class="text-3xl font-bold bg-gradient-to-r from-gray-900 via-blue-800 to-indigo-900 bg-clip-text text-transparent">
                  RAG SQL Studio
                </h1>
                <p class="text-sm text-gray-500 mt-1">Natural Language Database Interface</p>
              </div>
            </div>
            <!-- Modern Status Indicator -->
            <div class="flex items-center gap-3">
              <div *ngIf="currentConnectionId" 
                   class="flex items-center gap-2 bg-green-50 px-4 py-2 rounded-full border border-green-200">
                <div class="relative">
                  <div class="w-2 h-2 bg-green-500 rounded-full"></div>
                  <div class="absolute inset-0 w-2 h-2 bg-green-400 rounded-full animate-ping"></div>
                </div>
                <span class="text-green-700 font-medium text-sm">Connected</span>
              </div>
              <div *ngIf="!currentConnectionId" 
                   class="flex items-center gap-2 bg-amber-50 px-4 py-2 rounded-full border border-amber-200">
                <div class="w-2 h-2 bg-amber-500 rounded-full"></div>
                <span class="text-amber-700 font-medium text-sm">Not Connected</span>
              </div>
            </div>
          </div>
        </div>
      </header>
      
      <main class="flex-1 w-full px-8 py-6">
        <!-- First Row - Connection and Tools with Golden Ratio -->
        <div class="mb-6">
          <div class="grid grid-cols-1 lg:grid-cols-5 gap-6">
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
            
            <!-- Cache Stats - Golden Ratio Width -->
            <div class="lg:col-span-3">
              <app-cache-stats [currentConnectionId]="currentConnectionId"></app-cache-stats>
            </div>
          </div>
        </div>
        
        <!-- Second Row - Hints Search with Better Spacing -->
        <div class="mb-6">
          <app-hints-search
            [connectionId]="currentConnectionId"
            (hintSelected)="onHintSelected($event)"
            (suggestionUsed)="onSuggestionUsed($event)">
          </app-hints-search>
        </div>

        <!-- Vocabulary Insights Component -->
        <div class="mb-6">
          <app-vocabulary-insights></app-vocabulary-insights>
        </div>
        
        <!-- Third Row - Tabbed Section -->
        <div class="w-full">
          <div class="bg-white/95 backdrop-blur rounded-2xl shadow-xl border border-gray-100 overflow-hidden">
            <!-- Modern Tab Headers -->
            <div class="bg-gradient-to-r from-gray-50 to-blue-50 border-b border-gray-200">
              <nav class="flex gap-2 px-6 pt-4" aria-label="Tabs">
                <button
                  (click)="activeTab = 'notebook'"
                  [class.bg-white]="activeTab === 'notebook'"
                  [class.border-blue-500]="activeTab === 'notebook'"
                  [class.text-blue-600]="activeTab === 'notebook'"
                  [class.shadow-sm]="activeTab === 'notebook'"
                  [class.bg-transparent]="activeTab !== 'notebook'"
                  [class.text-gray-500]="activeTab !== 'notebook'"
                  [class.hover:text-gray-700]="activeTab !== 'notebook'"
                  [class.hover:border-gray-300]="activeTab !== 'notebook'"
                  class="whitespace-nowrap py-3 px-6 border-b-3 font-semibold text-sm rounded-t-lg transition-all duration-200">
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
                  class="whitespace-nowrap py-3 px-6 border-b-3 font-semibold text-sm rounded-t-lg transition-all duration-200">
                  Database Documentation
                </button>
              </nav>
            </div>

            <!-- Tab Content with Better Spacing -->
            <div class="p-8">
              <!-- Enhanced Notebook Tab -->
              <div *ngIf="activeTab === 'notebook'">
                <div class="flex justify-between items-center mb-6">
                  <div>
                    <h2 class="text-2xl font-bold text-gray-900">Query Notebook</h2>
                    <p class="text-sm text-gray-500 mt-1">Execute natural language queries with AI assistance</p>
                  </div>
                  <div class="flex gap-3">
                    <button 
                      (click)="addNewCell()"
                      [disabled]="!currentConnectionId"
                      class="px-5 py-2.5 bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-medium rounded-xl hover:from-blue-700 hover:to-indigo-700 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 shadow-lg hover:shadow-xl transform hover:-translate-y-0.5">
                      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path>
                      </svg>
                      <span>Add Cell</span>
                    </button>
                    <button 
                      (click)="clearNotebook()"
                      [disabled]="cells.length === 0"
                      class="px-5 py-2.5 bg-white text-gray-700 font-medium rounded-xl hover:bg-gray-50 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 border border-gray-300 shadow-md hover:shadow-lg">
                      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                      </svg>
                      <span>Clear All</span>
                    </button>
                  </div>
                </div>
                
                <div *ngIf="!currentConnectionId" class="text-center py-12 bg-gradient-to-br from-gray-50 to-blue-50 rounded-2xl border-2 border-dashed border-gray-300">
                  <svg class="w-16 h-16 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4"></path>
                  </svg>
                  <h3 class="text-lg font-semibold text-gray-700">No Database Connected</h3>
                  <p class="text-sm text-gray-500 mt-2">Select a connection from above to start querying</p>
                </div>
                
                <div *ngIf="currentConnectionId && cells.length === 0" class="text-center py-12 bg-gradient-to-br from-blue-50 to-indigo-50 rounded-2xl border-2 border-dashed border-blue-300">
                  <svg class="w-16 h-16 text-blue-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"></path>
                  </svg>
                  <h3 class="text-lg font-semibold text-gray-700">Ready to Query</h3>
                  <p class="text-sm text-gray-500 mt-2 mb-6">Start by creating your first query cell</p>
                  <button 
                    (click)="addNewCell()"
                    class="px-6 py-3 bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-medium rounded-xl hover:from-blue-700 hover:to-indigo-700 transition-all duration-200 shadow-lg hover:shadow-xl transform hover:-translate-y-0.5">
                    <span class="flex items-center gap-2">
                      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path>
                      </svg>
                      <span>Create Cell</span>
                    </span>
                  </button>
                </div>
                
                <div *ngIf="currentConnectionId" class="space-y-6">
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
                
                <div *ngIf="currentConnectionId && cells.length > 0" class="mt-6">
                  <button 
                    (click)="addNewCell()"
                    class="w-full border-2 border-dashed border-gray-300 rounded-xl py-4 hover:border-blue-400 hover:bg-blue-50 text-base text-gray-600 font-medium transition-all duration-200">
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
    private toastr: ToastrService,
    private storageService: StorageService
  ) {}
  
  ngOnInit() {
    // Restore saved connection
    const savedConnectionId = this.storageService.getSelectedConnection();
    if (savedConnectionId) {
      this.currentConnectionId = savedConnectionId;
      this.notebookService.setConnectionId(savedConnectionId);
    }
    
    // Restore saved notebook cells
    const savedCells = this.storageService.getNotebookCells();
    if (savedCells && savedCells.length > 0) {
      savedCells.forEach(cell => {
        if (cell.type === 'prompt' && cell.content) {
          this.notebookService.addPromptCell(cell.content);
        }
      });
    }
    
    // Subscribe to notebook changes
    this.notebookService.session$.subscribe(session => {
      if (session) {
        this.cells = session.cells;
        this.currentConnectionId = session.connection_id || null;
        
        // Save cells to local storage (without results)
        if (this.cells.length > 0) {
          this.storageService.saveNotebookCells(this.cells);
        }
      }
    });
  }
  
  onConnectionSelected(connectionId: number) {
    this.currentConnectionId = connectionId;
    this.notebookService.setConnectionId(connectionId);
    
    // Save to local storage
    this.storageService.saveSelectedConnection(connectionId);
    
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
        
        // Add response cell with metadata
        this.notebookService.addResponseCell(
          cell.id,
          response.generated_sql || '',
          response.result_type,
          response.result_data,
          response.execution_time,
          response.metadata  // Pass metadata for pattern matching info
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