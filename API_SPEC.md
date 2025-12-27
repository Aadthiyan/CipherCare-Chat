# API Specification

## Authentication
All protected endpoints require a Bearer Token in the Authorization header.

## Endpoints

### 1. Ingestion
- **POST** `/api/v1/ingest/upload`
  - Uploads a FHIR bundle for processing.
  - **Body**: Multipart File.

### 2. Chat
- **POST** `/api/v1/chat/query`
  - Submits a clinical question.
  - **Body**: 
    ```json
    {
      "patient_id": "uuid",
      "question": "string"
    }
    ```
  - **Response**:
    ```json
    {
      "answer": "string",
      "citations": [...]
    }
    ```

### 3. Patient
- **GET** `/api/v1/patients`
  - List available patients (limited by access).
- **GET** `/api/v1/patients/{id}`
  - Get patient details.
