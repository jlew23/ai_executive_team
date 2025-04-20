# API Documentation

This document provides comprehensive information about the AI Executive Team API, including endpoints, request/response formats, authentication, and examples.

## API Overview

The AI Executive Team API is a RESTful API that allows you to interact with the system programmatically. It provides endpoints for managing agents, knowledge base, conversations, and more.

## Authentication

All API requests require authentication using an API key. The API key should be included in the `Authorization` header of the request.

```
Authorization: Bearer YOUR_API_KEY
```

API keys can be generated and managed through the web dashboard by users with administrator privileges.

## Base URL

The base URL for all API endpoints is:

```
https://your-deployment-url.com/api/v1
```

## Response Format

All API responses are in JSON format and include a standard structure:

```json
{
  "success": true,
  "data": { ... },
  "message": "Optional message",
  "errors": [ ... ]
}
```

- `success`: Boolean indicating whether the request was successful
- `data`: The response data (only present if success is true)
- `message`: Optional message providing additional information
- `errors`: Array of error messages (only present if success is false)

## Error Handling

The API uses standard HTTP status codes to indicate the success or failure of a request:

- `200 OK`: The request was successful
- `201 Created`: The resource was successfully created
- `400 Bad Request`: The request was invalid
- `401 Unauthorized`: Authentication failed
- `403 Forbidden`: The authenticated user does not have permission to access the resource
- `404 Not Found`: The requested resource was not found
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: An error occurred on the server

## Rate Limiting

The API implements rate limiting to prevent abuse. The current limits are:

- 100 requests per minute per API key
- 5,000 requests per day per API key

Rate limit information is included in the response headers:

- `X-RateLimit-Limit`: The maximum number of requests allowed in the current time window
- `X-RateLimit-Remaining`: The number of requests remaining in the current time window
- `X-RateLimit-Reset`: The time at which the current rate limit window resets (Unix timestamp)

## Pagination

List endpoints support pagination using the following query parameters:

- `page`: The page number (default: 1)
- `per_page`: The number of items per page (default: 20, max: 100)

Pagination information is included in the response:

```json
{
  "success": true,
  "data": {
    "items": [ ... ],
    "page": 1,
    "per_page": 20,
    "total": 45,
    "total_pages": 3,
    "has_next": true,
    "has_prev": false,
    "next_page": 2,
    "prev_page": null
  }
}
```

## API Endpoints

### Agents

#### List Agents

```
GET /agents
```

Returns a list of all available agents.

**Query Parameters:**
- `page`: The page number (default: 1)
- `per_page`: The number of items per page (default: 20, max: 100)
- `status`: Filter by agent status (optional)

**Response:**
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "director",
        "name": "Director Agent",
        "description": "Orchestrates the team and delegates tasks",
        "status": "active",
        "metrics": {
          "conversations": 120,
          "success_rate": 0.95
        }
      },
      {
        "id": "sales",
        "name": "Sales Agent",
        "description": "Handles sales-related queries and tasks",
        "status": "active",
        "metrics": {
          "conversations": 85,
          "success_rate": 0.92
        }
      }
    ],
    "page": 1,
    "per_page": 20,
    "total": 6,
    "total_pages": 1,
    "has_next": false,
    "has_prev": false,
    "next_page": null,
    "prev_page": null
  }
}
```

#### Get Agent

```
GET /agents/{agent_id}
```

Returns detailed information about a specific agent.

**Path Parameters:**
- `agent_id`: The ID of the agent

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "director",
    "name": "Director Agent",
    "description": "Orchestrates the team and delegates tasks",
    "status": "active",
    "capabilities": [
      "task_delegation",
      "team_coordination",
      "decision_making"
    ],
    "metrics": {
      "conversations": 120,
      "success_rate": 0.95,
      "average_response_time": 1.2,
      "tasks_delegated": 450
    },
    "configuration": {
      "model": "gpt-4",
      "temperature": 0.7,
      "max_tokens": 2000
    }
  }
}
```

#### Update Agent Configuration

```
PATCH /agents/{agent_id}/configuration
```

Updates the configuration of a specific agent.

**Path Parameters:**
- `agent_id`: The ID of the agent

**Request Body:**
```json
{
  "model": "gpt-4",
  "temperature": 0.5,
  "max_tokens": 1500
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "director",
    "configuration": {
      "model": "gpt-4",
      "temperature": 0.5,
      "max_tokens": 1500
    }
  },
  "message": "Agent configuration updated successfully"
}
```

### Knowledge Base

#### List Documents

```
GET /knowledge-base/documents
```

Returns a list of documents in the knowledge base.

**Query Parameters:**
- `page`: The page number (default: 1)
- `per_page`: The number of items per page (default: 20, max: 100)
- `category`: Filter by document category (optional)
- `type`: Filter by document type (optional)

**Response:**
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "doc-123",
        "title": "Sales Strategy 2025",
        "type": "pdf",
        "category": "sales",
        "created_at": "2025-03-15T10:30:00Z",
        "updated_at": "2025-03-15T10:30:00Z",
        "version": 1,
        "size_bytes": 1250000
      },
      {
        "id": "doc-124",
        "title": "Marketing Plan Q2 2025",
        "type": "docx",
        "category": "marketing",
        "created_at": "2025-04-01T14:20:00Z",
        "updated_at": "2025-04-05T09:15:00Z",
        "version": 2,
        "size_bytes": 980000
      }
    ],
    "page": 1,
    "per_page": 20,
    "total": 45,
    "total_pages": 3,
    "has_next": true,
    "has_prev": false,
    "next_page": 2,
    "prev_page": null
  }
}
```

#### Upload Document

```
POST /knowledge-base/documents
```

Uploads a new document to the knowledge base.

**Request Body (multipart/form-data):**
- `file`: The document file
- `title`: Document title
- `category`: Document category (optional)
- `description`: Document description (optional)
- `metadata`: Additional metadata as JSON string (optional)

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "doc-125",
    "title": "Technical Specifications",
    "type": "pdf",
    "category": "technical",
    "created_at": "2025-04-12T07:45:00Z",
    "updated_at": "2025-04-12T07:45:00Z",
    "version": 1,
    "size_bytes": 2100000,
    "processing_status": "processing"
  },
  "message": "Document uploaded successfully and is being processed"
}
```

#### Search Knowledge Base

```
GET /knowledge-base/search
```

Searches the knowledge base for relevant information.

**Query Parameters:**
- `query`: The search query
- `page`: The page number (default: 1)
- `per_page`: The number of items per page (default: 20, max: 100)
- `filter`: JSON string with filter criteria (optional)
- `hybrid`: Whether to use hybrid search (default: true)

**Response:**
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "chunk-789",
        "document_id": "doc-123",
        "document_title": "Sales Strategy 2025",
        "content": "Our target market for 2025 includes enterprise customers in the healthcare and finance sectors...",
        "relevance_score": 0.92,
        "page_number": 5
      },
      {
        "id": "chunk-456",
        "document_id": "doc-124",
        "document_title": "Marketing Plan Q2 2025",
        "content": "The marketing strategy for healthcare clients focuses on demonstrating ROI and compliance benefits...",
        "relevance_score": 0.85,
        "page_number": 12
      }
    ],
    "page": 1,
    "per_page": 20,
    "total": 8,
    "total_pages": 1,
    "has_next": false,
    "has_prev": false,
    "next_page": null,
    "prev_page": null
  }
}
```

### Conversations

#### Start Conversation

```
POST /conversations
```

Starts a new conversation with an agent.

**Request Body:**
```json
{
  "agent_id": "sales",
  "message": "What are our current sales targets for Q2?",
  "metadata": {
    "user_id": "user-456",
    "department": "marketing"
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "conversation_id": "conv-789",
    "agent_id": "sales",
    "messages": [
      {
        "id": "msg-001",
        "role": "user",
        "content": "What are our current sales targets for Q2?",
        "timestamp": "2025-04-12T07:50:00Z"
      },
      {
        "id": "msg-002",
        "role": "agent",
        "content": "Based on our current sales strategy, the Q2 targets are $2.5M for enterprise clients and $1.8M for mid-market clients. These targets represent a 15% increase over Q1 performance. Would you like to see the breakdown by region or product line?",
        "timestamp": "2025-04-12T07:50:05Z",
        "sources": [
          {
            "document_id": "doc-123",
            "document_title": "Sales Strategy 2025",
            "page_number": 8
          }
        ]
      }
    ],
    "created_at": "2025-04-12T07:50:00Z",
    "updated_at": "2025-04-12T07:50:05Z",
    "status": "active"
  }
}
```

#### Send Message

```
POST /conversations/{conversation_id}/messages
```

Sends a message to an existing conversation.

**Path Parameters:**
- `conversation_id`: The ID of the conversation

**Request Body:**
```json
{
  "message": "Yes, please show me the breakdown by region."
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "message_id": "msg-003",
    "conversation_id": "conv-789",
    "content": "Yes, please show me the breakdown by region.",
    "timestamp": "2025-04-12T07:51:00Z"
  }
}
```

#### Get Conversation

```
GET /conversations/{conversation_id}
```

Returns details of a specific conversation.

**Path Parameters:**
- `conversation_id`: The ID of the conversation

**Response:**
```json
{
  "success": true,
  "data": {
    "conversation_id": "conv-789",
    "agent_id": "sales",
    "messages": [
      {
        "id": "msg-001",
        "role": "user",
        "content": "What are our current sales targets for Q2?",
        "timestamp": "2025-04-12T07:50:00Z"
      },
      {
        "id": "msg-002",
        "role": "agent",
        "content": "Based on our current sales strategy, the Q2 targets are $2.5M for enterprise clients and $1.8M for mid-market clients. These targets represent a 15% increase over Q1 performance. Would you like to see the breakdown by region or product line?",
        "timestamp": "2025-04-12T07:50:05Z",
        "sources": [
          {
            "document_id": "doc-123",
            "document_title": "Sales Strategy 2025",
            "page_number": 8
          }
        ]
      },
      {
        "id": "msg-003",
        "role": "user",
        "content": "Yes, please show me the breakdown by region.",
        "timestamp": "2025-04-12T07:51:00Z"
      },
      {
        "id": "msg-004",
        "role": "agent",
        "content": "Here's the regional breakdown for Q2 sales targets:\n\n- North America: $1.8M\n- Europe: $1.2M\n- Asia-Pacific: $0.9M\n- Rest of World: $0.4M\n\nNorth America and Europe are expected to see the highest growth rates at 18% and 16% respectively.",
        "timestamp": "2025-04-12T07:51:05Z",
        "sources": [
          {
            "document_id": "doc-123",
            "document_title": "Sales Strategy 2025",
            "page_number": 10
          }
        ]
      }
    ],
    "created_at": "2025-04-12T07:50:00Z",
    "updated_at": "2025-04-12T07:51:05Z",
    "status": "active",
    "metadata": {
      "user_id": "user-456",
      "department": "marketing"
    }
  }
}
```

### Analytics

#### Get Agent Performance

```
GET /analytics/agents/{agent_id}/performance
```

Returns performance metrics for a specific agent.

**Path Parameters:**
- `agent_id`: The ID of the agent

**Query Parameters:**
- `start_date`: Start date for the metrics (ISO format)
- `end_date`: End date for the metrics (ISO format)
- `interval`: Time interval for data points (hourly, daily, weekly, monthly)

**Response:**
```json
{
  "success": true,
  "data": {
    "agent_id": "sales",
    "metrics": {
      "conversations": {
        "total": 85,
        "data_points": [
          {"date": "2025-04-01", "value": 12},
          {"date": "2025-04-02", "value": 8},
          {"date": "2025-04-03", "value": 15}
        ]
      },
      "success_rate": {
        "average": 0.92,
        "data_points": [
          {"date": "2025-04-01", "value": 0.91},
          {"date": "2025-04-02", "value": 0.94},
          {"date": "2025-04-03", "value": 0.93}
        ]
      },
      "response_time": {
        "average": 1.8,
        "data_points": [
          {"date": "2025-04-01", "value": 1.9},
          {"date": "2025-04-02", "value": 1.7},
          {"date": "2025-04-03", "value": 1.8}
        ]
      }
    },
    "start_date": "2025-04-01",
    "end_date": "2025-04-03",
    "interval": "daily"
  }
}
```

## Webhook Integration

The API supports webhook notifications for various events. Webhooks can be configured in the web dashboard.

### Webhook Events

- `conversation.created`: Triggered when a new conversation is created
- `conversation.message.created`: Triggered when a new message is added to a conversation
- `knowledge_base.document.uploaded`: Triggered when a new document is uploaded
- `knowledge_base.document.processed`: Triggered when document processing is complete

### Webhook Payload

```json
{
  "event": "conversation.message.created",
  "timestamp": "2025-04-12T07:51:05Z",
  "data": {
    "conversation_id": "conv-789",
    "message_id": "msg-004",
    "agent_id": "sales",
    "role": "agent",
    "content": "Here's the regional breakdown for Q2 sales targets...",
    "metadata": {
      "user_id": "user-456",
      "department": "marketing"
    }
  }
}
```

## API Client Libraries

We provide official client libraries for the following languages:

- [Python](https://github.com/ai-executive-team/python-client)
- [JavaScript](https://github.com/ai-executive-team/js-client)
- [Java](https://github.com/ai-executive-team/java-client)

## API Versioning

The API uses versioning to ensure backward compatibility. The current version is `v1`. When breaking changes are introduced, a new version will be released.

## Support

If you encounter any issues or have questions about the API, please contact our support team at api-support@ai-executive-team.com.
