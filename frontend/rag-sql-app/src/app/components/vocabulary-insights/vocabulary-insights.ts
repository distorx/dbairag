import { Component, OnInit, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../services/api.service';

interface VocabularySuggestion {
  text: string;
  type: 'column' | 'enum' | 'location';
  column?: string;
  enum_field?: string;
  enum_value?: number;
  location?: string;
  location_type?: string;
}

interface ParsedQuery {
  columns: Array<{ phrase: string; column: string; position: number }>;
  enums: Array<{ word: string; field: string; value: number }>;
  locations: Array<{ word: string; type: string }>;
}

@Component({
  selector: 'app-vocabulary-insights',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './vocabulary-insights.html',
  styleUrls: ['./vocabulary-insights.css']
})
export class VocabularyInsightsComponent implements OnInit {
  @Input() currentQuery: string = '';
  
  vocabularyStats: any = null;
  suggestions: VocabularySuggestion[] = [];
  parsedQuery: ParsedQuery | null = null;
  showInsights: boolean = false;
  activeTab: string = 'columns';
  
  // Sample columns for display
  sampleColumnMappings: Array<{ natural: string; column: string }> = [];
  sampleEnums: any = {};
  sampleLocations: string[] = [];
  
  constructor(private apiService: ApiService) {}
  
  ngOnInit() {
    this.loadVocabularyStats();
    this.loadSampleData();
  }
  
  loadVocabularyStats() {
    this.apiService.getVocabularyStats().subscribe({
      next: (response) => {
        this.vocabularyStats = response.stats;
      },
      error: (error) => {
        console.error('Error loading vocabulary stats:', error);
      }
    });
  }
  
  loadSampleData() {
    // Load sample column mappings
    this.apiService.getVocabularyColumns().subscribe({
      next: (response) => {
        const columns = response.columns;
        this.sampleColumnMappings = Object.entries(columns)
          .slice(0, 10)
          .map(([natural, column]) => ({ natural, column: column as string }));
      },
      error: (error) => {
        console.error('Error loading vocabulary columns:', error);
      }
    });
    
    // Load sample enums
    this.apiService.getVocabularyEnums().subscribe({
      next: (response) => {
        this.sampleEnums = response.enums;
      },
      error: (error) => {
        console.error('Error loading vocabulary enums:', error);
      }
    });
    
    // Load sample locations
    this.apiService.getVocabularyLocations().subscribe({
      next: (response) => {
        this.sampleLocations = response.cities.slice(0, 10);
      },
      error: (error) => {
        console.error('Error loading vocabulary locations:', error);
      }
    });
  }
  
  onQueryChange(query: string) {
    this.currentQuery = query;
    
    if (query.length > 2) {
      // Get suggestions
      this.apiService.getVocabularySuggestions(query).subscribe({
        next: (response) => {
          this.suggestions = response.suggestions;
        },
        error: (error) => {
          console.error('Error getting suggestions:', error);
        }
      });
      
      // Parse query
      this.apiService.parseWithVocabulary(query).subscribe({
        next: (response) => {
          this.parsedQuery = response.detected;
        },
        error: (error) => {
          console.error('Error parsing query:', error);
        }
      });
    } else {
      this.suggestions = [];
      this.parsedQuery = null;
    }
  }
  
  toggleInsights() {
    this.showInsights = !this.showInsights;
  }
  
  applySuggestion(suggestion: VocabularySuggestion) {
    this.currentQuery = suggestion.text;
    this.onQueryChange(this.currentQuery);
  }
  
  getEnumEntries(enumObj: any): Array<{ key: string; value: any }> {
    return Object.entries(enumObj).map(([key, value]) => ({ key, value }));
  }
}