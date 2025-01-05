from datetime import datetime
import tika
tika.initVM()
from tika import parser
from openai_client import client
import pdfplumber
import json
from docx import Document
from PyPDF2 import PdfReader


def tika_parser(filename):
    text_from_document = None
    try:
        tika.initVM()
        headers = {"X-Tika-OCRLanguage": "eng","X-Tika-PDFextractInlineImages": "true"}
        doc1 = parser.from_file(filename, headers= headers)
        while '\n\n' in doc1['content']:
            doc1['content']=doc1['content'].replace('\t',' ').replace('\n\n','\n')
        while '  ' in doc1['content']:
            doc1['content']=doc1['content'].replace('  ',' ')
        text_from_document=doc1['content'].encode().decode('ascii','ignore')
        ''' Text cleaning for mulitple spaces and . - . Add if anything else is needed'''
    except Exception as e:
        print("Error in tika",e)
        text_from_document = None
    return text_from_document


def tika_bytes_parser(bytes_io_obj):
    text_from_document = None
    try:
        tika.initVM()
        bytes_data = bytes_io_obj.getvalue()
        headers = {"X-Tika-OCRLanguage": "eng", "X-Tika-PDFextractInlineImages": "true"}
        doc = parser.from_buffer(bytes_data, headers=headers)
        cleaned_text = doc['content'].replace('\t', ' ').replace('\n\n', '\n').replace('  ', ' ')
        text_from_document = cleaned_text.encode().decode('ascii', 'ignore')
    except Exception as e:
        print("Error in tika bytes:", e)
        text_from_document = None
    return text_from_document


def extract_text_from_pdf(pdf_path,filename):
    text_from_document = ""
    try:
        if filename.endswith(".pdf"):
            # with pdfplumber.open(pdf_path) as pdf:
            #     for page in pdf.pages:
            #         text_from_document += page.extract_text()
            reader = PdfReader(pdf_path)
            text_from_document = ""

            for page in reader.pages:
                text_from_document += page.extract_text()

        elif filename.endswith(".txt"):
            text_from_document = pdf_path.getvalue()

            text_from_document = bytes_extract(text_from_document)
        elif filename.endswith(".docx") or filename.endswith(".doc"):
            doc = Document(pdf_path)
            full_text = []
            for para in doc.paragraphs:
                full_text.append(para.text)
            text_from_document = '\n'.join(full_text)
        else:
            text_from_document = ''
    except Exception as e:
        print("Error extracting text from PDF:", e)
    return text_from_document


def FineTuningModal(system,user_message,modal):
    try:
        completion = client.chat.completions.create(
                model=modal,
                temperature=0, 
                top_p=0,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user_message}
                ])
        response = (completion.choices[0].message).content
        token = completion.usage.total_tokens
    except Exception as e:
        print("Exception in Finetune",e)
        response = None
        token = 0
    return response,token


def bytes_extract(bytes_data): 
    if isinstance(bytes_data, bytes):
        json_string = bytes_data.decode('utf-8')
        try:
            data_list = json.loads(json_string)
        except:
            data_list = json_string
        return data_list
    return bytes_data


def extract_date(timestamp):
    if timestamp and timestamp != "None":
        try:
            dt_object = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S.%f")
        except:
            if 'Product Duration' in timestamp:
                dt_object = '-'
            elif timestamp:
                dt_object = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
            else:
                dt_object = timestamp
        # Convert to desired format
        if dt_object != '-' and dt_object:
            original_month = dt_object.month
            formatted_date = f"{dt_object.day:02}-{original_month:02}-{dt_object.year}"
            # formatted_date = dt_object.strftime("%d-%m-%Y")
            # formatted_date = f"{int(formatted_date[:2])}-{int(formatted_date[3:5])}-{formatted_date[6:]}"
            return formatted_date
        else:
            return dt_object

    else:
        return "-"    