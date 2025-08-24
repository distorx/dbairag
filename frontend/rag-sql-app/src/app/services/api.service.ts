import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

export interface Connection {
  id?: number;
  name: string;
  connection_string: string;
  database_type: string;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface QueryRequest {
  connection_id: number;
  prompt: string;
}

export interface QueryResponse {
  id?: number;
  prompt: string;
  generated_sql?: string;
  result_type: 'text' | 'table' | 'error';
  result_data: any;
  execution_time?: number;
  created_at?: string;
  metadata?: any;  // Add metadata field for pattern matching info
}

export interface EnumFile {
  id: number;
  connection_id: number;
  filename: string;
  original_filename: string;
  description?: string;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
}

export interface QueryHint {
  id: number;
  category: string;
  keywords: string[];
  example: string;
  sql_pattern: string;
  tags: string[];
  popularity: number;
}

export interface Suggestion {
  type: 'hint' | 'pattern';
  category: string;
  suggestion: string;
  sql_pattern: string;
  score: number;
}

export interface CacheStats {
  connected: boolean;
  total_connections_received: number;
  total_commands_processed: number;
  keyspace_hits: number;
  keyspace_misses: number;
  hit_rate: number;
  used_memory_human: string;
  cached_keys: {
    schemas: number;
    enums: number;
    sql_queries: number;
    query_results: number;
  };
}

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private apiUrl = environment.apiUrl || 'http://localhost:8000/api';

  constructor(private http: HttpClient) { }

  // Connection endpoints
  getConnections(): Observable<Connection[]> {
    return this.http.get<Connection[]>(`${this.apiUrl}/connections`);
  }

  getConnection(id: number): Observable<Connection> {
    return this.http.get<Connection>(`${this.apiUrl}/connections/${id}`);
  }

  createConnection(connection: Connection): Observable<Connection> {
    return this.http.post<Connection>(`${this.apiUrl}/connections`, connection);
  }

  updateConnection(id: number, connection: Partial<Connection>): Observable<Connection> {
    return this.http.put<Connection>(`${this.apiUrl}/connections/${id}`, connection);
  }

  deleteConnection(id: number): Observable<any> {
    return this.http.delete(`${this.apiUrl}/connections/${id}`);
  }

  testConnection(id: number): Observable<{ success: boolean; message: string }> {
    return this.http.post<{ success: boolean; message: string }>(
      `${this.apiUrl}/connections/${id}/test`,
      {}
    );
  }

  // Query endpoints
  executeQuery(request: QueryRequest): Observable<QueryResponse> {
    return this.http.post<QueryResponse>(`${this.apiUrl}/queries/execute`, request);
  }

  executeQueryOptimized(request: QueryRequest): Observable<QueryResponse> {
    return this.http.post<QueryResponse>(`${this.apiUrl}/queries/execute-optimized`, request);
  }

  getQueryHistory(connectionId: number): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/queries/history/${connectionId}`);
  }

  // Enum file management endpoints
  uploadEnumFile(connectionId: number, file: File, description?: string): Observable<EnumFile> {
    const formData = new FormData();
    formData.append('file', file);
    if (description) {
      formData.append('description', description);
    }
    return this.http.post<EnumFile>(`${this.apiUrl}/queries/enums/${connectionId}/upload`, formData);
  }

  getEnumFiles(connectionId: number): Observable<EnumFile[]> {
    return this.http.get<EnumFile[]>(`${this.apiUrl}/queries/enums/${connectionId}/files`);
  }

  deleteEnumFile(connectionId: number, fileId: number): Observable<any> {
    return this.http.delete(`${this.apiUrl}/queries/enums/${connectionId}/files/${fileId}`);
  }

  // Hints and suggestions endpoints
  getHints(category?: string): Observable<QueryHint[]> {
    const params = category ? { params: { category } } : {};
    return this.http.get<QueryHint[]>(`${this.apiUrl}/hints`, params);
  }

  getSuggestions(userInput: string, limit: number = 10): Observable<Suggestion[]> {
    return this.http.post<Suggestion[]>(`${this.apiUrl}/hints/suggestions`, {
      user_input: userInput,
      limit
    });
  }

  createHint(hint: Partial<QueryHint>): Observable<{ id: number; message: string }> {
    return this.http.post<{ id: number; message: string }>(`${this.apiUrl}/hints`, hint);
  }

  updateHint(hintId: number, hint: Partial<QueryHint>): Observable<{ id: number; message: string }> {
    return this.http.put<{ id: number; message: string }>(`${this.apiUrl}/hints/${hintId}`, hint);
  }

  incrementHintPopularity(hintId: number): Observable<{ message: string }> {
    return this.http.post<{ message: string }>(`${this.apiUrl}/hints/popularity/${hintId}`, {});
  }

  getHintCategories(): Observable<string[]> {
    return this.http.get<string[]>(`${this.apiUrl}/hints/categories`);
  }

  getHintStats(): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}/hints/stats`);
  }

  initializeHints(): Observable<{ message: string }> {
    return this.http.post<{ message: string }>(`${this.apiUrl}/hints/initialize`, {});
  }

  learnFromHistory(limit: number = 100): Observable<any> {
    return this.http.post<any>(`${this.apiUrl}/hints/learn?limit=${limit}`, {});
  }

  // Cache management endpoints
  getCacheStats(): Observable<CacheStats> {
    return this.http.get<CacheStats>(`${this.apiUrl}/queries/cache/stats`);
  }

  invalidateCache(connectionId?: number): Observable<{ message: string; deleted: number }> {
    if (connectionId) {
      return this.http.post<{ message: string; deleted: number }>(
        `${this.apiUrl}/queries/cache/invalidate/${connectionId}`, 
        {}
      );
    }
    return this.http.post<{ message: string; deleted: number }>(
      `${this.apiUrl}/hints/cache/invalidate`, 
      {}
    );
  }

  warmCache(): Observable<{ message: string; hints_loaded: number; patterns_loaded: number }> {
    return this.http.post<{ message: string; hints_loaded: number; patterns_loaded: number }>(
      `${this.apiUrl}/hints/cache/warm`, 
      {}
    );
  }

  // Documentation endpoints
  getDocumentation(connectionId: number, format: string = 'json'): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}/queries/documentation/${connectionId}?format=${format}`);
  }

  refreshDocumentation(connectionId: number): Observable<any> {
    return this.http.post<any>(`${this.apiUrl}/queries/documentation/${connectionId}/refresh`, {});
  }
  
  // Field analysis endpoint
  getFieldAnalysis(connectionId: number): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}/queries/field-analysis/${connectionId}`);
  }

  // Test field analysis endpoint with mock data
  getFieldAnalysisTest(connectionId: number): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}/queries/field-analysis/${connectionId}/test`);
  }

  // Vocabulary Service Endpoints
  getVocabularyStats(): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}/queries/vocabulary/stats`);
  }

  getVocabularyColumns(): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}/queries/vocabulary/columns`);
  }

  getVocabularyEnums(): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}/queries/vocabulary/enums`);
  }

  getVocabularyLocations(): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}/queries/vocabulary/locations`);
  }

  getVocabularySuggestions(query: string): Observable<any> {
    return this.http.post<any>(`${this.apiUrl}/queries/vocabulary/suggest`, { query });
  }

  parseWithVocabulary(query: string): Observable<any> {
    return this.http.post<any>(`${this.apiUrl}/queries/vocabulary/parse`, { query });
  }
}