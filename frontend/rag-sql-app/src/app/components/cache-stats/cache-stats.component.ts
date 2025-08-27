import { Component, OnInit, OnDestroy, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService, CacheStats } from '../../services/api.service';
import { ToastrService } from 'ngx-toastr';
import { interval, Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

@Component({
  selector: 'app-cache-stats',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="bg-white rounded-xl shadow-lg border border-gray-100 overflow-hidden h-full">
      <!-- Header -->
      <div class="bg-gradient-to-r from-purple-600 to-indigo-600 px-3 py-2">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2">
            <svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path>
            </svg>
            <h3 class="text-sm font-semibold text-white">Cache Performance</h3>
          </div>
          <span class="bg-white/20 text-white px-2 py-0.5 rounded-full text-xs">
            {{ stats?.connected ? 'Active' : 'Offline' }}
          </span>
        </div>
      </div>
      
      <div class="p-3">
        <!-- Action Buttons -->
        <div class="flex gap-1 mb-2">
          <button 
            (click)="refreshAllMetadata()"
            [disabled]="refreshingAll"
            title="Refresh all database metadata (schemas, enums, documentation)"
            class="flex-1 flex items-center justify-center gap-1 bg-blue-600 text-white px-2 py-1 rounded text-xs font-medium hover:bg-blue-700 disabled:opacity-50 transition-all duration-200">
            <svg *ngIf="!refreshingAll" class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
            </svg>
            <svg *ngIf="refreshingAll" class="animate-spin w-3 h-3" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="m4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            Refresh
          </button>
          <button 
            (click)="warmCache()"
            [disabled]="warming"
            title="Pre-load cache with hints and patterns"
            class="flex-1 flex items-center justify-center gap-1 bg-green-600 text-white px-2 py-1 rounded text-xs font-medium hover:bg-green-700 disabled:opacity-50 transition-all duration-200">
            <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path>
            </svg>
            Warm
          </button>
          <button 
            (click)="invalidateCache()"
            [disabled]="invalidating"
            title="Clear all cached data"
            class="flex-1 flex items-center justify-center gap-1 bg-gray-600 text-white px-2 py-1 rounded text-xs font-medium hover:bg-gray-700 disabled:opacity-50 transition-all duration-200">
            <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
            </svg>
            Clear
          </button>
        </div>
        
        <div *ngIf="stats" class="space-y-2">
          <!-- Hit Rate Card -->
          <div class="bg-gradient-to-r from-blue-50 to-indigo-50 rounded p-2 border border-blue-200">
            <div class="flex items-center justify-between mb-1">
              <span class="text-xs font-semibold text-gray-700">Cache Hit Rate</span>
              <span class="text-lg font-bold text-blue-600">{{ (stats.hit_rate * 100).toFixed(1) }}%</span>
            </div>
            <div class="w-full bg-white rounded-full h-2 shadow-inner">
              <div 
                class="bg-gradient-to-r from-blue-500 to-indigo-500 h-2 rounded-full transition-all duration-500"
                [style.width.%]="(stats.hit_rate * 100)">
              </div>
            </div>
            <div class="flex justify-between mt-1 text-xs text-gray-600">
              <span>Hits: {{ stats.keyspace_hits }}</span>
              <span>Misses: {{ stats.keyspace_misses }}</span>
            </div>
          </div>
          
          <!-- Memory Usage Card -->
          <div class="bg-gradient-to-r from-purple-50 to-indigo-50 rounded p-2 border border-purple-200">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-xs font-semibold text-gray-700">Memory Usage</p>
                <p class="text-xs text-gray-500">Commands: {{ stats.total_commands_processed }}</p>
              </div>
              <div class="text-right">
                <p class="text-lg font-bold text-purple-600">{{ stats.used_memory_human }}</p>
                <p class="text-xs text-gray-500">Redis</p>
              </div>
            </div>
          </div>
          
          <!-- Cached Items Grid -->
          <div class="bg-gradient-to-r from-teal-50 to-cyan-50 rounded p-2 border border-teal-200">
            <h4 class="text-xs font-semibold text-gray-700 mb-1">Cached Items</h4>
            <div class="grid grid-cols-2 gap-1">
              <div class="bg-white rounded p-1 border border-teal-100">
                <div class="flex items-center justify-between">
                  <span class="text-xs text-gray-600">Schemas</span>
                  <span class="text-sm font-bold text-teal-600">{{ stats.cached_keys.schemas }}</span>
                </div>
              </div>
              <div class="bg-white rounded p-1 border border-cyan-100">
                <div class="flex items-center justify-between">
                  <span class="text-xs text-gray-600">Enums</span>
                  <span class="text-sm font-bold text-cyan-600">{{ stats.cached_keys.enums }}</span>
                </div>
              </div>
              <div class="bg-white rounded p-1 border border-teal-100">
                <div class="flex items-center justify-between">
                  <span class="text-xs text-gray-600">Queries</span>
                  <span class="text-sm font-bold text-teal-600">{{ stats.cached_keys.sql_queries }}</span>
                </div>
              </div>
              <div class="bg-white rounded p-1 border border-cyan-100">
                <div class="flex items-center justify-between">
                  <span class="text-xs text-gray-600">Results</span>
                  <span class="text-sm font-bold text-cyan-600">{{ stats.cached_keys.query_results }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <!-- Loading State -->
        <div *ngIf="!stats" class="flex flex-col items-center justify-center py-6">
          <div class="relative">
            <div class="animate-spin rounded-full h-8 w-8 border-3 border-gray-200"></div>
            <div class="animate-spin rounded-full h-8 w-8 border-3 border-blue-500 border-t-transparent absolute top-0"></div>
          </div>
          <p class="text-gray-500 text-xs mt-2">Loading cache statistics...</p>
        </div>
      </div>
    </div>
  `
})
export class CacheStatsComponent implements OnInit, OnDestroy {
  @Input() currentConnectionId: number | null = null;
  
  stats: CacheStats | null = null;
  warming = false;
  invalidating = false;
  refreshingAll = false;
  
  private destroy$ = new Subject<void>();
  
  constructor(
    private apiService: ApiService,
    private toastr: ToastrService
  ) {}
  
  ngOnInit() {
    this.loadStats();
    
    // Refresh stats every 10 seconds
    interval(10000)
      .pipe(takeUntil(this.destroy$))
      .subscribe(() => this.loadStats());
  }
  
  ngOnDestroy() {
    this.destroy$.next();
    this.destroy$.complete();
  }
  
  loadStats() {
    this.apiService.getCacheStats().subscribe({
      next: (stats) => {
        this.stats = stats;
      },
      error: (err) => {
        console.error('Failed to load cache stats:', err);
      }
    });
  }
  
  warmCache() {
    this.warming = true;
    this.apiService.warmCache().subscribe({
      next: (result) => {
        this.toastr.success(
          `Loaded ${result.hints_loaded} hints and ${result.patterns_loaded} patterns`,
          'Cache Warmed'
        );
        this.warming = false;
        this.loadStats();
      },
      error: (err) => {
        this.toastr.error('Failed to warm cache', 'Error');
        this.warming = false;
      }
    });
  }
  
  invalidateCache() {
    if (!confirm('Clear all cached data? This may temporarily slow down queries.')) return;
    
    this.invalidating = true;
    this.apiService.invalidateCache().subscribe({
      next: (result) => {
        this.toastr.success(`Cleared ${result.deleted} cache entries`, 'Cache Cleared');
        this.invalidating = false;
        this.loadStats();
      },
      error: (err) => {
        this.toastr.error('Failed to clear cache', 'Error');
        this.invalidating = false;
      }
    });
  }
  
  async refreshAllMetadata() {
    if (!this.currentConnectionId) {
      this.toastr.warning('Please select a database connection first', 'No Connection');
      return;
    }
    
    this.refreshingAll = true;
    let refreshedCount = 0;
    
    try {
      // 1. Refresh documentation (which includes schema information)
      await this.apiService.refreshDocumentation(this.currentConnectionId).toPromise();
      refreshedCount++;
      
      // 2. Clear and reload enums by invalidating connection-specific cache
      await this.apiService.invalidateCache(this.currentConnectionId).toPromise();
      refreshedCount++;
      
      // 3. Warm cache with fresh data
      await this.apiService.warmCache().toPromise();
      refreshedCount++;
      
      // Reload stats to show updated cache
      this.loadStats();
      
      this.toastr.success(
        'All database metadata refreshed! Fresh schemas, enums, and documentation are now available.',
        'Complete Refresh Done'
      );
      
    } catch (err: any) {
      const errorMsg = err.error?.detail || 'Failed to refresh all metadata';
      this.toastr.error(errorMsg, 'Refresh Failed');
    } finally {
      this.refreshingAll = false;
    }
  }
}