import { Component, Input, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../../services/api.service';
import { ToastrService } from 'ngx-toastr';

@Component({
  selector: 'app-field-analysis',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="bg-white rounded-lg shadow-md border border-gray-200">
      <div class="p-4 border-b border-gray-200">
        <h3 class="text-lg font-semibold text-gray-900 flex items-center gap-2">
          🏷️ Database Field Analysis
          <button 
            (click)="refreshAnalysis()"
            [disabled]="isLoading"
            class="text-sm bg-blue-500 text-white px-3 py-1 rounded hover:bg-blue-600 disabled:opacity-50">
            {{ isLoading ? 'Loading...' : 'Refresh' }}
          </button>
        </h3>
        <p class="text-sm text-gray-600 mt-1">Semantic insights about available data and query capabilities</p>
      </div>
      
      <div class="p-4" *ngIf="!isLoading && analysis">
        <!-- Entity Overview -->
        <div *ngIf="hasEntities()" class="mb-6">
          <h4 class="text-md font-semibold text-gray-800 mb-3">📊 Available Entities</h4>
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            <div *ngFor="let entity of getEntityList()" 
                 class="border border-gray-200 rounded-lg p-3 bg-gray-50">
              <div class="flex items-center gap-2 mb-2">
                <span class="font-medium text-gray-800 capitalize">{{ entity.type }}</span>
                <span class="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded">{{ entity.tables.length }} tables</span>
              </div>
              <div class="text-xs text-gray-600">
                {{ entity.tables.join(', ') }}
              </div>
            </div>
          </div>
        </div>
        
        <!-- Data Domains -->
        <div *ngIf="hasDataDomains()" class="mb-6">
          <h4 class="text-md font-semibold text-gray-800 mb-3">🏷️ Data Categories</h4>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div *ngFor="let domain of getDataDomains()" 
                 class="border border-gray-200 rounded-lg p-3">
              <div class="flex items-center gap-2 mb-2">
                <span class="font-medium text-gray-800 capitalize">{{ domain.category }}</span>
                <span class="text-xs bg-green-100 text-green-700 px-2 py-1 rounded">{{ domain.field_count }} fields</span>
              </div>
              <div class="text-xs text-gray-600 mb-2">{{ domain.description }}</div>
              <div class="text-xs text-gray-500">
                Tables: {{ domain.tables.join(', ') }}
              </div>
            </div>
          </div>
        </div>
        
        <!-- Query Suggestions -->
        <div *ngIf="hasQuerySuggestions()" class="mb-6">
          <h4 class="text-md font-semibold text-gray-800 mb-3">💡 Query Suggestions</h4>
          <div class="space-y-2">
            <div *ngFor="let suggestion of getQuerySuggestions()" 
                 class="border border-gray-200 rounded-lg p-3 bg-blue-50">
              <div class="flex items-center justify-between">
                <div class="flex-1">
                  <div class="font-medium text-blue-800 text-sm">{{ suggestion.query_description }}</div>
                  <div class="text-xs text-gray-600 italic mt-1">"{{ suggestion.example_query }}"</div>
                  <div class="text-xs text-blue-600 mt-1">
                    Type: {{ suggestion.type }} | Confidence: {{ (suggestion.confidence * 100) | number:'1.0-0' }}%
                  </div>
                </div>
                <button 
                  (click)="useQuerySuggestion(suggestion.example_query)"
                  class="ml-3 bg-blue-500 text-white px-3 py-1 rounded text-xs hover:bg-blue-600">
                  Try It
                </button>
              </div>
            </div>
          </div>
        </div>
        
        <!-- Missing Fields -->
        <div *ngIf="hasMissingFields()" class="mb-6">
          <h4 class="text-md font-semibold text-gray-800 mb-3">⚠️ Potential Limitations</h4>
          <div class="space-y-3">
            <div *ngFor="let missing of getMissingFields()" 
                 class="border border-orange-200 rounded-lg p-3 bg-orange-50">
              <div class="font-medium text-orange-800 text-sm">{{ missing.table }}</div>
              <div class="space-y-1 mt-2">
                <div *ngFor="let field of missing.fields" class="text-xs">
                  <span class="text-orange-700 font-medium">Missing:</span> {{ field.field_name }}
                  <span class="text-gray-600 ml-2">- {{ field.reason }}</span>
                  <div *ngIf="field.alternatives.length > 0" class="text-gray-500 ml-4">
                    Alternatives: {{ field.alternatives.join(', ') }}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <!-- Database Statistics -->
        <div class="bg-gray-50 rounded-lg p-3">
          <h4 class="text-md font-semibold text-gray-800 mb-2">📈 Database Statistics</h4>
          <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
            <div>
              <div class="text-2xl font-bold text-blue-600">{{ getTotalTables() }}</div>
              <div class="text-xs text-gray-600">Total Tables</div>
            </div>
            <div>
              <div class="text-2xl font-bold text-green-600">{{ getTotalFields() }}</div>
              <div class="text-xs text-gray-600">Total Fields</div>
            </div>
            <div>
              <div class="text-2xl font-bold text-purple-600">{{ getTotalRelationships() }}</div>
              <div class="text-xs text-gray-600">Relationships</div>
            </div>
            <div>
              <div class="text-2xl font-bold text-orange-600">{{ getDataCategories() }}</div>
              <div class="text-xs text-gray-600">Data Categories</div>
            </div>
          </div>
        </div>
      </div>
      
      <div *ngIf="isLoading" class="p-8 text-center">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-2"></div>
        <p class="text-gray-600">Analyzing database fields...</p>
      </div>
      
      <div *ngIf="!isLoading && !analysis" class="p-8 text-center text-gray-500">
        <p>No field analysis available. Please select a connection first.</p>
      </div>
    </div>
  `,
  styles: []
})
export class FieldAnalysisComponent implements OnInit {
  @Input() connectionId: number | null = null;
  
  analysis: any = null;
  isLoading = false;
  
  constructor(
    private apiService: ApiService,
    private toastr: ToastrService
  ) {}
  
  ngOnInit() {
    if (this.connectionId) {
      this.loadAnalysis();
    }
  }
  
  ngOnChanges() {
    if (this.connectionId) {
      this.loadAnalysis();
    } else {
      this.analysis = null;
    }
  }
  
  loadAnalysis() {
    if (!this.connectionId) return;
    
    this.isLoading = true;
    this.apiService.getFieldAnalysisTest(this.connectionId).subscribe({
      next: (response) => {
        this.analysis = response;
        this.isLoading = false;
        console.log('Field analysis loaded:', this.analysis);
      },
      error: (error) => {
        console.error('Error loading field analysis:', error);
        this.toastr.error('Failed to load field analysis', 'Error');
        this.isLoading = false;
        this.analysis = null;
      }
    });
  }
  
  refreshAnalysis() {
    this.loadAnalysis();
  }
  
  // Helper methods
  hasEntities(): boolean {
    return this.analysis?.data_availability?.entities && 
           Object.keys(this.analysis.data_availability.entities).length > 0;
  }
  
  getEntityList(): any[] {
    if (!this.hasEntities()) return [];
    
    return Object.entries(this.analysis.data_availability.entities).map(([type, info]: [string, any]) => ({
      type,
      tables: Array.isArray(info) ? info.map((i: any) => i.table) : [info.table].filter(Boolean)
    }));
  }
  
  hasDataDomains(): boolean {
    return this.analysis?.field_categories && 
           Object.keys(this.analysis.field_categories).length > 0;
  }
  
  getDataDomains(): any[] {
    if (!this.hasDataDomains()) return [];
    
    return Object.entries(this.analysis.field_categories).map(([category, fields]: [string, any]) => ({
      category,
      field_count: Array.isArray(fields) ? fields.length : 0,
      description: this.getCategoryDescription(category),
      tables: Array.isArray(fields) ? [...new Set(fields.map((f: any) => f.table))] : []
    }));
  }
  
  getCategoryDescription(category: string): string {
    const descriptions: { [key: string]: string } = {
      'identity': 'Unique identifiers and primary/foreign keys',
      'personal_info': 'Personal names and titles',
      'contact': 'Contact information and addresses',
      'temporal': 'Dates, times, and temporal information',
      'academic': 'Academic and educational information',
      'financial': 'Financial and monetary information',
      'status': 'Status and state information',
      'location': 'Geographic and location information',
      'description': 'Descriptive text and comments'
    };
    return descriptions[category] || 'Various data fields';
  }
  
  hasQuerySuggestions(): boolean {
    return this.analysis?.query_suggestions && 
           Array.isArray(this.analysis.query_suggestions) &&
           this.analysis.query_suggestions.length > 0;
  }
  
  getQuerySuggestions(): any[] {
    if (!this.hasQuerySuggestions()) return [];
    return this.analysis.query_suggestions.slice(0, 6); // Show top 6
  }
  
  hasMissingFields(): boolean {
    return this.analysis?.missing_fields && 
           Object.keys(this.analysis.missing_fields).length > 0;
  }
  
  getMissingFields(): any[] {
    if (!this.hasMissingFields()) return [];
    
    return Object.entries(this.analysis.missing_fields).map(([table, fields]) => ({
      table,
      fields
    }));
  }
  
  getTotalTables(): number {
    return this.analysis?.tables ? Object.keys(this.analysis.tables).length : 0;
  }
  
  getTotalFields(): number {
    if (!this.analysis?.field_categories) return 0;
    return Object.values(this.analysis.field_categories).reduce((total: number, fields: any) => {
      return total + (Array.isArray(fields) ? fields.length : 0);
    }, 0);
  }
  
  getTotalRelationships(): number {
    return this.analysis?.relationships?.length || 0;
  }
  
  getDataCategories(): number {
    return this.analysis?.field_categories ? Object.keys(this.analysis.field_categories).length : 0;
  }
  
  useQuerySuggestion(query: string) {
    // For now, just show a toast. In a real app, you might add this to a notebook cell
    this.toastr.info(`Try this query: "${query}"`, 'Query Suggestion');
  }
}