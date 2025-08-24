"""
Column Intelligence Service - Analyzes column names to understand semantic meaning
and relationships for intelligent query generation
"""
import re
import logging
from typing import Dict, List, Any, Optional, Tuple

logger = logging.getLogger(__name__)

class ColumnIntelligenceService:
    """Service that understands column semantics for intelligent query generation"""
    
    def __init__(self):
        # Common patterns for understanding column purposes
        self.location_patterns = {
            'city': ['city', 'ciudad', 'municipio', 'town'],
            'state': ['state', 'estado', 'province', 'provincia'],
            'region': ['region', 'area', 'zone', 'distrito'],
            'address': ['address', 'direccion', 'addr', 'location'],
            'postal': ['postal', 'zip', 'zipcode', 'codigo'],
            'physical': ['physical', 'fisico', 'actual', 'real']
        }
        
        self.temporal_patterns = {
            'creation': ['created', 'creation', 'registered', 'added'],
            'update': ['updated', 'modified', 'changed', 'edited'],
            'birth': ['birth', 'nacimiento', 'born', 'dob'],
            'graduation': ['graduation', 'graduated', 'graduate', 'completion'],
            'enrollment': ['enrollment', 'enrolled', 'matricula', 'admission'],
            'date': ['date', 'fecha', 'time', 'timestamp']
        }
        
        self.identifier_patterns = {
            'primary': ['id', 'key', 'identifier', 'code'],
            'foreign': ['_id', 'ref', 'fk', 'reference'],
            'user': ['user', 'usuario', 'account', 'member'],
            'student': ['student', 'estudiante', 'alumno', 'pupil']
        }
        
        self.status_patterns = {
            'status': ['status', 'estado', 'state', 'condition'],
            'active': ['active', 'activo', 'enabled', 'valid'],
            'approved': ['approved', 'aprobado', 'accepted', 'confirmed']
        }
    
    def analyze_column_semantics(self, schema_info: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze column names to understand their semantic meaning"""
        semantic_analysis = {
            'location_columns': {},
            'temporal_columns': {},
            'relationship_columns': {},
            'status_columns': {},
            'identifier_columns': {}
        }
        
        if not schema_info or 'tables' not in schema_info:
            return semantic_analysis
        
        for table_name, table_info in schema_info.get('tables', {}).items():
            columns = table_info.get('columns', [])
            
            for column in columns:
                col_name = column.get('name', '').lower()
                col_type = column.get('data_type', '').lower()
                
                # Analyze location columns
                if self._is_location_column(col_name):
                    if table_name not in semantic_analysis['location_columns']:
                        semantic_analysis['location_columns'][table_name] = []
                    
                    location_type = self._get_location_type(col_name)
                    semantic_analysis['location_columns'][table_name].append({
                        'column': column['name'],
                        'type': location_type,
                        'is_id': 'id' in col_name.lower(),
                        'is_postal': 'postal' in col_name.lower(),
                        'is_physical': 'physical' in col_name.lower() or 'fisico' in col_name.lower()
                    })
                
                # Analyze temporal columns
                if self._is_temporal_column(col_name, col_type):
                    if table_name not in semantic_analysis['temporal_columns']:
                        semantic_analysis['temporal_columns'][table_name] = []
                    
                    temporal_type = self._get_temporal_type(col_name)
                    semantic_analysis['temporal_columns'][table_name].append({
                        'column': column['name'],
                        'type': temporal_type,
                        'data_type': col_type
                    })
                
                # Analyze relationship columns (foreign keys)
                if self._is_relationship_column(col_name):
                    if table_name not in semantic_analysis['relationship_columns']:
                        semantic_analysis['relationship_columns'][table_name] = []
                    
                    referenced_table = self._infer_referenced_table(col_name)
                    semantic_analysis['relationship_columns'][table_name].append({
                        'column': column['name'],
                        'likely_references': referenced_table,
                        'type': 'foreign_key'
                    })
                
                # Analyze status columns
                if self._is_status_column(col_name):
                    if table_name not in semantic_analysis['status_columns']:
                        semantic_analysis['status_columns'][table_name] = []
                    
                    semantic_analysis['status_columns'][table_name].append({
                        'column': column['name'],
                        'data_type': col_type
                    })
                
                # Analyze identifier columns
                if self._is_identifier_column(col_name):
                    if table_name not in semantic_analysis['identifier_columns']:
                        semantic_analysis['identifier_columns'][table_name] = []
                    
                    semantic_analysis['identifier_columns'][table_name].append({
                        'column': column['name'],
                        'is_primary': col_name == 'id' or col_name.endswith('_id'),
                        'data_type': col_type
                    })
        
        return semantic_analysis
    
    def _is_location_column(self, col_name: str) -> bool:
        """Check if column name indicates location data"""
        col_lower = col_name.lower()
        for category, patterns in self.location_patterns.items():
            if any(pattern in col_lower for pattern in patterns):
                return True
        return False
    
    def _get_location_type(self, col_name: str) -> str:
        """Determine the type of location column"""
        col_lower = col_name.lower()
        for category, patterns in self.location_patterns.items():
            if any(pattern in col_lower for pattern in patterns):
                return category
        return 'unknown'
    
    def _is_temporal_column(self, col_name: str, col_type: str) -> bool:
        """Check if column is temporal (date/time)"""
        col_lower = col_name.lower()
        type_lower = col_type.lower()
        
        # Check by data type
        if any(t in type_lower for t in ['date', 'time', 'datetime', 'timestamp']):
            return True
        
        # Check by name patterns
        for category, patterns in self.temporal_patterns.items():
            if any(pattern in col_lower for pattern in patterns):
                return True
        
        return False
    
    def _get_temporal_type(self, col_name: str) -> str:
        """Determine the type of temporal column"""
        col_lower = col_name.lower()
        for category, patterns in self.temporal_patterns.items():
            if any(pattern in col_lower for pattern in patterns):
                return category
        return 'date'
    
    def _is_relationship_column(self, col_name: str) -> bool:
        """Check if column is likely a foreign key"""
        col_lower = col_name.lower()
        
        # Common foreign key patterns
        fk_patterns = ['_id', 'id_', 'ref_', '_ref', 'fk_']
        
        # Exclude primary keys
        if col_lower == 'id':
            return False
        
        # Check for foreign key patterns
        return any(pattern in col_lower for pattern in fk_patterns) or col_lower.endswith('id')
    
    def _infer_referenced_table(self, col_name: str) -> str:
        """Infer the table being referenced by a foreign key column"""
        col_lower = col_name.lower()
        
        # Remove common suffixes
        cleaned = col_lower.replace('_id', '').replace('id_', '').replace('_ref', '')
        
        # Common mappings
        table_mappings = {
            'city': 'Cities',
            'citypostal': 'Cities',
            'cityphysical': 'Cities',
            'cityidpostal': 'Cities',
            'cityidphysical': 'Cities',
            'student': 'Students',
            'user': 'AspNetUsers',
            'highschool': 'HighSchools',
            'region': 'Regions',
            'municipio': 'Municipios',
            'occupation': 'Occupations',
            'university': 'Universities',
            'document': 'StudentDocuments',
            'documenttype': 'StudentDocumentTypes'
        }
        
        for key, table in table_mappings.items():
            if key in cleaned:
                return table
        
        # Try to capitalize and pluralize
        if cleaned:
            return cleaned.capitalize() + 's'
        
        return 'Unknown'
    
    def _is_status_column(self, col_name: str) -> bool:
        """Check if column represents a status"""
        col_lower = col_name.lower()
        for category, patterns in self.status_patterns.items():
            if any(pattern in col_lower for pattern in patterns):
                return True
        return False
    
    def _is_identifier_column(self, col_name: str) -> bool:
        """Check if column is an identifier"""
        col_lower = col_name.lower()
        for category, patterns in self.identifier_patterns.items():
            if any(pattern in col_lower for pattern in patterns):
                return True
        return False
    
    def generate_location_aware_query(self, 
                                     prompt: str, 
                                     semantic_analysis: Dict[str, Any],
                                     schema_info: Dict[str, Any]) -> Optional[str]:
        """Generate SQL query understanding location references in natural language"""
        prompt_lower = prompt.lower()
        
        # Check for location references
        location_keywords = self._extract_location_keywords(prompt_lower)
        if not location_keywords:
            return None
        
        # Check if we have Students table with location columns
        student_location_cols = semantic_analysis.get('location_columns', {}).get('Students', [])
        if not student_location_cols:
            return None
        
        # Look for city references
        for location in location_keywords:
            # Find city ID columns in Students table
            city_id_cols = [col for col in student_location_cols 
                          if col['type'] == 'city' and col['is_id']]
            
            if city_id_cols and 'Cities' in schema_info.get('tables', {}):
                # Determine which city column to use
                if 'postal' in prompt_lower:
                    city_col = next((col for col in city_id_cols if col['is_postal']), city_id_cols[0])
                elif 'physical' in prompt_lower or 'fisico' in prompt_lower:
                    city_col = next((col for col in city_id_cols if col['is_physical']), city_id_cols[0])
                else:
                    # Default to physical location
                    city_col = next((col for col in city_id_cols if col['is_physical']), city_id_cols[0])
                
                # Determine the action
                if 'count' in prompt_lower:
                    logger.info(f"🎯 Location-aware query: Count students from {location}")
                    return f"""SELECT COUNT(DISTINCT s.Id) AS total
                             FROM Students s WITH (NOLOCK)
                             INNER JOIN Cities c WITH (NOLOCK) ON s.{city_col['column']} = c.Id
                             WHERE c.Name COLLATE Latin1_General_CI_AI LIKE '%{location}%'"""
                
                elif any(action in prompt_lower for action in ['show', 'list', 'find', 'get']):
                    # Extract limit if specified
                    numbers = re.findall(r'\d+', prompt_lower)
                    limit = int(numbers[0]) if numbers else 100
                    
                    logger.info(f"🎯 Location-aware query: Show students from {location}")
                    return f"""SELECT TOP {limit} s.*, c.Name AS CityName
                             FROM Students s WITH (NOLOCK)
                             INNER JOIN Cities c WITH (NOLOCK) ON s.{city_col['column']} = c.Id
                             WHERE c.Name COLLATE Latin1_General_CI_AI LIKE '%{location}%'"""
                
                elif 'group' in prompt_lower or 'by city' in prompt_lower:
                    logger.info(f"🎯 Location-aware query: Group students by city")
                    return f"""SELECT c.Name AS City, COUNT(s.Id) AS StudentCount
                             FROM Students s WITH (NOLOCK)
                             INNER JOIN Cities c WITH (NOLOCK) ON s.{city_col['column']} = c.Id
                             GROUP BY c.Name
                             ORDER BY COUNT(s.Id) DESC"""
        
        return None
    
    def _extract_location_keywords(self, prompt: str) -> List[str]:
        """Extract potential location names from prompt"""
        locations = []
        
        # Common Puerto Rico cities
        pr_cities = [
            'san juan', 'bayamon', 'carolina', 'ponce', 'caguas',
            'guaynabo', 'mayaguez', 'trujillo alto', 'arecibo', 'fajardo',
            'toa baja', 'vega baja', 'canovanas', 'humacao', 'rio grande',
            'guayama', 'cayey', 'cidra', 'manati', 'aguadilla',
            'dorado', 'yauco', 'juana diaz', 'gurabo', 'san lorenzo',
            'isabela', 'san sebastian', 'coamo', 'hatillo', 'cabo rojo',
            'las piedras', 'comerio', 'naranjito', 'vega alta', 'aibonito',
            'salinas', 'barceloneta', 'morovis', 'san german', 'sabana grande',
            'aguas buenas', 'moca', 'patillas', 'guanica', 'santa isabel'
        ]
        
        # Check for known cities
        for city in pr_cities:
            if city in prompt.lower():
                locations.append(city.title())
        
        # Also check for capitalized words that might be city names
        words = prompt.split()
        for word in words:
            if word[0].isupper() and word.lower() not in ['select', 'from', 'where', 'count', 'show', 'students']:
                # Could be a city name
                locations.append(word)
        
        # Check for phrases with "from" or "in"
        from_pattern = re.findall(r'(?:from|in)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)', prompt, re.IGNORECASE)
        locations.extend(from_pattern)
        
        return list(set(locations))  # Remove duplicates
    
    def enhance_query_with_semantics(self, 
                                    prompt: str,
                                    base_query: str,
                                    semantic_analysis: Dict[str, Any]) -> str:
        """Enhance a base query with semantic understanding"""
        enhanced_query = base_query
        prompt_lower = prompt.lower()
        
        # Add temporal filters if mentioned
        if any(temporal in prompt_lower for temporal in ['this year', 'last year', 'this month']):
            temporal_cols = semantic_analysis.get('temporal_columns', {})
            
            if 'Students' in temporal_cols:
                creation_cols = [col for col in temporal_cols['Students'] 
                               if col['type'] == 'creation']
                
                if creation_cols and 'WHERE' not in enhanced_query.upper():
                    col_name = creation_cols[0]['column']
                    
                    if 'this year' in prompt_lower:
                        enhanced_query += f" WHERE YEAR({col_name}) = YEAR(GETDATE())"
                    elif 'last year' in prompt_lower:
                        enhanced_query += f" WHERE YEAR({col_name}) = YEAR(GETDATE()) - 1"
                    elif 'this month' in prompt_lower:
                        enhanced_query += f" WHERE YEAR({col_name}) = YEAR(GETDATE()) AND MONTH({col_name}) = MONTH(GETDATE())"
        
        return enhanced_query

# Global instance
column_intelligence = ColumnIntelligenceService()