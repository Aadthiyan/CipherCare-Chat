import os
import time
import logging
import uuid
from datetime import datetime
from dotenv import load_dotenv

load_dotenv() # Load vars from .env

from fastapi import FastAPI, Depends, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Import Modules
from backend.auth import (
    create_access_token, 
    verify_password, 
    FAKE_USERS_DB, 
    ACCESS_TOKEN_EXPIRE_MINUTES,
    require_role, 
    get_current_user,
    check_patient_access
)
from backend.auth_enhanced import (
    authenticate_user,
    create_user,
    create_access_token as create_access_token_enhanced,
    create_refresh_token,
    verify_token,
    get_current_user as get_current_user_enhanced,
    create_password_reset_token,
    reset_password,
    change_password,
    get_user,
    get_user_by_email,
    TokenData as TokenDataEnhanced,
    revoke_refresh_token
)
from backend.models import (
    LoginRequest, 
    PatientSearchRequest, 
    QueryResponse, 
    TokenData, 
    Token, 
    SourceDocument,
    SignupRequest,
    OTPVerifyRequest,
    TokenResponse,
    UserResponse,
    PasswordResetRequest,
    PasswordResetConfirm,
    ChangePasswordRequest
)
from backend.logging_config import setup_logging
from backend.multi_database_manager import get_multi_db_manager
from backend.exceptions import (
    CiperCareException,
    ServiceInitializationError,
    SearchError,
    EmbeddingError,
    LLMError,
    AuthorizationError,
    PatientAccessDeniedError,
    ValidationError
)
from embeddings.embedder import ClinicalEmbedder
from backend.llm import LLMService

# 1. Setup Logging
setup_logging()
logger = logging.getLogger("backend")

# 2. Setup Rate Limiter
limiter = Limiter(key_func=get_remote_address)

# 3. Initialize App
app = FastAPI(
    title="CiperCare API",
    description="HIPAA-Compliant Encrypted Medical Chatbot Backend",
    version="0.1.0"
)

# Include admin routes (for patient data upload)
from backend.admin_routes import router as admin_router
app.include_router(admin_router)

# Global Services
services = {}

@app.on_event("startup")
async def startup_event():
    global services
    service_status = {}
    
    try:
        # Initialize PostgreSQL connection pool for authentication
        from backend.database import init_db_pool
        # Use smaller pool size for Render's connection limits
        if not init_db_pool(min_conn=2, max_conn=10):
            raise ServiceInitializationError(
                "PostgreSQL",
                "Failed to initialize database connection pool",
                details={"check": "DATABASE_URL in .env"}
            )
        service_status["postgres"] = "✓"
        logger.info("PostgreSQL connection pool initialized (2-10 connections)")
        
        # Load Embedder (768-dim model for maximum quality)
        embedding_model = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-mpnet-base-v2")
        try:
            services["embedder"] = ClinicalEmbedder(model_name=embedding_model)
            service_status["embedder"] = "✓"
            logger.info(f"Loaded embedding model: {embedding_model}")
        except Exception as e:
            service_status["embedder"] = "✗"
            raise ServiceInitializationError(
                "Embedder",
                str(e),
                details={"model": embedding_model, "error_type": type(e).__name__}
            )
        
        # Load Vector Database (Multi-Database with sharding)
        try:
            # Initialize multi-database manager
            services["db"] = await get_multi_db_manager()
            logger.info("Loaded Multi-Database manager (PostgreSQL + pgvector)")
            
            services["crypto"] = None  # Multi-DB doesn't have built-in crypto service
            service_status["db"] = "✓"
        except ServiceInitializationError:
            service_status["db"] = "✗"
            raise
        except Exception as e:
            service_status["db"] = "✗"
            raise ServiceInitializationError(
                "Vector Database",
                str(e),
                details={"db_type": "multi-database", "error_type": type(e).__name__}
            )
        
        # Load LLM
        try:
            services["llm"] = LLMService()
            service_status["llm"] = "✓"
        except Exception as e:
            service_status["llm"] = "⚠ (Optional)"
            services["llm"] = None
        
        # Print clean startup summary
        print("\n" + "="*50)
        print("  BACKEND SERVICES STATUS")
        print("="*50)
        for service, status in service_status.items():
            print(f"  {status} {service.upper():<15} Ready")
        print("="*50)
        print("  🚀 Backend online on http://0.0.0.0:8000")
        print("="*50 + "\n")
        
        logger.info(f"Services initialized: {list(services.keys())}")
        
    except ServiceInitializationError as e:
        print(f"\n✗ {e.message}: {e.details}\n")
        logger.error(f"Service Initialization Failed: {e.message}")
        raise
    except Exception as e:
        print(f"\n✗ Unexpected error: {str(e)[:100]}\n")
        logger.error(f"Unexpected service initialization error: {str(e)[:100]}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown"""
    try:
        # Optional: Close database pool on shutdown
        # from backend.database import close_db_pool
        # close_db_pool()
        logger.info("Application shutdown event called")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

# 4. Global Exception Handlers
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# 5. Middleware
# CORS
origins = [
    "http://localhost:3000",  # Next.js local
    "http://localhost:8000",  # Local backend
    "https://cipher-care.vercel.app",  # Vercel production
    "https://ciphercare-chat.vercel.app",  # Vercel production (alternative)
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request Logging Middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    # Skip logging for /docs and /openapi.json to reduce clutter
    if request.url.path not in ["/docs", "/openapi.json", "/favicon.ico"]:
        status_emoji = "✓" if response.status_code < 400 else "✗"
        logger.info(f"{status_emoji} {request.method} {request.url.path} → {response.status_code} ({process_time:.3f}s)")
    
    return response

# --- Endpoints ---

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "CiperCare Backend"}

@app.get("/ready")
async def readiness_check():
    # Check DB/Cyborg connectivity here
    # For now, just return true
    return {"status": "ready", "database": "connected"}

@app.post("/token", response_model=Token)
@limiter.limit("5/minute")
async def login_for_access_token(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    user_dict = FAKE_USERS_DB.get(form_data.username)
    if not user_dict:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
        
    hashed_password = user_dict["hashed_password"]
    if not verify_password(form_data.password, hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
        
    # Generate Token
    access_token = create_access_token(
        data={"sub": user_dict["username"], "roles": user_dict["roles"]}
    )
    return {"access_token": access_token, "token_type": "bearer"}

# --- Enhanced Authentication Endpoints ---

@app.post("/auth/signup")
@limiter.limit("3/minute")
async def signup(request: Request, signup_data: SignupRequest):
    """Register a new clinician account with OTP verification"""
    try:
        import bcrypt
        from backend.db_operations import (
            create_user_db, get_user_by_email, get_user_by_username, 
            generate_otp, store_otp
        )
        
        logger.debug(f"Signup request received: {signup_data.dict()}")
        
        # Validation
        if signup_data.password and len(signup_data.password) < 8:
            raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
        
        # Check if user already exists
        existing_user = get_user_by_username(signup_data.username)
        if existing_user:
            logger.warning(f"Signup failed: username '{signup_data.username}' already exists")
            raise HTTPException(status_code=400, detail="Username already taken")
        
        existing_email = get_user_by_email(signup_data.email)
        if existing_email:
            logger.warning(f"Signup failed: email '{signup_data.email}' already registered")
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Hash password
        password_hash = bcrypt.hashpw(signup_data.password.encode(), bcrypt.gensalt()).decode()
        
        # Create user in PostgreSQL database
        user = create_user_db(
            username=signup_data.username,
            email=signup_data.email,
            password_hash=password_hash,
            full_name=signup_data.full_name,
            roles=[signup_data.role or "resident"],
            assigned_patients=["any"] if signup_data.role == "attending" else ["P123", "P456"],
            department=signup_data.department
        )
        
        if not user:
            logger.error(f"Failed to create user in database: {signup_data.username}")
            raise HTTPException(status_code=500, detail="Registration failed")
        
        # Generate OTP code
        otp_code = generate_otp(length=6)
        store_otp(user['id'], otp_code, expires_in_minutes=15)
        
        # Send OTP via email
        from backend.email_service import email_service
        email_sent = email_service.send_otp_email(
            email=signup_data.email,
            full_name=signup_data.full_name,
            otp_code=otp_code
        )
        
        if email_sent:
            logger.info(f"New user registered: {signup_data.username} | OTP sent to {signup_data.email}")
        else:
            logger.warning(f"New user registered: {signup_data.username} | OTP code: {otp_code} (EMAIL FAILED TO SEND)")
        
        return {
            "status": "success",
            "message": "Account created! Please check your email for the verification code.",
            "user": {
                "id": str(user["id"]),
                "username": user["username"],
                "email": user["email"],
                "full_name": user["full_name"],
                "roles": user["roles"],
                "email_verified": False
            },
            "verification_required": True,
            "email_sent": email_sent
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Signup error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Registration failed")


@app.post("/auth/verify-otp")
@limiter.limit("5/minute")
async def verify_otp_endpoint(request: Request, otp_data: OTPVerifyRequest):
    """Verify user's account using OTP code"""
    try:
        from backend.db_operations import verify_otp as verify_otp_db
        
        logger.debug(f"OTP verification attempt for user: {otp_data.user_id}")
        
        # Verify the OTP
        if not verify_otp_db(otp_data.user_id, otp_data.otp_code):
            raise HTTPException(status_code=400, detail="Invalid or expired OTP code")
        
        logger.info(f"Account verified for user: {otp_data.user_id}")
        
        return {
            "status": "success",
            "message": "Account verified successfully! You can now login.",
            "user_id": otp_data.user_id
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OTP verification error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="OTP verification failed")


@app.post("/auth/verify-email")
@limiter.limit("5/minute")
async def verify_email(request: Request, token: str):
    """Verify user's email address using verification token (DEPRECATED - use /auth/verify-otp)"""
    try:
        from backend.db_operations import verify_email_token, mark_email_verified
        
        # Verify the token
        user_data = verify_email_token(token)
        if not user_data:
            raise HTTPException(status_code=400, detail="Invalid or expired verification token")
        
        # Mark email as verified
        if not mark_email_verified(user_data['id']):
            raise HTTPException(status_code=500, detail="Failed to verify email")
        
        logger.info(f"Email verified for user: {user_data['username']}")
        
        return {
            "status": "success",
            "message": "Email verified successfully! You can now login.",
            "user": {
                "username": user_data["username"],
                "email": user_data["email"]
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Email verification error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Email verification failed")


@app.post("/auth/login")
@limiter.limit("5/minute")
async def login(request: Request, login_data: LoginRequest):
    """Authenticate user and return access + refresh tokens"""
    try:
        user = authenticate_user(login_data.username, login_data.password)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid username or password")
        
        # Check if email is verified
        if not user.get("email_verified"):
            raise HTTPException(
                status_code=403, 
                detail="Email not verified. Check your inbox for verification email.",
                headers={"X-Email-Verification-Required": "true"}
            )
        
        # Create tokens
        access_token = create_access_token_enhanced(
            data={
                "sub": user["username"],
                "roles": user["roles"]
            }
        )
        refresh_token = create_refresh_token(user["username"])
        
        logger.info(f"User logged in: {login_data.username}")
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": {
                "username": user["username"],
                "email": user["email"],
                "full_name": user["full_name"],
                "roles": user["roles"]
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Authentication failed")


@app.post("/auth/refresh")
@limiter.limit("10/minute")
async def refresh_access_token(request: Request, refresh_token: str):
    """Get new access token using refresh token"""
    try:
        payload = verify_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        
        username = payload.get("sub")
        user = get_user(username)
        
        if not user or not user.get("is_active"):
            raise HTTPException(status_code=401, detail="User inactive or not found")
        
        # Create new access token
        new_access_token = create_access_token_enhanced(
            data={
                "sub": user["username"],
                "roles": user["roles"]
            }
        )
        
        logger.info(f"Access token refreshed for: {username}")
        
        return {
            "access_token": new_access_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {e}", exc_info=True)
        raise HTTPException(status_code=401, detail="Token refresh failed")


@app.post("/auth/logout")
@limiter.limit("10/minute")
async def logout(request: Request, token: str = Depends(get_current_user_enhanced)):
    """Logout user (revoke token)"""
    # In production, add token to revocation list
    logger.info(f"User logged out: {token.username}")
    return {"status": "success", "message": "Logged out successfully"}


@app.post("/auth/password-reset")
@limiter.limit("3/minute")
async def request_password_reset(request: Request, email_data: dict):
    """Request password reset (send email with reset link)"""
    try:
        email = email_data.get("email")
        if not email:
            raise HTTPException(status_code=400, detail="Email required")
        
        user = get_user_by_email(email)
        if not user:
            # Don't reveal if email exists (security)
            logger.warning(f"Password reset requested for non-existent email: {email}")
        else:
            reset_token = create_password_reset_token(email)
            # TODO: Send email with reset link
            # In production: send_reset_email(email, reset_token)
            logger.info(f"Password reset token created for: {email}")
        
        # Always return success for security
        return {
            "status": "success",
            "message": "If email exists, reset link will be sent shortly"
        }
    except Exception as e:
        logger.error(f"Password reset error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Password reset failed")


@app.post("/auth/password-reset-confirm")
@limiter.limit("5/minute")
async def confirm_password_reset(request: Request, reset_data: PasswordResetConfirm):
    """Confirm password reset with token"""
    try:
        if reset_password(reset_data.token, reset_data.new_password):
            logger.info("Password reset confirmed")
            return {"status": "success", "message": "Password reset successfully. Please login."}
        else:
            raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password reset confirm error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Password reset failed")


@app.post("/auth/change-password")
@limiter.limit("5/minute")
async def change_user_password(
    request: Request,
    password_data: ChangePasswordRequest,
    current_user: TokenData = Depends(get_current_user_enhanced)
):
    """Change password for authenticated user"""
    try:
        if change_password(current_user.username, password_data.old_password, password_data.new_password):
            logger.info(f"Password changed for: {current_user.username}")
            return {"status": "success", "message": "Password changed successfully"}
        else:
            raise HTTPException(status_code=400, detail="Invalid password")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Change password error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Password change failed")


@app.get("/auth/me")
async def get_current_user_info(current_user: TokenData = Depends(get_current_user_enhanced)):
    """Get current authenticated user info"""
    user = get_user(current_user.username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserResponse(
        username=user["username"],
        email=user["email"],
        full_name=user["full_name"],
        roles=user["roles"],
        department=user.get("department"),
        created_at=datetime.fromisoformat(user["created_at"]),
        is_active=user["is_active"]
    )

@app.post("/api/v1/query", response_model=QueryResponse)
# @limiter.limit("20/minute") 
async def query_patient_data(
    request: Request, 
    query_req: PatientSearchRequest, 
    current_user: TokenData = Depends(get_current_user_enhanced)
):
    query_id = str(uuid.uuid4())
    logger.info(f"Query {query_id} | User: {current_user.username} | Patient: {query_req.patient_id}")
    
    try:
        # --- Step 1: Validation & Access Control ---
        # Check if user has attending role
        if "attending" not in current_user.roles:
            logger.warning(f"Access Denied: User {current_user.username} doesn't have attending role")
            raise AuthorizationError(
                required_role="attending",
                user=current_user.username,
                details={"user_roles": current_user.roles}
            )
        
        # Validate patient ID
        if not query_req.patient_id or len(query_req.patient_id) < 1:
            raise ValidationError(
                field="patient_id",
                reason="Patient ID is required and must not be empty",
                value=query_req.patient_id
            )
        
        # Check patient access
        if not check_patient_access(current_user, query_req.patient_id):
            logger.warning(f"Access Denied: User {current_user.username} tried to access {query_req.patient_id}")
            raise PatientAccessDeniedError(
                patient_id=query_req.patient_id,
                user=current_user.username,
                reason="User does not have access to this patient record"
            )

        embedder = services.get("embedder")
        db = services.get("db")
        llm = services.get("llm")
        
        logger.debug(f"Services status - embedder: {embedder is not None}, db: {db is not None}, llm: {llm is not None}")
        
        # Crypto is optional in cloud mode, only require embedder, db, llm
        if not embedder or not db or not llm:
            missing_services = []
            if not embedder: missing_services.append("embedder")
            if not db: missing_services.append("database")
            if not llm: missing_services.append("llm")
            
            logger.error(f"Critical services not initialized: {missing_services}")
            raise HTTPException(
                status_code=503,
                detail=f"Backend services not initialized: {', '.join(missing_services)}"
            )
        
        # --- Step 2: Embedding Generation ---
        try:
            query_vec = embedder.get_embedding(query_req.question)
        except Exception as e:
            logger.error(f"Embedding failed: {str(e)[:100]}")
            raise EmbeddingError(
                reason=str(e)[:100],
                query_length=len(query_req.question),
                details={"error_type": type(e).__name__}
            )
            
        # --- Step 3: Vector Search (Multi-Database) ---
        raw_results = []
        try:
            raw_results = await db.query_vectors(
                query_vector=query_vec, 
                top_k=query_req.retrieve_k, 
                patient_id=query_req.patient_id
            )
            logger.info(f"Search found {len(raw_results)} results for {query_req.patient_id}")
        except SearchError:
            raise
        except Exception as e:
            logger.error(f"Search failed: {str(e)[:100]}")
            raise SearchError(
                reason="Vector search failed - database unavailable",
                patient_id=query_req.patient_id,
                details={"error": str(e)[:200], "question": query_req.question[:100]}
            )
        
        # --- Step 4: Decryption & Context Assembly ---
        source_docs = []
        context_text = f"PATIENT CONTEXT:\nPatient: {query_req.patient_id}\n\nRELEVANT RECORDS:\n"
        
        for i, res in enumerate(raw_results):
            try:
                metadata = res.get('metadata', {})
                
                # Check if data is encrypted or sample data
                if 'ciphertext' in metadata:
                    # Would decrypt encrypted data here
                    snippet = f"[Encrypted record {i+1}]"
                    doc_type = "encrypted_document"
                    doc_date = "encrypted"
                else:
                    # Real patient data from upload - extract available fields
                    patient_id = metadata.get('patient_id', 'Unknown')
                    gender = metadata.get('gender', 'Unknown')
                    birth_date = metadata.get('birth_date', 'Unknown')
                    data_source = metadata.get('data_source', 'Unknown')
                    num_conditions = metadata.get('num_conditions', 0)
                    num_medications = metadata.get('num_medications', 0)
                    primary_conditions = metadata.get('primary_conditions', 'N/A')
                    
                    snippet = f"Patient {patient_id} - {gender}, DOB: {birth_date}\n"
                    snippet += f"Primary Conditions: {primary_conditions}\n"
                    snippet += f"Total Conditions: {num_conditions}, Medications: {num_medications}\n"
                    snippet += f"Data Source: {data_source}"
                    
                    doc_type = metadata.get('record_type', 'patient_summary')
                    doc_date = birth_date
                
                context_text += f"[Document {i+1} - type: {doc_type}, date: {doc_date}]\n{snippet}\n\n"
                
                source_docs.append(SourceDocument(
                    type=doc_type,
                    date=doc_date,
                    snippet=snippet[:200] + "...",
                    similarity=float(res.get('score', 0))
                ))
                
            except Exception as e:
                logger.warning(f"Failed to process result {res.get('id', 'unknown')}: {str(e)[:80]}")
                continue

        # --- Step 5: LLM Inference ---
        generated_answer = ""
        confidence = 0.0
        
        try:
            if not source_docs:
                generated_answer = "No relevant clinical records found for this patient to answer the question."
                confidence = 0.0
            else:
                generated_answer = llm.generate_answer(query_req.question, context_text)
                # Estimate confidence based on top similarity
                confidence = float(raw_results[0]['score']) if raw_results else 0.0
                
        except LLMError as e:
            logger.error(f"LLM error: {e.message}")
            generated_answer = f"Analysis generation failed: {e.message[:100]}. Review source documents above."
            confidence = 0.0
        except Exception as e:
            logger.error(f"Unexpected LLM error: {str(e)[:100]}")
            generated_answer = "Error generating clinical response. Please review sources manually."
            confidence = 0.0

        # --- Step 6: Safety Guardrails ---
        # Mandatory Disclaimer
        disclaimer = "DISCLAIMER: This is clinical decision support, not a medical order. Verify all information."
        if "DISCLAIMER" not in generated_answer:
            generated_answer += f"\n\n{disclaimer}"

        # --- Step 7: Response ---
        logger.info(f"Query {query_id} Completed successfully. Confidence: {confidence:.3f}")
        
        return QueryResponse(
            query_id=query_id,
            answer=generated_answer,
            sources=source_docs,
            confidence=confidence,
            disclaimer=disclaimer
        )
        
    except ValidationError as e:
        logger.warning(f"Validation error in query {query_id}: {e.message}")
        raise HTTPException(status_code=400, detail=e.message)
    except PatientAccessDeniedError as e:
        logger.warning(f"Access denied for query {query_id}: {e.message}")
        raise HTTPException(status_code=403, detail=e.message)
    except AuthorizationError as e:
        logger.warning(f"Authorization error in query {query_id}: {e.message}")
        raise HTTPException(status_code=401, detail=e.message)
    except EmbeddingError as e:
        logger.error(f"Embedding error in query {query_id}: {e.message}")
        raise HTTPException(status_code=500, detail=f"Query processing failed: {e.message[:80]}")
    except SearchError as e:
        logger.error(f"Search error in query {query_id}: {e.message}")
        raise HTTPException(status_code=500, detail=f"Database search failed: {e.message[:80]}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in query {query_id}: {str(e)[:100]}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error. Check logs for details.")


@app.get("/api/v1/patients")
async def get_patients(
    search: str = None,
    limit: int = 100,
    current_user: TokenDataEnhanced = Depends(get_current_user_enhanced)
):
    """
    Get list of patients from database
    
    Args:
        search: Optional search query for semantic search
        limit: Maximum number of patients to return
        current_user: Authenticated user
    
    Returns:
        List of patient records
    """
    try:
        logger.info(f"User {current_user.username} requested patient list")
        
        # Load real patient data from synthea_patients_221.json
        import json
        from pathlib import Path
        
        patient_file = Path("synthea_patients_221.json")
        patients = []
        
        if patient_file.exists():
            try:
                with open(patient_file, 'r') as f:
                    data = json.load(f)
                
                # Convert from dict format to list format
                for patient_id, patient_data in data.items():
                    try:
                        # Extract demographics
                        demo = patient_data.get("demographics", {})
                        birth_date = demo.get("birthDate", "")
                        
                        # Calculate age
                        age = "N/A"
                        if birth_date:
                            try:
                                from datetime import datetime
                                birth_year = int(birth_date.split('-')[0])
                                age = datetime.now().year - birth_year
                            except:
                                pass
                        
                        # Get conditions
                        conditions = patient_data.get("conditions", [])
                        primary_condition = conditions[0].get("display", "Not specified") if conditions else "Not specified"
                        
                        # Get address
                        address = demo.get("address", {})
                        address_line = ""
                        if address.get("line"):
                            address_line = address["line"][0]
                        
                        # Build patient record
                        patient = {
                            "id": patient_id,
                            "name": patient_data.get("name", f"Patient {patient_id}"),
                            "age": age,
                            "gender": demo.get("gender", "Unknown")[0].upper() if demo.get("gender") else "U",
                            "dob": birth_date,
                            "condition": primary_condition,
                            "pcp": "Not assigned",
                            "riskLevel": "Medium",
                            "lastVisit": "Not visited",
                            "phone": "N/A",
                            "email": "N/A",
                            "address": address_line or f"{address.get('city', '')}, {address.get('state', '')}",
                            "numConditions": len(conditions),
                            "numMedications": len(patient_data.get("medications", [])),
                        }
                        
                        # Apply search filter
                        if search:
                            search_lower = search.lower()
                            if not (search_lower in patient["name"].lower() or
                                    search_lower in patient["id"].lower() or
                                    search_lower in patient["condition"].lower()):
                                continue
                        
                        patients.append(patient)
                        
                        # Apply limit
                        if len(patients) >= limit:
                            break
                            
                    except Exception as e:
                        logger.warning(f"Error processing patient {patient_id}: {e}")
                        continue
                
                logger.info(f"Loaded {len(patients)} real patients from {patient_file}")
                
            except Exception as e:
                logger.error(f"Error loading patient file: {e}")
                logger.warning("Falling back to empty patient list")
        else:
            logger.warning(f"Patient file not found: {patient_file}")
        
        return {
            "total": len(patients),
            "patients": patients
        }
        
    except Exception as e:
        logger.error(f"Error fetching patients: {str(e)}", exc_info=True)
        return {
            "total": 0,
            "patients": [],
            "message": f"Error fetching patients: {str(e)}"
        }


@app.get("/api/v1/patients/{patient_id}/details")
async def get_patient_details(
    patient_id: str,
    current_user: TokenDataEnhanced = Depends(get_current_user_enhanced)
):
    """
    Get detailed information for a specific patient
    
    Args:
        patient_id: The ID of the patient (e.g., PID-107)
        current_user: Authenticated user
    
    Returns:
        Detailed patient information
    """
    try:
        logger.info(f"User {current_user.username} requested details for patient {patient_id}")
        
        import json
        from pathlib import Path
        from datetime import datetime
        
        patient_file = Path("synthea_patients_221.json")
        
        if not patient_file.exists():
            raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found")
        
        with open(patient_file, 'r') as f:
            data = json.load(f)
        
        # Find patient by ID
        patient_data = data.get(patient_id)
        
        if not patient_data:
            raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found")
        
        # Get birth date and calculate age
        birth_date = patient_data.get("birthDate", "Unknown")
        age = None
        dob_display = "Unknown"
        
        if birth_date and birth_date != "Unknown":
            try:
                # Parse YYYY-MM-DD format
                birth_dt = datetime.strptime(birth_date, "%Y-%m-%d")
                age = (datetime.now() - birth_dt).days // 365
                dob_display = birth_dt.strftime("%B %d, %Y")
            except:
                pass
        
        # Get conditions
        conditions = patient_data.get("conditions", [])
        medications = patient_data.get("medications", [])
        procedures = patient_data.get("procedures", [])
        observations = patient_data.get("observations", [])
        
        # Map observation codes to human-readable labels
        observation_labels = {
            "8480-6": "Systolic blood pressure",
            "8462-4": "Diastolic blood pressure",
            "8867-4": "Heart rate",
            "2345-7": "Glucose [Mass/volume] in Serum or Plasma",
            "3141-9": "Body weight measured",
            "2710-2": "Oxygen saturation",
            "8310-5": "Body temperature",
            "39156-5": "BMI",
            "72514-3": "Pain severity",
            "11884-4": "Body height",
        }
        
        # Format vitals with proper labels
        formatted_vitals = []
        for obs in observations:
            obs_code = obs.get("code", "")
            obs_display = observation_labels.get(obs_code, obs.get("type", "Unknown Observation"))
            
            # Avoid duplicates - use code + date as unique key
            vital_key = f"{obs_code}_{obs.get('date', '')}"
            
            vital = {
                "type": obs_display,
                "code": obs_code,
                "value": obs.get("value", ""),
                "unit": obs.get("unit", ""),
                "date": obs.get("date", ""),
                "key": vital_key
            }
            
            # Avoid duplicate entries
            if vital_key not in [v["key"] for v in formatted_vitals]:
                formatted_vitals.append(vital)
            
            if len(formatted_vitals) >= 10:
                break
        
        # Remove the temporary key field
        for vital in formatted_vitals:
            vital.pop("key", None)
        
        # Build detailed response
        patient_details = {
            "id": patient_id,
            "name": patient_data.get("name", f"Patient {patient_id}"),
            "age": age,
            "gender": patient_data.get("gender", "Unknown"),
            "dob": dob_display,
            "birthDate": birth_date,
            "mrn": patient_id,
            "primaryCondition": conditions[0].get("display", "Not specified") if conditions else "Not specified",
            "conditions": [
                {
                    "name": c.get("display", "Unknown"),
                    "code": c.get("code", ""),
                    "status": "Active"
                }
                for c in conditions[:5]
            ],
            "medications": [
                {
                    "name": m.get("display", "Unknown"),
                    "dosage": m.get("dosage", "Not specified"),
                    "frequency": m.get("frequency", "Not specified")
                }
                for m in medications[:10]
            ],
            "procedures": [
                {
                    "name": p.get("display", "Unknown"),
                    "date": p.get("date", ""),
                    "code": p.get("code", "")
                }
                for p in procedures[:5]
            ],
            "vitals": formatted_vitals,
            "riskLevel": "Medium",
            "pcp": "Not assigned",
            "phone": patient_data.get("phone", "N/A"),
            "email": patient_data.get("email", "N/A"),
            "address": patient_data.get("address", "Not specified")
        }
        
        return patient_details
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching patient details for {patient_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error. Check logs for details.")


if __name__ == "__main__":
    import uvicorn
    # Generate self-signed certs for local Dev if needed, or run HTTP for now behind reverse proxy
    uvicorn.run(app, host="0.0.0.0", port=8000)
