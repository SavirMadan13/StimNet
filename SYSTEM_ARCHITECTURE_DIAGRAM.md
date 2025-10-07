# StimNet System Architecture Diagram

## Overview
StimNet is a distributed data access and remote execution framework that enables secure, federated analysis across multiple institutions while preserving data privacy. The system follows a peer-to-peer model where each node can act as both a data provider and computation requester.

## High-Level Architecture

```mermaid
graph TB
    subgraph "Institution A"
        A_Client[Client SDK]
        A_Node[Distributed Node Server]
        A_DB[(SQLite/PostgreSQL)]
        A_Data[(Protected Data)]
        A_Docker[Docker Execution Engine]
        A_Nginx[Nginx Proxy]
        
        A_Client --> A_Node
        A_Node --> A_DB
        A_Node --> A_Data
        A_Node --> A_Docker
        A_Nginx --> A_Node
    end
    
    subgraph "Institution B"
        B_Client[Client SDK]
        B_Node[Distributed Node Server]
        B_DB[(SQLite/PostgreSQL)]
        B_Data[(Protected Data)]
        B_Docker[Docker Execution Engine]
        B_Nginx[Nginx Proxy]
        
        B_Client --> B_Node
        B_Node --> B_DB
        B_Node --> B_Data
        B_Node --> B_Docker
        B_Nginx --> B_Node
    end
    
    subgraph "Institution C"
        C_Client[Client SDK]
        C_Node[Distributed Node Server]
        C_DB[(SQLite/PostgreSQL)]
        C_Data[(Protected Data)]
        C_Docker[Docker Execution Engine]
        C_Nginx[Nginx Proxy]
        
        C_Client --> C_Node
        C_Node --> C_DB
        C_Node --> C_Data
        C_Node --> C_Docker
        C_Nginx --> C_Node
    end
    
    %% Cross-institutional connections
    A_Nginx -.->|HTTPS/TLS| B_Nginx
    B_Nginx -.->|HTTPS/TLS| C_Nginx
    A_Nginx -.->|HTTPS/TLS| C_Nginx
    
    %% External connections
    External[External Researcher] --> A_Client
    External --> B_Client
    External --> C_Client
```

## Detailed Component Architecture

```mermaid
graph TB
    subgraph "Client Layer"
        SDK[Client SDK]
        Examples[Example Scripts]
        RemoteClient[Remote Client Test]
    end
    
    subgraph "API Gateway Layer"
        Nginx[Nginx Reverse Proxy]
        TLS[TLS/mTLS Termination]
        RateLimit[Rate Limiting]
        
        Nginx --> TLS
        Nginx --> RateLimit
    end
    
    subgraph "Application Layer"
        MainAPI[Main FastAPI Server<br/>distributed_node/main.py]
        SiteAPI[Site FastAPI Server<br/>site_app/main.py]
        Auth[Authentication Module<br/>security.py]
        Config[Configuration<br/>config.py]
        
        MainAPI --> Auth
        MainAPI --> Config
        SiteAPI --> Config
    end
    
    subgraph "Business Logic Layer"
        JobExecutor[Job Executor<br/>job_executor.py]
        Security[Security Validator<br/>security.py]
        Models[Data Models<br/>models.py]
        
        JobExecutor --> Security
        JobExecutor --> Models
    end
    
    subgraph "Execution Layer"
        Docker[Docker Engine]
        PythonContainer[Python Container]
        RContainer[R Container]
        WorkerScript[Worker Script<br/>worker/run_job.py]
        
        Docker --> PythonContainer
        Docker --> RContainer
        Docker --> WorkerScript
    end
    
    subgraph "Data Layer"
        Database[(Database<br/>SQLite/PostgreSQL)]
        DataCatalogs[Data Catalogs]
        ReadOnlyData[Read-Only Data Views]
        AuditLogs[Audit Logs]
        
        Database --> DataCatalogs
        Database --> AuditLogs
    end
    
    subgraph "Storage Layer"
        SubjectsCSV[subjects.csv]
        OutcomesCSV[outcomes.csv]
        PathsCSV[paths.csv]
        NIfTIFiles[NIfTI Files]
        Masks[ROI Masks]
        
        ReadOnlyData --> SubjectsCSV
        ReadOnlyData --> OutcomesCSV
        ReadOnlyData --> PathsCSV
        ReadOnlyData --> NIfTIFiles
        ReadOnlyData --> Masks
    end
    
    %% Connections
    SDK --> Nginx
    Nginx --> MainAPI
    Nginx --> SiteAPI
    MainAPI --> JobExecutor
    SiteAPI --> WorkerScript
    JobExecutor --> Docker
    MainAPI --> Database
    SiteAPI --> ReadOnlyData
    Docker --> ReadOnlyData
```

## Data Flow Architecture

```mermaid
sequenceDiagram
    participant Client as Client SDK
    participant Auth as Authentication
    participant API as Node API Server
    participant Validator as Security Validator
    participant Executor as Job Executor
    participant Docker as Docker Container
    participant Data as Protected Data
    participant DB as Database
    
    Note over Client,DB: Job Submission Flow
    
    Client->>Auth: 1. Authenticate (JWT)
    Auth-->>Client: Access Token
    
    Client->>API: 2. Discover Data Catalogs
    API->>DB: Query Available Catalogs
    DB-->>API: Catalog Metadata
    API-->>Client: Available Data Catalogs
    
    Client->>API: 3. Submit Analysis Script
    API->>Validator: 4. Validate Script Security
    Validator-->>API: Security Check Results
    
    alt Script is Safe
        API->>DB: 5. Store Job Record
        API->>Executor: 6. Queue Job for Execution
        API-->>Client: Job ID & Status
        
        Executor->>Docker: 7. Create Sandboxed Container
        Docker->>Data: 8. Mount Read-Only Data
        Docker->>Docker: 9. Execute Script
        Docker->>Data: 10. Process Data (No Export)
        Docker-->>Executor: 11. Return Aggregated Results
        
        Executor->>DB: 12. Store Results
        
        Note over Executor,DB: Privacy Check
        alt Cohort Size >= K_MIN
            Executor->>DB: Store Final Results
        else Cohort Size < K_MIN
            Executor->>DB: Block Results (Privacy)
        end
        
        Client->>API: 13. Poll Job Status
        API->>DB: Query Job Status
        DB-->>API: Job Results (if allowed)
        API-->>Client: Results or "Blocked"
        
    else Script is Unsafe
        API-->>Client: Security Validation Failed
    end
```

## Security Architecture

```mermaid
graph TB
    subgraph "External Threats"
        Attacker[Malicious Actor]
        BadScript[Malicious Script]
        DataTheft[Data Exfiltration Attempt]
    end
    
    subgraph "Security Perimeter"
        WAF[Web Application Firewall]
        TLS[TLS 1.3 Encryption]
        mTLS[Mutual TLS (Optional)]
        RateLimit[Rate Limiting]
    end
    
    subgraph "Authentication & Authorization"
        JWT[JWT Tokens]
        RBAC[Role-Based Access Control]
        APIKeys[API Key Management]
        NodeAuth[Node-to-Node Auth]
    end
    
    subgraph "Script Security"
        ScriptValidator[Script Security Validator]
        Patterns[Dangerous Pattern Detection]
        Sandbox[Docker Sandbox]
        NetworkIsolation[Network Isolation]
    end
    
    subgraph "Data Protection"
        KAnonymity[K-Anonymity Enforcement]
        DifferentialPrivacy[Differential Privacy]
        AggregationOnly[Aggregation-Only Results]
        ReadOnlyMount[Read-Only Data Mounts]
    end
    
    subgraph "Monitoring & Auditing"
        AuditLog[Comprehensive Audit Logs]
        SecurityMonitoring[Security Event Monitoring]
        AccessLogging[Access Pattern Analysis]
    end
    
    %% Threat mitigation flows
    Attacker -.->|Blocked by| WAF
    BadScript -.->|Detected by| ScriptValidator
    DataTheft -.->|Prevented by| NetworkIsolation
    
    %% Security layers
    WAF --> TLS
    TLS --> JWT
    JWT --> ScriptValidator
    ScriptValidator --> Sandbox
    Sandbox --> KAnonymity
    KAnonymity --> AuditLog
```

## Deployment Architecture

```mermaid
graph TB
    subgraph "Production Environment"
        subgraph "Load Balancer"
            LB[Nginx Load Balancer]
            SSL[SSL Termination]
        end
        
        subgraph "Application Tier"
            App1[Node Server 1]
            App2[Node Server 2]
            App3[Node Server N]
        end
        
        subgraph "Execution Tier"
            DockerHost1[Docker Host 1]
            DockerHost2[Docker Host 2]
            DockerHostN[Docker Host N]
        end
        
        subgraph "Data Tier"
            PrimaryDB[(Primary Database)]
            ReplicaDB[(Read Replica)]
            DataStore[(Protected Data Storage)]
        end
        
        subgraph "Monitoring"
            Prometheus[Prometheus]
            Grafana[Grafana]
            AlertManager[Alert Manager]
        end
    end
    
    subgraph "Development Environment"
        DevApp[Development Server]
        DevDB[(SQLite Database)]
        LocalDocker[Local Docker]
    end
    
    %% Production connections
    LB --> App1
    LB --> App2
    LB --> App3
    
    App1 --> DockerHost1
    App2 --> DockerHost2
    App3 --> DockerHostN
    
    App1 --> PrimaryDB
    App2 --> ReplicaDB
    App3 --> ReplicaDB
    
    App1 --> DataStore
    App2 --> DataStore
    App3 --> DataStore
    
    App1 --> Prometheus
    App2 --> Prometheus
    App3 --> Prometheus
    
    Prometheus --> Grafana
    Prometheus --> AlertManager
    
    %% Development connections
    DevApp --> DevDB
    DevApp --> LocalDocker
```

## Technology Stack

### Backend Services
- **FastAPI**: RESTful API framework with automatic OpenAPI documentation
- **SQLAlchemy**: ORM for database operations with support for SQLite and PostgreSQL
- **Pydantic**: Data validation and settings management
- **Docker**: Containerized script execution environment
- **Nginx**: Reverse proxy, load balancing, and TLS termination

### Security & Authentication
- **JWT (JSON Web Tokens)**: Stateless authentication
- **bcrypt**: Password hashing
- **TLS 1.3**: Transport layer security
- **mTLS**: Mutual authentication (optional)

### Data Processing
- **pandas**: Data manipulation and analysis
- **numpy**: Numerical computing
- **scipy**: Scientific computing
- **nibabel**: Neuroimaging data I/O
- **scikit-learn**: Machine learning utilities

### Monitoring & Observability
- **Prometheus**: Metrics collection
- **Grafana**: Visualization and dashboards
- **Structured Logging**: JSON-formatted application logs

### Development & Deployment
- **Docker Compose**: Multi-container orchestration
- **pytest**: Testing framework
- **GitHub Actions**: CI/CD pipeline
- **Poetry/pip**: Dependency management

## Key Features

### Privacy Preservation
- **K-Anonymity**: Minimum cohort size enforcement (configurable K_MIN)
- **Differential Privacy**: Optional noise injection for enhanced privacy
- **Aggregation-Only Results**: No individual-level data export
- **Read-Only Data Access**: Immutable data views during execution

### Security Controls
- **Sandboxed Execution**: Network-isolated Docker containers
- **Script Validation**: Pattern-based security scanning
- **Resource Limits**: CPU, memory, and execution time constraints
- **Audit Trail**: Comprehensive logging of all operations

### Scalability & Reliability
- **Horizontal Scaling**: Multiple node servers behind load balancer
- **Async Processing**: Non-blocking job execution
- **Database Replication**: Read replicas for improved performance
- **Health Monitoring**: Automated health checks and alerting

### Developer Experience
- **OpenAPI Documentation**: Auto-generated API documentation
- **Client SDK**: Python SDK for easy integration
- **Example Scripts**: Ready-to-use analysis examples
- **Multi-Language Support**: Python, R, SQL, and Jupyter notebooks
