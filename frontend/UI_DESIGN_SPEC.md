# RAG SQL Query Notebook - Modern UI Design Specification

## Design Philosophy
A modern, clean, and professional interface that combines the power of SQL querying with the simplicity of natural language, inspired by leading data science tools like Jupyter, DataBricks, and modern SaaS applications.

## Color Palette

### Primary Colors
- **Primary Blue**: `#3B82F6` (blue-500) - Main actions, active states
- **Primary Dark**: `#1E40AF` (blue-800) - Headers, emphasis
- **Primary Light**: `#DBEAFE` (blue-100) - Backgrounds, hover states

### Secondary Colors
- **Success Green**: `#10B981` (emerald-500)
- **Warning Amber**: `#F59E0B` (amber-500)
- **Error Red**: `#EF4444` (red-500)
- **Info Purple**: `#8B5CF6` (violet-500)

### Neutral Colors
- **Background**: `#F9FAFB` (gray-50)
- **Surface**: `#FFFFFF` (white)
- **Border**: `#E5E7EB` (gray-200)
- **Text Primary**: `#111827` (gray-900)
- **Text Secondary**: `#6B7280` (gray-500)

## Typography

### Font Stack
```css
font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
font-family-mono: 'JetBrains Mono', 'Fira Code', Consolas, monospace;
```

### Size Scale
- **Display**: `text-4xl` (36px) - Main header
- **Title**: `text-2xl` (24px) - Section headers
- **Subtitle**: `text-lg` (18px) - Card headers
- **Body**: `text-base` (16px) - General content
- **Small**: `text-sm` (14px) - Secondary content
- **Tiny**: `text-xs` (12px) - Labels, hints

## Component Design

### 1. Enhanced Header
```html
<!-- Gradient header with glass effect -->
<header class="bg-gradient-to-r from-blue-600 to-blue-700 backdrop-blur-lg shadow-xl">
  <div class="px-6 py-5">
    <div class="flex items-center justify-between">
      <div class="flex items-center space-x-4">
        <div class="bg-white/10 backdrop-blur p-2 rounded-lg">
          <svg class="w-8 h-8 text-white"><!-- SQL icon --></svg>
        </div>
        <div>
          <h1 class="text-3xl font-bold text-white tracking-tight">RAG SQL Studio</h1>
          <p class="text-blue-100 text-sm mt-1">Intelligent Natural Language SQL Interface</p>
        </div>
      </div>
      <div class="flex items-center space-x-3">
        <!-- Status indicators -->
        <div class="flex items-center space-x-2 bg-white/10 backdrop-blur px-3 py-2 rounded-lg">
          <div class="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
          <span class="text-white text-sm">Connected</span>
        </div>
      </div>
    </div>
  </div>
</header>
```

### 2. Connection Manager Card (Enhanced)
```html
<div class="bg-white rounded-xl shadow-sm hover:shadow-lg transition-all duration-300 border border-gray-100">
  <div class="p-5">
    <div class="flex items-center justify-between mb-4">
      <h3 class="text-lg font-semibold text-gray-900 flex items-center gap-2">
        <div class="p-2 bg-blue-50 rounded-lg">
          <svg class="w-5 h-5 text-blue-600"><!-- Database icon --></svg>
        </div>
        Database Connection
      </h3>
      <span class="px-2 py-1 text-xs font-medium bg-green-100 text-green-700 rounded-full">
        Active
      </span>
    </div>
    
    <!-- Connection selector with better styling -->
    <select class="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-lg 
                   focus:ring-2 focus:ring-blue-500 focus:border-transparent
                   transition-colors text-gray-700">
      <option>Production Database</option>
    </select>
    
    <!-- Quick stats -->
    <div class="mt-4 grid grid-cols-2 gap-3">
      <div class="bg-gray-50 rounded-lg p-3">
        <p class="text-xs text-gray-500">Tables</p>
        <p class="text-lg font-semibold text-gray-900">24</p>
      </div>
      <div class="bg-gray-50 rounded-lg p-3">
        <p class="text-xs text-gray-500">Queries</p>
        <p class="text-lg font-semibold text-gray-900">156</p>
      </div>
    </div>
  </div>
</div>
```

### 3. Enhanced Notebook Cell
```html
<div class="group bg-white rounded-xl shadow-sm hover:shadow-md transition-all duration-300 border border-gray-100 overflow-hidden">
  <!-- Cell header with gradient -->
  <div class="bg-gradient-to-r from-gray-50 to-white px-5 py-3 border-b border-gray-100">
    <div class="flex items-center justify-between">
      <div class="flex items-center space-x-3">
        <span class="text-sm font-mono text-gray-500">In [1]</span>
        <div class="flex items-center space-x-1">
          <span class="w-2 h-2 bg-green-500 rounded-full"></span>
          <span class="text-xs text-gray-500">Ready</span>
        </div>
      </div>
      <div class="opacity-0 group-hover:opacity-100 transition-opacity flex items-center space-x-2">
        <button class="p-1.5 hover:bg-gray-100 rounded-lg transition-colors">
          <svg class="w-4 h-4 text-gray-500"><!-- Copy icon --></svg>
        </button>
        <button class="p-1.5 hover:bg-gray-100 rounded-lg transition-colors">
          <svg class="w-4 h-4 text-gray-500"><!-- Delete icon --></svg>
        </button>
      </div>
    </div>
  </div>
  
  <!-- Input area with better styling -->
  <div class="p-5">
    <textarea 
      placeholder="Enter your natural language query..."
      class="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-lg 
             focus:ring-2 focus:ring-blue-500 focus:border-transparent
             placeholder-gray-400 text-gray-700 resize-none"
      rows="3">
    </textarea>
    
    <!-- AI Suggestions (appears on focus) -->
    <div class="mt-3 p-3 bg-blue-50 border border-blue-200 rounded-lg">
      <p class="text-xs font-medium text-blue-700 mb-2">Suggested queries:</p>
      <div class="space-y-1">
        <button class="text-xs text-blue-600 hover:text-blue-800 text-left">
          • Show all students with rejected applications
        </button>
      </div>
    </div>
    
    <!-- Execute button with animation -->
    <button class="mt-4 px-6 py-2.5 bg-gradient-to-r from-blue-600 to-blue-700 
                   text-white font-medium rounded-lg shadow-md
                   hover:shadow-lg transform hover:-translate-y-0.5 transition-all duration-200
                   flex items-center space-x-2">
      <svg class="w-4 h-4"><!-- Play icon --></svg>
      <span>Execute Query</span>
    </button>
  </div>
  
  <!-- Output area with syntax highlighting -->
  <div class="border-t border-gray-100">
    <div class="px-5 py-3 bg-gray-50">
      <span class="text-sm font-mono text-gray-500">Out [1]</span>
    </div>
    
    <!-- SQL Display with syntax highlighting -->
    <div class="px-5 py-4">
      <div class="bg-gray-900 rounded-lg p-4 overflow-x-auto">
        <pre class="text-sm font-mono text-gray-100">
<span class="text-blue-400">SELECT</span> <span class="text-green-400">COUNT</span>(<span class="text-purple-400">DISTINCT</span> s.Id) <span class="text-blue-400">AS</span> total 
<span class="text-blue-400">FROM</span> Students s 
<span class="text-blue-400">INNER JOIN</span> ScholarshipApplications sa 
<span class="text-blue-400">ON</span> s.Id = sa.StudentId 
<span class="text-blue-400">WHERE</span> sa.Status = <span class="text-orange-400">5</span></pre>
      </div>
    </div>
    
    <!-- Results table with better styling -->
    <div class="px-5 pb-5">
      <div class="bg-white border border-gray-200 rounded-lg overflow-hidden">
        <table class="w-full">
          <thead class="bg-gray-50 border-b border-gray-200">
            <tr>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
                Total
              </th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100">
            <tr class="hover:bg-gray-50 transition-colors">
              <td class="px-4 py-3 text-sm text-gray-900">31</td>
            </tr>
          </tbody>
        </table>
      </div>
      
      <!-- Execution stats -->
      <div class="mt-3 flex items-center justify-between text-xs text-gray-500">
        <span>Execution time: 482ms</span>
        <span>1 row returned</span>
      </div>
    </div>
  </div>
</div>
```

### 4. Enhanced Hints Search
```html
<div class="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
  <div class="relative">
    <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
      <svg class="w-5 h-5 text-gray-400"><!-- Search icon --></svg>
    </div>
    <input 
      type="text"
      placeholder="Search hints, patterns, or examples..."
      class="w-full pl-10 pr-10 py-3 bg-gray-50 border border-gray-200 rounded-lg
             focus:ring-2 focus:ring-blue-500 focus:border-transparent
             placeholder-gray-400 text-gray-700">
    
    <!-- Loading spinner -->
    <div class="absolute inset-y-0 right-0 pr-3 flex items-center">
      <svg class="animate-spin h-5 w-5 text-blue-500"><!-- Spinner --></svg>
    </div>
  </div>
  
  <!-- Category pills with better styling -->
  <div class="mt-4 flex flex-wrap gap-2">
    <button class="px-4 py-2 bg-blue-500 text-white text-sm font-medium rounded-full
                   shadow-sm hover:shadow-md transition-all">
      All
    </button>
    <button class="px-4 py-2 bg-gray-100 text-gray-700 text-sm font-medium rounded-full
                   hover:bg-gray-200 transition-colors">
      Aggregations
    </button>
    <button class="px-4 py-2 bg-gray-100 text-gray-700 text-sm font-medium rounded-full
                   hover:bg-gray-200 transition-colors">
      Joins
    </button>
  </div>
  
  <!-- Results dropdown with cards -->
  <div class="mt-4 space-y-2 max-h-64 overflow-y-auto">
    <div class="p-3 bg-gradient-to-r from-blue-50 to-white border border-blue-200 rounded-lg
                hover:shadow-md transition-all cursor-pointer">
      <div class="flex items-start justify-between">
        <div>
          <p class="text-sm font-medium text-gray-900">Count students with applications</p>
          <p class="text-xs text-gray-500 mt-1">Returns the total number of students who have submitted applications</p>
        </div>
        <span class="px-2 py-1 bg-blue-100 text-blue-700 text-xs font-medium rounded">
          Popular
        </span>
      </div>
    </div>
  </div>
</div>
```

### 5. Enhanced Cache Stats Dashboard
```html
<div class="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
  <div class="flex items-center justify-between mb-4">
    <h3 class="text-lg font-semibold text-gray-900 flex items-center gap-2">
      <div class="p-2 bg-purple-50 rounded-lg">
        <svg class="w-5 h-5 text-purple-600"><!-- Chart icon --></svg>
      </div>
      Performance Metrics
    </h3>
    <button class="text-sm text-blue-600 hover:text-blue-800 font-medium">
      Refresh
    </button>
  </div>
  
  <!-- Metric cards with gradients -->
  <div class="grid grid-cols-4 gap-4">
    <div class="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-4">
      <div class="flex items-center justify-between">
        <div>
          <p class="text-xs text-blue-600 font-medium">Cache Hit Rate</p>
          <p class="text-2xl font-bold text-blue-900 mt-1">94%</p>
        </div>
        <div class="p-2 bg-blue-200/50 rounded-lg">
          <svg class="w-6 h-6 text-blue-700"><!-- Trending up --></svg>
        </div>
      </div>
    </div>
    
    <div class="bg-gradient-to-br from-green-50 to-green-100 rounded-lg p-4">
      <div class="flex items-center justify-between">
        <div>
          <p class="text-xs text-green-600 font-medium">Avg Response</p>
          <p class="text-2xl font-bold text-green-900 mt-1">245ms</p>
        </div>
        <div class="p-2 bg-green-200/50 rounded-lg">
          <svg class="w-6 h-6 text-green-700"><!-- Lightning --></svg>
        </div>
      </div>
    </div>
  </div>
</div>
```

## Animations & Micro-interactions

### Hover Effects
```css
/* Card hover lift */
.card:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
}

/* Button press effect */
.btn:active {
  transform: scale(0.98);
}

/* Smooth transitions */
* {
  transition: all 0.2s ease;
}
```

### Loading States
```html
<!-- Skeleton loader for cells -->
<div class="animate-pulse">
  <div class="h-4 bg-gray-200 rounded w-1/4 mb-2"></div>
  <div class="h-10 bg-gray-200 rounded"></div>
</div>

<!-- Spinner with fade -->
<div class="flex items-center justify-center p-8">
  <div class="animate-spin rounded-full h-8 w-8 border-2 border-blue-500 border-t-transparent"></div>
</div>
```

### Success/Error Feedback
```html
<!-- Success toast -->
<div class="fixed bottom-4 right-4 bg-green-500 text-white px-6 py-3 rounded-lg shadow-lg
            transform transition-all duration-300 translate-y-0 opacity-100">
  <div class="flex items-center space-x-2">
    <svg class="w-5 h-5"><!-- Check icon --></svg>
    <span>Query executed successfully!</span>
  </div>
</div>
```

## Responsive Design

### Breakpoints
- **Mobile**: < 640px - Single column, collapsed navigation
- **Tablet**: 640px - 1024px - 2 column grid
- **Desktop**: 1024px - 1280px - 3 column grid
- **Wide**: > 1280px - Full layout with sidebars

### Mobile Optimizations
```html
<!-- Responsive grid -->
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
  <!-- Cards -->
</div>

<!-- Mobile menu -->
<div class="lg:hidden">
  <button class="p-2">
    <svg class="w-6 h-6"><!-- Menu icon --></svg>
  </button>
</div>
```

## Dark Mode Support

### Color Adjustments
```css
/* Dark mode palette */
.dark {
  --bg-primary: #111827;
  --bg-secondary: #1F2937;
  --text-primary: #F9FAFB;
  --text-secondary: #9CA3AF;
  --border: #374151;
}

/* Component dark mode */
.dark .card {
  @apply bg-gray-800 border-gray-700;
}

.dark .input {
  @apply bg-gray-900 text-gray-100 border-gray-700;
}
```

## Accessibility Features

### ARIA Labels
```html
<button aria-label="Execute query" role="button">
  <span class="sr-only">Execute query</span>
  <svg aria-hidden="true"><!-- Icon --></svg>
</button>
```

### Keyboard Navigation
- Tab order properly set
- Focus visible states
- Escape key to close modals
- Enter to submit forms

### Color Contrast
- All text meets WCAG AA standards
- Important actions have 4.5:1 contrast ratio
- Error states use patterns, not just color

## Implementation Priority

### Phase 1 - Core Visual Updates
1. Update color palette and typography
2. Enhance header and navigation
3. Improve card components styling
4. Add hover effects and transitions

### Phase 2 - Interactive Enhancements
1. Add loading states and skeletons
2. Implement micro-interactions
3. Add success/error feedback
4. Enhance form inputs

### Phase 3 - Advanced Features
1. Dark mode toggle
2. Responsive optimizations
3. Accessibility improvements
4. Performance optimizations

## CSS Utilities Needed

```css
/* Custom gradients */
.gradient-blue {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

/* Glass morphism */
.glass {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

/* Smooth shadows */
.shadow-soft {
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.04),
              0 2px 4px -1px rgba(0, 0, 0, 0.06);
}
```