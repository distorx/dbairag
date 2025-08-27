import { Component, OnInit, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';
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
                {{ getDatabaseIcon(conn.database_type) }} {{ conn.name }}
              </option>
            </select>
            <svg class="absolute left-3 top-2.5 w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path>
            </svg>
            <svg class="absolute right-3 top-3 w-4 h-4 text-gray-400 pointer-events-none" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
            </svg>
          </div>
          
          <!-- Selected Connection Info -->
          <div *ngIf="selectedConnectionId && getSelectedConnection()" class="mt-2 flex items-center gap-2 text-xs text-gray-600">
            <div [innerHTML]="getDatabaseIconSvg(getSelectedConnection()!.database_type)" class="w-4 h-4"></div>
            <span class="font-medium">{{ getDatabaseTypeName(getSelectedConnection()!.database_type) }} Database</span>
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
              <label class="block text-sm font-semibold text-gray-700 mb-2">Database Type</label>
              <select 
                [(ngModel)]="newConnection.database_type"
                class="w-full px-4 py-3 bg-white border border-gray-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all duration-200">
                <option value="mssql">{{ getDatabaseIcon('mssql') }} Microsoft SQL Server</option>
                <option value="sqlite">{{ getDatabaseIcon('sqlite') }} SQLite</option>
                <option value="mysql">{{ getDatabaseIcon('mysql') }} MySQL</option>
                <option value="postgresql">{{ getDatabaseIcon('postgresql') }} PostgreSQL</option>
                <option value="mongodb">{{ getDatabaseIcon('mongodb') }} MongoDB</option>
                <option value="oracle">{{ getDatabaseIcon('oracle') }} Oracle</option>
              </select>
            </div>
            
            <div>
              <label class="block text-sm font-semibold text-gray-700 mb-2">Connection String</label>
              <textarea 
                [(ngModel)]="newConnection.connection_string"
                [placeholder]="getConnectionStringPlaceholder()"
                rows="3"
                class="w-full px-4 py-3 bg-white border border-gray-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all duration-200 font-mono text-sm"></textarea>
              <small class="text-gray-500 mt-1 block">
                <span class="font-semibold">Example:</span> {{ getConnectionStringExample() }}
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
          <div class="grid grid-cols-2 gap-2">
            <button 
              (click)="testConnection()"
              class="flex items-center justify-center gap-1.5 bg-gray-600 text-white px-3 py-2 text-sm rounded-lg hover:bg-gray-700 transition-all duration-200 shadow hover:shadow-md">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
              </svg>
              Test
            </button>
            <button 
              (click)="editConnection()"
              class="flex items-center justify-center gap-1.5 bg-blue-600 text-white px-3 py-2 text-sm rounded-lg hover:bg-blue-700 transition-all duration-200 shadow hover:shadow-md">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"></path>
              </svg>
              Edit
            </button>
            <button 
              (click)="disconnectConnection()"
              class="flex items-center justify-center gap-1.5 bg-orange-600 text-white px-3 py-2 text-sm rounded-lg hover:bg-orange-700 transition-all duration-200 shadow hover:shadow-md">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path>
              </svg>
              Disconnect
            </button>
            <button 
              (click)="deleteConnection()"
              class="flex items-center justify-center gap-1.5 bg-red-600 text-white px-3 py-2 text-sm rounded-lg hover:bg-red-700 transition-all duration-200 shadow hover:shadow-md">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
              </svg>
              Delete
            </button>
          </div>
        </div>
        
        <!-- Edit Connection Form -->
        <div *ngIf="showEditForm" class="bg-gradient-to-br from-blue-50 to-cyan-50 rounded-lg p-4 border border-blue-200 mt-3">
          <h3 class="text-sm font-bold text-gray-800 mb-3 flex items-center gap-2">
            <svg class="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"></path>
            </svg>
            Edit Connection
          </h3>
          <div class="space-y-3">
            <div>
              <label class="block text-xs font-semibold text-gray-700 mb-1">Connection Name</label>
              <input 
                [(ngModel)]="editingConnection.name"
                type="text"
                placeholder="My Database"
                class="w-full px-3 py-2 bg-white border border-gray-200 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 text-sm">
            </div>
            
            <div>
              <label class="block text-xs font-semibold text-gray-700 mb-1">Connection String</label>
              <textarea 
                [(ngModel)]="editingConnection.connection_string"
                placeholder="Server=localhost;Database=mydb;User Id=user;Password=pass;"
                rows="4"
                class="w-full px-3 py-2 bg-white border border-gray-200 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 font-mono text-xs resize-none"></textarea>
              <small class="text-gray-500 mt-1 block text-xs">
                <span class="font-semibold">Example:</span> Server=localhost;Database=mydb;User Id=user;Password=pass;
              </small>
            </div>
            
            <div class="flex gap-2 pt-1">
              <button 
                (click)="testEditingConnection()"
                [disabled]="!editingConnection.name || !editingConnection.connection_string || testingConnection"
                class="flex-1 flex items-center justify-center gap-1.5 bg-gray-600 text-white px-3 py-2 rounded text-sm hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 shadow hover:shadow-md">
                <svg *ngIf="!testingConnection" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                </svg>
                <svg *ngIf="testingConnection" class="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                {{ testingConnection ? 'Testing...' : 'Test Connection' }}
              </button>
              <button 
                (click)="saveEditedConnection()"
                [disabled]="!editingConnection.name || !editingConnection.connection_string || savingConnection"
                class="flex-1 flex items-center justify-center gap-1.5 bg-gradient-to-r from-blue-600 to-cyan-600 text-white px-3 py-2 rounded text-sm hover:from-blue-700 hover:to-cyan-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 shadow hover:shadow-md">
                <svg *ngIf="!savingConnection" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
                </svg>
                <svg *ngIf="savingConnection" class="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                {{ savingConnection ? 'Updating...' : 'Update Connection' }}
              </button>
              <button 
                (click)="cancelEdit()"
                [disabled]="savingConnection || testingConnection"
                class="flex-1 flex items-center justify-center gap-1.5 bg-gray-500 text-white px-3 py-2 rounded text-sm hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 shadow hover:shadow-md">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                </svg>
                Cancel
              </button>
            </div>
            
            <div *ngIf="editMessage" 
                 class="mt-4 px-4 py-3 rounded-lg flex items-center gap-2"
                 [ngClass]="{
                   'bg-green-100 text-green-800 border border-green-200': editMessageType === 'success', 
                   'bg-red-100 text-red-800 border border-red-200': editMessageType === 'error'
                 }">
              <svg *ngIf="editMessageType === 'success'" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
              </svg>
              <svg *ngIf="editMessageType === 'error'" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
              </svg>
              {{ editMessage }}
            </div>
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
  showEditForm = false;
  newConnection: Connection = {
    name: '',
    connection_string: '',
    database_type: 'mssql',
    is_active: true
  };
  editingConnection: Connection = {
    name: '',
    connection_string: '',
    database_type: 'mssql',
    is_active: true
  };
  message = '';
  messageType: 'success' | 'error' = 'success';
  editMessage = '';
  editMessageType: 'success' | 'error' = 'success';
  testingConnection = false;
  savingConnection = false;
  
  constructor(
    private apiService: ApiService,
    private toastr: ToastrService,
    private storageService: StorageService,
    private sanitizer: DomSanitizer
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
        // Clear from storage
        this.storageService.clearSelectedConnection();
      },
      error: () => {
        this.toastr.error('Failed to delete connection', 'Error');
        this.showMessage('Failed to delete connection', 'error');
      }
    });
  }
  
  disconnectConnection() {
    if (!this.selectedConnectionId) return;
    
    const connectionName = this.connections.find(c => c.id === this.selectedConnectionId)?.name;
    this.selectedConnectionId = null;
    this.connectionSelected.emit(0); // Emit 0 or null to indicate no connection
    
    // Clear from storage
    this.storageService.clearSelectedConnection();
    
    // Clear any open forms
    this.showEditForm = false;
    this.showAddForm = false;
    
    this.toastr.info(`Disconnected from "${connectionName}"`, 'Disconnected');
    this.showMessage('Connection disconnected', 'success');
  }
  
  editConnection() {
    if (!this.selectedConnectionId) return;
    
    const connection = this.connections.find(c => c.id === this.selectedConnectionId);
    if (connection) {
      this.editingConnection = { ...connection };
      this.showEditForm = true;
      this.showAddForm = false; // Close add form if open
      this.editMessage = '';
    }
  }
  
  cancelEdit() {
    this.showEditForm = false;
    this.editingConnection = {
      name: '',
      connection_string: '',
      database_type: 'mssql',
      is_active: true
    };
    this.editMessage = '';
  }
  
  testEditingConnection() {
    this.testingConnection = true;
    this.toastr.info('Testing connection...', 'Testing');
    this.showEditMessage('Testing connection...', 'success');
    
    // Create a temporary connection object for testing
    const testConnection = { ...this.editingConnection };
    
    // For testing, we need to create a temporary connection
    this.apiService.createConnection(testConnection).subscribe({
      next: (tempConn) => {
        this.apiService.testConnection(tempConn.id!).subscribe({
          next: (result) => {
            if (result.success) {
              this.toastr.success('Connection test successful! Database is reachable.', 'Success');
              this.showEditMessage('Connection successful!', 'success');
            } else {
              this.toastr.error(result.message, 'Connection Failed');
              this.showEditMessage(result.message, 'error');
            }
            this.testingConnection = false;
            // Delete the temporary connection
            this.apiService.deleteConnection(tempConn.id!).subscribe();
          },
          error: () => {
            this.toastr.error('Connection test failed. Please check your connection string.', 'Error');
            this.showEditMessage('Connection test failed', 'error');
            this.testingConnection = false;
            this.apiService.deleteConnection(tempConn.id!).subscribe();
          }
        });
      },
      error: (err) => {
        const message = err.error?.detail || 'Connection test failed';
        this.toastr.error(message, 'Error');
        this.showEditMessage(message, 'error');
        this.testingConnection = false;
      }
    });
  }
  
  saveEditedConnection() {
    if (!this.selectedConnectionId || !this.editingConnection.name || !this.editingConnection.connection_string) {
      return;
    }
    
    this.savingConnection = true;
    this.apiService.updateConnection(this.selectedConnectionId, this.editingConnection).subscribe({
      next: (updatedConn) => {
        // Update the connection in the list
        const index = this.connections.findIndex(c => c.id === this.selectedConnectionId);
        if (index !== -1) {
          this.connections[index] = updatedConn;
        }
        
        this.toastr.success(`Connection "${updatedConn.name}" updated successfully!`, 'Success');
        this.showEditMessage('Connection updated successfully', 'success');
        
        // Close the edit form after a short delay
        setTimeout(() => {
          this.showEditForm = false;
          this.cancelEdit();
          this.savingConnection = false;
        }, 1500);
        
        // Update cache
        this.storageService.saveConnectionList(this.connections);
      },
      error: (err) => {
        const message = err.error?.detail || 'Failed to update connection';
        this.toastr.error(message, 'Error');
        this.showEditMessage(message, 'error');
        this.savingConnection = false;
      }
    });
  }
  
  private showEditMessage(message: string, type: 'success' | 'error') {
    this.editMessage = message;
    this.editMessageType = type;
    setTimeout(() => {
      this.editMessage = '';
    }, 5000);
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
  
  getSelectedConnection(): Connection | undefined {
    return this.connections.find(c => c.id === this.selectedConnectionId);
  }
  
  getDatabaseIcon(dbType: string): string {
    switch(dbType?.toLowerCase()) {
      case 'mssql':
      case 'sqlserver':
        return '🔷';  // SQL Server icon (blue diamond)
      case 'sqlite':
        return '🟢';  // SQLite icon (green circle)
      case 'mysql':
        return '🟠';  // MySQL icon (orange circle)
      case 'postgresql':
      case 'postgres':
        return '🟣';  // PostgreSQL icon (purple circle)
      case 'mongodb':
        return '🍃';  // MongoDB icon (leaf)
      case 'oracle':
        return '🔴';  // Oracle icon (red circle)
      default:
        return '⚫';  // Generic database icon (black circle)
    }
  }
  
  getDatabaseIconSvg(dbType: string): SafeHtml {
    let svg = '';
    switch(dbType?.toLowerCase()) {
      case 'mssql':
      case 'sqlserver':
        svg = `<svg class="w-4 h-4 text-blue-500" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8z"/>
          <path d="M8 8h8v2H8zm0 3h8v2H8zm0 3h5v2H8z"/>
        </svg>`;
        break;
      case 'sqlite':
        svg = `<svg class="w-4 h-4 text-teal-500" viewBox="0 0 24 24" fill="currentColor">
          <path d="M21 6l-3-3H6c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V8l-2-2h-2V4H8v12h8V8h2l3 3v8c0 1.7-1.3 3-3 3H6c-1.7 0-3-1.3-3-3V5c0-1.7 1.3-3 3-3h12l3 3v1z"/>
        </svg>`;
        break;
      case 'mysql':
        svg = `<svg class="w-4 h-4 text-orange-500" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 3C7.58 3 4 4.79 4 7v10c0 2.21 3.59 4 8 4s8-1.79 8-4V7c0-2.21-3.58-4-8-4zm6 14c0 .5-2.13 2-6 2s-6-1.5-6-2v-2.23c1.61.78 3.72 1.23 6 1.23s4.39-.45 6-1.23V17zm0-4.55c-1.3.95-3.58 1.55-6 1.55s-4.7-.6-6-1.55V9.64c1.47.83 3.61 1.36 6 1.36s4.53-.53 6-1.36v2.81zM12 9C8.13 9 6 7.5 6 7s2.13-2 6-2 6 1.5 6 2-2.13 2-6 2z"/>
        </svg>`;
        break;
      case 'postgresql':
      case 'postgres':
        svg = `<svg class="w-4 h-4 text-purple-500" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 2c5.514 0 10 3.592 10 8.007 0 4.917-5.145 7.961-9.91 7.961-1.937 0-3.383-.397-4.394-.644-1.043-.256-1.336-.744-1.336-1.324 0-.802.355-1.278 1.521-1.436.796-.108 1.227-.142 1.746-.223.877-.135 1.432-.36 1.866-.727-.413.364-1.125.603-2.119.722-.979.117-1.835.182-1.835.764 0 1.235 2.204 1.9 5.461 1.9 4.268 0 8-2.582 8-5.993C20 5.703 16.418 3 12 3c-4.418 0-8 2.703-8 6.007 0 .748.184 1.448.512 2.077-.192-.232-.312-.502-.312-.82 0-1.408 1.149-2.264 1.375-2.482-.058.22-.095.475-.095.755 0 2.066 1.741 2.74 3.094 2.74.395 0 .727-.066 1.006-.158-.271.177-.621.381-1.08.381-1.164 0-2.5-1.051-2.5-3.493C6 4.598 8.686 2 12 2z"/>
        </svg>`;
        break;
      default:
        svg = `<svg class="w-4 h-4 text-purple-600" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 3C7.58 3 4 4.79 4 7s3.58 4 8 4 8-1.79 8-4-3.58-4-8-4zM4 9v3c0 2.21 3.58 4 8 4s8-1.79 8-4V9c0 2.21-3.58 4-8 4s-8-1.79-8-4zm0 5v3c0 2.21 3.58 4 8 4s8-1.79 8-4v-3c0 2.21-3.58 4-8 4s-8-1.79-8-4z"/>
        </svg>`;
    }
    return this.sanitizer.bypassSecurityTrustHtml(svg);
  }
  
  getDatabaseTypeName(dbType: string): string {
    switch(dbType?.toLowerCase()) {
      case 'mssql':
      case 'sqlserver':
        return 'SQL Server';
      case 'sqlite':
        return 'SQLite';
      case 'mysql':
        return 'MySQL';
      case 'postgresql':
      case 'postgres':
        return 'PostgreSQL';
      case 'mongodb':
        return 'MongoDB';
      case 'oracle':
        return 'Oracle';
      default:
        return dbType || 'Database';
    }
  }
  
  getConnectionStringPlaceholder(): string {
    switch(this.newConnection.database_type?.toLowerCase()) {
      case 'mssql':
        return 'Server=hostname;Database=dbname;User Id=username;Password=password;';
      case 'sqlite':
        return 'sqlite:///path/to/database.db or /absolute/path/to/database.db';
      case 'mysql':
        return 'mysql://username:password@hostname:3306/database';
      case 'postgresql':
        return 'postgresql://username:password@hostname:5432/database';
      case 'mongodb':
        return 'mongodb://username:password@hostname:27017/database';
      case 'oracle':
        return 'oracle://username:password@hostname:1521/service_name';
      default:
        return 'Enter your database connection string';
    }
  }
  
  getConnectionStringExample(): string {
    switch(this.newConnection.database_type?.toLowerCase()) {
      case 'mssql':
        return 'Server=localhost;Database=mydb;User Id=sa;Password=myPass123;';
      case 'sqlite':
        return 'sqlite:///./mydatabase.db';
      case 'mysql':
        return 'mysql://root:password@localhost:3306/mydb';
      case 'postgresql':
        return 'postgresql://postgres:password@localhost:5432/mydb';
      case 'mongodb':
        return 'mongodb://admin:password@localhost:27017/mydb';
      case 'oracle':
        return 'oracle://scott:tiger@localhost:1521/ORCL';
      default:
        return 'Select a database type for examples';
    }
  }
}