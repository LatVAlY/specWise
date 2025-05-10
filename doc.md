 # Pipelines Overview

 The following diagram illustrates the high-level workflow of the system, showing how requests flow from the API through databases, queues, workers, and external services like OpenAI.

 ```mermaid
 flowchart LR
   subgraph Client Layer
     A[Client]
   end
   subgraph API Layer
     B[API Gateway]
     C[Application Server]
   end
   subgraph Database Layer
     D[(Primary DB)]
     I[(Redis Cache)]
   end
   subgraph Queue Layer
     E[(Message Queue)]
   end
   subgraph Worker Layer
     F[Worker Process]
   end
   subgraph External Services
     G[(OpenAI)]
     H[(External API)]
   end

   A --> B
   B --> C
   C --> D
   C --> E
   C --> I
   E --> F
   F --> D
   F --> I
   F --> G
   F --> H

   style A fill:#f0f0f0,stroke:#333,stroke-width:1px
   style B fill:#a2d5f2,stroke:#333,stroke-width:1px
   style C fill:#a2d5f2,stroke:#333,stroke-width:1px
   style D fill:#f7cac9,stroke:#333,stroke-width:1px
   style I fill:#88d8b0,stroke:#333,stroke-width:1px
   style E fill:#f1e3dd,stroke:#333,stroke-width:1px
   style F fill:#ffeadb,stroke:#333,stroke-width:1px
   style G fill:#c06c84,stroke:#333,stroke-width:1px
   style H fill:#6c5b7b,stroke:#333,stroke-width:1px
 ```