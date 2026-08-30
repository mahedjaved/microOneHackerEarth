# Contract: No-RAG (Direct LLM) Endpoint

**Endpoint**: `POST /no_rag/`
**Feature**: 003-comparative-study
**Date**: 2026-08-30

## Purpose

Direct LLM endpoint without any retrieval or grounding, serving as the simplest baseline for comparison.

## Request

### Method
POST

### Content-Type
`application/x-www-form-urlencoded`

### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| question | string | Yes | The question to answer |

### Example
```http
POST /no_rag/ HTTP/1.1
Content-Type: application/x-www-form-urlencoded

question=What+is+aspirin+used+for%3F
```

## Response

### Status Codes

| Code | Description |
|------|-------------|
| 200 | Successful response |
| 422 | Empty or invalid question |
| 429 | Rate limit exceeded |
| 500 | Internal server error |

### Response Schema (200)

```json
{
  "response": "string - The generated answer",
  "system": "no_rag"
}
```

### Response Fields

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| response | string | No | Generated answer text |
| system | string | No | Always `"no_rag"` |

### Example Response
```json
{
  "response": "Aspirin is a common medication used to treat pain, fever, and inflammation. It belongs to a class of drugs called nonsteroidal anti-inflammatory drugs (NSAIDs).",
  "system": "no_rag"
}
```

### Error Response (422)
```json
{
  "detail": "Question cannot be empty"
}
```

### Error Response (429)
```json
{
  "error": "rate_limit_exceeded",
  "message": "Groq API rate limit exceeded",
  "retry_after": 30
}
```

## Behavior

1. Validates question is non-empty
2. Sends question directly to Groq `groq/compound-mini` with system prompt
3. Returns response without any sources, confidence, or grounding

## System Prompt

```
You are a helpful assistant. Answer questions based on your general knowledge.
If you don't know, say so.
```

## Differences from UQ-RAG (`/ask/`)

| Feature | `/no_rag/` | `/ask/` |
|---------|------------|---------|
| Retrieval | No | Yes (Pinecone) |
| Sources | No | Yes |
| Safety gate | No | Yes |
| Confidence score | No | Yes |
| Doubt certificate | No | Yes |
| Emergency detection | No | Yes |

## Test Cases

| Question | Expected Behavior |
|----------|-------------------|
| "What is aspirin used for?" | Returns general knowledge answer |
| "" (empty) | Returns 422 error |
| "I have severe chest pain" | Returns general answer WITHOUT emergency detection |
| "What is the meaning of life?" | Returns general answer WITHOUT doubt certificate |
