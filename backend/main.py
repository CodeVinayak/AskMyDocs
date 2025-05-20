import os
import boto3
import json
import logging # Import logging
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
from elasticsearch.helpers import delete_by_query # Import delete_by_query
from elasticsearch import ElasticsearchException # Import ElasticsearchException
from botocore.exceptions import BotoCoreError, ClientError # Import S3 exceptions
from pydantic import BaseModel # Import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

# S3 Configuration
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION")

# Ensure S3 bucket name is configured on startup
@app.on_event("startup")
async def check_s3_config():
    if not S3_BUCKET_NAME:
        logger.error("S3_BUCKET_NAME environment variable is not set.")
        # Depending on requirements, you might want to raise an exception here
        # or ensure relevant endpoints handle this gracefully.

s3_client = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION
)

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

# LLM and RAG setup (Placeholder for now, actual implementation needed based on chosen LLM/LangChain components)
# from langchain.llms import OpenAI
# from langchain.chains import RetrievalQA
# from langchain.vectorstores import PGVector
# from langchain_core.output_parsers import StrOutputParser
# from langchain_core.runnables import RunnablePassthrough
# from langchain_core.prompts import ChatPromptTemplate

# llm = None # Initialize LLM
# vectorstore = None # Initialize vectorstore
# retriever = None # Initialize retriever
# rag_chain = None # Initialize RAG chain

@app.on_event("startup")
async def startup_event():
    logger.info("Application startup initiated.")
    # Create Elasticsearch index on startup
    try:
        create_index_if_not_exists()
        logger.info("Elasticsearch index check/creation complete.")
    except ElasticsearchException as e:
        logger.error(f"Failed to connect to Elasticsearch on startup: {e}")
        # Depending on requirements, you might want to exit here

    # Load embedding model on startup
    global embedding_model
    try:
        embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
        logger.info(f"Embedding model '{EMBEDDING_MODEL_NAME}' loaded.")
    except Exception as e:
        logger.error(f"Failed to load embedding model {EMBEDDING_MODEL_NAME}: {e}")

    # TODO: Initialize LLM, Vectorstore (PGVector), Retriever, and RAG Chain here
    # Example (requires more detailed setup):
    # global llm, vectorstore, retriever, rag_chain
    # try:
    #     llm = OpenAI(api_key=os.getenv("OPENAI_API_KEY")) # Load OpenAI API key from env
    #     connection_string = os.getenv("DATABASE_URL")
    #     vectorstore = PGVector(connection_string=connection_string, embedding_function=embedding_model, index_table="document_chunks", vector_column="embedding")
    #     retriever = vectorstore.as_retriever(search_kwargs={"filter": {"owner_id": current_user.id}})
    #     prompt_template = "..."
    #     prompt = ChatPromptTemplate.from_template(prompt_template)
    #     rag_chain = (
    #         {"context": retriever, "question": RunnablePassthrough()} # Correct input names based on chain/LLM
    #         | prompt
    #         | llm
    #         | StrOutputParser()
    #     )
    #     logger.info("LLM and RAG components initialized.")
    # except Exception as e:
    #     logger.error(f"Failed to initialize LLM/RAG components: {e}")
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
        # Try to get a connection from the pool
        db.connection()
        status_report["database"] = "connected"
        logger.debug("Database connection successful.")
    except SQLAlchemyError as e:
        status_report["database"] = "disconnected"
        status_report["status"] = "unhealthy"
        status_report["error"] = str(e)
        logger.error(f"Database connection failed: {e}")

    try:
        # Try to list buckets to check S3 connection
        s3_client.list_buckets()
        status_report["s3"] = "connected"
        logger.debug("S3 connection successful.")
    except (BotoCoreError, ClientError) as e:
        status_report["s3"] = "disconnected"
        status_report["status"] = "unhealthy"
        status_report.setdefault("error", []).append(f"S3 connection failed: {e}")
        logger.error(f"S3 connection failed: {e}")

    try:
        # Try to get Elasticsearch cluster health
        es_client.cluster.health(request_timeout=1) # Use a timeout for health check
        status_report["elasticsearch"] = "connected"
        logger.debug("Elasticsearch connection successful.")
    except ElasticsearchException as e:
        status_report["elasticsearch"] = "disconnected"
        status_report["status"] = "unhealthy"
        status_report.setdefault("error", []).append(f"Elasticsearch connection failed: {e}")
        logger.error(f"Elasticsearch connection failed: {e}")

    # Check if embedding model is loaded
    if embedding_model is None:
        status_report["embedding_model"] = "not loaded"
        status_report["status"] = "unhealthy"
        status_report.setdefault("error", []).append("Embedding model not loaded")
        logger.error("Embedding model not loaded.")
    else:
         status_report["embedding_model"] = "loaded"
         logger.debug("Embedding model is loaded.")

    # TODO: Add check for LLM/LangChain components if initialized on startup
    # if rag_chain is None:
    #    status_report["rag_chain"] = "not initialized"
    #    status_report["status"] = "unhealthy"
    #    status_report.setdefault("error", []).append("RAG chain not initialized.")
    #    logger.error("RAG chain not initialized.")
    # else:
    #     status_report["rag_chain"] = "initialized"

    if status_report["status"] == "unhealthy":
         logger.warning("Health check reported unhealthy status.")
    else:
        logger.info("Health check reported healthy status.")

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

@documents_router.get("/", response_model=List[models.Document]) # Assuming Document model can be used as response model
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

        # 3. Delete the original file from S3
        try:
            s3_client.delete_object(Bucket=S3_BUCKET_NAME, Key=document.storage_path)
            logger.info(f"Deleted S3 object: {document.storage_path}")
        except ClientError as e:
             if e.response['Error']['Code'] == 'NoSuchKey':
                 logger.warning(f"S3 object not found during deletion: {document.storage_path}")
             else:
                 logger.error(f"S3 client error deleting object {document.storage_path}: {e}", exc_info=True)
                 # Continue with other deletions, but log the error
        except BotoCoreError as e:
             logger.error(f"S3 boto core error deleting object {document.storage_path}: {e}", exc_info=True)
             # Continue with other deletions, but log the error
        except Exception as e:
             logger.error(f"Unexpected S3 error deleting object {document.storage_path}: {e}", exc_info=True)
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
        # Note: S3 and ES errors are logged but don't necessarily roll back the DB transaction
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
    if not S3_BUCKET_NAME:
        logger.error("S3_BUCKET_NAME is not configured.")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Server configuration error: S3 not configured.")
    if embedding_model is None:
        logger.error("Embedding model is not loaded.")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Server configuration error: Embedding model not loaded.")
    # TODO: Add check for LLM/LangChain components if needed before processing

    # Note: The parsing, chunking, embedding, and indexing process below is synchronous
    # and blocking. For a production application, this should be offloaded to a
    # background worker or message queue to avoid blocking the API request.
    logger.info(f"Starting processing for file: {file.filename}")

    try:
        # Generate a unique key for the file in S3
        # Include user ID in the S3 key for better organization and security
        s3_key = f"uploads/{current_user.id}/{os.path.basename(file.filename)}"
        logger.debug(f"Generated S3 key: {s3_key}")

        # Upload file to S3
        try:
            file.file.seek(0) # Move cursor to the beginning of the file
            s3_client.upload_fileobj(file.file, S3_BUCKET_NAME, s3_key)
            logger.info(f"Successfully uploaded file {file.filename} to S3 key {s3_key}.")
        except (BotoCoreError, ClientError) as e:
             logger.error(f"S3 upload failed for {file.filename}: {e}", exc_info=True)
             raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to upload file to S3: {e}")
        except Exception as e:
             logger.error(f"Unexpected error during S3 upload for {file.filename}: {e}", exc_info=True)
             raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to upload file to S3: {e}")

        # Create a database record
        db_document = models.Document(
            filename=file.filename,
            storage_path=s3_key,
            owner_id=current_user.id, # Use authenticated user's ID
            status="uploaded" # Initial status
        )
        try:
            db.add(db_document)
            db.commit()
            db.refresh(db_document)
            logger.info(f"Created DB record for document {db_document.id} (user {current_user.id}).")
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Database error creating document record for {file.filename} (user {current_user.id}): {e}", exc_info=True)
            # Consider cleaning up S3 file if DB commit fails here
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create document record in database")
        except Exception as e:
            db.rollback()
            logger.error(f"Unexpected error creating document record for {file.filename} (user {current_user.id}): {e}", exc_info=True)
            # Consider cleaning up S3 file if DB commit fails here
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create document record in database")

        # --- Parsing, Chunking, Embedding, and Indexing ---
        parsed_elements = []
        try:
            file.file.seek(0) # Reset cursor to the beginning
            # Use filename argument for better parsing with unstructured.io
            # Add content_type for better parsing detection
            content_type = file.content_type # Get content type from UploadFile
            logger.debug(f"Attempting to parse file {file.filename} with content type {content_type}.")
            parsed_elements = partition(file=file.file, filename=file.filename, content_type=content_type)
            logger.info(f"Successfully parsed file {file.filename}. Found {len(parsed_elements)} elements.")
        except Exception as parsing_error:
            logger.error(f"Error parsing document {file.filename}: {parsing_error}", exc_info=True)
            db_document.status = "parsing_failed"
            db.commit() # Commit status update
            # Depending on requirements, you might want to raise HTTPException here
            # raise HTTPException(status_code=500, detail=f"Failed to parse document: {parsing_error}")
            # Continue processing even if parsing failed, but mark status
            # If parsing fails, there will be no chunks to save or index
            parsed_elements = [] # Ensure empty list if parsing failed

        chunks_to_index = []
        db_chunks_to_save = []

        if parsed_elements:
            logger.debug(f"Processing {len(parsed_elements)} parsed elements for chunking and embedding.")
            for element in parsed_elements:
                text = str(element)
                # Convert metadata to a JSON string for storage in PostgreSQL
                metadata = element.metadata.to_dict() if hasattr(element, 'metadata') and element.metadata else {}
                 # Add core metadata
                metadata["filename"] = file.filename
                metadata["s3_key"] = s3_key
                metadata["document_db_id"] = db_document.id
                metadata["owner_id"] = current_user.id # Add owner ID to metadata
                # Ensure metadata is serializable if needed, unstructured metadata can be complex
                # Using json.dumps will handle basic types, but complex objects might need custom handling
                metadata_json = json.dumps(metadata)

                # Split text into chunks
                chunks = text_splitter.create_documents([text], metadatas=[metadata])
                logger.debug(f"Split element into {len(chunks)} chunks.")

                for chunk in chunks:
                    try:
                        # Generate embedding for the chunk
                        if embedding_model is None:
                             raise Exception("Embedding model not loaded.")
                        chunk_embedding = embedding_model.encode(chunk.page_content).tolist()
                        logger.debug("Generated embedding for a chunk.")

                        # Prepare chunk for Elasticsearch (keyword/metadata search)
                        chunks_to_index.append({
                            "chunk_text": chunk.page_content,
                            "metadata": chunk.metadata # Keep original metadata object for ES
                         })

                        # Prepare chunk for PostgreSQL (vector storage)
                        db_chunks_to_save.append(
                            models.DocumentChunk(
                                document_id=db_document.id,
                                chunk_text=chunk.page_content,
                                metadata=metadata_json, # Store metadata as JSON string
                                embedding=chunk_embedding
                            )
                        )
                    except Exception as chunk_processing_error:
                         logger.error(f"Error processing chunk for document ID {db_document.id}: {chunk_processing_error}", exc_info=True)
                         # Decide how to handle chunk-level errors - skip chunk or fail document?
                         # Currently, we log and skip the problematic chunk.
                         continue # Skip to the next chunk if processing fails

            # Save chunks to PostgreSQL
            if db_chunks_to_save:
                try:
                    db.add_all(db_chunks_to_save)
                    # db.commit() # Defer commit until after Elasticsearch indexing
                    logger.info(f"Prepared {len(db_chunks_to_save)} chunks for saving to PostgreSQL for document ID {db_document.id}.")
                except SQLAlchemyError as e:
                    # Note: DB transaction might already be in a failed state if parsing_failed was committed
                    # If not, rollback here.
                    # db.rollback() # Careful with rollback if partial commit happened earlier
                    logger.error(f"Database error saving chunks for document ID {db_document.id}: {e}", exc_info=True)
                    # Mark document as indexing failed in DB?
                    db_document.status = "db_save_failed"
                    # db.commit() # Commit status update
                    chunks_to_index = [] # Prevent ES indexing if DB save failed
                    db_chunks_to_save = [] # Clear chunks to prevent re-attempting save later in this block
                except Exception as e:
                    logger.error(f"Unexpected error saving chunks for document ID {db_document.id}: {e}", exc_info=True)
                    db_document.status = "db_save_failed"
                    chunks_to_index = []
                    db_chunks_to_save = []

            # Index chunks into Elasticsearch
            if chunks_to_index:
                try:
                     # Ensure Elasticsearch index exists before indexing (redundant with startup check, but safer)
                     # create_index_if_not_exists() # This is now done on startup
                     index_document_chunks(db_document.id, chunks_to_index)
                     db_document.status = "indexed"
                     logger.info(f"Successfully indexed chunks for document ID {db_document.id} into Elasticsearch.")
                except ElasticsearchException as e:
                     logger.error(f"Elasticsearch indexing failed for document ID {db_document.id}: {e}", exc_info=True)
                     db_document.status = "es_index_failed"
                except Exception as e:
                     logger.error(f"Unexpected error during Elasticsearch indexing for document ID {db_document.id}: {e}", exc_info=True)
                     db_document.status = "es_index_failed"

            # If chunks were prepared for saving and no DB error occurred during add_all, commit here
            if db_chunks_to_save and db_document.status != "db_save_failed": # Check if DB save preparation was successful
                 try:
                     db.commit() # Final commit for chunks and status
                     logger.info(f"Final DB commit successful for document ID {db_document.id} processing.")
                 except SQLAlchemyError as e:
                      logger.error(f"Final DB commit failed for document ID {db_document.id}: {e}", exc_info=True)
                      # This is a critical failure after successful steps, status might be inconsistent
                      # Recovery might need manual intervention or a dedicated process
                      db.rollback() # Attempt to rollback even if it might be inconsistent
                      db_document.status = "final_commit_failed"
                      # Need to re-query db_document and commit status update if possible or handle externally
                 except Exception as e:
                     logger.error(f"Unexpected error during final DB commit for document ID {db_document.id}: {e}", exc_info=True)
                     db.rollback()
                     db_document.status = "final_commit_failed"
            elif db_document.status == "uploaded": # If no parsed elements and status is still 'uploaded'
                 db_document.status = "no_content" # Or 'processing_complete_no_content'
                 logger.warning(f"No parsed elements or chunks found for document {file.filename}. Marking as no_content.")
                 try:
                      db.commit() # Commit status update
                 except Exception as e:
                      logger.error(f"Error committing status for no_content for document ID {db_document.id}: {e}", exc_info=True)

        else: # If parsing_failed or no elements returned
             if db_document.status == "uploaded": # If status wasn't already set by parsing error
                 db_document.status = "parsing_failed" # Ensure status is marked
                 logger.warning(f"No parsed elements for document {file.filename}. Marking as parsing_failed.")
                 try:
                      db.commit() # Commit status update
                 except Exception as e:
                      logger.error(f"Error committing status for parsing_failed for document ID {db_document.id}: {e}", exc_info=True)

        # --- End Parsing, Chunking, Embedding, and Indexing ---
        logger.info(f"Processing complete for file: {file.filename}. Final status: {db_document.status}")

        # Refresh the document object to get the latest status before returning
        db.refresh(db_document)

        return {
            "message": "Document upload and processing initiated.", # Message remains general as processing is complex
            "document_id": db_document.id,
            "filename": db_document.filename,
            "s3_key": db_document.storage_path,
            "status": db_document.status,
            "chunk_count": len(db_chunks_to_save) if db_document.status != "db_save_failed" else 0 # Report saved chunks if not failed at DB save
        }

    except HTTPException as e:
        # Catch explicit HTTPExceptions raised during the process
        # Log the error but re-raise it so FastAPI handles the response
        logger.error(f"HTTPException during upload processing for {file.filename} (user {current_user.id}): {e.detail}", exc_info=True)
        raise e
    except Exception as e:
        # Catch any other unexpected errors during the entire process
        logger.error(f"Unexpected error during upload processing for {file.filename} (user {current_user.id}): {e}", exc_info=True)
        # Consider cleaning up partially created resources (S3, DB record) here
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred during document processing: {e}")

@app.post("/query/")
# Apply the authentication dependency
async def query_documents(query_request: QueryRequest, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    logger.info(f"User {current_user.id} submitting query: {query_request.query[:100]}...") # Log first 100 chars
    # Ensure LLM/RAG components are initialized
    # global rag_chain # Assuming rag_chain is global from startup
    # if rag_chain is None:
    #     logger.error("RAG components not initialized for query.")
    #     raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="RAG components not initialized.")

    # TODO: Implement retrieval and generation logic here using LangChain and current_user.id
    # This will involve:
    # 1. Generating embedding for the user query
    # 2. Using the vectorstore (PGVector) to find relevant chunks for the current user
    #    (Filter by owner_id in the vectorstore query if possible, or filter results)
    # 3. Passing the query and retrieved chunks to the LLM via the RAG chain
    # 4. Returning the LLM's generated answer

    try:
        # Placeholder response
        answer_text = f"Received query: {query_request.query}. RAG functionality for user {current_user.id} is not yet fully implemented."
        logger.info(f"Query processed for user {current_user.id}. Returning placeholder answer.")
        return {"answer": answer_text}
    except Exception as e:
        logger.error(f"Error during query processing for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An error occurred during query processing.")

# Include routers
app.include_router(auth_router)
app.include_router(documents_router) 