import { Component, OnInit, OnDestroy } from '@angular/core';
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
    <div class="bg-white rounded-lg shadow-md p-4 h-full">
      <div class="flex justify-between items-center mb-3">
        <h3 class="text-lg font-semibold">Cache Performance</h3>
        <div class="flex gap-2">
          <button 
            (click)="warmCache()"
            [disabled]="warming"
            class="bg-green-500 text-white px-3 py-1 rounded text-sm hover:bg-green-600 disabled:opacity-50">
            {{ warming ? 'Warming...' : 'Warm Cache' }}
          </button>
          <button 
            (click)="invalidateCache()"
            [disabled]="invalidating"
            class="bg-red-500 text-white px-3 py-1 rounded text-sm hover:bg-red-600 disabled:opacity-50">
            {{ invalidating ? 'Clearing...' : 'Clear Cache' }}
          </button>
        </div>
      </div>
      
      <div *ngIf="stats" class="space-y-3">
        <!-- Connection Status -->
        <div class="flex items-center justify-between">
          <span class="text-sm text-gray-600">Redis Status</span>
          <span [class]="stats.connected ? 'text-green-600' : 'text-red-600'" class="font-medium">
            {{ stats.connected ? '🟢 Connected' : '🔴 Disconnected' }}
          </span>
        </div>
        
        <!-- Hit Rate -->
        <div class="flex items-center justify-between">
          <span class="text-sm text-gray-600">Cache Hit Rate</span>
          <div class="flex items-center gap-2">
            <div class="w-32 bg-gray-200 rounded-full h-2">
              <div 
                class="bg-blue-500 h-2 rounded-full transition-all duration-300"
                [style.width.%]="(stats.hit_rate * 100)">
              </div>
            </div>
            <span class="text-sm font-medium">{{ (stats.hit_rate * 100).toFixed(1) }}%</span>
          </div>
        </div>
        
        <!-- Memory Usage -->
        <div class="flex items-center justify-between">
          <span class="text-sm text-gray-600">Memory Usage</span>
          <span class="text-sm font-medium">{{ stats.used_memory_human }}</span>
        </div>
        
        <!-- Cached Items -->
        <div class="border-t pt-3">
          <div class="text-sm font-medium text-gray-700 mb-2">Cached Items</div>
          <div class="grid grid-cols-2 gap-2 text-xs">
            <div class="flex justify-between">
              <span class="text-gray-600">Schemas:</span>
              <span class="font-medium">{{ stats.cached_keys.schemas }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-600">Enums:</span>
              <span class="font-medium">{{ stats.cached_keys.enums }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-600">SQL Queries:</span>
              <span class="font-medium">{{ stats.cached_keys.sql_queries }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-600">Results:</span>
              <span class="font-medium">{{ stats.cached_keys.query_results }}</span>
            </div>
          </div>
        </div>
        
        <!-- Stats -->
        <div class="border-t pt-3 text-xs text-gray-500">
          <div>Total Commands: {{ stats.total_commands_processed }}</div>
          <div>Hits: {{ stats.keyspace_hits }} | Misses: {{ stats.keyspace_misses }}</div>
        </div>
      </div>
      
      <div *ngIf="!stats" class="text-center py-4">
        <div class="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500"></div>
      </div>
    </div>
  `
})
export class CacheStatsComponent implements OnInit, OnDestroy {
  stats: CacheStats | null = null;
  warming = false;
  invalidating = false;
  
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
}