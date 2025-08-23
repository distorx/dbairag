import { Component, Input, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService, EnumFile } from '../../services/api.service';
import { ToastrService } from 'ngx-toastr';

@Component({
  selector: 'app-enum-manager',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="bg-white rounded-lg shadow-md p-4 h-full">
      <div class="flex justify-between items-center mb-3">
        <h3 class="text-lg font-semibold">Enum Files</h3>
        <button 
          (click)="toggleUpload()"
          class="bg-green-500 text-white px-3 py-1 rounded text-sm hover:bg-green-600">
          {{ showUpload ? 'Cancel' : 'Upload' }}
        </button>
      </div>
      
      <!-- Upload form -->
      <div *ngIf="showUpload" class="mb-4 p-3 bg-gray-50 rounded">
        <div class="mb-2">
          <label class="block text-sm font-medium text-gray-700 mb-1">
            Select JSON file
          </label>
          <input 
            type="file" 
            accept=".json"
            (change)="onFileSelected($event)"
            class="block w-full text-sm text-gray-500
              file:mr-4 file:py-2 file:px-4
              file:rounded file:border-0
              file:text-sm file:font-semibold
              file:bg-blue-50 file:text-blue-700
              hover:file:bg-blue-100">
        </div>
        <div class="mb-2">
          <label class="block text-sm font-medium text-gray-700 mb-1">
            Description (optional)
          </label>
          <input 
            type="text"
            [(ngModel)]="description"
            placeholder="e.g., Application status codes"
            class="w-full px-3 py-1 border border-gray-300 rounded text-sm">
        </div>
        <button 
          (click)="uploadFile()"
          [disabled]="!selectedFile || uploading"
          class="bg-blue-500 text-white px-4 py-2 rounded text-sm hover:bg-blue-600 disabled:opacity-50">
          {{ uploading ? 'Uploading...' : 'Upload File' }}
        </button>
      </div>
      
      <!-- Enum files list -->
      <div *ngIf="!loading && enumFiles.length === 0" class="text-center py-4 text-gray-500">
        No enum files uploaded yet
      </div>
      
      <div *ngIf="loading" class="text-center py-4">
        <div class="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500"></div>
      </div>
      
      <div class="space-y-2">
        <div *ngFor="let file of enumFiles" 
             class="flex items-center justify-between p-2 hover:bg-gray-50 rounded">
          <div class="flex-1">
            <div class="font-medium text-sm">{{ file.original_filename }}</div>
            <div class="text-xs text-gray-500">
              {{ file.description || 'No description' }}
            </div>
            <div class="text-xs text-gray-400">
              Uploaded: {{ file.created_at | date:'short' }}
            </div>
          </div>
          <button 
            (click)="deleteFile(file)"
            class="text-red-500 hover:text-red-700 p-1">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                    d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16">
              </path>
            </svg>
          </button>
        </div>
      </div>
    </div>
  `
})
export class EnumManagerComponent implements OnInit {
  @Input() connectionId!: number;
  
  enumFiles: EnumFile[] = [];
  loading = false;
  showUpload = false;
  uploading = false;
  selectedFile: File | null = null;
  description = '';
  
  constructor(
    private apiService: ApiService,
    private toastr: ToastrService
  ) {}
  
  ngOnInit() {
    this.loadEnumFiles();
  }
  
  loadEnumFiles() {
    if (!this.connectionId) return;
    
    this.loading = true;
    this.apiService.getEnumFiles(this.connectionId).subscribe({
      next: (files) => {
        this.enumFiles = files;
        this.loading = false;
      },
      error: (err) => {
        this.toastr.error('Failed to load enum files', 'Error');
        this.loading = false;
      }
    });
  }
  
  toggleUpload() {
    this.showUpload = !this.showUpload;
    if (!this.showUpload) {
      this.selectedFile = null;
      this.description = '';
    }
  }
  
  onFileSelected(event: any) {
    const file = event.target.files[0];
    if (file && file.type === 'application/json') {
      this.selectedFile = file;
    } else {
      this.toastr.error('Please select a valid JSON file', 'Invalid File');
      this.selectedFile = null;
    }
  }
  
  uploadFile() {
    if (!this.selectedFile || !this.connectionId) return;
    
    this.uploading = true;
    this.apiService.uploadEnumFile(
      this.connectionId, 
      this.selectedFile, 
      this.description
    ).subscribe({
      next: (file) => {
        this.toastr.success('Enum file uploaded successfully', 'Success');
        this.enumFiles.push(file);
        this.uploading = false;
        this.toggleUpload();
      },
      error: (err) => {
        this.toastr.error(err.error?.detail || 'Failed to upload file', 'Error');
        this.uploading = false;
      }
    });
  }
  
  deleteFile(file: EnumFile) {
    if (!confirm(`Delete enum file "${file.original_filename}"?`)) return;
    
    this.apiService.deleteEnumFile(this.connectionId, file.id).subscribe({
      next: () => {
        this.toastr.success('Enum file deleted', 'Success');
        this.enumFiles = this.enumFiles.filter(f => f.id !== file.id);
      },
      error: (err) => {
        this.toastr.error('Failed to delete file', 'Error');
      }
    });
  }
}