from flask import abort, request
from flask.views import MethodView
from flask_smorest import Blueprint
from db import db
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func, select
from datetime import datetime, timezone, date
from .utils import create_notification

from models.invoices import Invoices, StatusEnumList
from models import Users ,Payments, RefundDisputes
from models.coach_client_relationships import CoachClientRelationships

from schemas.invoice_schema import CreateInvoiceSchema, CreateDisputeSchema

invoice_blp = Blueprint("InvoiceOperations", __name__, url_prefix="/invoice", description="Invoice Operations")

### Coaches issues an invoice to a client
@invoice_blp.route("/issue-invoice")
class IssueInvoiceView(MethodView):
    @jwt_required()
    @invoice_blp.arguments(CreateInvoiceSchema)
    @invoice_blp.response(201, CreateInvoiceSchema)
    def post(self, data):
        current_coach_id = get_jwt_identity()
        coach = Users.query.filter_by(auth_id=current_coach_id).first()
        if not coach:
            abort(404, description="Coach not found.")

        relationship = CoachClientRelationships.query.filter_by(
            coach_profile_id=coach.user_id,
            client_user_id=data['client_user_id'] 
        ).first()
        if not relationship:
            abort(404, description="You do not have an active relationship with this client.")

        new_invoice = Invoices(
            relationship_id=relationship.relationship_id,
            subtotal=data['subtotal'],         
            currency="USD",                  
            payment_method_id=1,             
            issued_at=datetime.utcnow(),
            pay_date=data.get('pay_date')
        )

        try:
            db.session.add(new_invoice)
            db.session.commit()
            #Notification goes here?
            return new_invoice
            
        except Exception as e:
            db.session.rollback()
            abort(500, description=f"Database error while issuing invoice: {str(e)}")

### Coach voids an invoice
@invoice_blp.route("/void-invoice/<int:invoice_id>")
class VoidInvoiceView(MethodView):
    @jwt_required()
    @invoice_blp.response(200, CreateInvoiceSchema) 
    def patch(self, invoice_id):
        current_coach_id = get_jwt_identity()
        coach = Users.query.filter_by(auth_id=current_coach_id).first()
        
        if not coach:
            abort(404, description="Coach not found.")

        invoice = Invoices.query.filter_by(invoice_id=invoice_id).first()
        if not invoice:
            abort(404, description="Invoice not found.")

        relationship = CoachClientRelationships.query.filter_by(
            relationship_id=invoice.relationship_id,
            coach_profile_id=coach.user_id
        ).first()

        if not relationship:
            abort(403, description="You do not have permission to void this invoice.")

        if invoice.status.name == "succeeded" or invoice.status.name == "paid":
            abort(400, description="Cannot void an invoice that has already been paid.")

        invoice.status = StatusEnumList.voided

        try:
            db.session.commit()
            
            #notification goes here
            return invoice
            
        except Exception as e:
            db.session.rollback()
            abort(500, description=f"Database error while voiding invoice: {str(e)}")

### Client disputes an invoice and sends it to admin for review
@invoice_blp.route("/dispute-invoice/<int:invoice_id>")
class DisputeInvoiceView(MethodView):
    @jwt_required()
    @invoice_blp.arguments(CreateDisputeSchema)
    def post(self, data, invoice_id):
        current_client_id = get_jwt_identity()
        client = Users.query.filter_by(auth_id=current_client_id).first()
        
        if not client:
            abort(404, description="Client not found.")

        invoice = Invoices.query.filter_by(invoice_id=invoice_id).first()
        if not invoice:
            abort(404, description="Invoice not found.")

        relationship = CoachClientRelationships.query.filter_by(
            relationship_id=invoice.relationship_id,
            client_user_id=client.user_id
        ).first()

        if not relationship:
            abort(403, description="You do not have permission to dispute this invoice.")

        if invoice.status.name != "paid":
            abort(400, description="Only paid invoices can be disputed.")

        payment = Payments.query.filter_by(invoice_id=invoice.invoice_id).first()
        if not payment:
            abort(404, description="Could not find the payment record tied to this invoice.")

        new_dispute = RefundDisputes(
            payment_id=payment.payment_id,
            opened_by_user_id=client.user_id,
            reason=data['reason']
        )

        try:
            db.session.add(new_dispute)
            invoice.status = StatusEnumList.under_review 
            db.session.commit()
            #Notification goes here?
            return {"message": "Invoice disputed successfully. Admin will review the dispute."}, 201
            
        except Exception as e:
            db.session.rollback()
            abort(500, description=f"Database error while submitting dispute: {str(e)}")