import { Component, OnInit, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ToastrService } from 'ngx-toastr';
import { ApiService, Connection } from '../../services/api.service';

@Component({
  selector: 'app-connection-manager',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="bg-white rounded-lg shadow-md p-6">
      <h2 class="text-xl font-bold mb-4">Database Connections</h2>
      
      <!-- Connection List -->
      <div class="mb-4">
        <select 
          [(ngModel)]="selectedConnectionId"
          (change)="onConnectionSelect()"
          class="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500">
          <option [value]="null">Select a connection...</option>
          <option *ngFor="let conn of connections" [value]="conn.id">
            {{ conn.name }} ({{ conn.database_type }})
          </option>
        </select>
      </div>
      
      <!-- Add New Connection -->
      <div class="mb-4">
        <button 
          (click)="showAddForm = !showAddForm"
          class="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600">
          {{ showAddForm ? 'Cancel' : 'Add New Connection' }}
        </button>
      </div>
      
      <!-- New Connection Form -->
      <div *ngIf="showAddForm" class="border-t pt-4">
        <h3 class="text-lg font-semibold mb-3">New Connection</h3>
        <div class="space-y-3">
          <div>
            <label class="block text-sm font-medium mb-1">Connection Name</label>
            <input 
              [(ngModel)]="newConnection.name"
              type="text"
              placeholder="My Database"
              class="w-full p-2 border border-gray-300 rounded-md">
          </div>
          
          <div>
            <label class="block text-sm font-medium mb-1">Connection String</label>
            <textarea 
              [(ngModel)]="newConnection.connection_string"
              placeholder="Server=localhost;Database=mydb;User Id=user;Password=pass;"
              rows="3"
              class="w-full p-2 border border-gray-300 rounded-md"></textarea>
            <small class="text-gray-500">
              Example: Server=localhost;Database=mydb;User Id=user;Password=pass;
            </small>
          </div>
          
          <div class="flex gap-2">
            <button 
              (click)="testNewConnection()"
              [disabled]="!newConnection.name || !newConnection.connection_string"
              class="bg-gray-500 text-white px-4 py-2 rounded hover:bg-gray-600 disabled:opacity-50">
              Test Connection
            </button>
            <button 
              (click)="saveConnection()"
              [disabled]="!newConnection.name || !newConnection.connection_string"
              class="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600 disabled:opacity-50">
              Save Connection
            </button>
          </div>
          
          <div *ngIf="message" 
               [ngClass]="{'text-green-600': messageType === 'success', 'text-red-600': messageType === 'error'}"
               class="mt-2">
            {{ message }}
          </div>
        </div>
      </div>
      
      <!-- Selected Connection Actions -->
      <div *ngIf="selectedConnectionId" class="border-t pt-4 mt-4">
        <div class="flex gap-2">
          <button 
            (click)="testConnection()"
            class="bg-gray-500 text-white px-4 py-2 rounded hover:bg-gray-600">
            Test Connection
          </button>
          <button 
            (click)="deleteConnection()"
            class="bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600">
            Delete Connection
          </button>
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
    private toastr: ToastrService
  ) {}
  
  ngOnInit() {
    this.loadConnections();
  }
  
  loadConnections() {
    this.apiService.getConnections().subscribe({
      next: (connections) => {
        this.connections = connections;
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