import boto3
import json

s3= boto3.client('s3')
rekognition = boto3.client('rekognition', region_name='us-east-1')
dynamodbTableName = 'student-record'
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
studentTable = dynamodb.Table(dynamodbTableName)
bucketName = 'visitor-student-image-storage'
threshold = 80
attendanceId = []


def lambda_handler(event, context):
    print('event: ', json.dumps(event))
    Key = event['Records'][0]['s3']['object']['key']
    try:
        response = index_student_image(bucketName,Key)
        print(response)
    except Exception as e:
        print(e)
        print('Error processing object {} from bucket {}. '.format(Key, bucketName))
        raise e
    for record in response['FaceRecords']:
        try:
            response1=rekognition.search_faces(CollectionId='students',
                                                FaceId=record['Face']['FaceId'],
                                                MaxFaces=2,
                                                FaceMatchThreshold= threshold
                                            )
            print(response1)
        except Exception as e:
            print("failed")
            raise e
        attendanceId.append(response1['FaceMatches'][0]['Face']['FaceId'])
    for faceID in attendanceId:
        update_attendance(faceID, 'yes')

    return "success"
    

def update_attendance(faceId, attendance):
    update_response = studentTable.update_item(
            Key={'rekognitionid': faceId},
            UpdateExpression='SET attendance = :yes',
            ExpressionAttributeValues={
                ':yes' : attendance
            })
    print("UPDATED_NEW")
    return True

def index_student_image(bucket, key):
    response = rekognition.index_faces(
        Image = {
            'S3Object': {
                'Bucket': bucket,
                'Name': key
            }
        },
        CollectionId='students'
    )
    return response
