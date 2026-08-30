# Contract: MedRAG Baseline Endpoint

**Endpoint**: `POST /medrag_baseline/`
**Feature**: 003-comparative-study
**Date**: 2026-08-30

## Purpose

Standard RAG endpoint without uncertainty quantification, replicating the MedRAG approach (ACL 2024) for baseline comparison.

## Request

### Method
POST

### Content-Type
`application/x-www-form-urlencoded`

### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| question | string | Yes | The medical question to answer |

### Example
```http
POST /medrag_baseline/ HTTP/1.1
Content-Type: application/x-www-form-urlencoded

question=What+is+aspirin+used+for%3F
```

## Response

### Status Codes

| Code | Description |
|------|-------------|
| 200 | Successful response |
| 422 | Empty or invalid question |
| 500 | Internal server error |
| 503 | Vector store unavailable |

### Response Schema (200)

```json
{
  "response": "string - The generated answer",
  "sources": ["string - Source document identifiers"],
  "system": "medrag_baseline",
  "confidence": null,
  "doubt_certificate": null,
  " "safety_check": "none",
  "emergency": false,
  "retrieval_scores": [0.85, 0.72, 0.68]
}
```

### Response Fields

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| response | string | No | Generated answer text |
| sources | list[string] | No | Source document identifiers |
| system | string | No | Always `"medrag_baseline"` |
| confidence | float | Yes | Always `null` (no UQ) |
| doubt_certificate | object | Yes | Always `null` (no UQ) |
| safety_check | string | No | Always `"none"` |
| emergency | boolean | No | Always `false` |
| retrieval_scores | list[float] | Yes | Pinecone similarity scores |

### Example Response
```json
{
  "response": "Aspirin is used to treat pain, fever, and inflammation. It is also used in low doses to prevent heart attacks and strokes.",
  "sources": ["medlineplus_aspirin.pdf", "drugs_com_aspirin.pdf"],
  "system": "medrag_baseline",
  "confidence": null,
  "doubt_certificate": null,
  "safety_check": "none",
  "emergency": false,
  "retrieval_scores": [0.85, 0.72, 0.68]
}
```

### Error Response (422)
```json
{
  "detail": "Question cannot be empty"
}
```

### Error Response (503)
```json
{
  "error": "vector_store_unavailable",
  "message": "Pinecone vector store is not accessible"
}
```

## Behavior

1. Validates question is non-empty
2. Embeds question using `all-MiniLM-L6-v2`
3. Queries Pinecone `medical-index` with top-5 retrieval
4. Concatenates retrieved chunks as context
5. Sends to Groq `groq/compound-mini` with standard medical prompt
6. Returns response with sources but no confidence/doubt data

## Differences from UQ-RAG (`/ask/`)

| Feature | `/medrag_baseline/` | `/ask/` |
|---------|---------------------|---------|
| Safety gate | No | Yes |
| Claim verification | No | Yes |
| Conformal prediction | No | Yes |
| Confidence score | No | Yes |
| Doubt certificate | No | Yes |
| Emergency detection | No | Yes |
| Retrieval top-k | 5 | 3 |

## Test Cases

| Question | Expected Behavior |
|----------|-------------------|
| "What is aspirin used for?" | Returns answer with pain/fever keywords |
| "" (empty) | Returns 422 error |
| "I have severe chest pain" | Returns answer WITHOUT emergency detection (baseline) |
| "What is the meaning of life?" | Returns answer WITHOUT doubt certificate (baseline) |
