import os
from flask import Flask, render_template, request
import mysql.connector
import os.path
import mysql.connector
import boto3,botocore
from collections import OrderedDict
import random

app = Flask(__name__)
app.config['UPLOAD_FOLDER']="static/" #the path for images folder
path = './static/'

#app.config['S3_BUCKET']="cloudprojs3"
#app.config['S3_LOCATION']='http://cloudprojs3.s3.amazonaws.com/'

#app.config['KEY']= "AKIAYZCL2IUQ5ECJA26T"
#app.config['SECRET']="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"

ec2 = boto3.resource(
   'ec2',
   region_name ='us-east-1',
   aws_access_key_id = app.config['KEY'],
   aws_secret_access_key = app.config['SECRET']
   )
import os
from flask import Flask, render_template, request
import mysql.connector
import os.path
import mysql.connector
import boto3,botocore
from collections import OrderedDict
import random

app = Flask(__name__)
app.config['UPLOAD_FOLDER']="static/" #the path for images folder
path = './static/'

app.config['S3_BUCKET']="cloudprojs3"
app.config['S3_LOCATION']='http://cloudprojs3.s3.amazonaws.com/'

app.config['KEY']= "AKIAYZCL2IUQ5ECJA26T"
app.config['SECRET']="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"

ec2 = boto3.resource(
   'ec2',
   region_name ='us-east-1',
   aws_access_key_id = app.config['KEY'],
   aws_secret_access_key = app.config['SECRET']
                                                                             
)
autoScaling = boto3.client(
   "autoscaling",
   region_name ='us-east-1',
   aws_access_key_id = app.config['KEY'],
   aws_secret_access_key = app.config['SECRET']
)

cloudWatch = boto3.client(
   "cloudwatch",
   region_name ='us-east-1',
   aws_access_key_id = app.config['KEY'],
   aws_secret_access_key = app.config['SECRET']
)

policy = '0'
capacity = 0
li = []
cache = OrderedDict()
@app.route('/')
def main() :
    return render_template("index.html")

@app.route('/manager',methods=['GET','POST'])
def manager():
    global capacity, policy, li
    if request.method == 'POST':
        if request.form.get('apply')=='Apply' :
           capacity = int(request.form['capacityMB'])
           clearMemcache()
           for x in range(capacity) :
                createInstance()
           instancesInfo = ec2Client.describe_instances()
           data = instancesInfo["Reservations"]
           for instances in data:
               instance=instances["Instances"]
               for ids in instance:
                   instance_id = ids['InstanceId']
                   if instance_id == "i-092827afdafcdc0a7" or ids['State']['Name'] == "terminated":
                      continue
                   li.append(instance_id)
          policy = request.form['replacepolicy']
        if request.form.get('grow') == 'Grow (+1)':
           capacity = capacity + 1
           if capacity > 8 :
              return render_template ("manager.html", message = "Maxmum number of instance has been created (8)" )
           createInstance()
        elif request.form.get('shrink') == 'Shrink (-1)':
           capacity = capacity - 1
           if(policy=='0'):
             deleteInstance()
           elif(policy=='1'):
             lru()
           print("Shrink")
           if capacity < 1 :
              return render_template ("manager.html", message = 'Has no instances to delete(minmum 1)')
           #if policy == '0' :
              #print("policy")
#              randomPolicy()
          # deleteInstance()
        if request.form.get('clearmem') == 'Clear Memcache' :
              clearMemcache()
        elif request.form.get('clear') == 'Clear Database & S3' :
              deleteDatabaseAndS3()
    return render_template("manager.html")

@app.route('/request', methods = ['GET','POST'])
def req():
    if request.method == 'POST' :

        try:
            con=mysql.connector.connect(host='database-2.ce56zqclzkbk.us-east-1.rds.amazonaws.com',username='admin',password='lamamaialaa',database='cddb')
            #con = mysql.connector.connect(host = 'localhost', user = 'root', password = '1955', database = 'db')
            cur = con.cursor()
            key = request.form['key']
            cur.execute("SELECT keyy FROM images WHERE keyy = %s", [key])
            isNewKey = len(cur.fetchall()) == 0

            if not isNewKey :
                 name = s3.generate_presigned_url('get_object', Params = {'Bucket': "cloudprojs3", 'Key': key}, ExpiresIn = 100)

            else :
                 return render_template('request.html', keyCheck = "key not found !")
            return render_template('request.html', user_image = name)

        except:
            return("error occur")

        finally:
            con.close()

    return render_template('request.html')

@app.route('/upload', methods = ['POST','GET'])
def upload():
    if request.method=='POST':
        key= request.form['key1']
        con=mysql.connector.connect(host='database-2.ce56zqclzkbk.us-east-1.rds.amazonaws.com',username='admin',password='lamamaialaa',database='cddb')
       #con = mysql.connector.connect(host = 'localhost', user = 'root', password = '1955', database = 'db')
        cur = con.cursor()
        image = request.files['image']

        if image.filename != '':
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], image.filename)
            image.save(filepath)
        cur.execute("SELECT keyy FROM images WHERE keyy = %s", [key])
            isNewKey = len(cur.fetchall()) == 0
            # saveFile(path + image.filename, image.filename, imagePath)

            if(isNewKey) :
                s3.upload_file(Filename=filepath,Bucket=app.config["S3_BUCKET"],Key=key)
                cur.execute("INSERT INTO images (keyy,image) VALUES(%s,%s)",(key,image.filename))
                #s3.upload_file(Filename=f"{imagePath}/{image.filename}",Bucket=app.config["S3_BUCKET"],Key=key)
                done = "Upload Successfully"

            else :
                s3.upload_file(Filename=filepath,Bucket=app.config["S3_BUCKET"], Key = key)
                cur.execute("UPDATE images SET image = %s WHERE keyy = %s", (image.filename,key))
                done = "Update Successfully"

            con.commit()
            con.close()
            return render_template('upload.html', done = done)

    return render_template('upload.html')

@app.route('/list', methods = ['POST','GET'])
def keyList():
    if request.method == 'GET' :
        try:
            con=mysql.connector.connect(host='database-2.ce56zqclzkbk.us-east-1.rds.amazonaws.com',username='admin',password='lamamaialaa',database='cddb')
            #con = mysql.connector.connect(host = 'localhost', user = 'root', password = '1955', database = 'db')
            cur = con.cursor()
            cur.execute("SELECT keyy FROM images")
            con.commit()

        except:
            return 'error'

        finally:
            return render_template('KeyList.html', keys=[str(val[0]) for val in cur.fetchall()])

    return render_template('KeyList.html')
def createInstance() :
    global ec2, li
    ec2.create_instances(
        ImageId = 'ami-098a105cd8df85ff3',
        MinCount = 1,
        MaxCount = 1,
        InstanceType ='t2.micro',
        KeyName='test',
        SecurityGroups =  ['launch-wizard-4', 'ec2-rds-6']
        )
    instancesInfo = ec2Client.describe_instances()
    data = instancesInfo["Reservations"]
    for instances in data:
        instance=instances["Instances"]
        for ids in instance:
            instance_id = ids['InstanceId']
            if ids['State']['Name'] == "pending":
               li.append(instance_id)
       #        position(instance_id)

def deleteInstance() :
    global li
    ec2Client.stop_instances(InstanceIds=[random.choice(li)])
def clearMemcache() :
    global li
    if len(li) > 0 :
       ec2Client.stop_instances(InstanceIds=li)
    li = []

def deleteDatabaseAndS3() :
    con=mysql.connector.connect(host='database-2.ce56zqclzkbk.us-east-1.rds.amazonaws.com',username='admin',password='lamamaialaa',database='cddb')
    # con = mysql.connector.connect(host = 'localhost', user = 'root', password = '1955', database = 'db')
    cur = con.cursor()
    cur.execute("DROP TABLE images")
    con.commit()
    con.close()
    createDatabase()
    objects = s3.list_objects(Bucket=app.config['S3_BUCKET'])['Contents']
    for obj in objects:
        s3.delete_object(Bucket=app.config['S3_BUCKET'], Key=obj['Key'])

def createDatabase() :
    con=mysql.connector.connect(host='database-2.ce56zqclzkbk.us-east-1.rds.amazonaws.com',username='admin',password='lamamaialaa',database='cddb')
    #con = mysql.connector.connect(host = 'localhost', user = 'root', password = '1955', database = 'db')
    cur = con.cursor()
    cur.execute("CREATE TABLE images (keyy INT PRIMARY KEY NOT NULL, image VARCHAR(255) NOT NULL)")
    con.commit()
    con.close()


def lru():
  global li
  ec2Client.stop_instances(InstanceIds=[li[len(li)-1]])
if __name__ == '__main__':
    app.run('0.0.0.0',5001,debug=True)
