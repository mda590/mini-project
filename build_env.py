#!/usr/bin/python

import boto3
import botocore
import argparse
import urllib2
import json
import time
from troposphere import Base64, FindInMap, GetAtt, Join, Output, Parameter, Ref, Tags, Template
from troposphere.ec2 import PortRange, NetworkAcl, Route, \
    VPCGatewayAttachment, SubnetRouteTableAssociation, Subnet, RouteTable, \
    VPC, NetworkInterfaceProperty, NetworkAclEntry, \
    SubnetNetworkAclAssociation, EIP, Instance, InternetGateway, \
    SecurityGroupRule, SecurityGroup
from troposphere.policies import CreationPolicy, ResourceSignal
from troposphere.cloudformation import Init, InitFile, InitFiles, \
    InitConfig, InitService, InitServices, Metadata

stack_name = 'matt-adorjan-mini-project'

def run_tests(http_address):
    ''' Tests to ensure that the HTTP server is up and displaying the correct content. '''
    print
    print '################ 4. Test Phase ################'
    print 'Confirming whether Automation for the People appears on the page served by our instance.'
    
    # Connect to index.html page on newly deployed instance
    response = urllib2.urlopen(http_address)
    html = response.read()
    expected_text = 'Automation for the People!'

    # Verify that the expected text exists in the index.html page
    if(expected_text in html):
        print 'Tests PASSED! Automation for the People was found on the index.html page.'
    else:
        print 'Tests FAILED! Automation for the People was not found on the index.html page.'

def create_stack(key, secretKey, region, template):
    ''' Creates the CloudFormation stack based off of the template generated. '''
    print
    print '################ 3. Stack Creation Phase ################'
    
    cfn = boto3.client(
        'cloudformation',
        region_name=region,
        aws_access_key_id=key,
        aws_secret_access_key=secretKey
    )
    
    # Set the seconds counter to display duration of stack build process
    seconds = 0

    # Validate the CloudFormation template syntax
    try:
        print 'Validating the CloudFormation template syntax.'
        cfn.validate_template(TemplateBody=template)
    except botocore.exceptions.ClientError as err:
        print 'CloudFormation template validation failed: %s' % err.response['Error']['Message']
    
    print 'CloudFormation template validated successfully!'

    # Create the stack and monitor progress
    try:
        cfn.create_stack(StackName=stack_name, TemplateBody=template)

        stackCreationRunning = True
        while stackCreationRunning:
            stacks_description = cfn.describe_stacks(StackName=stack_name)
            status = stacks_description['Stacks'][0]['StackStatus']

            if(status == 'CREATE_COMPLETE'):
                print
                print 'CloudFormation stack build completed!'

                # Get the URL of the EC2 instance to return
                for output in stacks_description['Stacks'][0]['Outputs']:
                    if output['OutputKey'] == 'URL':
                        http_url = output['OutputValue']

                # Print stack details
                print
                print '#### Stack Details ####'
                print 'Stack name: ' + stack_name
                print 'HTTP server URL: ' + http_url
                stackCreationRunning = False

                return http_url

            # If stack creation failed and rolled back
            elif(status == 'ROLLBACK_COMPLETE'):
                print 'CloudFormation stack creation failed.' \
                        'For more information, check the AWS console.'
                stackCreationRunning = False

            # If stack creatino is still in progress
            else:
                print 'CloudFormation stack is building... (' + str(seconds) + ' seconds)'
                # Display the time elapsed since the build started
                seconds = seconds + 5
                # Wait 5 seconds before checking status again
                time.sleep(5)
    
    except botocore.exceptions.ClientError as err:
        print 'CloudFormation stack creation failed: %s' % err.response['Error']['Message']

def build_template(keyPair, instanceType):
    ''' Builds the CloudFormation template which will create EC2 and supporting resources. '''
    print
    print '################ 2. Template Build Phase ################'
    print 'Starting CloudFormation template build.'

    ### Template Info ###
    mini_template = Template()
    
    # Define template version and description
    mini_template.add_version('2010-09-09')
    mini_template.add_description('Provisions VPC, IGW, Route Table, Subnet, and EC2 instance in AWS to support a static website.')

    ### Parameters ###
    instance_type = mini_template.add_parameter(
        Parameter(
            'InstanceType',
            Type='String',
            Description='EC2 instance type',
            Default=instanceType,
            AllowedValues=[
                't1.micro',
                't2.micro', 't2.small', 't2.medium',
                'm1.small', 'm1.medium', 'm1.large', 'm1.xlarge',
                'm2.xlarge', 'm2.2xlarge', 'm2.4xlarge',
                'm3.medium', 'm3.large', 'm3.xlarge', 'm3.2xlarge',
                'm4.large', 'm4.xlarge', 'm4.2xlarge', 'm4.4xlarge', 'm4.10xlarge',
                'c1.medium', 'c1.xlarge',
                'c3.large', 'c3.xlarge', 'c3.2xlarge', 'c3.4xlarge', 'c3.8xlarge',
                'c4.large', 'c4.xlarge', 'c4.2xlarge', 'c4.4xlarge', 'c4.8xlarge',
                'g2.2xlarge',
                'r3.large', 'r3.xlarge', 'r3.2xlarge', 'r3.4xlarge', 'r3.8xlarge',
                'i2.xlarge', 'i2.2xlarge', 'i2.4xlarge', 'i2.8xlarge',
                'd2.xlarge', 'd2.2xlarge', 'd2.4xlarge', 'd2.8xlarge',
                'hi1.4xlarge',
                'hs1.8xlarge',
                'cr1.8xlarge',
                'cc2.8xlarge',
                'cg1.4xlarge'
            ],
            ConstraintDescription='must be a valid EC2 instance type.',
        )
    )

    ### Mappings ###
    
    # AMI Mapping for Amazon Linux AMI as of 03-Jan-2017
    mini_template.add_mapping(
        'AWSRegionArch2AMI', {
            'us-east-1':        { 'HVM64': 'ami-9be6f38c' },
            'us-east-2':        { 'HVM64': 'ami-38cd975d' },
            'us-west-1':        { 'HVM64': 'ami-b73d6cd7' },
            'us-west-2':        { 'HVM64': 'ami-1e299d7e' },
            'ca-central-1':     { 'HVM64': 'ami-eb20928f' },
            'eu-west-1':        { 'HVM64': 'ami-c51e3eb6' },
            'eu-west-2':        { 'HVM64': 'ami-bfe0eadb' },
            'eu-central-1':     { 'HVM64': 'ami-211ada4e' },            
            'ap-southeast-1':   { 'HVM64': 'ami-4dd6782e' },
            'ap-southeast-2':   { 'HVM64': 'ami-28cff44b' },
            'ap-northeast-1':   { 'HVM64': 'ami-9f0c67f8' },
            'ap-northeast-2':   { 'HVM64': 'ami-94bb6dfa' },
            'ap-south-1':       { 'HVM64': 'ami-9fc7b0f0' },
            'sa-east-1':        { 'HVM64': 'ami-bb40d8d7' }
        }
    )

    ### Resources ###

    # VPC
    vpc = mini_template.add_resource(
        VPC(
            'VPC', 
            CidrBlock='172.16.0.0/16', 
            EnableDnsSupport='True',
            EnableDnsHostnames='True',
            Tags=Tags(Name=stack_name + '-vpc', Project=stack_name)
        )
    )

    # Internet Gateway
    igw = mini_template.add_resource(
        InternetGateway(
            'InternetGateway', 
            Tags=Tags(Name=stack_name + '-igw', Project=stack_name)
        )
    )

    # Attach IGW to VPC
    attach_gateway = mini_template.add_resource(
        VPCGatewayAttachment(
            'AttachGateway', 
            VpcId=Ref(vpc), 
            InternetGatewayId=Ref(igw)
        )
    )

    # Route Table
    route_table = mini_template.add_resource(
        RouteTable(
            'RouteTable', 
            VpcId=Ref(vpc), 
            Tags=Tags(Name=stack_name + '-routetable', Project=stack_name)
        )
    )

    # Route 0.0.0.0 -> IGW
    route01 = mini_template.add_resource(
        Route(
            'Route', 
            DependsOn='AttachGateway', 
            GatewayId=Ref(igw), 
            DestinationCidrBlock='0.0.0.0/0', 
            RouteTableId=Ref(route_table)
        )
    )

    # Subnet
    subnet = mini_template.add_resource(
        Subnet(
            'Subnet', 
            CidrBlock='172.16.10.0/24', 
            VpcId=Ref(vpc),
            MapPublicIpOnLaunch='True',
            Tags=Tags(Name=stack_name + '-subnet', Project=stack_name)
        )
    )

    # Subnet -> Route Table
    subnet_route_associate = mini_template.add_resource(
        SubnetRouteTableAssociation(
            'SubnetRouteTableAssociation', 
            SubnetId=Ref(subnet), 
            RouteTableId=Ref(route_table)
        )
    )

    # Security Group allowing access via SSH and HTTP
    web_security_group = mini_template.add_resource(
        SecurityGroup(
            'WebSecurityGroup', 
            GroupDescription='Enable access to the web server on ports 80 and 22.', 
            VpcId=Ref(vpc),
            Tags=Tags(Name=stack_name + '-securitygroup', Project=stack_name),
            SecurityGroupIngress=[
                SecurityGroupRule(
                    IpProtocol='tcp',
                    FromPort='22',
                    ToPort='22',
                    CidrIp='0.0.0.0/0'
                ),
                SecurityGroupRule(
                    IpProtocol='tcp',
                    FromPort='80',
                    ToPort='80',
                    CidrIp='0.0.0.0/0'
                )
            ]
        )
    )

    # Metadata to install Apache
    ec2_metadata=Metadata(Init({
        'config': InitConfig(packages={
            'yum': {
                'httpd': []
            }
        },
        files=InitFiles({
            '/var/www/html/index.html': InitFile(
                content='<html><body><h2>Automation for the People!</h2></body></html>',
                mode='000644',
                owner='root',
                group='root'
            )
        }),
        services={
            'sysvinit': InitServices({
                'httpd': InitService(enabled=True,
                ensureRunning=True)
            })
        })
    }))

    # EC2 Instance
    ec2 = mini_template.add_resource(
        Instance(
            'Ec2Instance',
            ImageId=FindInMap(
                'AWSRegionArch2AMI',
                Ref('AWS::Region'),
                'HVM64'),
            Metadata=ec2_metadata,
            InstanceType=Ref(instance_type),
            KeyName=keyPair,
            SecurityGroupIds=[Ref(web_security_group), ],
            SubnetId=Ref(subnet),
            Tags=Tags(Name=stack_name + '-ec2', Project=stack_name),
            CreationPolicy=CreationPolicy(
                ResourceSignal=ResourceSignal(
                    Timeout='PT15M')),
            UserData=Base64(
                Join(
                    '',
                    [
                        '#!/bin/bash -x\n',
                        'yum update -y\n',
                        'yum update -y aws-cfn-bootstrap\n',
                        '/opt/aws/bin/cfn-init -v ',
                        '         --stack ',
                        Ref('AWS::StackName'),
                        '         --resource Ec2Instance ',
                        '         --region ',
                        Ref('AWS::Region'),
                        '\n',
                        '/opt/aws/bin/cfn-signal -e $? ',
                        '         --stack ',
                        Ref('AWS::StackName'),
                        '         --resource Ec2Instance ',
                        '         --region ',
                        Ref('AWS::Region'),
                        '\n',
                    ]
                )
            )
        )
    )

    ### Outputs ###

    # Output the Public DNS address for the EC2 instance
    mini_template.add_output(
        Output('URL',
            Description='HTTP Server URL',
            Value=Join('', [ 'http://', GetAtt('Ec2Instance', 'PublicDnsName') ])
        )
    )

    print 'CloudFormation template build is completed.'
    return mini_template

def key_pair(key, secretKey, region, keyPair):
    ''' Validate the EC2 key pair entered exists.'''
    print
    print '################ 1. Key Pair Validation Phase ################'
    ec2 = boto3.client(
        'ec2',
        region_name=region,
        aws_access_key_id=key,
        aws_secret_access_key=secretKey
    )
    
    # Get all keypairs which exist in the selected region
    key_pairs = ec2.describe_key_pairs()

    if(keyPair in json.dumps(key_pairs['KeyPairs'])):
        print keyPair + ' key pair was found!'
        return keyPair
    else:
        print 'The key pair name you entered was not found.'
        print 'Please enter a valid key pair name and run the script again.'
        return None

def getParams_run():
    ''' Gets parameters from the command line and executes each step of the script. '''

    print '################ Matt Adorjan - Mini Project ################'

    # Define and parse parameters passed in when running from the command line
    parse = argparse.ArgumentParser(
        description='Mini Project script which provisions \
                    VPC, IGW, Route Table, Subnet, and EC2 instance \
                    in AWS to support a static website.')
    parse.add_argument('-k','--key', help='AWS Access Key',required=True)
    parse.add_argument('-s','--secretkey',help='AWS Secret Access Key', required=True)
    parse.add_argument('-p','--keypair',help='EC2 Key Pair', required=True)
    parse.add_argument('-r','--region',help='AWS Region', default='us-east-1', required=False)
    parse.add_argument('-i','--instancetype',help='EC2 Instance Type (e.g. t2.micro)', default='t2.micro', required=False)
    args = parse.parse_args()

    # 1. Select Key Pair to use for EC2 Instance
    ec2KeyPair = key_pair(args.key, args.secretkey, args.region, args.keypair)

    # 2. Build the template
    if(ec2KeyPair != None):
        ec2Template = build_template(ec2KeyPair, args.instancetype)
    else:
        return

    # 3. Create the stack and store the web address
    http_address = create_stack(args.key, args.secretkey, args.region, ec2Template.to_json())

    # 4. Test the stack
    run_tests(http_address)

if __name__ == '__main__':
    getParams_run()
