"""Service for generating database documentation with relationships and field descriptions"""
from typing import Dict, List, Any, Optional
import pymssql
from sqlalchemy.ext.asyncio import AsyncSession
import json
import re

class DocumentationService:
    def __init__(self):
        self.field_descriptions = self._load_field_descriptions()
    
    def _load_field_descriptions(self) -> Dict[str, str]:
        """Load common field name descriptions"""
        return {
            # IDs and Keys
            'id': 'Unique identifier for the record',
            'userid': 'Reference to the user who owns or created this record',
            'user_id': 'Reference to the user who owns or created this record',
            'customerid': 'Reference to the customer associated with this record',
            'customer_id': 'Reference to the customer associated with this record',
            'productid': 'Reference to the product',
            'product_id': 'Reference to the product',
            'orderid': 'Reference to the order',
            'order_id': 'Reference to the order',
            'categoryid': 'Reference to the category',
            'category_id': 'Reference to the category',
            'cityid': 'Reference to the city',
            'city_id': 'Reference to the city',
            'countryid': 'Reference to the country',
            'country_id': 'Reference to the country',
            'stateid': 'Reference to the state/province',
            'state_id': 'Reference to the state/province',
            
            # Names and Descriptions
            'name': 'Name or title of the record',
            'username': 'User login name',
            'firstname': 'First name of the person',
            'first_name': 'First name of the person',
            'lastname': 'Last name of the person',
            'last_name': 'Last name of the person',
            'fullname': 'Full name of the person',
            'full_name': 'Full name of the person',
            'displayname': 'Display name shown in the UI',
            'display_name': 'Display name shown in the UI',
            'title': 'Title or heading',
            'description': 'Detailed description or notes',
            'shortdescription': 'Brief description or summary',
            'short_description': 'Brief description or summary',
            'cityname': 'Name of the city',
            'city_name': 'Name of the city',
            'countryname': 'Name of the country',
            'country_name': 'Name of the country',
            
            # Contact Information
            'email': 'Email address',
            'phone': 'Phone number',
            'phonenumber': 'Phone number',
            'phone_number': 'Phone number',
            'mobile': 'Mobile phone number',
            'fax': 'Fax number',
            'website': 'Website URL',
            'address': 'Physical address',
            'street': 'Street address',
            'city': 'City name',
            'state': 'State or province',
            'province': 'Province',
            'country': 'Country',
            'zipcode': 'ZIP or postal code',
            'zip_code': 'ZIP or postal code',
            'postalcode': 'Postal code',
            'postal_code': 'Postal code',
            
            # Dates and Times
            'createdat': 'Date and time when the record was created',
            'created_at': 'Date and time when the record was created',
            'createddate': 'Date when the record was created',
            'created_date': 'Date when the record was created',
            'updatedat': 'Date and time when the record was last updated',
            'updated_at': 'Date and time when the record was last updated',
            'modifiedat': 'Date and time when the record was last modified',
            'modified_at': 'Date and time when the record was last modified',
            'deletedat': 'Date and time when the record was deleted (soft delete)',
            'deleted_at': 'Date and time when the record was deleted (soft delete)',
            'date': 'Date value',
            'datetime': 'Date and time value',
            'timestamp': 'Timestamp of the event',
            'startdate': 'Start date of the period',
            'start_date': 'Start date of the period',
            'enddate': 'End date of the period',
            'end_date': 'End date of the period',
            'birthdate': 'Date of birth',
            'birth_date': 'Date of birth',
            'orderdate': 'Date when the order was placed',
            'order_date': 'Date when the order was placed',
            'shippeddate': 'Date when the order was shipped',
            'shipped_date': 'Date when the order was shipped',
            'deliverydate': 'Date when the order was delivered',
            'delivery_date': 'Date when the order was delivered',
            
            # Status and Flags
            'status': 'Current status of the record',
            'isactive': 'Whether the record is active',
            'is_active': 'Whether the record is active',
            'isenabled': 'Whether the feature/record is enabled',
            'is_enabled': 'Whether the feature/record is enabled',
            'isdeleted': 'Whether the record is deleted (soft delete)',
            'is_deleted': 'Whether the record is deleted (soft delete)',
            'isvisible': 'Whether the record is visible',
            'is_visible': 'Whether the record is visible',
            'ispublished': 'Whether the content is published',
            'is_published': 'Whether the content is published',
            'isapproved': 'Whether the record is approved',
            'is_approved': 'Whether the record is approved',
            'isverified': 'Whether the record is verified',
            'is_verified': 'Whether the record is verified',
            
            # Financial
            'price': 'Price or cost amount',
            'unitprice': 'Price per unit',
            'unit_price': 'Price per unit',
            'amount': 'Total amount',
            'quantity': 'Quantity or count',
            'discount': 'Discount amount or percentage',
            'tax': 'Tax amount',
            'total': 'Total amount including all charges',
            'subtotal': 'Subtotal before tax and discounts',
            'balance': 'Current balance',
            'credit': 'Credit amount',
            'debit': 'Debit amount',
            'payment': 'Payment amount',
            'revenue': 'Revenue amount',
            'cost': 'Cost amount',
            
            # User and System
            'createdby': 'User who created the record',
            'created_by': 'User who created the record',
            'updatedby': 'User who last updated the record',
            'updated_by': 'User who last updated the record',
            'modifiedby': 'User who last modified the record',
            'modified_by': 'User who last modified the record',
            'deletedby': 'User who deleted the record',
            'deleted_by': 'User who deleted the record',
            'approvedby': 'User who approved the record',
            'approved_by': 'User who approved the record',
            
            # Other Common Fields
            'notes': 'Additional notes or comments',
            'comments': 'User comments',
            'tags': 'Tags or labels for categorization',
            'category': 'Category classification',
            'type': 'Type or kind of the record',
            'code': 'Code or identifier',
            'number': 'Number or numeric identifier',
            'sequence': 'Sequence number',
            'order': 'Order or position',
            'priority': 'Priority level',
            'rating': 'Rating or score',
            'score': 'Score value',
            'value': 'Generic value field',
            'data': 'Generic data field',
            'metadata': 'Additional metadata',
            'properties': 'Properties or attributes',
            'settings': 'Configuration settings',
            'options': 'Available options',
            'parameters': 'Parameters or arguments',
        }
    
    def get_field_description(self, field_name: str, table_name: str = None) -> str:
        """Get description for a field based on its name"""
        field_lower = field_name.lower()
        
        # Check exact match first
        if field_lower in self.field_descriptions:
            return self.field_descriptions[field_lower]
        
        # Check patterns
        if field_lower.endswith('_id') or field_lower.endswith('id'):
            entity = field_lower.replace('_id', '').replace('id', '')
            return f'Reference to the {entity} entity'
        
        if field_lower.endswith('_name') or field_lower.endswith('name'):
            entity = field_lower.replace('_name', '').replace('name', '')
            return f'Name of the {entity}'
        
        if field_lower.endswith('_date') or field_lower.endswith('date'):
            event = field_lower.replace('_date', '').replace('date', '')
            return f'Date of the {event} event'
        
        if field_lower.endswith('_at'):
            event = field_lower.replace('_at', '')
            return f'Timestamp when {event} occurred'
        
        if field_lower.startswith('is_') or field_lower.startswith('has_'):
            feature = field_lower.replace('is_', '').replace('has_', '')
            return f'Boolean flag indicating if {feature}'
        
        if field_lower.endswith('_count') or field_lower.endswith('count'):
            entity = field_lower.replace('_count', '').replace('count', '')
            return f'Number of {entity} items'
        
        # Default description
        return f'{field_name} field'
    
    def parse_connection_string(self, connection_string: str) -> Dict[str, str]:
        """Parse MSSQL connection string"""
        params = {}
        parts = connection_string.split(';')
        
        for part in parts:
            if '=' in part:
                key, value = part.split('=', 1)
                key = key.strip().lower()
                value = value.strip()
                
                if key in ['server', 'data source']:
                    params['server'] = value
                elif key in ['database', 'initial catalog']:
                    params['database'] = value
                elif key in ['user id', 'uid', 'user']:
                    params['user'] = value
                elif key in ['password', 'pwd']:
                    params['password'] = value
        
        return params
    
    async def get_database_documentation(self, connection_string: str) -> Dict[str, Any]:
        """Generate comprehensive database documentation"""
        try:
            # Parse connection string
            params = self.parse_connection_string(connection_string)
            
            # Connect using pymssql
            conn = pymssql.connect(
                server=params.get('server'),
                database=params.get('database'),
                user=params.get('user'),
                password=params.get('password')
            )
            cursor = conn.cursor()
            
            documentation = {
                'database_info': {},
                'tables': {},
                'relationships': [],
                'views': {},
                'stored_procedures': {},
                'statistics': {}
            }
            
            # Get database info
            documentation['database_info'] = {
                'database_name': params.get('database', 'Unknown'),
                'driver': 'pymssql',
                'server': params.get('server', 'Unknown'),
            }
            
            # Get all tables using SQL query
            cursor.execute("""
                SELECT 
                    TABLE_SCHEMA,
                    TABLE_NAME
                FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_TYPE = 'BASE TABLE'
                    AND TABLE_SCHEMA NOT IN ('sys', 'INFORMATION_SCHEMA')
                ORDER BY TABLE_SCHEMA, TABLE_NAME
            """)
            
            table_list = []
            for row in cursor.fetchall():
                schema = row[0] or 'dbo'
                table_name = row[1]
                full_name = f"[{schema}].[{table_name}]" if schema != 'dbo' else f"[{table_name}]"
                table_list.append({
                    'schema': schema,
                    'name': table_name,
                    'full_name': full_name
                })
            
            # Get details for each table
            for table_info in table_list:
                table_name = table_info['full_name']
                documentation['tables'][table_name] = {
                    'schema': table_info['schema'],
                    'name': table_info['name'],
                    'columns': [],
                    'primary_keys': [],
                    'foreign_keys': [],
                    'indexes': [],
                    'row_count': 0
                }
                
                # Get columns
                cursor.execute(f"""
                    SELECT 
                        COLUMN_NAME,
                        DATA_TYPE,
                        CHARACTER_MAXIMUM_LENGTH,
                        IS_NULLABLE,
                        COLUMN_DEFAULT
                    FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE TABLE_SCHEMA = '{table_info['schema']}'
                        AND TABLE_NAME = '{table_info['name']}'
                    ORDER BY ORDINAL_POSITION
                """)
                
                for col_row in cursor.fetchall():
                    col_info = {
                        'name': col_row[0],
                        'type': col_row[1],
                        'size': col_row[2] or 0,
                        'nullable': col_row[3] == 'YES',
                        'default': col_row[4],
                        'description': self.get_field_description(col_row[0], table_info['name'])
                    }
                    documentation['tables'][table_name]['columns'].append(col_info)
                
                # Get primary keys
                try:
                    cursor.execute(f"""
                        SELECT COLUMN_NAME
                        FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
                        WHERE OBJECTPROPERTY(OBJECT_ID(CONSTRAINT_NAME), 'IsPrimaryKey') = 1
                            AND TABLE_SCHEMA = '{table_info['schema']}'
                            AND TABLE_NAME = '{table_info['name']}'
                    """)
                    for pk_row in cursor.fetchall():
                        documentation['tables'][table_name]['primary_keys'].append(pk_row[0])
                except:
                    pass
                
                # Get foreign keys (relationships)
                try:
                    cursor.execute(f"""
                        SELECT 
                            fk.name AS constraint_name,
                            cp.name AS from_column,
                            OBJECT_SCHEMA_NAME(fk.referenced_object_id) AS to_schema,
                            OBJECT_NAME(fk.referenced_object_id) AS to_table,
                            cr.name AS to_column
                        FROM sys.foreign_keys fk
                        INNER JOIN sys.foreign_key_columns fkc 
                            ON fk.object_id = fkc.constraint_object_id
                        INNER JOIN sys.columns cp 
                            ON fkc.parent_column_id = cp.column_id 
                            AND fkc.parent_object_id = cp.object_id
                        INNER JOIN sys.columns cr 
                            ON fkc.referenced_column_id = cr.column_id 
                            AND fkc.referenced_object_id = cr.object_id
                        WHERE OBJECT_SCHEMA_NAME(fk.parent_object_id) = '{table_info['schema']}'
                            AND OBJECT_NAME(fk.parent_object_id) = '{table_info['name']}'
                    """)
                    
                    for fk_row in cursor.fetchall():
                        to_schema = fk_row[2] or 'dbo'
                        to_table = fk_row[3]
                        to_full_name = f"[{to_schema}].[{to_table}]" if to_schema != 'dbo' else f"[{to_table}]"
                        
                        fk_info = {
                            'column': fk_row[1],
                            'references_table': to_full_name,
                            'references_column': fk_row[4],
                            'constraint_name': fk_row[0]
                        }
                        documentation['tables'][table_name]['foreign_keys'].append(fk_info)
                        
                        # Add to relationships
                        relationship = {
                            'from_table': table_name,
                            'from_column': fk_row[1],
                            'to_table': to_full_name,
                            'to_column': fk_row[4],
                            'relationship_type': 'foreign_key',
                            'constraint_name': fk_row[0]
                        }
                        documentation['relationships'].append(relationship)
                except:
                    pass
                
                # Get row count
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    row_count = cursor.fetchone()[0]
                    documentation['tables'][table_name]['row_count'] = row_count
                except:
                    pass
            
            # Get views
            try:
                cursor.execute("""
                    SELECT 
                        TABLE_SCHEMA,
                        TABLE_NAME
                    FROM INFORMATION_SCHEMA.VIEWS
                    WHERE TABLE_SCHEMA NOT IN ('sys', 'INFORMATION_SCHEMA')
                    ORDER BY TABLE_SCHEMA, TABLE_NAME
                """)
                
                for view_row in cursor.fetchall():
                    view_schema = view_row[0] or 'dbo'
                    view_name = view_row[1]
                    view_full_name = f"[{view_schema}].[{view_name}]" if view_schema != 'dbo' else f"[{view_name}]"
                    
                    documentation['views'][view_full_name] = {
                        'schema': view_schema,
                        'name': view_name,
                        'columns': []
                    }
                    
                    # Get view columns
                    cursor.execute(f"""
                        SELECT 
                            COLUMN_NAME,
                            DATA_TYPE
                        FROM INFORMATION_SCHEMA.COLUMNS
                        WHERE TABLE_SCHEMA = '{view_schema}'
                            AND TABLE_NAME = '{view_name}'
                        ORDER BY ORDINAL_POSITION
                    """)
                    
                    for col_row in cursor.fetchall():
                        col_info = {
                            'name': col_row[0],
                            'type': col_row[1],
                            'description': self.get_field_description(col_row[0])
                        }
                        documentation['views'][view_full_name]['columns'].append(col_info)
            except:
                pass
            
            # Get stored procedures
            try:
                cursor.execute("""
                    SELECT 
                        ROUTINE_SCHEMA,
                        ROUTINE_NAME,
                        ROUTINE_TYPE
                    FROM INFORMATION_SCHEMA.ROUTINES
                    WHERE ROUTINE_SCHEMA NOT IN ('sys', 'INFORMATION_SCHEMA')
                    ORDER BY ROUTINE_SCHEMA, ROUTINE_NAME
                """)
                
                for proc_row in cursor.fetchall():
                    proc_schema = proc_row[0] or 'dbo'
                    proc_name = proc_row[1]
                    proc_full_name = f"[{proc_schema}].[{proc_name}]" if proc_schema != 'dbo' else f"[{proc_name}]"
                    
                    documentation['stored_procedures'][proc_full_name] = {
                        'schema': proc_schema,
                        'name': proc_name,
                        'type': proc_row[2]
                    }
            except:
                pass
            
            # Calculate statistics
            documentation['statistics'] = {
                'total_tables': len(documentation['tables']),
                'total_columns': sum(len(t['columns']) for t in documentation['tables'].values()),
                'total_relationships': len(documentation['relationships']),
                'total_views': len(documentation['views']),
                'total_stored_procedures': len(documentation['stored_procedures']),
                'total_rows': sum(t.get('row_count', 0) for t in documentation['tables'].values())
            }
            
            cursor.close()
            conn.close()
            
            return documentation
            
        except Exception as e:
            return {
                'error': str(e),
                'documentation': None
            }
    
    def generate_markdown_documentation(self, documentation: Dict[str, Any]) -> str:
        """Generate markdown documentation from the documentation dict"""
        md_lines = []
        
        # Header
        md_lines.append("# Database Documentation")
        md_lines.append("")
        md_lines.append(f"Generated documentation for {documentation['database_info'].get('database_name', 'Unknown Database')}")
        md_lines.append("")
        
        # Statistics
        md_lines.append("## Database Statistics")
        md_lines.append("")
        stats = documentation['statistics']
        md_lines.append(f"- **Total Tables**: {stats['total_tables']}")
        md_lines.append(f"- **Total Columns**: {stats['total_columns']}")
        md_lines.append(f"- **Total Relationships**: {stats['total_relationships']}")
        md_lines.append(f"- **Total Views**: {stats['total_views']}")
        md_lines.append(f"- **Total Stored Procedures**: {stats['total_stored_procedures']}")
        md_lines.append(f"- **Total Rows**: {stats['total_rows']:,}")
        md_lines.append("")
        
        # Table of Contents
        md_lines.append("## Table of Contents")
        md_lines.append("")
        md_lines.append("1. [Tables](#tables)")
        md_lines.append("2. [Relationships](#relationships)")
        md_lines.append("3. [Views](#views)")
        md_lines.append("4. [Stored Procedures](#stored-procedures)")
        md_lines.append("")
        
        # Tables
        md_lines.append("## Tables")
        md_lines.append("")
        
        for table_name, table_info in documentation['tables'].items():
            md_lines.append(f"### {table_name}")
            md_lines.append("")
            md_lines.append(f"**Rows**: {table_info['row_count']:,}")
            md_lines.append("")
            
            # Primary Keys
            if table_info['primary_keys']:
                md_lines.append(f"**Primary Keys**: {', '.join(table_info['primary_keys'])}")
                md_lines.append("")
            
            # Columns
            md_lines.append("#### Columns")
            md_lines.append("")
            md_lines.append("| Column | Type | Nullable | Description |")
            md_lines.append("|--------|------|----------|-------------|")
            
            for col in table_info['columns']:
                nullable = "Yes" if col['nullable'] else "No"
                is_pk = "🔑 " if col['name'] in table_info['primary_keys'] else ""
                is_fk = "🔗 " if any(fk['column'] == col['name'] for fk in table_info['foreign_keys']) else ""
                col_display = f"{is_pk}{is_fk}{col['name']}"
                md_lines.append(f"| {col_display} | {col['type']} | {nullable} | {col['description']} |")
            
            md_lines.append("")
            
            # Foreign Keys
            if table_info['foreign_keys']:
                md_lines.append("#### Foreign Keys")
                md_lines.append("")
                for fk in table_info['foreign_keys']:
                    md_lines.append(f"- **{fk['column']}** → {fk['references_table']}.{fk['references_column']}")
                md_lines.append("")
        
        # Relationships
        md_lines.append("## Relationships")
        md_lines.append("")
        md_lines.append("| From Table | From Column | To Table | To Column | Type |")
        md_lines.append("|------------|-------------|----------|-----------|------|")
        
        for rel in documentation['relationships']:
            md_lines.append(f"| {rel['from_table']} | {rel['from_column']} | {rel['to_table']} | {rel['to_column']} | {rel['relationship_type']} |")
        
        md_lines.append("")
        
        # Views
        if documentation['views']:
            md_lines.append("## Views")
            md_lines.append("")
            
            for view_name, view_info in documentation['views'].items():
                md_lines.append(f"### {view_name}")
                md_lines.append("")
                md_lines.append("| Column | Type | Description |")
                md_lines.append("|--------|------|-------------|")
                
                for col in view_info['columns']:
                    md_lines.append(f"| {col['name']} | {col['type']} | {col['description']} |")
                
                md_lines.append("")
        
        # Stored Procedures
        if documentation['stored_procedures']:
            md_lines.append("## Stored Procedures")
            md_lines.append("")
            
            for proc_name, proc_info in documentation['stored_procedures'].items():
                md_lines.append(f"- **{proc_name}** (Type: {proc_info['type']})")
            
            md_lines.append("")
        
        return "\n".join(md_lines)

# Global instance
documentation_service = DocumentationService()