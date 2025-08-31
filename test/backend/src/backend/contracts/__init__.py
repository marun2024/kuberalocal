"""
Contracts and Tags module - Complete implementation.

This module provides a full-featured contracts and tags management system with:
- Multi-tenant compatibility (no foreign key constraints)
- Many-to-many relationships handled at application level
- Complete CRUD operations with validation
- Bulk operations and analytics
- RESTful API endpoints

Import order is important to avoid circular dependencies:
1. Models (database structure)
2. Schemas (request/response validation)  
3. Queries (data retrieval)
4. Commands (business logic)
5. Routers (API endpoints)
"""

# Core imports
from .models import Tag, Contract, TagContractLink

# Schema imports
from .schemas import (
    # Tag schemas
    TagBase, TagCreate, TagUpdate, TagResponse, TagRead,
    # Contract schemas  
    ContractBase, ContractCreate, ContractUpdate, ContractResponse, ContractRead,
    # Relationship schemas
    LinkRequest, LinkResponse, BulkLinkRequest,
    # Filter schemas
    TagFilter, ContractFilter, ContractSearch
)

# Query imports
from .queries import (
    # Tag queries
    get_tag_query, list_tags_query, tag_exists_by_name, count_tags_query,
    # Contract queries  
    get_contract_query, list_contracts_query, search_contracts_query, 
    contract_exists_by_reference, count_contracts_query,
    # Relationship queries
    link_exists_query, get_link_query, get_contracts_for_tag_query, 
    get_tags_for_contract_query, get_tag_with_contracts_query, 
    get_contract_with_tags_query, count_links_for_tag_query, 
    count_links_for_contract_query,
    # Analytics queries
    get_most_used_tags_query, get_contracts_expiring_soon_query
)

# Command imports
from .commands import (
    # Tag commands
    create_tag_command, update_tag_command, delete_tag_command,
    # Contract commands
    create_contract_command, update_contract_command, delete_contract_command,
    # Relationship commands
    link_tag_to_contract_command, unlink_tag_from_contract_command,
    # Bulk operations
    bulk_link_tags_to_contract_command, bulk_link_contracts_to_tag_command,
    bulk_unlink_tags_from_contract_command, bulk_unlink_contracts_from_tag_command,
    # Specialized commands
    duplicate_tag_command, merge_tags_command,
    # Utility commands
    cleanup_orphaned_links_command
)

# Router imports
from .routers import (
    tag_router, contract_router, relationship_router, 
    bulk_router, analytics_router, maintenance_router
)

# Version info
__version__ = "1.0.0"
__author__ = "Kubera Development Team"
__description__ = "Complete contracts and tags management system"

# Public API exports
__all__ = [
    # Version info
    "__version__", "__author__", "__description__",
    
    # Models
    "Tag", "Contract", "TagContractLink",
    
    # Schemas
    "TagBase", "TagCreate", "TagUpdate", "TagResponse", "TagRead",
    "ContractBase", "ContractCreate", "ContractUpdate", "ContractResponse", "ContractRead", 
    "LinkRequest", "LinkResponse", "BulkLinkRequest",
    "TagFilter", "ContractFilter", "ContractSearch",
    
    # Queries
    "get_tag_query", "list_tags_query", "tag_exists_by_name", "count_tags_query",
    "get_contract_query", "list_contracts_query", "search_contracts_query", 
    "contract_exists_by_reference", "count_contracts_query",
    "link_exists_query", "get_link_query", "get_contracts_for_tag_query", 
    "get_tags_for_contract_query", "get_tag_with_contracts_query", 
    "get_contract_with_tags_query", "count_links_for_tag_query", 
    "count_links_for_contract_query",
    "get_most_used_tags_query", "get_contracts_expiring_soon_query",
    
    # Commands
    "create_tag_command", "update_tag_command", "delete_tag_command",
    "create_contract_command", "update_contract_command", "delete_contract_command", 
    "link_tag_to_contract_command", "unlink_tag_from_contract_command",
    "bulk_link_tags_to_contract_command", "bulk_link_contracts_to_tag_command",
    "bulk_unlink_tags_from_contract_command", "bulk_unlink_contracts_from_tag_command",
    "duplicate_tag_command", "merge_tags_command", "cleanup_orphaned_links_command",
    
    # Routers
    "tag_router", "contract_router", "relationship_router", 
    "bulk_router", "analytics_router", "maintenance_router"
]

# Module configuration
MULTI_TENANT_COMPATIBLE = True
APPLICATION_LEVEL_INTEGRITY = True
FOREIGN_KEY_CONSTRAINTS = False