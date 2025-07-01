import os
import boto3
import json
import logging # Import logging
import sys # Import sys
from fastapi import FastAPI, Depends, UploadFile, File, HTTPException, status, APIRouter, Request # Import Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse # Import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError # Import SQLAlchemyError
from sqlalchemy import delete # Import delete
from .db.database import engine, SessionLocal, Base, get_db
from .db import models
from unstructured.partition.auto import partition
from langchain_text_splitters import RecursiveCharacterTextSplitter
from .elasticsearch_client import es_client, create_index_if_not_exists, index_document_chunks, INDEX_NAME # Import INDEX_NAME
from sentence_transformers import SentenceTransformer
from typing import List, Optional # Import Optional
from .auth import get_password_hash, verify_password, create_access_token, get_current_user, UserCreate, UserLogin, Token, UserPublic # Import auth components
from datetime import timedelta
from elasticsearch import ElasticsearchException # Import ElasticsearchException
from botocore.exceptions import BotoCoreError, ClientError # Import S3 exceptions
from pydantic import BaseModel # Import BaseModel
from pythonjsonlogger.jsonlogger import JsonFormatter # Import JsonFormatter
from .schemas import DocumentBase

# LangChain Imports for RAG
# from langchain_openai import ChatOpenAI # REMOVE
from langchain_community.vectorstores import PGVector # For PostgreSQL vector store
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableParallel

# Add Gemini API import
import google.generativeai as genai

# Configure logging with JSON format
logger = logging.getLogger()
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
formatter = JsonFormatter(
    '%(levelname)s %(asctime)s %(name)s %(process)d %(message)s'
)
handler.setFormatter(formatter)
logger.addHandler(handler)

# Suppress default uvicorn access logs if preferred, or configure them separately if needed
logging.getLogger("uvicorn.access").propagate = False

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="AskMyDocs API")

# Create API routers
auth_router = APIRouter(prefix="/auth", tags=["auth"])
documents_router = APIRouter(prefix="/documents", tags=["documents"])

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure local storage directory exists
LOCAL_STORAGE_DIR = os.path.join(os.path.dirname(__file__), 'storage')
os.makedirs(LOCAL_STORAGE_DIR, exist_ok=True)

# Embedding Model (using a default model for now)
# Consider using environment variables to configure the model
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
embedding_model = None

# Text Splitter
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    length_function=len,
)

# Gemini API key from environment
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
gemini_model = None

def initialize_gemini():
    global gemini_model
    if not GEMINI_API_KEY:
        logger.error("GEMINI_API_KEY environment variable is not set. Gemini will not be initialized.")
        gemini_model = None
    else:
        genai.configure(api_key=GEMINI_API_KEY)
        gemini_model = genai.GenerativeModel('models/gemini-2.5-flash')
        logger.info("Gemini model 'models/gemini-2.5-flash' initialized.")

@app.on_event("startup")
async def startup_event():
    logger.info("Application startup initiated.")
    # Create Elasticsearch index on startup
    try:
        create_index_if_not_exists()
        logger.info("Elasticsearch index check/creation complete.")
    except ElasticsearchException as e:
        logger.error(f"Failed to connect to Elasticsearch on startup: {e}")
    # Load embedding model on startup
    global embedding_model
    try:
        embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
        logger.info(f"Embedding model '{EMBEDDING_MODEL_NAME}' loaded.")
    except Exception as e:
        logger.error(f"Failed to load embedding model {EMBEDDING_MODEL_NAME}: {e}")
    # Initialize Gemini
    initialize_gemini()
    logger.info("Application startup complete.")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Application shutting down.")
    # TODO: Clean up resources like database sessions, Elasticsearch connections if necessary

# Global Exception Handler
@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception for request: {request.method} {request.url}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred.", "error": str(exc) if os.getenv("ENVIRONMENT") == "development" else None} # Include detailed error only in development
    )


@app.get("/")
async def root():
    logger.info("Root endpoint accessed.")
    return {"message": "Welcome to AskMyDocs API"}

@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    logger.info("Health check endpoint accessed.")
    status_report = {"status": "healthy"}
    try:
        db.connection()
        status_report["database"] = "connected"
        logger.debug("Database connection successful.")
    except SQLAlchemyError as e:
        status_report["database"] = "disconnected"
        status_report["status"] = "unhealthy"
        status_report["error"] = str(e)
        logger.error(f"Database connection failed: {e}")
    try:
        es_client.cluster.health(request_timeout=1)
        status_report["elasticsearch"] = "connected"
        logger.debug("Elasticsearch connection successful.")
    except ElasticsearchException as e:
        status_report["elasticsearch"] = "disconnected"
        status_report["status"] = "unhealthy"
        status_report.setdefault("error", []).append(f"Elasticsearch connection failed: {e}")
        logger.error(f"Elasticsearch connection failed: {e}")
    if embedding_model is None:
        status_report["embedding_model"] = "not loaded"
        status_report["status"] = "unhealthy"
        status_report.setdefault("error", []).append("Embedding model not loaded")
        logger.error("Embedding model not loaded.")
    else:
        status_report["embedding_model"] = "loaded"
        logger.debug("Embedding model is loaded.")
    return status_report

# --- Authentication Endpoints ---

@auth_router.post("/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    logger.info(f"Attempting to register user with email: {user_data.email}")
    # Check if user with this email or username already exists
    db_user = db.query(models.User).filter(
        (models.User.email == user_data.email) | (models.User.username == user_data.username)
    ).first()
    if db_user:
        logger.warning(f"Registration failed: Email or username already exists for {user_data.email}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email or username already registered")

    # Hash the password
    hashed_password = get_password_hash(user_data.password)

    # Create new user
    new_user = models.User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password
    )
    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        logger.info(f"User registered successfully with ID: {new_user.id}")
        return new_user
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Database integrity error during registration for {user_data.email}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email or username already registered (Integrity Error)") # More specific error
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error during registration for {user_data.email}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error during registration")
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error during user registration for {user_data.email}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to register user")

@auth_router.post("/login", response_model=Token)
async def login_for_access_token(form_data: UserLogin, db: Session = Depends(get_db)):
    logger.info(f"Attempting to log in user with email: {form_data.email}")
    # Authenticate user by email and password
    user = db.query(models.User).filter(models.User.email == form_data.email).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        logger.warning(f"Login failed: Incorrect credentials for {form_data.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create JWT access token
    access_token_expires = timedelta(minutes=30) # Match ACCESS_TOKEN_EXPIRE_MINUTES in auth.py
    access_token = create_access_token(
        data={"sub": str(user.id)}, # Use user ID as the subject claim
        expires_delta=access_token_expires
    )
    logger.info(f"User logged in successfully with ID: {user.id}")
    return {"access_token": access_token, "token_type": "bearer"}

# --- Document Endpoints (Secured) ---

@documents_router.get("/", response_model=List[DocumentBase])
async def list_documents(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    logger.info(f"User {current_user.id} requesting list of documents.")
    try:
        # Retrieve all documents for the current user
        documents = db.query(models.Document).filter(models.Document.owner_id == current_user.id).all()
        logger.info(f"Retrieved {len(documents)} documents for user {current_user.id}.")
        return documents
    except SQLAlchemyError as e:
        logger.error(f"Database error retrieving documents for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve documents")
    except Exception as e:
        logger.error(f"Unexpected error retrieving documents for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve documents")

@documents_router.delete("/{document_id}")
async def delete_document(document_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    logger.info(f"User {current_user.id} attempting to delete document ID {document_id}.")
    # Find the document and ensure it belongs to the current user
    document = db.query(models.Document).filter(
        models.Document.id == document_id,
        models.Document.owner_id == current_user.id
    ).first()

    if not document:
        logger.warning(f"Delete failed: Document ID {document_id} not found or unauthorized for user {current_user.id}.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found or you don't have permission to delete it")

    try:
        # 1. Delete associated chunks from PostgreSQL
        try:
            delete_chunks_q = delete(models.DocumentChunk).where(models.DocumentChunk.document_id == document_id)
            result = db.execute(delete_chunks_q)
            # db.commit() # Defer commit until main document is deleted
            logger.info(f"Deleted {result.rowcount} chunks from PostgreSQL for document ID {document_id}.")
        except SQLAlchemyError as e:
            logger.error(f"Database error deleting chunks for document ID {document_id}: {e}", exc_info=True)
            # Continue with other deletions, but log the error

        # 2. Delete associated documents/chunks from Elasticsearch
        try:
            # Delete by document_db_id field
            es_client.delete_by_query(
                index=INDEX_NAME,
                body={
                    "query": {
                        "term": {
                            "metadata.document_db_id": document_id
                        }
                    }
                },
                refresh=True # Make deletions visible immediately
            )
            logger.info(f"Deleted Elasticsearch documents for document ID {document_id}.")
        except ElasticsearchException as e:
            logger.error(f"Error deleting from Elasticsearch for document ID {document_id}: {e}", exc_info=True)
            # Continue with other deletions, but log the error

        # 3. Delete the original file from local storage
        try:
            local_file_path = document.storage_path
            if os.path.exists(local_file_path):
                os.remove(local_file_path)
            logger.info(f"Deleted local file: {local_file_path}")
        except Exception as e:
            logger.error(f"Error deleting local file {local_file_path}: {e}", exc_info=True)
            # Continue with other deletions, but log the error

        # 4. Delete the document record from PostgreSQL
        db.delete(document)
        db.commit() # Commit the transaction including chunk deletions
        logger.info(f"Document record with ID {document_id} deleted from PostgreSQL.")

        logger.info(f"Document ID {document_id} deleted successfully for user {current_user.id}.")
        return {"message": f"Document with ID {document_id} deleted successfully"}

    except SQLAlchemyError as e:
        db.rollback() # Rollback DB changes if deleting the main document fails
        logger.error(f"Database error deleting document record {document_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to delete document record: {e}")
    except Exception as e:
        # Note: ES errors are logged but don't necessarily roll back the DB transaction
        # The document record deletion is attempted last.
        logger.error(f"Unexpected error during document deletion for ID {document_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to delete document: {e}")

# --- Main App Endpoints (Secured) ---

# Pydantic model for query request body
class QueryRequest(BaseModel):
    query: str

@app.post("/upload/")
async def upload_document(file: UploadFile = File(...), db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    logger.info(f"User {current_user.id} attempting to upload file: {file.filename}")
    if embedding_model is None:
        logger.error("Embedding model is not loaded.")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Server configuration error: Embedding model not loaded.")
    logger.info(f"Starting processing for file: {file.filename}")
    try:
        # Save file to local storage
        user_dir = os.path.join(LOCAL_STORAGE_DIR, str(current_user.id))
        os.makedirs(user_dir, exist_ok=True)
        local_file_path = os.path.join(user_dir, file.filename)
        with open(local_file_path, "wb") as f:
            f.write(await file.read())
        logger.info(f"Successfully saved file {file.filename} to local path {local_file_path}.")
        # Create a database record
        db_document = models.Document(
            filename=file.filename,
            storage_path=local_file_path,
            owner_id=current_user.id,
            status="uploaded"
        )
        try:
            db.add(db_document)
            db.commit()
            db.refresh(db_document)
            logger.info(f"Created DB record for document {db_document.id} (user {current_user.id}).")
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Database error creating document record for {file.filename} (user {current_user.id}): {e}", exc_info=True)
            # Clean up local file if DB commit fails
            if os.path.exists(local_file_path):
                os.remove(local_file_path)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create document record in database")
        except Exception as e:
            db.rollback()
            logger.error(f"Unexpected error creating document record for {file.filename} (user {current_user.id}): {e}", exc_info=True)
            if os.path.exists(local_file_path):
                os.remove(local_file_path)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create document record in database")
        # --- Parsing, Chunking, Embedding, and Indexing ---
        parsed_elements = []
        try:
            with open(local_file_path, "rb") as f:
                content_type = file.content_type
                logger.debug(f"Attempting to parse file {file.filename} with content type {content_type}.")
                parsed_elements = partition(filename=local_file_path, content_type=content_type)
            logger.info(f"Successfully parsed file {file.filename}. Found {len(parsed_elements)} elements.")
        except Exception as parsing_error:
            logger.error(f"Error parsing document {file.filename}: {parsing_error}", exc_info=True)
            db_document.status = "parsing_failed"
            db.commit()
            parsed_elements = []
        chunks_to_index = []
        db_chunks_to_save = []
        if parsed_elements:
            logger.debug(f"Processing {len(parsed_elements)} parsed elements for chunking and embedding.")
            for element in parsed_elements:
                text = str(element)
                metadata = element.metadata.to_dict() if hasattr(element, 'metadata') and element.metadata else {}
                metadata["filename"] = file.filename
                metadata["local_path"] = local_file_path
                metadata["document_db_id"] = db_document.id
                metadata["owner_id"] = current_user.id
                metadata_json = json.dumps(metadata)
                chunks = text_splitter.create_documents([text], metadatas=[metadata])
                logger.debug(f"Split element into {len(chunks)} chunks.")
                for chunk in chunks:
                    try:
                        if embedding_model is None:
                            raise Exception("Embedding model not loaded.")
                        chunk_embedding = embedding_model.encode(chunk.page_content).tolist()
                        logger.debug("Generated embedding for a chunk.")
                        chunks_to_index.append({
                            "chunk_text": chunk.page_content,
                            "metadata": chunk.metadata
                        })
                        db_chunks_to_save.append(
                            models.DocumentChunk(
                                document_id=db_document.id,
                                chunk_text=chunk.page_content,
                                metadata=metadata_json,
                                embedding=chunk_embedding
                            )
                        )
                    except Exception as chunk_processing_error:
                        logger.error(f"Error processing chunk for document ID {db_document.id}: {chunk_processing_error}", exc_info=True)
                        continue
            if db_chunks_to_save:
                try:
                    db.add_all(db_chunks_to_save)
                    logger.info(f"Prepared {len(db_chunks_to_save)} chunks for saving to PostgreSQL for document ID {db_document.id}.")
                except SQLAlchemyError as e:
                    logger.error(f"Database error saving chunks for document ID {db_document.id}: {e}", exc_info=True)
                    db.rollback()
                    db_document.status = "db_save_failed"
                    db.add(db_document)
                    db.commit()
                    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to save document chunks to database")
                except Exception as e:
                    logger.error(f"Unexpected error saving chunks for document ID {db_document.id}: {e}", exc_info=True)
                    db.rollback()
                    db_document.status = "db_save_failed"
                    db.add(db_document)
                    db.commit()
                    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to save document chunks to database")
            if chunks_to_index:
                try:
                    index_document_chunks(chunks_to_index)
                    logger.info(f"Indexed {len(chunks_to_index)} chunks in Elasticsearch for document ID {db_document.id}.")
                except ElasticsearchException as e:
                    logger.error(f"Elasticsearch indexing failed for document ID {db_document.id}: {e}", exc_info=True)
                    db.rollback()
                    db_document.status = "es_indexing_failed"
                    db.add(db_document)
                    db.commit()
                    # Clean up local file if indexing fails
                    if os.path.exists(local_file_path):
                        os.remove(local_file_path)
                    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to index document in search engine")
                except Exception as e:
                    logger.error(f"Unexpected error during Elasticsearch indexing for document ID {db_document.id}: {e}", exc_info=True)
                    db.rollback()
                    db_document.status = "es_indexing_failed"
                    db.add(db_document)
                    db.commit()
                    if os.path.exists(local_file_path):
                        os.remove(local_file_path)
                    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to index document in search engine")
            db_document.status = "processed"
            db.commit()
            logger.info(f"Document {db_document.id} processed successfully.")
            return JSONResponse(status_code=status.HTTP_201_CREATED, content={
                "message": "Document uploaded and processed successfully",
                "document_id": db_document.id,
                "filename": db_document.filename,
                "status": db_document.status
            })
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Unhandled error during document upload for {file.filename}: {e}", exc_info=True)
        # Clean up local file if a general error occurred before final commit
        if 'local_file_path' in locals() and os.path.exists(local_file_path):
            os.remove(local_file_path)
        db.rollback()
        if 'db_document' in locals() and db_document.status != "processed":
            db_document.status = "failed_unhandled_error"
            db.add(db_document)
            try:
                db.commit()
                logger.warning(f"Document {db_document.id} status updated to failed_unhandled_error.")
            except Exception as db_update_e:
                logger.error(f"Failed to update document status to failed_unhandled_error for {db_document.id}: {db_update_e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred during document processing: {e}")

@app.post("/query/")
async def query_documents(query_request: QueryRequest, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    logger.info(f"User {current_user.id} submitting query: {query_request.query[:100]}...")
    global gemini_model
    if gemini_model is None:
        logger.error("Gemini model not initialized for query.")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Gemini model not initialized.")
    try:
        # Retrieve relevant chunks for the user from the database (simple RAG)
        # For now, fetch all chunks for the user's documents (can be improved with vector search)
        user_documents = db.query(models.Document).filter(models.Document.owner_id == current_user.id).all()
        document_ids = [doc.id for doc in user_documents]
        chunks = db.query(models.DocumentChunk).filter(models.DocumentChunk.document_id.in_(document_ids)).all()
        context = "\n".join([chunk.chunk_text for chunk in chunks])
        prompt = f"You are an assistant for question-answering tasks. Use the following context to answer the question. If you don't know the answer, say so.\n\nContext:\n{context}\n\nQuestion: {query_request.query}\n\nAnswer:"
        response = gemini_model.generate_content(prompt)
        answer_text = response.text if hasattr(response, 'text') else str(response)
        logger.info(f"Query processed for user {current_user.id}. Answer generated.")
        return {"answer": answer_text}
    except Exception as e:
        logger.error(f"Error during query processing for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An error occurred during query processing.")

# Include routers
app.include_router(auth_router)
app.include_router(documents_router) 