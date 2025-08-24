import { Injectable } from '@angular/core';

@Injectable({
  providedIn: 'root'
})
export class StorageService {
  private readonly STORAGE_KEYS = {
    SELECTED_CONNECTION: 'rag_sql_selected_connection',
    CONNECTION_LIST: 'rag_sql_connections',
    QUERY_HISTORY: 'rag_sql_query_history',
    NOTEBOOK_CELLS: 'rag_sql_notebook_cells',
    USER_PREFERENCES: 'rag_sql_preferences'
  };

  constructor() {
    this.initializeStorage();
  }

  private initializeStorage(): void {
    // Check if localStorage is available
    if (!this.isLocalStorageAvailable()) {
      console.warn('LocalStorage is not available');
    }
  }

  private isLocalStorageAvailable(): boolean {
    try {
      const test = '__storage_test__';
      localStorage.setItem(test, test);
      localStorage.removeItem(test);
      return true;
    } catch {
      return false;
    }
  }

  // Connection Management
  saveSelectedConnection(connectionId: number | null): void {
    if (connectionId === null) {
      localStorage.removeItem(this.STORAGE_KEYS.SELECTED_CONNECTION);
    } else {
      localStorage.setItem(this.STORAGE_KEYS.SELECTED_CONNECTION, connectionId.toString());
    }
  }

  getSelectedConnection(): number | null {
    const stored = localStorage.getItem(this.STORAGE_KEYS.SELECTED_CONNECTION);
    return stored ? parseInt(stored, 10) : null;
  }

  // Connection List Cache
  saveConnectionList(connections: any[]): void {
    localStorage.setItem(this.STORAGE_KEYS.CONNECTION_LIST, JSON.stringify(connections));
    localStorage.setItem(this.STORAGE_KEYS.CONNECTION_LIST + '_timestamp', Date.now().toString());
  }

  getConnectionList(): { connections: any[], timestamp: number } | null {
    const connections = localStorage.getItem(this.STORAGE_KEYS.CONNECTION_LIST);
    const timestamp = localStorage.getItem(this.STORAGE_KEYS.CONNECTION_LIST + '_timestamp');
    
    if (connections && timestamp) {
      return {
        connections: JSON.parse(connections),
        timestamp: parseInt(timestamp, 10)
      };
    }
    return null;
  }

  isConnectionListCacheValid(maxAgeMs: number = 5 * 60 * 1000): boolean { // 5 minutes default
    const cached = this.getConnectionList();
    if (!cached) return false;
    
    const age = Date.now() - cached.timestamp;
    return age < maxAgeMs;
  }

  // Query History
  saveQueryHistory(connectionId: number, query: string, result: any): void {
    const key = `${this.STORAGE_KEYS.QUERY_HISTORY}_${connectionId}`;
    const history = this.getQueryHistory(connectionId);
    
    const newEntry = {
      query,
      result: result ? { 
        rowCount: result.row_count || result.data?.length || 0,
        success: true 
      } : { success: false },
      timestamp: Date.now()
    };
    
    history.unshift(newEntry);
    // Keep only last 50 queries per connection
    if (history.length > 50) {
      history.pop();
    }
    
    localStorage.setItem(key, JSON.stringify(history));
  }

  getQueryHistory(connectionId: number): any[] {
    const key = `${this.STORAGE_KEYS.QUERY_HISTORY}_${connectionId}`;
    const stored = localStorage.getItem(key);
    return stored ? JSON.parse(stored) : [];
  }

  // Notebook Cells
  saveNotebookCells(cells: any[]): void {
    // Don't save cell results, just the queries
    const cellsToSave = cells.map(cell => ({
      type: cell.type,
      content: cell.content,
      id: cell.id
    }));
    
    localStorage.setItem(this.STORAGE_KEYS.NOTEBOOK_CELLS, JSON.stringify(cellsToSave));
    localStorage.setItem(this.STORAGE_KEYS.NOTEBOOK_CELLS + '_timestamp', Date.now().toString());
  }

  getNotebookCells(): any[] | null {
    const stored = localStorage.getItem(this.STORAGE_KEYS.NOTEBOOK_CELLS);
    const timestamp = localStorage.getItem(this.STORAGE_KEYS.NOTEBOOK_CELLS + '_timestamp');
    
    // Only restore if less than 24 hours old
    if (stored && timestamp) {
      const age = Date.now() - parseInt(timestamp, 10);
      if (age < 24 * 60 * 60 * 1000) { // 24 hours
        return JSON.parse(stored);
      }
    }
    return null;
  }

  // User Preferences
  savePreferences(preferences: any): void {
    localStorage.setItem(this.STORAGE_KEYS.USER_PREFERENCES, JSON.stringify(preferences));
  }

  getPreferences(): any {
    const stored = localStorage.getItem(this.STORAGE_KEYS.USER_PREFERENCES);
    return stored ? JSON.parse(stored) : {
      pageSize: 25,
      theme: 'light',
      autoExecute: false,
      showHints: true
    };
  }

  // Clear functions
  clearConnectionData(): void {
    localStorage.removeItem(this.STORAGE_KEYS.SELECTED_CONNECTION);
    localStorage.removeItem(this.STORAGE_KEYS.CONNECTION_LIST);
    localStorage.removeItem(this.STORAGE_KEYS.CONNECTION_LIST + '_timestamp');
  }

  clearQueryHistory(connectionId?: number): void {
    if (connectionId) {
      const key = `${this.STORAGE_KEYS.QUERY_HISTORY}_${connectionId}`;
      localStorage.removeItem(key);
    } else {
      // Clear all query history
      Object.keys(localStorage).forEach(key => {
        if (key.startsWith(this.STORAGE_KEYS.QUERY_HISTORY)) {
          localStorage.removeItem(key);
        }
      });
    }
  }

  clearNotebook(): void {
    localStorage.removeItem(this.STORAGE_KEYS.NOTEBOOK_CELLS);
    localStorage.removeItem(this.STORAGE_KEYS.NOTEBOOK_CELLS + '_timestamp');
  }

  clearAll(): void {
    Object.values(this.STORAGE_KEYS).forEach(key => {
      localStorage.removeItem(key);
      localStorage.removeItem(key + '_timestamp');
    });
    // Clear all query history
    this.clearQueryHistory();
  }
}