| Source Component | Destination Component | Protocol | Data Transferred | Security |
|:---|:---|:---|:---|:---|
| **Frontend** | **Backend API** | HTTPS (REST) | User queries, JWT Token | TLS 1.3 |
| **Backend API** | **Auth0** | HTTPS | Credentials, Tokens | TLS 1.3 |
| **Backend API** | **CyborgDB** | TCP (Postgres) | Encrypted Vectors, Queries | SSL + Auth |
| **Backend API** | **Private LLM** | HTTP/gRPC | Context, Prompts | Internal Network Only |
| **Backend API** | **Key Manager** | HTTPS | Key Requests | IAM Roles / mTLS |
| **Ingestion Svc** | **De-ID Model** | Internal Lib | Raw Text | In-Memory |
| **Ingestion Svc** | **Embed Model** | Internal Lib | De-ID Text | In-Memory |
| **Backend API** | **Audit Log** | TCP (Postgres) | User ID, Query Metadata | SSL |
