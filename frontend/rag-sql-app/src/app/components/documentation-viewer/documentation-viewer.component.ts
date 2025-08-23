import { Component, Input, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../services/api.service';
import { ToastrService } from 'ngx-toastr';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';
import * as marked from 'marked';

interface DatabaseDocumentation {
  database_info: {
    database_name: string;
    driver: string;
    server: string;
  };
  tables: Record<string, TableInfo>;
  relationships: Relationship[];
  views: Record<string, ViewInfo>;
  stored_procedures: Record<string, ProcedureInfo>;
  statistics: {
    total_tables: number;
    total_columns: number;
    total_relationships: number;
    total_views: number;
    total_stored_procedures: number;
    total_rows: number;
  };
}

interface TableInfo {
  schema: string;
  name: string;
  columns: ColumnInfo[];
  primary_keys: string[];
  foreign_keys: ForeignKey[];
  row_count: number;
}

interface ColumnInfo {
  name: string;
  type: string;
  size: number;
  nullable: boolean;
  default: string;
  description: string;
}

interface ForeignKey {
  column: string;
  references_table: string;
  references_column: string;
  constraint_name: string;
}

interface Relationship {
  from_table: string;
  from_column: string;
  to_table: string;
  to_column: string;
  relationship_type: string;
  constraint_name: string;
}

interface ViewInfo {
  schema: string;
  name: string;
  columns: ColumnInfo[];
}

interface ProcedureInfo {
  schema: string;
  name: string;
  type: string;
}

@Component({
  selector: 'app-documentation-viewer',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="bg-white rounded-lg shadow-md p-6">
      <div class="flex justify-between items-center mb-4">
        <h2 class="text-2xl font-bold">Database Documentation</h2>
        <div class="flex gap-2">
          <button
            (click)="toggleView()"
            class="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600">
            {{ viewMode === 'visual' ? 'Markdown View' : 'Visual View' }}
          </button>
          <button
            (click)="refreshDocumentation()"
            [disabled]="loading"
            class="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600 disabled:opacity-50 relative">
            <span *ngIf="!loading">🔄 Refresh</span>
            <span *ngIf="loading" class="flex items-center">
              <svg class="animate-spin h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Refreshing...
            </span>
          </button>
          <button
            (click)="downloadDocumentation()"
            [disabled]="!documentation"
            class="bg-gray-500 text-white px-4 py-2 rounded hover:bg-gray-600 disabled:opacity-50">
            Download MD
          </button>
        </div>
      </div>
      
      <!-- Loading State -->
      <div *ngIf="loading" class="text-center py-8">
        <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-green-500"></div>
        <p class="mt-2 text-gray-600">
          <span *ngIf="!documentation">Generating fresh documentation from database...</span>
          <span *ngIf="documentation">Refreshing documentation with latest database changes...</span>
        </p>
        <p class="mt-1 text-sm text-gray-500">This ensures you have the most current schema, enums, and relationships</p>
      </div>
      
      <!-- Error State -->
      <div *ngIf="error" class="bg-red-50 border border-red-200 rounded p-4 text-red-800">
        {{ error }}
      </div>
      
      <!-- Visual View -->
      <div *ngIf="!loading && !error && documentation && viewMode === 'visual'" class="space-y-6">
        <!-- Statistics -->
        <div class="bg-gray-50 rounded-lg p-4">
          <h3 class="text-lg font-semibold mb-3">Database Statistics</h3>
          <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
            <div class="text-center">
              <div class="text-2xl font-bold text-blue-600">{{ documentation.statistics.total_tables }}</div>
              <div class="text-sm text-gray-600">Tables</div>
            </div>
            <div class="text-center">
              <div class="text-2xl font-bold text-green-600">{{ documentation.statistics.total_columns }}</div>
              <div class="text-sm text-gray-600">Columns</div>
            </div>
            <div class="text-center">
              <div class="text-2xl font-bold text-purple-600">{{ documentation.statistics.total_relationships }}</div>
              <div class="text-sm text-gray-600">Relationships</div>
            </div>
            <div class="text-center">
              <div class="text-2xl font-bold text-orange-600">{{ documentation.statistics.total_views }}</div>
              <div class="text-sm text-gray-600">Views</div>
            </div>
            <div class="text-center">
              <div class="text-2xl font-bold text-red-600">{{ documentation.statistics.total_stored_procedures }}</div>
              <div class="text-sm text-gray-600">Procedures</div>
            </div>
            <div class="text-center">
              <div class="text-2xl font-bold text-indigo-600">{{ documentation.statistics.total_rows | number }}</div>
              <div class="text-sm text-gray-600">Total Rows</div>
            </div>
          </div>
        </div>
        
        <!-- Search/Filter -->
        <div class="flex gap-2">
          <input
            type="text"
            [(ngModel)]="searchTerm"
            (ngModelChange)="filterTables()"
            placeholder="Search tables..."
            class="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
          <select
            [(ngModel)]="selectedSchema"
            (ngModelChange)="filterTables()"
            class="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
            <option value="">All Schemas</option>
            <option *ngFor="let schema of schemas" [value]="schema">{{ schema }}</option>
          </select>
        </div>
        
        <!-- Tables -->
        <div class="space-y-4">
          <h3 class="text-lg font-semibold">Tables ({{ filteredTables.length }})</h3>
          
          <div *ngFor="let table of filteredTables" class="border border-gray-200 rounded-lg overflow-hidden">
            <div 
              (click)="toggleTable(table.name)"
              class="bg-gray-50 px-4 py-3 cursor-pointer hover:bg-gray-100 flex justify-between items-center">
              <div>
                <span class="font-semibold">{{ table.name }}</span>
                <span class="ml-2 text-sm text-gray-600">({{ table.row_count | number }} rows)</span>
                <span *ngIf="table.primary_keys.length > 0" class="ml-2 text-xs bg-yellow-100 text-yellow-800 px-2 py-1 rounded">
                  PK: {{ table.primary_keys.join(', ') }}
                </span>
              </div>
              <svg [class.rotate-180]="expandedTables.has(table.name)" 
                   class="w-5 h-5 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
              </svg>
            </div>
            
            <div *ngIf="expandedTables.has(table.name)" class="p-4">
              <!-- Columns -->
              <div class="mb-4">
                <h4 class="font-semibold mb-2">Columns</h4>
                <div class="overflow-x-auto">
                  <table class="w-full text-sm">
                    <thead>
                      <tr class="border-b">
                        <th class="text-left py-2">Column</th>
                        <th class="text-left py-2">Type</th>
                        <th class="text-left py-2">Nullable</th>
                        <th class="text-left py-2">Description</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr *ngFor="let col of table.columns" class="border-b">
                        <td class="py-2">
                          <span *ngIf="table.primary_keys.includes(col.name)" class="mr-1">🔑</span>
                          <span *ngIf="isForeignKey(table, col.name)" class="mr-1">🔗</span>
                          {{ col.name }}
                        </td>
                        <td class="py-2">{{ col.type }}</td>
                        <td class="py-2">
                          <span [class.text-green-600]="!col.nullable" [class.text-gray-400]="col.nullable">
                            {{ col.nullable ? 'Yes' : 'No' }}
                          </span>
                        </td>
                        <td class="py-2 text-gray-600">{{ col.description }}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
              
              <!-- Foreign Keys -->
              <div *ngIf="table.foreign_keys.length > 0" class="mb-4">
                <h4 class="font-semibold mb-2">Foreign Keys</h4>
                <div class="space-y-1">
                  <div *ngFor="let fk of table.foreign_keys" class="text-sm">
                    <span class="font-mono bg-gray-100 px-2 py-1 rounded">{{ fk.column }}</span>
                    →
                    <span class="font-mono bg-blue-100 px-2 py-1 rounded">{{ fk.references_table }}.{{ fk.references_column }}</span>
                  </div>
                </div>
              </div>
              
              <!-- Related Tables -->
              <div *ngIf="getRelatedTables(table.name).length > 0" class="mb-4">
                <h4 class="font-semibold mb-2">Related Tables</h4>
                <div class="flex flex-wrap gap-2">
                  <button
                    *ngFor="let related of getRelatedTables(table.name)"
                    (click)="scrollToTable(related)"
                    class="text-sm bg-blue-50 text-blue-700 px-3 py-1 rounded hover:bg-blue-100">
                    {{ related }}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <!-- Relationships Diagram -->
        <div *ngIf="documentation.relationships.length > 0" class="space-y-4">
          <h3 class="text-lg font-semibold">Relationships ({{ documentation.relationships.length }})</h3>
          <div class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead>
                <tr class="border-b">
                  <th class="text-left py-2">From Table</th>
                  <th class="text-left py-2">From Column</th>
                  <th class="text-left py-2"></th>
                  <th class="text-left py-2">To Table</th>
                  <th class="text-left py-2">To Column</th>
                </tr>
              </thead>
              <tbody>
                <tr *ngFor="let rel of documentation.relationships" class="border-b hover:bg-gray-50">
                  <td class="py-2 font-mono">{{ rel.from_table }}</td>
                  <td class="py-2 font-mono">{{ rel.from_column }}</td>
                  <td class="py-2 text-center">→</td>
                  <td class="py-2 font-mono">{{ rel.to_table }}</td>
                  <td class="py-2 font-mono">{{ rel.to_column }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
      
      <!-- Markdown View -->
      <div *ngIf="!loading && !error && markdownContent && viewMode === 'markdown'" 
           class="prose prose-sm max-w-none markdown-content"
           [innerHTML]="renderedMarkdown">
      </div>
    </div>
  `,
  styles: [`
    .markdown-content {
      @apply text-gray-800;
    }
    .markdown-content h1 { @apply text-3xl font-bold mt-6 mb-4; }
    .markdown-content h2 { @apply text-2xl font-bold mt-5 mb-3; }
    .markdown-content h3 { @apply text-xl font-semibold mt-4 mb-2; }
    .markdown-content h4 { @apply text-lg font-semibold mt-3 mb-2; }
    .markdown-content table { @apply w-full border-collapse my-4; }
    .markdown-content th { @apply bg-gray-100 border border-gray-300 px-3 py-2 text-left; }
    .markdown-content td { @apply border border-gray-300 px-3 py-2; }
    .markdown-content ul { @apply list-disc list-inside my-2; }
    .markdown-content li { @apply my-1; }
    .markdown-content code { @apply bg-gray-100 px-1 py-0.5 rounded text-sm; }
    .markdown-content pre { @apply bg-gray-100 p-3 rounded overflow-x-auto; }
  `]
})
export class DocumentationViewerComponent implements OnInit {
  @Input() connectionId!: number;
  
  documentation: DatabaseDocumentation | null = null;
  markdownContent: string = '';
  renderedMarkdown: SafeHtml = '';
  loading = false;
  error = '';
  viewMode: 'visual' | 'markdown' = 'visual';
  
  searchTerm = '';
  selectedSchema = '';
  schemas: string[] = [];
  filteredTables: TableInfo[] = [];
  expandedTables = new Set<string>();
  
  constructor(
    private apiService: ApiService,
    private toastr: ToastrService,
    private sanitizer: DomSanitizer
  ) {}
  
  ngOnInit() {
    if (this.connectionId) {
      this.loadDocumentation();
    }
  }
  
  async loadDocumentation() {
    this.loading = true;
    this.error = '';
    
    try {
      // Load JSON documentation
      const response = await this.apiService.getDocumentation(this.connectionId, 'json').toPromise();
      this.documentation = response as DatabaseDocumentation;
      
      // Extract unique schemas
      this.schemas = [...new Set(Object.values(this.documentation.tables).map(t => t.schema).filter(s => s))];
      
      // Initialize filtered tables
      this.filterTables();
      
      // Load markdown version
      const mdResponse = await this.apiService.getDocumentation(this.connectionId, 'markdown').toPromise();
      if (mdResponse && mdResponse.content) {
        this.markdownContent = mdResponse.content;
        const parsedHtml = await marked.parse(this.markdownContent);
        this.renderedMarkdown = this.sanitizer.bypassSecurityTrustHtml(parsedHtml);
      }
      
      this.loading = false;
    } catch (err: any) {
      this.error = err.error?.detail || 'Failed to load documentation';
      this.loading = false;
      this.toastr.error(this.error, 'Error');
    }
  }
  
  filterTables() {
    if (!this.documentation) return;
    
    let tables = Object.values(this.documentation.tables);
    
    // Filter by schema
    if (this.selectedSchema) {
      tables = tables.filter(t => t.schema === this.selectedSchema);
    }
    
    // Filter by search term
    if (this.searchTerm) {
      const term = this.searchTerm.toLowerCase();
      tables = tables.filter(t => 
        t.name.toLowerCase().includes(term) ||
        t.columns.some(c => c.name.toLowerCase().includes(term))
      );
    }
    
    this.filteredTables = tables;
  }
  
  toggleTable(tableName: string) {
    if (this.expandedTables.has(tableName)) {
      this.expandedTables.delete(tableName);
    } else {
      this.expandedTables.add(tableName);
    }
  }
  
  isForeignKey(table: TableInfo, columnName: string): boolean {
    return table.foreign_keys.some(fk => fk.column === columnName);
  }
  
  getRelatedTables(tableName: string): string[] {
    if (!this.documentation) return [];
    
    const related = new Set<string>();
    
    // Find tables this table references
    const table = this.documentation.tables[tableName];
    if (table) {
      table.foreign_keys.forEach(fk => {
        related.add(fk.references_table);
      });
    }
    
    // Find tables that reference this table
    this.documentation.relationships
      .filter(rel => rel.to_table === tableName)
      .forEach(rel => related.add(rel.from_table));
    
    return Array.from(related);
  }
  
  scrollToTable(tableName: string) {
    // Expand the table if not already expanded
    this.expandedTables.add(tableName);
    
    // Scroll to the table element
    setTimeout(() => {
      const element = document.getElementById(`table-${tableName}`);
      if (element) {
        element.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    }, 100);
  }
  
  toggleView() {
    this.viewMode = this.viewMode === 'visual' ? 'markdown' : 'visual';
  }
  
  async refreshDocumentation() {
    this.loading = true;
    
    try {
      await this.apiService.refreshDocumentation(this.connectionId).toPromise();
      await this.loadDocumentation();
      this.toastr.success(
        'Documentation refreshed with latest database schema, enums, and relationships!', 
        'Fresh Data Loaded'
      );
    } catch (err: any) {
      const errorMsg = err.error?.detail || 'Failed to refresh documentation';
      this.toastr.error(errorMsg, 'Refresh Failed');
      this.loading = false;
    }
  }
  
  downloadDocumentation() {
    if (!this.markdownContent) return;
    
    const blob = new Blob([this.markdownContent], { type: 'text/markdown' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `database-documentation-${this.connectionId}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
    
    this.toastr.success('Documentation downloaded', 'Success');
  }
}