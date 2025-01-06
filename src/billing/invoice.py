from amazonservice.dynamodb import get_item, query_item, update_item
from settings.constants import BUCKETNAME, INVOICETABLE
from settings.env import get_env_vars
from typing import Dict, Optional
import requests
from amazonservice.download import upload_s3_files
from datetime import datetime
import time
from settings.configuration import DEV_S3BUCKET, DEVINVOICE_TABLE
from subscriptions.stripe_service import *

def get_invoice(event: Dict, user: str, email: str, username: str) -> Dict:
    try:
        env_vars: Dict[str, Optional[str]] = get_env_vars()
        AWS_BUCKET_NAME = env_vars.get(BUCKETNAME,'zita-featurez24-297')
        table= env_vars.get(INVOICETABLE ,'invoice-featureZ24-278')
        if 'feature' in table:
            table= DEVINVOICE_TABLE 
        if 'feature' in AWS_BUCKET_NAME:
            AWS_BUCKET_NAME = DEV_S3BUCKET
        item = query_item(table,'email',email)
        download_url = None
        inv_id = None
        if event.get('queryparams'):
            if event.get('queryparams'):
                queryparams = event.get('queryparams')
                invoice_id = queryparams.get('invoice_id')
                inv_id = invoice_id
                if invoice_id:
                    inv_key = {'email':email, 'invoice':invoice_id} 
                    invoice_obj = get_item(table,inv_key)
                    if invoice_obj.get('invoice_pdf'):
                        download_url = invoice_obj.get('invoice_pdf')
                    if invoice_obj.get('download_url'):
                        download_url = invoice_obj.get('download_url')
                    if download_url:
                        download_content = invoice_download(download_url)
                        if download_content is None:
                            created_at = invoice_obj.get('payment_date')
                            inv_number = invoice_obj.get('invoice_id')
                            '''Step-1 Downloaded Invoice'''
                            if get_download_invoice_pdf(inv_number):
                                download_content = get_download_invoice_pdf(inv_number)
                                invoiceobj_id = inv_number
                            else: 
                                '''Step-2 Downloaded Invoice'''
                                download_content,invoiceobj_id = invoice_expired_link(created_at,invoice_id)
                            update_expired_invoice(table,inv_key,invoiceobj_id)
                        if download_content:                          
                            dt = datetime.now()
                            formatted_date = dt.strftime("%d.%m.%Y")
                            filename = f"Billing_Invoice_{formatted_date}.pdf"
                            download_url = upload_s3_files(AWS_BUCKET_NAME,'Invoice',filename,download_content)
                        else:
                            raise Exception('Invoice Link Expired')
                else:
                    raise Exception('give me invoice id in queryparams')
        item_length = len(item) - 1
        data = {
            'statusCode':200,
            'success': True,
            'item':item,
            'item_length':item_length,
            'download_url':download_url,
            'inv_id':inv_id,
            'message': "get User invoice successfully"} 
        return data
    except Exception as e:
        return {'statusCode': 400,'success': False, 'error': str(e)} 

  

def invoice_download(url):  
    if url:
        response = requests.get(url)
        # Check if the request was successful
        pdf_content = None
        if response.status_code == 200:
            pdf_content = response.content

        return pdf_content
    
def invoice_extraction(invoice,invoice_id):
    if invoice['number'] == invoice_id:
        invoice_obj = Invoice.retrieve_invoice(invoice['id'])
        invoice_number = invoice['id']
        if invoice_obj.get('invoice_pdf'):
            download_url = invoice_obj.get('invoice_pdf')
        if invoice_obj.get('download_url'):
            download_url = invoice_obj.get('download_url')
        if download_url:
            download_content = invoice_download(download_url)
            return download_content,invoice_number
    return None,None
        
def find_invoice(first_invoice,invoice_id):
    if first_invoice:
        new_first_invoice = None
        invoices = Invoice.invoice_list(ending_before=first_invoice, limit=100)
        for ids, invoice in enumerate(invoices['data']):
            if ids == 0:
                new_first_invoice = invoice['id']
            download_content,invoice_number = invoice_extraction(invoice,invoice_id)
            if download_content and invoice_number:
                return download_content,invoice_number
        if new_first_invoice:
            download_content,invoice_id = find_invoice(new_first_invoice,invoice_id)
            if download_content and invoice_id:
                return download_content,invoice_id
    return None,None

    

def invoice_expired_link(date_str,invoice_id):
    try:
        current_date = datetime.strptime(date_str,'%Y-%m-%d %H:%M:%S.%f' )
    except:
        current_date = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
    next_day = current_date + timedelta(days=1)
    timestamp = int(time.mktime(next_day.timetuple()))
    invoices = Invoice.invoice_list(created={'lte': timestamp}, limit=1000)

    first_invoice = None
    for ids, invoice in enumerate(invoices['data']):
        if ids == 0:
            first_invoice = invoice['id']
        download_content,invoice_number = invoice_extraction(invoice,invoice_id)
        if download_content and invoice_number:
            return download_content,invoice_number
    if first_invoice:
        download_content,invoice_id = find_invoice(first_invoice,invoice_id)
        if download_content and invoice_id:
            return download_content,invoice_id
    return None, None

def update_expired_invoice(table,inv_key,invoice_id):
    if invoice_id:
        invoice_obj = Invoice.retrieve_invoice(invoice_id)
        invoice_id = invoice_obj.get('id')
        invoice_pdf =  invoice_obj.get('invoice_pdf')
        update_expression = 'SET #inv_pdf = :inv_pdf_val,#inv_id = :inv_id_val'
        attribute_names = {'#inv_pdf': 'invoice_pdf','#inv_id':'invoice_id'}
        attribute_values = {':inv_pdf_val': invoice_pdf,':inv_id_val':invoice_id}
        table_updation = update_item(table,inv_key,update_expression,attribute_values,attribute_names)


def get_download_invoice_pdf(invoice_id):
    if invoice_id:
        invoice_obj = Invoice.retrieve_invoice(invoice_id)
        invoice_pdf = invoice_obj.get('invoice_pdf')
        if invoice_pdf:
            download_content = invoice_download(invoice_pdf)
            return download_content
    return None
            

    
    
    


