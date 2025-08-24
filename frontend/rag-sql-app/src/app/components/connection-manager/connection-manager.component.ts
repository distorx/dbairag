import { Component, OnInit, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ToastrService } from 'ngx-toastr';
import { ApiService, Connection } from '../../services/api.service';
import { StorageService } from '../../services/storage.service';

@Component({
  selector: 'app-connection-manager',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="bg-white rounded-xl shadow-lg border border-gray-100 overflow-hidden">
      <!-- Header -->
      <div class="bg-gradient-to-r from-purple-600 to-indigo-600 px-3 py-2">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2">
            <svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4"></path>
            </svg>
            <h3 class="text-sm font-semibold text-white">Database Connections</h3>
          </div>
          <span class="bg-white/20 text-white px-2 py-0.5 rounded-full text-xs">
            {{ connections.length }} {{ connections.length === 1 ? 'Connection' : 'Connections' }}
          </span>
        </div>
      </div>
      
      <div class="p-3">
        <!-- Connection List -->
        <div class="mb-3">
          <label class="block text-xs font-semibold text-gray-700 mb-1">Active Connection</label>
          <div class="relative">
            <select 
              [(ngModel)]="selectedConnectionId"
              (change)="onConnectionSelect()"
              class="w-full pl-9 pr-8 py-2 bg-gray-50 border border-gray-200 rounded text-sm focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all duration-200 appearance-none cursor-pointer hover:bg-gray-100">
              <option [value]="null">Select a connection...</option>
              <option *ngFor="let conn of connections" [value]="conn.id">
                {{ conn.name }} ({{ conn.database_type }})
              </option>
            </select>
            <svg class="absolute left-3 top-2.5 w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path>
            </svg>
            <svg class="absolute right-3 top-3 w-4 h-4 text-gray-400 pointer-events-none" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
            </svg>
          </div>
        </div>
        
        <!-- Add New Connection Button -->
        <div class="mb-3">
          <button 
            (click)="showAddForm = !showAddForm"
            class="w-full flex items-center justify-center gap-2 bg-gradient-to-r from-purple-600 to-indigo-600 text-white px-3 py-2 rounded hover:from-purple-700 hover:to-indigo-700 transition-all duration-200 shadow text-sm">
            <svg *ngIf="!showAddForm" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path>
            </svg>
            <svg *ngIf="showAddForm" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
            </svg>
            {{ showAddForm ? 'Cancel' : 'Add New Connection' }}
          </button>
        </div>
        
        <!-- New Connection Form -->
        <div *ngIf="showAddForm" class="bg-gradient-to-br from-purple-50 to-indigo-50 rounded-lg p-6 mb-6 border border-purple-200">
          <h3 class="text-lg font-bold text-gray-800 mb-4 flex items-center gap-2">
            <svg class="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path>
            </svg>
            New Connection
          </h3>
          <div class="space-y-4">
            <div>
              <label class="block text-sm font-semibold text-gray-700 mb-2">Connection Name</label>
              <input 
                [(ngModel)]="newConnection.name"
                type="text"
                placeholder="My Database"
                class="w-full px-4 py-3 bg-white border border-gray-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all duration-200">
            </div>
            
            <div>
              <label class="block text-sm font-semibold text-gray-700 mb-2">Connection String</label>
              <textarea 
                [(ngModel)]="newConnection.connection_string"
                placeholder="Server=localhost;Database=mydb;User Id=user;Password=pass;"
                rows="3"
                class="w-full px-4 py-3 bg-white border border-gray-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all duration-200 font-mono text-sm"></textarea>
              <small class="text-gray-500 mt-1 block">
                <span class="font-semibold">Example:</span> Server=localhost;Database=mydb;User Id=user;Password=pass;
              </small>
            </div>
            
            <div class="flex gap-3 pt-2">
              <button 
                (click)="testNewConnection()"
                [disabled]="!newConnection.name || !newConnection.connection_string"
                class="flex-1 flex items-center justify-center gap-2 bg-gray-600 text-white px-4 py-3 rounded-lg hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 shadow-md hover:shadow-lg">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                </svg>
                Test Connection
              </button>
              <button 
                (click)="saveConnection()"
                [disabled]="!newConnection.name || !newConnection.connection_string"
                class="flex-1 flex items-center justify-center gap-2 bg-gradient-to-r from-green-600 to-emerald-600 text-white px-4 py-3 rounded-lg hover:from-green-700 hover:to-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 shadow-md hover:shadow-lg">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
                </svg>
                Save Connection
              </button>
            </div>
            
            <div *ngIf="message" 
                 class="mt-4 px-4 py-3 rounded-lg flex items-center gap-2"
                 [ngClass]="{
                   'bg-green-100 text-green-800 border border-green-200': messageType === 'success', 
                   'bg-red-100 text-red-800 border border-red-200': messageType === 'error'
                 }">
              <svg *ngIf="messageType === 'success'" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
              </svg>
              <svg *ngIf="messageType === 'error'" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
              </svg>
              {{ message }}
            </div>
          </div>
        </div>
        
        <!-- Selected Connection Actions -->
        <div *ngIf="selectedConnectionId" class="bg-gray-50 rounded-lg p-4">
          <p class="text-sm font-semibold text-gray-700 mb-3">Connection Actions</p>
          <div class="flex gap-3">
            <button 
              (click)="testConnection()"
              class="flex-1 flex items-center justify-center gap-2 bg-gray-600 text-white px-4 py-2.5 rounded-lg hover:bg-gray-700 transition-all duration-200 shadow hover:shadow-md">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
              </svg>
              Test
            </button>
            <button 
              (click)="deleteConnection()"
              class="flex-1 flex items-center justify-center gap-2 bg-red-600 text-white px-4 py-2.5 rounded-lg hover:bg-red-700 transition-all duration-200 shadow hover:shadow-md">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
              </svg>
              Delete
            </button>
          </div>
        </div>
      </div>
    </div>
  `,
  styles: []
})
export class ConnectionManagerComponent implements OnInit {
  @Output() connectionSelected = new EventEmitter<number>();
  
  connections: Connection[] = [];
  selectedConnectionId: number | null = null;
  showAddForm = false;
  newConnection: Connection = {
    name: '',
    connection_string: '',
    database_type: 'mssql',
    is_active: true
  };
  message = '';
  messageType: 'success' | 'error' = 'success';
  
  constructor(
    private apiService: ApiService,
    private toastr: ToastrService,
    private storageService: StorageService
  ) {}
  
  ngOnInit() {
    // Check if we have cached connections first
    const cached = this.storageService.getConnectionList();
    if (cached && this.storageService.isConnectionListCacheValid()) {
      this.connections = cached.connections;
      
      // Restore selected connection
      const savedConnectionId = this.storageService.getSelectedConnection();
      if (savedConnectionId && this.connections.some(c => c.id === savedConnectionId)) {
        this.selectedConnectionId = savedConnectionId;
        this.connectionSelected.emit(savedConnectionId);
      }
    }
    
    // Always load fresh connections from server
    this.loadConnections();
  }
  
  loadConnections() {
    this.apiService.getConnections().subscribe({
      next: (connections) => {
        this.connections = connections;
        
        // Save to cache
        this.storageService.saveConnectionList(connections);
        
        // If we have a saved connection that wasn't in cache, restore it
        const savedConnectionId = this.storageService.getSelectedConnection();
        if (savedConnectionId && !this.selectedConnectionId && connections.some(c => c.id === savedConnectionId)) {
          this.selectedConnectionId = savedConnectionId;
          this.connectionSelected.emit(savedConnectionId);
        }
        
        if (connections.length === 0) {
          this.toastr.info('No connections found. Please add a new connection.', 'Info');
        }
      },
      error: (err) => {
        this.toastr.error('Failed to load connections', 'Error');
        this.showMessage('Failed to load connections', 'error');
      }
    });
  }
  
  onConnectionSelect() {
    if (this.selectedConnectionId) {
      this.connectionSelected.emit(this.selectedConnectionId);
      // Save selected connection to local storage
      this.storageService.saveSelectedConnection(this.selectedConnectionId);
    }
  }
  
  testNewConnection() {
    // For testing new connection, we need to save it temporarily
    this.toastr.info('Testing connection...', 'Testing');
    this.showMessage('Testing connection...', 'success');
    
    // This is a simplified version - in production, you'd want a separate test endpoint
    this.apiService.createConnection(this.newConnection).subscribe({
      next: (conn) => {
        this.apiService.testConnection(conn.id!).subscribe({
          next: (result) => {
            if (result.success) {
              this.toastr.success('Connection test successful! Database is reachable.', 'Success');
              this.showMessage('Connection successful!', 'success');
            } else {
              this.toastr.error(result.message, 'Connection Failed');
              this.showMessage(result.message, 'error');
            }
            // Delete the test connection
            this.apiService.deleteConnection(conn.id!).subscribe();
          },
          error: () => {
            this.toastr.error('Connection test failed. Please check your connection string.', 'Error');
            this.showMessage('Connection test failed', 'error');
            this.apiService.deleteConnection(conn.id!).subscribe();
          }
        });
      },
      error: (err) => {
        const message = err.error?.detail || 'Connection test failed';
        this.toastr.error(message, 'Error');
        this.showMessage(message, 'error');
      }
    });
  }
  
  saveConnection() {
    this.apiService.createConnection(this.newConnection).subscribe({
      next: (conn) => {
        this.connections.push(conn);
        this.toastr.success(`Connection "${conn.name}" saved successfully!`, 'Success');
        this.showMessage('Connection saved successfully', 'success');
        this.showAddForm = false;
        this.resetNewConnection();
        this.selectedConnectionId = conn.id!;
        this.onConnectionSelect();
        
        // Load enums if available
        this.loadEnumsForConnection(conn.id!);
      },
      error: (err) => {
        const message = err.error?.detail || 'Failed to save connection';
        this.toastr.error(message, 'Error');
        this.showMessage(message, 'error');
      }
    });
  }
  
  testConnection() {
    if (!this.selectedConnectionId) return;
    
    this.toastr.info('Testing connection...', 'Testing');
    
    this.apiService.testConnection(this.selectedConnectionId).subscribe({
      next: (result) => {
        if (result.success) {
          this.toastr.success('Connection test successful! Database is reachable.', 'Success');
          this.showMessage('Connection successful!', 'success');
        } else {
          this.toastr.error(result.message, 'Connection Failed');
          this.showMessage(result.message, 'error');
        }
      },
      error: () => {
        this.toastr.error('Connection test failed. Please check your connection string.', 'Error');
        this.showMessage('Connection test failed', 'error');
      }
    });
  }
  
  deleteConnection() {
    if (!this.selectedConnectionId || !confirm('Are you sure you want to delete this connection?')) {
      return;
    }
    
    this.apiService.deleteConnection(this.selectedConnectionId).subscribe({
      next: () => {
        this.connections = this.connections.filter(c => c.id !== this.selectedConnectionId);
        this.selectedConnectionId = null;
        this.toastr.success('Connection deleted successfully', 'Success');
        this.showMessage('Connection deleted', 'success');
      },
      error: () => {
        this.toastr.error('Failed to delete connection', 'Error');
        this.showMessage('Failed to delete connection', 'error');
      }
    });
  }
  
  private loadEnumsForConnection(connectionId: number) {
    // Try to load enums from the default location
    const enumFilePath = '/home/rick/Downloads/api_enums.json';
    
    // This would be better as a separate API call, but for now we'll just log
    console.log(`Consider loading enums for connection ${connectionId} from ${enumFilePath}`);
  }
  
  private resetNewConnection() {
    this.newConnection = {
      name: '',
      connection_string: '',
      database_type: 'mssql',
      is_active: true
    };
  }
  
  private showMessage(message: string, type: 'success' | 'error') {
    this.message = message;
    this.messageType = type;
    setTimeout(() => {
      this.message = '';
    }, 5000);
  }
}