import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';
import { v4 as uuidv4 } from 'uuid';

export interface Cell {
  id: string;
  type: 'prompt' | 'response';
  content: string;
  result_type?: 'text' | 'table' | 'error';
  result_data?: any;
  execution_time?: number;
  created_at: Date;
  isExecuting?: boolean;
}

export interface NotebookSession {
  id: string;
  connection_id?: number;
  cells: Cell[];
  created_at: Date;
  updated_at: Date;
}

@Injectable({
  providedIn: 'root'
})
export class NotebookService {
  private currentSession$ = new BehaviorSubject<NotebookSession | null>(null);
  
  constructor() {
    this.initializeSession();
  }

  get session$() {
    return this.currentSession$.asObservable();
  }

  get currentSession() {
    return this.currentSession$.value;
  }

  initializeSession() {
    const session: NotebookSession = {
      id: uuidv4(),
      cells: [],
      created_at: new Date(),
      updated_at: new Date()
    };
    this.currentSession$.next(session);
  }

  setConnectionId(connectionId: number) {
    if (this.currentSession) {
      this.currentSession.connection_id = connectionId;
      this.currentSession.updated_at = new Date();
      this.currentSession$.next(this.currentSession);
    }
  }

  addPromptCell(content: string = ''): Cell {
    const cell: Cell = {
      id: uuidv4(),
      type: 'prompt',
      content,
      created_at: new Date()
    };
    
    if (this.currentSession) {
      this.currentSession.cells.push(cell);
      this.currentSession.updated_at = new Date();
      this.currentSession$.next(this.currentSession);
    }
    
    return cell;
  }

  addResponseCell(
    promptCellId: string,
    content: string,
    result_type: 'text' | 'table' | 'error',
    result_data: any,
    execution_time?: number
  ): Cell {
    const cell: Cell = {
      id: uuidv4(),
      type: 'response',
      content,
      result_type,
      result_data,
      execution_time,
      created_at: new Date()
    };
    
    if (this.currentSession) {
      // Find the prompt cell and add response after it
      const promptIndex = this.currentSession.cells.findIndex(c => c.id === promptCellId);
      if (promptIndex !== -1) {
        this.currentSession.cells.splice(promptIndex + 1, 0, cell);
      } else {
        this.currentSession.cells.push(cell);
      }
      this.currentSession.updated_at = new Date();
      this.currentSession$.next(this.currentSession);
    }
    
    return cell;
  }

  updateCell(cellId: string, updates: Partial<Cell>) {
    if (this.currentSession) {
      const cellIndex = this.currentSession.cells.findIndex(c => c.id === cellId);
      if (cellIndex !== -1) {
        this.currentSession.cells[cellIndex] = {
          ...this.currentSession.cells[cellIndex],
          ...updates
        };
        this.currentSession.updated_at = new Date();
        this.currentSession$.next(this.currentSession);
      }
    }
  }

  deleteCell(cellId: string) {
    if (this.currentSession) {
      this.currentSession.cells = this.currentSession.cells.filter(c => c.id !== cellId);
      this.currentSession.updated_at = new Date();
      this.currentSession$.next(this.currentSession);
    }
  }

  clearSession() {
    if (this.currentSession) {
      const connectionId = this.currentSession.connection_id;
      this.initializeSession();
      if (connectionId) {
        this.setConnectionId(connectionId);
      }
    }
  }
}