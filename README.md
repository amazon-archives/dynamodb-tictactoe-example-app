# Tic Tac Toe on DynamoDB

TicTacToe is a lightweight application that runs on Python and depends on two packages, Flask(0.9) and Boto(2.27).  If you want in depth information about the application and DynamoDB check out [Tic Tac Toe on DynamoDB](http://docs.aws.amazon.com/amazondynamodb/latest/developerguide/ExampleApps.html).

Below are instructions that will help you launch the application.
These instructions will also require you to have access to a terminal.

**Note: May need administrative privileges for these installations**

## Installing Python

Download Python (use v2.7) by following the instructions on https://www.python.org/download/

## Installing Flask and Boto (Choose one of the two options):
    
Download/install pip *(Follow the instructions here http://pip.readthedocs.org/en/latest/installing.html)*

   Once you have pip up to date and installed, run these commands.

        pip install Flask
        pip install boto

* * *
Alternatively, clone the two packages from git and running the setup scripts.

   *Flask:*
   
        git clone http://github.com/mitsuhiko/flask.git
        cd flask
        python setup.py develop    

   *Boto:*
   
        git clone git://github.com/boto/boto.git
        cd boto
        python setup.py install

   **Note: If you don't have the Git CLI tools yet, there is a section Installing Git below.**

## Configuring Tic Tac Toe
Once you have these dependencies set up, you will have to run the application with your own configurations.

The full list of options is as follows:

      python application.py [-h] [--config pathToConfig] [--mode (local | service)]
                            [--endpoint ENDPOINT] [--port dbPort] [--serverPort flaskPort]

Additionally you can set your ENVIRONMENT VARIABLES: **AWS_ACCESS_KEY_ID** and **AWS_SECRET_ACCESS_KEY** instead of using config file.
This way, you can just run the following command and start the webserver on the default port 5000 and call DynamoDB in the SDK's default region.

      python application.py

Your config file will vary depending, but the general structure is as follows:

* Use the **[dynamodb]** tag to specify all dynamodb specific configurations (i.e. endpoint, region, port).  For more information about regions and endpoints, check out [Regions and Endpoints](http://docs.aws.amazon.com/general/latest/gr/rande.html#ddb_region).

* Use the **[flask]** tag to specify all flask specific configurations (i.e. serverPort, secret_key).

**Note: Secret_key is generated on start up in the app, but will be used when you spawn the Tic Tac Toe application on multiple instances and want to encrypt cookies with the same key.**

## Launching TicTacToe onto ElasticBeanstalk (EB)

In order to launch this project onto an ElasticBeanstalk instance you'll need two more tools, Git and EB.

Below are instructions that will help you launch your project onto EB.

### Installing Git
[Download the Git CLI](http://git-scm.com/)

Once you have git installed, make sure you are inside the application's root directory. Initialize your local Git repository using

        git init .

### Installing EB
[Download the Elastic Beanstalk CLI](http://aws.amazon.com/code/6752709412171743) 

Initialize your EB instance using

        eb init

Setting up your IAM User/Role
    In your AWS console, go to the service called IAM. For the sake of this application, you need to configure Users and Roles.  You start off by creating a new User (an alias for your account) and follow the steps for generating access keys (if you haven't already).  You can then manage the permissions on this User, and using either the templates or custom permissions, ensure your user has permissions to ElasticBeanstalk and DynamoDB.  Afterwards go to the Role you init your EB instance with (if you haven't init'ed yet create a new Role here) and manage permissions once again, ensuring access DynamoDB is allowed.

Once your instance is setup and linked with your AWS account, run

    eb start

    eb status --verbose
    
**Note: You may have to run eb status multiple times to verify your application has Status Green, which means it's available.**

Follow the URL given to you by 'eb status' and you should be good to go!

**Note: [Full instructions for launching Flask on EB](http://docs.aws.amazon.com/elasticbeanstalk/latest/dg/create_deploy_Python_flask.html)**
