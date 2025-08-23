"""
Field analyzer service for semantic tagging and relationship discovery
"""
import re
from typing import Dict, List, Any, Set, Optional, Tuple
import logging
from collections import defaultdict
from .dynamic_fuzzy_matcher import DynamicFuzzyMatcher

logger = logging.getLogger(__name__)

class FieldAnalyzerService:
    def __init__(self):
        self.fuzzy_matcher = DynamicFuzzyMatcher()
        # Semantic field categories with patterns and keywords
        self.field_categories = {
            "identity": {
                "patterns": [r".*id$", r".*_id$", r".*key$", r".*_key$", r"^id$", r"^pk$"],
                "keywords": ["id", "key", "uuid", "guid", "identifier", "code", "number"],
                "description": "Unique identifiers and primary/foreign keys"
            },
            "personal_info": {
                "patterns": [r".*name$", r".*_name$", r"first.*", r"last.*", r"middle.*"],
                "keywords": ["name", "first", "last", "middle", "full", "nickname", "title", "prefix", "suffix"],
                "description": "Personal names and titles"
            },
            "contact": {
                "patterns": [r".*email$", r".*phone$", r".*address$", r".*contact$"],
                "keywords": ["email", "phone", "address", "contact", "mobile", "telephone", "zip", "postal", "city", "state", "country"],
                "description": "Contact information and addresses"
            },
            "temporal": {
                "patterns": [r".*date$", r".*_date$", r".*time$", r".*_time$", r".*created$", r".*updated$"],
                "keywords": ["date", "time", "created", "updated", "modified", "timestamp", "year", "month", "day", "birth", "dob"],
                "description": "Dates, times, and temporal information"
            },
            "academic": {
                "patterns": [r".*grade$", r".*gpa$", r".*score$", r".*class$", r".*course$", r".*school$"],
                "keywords": ["grade", "gpa", "score", "class", "course", "school", "student", "teacher", "subject", "semester", "year", "level", "major"],
                "description": "Academic and educational information"
            },
            "financial": {
                "patterns": [r".*price$", r".*cost$", r".*amount$", r".*salary$", r".*fee$", r".*payment$"],
                "keywords": ["price", "cost", "amount", "salary", "fee", "payment", "money", "currency", "balance", "total", "sum"],
                "description": "Financial and monetary information"
            },
            "status": {
                "patterns": [r".*status$", r".*_status$", r".*active$", r".*enabled$", r".*deleted$"],
                "keywords": ["status", "active", "enabled", "disabled", "deleted", "archived", "published", "approved", "pending"],
                "description": "Status and state information"
            },
            "location": {
                "patterns": [r".*location$", r".*address$", r".*city$", r".*state$", r".*country$"],
                "keywords": ["location", "address", "city", "state", "country", "zip", "postal", "latitude", "longitude", "coordinates"],
                "description": "Geographic and location information"
            },
            "description": {
                "patterns": [r".*description$", r".*desc$", r".*comment$", r".*note$", r".*text$"],
                "keywords": ["description", "desc", "comment", "note", "text", "content", "body", "message", "remarks"],
                "description": "Descriptive text and comments"
            }
        }
        
        # Common relationship patterns
        self.relationship_patterns = {
            "ownership": ["has", "owns", "belongs_to", "owner", "owned_by"],
            "association": ["member_of", "enrolled_in", "assigned_to", "works_at", "studies_at"],
            "hierarchy": ["parent", "child", "manager", "subordinate", "supervisor"],
            "temporal": ["before", "after", "during", "created_by", "updated_by"]
        }
        
        # Entity recognition patterns with scholarship context
        self.entity_patterns = {
            "student": ["student", "students", "pupil", "learner", "enrollee", "estudiante", "estudiantes", "becario", "becarios"],
            "application": ["application", "applications", "apply", "aplicacion", "aplicaciones", "solicitud", "solicitudes", "postulacion", "postulaciones"],
            "scholarship": ["scholarship", "scholarships", "beca", "becas", "grant", "grants", "aid", "financial_aid", "ayuda", "apoyo"],
            "teacher": ["teacher", "instructor", "professor", "educator", "faculty", "profesor", "profesores", "docente", "docentes"],
            "course": ["course", "class", "subject", "curriculum", "curso", "cursos", "materia", "materias"],
            "vehicle": ["car", "vehicle", "auto", "automobile", "truck", "bike", "vehiculo", "vehiculos"],
            "user": ["user", "person", "individual", "customer", "client", "usuario", "usuarios", "persona", "personas"],
            "order": ["order", "purchase", "transaction", "sale", "orden", "ordenes", "compra", "venta"],
            "product": ["product", "item", "goods", "merchandise", "producto", "productos", "articulo", "articulos"],
            "institution": ["school", "university", "college", "institution", "escuela", "universidad", "colegio", "institucion"],
            "government": ["senate", "government", "public", "senado", "gobierno", "publico", "estatal"]
        }
        
        # Domain-specific relationship patterns for scholarship systems
        self.scholarship_relationships = {
            "student_application": ["students apply for scholarships", "aplicar beca", "postular beca"],
            "application_status": ["pending", "approved", "rejected", "pendiente", "aprobado", "rechazado"],
            "scholarship_types": ["merit", "need-based", "government", "private", "merito", "necesidad", "gubernamental"],
            "academic_requirements": ["gpa", "grades", "achievements", "notas", "logros", "rendimiento"]
        }
        
        # Table name normalization patterns (including common typos/variations)
        self.table_name_variations = {
            "student": ["student", "students", "estudiante", "estudiantes", "stident"],  # Note: stident typo in DB
            "application": ["application", "applications", "aplicacion", "aplicaciones", "solicitud", "solicitudes"],
            "scholarship": ["scholarship", "scholarships", "beca", "becas", "scholaship"],  # Note: scholaship typo
            "scholarshipapplication": ["scholarshipapplication", "scholarshipapplications", "scholashipapplication", "scholashipapplications"],  # Various typo combinations
            "enrollment": ["enrollment", "enrollments", "inscripcion", "inscripciones"],
            "faculty": ["faculty", "professor", "teacher", "profesor", "profesores", "docente", "docentes"]
        }

    def analyze_database_fields(self, schema_info: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze all fields in the database and generate semantic insights"""
        
        if not schema_info or "tables" not in schema_info:
            return {"error": "No schema information available"}
        
        # Let the fuzzy matcher learn from the schema
        self.fuzzy_matcher.learn_from_schema(schema_info)
        logger.info(f"Fuzzy matcher learned from schema with {len(schema_info.get('tables', {}))} tables")
        
        analysis = {
            "tables": {},
            "field_categories": {},
            "semantic_tags": {},
            "relationships": [],
            "missing_fields": {},
            "query_suggestions": [],
            "data_availability": {},
            "fuzzy_patterns": {
                "compound_tables": self.fuzzy_matcher.compound_tables,
                "learned_mappings": dict(self.fuzzy_matcher.learned_mappings),
                "table_patterns": dict(self.fuzzy_matcher.table_patterns)
            }
        }
        
        # Analyze each table
        for table_name, table_info in schema_info["tables"].items():
            table_analysis = self._analyze_table_fields(table_name, table_info)
            analysis["tables"][table_name] = table_analysis
            
            # Collect field categories
            for field_name, field_info in table_analysis["fields"].items():
                for category in field_info["categories"]:
                    if category not in analysis["field_categories"]:
                        analysis["field_categories"][category] = []
                    analysis["field_categories"][category].append({
                        "table": table_name,
                        "field": field_name,
                        "data_type": field_info["data_type"]
                    })
        
        # Generate semantic tags
        analysis["semantic_tags"] = self._generate_semantic_tags(analysis["tables"])
        
        # Discover relationships
        analysis["relationships"] = self._discover_relationships(schema_info, analysis["tables"])
        
        # Identify missing fields and suggest alternatives
        analysis["missing_fields"] = self._identify_missing_fields(analysis["tables"])
        
        # Generate query suggestions based on available data
        analysis["query_suggestions"] = self._generate_query_suggestions(analysis)
        
        # Create data availability summary
        analysis["data_availability"] = self._create_availability_summary(analysis)
        
        logger.info(f"Field analysis completed for {len(analysis['tables'])} tables")
        return analysis
    
    def _analyze_table_fields(self, table_name: str, table_info: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze fields in a single table"""
        
        table_analysis = {
            "entity_type": self._identify_entity_type(table_name),
            "fields": {},
            "primary_concept": self._extract_primary_concept(table_name),
            "data_domains": set()
        }
        
        if "columns" not in table_info:
            return table_analysis
        
        for column in table_info["columns"]:
            field_name = column.get("name", "").lower()
            field_analysis = {
                "original_name": column.get("name", ""),
                "data_type": column.get("data_type", ""),
                "nullable": column.get("nullable", True),
                "categories": self._categorize_field(field_name),
                "semantic_meaning": self._interpret_field_meaning(field_name, table_name),
                "related_concepts": self._find_related_concepts(field_name)
            }
            
            table_analysis["fields"][field_name] = field_analysis
            table_analysis["data_domains"].update(field_analysis["categories"])
        
        # Convert set to list for JSON serialization
        table_analysis["data_domains"] = list(table_analysis["data_domains"])
        
        return table_analysis
    
    def _categorize_field(self, field_name: str) -> List[str]:
        """Categorize a field based on patterns and keywords"""
        categories = []
        field_lower = field_name.lower()
        
        for category, rules in self.field_categories.items():
            # Check patterns
            for pattern in rules["patterns"]:
                if re.match(pattern, field_lower):
                    categories.append(category)
                    break
            
            # Check keywords
            if category not in categories:
                for keyword in rules["keywords"]:
                    if keyword in field_lower:
                        categories.append(category)
                        break
        
        return categories if categories else ["other"]
    
    def _interpret_field_meaning(self, field_name: str, table_name: str) -> str:
        """Generate a human-readable interpretation of what this field represents"""
        field_lower = field_name.lower()
        table_lower = table_name.lower()
        
        # Handle ID fields
        if "id" in field_lower:
            if field_lower == "id" or field_lower == f"{table_lower}_id":
                return f"Unique identifier for {table_name}"
            else:
                referenced_entity = field_lower.replace("_id", "").replace("id", "")
                return f"Reference to {referenced_entity}"
        
        # Handle common patterns
        if "name" in field_lower:
            return f"Name or title associated with {table_name}"
        elif "date" in field_lower:
            return f"Date/time information for {table_name}"
        elif "email" in field_lower:
            return f"Email address for {table_name}"
        elif "phone" in field_lower:
            return f"Phone number for {table_name}"
        elif "address" in field_lower:
            return f"Address information for {table_name}"
        else:
            return f"{field_name} property of {table_name}"
    
    def _find_related_concepts(self, field_name: str) -> List[str]:
        """Find concepts related to this field"""
        field_lower = field_name.lower()
        related = []
        
        # Find entity relationships
        for entity, variants in self.entity_patterns.items():
            for variant in variants:
                if variant in field_lower:
                    related.append(entity)
                    break
        
        return related
    
    def _identify_entity_type(self, table_name: str) -> Optional[str]:
        """Identify what type of entity this table represents"""
        table_lower = table_name.lower()
        
        for entity, variants in self.entity_patterns.items():
            for variant in variants:
                if variant in table_lower:
                    return entity
        
        return None
    
    def _extract_primary_concept(self, table_name: str) -> str:
        """Extract the main concept this table represents"""
        # Remove common prefixes/suffixes
        concept = table_name.lower()
        concept = re.sub(r'^(tbl_|table_|tb_)', '', concept)
        concept = re.sub(r'(s|es)$', '', concept)  # Remove plural endings
        return concept
    
    def _generate_semantic_tags(self, tables_analysis: Dict[str, Any]) -> Dict[str, List[str]]:
        """Generate semantic tags for quick access"""
        tags = defaultdict(list)
        
        for table_name, table_info in tables_analysis.items():
            for field_name, field_info in table_info["fields"].items():
                for category in field_info["categories"]:
                    tags[category].append({
                        "table": table_name,
                        "field": field_info["original_name"],
                        "meaning": field_info["semantic_meaning"]
                    })
        
        return dict(tags)
    
    def _discover_relationships(self, schema_info: Dict[str, Any], tables_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Discover potential relationships between tables"""
        relationships = []
        
        # Add explicit foreign key relationships from schema
        if "relationships" in schema_info:
            for rel in schema_info["relationships"]:
                relationships.append({
                    "type": "explicit_fk",
                    "from_table": rel["from_table"],
                    "from_column": rel["from_column"],
                    "to_table": rel["to_table"],
                    "to_column": rel["to_column"],
                    "confidence": 1.0,
                    "description": f"{rel['from_table']} references {rel['to_table']}"
                })
        
        # Infer implicit relationships based on field patterns
        for table_name, table_info in tables_analysis.items():
            for field_name, field_info in table_info["fields"].items():
                if field_name.endswith("_id") and field_name != "id":
                    referenced_table = field_name[:-3]  # Remove "_id"
                    
                    # Look for matching table
                    for other_table in tables_analysis.keys():
                        if other_table.lower() == referenced_table or \
                           other_table.lower() == referenced_table + "s" or \
                           other_table.lower() == referenced_table + "es":
                            
                            relationships.append({
                                "type": "inferred_fk",
                                "from_table": table_name,
                                "from_column": field_info["original_name"],
                                "to_table": other_table,
                                "to_column": "id",
                                "confidence": 0.8,
                                "description": f"{table_name} likely references {other_table}"
                            })
        
        return relationships
    
    def _identify_missing_fields(self, tables_analysis: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        """Identify commonly expected fields that are missing"""
        missing_analysis = {}
        
        for table_name, table_info in tables_analysis.items():
            missing_fields = []
            existing_fields = set(table_info["fields"].keys())
            entity_type = table_info.get("entity_type")
            
            # Common fields expected for different entities
            expected_fields = {
                "student": ["email", "phone", "address", "birth_date", "enrollment_date"],
                "teacher": ["email", "phone", "hire_date", "department"],
                "course": ["description", "credits", "prerequisites"],
                "user": ["email", "created_date", "last_login"],
                "vehicle": ["make", "model", "year", "owner_id"],
                "order": ["order_date", "total_amount", "customer_id"]
            }
            
            if entity_type and entity_type in expected_fields:
                for expected_field in expected_fields[entity_type]:
                    if expected_field not in existing_fields:
                        # Look for similar fields
                        similar_fields = self._find_similar_fields(expected_field, existing_fields)
                        
                        missing_fields.append({
                            "field_name": expected_field,
                            "reason": f"Commonly expected for {entity_type} entities",
                            "alternatives": similar_fields,
                            "impact": "May limit query capabilities"
                        })
            
            if missing_fields:
                missing_analysis[table_name] = missing_fields
        
        return missing_analysis
    
    def _find_similar_fields(self, target_field: str, existing_fields: Set[str]) -> List[str]:
        """Find fields that might be similar to the target field"""
        similar = []
        target_lower = target_field.lower()
        
        for field in existing_fields:
            field_lower = field.lower()
            
            # Check for partial matches
            if any(part in field_lower for part in target_lower.split('_')):
                similar.append(field)
        
        return similar
    
    def _generate_query_suggestions(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate query suggestions based on available data"""
        suggestions = []
        
        # Analyze what types of queries are possible
        for table_name, table_info in analysis["tables"].items():
            entity_type = table_info.get("entity_type")
            fields = table_info["fields"]
            
            # Suggest basic queries
            suggestions.append({
                "type": "basic_list",
                "query_description": f"List all {table_name}",
                "example_query": f"Show me all {table_name}",
                "available_fields": list(fields.keys()),
                "confidence": 1.0
            })
            
            # Suggest filtered queries based on available categories
            for field_name, field_info in fields.items():
                if "status" in field_info["categories"]:
                    suggestions.append({
                        "type": "filtered",
                        "query_description": f"Filter {table_name} by {field_name}",
                        "example_query": f"Show me active {table_name}",
                        "filter_field": field_name,
                        "confidence": 0.9
                    })
        
        # Suggest relationship-based queries
        for rel in analysis["relationships"]:
            suggestions.append({
                "type": "relationship",
                "query_description": f"Find {rel['to_table']} related to {rel['from_table']}",
                "example_query": f"Show me {rel['to_table']} for each {rel['from_table']}",
                "relationship": rel,
                "confidence": rel["confidence"]
            })
        
        return suggestions
    
    def _create_availability_summary(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Create a summary of what data is available for queries"""
        summary = {
            "entities": {},
            "data_domains": {},
            "query_capabilities": {},
            "limitations": []
        }
        
        # Summarize entities
        for table_name, table_info in analysis["tables"].items():
            entity_type = table_info.get("entity_type", "unknown")
            summary["entities"][entity_type] = summary["entities"].get(entity_type, [])
            summary["entities"][entity_type].append({
                "table": table_name,
                "fields_count": len(table_info["fields"]),
                "data_domains": table_info["data_domains"]
            })
        
        # Summarize data domains
        for category, fields in analysis["field_categories"].items():
            summary["data_domains"][category] = {
                "description": self.field_categories.get(category, {}).get("description", ""),
                "field_count": len(fields),
                "tables": list(set([f["table"] for f in fields]))
            }
        
        # Identify query capabilities
        if "student" in summary["entities"]:
            summary["query_capabilities"]["student_queries"] = [
                "List students", "Filter by enrollment status", "Find student contact info"
            ]
        
        if "academic" in summary["data_domains"]:
            summary["query_capabilities"]["academic_queries"] = [
                "Grade analysis", "Course enrollment", "Academic performance"
            ]
        
        # Identify limitations
        for table_name, missing_fields in analysis["missing_fields"].items():
            for missing in missing_fields:
                summary["limitations"].append(f"Cannot query {missing['field_name']} for {table_name} - field not available")
        
        return summary
    
    def resolve_table_name(self, query_term: str, available_tables: List[str]) -> Optional[str]:
        """
        Intelligent table name resolution using dynamic fuzzy matching.
        Learns from the actual database schema to handle any database structure.
        """
        # Use the dynamic fuzzy matcher which has learned from the schema
        result = self.fuzzy_matcher.find_best_table_match(query_term, threshold=60)
        
        if result:
            matched_table, score = result
            logger.info(f"Dynamic fuzzy matched '{query_term}' to '{matched_table}' with score {score}")
            return matched_table
        
        # Fallback to simple substring matching if fuzzy matching fails
        query_lower = query_term.lower()
        for table in available_tables:
            if query_lower in table.lower() or table.lower() in query_lower:
                return table
        
        return None
    
    def generate_schema_context_for_query(self, user_query: str, available_tables: List[str], analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate enhanced schema context specifically for a user query.
        This provides the AI with table name mappings and relationship context.
        Uses fuzzy matching to handle misspellings and typos.
        """
        context = {
            "table_mappings": {},
            "relevant_tables": [],
            "domain_context": "",
            "relationship_hints": [],
            "query_intent": self._analyze_query_intent(user_query),
            "spelling_corrections": []
        }
        
        # Use dynamic fuzzy matcher to analyze the query
        suggestions = self.fuzzy_matcher.suggest_query_corrections(user_query)
        
        # Add table mappings from suggestions
        if suggestions.get("table_suggestions"):
            context["table_mappings"] = suggestions["table_suggestions"]
            context["relevant_tables"] = list(set(suggestions["table_suggestions"].values()))
        
        # Add column suggestions if any
        if suggestions.get("column_suggestions"):
            context["column_hints"] = suggestions["column_suggestions"]
        
        # Add confidence scores
        if suggestions.get("confidence_scores"):
            context["match_confidence"] = suggestions["confidence_scores"]
        
        # Add learned patterns that were used
        if suggestions.get("learned_patterns_used"):
            context["patterns_used"] = suggestions["learned_patterns_used"]
        
        if suggestions.get("suggested_query"):
            context["suggested_query"] = suggestions["suggested_query"]
            context["query_confidence"] = suggestions["confidence_score"]
        
        # Add domain context based on database name pattern or analysis
        if "beca" in user_query.lower() or "scholarship" in user_query.lower() or any("scholarship" in t.lower() for t in available_tables):
            context["domain_context"] = "scholarship_management_system"
            context["relationship_hints"].extend([
                "Students apply for scholarships through scholashipapplications table",
                "Join students.id with scholashipapplications.studentid (may be spelled 'stidentid')",
                "Applications have status (pending/approved/rejected)",
                "Tables may have spelling variations (e.g., 'scholaship' instead of 'scholarship')"
            ])
        
        # Add relationship context for relevant tables
        for table in context["relevant_tables"]:
            if table in analysis.get("tables", {}):
                table_analysis = analysis["tables"][table]
                entity_type = table_analysis.get("entity_type", "")
                if entity_type in ["student", "application", "scholarship"]:
                    context["relationship_hints"].append(
                        f"{table} is a {entity_type} entity with {len(table_analysis.get('fields', {}))} fields"
                    )
        
        return context
    
    def _analyze_query_intent(self, user_query: str) -> Dict[str, Any]:
        """Analyze what the user is trying to accomplish with their query"""
        query_lower = user_query.lower()
        
        intent = {
            "action": "unknown",
            "entities": [],
            "metrics": [],
            "filters": []
        }
        
        # Detect action words
        if any(word in query_lower for word in ["count", "how many", "number", "cantidad", "cuantos"]):
            intent["action"] = "count"
        elif any(word in query_lower for word in ["list", "show", "display", "find", "mostrar", "listar"]):
            intent["action"] = "list"
        elif any(word in query_lower for word in ["sum", "total", "average", "avg", "suma", "promedio"]):
            intent["action"] = "aggregate"
        
        # Detect entities from our patterns
        for entity_type, variations in self.entity_patterns.items():
            for variation in variations:
                if variation in query_lower:
                    intent["entities"].append(entity_type)
        
        # Detect relationship context
        if "with" in query_lower or "having" in query_lower or "con" in query_lower:
            intent["has_relationships"] = True
        
        return intent

    def generate_field_suggestions_for_query(self, query: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate suggestions for a specific query based on field analysis"""
        query_lower = query.lower()
        suggestions = {
            "available_data": [],
            "missing_data": [],
            "alternative_queries": [],
            "field_mappings": {}
        }
        
        # Analyze what the query is asking for
        mentioned_concepts = []
        for entity, variants in self.entity_patterns.items():
            for variant in variants:
                if variant in query_lower:
                    mentioned_concepts.append(entity)
        
        # Check what's available for mentioned concepts
        for concept in mentioned_concepts:
            if concept in analysis["data_availability"]["entities"]:
                entity_info = analysis["data_availability"]["entities"][concept]
                suggestions["available_data"].extend([
                    f"Can query {info['table']} with {info['fields_count']} available fields"
                    for info in entity_info
                ])
        
        # Identify missing information
        if "car" in query_lower or "vehicle" in query_lower:
            vehicle_tables = [t for t in analysis["tables"] if "vehicle" in t.lower() or "car" in t.lower()]
            if not vehicle_tables:
                suggestions["missing_data"].append(
                    "No vehicle/car information available in database"
                )
                suggestions["alternative_queries"].append(
                    "Consider querying transportation-related fields if available"
                )
        
        return suggestions