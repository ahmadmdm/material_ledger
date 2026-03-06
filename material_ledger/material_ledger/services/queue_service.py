# Copyright (c) 2026, Ahmad
# For license information, please see license.txt

"""
Queue Service for AI Background Processing
Handles data chunking, queue management, and background jobs
"""

import frappe
from frappe import _
from frappe.utils import now, now_datetime, add_days, cint, flt
import json
import uuid
import hashlib
import datetime


def _json_serial(obj):
    """JSON serializer for objects not serializable by default"""
    if isinstance(obj, (datetime.date, datetime.datetime)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


class AIQueueService:
    """Service for managing AI processing queue"""
    
    def __init__(self):
        self.chunk_size = 1000  # Records per chunk
        self.max_retries = 3
    
    def create_ai_job(self, job_type, company, filters, user=None):
        """
        Create a new AI processing job
        
        Args:
            job_type: Type of AI analysis (prediction, anomaly, etc.)
            company: Company name
            filters: Dictionary of filters
            user: User requesting the job
            
        Returns:
            dict: Job details with job_id
        """
        if not user:
            user = frappe.session.user
            
        job_id = str(uuid.uuid4())
        
        # Create cache key
        cache_key = self._generate_cache_key(job_type, company, filters)
        
        # Check if we have cached results (within 7 days)
        cached_result = self._get_cached_result(cache_key)
        if cached_result:
            return {
                "status": "completed",
                "job_id": job_id,
                "data": cached_result,
                "from_cache": True
            }
        
        # Create job document
        job_doc = frappe.get_doc({
            "doctype": "AI Job Queue",
            "job_id": job_id,
            "job_type": job_type,
            "company": company,
            "filters": json.dumps(filters),
            "user": user,
            "status": "queued",
            "cache_key": cache_key,
            "created_at": now()
        })
        job_doc.insert()
        
        # Queue the job for background processing
        frappe.enqueue(
            method="material_ledger.material_ledger.services.queue_service.process_ai_job",
            queue="long",
            timeout=3600,  # 1 hour
            ai_job_id=job_id,
            job_type=job_type,
            company=company,
            filters=filters,
            user=user
        )
        
        return {
            "status": "queued",
            "job_id": job_id,
            "message": _("AI analysis started in background. You will be notified when complete.")
        }
    
    def _generate_cache_key(self, job_type, company, filters):
        """Generate unique cache key for job"""
        key_data = f"{job_type}:{company}:{json.dumps(filters, sort_keys=True)}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _get_cached_result(self, cache_key):
        """Get cached result if exists and not expired"""
        if frappe.db.exists("AI Result Cache", cache_key):
            cache_doc = frappe.get_doc("AI Result Cache", cache_key)
            if cache_doc.expires_at and cache_doc.expires_at > now_datetime():
                return json.loads(cache_doc.result_data)
        return None
    
    def _cache_result(self, cache_key, result_data):
        """Cache result for 7 days"""
        expires_at = add_days(now(), 7)
        
        if frappe.db.exists("AI Result Cache", cache_key):
            cache_doc = frappe.get_doc("AI Result Cache", cache_key)
            cache_doc.result_data = json.dumps(result_data, default=_json_serial)
            cache_doc.expires_at = expires_at
            cache_doc.save(ignore_permissions=True)
        else:
            cache_doc = frappe.get_doc({
                "doctype": "AI Result Cache", 
                "name": cache_key,
                "cache_key": cache_key,
                "result_data": json.dumps(result_data, default=_json_serial),
                "expires_at": expires_at
            })
            cache_doc.insert(ignore_permissions=True)
    
    def get_job_status(self, job_id):
        """Get current job status"""
        job_name = frappe.db.get_value("AI Job Queue", {"job_id": job_id}, "name")
        if not job_name:
            return {"status": "not_found"}
            
        job_doc = frappe.get_doc("AI Job Queue", job_name)
        return {
            "status": job_doc.status,
            "progress": job_doc.progress or 0,
            "result": json.loads(job_doc.result) if job_doc.result else None,
            "error": job_doc.error
        }
    
    def chunk_data(self, data, chunk_size=None):
        """
        Split data into processable chunks
        
        Args:
            data: List or query result
            chunk_size: Size of each chunk
            
        Returns:
            list: List of data chunks
        """
        if not chunk_size:
            chunk_size = self.chunk_size
            
        chunks = []
        for i in range(0, len(data), chunk_size):
            chunks.append(data[i:i + chunk_size])
        return chunks


def process_ai_job(ai_job_id, job_type, company, filters, user):
    """
    Background job processor for AI analysis
    
    This function runs in the background and processes the AI job
    """
    try:
        # Update job status
        job_doc = frappe.get_doc("AI Job Queue", {"job_id": ai_job_id})
        job_doc.status = "processing"
        job_doc.started_at = now()
        job_doc.save()
        
        # Get queue service
        queue_service = AIQueueService()
        
        # Process based on job type
        if job_type == "financial_prediction":
            result = process_financial_prediction(company, filters, job_doc)
        elif job_type == "anomaly_detection":
            result = process_anomaly_detection(company, filters, job_doc)
        elif job_type == "investment_analysis":
            result = process_investment_analysis(company, filters, job_doc)
        elif job_type == "comprehensive_analysis":
            result = process_comprehensive_analysis(company, filters, job_doc)
        else:
            raise ValueError(f"Unknown job type: {job_type}")
        
        # Update job completion
        job_doc.status = "completed"
        job_doc.progress = 100
        job_doc.result = json.dumps(result, default=_json_serial)
        job_doc.completed_at = now()
        job_doc.save()
        
        # Cache the result
        queue_service._cache_result(job_doc.cache_key, result)
        
        # Send notification
        send_completion_notification(user, job_type, ai_job_id, result)
        
    except Exception as e:
        # Update job with error
        job_doc = frappe.get_doc("AI Job Queue", {"job_id": ai_job_id})
        job_doc.status = "failed"
        job_doc.error = str(e)
        job_doc.save()
        
        # Send error notification
        send_error_notification(user, job_type, ai_job_id, str(e))
        
        # Log error
        frappe.log_error(f"AI Job Failed: {str(e)}", "AI Queue Service")


def process_financial_prediction(company, filters, job_doc):
    """Process financial prediction analysis"""
    from material_ledger.material_ledger.services.ai_prediction_service import AIPredictionService
    
    prediction_service = AIPredictionService()
    
    # Update progress
    job_doc.progress = 20
    job_doc.save()
    
    # Get historical data in chunks
    data = prediction_service.get_historical_data(company, filters)
    chunks = prediction_service.chunk_financial_data(data)
    
    # Update progress
    job_doc.progress = 40
    job_doc.save()
    
    # Process chunks
    predictions = []
    for i, chunk in enumerate(chunks):
        chunk_prediction = prediction_service.predict_chunk(chunk)
        predictions.append(chunk_prediction)
        
        # Update progress
        progress = 40 + (50 * (i + 1) / len(chunks))
        job_doc.progress = int(progress)
        job_doc.save()
    
    # Combine predictions
    final_result = prediction_service.combine_predictions(predictions)
    
    # Update progress
    job_doc.progress = 95
    job_doc.save()
    
    return final_result


def process_anomaly_detection(company, filters, job_doc):
    """Process anomaly detection analysis"""
    from material_ledger.material_ledger.services.ai_anomaly_service import AIAnomalyService
    
    anomaly_service = AIAnomalyService()
    
    # Update progress
    job_doc.progress = 25
    job_doc.save()
    
    # Get transaction data
    data = anomaly_service.get_transaction_data(company, filters)
    chunks = anomaly_service.chunk_transaction_data(data)
    
    # Update progress  
    job_doc.progress = 50
    job_doc.save()
    
    # Detect anomalies in chunks
    anomalies = []
    for i, chunk in enumerate(chunks):
        chunk_anomalies = anomaly_service.detect_chunk_anomalies(chunk)
        anomalies.extend(chunk_anomalies)
        
        # Update progress
        progress = 50 + (40 * (i + 1) / len(chunks))
        job_doc.progress = int(progress)
        job_doc.save()
    
    # Generate final report
    final_result = anomaly_service.generate_anomaly_report(anomalies)
    
    return final_result


def process_investment_analysis(company, filters, job_doc):
    """Process investment analysis"""
    from material_ledger.material_ledger.services.ai_investment_service import AIInvestmentService
    
    investment_service = AIInvestmentService()
    
    # Update progress
    job_doc.progress = 30
    job_doc.save()
    
    # Get investment data
    data = investment_service.get_investment_data(company, filters)
    
    # Update progress
    job_doc.progress = 60
    job_doc.save()
    
    # Analyze investment opportunities
    result = investment_service.analyze_investments(data)
    
    # Update progress
    job_doc.progress = 90
    job_doc.save()
    
    return result


def process_comprehensive_analysis(company, filters, job_doc):
    """Process comprehensive financial analysis"""
    from material_ledger.material_ledger.services.ai_service import get_ai_service
    
    ai_service = get_ai_service()
    
    # Update progress
    job_doc.progress = 20
    job_doc.save()
    
    # Get comprehensive financial data
    from material_ledger.material_ledger.api import get_financial_analysis
    financial_data = get_financial_analysis(company, str(filters.get('year', 2026)))
    
    # Update progress
    job_doc.progress = 50
    job_doc.save()
    
    # Generate AI report
    ai_report = ai_service.generate_financial_report(company, filters.get('year', 2026), financial_data)
    
    # Update progress
    job_doc.progress = 90
    job_doc.save()
    
    return {
        "financial_data": financial_data,
        "ai_analysis": ai_report,
        "generated_at": now()
    }


def send_completion_notification(user, job_type, job_id, result):
    """Send completion notification to user"""
    try:
        notification_doc = frappe.get_doc({
            "doctype": "Notification Log",
            "for_user": user,
            "type": "Alert",
            "subject": _("AI Analysis Complete"),
            "email_content": _("Your {0} analysis has been completed successfully. Job ID: {1}").format(job_type, job_id),
            "document_type": "AI Job Queue",
            "document_name": job_id
        })
        notification_doc.insert()
        
        # Also create a system notification
        frappe.publish_realtime(
            event="ai_job_complete",
            message={
                "job_id": job_id,
                "job_type": job_type,
                "status": "completed"
            },
            user=user
        )
        
    except Exception as e:
        frappe.log_error(f"Notification Error: {str(e)}", "AI Queue Service")


def send_error_notification(user, job_type, job_id, error):
    """Send error notification to user"""
    try:
        notification_doc = frappe.get_doc({
            "doctype": "Notification Log",
            "for_user": user,
            "type": "Alert", 
            "subject": _("AI Analysis Failed"),
            "email_content": _("Your {0} analysis failed. Job ID: {1}. Error: {2}").format(job_type, job_id, error),
            "document_type": "AI Job Queue",
            "document_name": job_id
        })
        notification_doc.insert()
        
        # Also create a system notification
        frappe.publish_realtime(
            event="ai_job_error",
            message={
                "job_id": job_id,
                "job_type": job_type,
                "status": "failed",
                "error": error
            },
            user=user
        )
        
    except Exception as e:
        frappe.log_error(f"Error Notification Error: {str(e)}", "AI Queue Service")


# API Endpoints
@frappe.whitelist()
def queue_ai_analysis(job_type, company, filters=None):
    """API endpoint to queue AI analysis"""
    if not filters:
        filters = {}
    if isinstance(filters, str):
        filters = json.loads(filters)
        
    queue_service = AIQueueService()
    return queue_service.create_ai_job(job_type, company, filters)


@frappe.whitelist()
def get_ai_job_status(job_id):
    """API endpoint to get job status"""
    queue_service = AIQueueService()
    return queue_service.get_job_status(job_id)


@frappe.whitelist()
def get_user_ai_jobs():
    """Get all AI jobs for current user"""
    jobs = frappe.get_all(
        "AI Job Queue",
        filters={"user": frappe.session.user},
        fields=["job_id", "job_type", "company", "status", "progress", "created_at", "completed_at"],
        order_by="created_at desc",
        limit=50
    )
    return jobs