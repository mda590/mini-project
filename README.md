# Matt Adorjan - Mini Project

## About this Project
This project is a demo of the creation of a web server, deployment of a single static web page, and testing of the deployment.
The deployment is meant to be fully automated - a single line command can build, run, and test the environment.

## Prerequisites
* :cloud: You must have an AWS account to successfully execute this automated deployment.
* :closed_lock_with_key: You will need the Access Key and Secret Access Key for an IAM user with access to CloudFormation and EC2.
    * Generally, the built-in AdministratorAccess policy will be sufficient for testing this script, however
    using the AdministratorAccess policy in a production environment should be avoided in favor of fine grained policies.
* :key: You will need an EC2 Key Pair created on your account which can be passed as a parameter.

The script is written fully in Python utilizing Troposphere for the creation of the CloudFormation template,
and the Boto3 Python SDK for AWS for deploying the infrastructure.

:snake: The following Python packages are required:
 * Troposphere (pip install troposphere)
 * Boto3 Python SDK (pip install boto3)
 * Botocore (installed as a part of Boto3)
 * Other packages required (should already be installed as a part of Python):
        argparse, urllib2, json, time

## Utilization Instructions
The script takes 5 parameters. To see how to use the script and each of the parameters, run:
```python
python build_env.py --help
```

The accepted parameters are:

Parameter | Required | Description
--------- | -------- | -----------
-k        | Yes      | AWS Access Key ID
-s        | Yes      | AWS Secret Access Key ID
-p        | Yes      | EC2 Key Pair to use for new instance
-r        | No       | AWS Region Name Identifier (default is us-east-1)
-i        | No       | AWS Instance Type (default is t2.micro)

Example script execution:
```python
python build_env.py -k <access-key> -s <secret-key> -p 'matt-ohio-key' -r 'us-east-2' -i 't2.micro'
```

## Automation Phases
### By executing the script, you will be kicking off the following 4 phases:
1. Key Pair Validation
    * Validates that the key pair passed as a parameter exists in the account.
    * If the key pair does not exist, the script will exit and require a valid key pair be entered.
2. CloudFormation Template Build
    * Uses Troposphere
    * Builds the following "base" components: VPC, Internet Gateway, Route Table, Subnet, and Security Group
    * Builds an EC2 instance
    * Installs Apache and configures the index.html page using CloudFormation EC2 Instance Metadata.
3. Stack Creation
    * Validates the template syntax for the template generated in Phase #2.
    * Creates a stack in your AWS account using the template generated and outputs the URL of the instance when complete.
4. Test
    * Verifies that the text "Automation to the People" appears on the index.html page.

