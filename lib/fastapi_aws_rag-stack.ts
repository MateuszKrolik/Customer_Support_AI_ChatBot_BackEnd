import * as cdk from 'aws-cdk-lib';
import {Construct} from 'constructs';
import {Architecture, DockerImageCode, DockerImageFunction, FunctionUrlAuthType,} from 'aws-cdk-lib/aws-lambda';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import {ManagedPolicy} from "aws-cdk-lib/aws-iam";

// import {AttributeType, BillingMode, Table} from "aws-cdk-lib/aws-dynamodb";

export class FastapiAwsRagStack extends cdk.Stack {
    constructor(scope: Construct, id: string, props?: cdk.StackProps) {
        super(scope, id, props);
        // Retrieve secrets from SSM Parameter Store
        const dynamoDbTableName = ssm.StringParameter.valueForStringParameter(
            this,
            '/fastapi-rag/DYNAMODB_TABLE_NAME'
        );

        // The code that defines your stack goes here
        const apiImageCode = DockerImageCode.fromImageAsset('./app', {
            cmd: ['api/main.handler'],
            buildArgs: {
                platform: 'linux/amd64',
            },
        });

        // // uncomment if there are changes made to table
        // const queryTable = new Table(this, 'QueryTable', {
        //     partitionKey: {name: 'query_id', type: AttributeType.STRING},
        //     billingMode: BillingMode.PAY_PER_REQUEST
        // });

        const apiFunction = new DockerImageFunction(this, 'ApiFunc', {
            code: apiImageCode,
            memorySize: 256,
            timeout: cdk.Duration.seconds(30),
            architecture: Architecture.X86_64,
            environment: {
                DYNAMODB_TABLE_NAME: dynamoDbTableName,
            },
        });

        // // uncomment if there are changes made to table
        // queryTable.grantReadWriteData(apiFunction);
        apiFunction.role?.addManagedPolicy(
            ManagedPolicy.fromAwsManagedPolicyName("AmazonBedrockFullAccess")
        )
        apiFunction.role?.addManagedPolicy(
            ManagedPolicy.fromAwsManagedPolicyName("AmazonDynamoDBFullAccess")
        );

        // Public URL for the API function.
        const functionUrl = apiFunction.addFunctionUrl({
            authType: FunctionUrlAuthType.NONE,
        });

        // Output the URL for the API function.
        new cdk.CfnOutput(this, 'FunctionUrl', {
            value: functionUrl.url,
        });

        // // uncomment if there are changes made to table
        // // Output the table name to confirm creation
        // new cdk.CfnOutput(this, 'QueryTableName', {
        //     value: queryTable.tableName,
        // });
    }
}
