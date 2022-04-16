import boto3
import os
import json
import re

def handler(event, context):
    print(event)
    print(event['body'])

    if event['httpMethod'] == "DELETE":
        if check(event['body']):
            if event['resource'] == "/api/email/unsubscribe":
                unsubscribe(event['body'])
                return api_response("Success", 200)
            else:
                return api_response("Failure", 404)
        else:
            return api_response("Invalid email", 400)
    elif event['httpMethod'] == "POST":
        if check(event['body']):
            if event['resource'] == "/api/email/subscribe":
                subscribe(event['body'])
                return api_response("Success", 200)
            else:
                return api_response("Failure", 404)
        else:
            return api_response("Invalid email", 400)
    else:
        return api_response("Failure", 404)


def check(email):
    regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    if(re.fullmatch(regex, email)):
        return True
    else:
        return False

def api_response(text, code):
    outcome = {
        "isBase64Encoded": 'false',
        "statusCode": code,
        "headers": {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': '*',
            'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
        },
        "body": text
    }

    return outcome

def unsubscribe(email):
    print("Unsubscribe: "+email)
    client = boto3.client('s3')
    output_file = '/tmp/email-list.txt'
    new_file = '/tmp/email-list-new.txt'
    client.download_file(os.environ['BUCKET_NAME'], os.environ['EMAIL_LIST_KEY'], output_file)
    
    file_input = open(output_file, 'r')
    Lines = file_input.readlines()
    
    file_ouptut = open(new_file, 'w')
    for line in Lines:
        if line.strip() != email.strip():
            file_ouptut.writelines(line)
    file_ouptut.close()

    client.upload_file(new_file, os.environ['BUCKET_NAME'], os.environ['EMAIL_LIST_KEY'])

    ses_client = boto3.client('ses')
    print("Emailing "+email.strip())
    response = ses_client.send_email(
        Source="blog-notifications@claytondavis.dev",
        Destination={
            'ToAddresses': [
                email.strip(),
            ]
        },
        Message={
            'Subject': {
                'Data': "Unsubscribed - blog.claytondavis.dev",
                'Charset': 'UTF-8'
            },
            'Body': {
                'Html': {
                    'Data': "You have been unsubscribed - come back soon!",
                    'Charset': 'UTF-8'
                }
            }
        },
        ReplyToAddresses=[
            'blog@claytondavis.dev',
        ]
    )
    print(response)

    return True

def subscribe(email):
    print("Subscribe: "+email)
    client = boto3.client('s3')
    email_file = '/tmp/email-list.txt'
    client.download_file(os.environ['BUCKET_NAME'], os.environ['EMAIL_LIST_KEY'], email_file)
    
    exists = False
    file_input = open(email_file, 'r')
    Lines = file_input.readlines()
    for line in Lines:
        if line.strip() == email.strip():
            exists = True

    if not exists:
        file_ouptut = open(email_file, 'a')
        file_ouptut.writelines("\n"+email.strip())
        file_ouptut.close()

    client.upload_file(email_file, os.environ['BUCKET_NAME'], os.environ['EMAIL_LIST_KEY'])

    ses_client = boto3.client('ses')
    print("Emailing "+email.strip())
    response = ses_client.send_email(
        Source="blog-notifications@claytondavis.dev",
        Destination={
            'ToAddresses': [
                email.strip(),
            ]
        },
        Message={
            'Subject': {
                'Data': "Thank you for subscribing - blog.claytondavis.dev",
                'Charset': 'UTF-8'
            },
            'Body': {
                'Html': {
                    'Data': "Thank you for subscribing! <br /><br /><a href=\"https://blog.claytondavis.dev/unsubscribe/index.html?email="+line+"\">Unsubscribe</a>",
                    'Charset': 'UTF-8'
                }
            }
        },
        ReplyToAddresses=[
            'blog@claytondavis.dev',
        ]
    )
    print(response)

    return True

def sendEmail(event, context):
    print(event)
    print("Subject: "+event['subject'])
    print("Body: "+event['body'])

    client = boto3.client('s3')
    email_file = '/tmp/email-list.txt'
    client.download_file(os.environ['BUCKET_NAME'], os.environ['EMAIL_LIST_KEY'], email_file)
    
    exists = False
    file_input = open(email_file, 'r')
    Lines = file_input.readlines()
    ses_client = boto3.client('ses')
    for line in Lines:
        if line.strip() != '':
            print("Emailing "+line.strip())
            response = ses_client.send_email(
                Source="blog-notifications@claytondavis.dev",
                Destination={
                    'ToAddresses': [
                        line.strip(),
                    ]
                },
                Message={
                    'Subject': {
                        'Data': event['subject'],
                        'Charset': 'UTF-8'
                    },
                    'Body': {
                        'Html': {
                            'Data': event['body']+"<br /><br /><a href=\"https://blog.claytondavis.dev/unsubscribe/index.html?email="+line+"\">Unsubscribe</a>",
                            'Charset': 'UTF-8'
                        }
                    }
                },
                ReplyToAddresses=[
                    'blog@claytondavis.dev',
                ]
            )
            print(response)
